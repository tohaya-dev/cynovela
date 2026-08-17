#!/usr/bin/env python3
"""reindex_vectors.py — 既存 demo.db の塊(chunks)からベクターインデックス(ChromaDB)を再構築する。

背景 (key-vector-fix-20260721): 稼働側の Chroma ベクターが失われても、demo.db の
chunks(raw=enc: 暗号文 / masked=マスキング平文)は無傷で残る。本ツールは原本ファイルを
使わず、DB の塊から publish_collection_iter と同じ形式のベクターを作り直す。

原則:
  - demo.db へは一切書き込まない (mode=ro)。作るのは Chroma 側のインデックスのみ。
  - 埋め込みは publish と同じ BAAI/bge-m3 (Chroma SentenceTransformerEmbeddingFunction,
    1024次元)。モデルは store/models 同梱キャッシュから読む (新規ダウンロードしない)。
  - raw 層の documents は publish と同じく enc: 暗号文で格納する (embeddings は復号平文
    から計算)。復号できない raw 行はスキップして件数を報告する。
  - 外部埋め込み (openai_compat) が設定されている環境では起動を拒否する
    (masked-only 不可侵ガードを本ツールは実装しないため)。
  - コレクション単位で完了・保存する (途中で止まってもそこまでは残る)。既に
    件数一致しているコレクションはスキップするため再実行で続きから再開できる。

使い方 (アプリのツリー直下で実行):
  python tools/reindex_vectors.py --db store/db/demo.db \
      --chroma store/vector/demo/chroma \
      [--collections all|id1,id2] [--device cpu|mps] [--batch 64] \
      [--cache /path/to/embcache.npz] [--measure 200] [--max-seconds 14400]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sqlite3
import sys
import time

_APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _APP_DIR)

EMB_MODEL = "BAAI/bge-m3"
EMB_DIM = 1024
CHUNKING_VERSION = "child_256_32_v1"
EXTRACTOR_VERSION = "plaintext_v1"
DEFAULT_ROLES = ["admin", "viewer"]


def _guard_no_external_embedding() -> None:
    try:
        from core.config import CYNOVELA_CONFIG as _CFG
    except Exception:
        return
    prov = ((_CFG.get("embedding") or {}).get("provider") or "local").lower()
    if prov not in ("local", "", "bge_m3", "default"):
        print(f"[ABORT] embedding.provider={prov} (外部埋め込み構成)。本ツールは "
              "masked-only ガードを実装しないため外部構成では実行しない。")
        sys.exit(3)


def _get_ef(device: str, cache_folder: str):
    from chromadb.utils import embedding_functions
    # EGRESS-FIX 20260724 (rag.py と同型): 同梱モデルが解決できる場合は repo id ではなく
    # ローカルパスを渡す。repo id + cache_folder のままだと初回ロード時に HF Hub へ
    # メタデータ照会が走り、遮断環境で失敗する。
    _target = EMB_MODEL
    try:
        from config import resolve_model_path as _resolve_mp
        _cand = _resolve_mp(EMB_MODEL)
        if _cand != EMB_MODEL and os.path.isdir(_cand):
            _target = _cand
    except Exception:
        pass
    kwargs = {"model_name": _target, "cache_folder": cache_folder}
    if device:
        kwargs["device"] = device
    return embedding_functions.SentenceTransformerEmbeddingFunction(**kwargs)


class EmbCache:
    """sha256(text) → 1024次元ベクター のキャッシュ (npz)。系統間で同一本文の再計算を省く。"""

    def __init__(self, path: str | None):
        self.path = path
        self.map: dict[str, list[float]] = {}
        self.dirty = 0
        if path and os.path.exists(path):
            import numpy as np
            z = np.load(path, allow_pickle=False)
            keys = [k.decode() if isinstance(k, bytes) else str(k) for k in z["keys"]]
            for k, v in zip(keys, z["vecs"]):
                self.map[k] = v.tolist()
            print(f"[cache] loaded {len(self.map)} embeddings from {path}")

    def save(self) -> None:
        if not self.path or not self.dirty:
            return
        import numpy as np
        keys = np.array(list(self.map.keys()))
        vecs = np.array(list(self.map.values()), dtype="float32")
        np.savez(self.path, keys=keys, vecs=vecs)
        self.dirty = 0
        print(f"[cache] saved {len(self.map)} embeddings to {self.path}")


def _h(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _embed(texts: list[str], ef, cache: EmbCache, batch: int) -> list[list[float]]:
    out: list[list[float] | None] = [None] * len(texts)
    miss_idx = []
    for i, t in enumerate(texts):
        v = cache.map.get(_h(t))
        if v is not None:
            out[i] = v
        else:
            miss_idx.append(i)
    for b in range(0, len(miss_idx), batch):
        idxs = miss_idx[b:b + batch]
        vecs = ef([texts[i] for i in idxs])
        for i, v in zip(idxs, vecs):
            lv = [float(x) for x in v]
            out[i] = lv
            cache.map[_h(texts[i])] = lv
            cache.dirty += 1
    return out  # type: ignore[return-value]


def _parse_chunk_id(cid: str):
    masked = cid.endswith("__masked")
    base = cid[:-len("__masked")] if masked else cid
    logical, _, ver = base.rpartition(":")
    parts = logical.split("#")
    # DD-CYN-0091 B: 新形式 {collection_id}#{source_id}#{file_id}#cNNNNN と
    # 旧形式 {source_id}#{file_id}#cNNNNN の両方を読む。親 id の再構成は実際の id から
    # 導いた接頭辞 (prefix) を使い、形式の差を吸収する。
    if len(parts) == 4 and parts[3].startswith("c"):
        _src, _fid, _cpart = parts[1], parts[2], parts[3]
    elif len(parts) == 3 and parts[2].startswith("c"):
        _src, _fid, _cpart = parts[0], parts[1], parts[2]
    else:
        return None
    return {
        "masked": masked, "logical": logical, "ver": ver or "baai_bge_m3_v1",
        "source_id": _src, "file_id": _fid, "index": int(_cpart[1:]),
        "prefix": logical.rsplit("#c", 1)[0],
        "raw_doc_id": base,
    }


def reindex_collection(conn, chroma, col_row, ef, cache: EmbCache, batch: int) -> dict:
    from vault_enc import enc_raw, dec_raw
    cid = col_row["id"]
    rows = conn.execute(
        "SELECT chunk_id, workspace_id, source_doc, page_hint, content, acl_roles, "
        "pii_detected, excluded, tier FROM chunks WHERE collection_id = ? ORDER BY chunk_id",
        (cid,),
    ).fetchall()
    files = {r["id"]: dict(r) for r in conn.execute("SELECT id, name, path FROM files").fetchall()}
    # parent 構成: ファイルごとに 実親数 から group を導出 (publish の i//group と同型)
    nchild: dict[tuple, int] = {}
    for r in rows:
        p = _parse_chunk_id(r["chunk_id"])
        if p and not p["masked"]:
            nchild[(p["source_id"], p["file_id"])] = nchild.get((p["source_id"], p["file_id"]), 0) + 1
    ngroup: dict[tuple, int | None] = {}
    for (sid, fid), nc in nchild.items():
        np_ = conn.execute(
            "SELECT COUNT(*) FROM parent_chunks WHERE parent_id LIKE ? AND tier='raw'",
            (f"{sid}#{fid}#p%",),
        ).fetchone()[0]
        ngroup[(sid, fid)] = max(1, math.ceil(nc / np_)) if np_ else None

    try:
        col_roles = json.loads(col_row["allowed_roles_json"]) if col_row["allowed_roles_json"] else None
        if not (isinstance(col_roles, list) and col_roles):
            col_roles = None
    except Exception:
        col_roles = None

    raw_hash: dict[str, str] = {}
    prepared = {"raw": [], "masked": []}
    skipped = []
    for r in rows:
        p = _parse_chunk_id(r["chunk_id"])
        if p is None:
            skipped.append((r["chunk_id"], "unparsable-id"))
            continue
        tier = "masked" if p["masked"] else "raw"
        if tier == "raw":
            # masked-only §9-1 (vector-tier-masked-only-20260724): マスキング前 (raw) の層は
            # 再構築しない (ベクターはマスキング済み一組のみ)。raw 行は content_hash の親和
            # (publish は masked メタにも raw 平文ハッシュを載せる) のためだけに復号する。
            plain = dec_raw(r["content"])
            if plain.startswith("enc:"):
                skipped.append((r["chunk_id"], "undecryptable"))
                continue
            raw_hash[p["logical"]] = _h(plain)
            continue
        else:
            # masked-only §9-2: 金庫 (関係DB) は masked 行も暗号化格納されるため復号する。
            # Chroma 側 masked documents は検索層としてマスキング済み平文のまま置く (従来どおり)。
            plain_m = dec_raw(r["content"])
            if plain_m.startswith("enc:"):
                skipped.append((r["chunk_id"], "undecryptable"))
                continue
            doc = plain_m
            embed_text = plain_m
        try:
            roles = json.loads(r["acl_roles"]) if r["acl_roles"] else None
            if not (isinstance(roles, list) and roles):
                roles = None
        except Exception:
            roles = None
        f = files.get(p["file_id"], {})
        g = ngroup.get((p["source_id"], p["file_id"]))
        parent_id = f"{p['prefix']}#p{p['index'] // g:05d}" if g else None
        meta = {
            "file_path": f.get("path", ""),
            "file_name": f.get("name") or r["source_doc"] or "",
            "chunk_index": p["index"],
            "source_id": p["source_id"],
            "file_id": p["file_id"],
            "logical_chunk_id": p["logical"] + ("__masked" if p["masked"] else ""),
            "vector_id": r["chunk_id"],
            "content_hash": "",  # 後段で raw 平文ハッシュに揃える
            "chunking_version": CHUNKING_VERSION,
            "extractor_version": EXTRACTOR_VERSION,
            "embedding_model": EMB_MODEL,
            "embedding_version": p["ver"],
            "embedding_dim": EMB_DIM,
            "pii_detected": bool(r["pii_detected"]),
            "excluded": bool(r["excluded"]),
            "allowed_roles": roles or col_roles or list(DEFAULT_ROLES),
            "acl_source": "cynovela",
            "workspace_id": r["workspace_id"],
            "tier": tier,
        }
        if parent_id:
            meta["parent_id"] = parent_id + ("__masked" if p["masked"] else "")
        prepared[tier].append({"id": r["chunk_id"], "doc": doc, "meta": meta,
                               "embed_text": embed_text, "logical": p["logical"]})

    # content_hash: publish は masked メタにも raw 平文ハッシュを載せる (dict コピー由来)
    for item in prepared["masked"]:
        item["meta"]["content_hash"] = raw_hash.get(item["logical"]) or _h(item["embed_text"])

    result = {"collection": cid, "name": col_row["name"], "skipped": skipped}
    # masked-only §9-1: マスキング前の層のコレクションが残っていれば撤去する (レガシー掃除)。
    try:
        chroma.delete_collection(name=f"{cid}__raw")
        result["raw_collection_deleted"] = True
    except Exception:
        result["raw_collection_deleted"] = False
    for tier in ("masked",):
        items = prepared[tier]
        result[f"{tier}_db"] = sum(1 for r in rows if (r["tier"] == tier))
        result[f"{tier}_prepared"] = len(items)
        if not items:
            result[f"{tier}_vec"] = 0
            continue
        name = f"{cid}__{tier}"
        # publish 経路 (rag.py get_chroma wrapper) と同じく cosine 空間で作成する。
        # 既定の L2 のままだと検索側の _dist_to_sim (cosine 前提) が全ヒット 0% に潰す。
        ccol = chroma.get_or_create_collection(
            name=name, metadata={"hnsw:space": "cosine"}, embedding_function=None
        )
        t0 = time.time()
        for b in range(0, len(items), 500):
            part = items[b:b + 500]
            embs = _embed([x["embed_text"] for x in part], ef, cache, batch)
            ccol.upsert(
                ids=[x["id"] for x in part],
                documents=[x["doc"] for x in part],
                metadatas=[x["meta"] for x in part],
                embeddings=embs,
            )
            print(f"  [{cid} {tier}] {min(b + 500, len(items))}/{len(items)} "
                  f"({time.time() - t0:.1f}s)", flush=True)
        result[f"{tier}_vec"] = ccol.count()
    cache.save()
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--chroma", required=True)
    ap.add_argument("--collections", default="all")
    ap.add_argument("--device", default="")
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--cache", default="")
    ap.add_argument("--models", default=os.path.join(_APP_DIR, "store", "models"))
    ap.add_argument("--measure", type=int, default=0,
                    help="埋め込み速度を N 塊で実測して終了 (書き込みなし)")
    ap.add_argument("--max-seconds", type=int, default=14400)
    args = ap.parse_args()

    _guard_no_external_embedding()
    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    ef = _get_ef(args.device, args.models)
    cache = EmbCache(args.cache or None)

    if args.measure:
        rows = conn.execute(
            "SELECT content FROM chunks WHERE tier='masked' AND content != '' LIMIT ?",
            (args.measure,),
        ).fetchall()
        texts = [r["content"] for r in rows]
        t0 = time.time()
        ef(texts[:8])  # ウォームアップ (モデルロード分離)
        t1 = time.time()
        for b in range(0, len(texts), args.batch):
            ef(texts[b:b + args.batch])
        dt = time.time() - t1
        print(f"[measure] model_load={t1 - t0:.1f}s embed {len(texts)} chunks in {dt:.1f}s "
              f"= {len(texts) / dt:.2f} chunks/s (device={args.device or 'default(cpu)'})")
        return 0

    import chromadb
    chroma = chromadb.PersistentClient(path=args.chroma)

    cols = conn.execute(
        "SELECT c.id, c.name, c.allowed_roles_json, "
        "(SELECT COUNT(*) FROM chunks ch WHERE ch.collection_id = c.id) AS n "
        "FROM collections c WHERE n > 0 ORDER BY n ASC"
    ).fetchall()
    if args.collections != "all":
        want = set(args.collections.split(","))
        cols = [c for c in cols if c["id"] in want]

    t_start = time.time()
    results = []
    for col in cols:
        if time.time() - t_start > args.max_seconds:
            print(f"[STOP] max-seconds {args.max_seconds} 到達。ここまでの完了分は保存済み。")
            break
        # 再開性: 既に raw/masked とも件数一致ならスキップ
        try:
            raw_n = chroma.get_collection(f"{col['id']}__raw").count()
        except Exception:
            raw_n = -1
        try:
            masked_n = chroma.get_collection(f"{col['id']}__masked").count()
        except Exception:
            masked_n = -1
        db_raw = conn.execute(
            "SELECT SUM(tier='raw'), SUM(tier='masked') FROM chunks WHERE collection_id=?",
            (col["id"],),
        ).fetchone()
        if raw_n >= (db_raw[0] or 0) and masked_n >= (db_raw[1] or 0) and raw_n > 0:
            print(f"[skip] {col['id']} ({col['name']}): 既にインデックスあり raw={raw_n} masked={masked_n}")
            continue
        print(f"[start] {col['id']} ({col['name']}) chunks={col['n']}")
        r = reindex_collection(conn, chroma, col, ef, cache, args.batch)
        results.append(r)
        print(f"[done] {col['id']} raw {r['raw_prepared']}/{r['raw_db']} -> vec {r['raw_vec']} | "
              f"masked {r['masked_prepared']}/{r['masked_db']} -> vec {r['masked_vec']} | "
              f"skipped {len(r['skipped'])}")
        for s in r["skipped"][:10]:
            print(f"    skipped: {s[0]} ({s[1]})")
    print("[summary]")
    for r in results:
        print(f"  {r['collection']} ({r['name']}): raw_vec={r['raw_vec']} masked_vec={r['masked_vec']} "
              f"skipped={len(r['skipped'])}")
    print("[note] BM25 はサーバ起動時に rebuild_bm25_from_db で再構築される (server.py:805-818)。"
          "反映にはサーバ再起動が必要。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
