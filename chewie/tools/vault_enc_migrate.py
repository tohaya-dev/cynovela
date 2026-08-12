"""vault-enc 既存データ移行スクリプト（冪等）。

raw tier のみを対象に、SQLite chunks/parent_chunks と Chroma `{cid}__raw` の
documents を `enc_raw` で再書き込みする。``enc:`` 始まりの行はスキップする (冪等)。

masked tier / __masked collection は不変。embeddings は Chroma 既存値を再利用する
（再埋め込みは行わない）。
"""

from __future__ import annotations

import os
import sys
import sqlite3
import time
from pathlib import Path

# 依存: vault_enc / chromadb (本プロジェクトの環境)
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import vault_enc  # noqa: E402
import chromadb  # noqa: E402

DB_PATH = os.environ.get(
    "CYNOVELA_DB",
    os.path.expanduser("~/.cynovela-alphaga/demo/v13-demo.db"),
)
CHROMA_PATH = os.environ.get(
    "CYNOVELA_CHROMA",
    os.path.expanduser("~/.cynovela-alphaga/demo/chroma"),
)
ENC_PREFIX = vault_enc.ENC_PREFIX


def _print(msg: str) -> None:
    print(f"[vault-enc-migrate] {msg}", flush=True)


def migrate_sqlite_chunks(conn: sqlite3.Connection) -> tuple[int, int]:
    """chunks テーブル tier='raw' の content を enc_raw で入れ直し。冪等。

    Returns:
        (touched, skipped) — 暗号化したレコード数、既に enc: 始まりだった件数。
    """
    rows = conn.execute(
        "SELECT chunk_id, content FROM chunks WHERE tier = 'raw' AND content IS NOT NULL AND content != ''",
    ).fetchall()
    touched = 0
    skipped = 0
    for cid, content in rows:
        if content.startswith(ENC_PREFIX):
            skipped += 1
            continue
        new_val = vault_enc.enc_raw(content)
        conn.execute("UPDATE chunks SET content = ? WHERE chunk_id = ?", (new_val, cid))
        touched += 1
    conn.commit()
    _print(f"chunks raw migrated: touched={touched} skipped(already enc)={skipped}")
    return touched, skipped


def migrate_sqlite_parents(conn: sqlite3.Connection) -> tuple[int, int]:
    """parent_chunks テーブル tier='raw' の content を enc_raw で入れ直し。冪等。"""
    rows = conn.execute(
        "SELECT parent_id, content FROM parent_chunks WHERE tier = 'raw' AND content IS NOT NULL AND content != ''",
    ).fetchall()
    touched = 0
    skipped = 0
    for pid, content in rows:
        if content.startswith(ENC_PREFIX):
            skipped += 1
            continue
        new_val = vault_enc.enc_raw(content)
        conn.execute(
            "UPDATE parent_chunks SET content = ? WHERE parent_id = ?", (new_val, pid)
        )
        touched += 1
    conn.commit()
    _print(
        f"parent_chunks raw migrated: touched={touched} skipped(already enc)={skipped}"
    )
    return touched, skipped


def migrate_chroma_raw(client: chromadb.PersistentClient) -> tuple[int, int, int]:
    """Chroma 各 ``{cid}__raw`` collection の documents を enc_raw で入れ直し。冪等。

    Returns:
        (collections_processed, docs_touched, docs_skipped)
    """
    cols_processed = 0
    docs_touched_total = 0
    docs_skipped_total = 0
    for col_info in client.list_collections():
        name = col_info.name
        if not name.endswith("__raw"):
            continue
        col = client.get_collection(name=name)
        # 既存値を全部取り出す (大規模 collection でも本砂場では数千件程度の想定)
        # 注: Chroma の戻り値は numpy.ndarray を含むため ``or []`` (真偽値判定) は避ける。
        data = col.get(include=["documents", "metadatas", "embeddings"])
        ids = data.get("ids") if data.get("ids") is not None else []
        docs = data.get("documents") if data.get("documents") is not None else []
        metas = data.get("metadatas") if data.get("metadatas") is not None else []
        embs = data.get("embeddings") if data.get("embeddings") is not None else []
        # numpy 配列でも len() は安全に動く。
        if len(ids) == 0:
            cols_processed += 1
            continue

        # 暗号化必要な subset のみ抽出 (enc: 始まりはスキップ)
        upsert_ids: list[str] = []
        upsert_docs: list[str] = []
        upsert_metas: list[dict] = []
        upsert_embs: list[list[float]] = []
        skipped_local = 0
        for i, _id in enumerate(ids):
            d = docs[i] if i < len(docs) else ""
            if isinstance(d, str) and d.startswith(ENC_PREFIX):
                skipped_local += 1
                continue
            new_d = vault_enc.enc_raw(d or "")
            upsert_ids.append(_id)
            upsert_docs.append(new_d)
            # metadatas / embeddings は既存値を温存
            upsert_metas.append(metas[i] if i < len(metas) else {})
            if i < len(embs):
                e = embs[i]
                # numpy 配列で来ることがあるので list[float] に正規化 (None 判定も numpy 安全に行う)
                try:
                    upsert_embs.append([float(x) for x in e])
                except Exception:
                    try:
                        upsert_embs.append(list(e))
                    except Exception:
                        upsert_embs.append(None)
            else:
                upsert_embs.append(None)  # 念のため

        if upsert_ids:
            # embeddings が None を含む場合は引数から除外して default に頼る挙動を避ける
            # → ここは全件埋まっている前提だが、念のため安全側で組み立てる。
            if any(e is None for e in upsert_embs):
                # 部分 None があれば metadatas/documents のみ更新する safer path
                col.update(ids=upsert_ids, documents=upsert_docs, metadatas=upsert_metas)
            else:
                col.upsert(
                    ids=upsert_ids,
                    documents=upsert_docs,
                    metadatas=upsert_metas,
                    embeddings=upsert_embs,
                )

        cols_processed += 1
        docs_touched_total += len(upsert_ids)
        docs_skipped_total += skipped_local
        _print(
            f"  {name}: touched={len(upsert_ids)} skipped(already enc)={skipped_local} (total ids={len(ids)})"
        )

    _print(
        f"chroma raw migration: collections={cols_processed} docs_touched={docs_touched_total} docs_skipped={docs_skipped_total}"
    )
    return cols_processed, docs_touched_total, docs_skipped_total


def main() -> int:
    _print(f"DB={DB_PATH}")
    _print(f"CHROMA={CHROMA_PATH}")
    if not os.path.exists(DB_PATH):
        _print("FATAL: DB not found")
        return 2
    if not os.path.isdir(CHROMA_PATH):
        _print("FATAL: Chroma directory not found")
        return 2

    t0 = time.time()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        ch_t, ch_s = migrate_sqlite_chunks(conn)
        pc_t, pc_s = migrate_sqlite_parents(conn)
    finally:
        conn.close()

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    co_n, do_t, do_s = migrate_chroma_raw(client)

    elapsed = time.time() - t0
    _print(
        f"DONE in {elapsed:.1f}s — chunks touched={ch_t}, parents touched={pc_t}, "
        f"chroma collections={co_n} docs touched={do_t}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
