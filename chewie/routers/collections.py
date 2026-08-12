"""Collections endpoints (/api/collections/*)."""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime

from core.api_schema import parse_body_pydantic
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from db import get_db, new_id
from core.auth import _require_admin, _require_authenticated
from core.audit import _log_audit, log_admin_change
from core.errors import api_error
# ga-close-v3 PartD D-3: 伏字件数の数え方は guardrail.py の 1 か所に集約する。
from guardrail import PII_COUNT_TIER, pii_counts_from_db

router = APIRouter(tags=["collections"])


RAG_STRATEGIES = {"simple", "hybrid_bm25", "contextual"}


# ============================================================
# Stage R7 C-4: Smart Ingestion Stage 2/3 状態遷移
# ============================================================
# 遷移パス (Notion 35994ef8 / Phase 3 Recon Agent J §1-3 中):
#   draft → ingested → ready
#   draft → publishing → ready / failed (legacy 経路、互換維持)
#   publishing → stopped (中断)
#
# migration 0002 で collections.status の CHECK に 'ingested' を追加。
# Phase 3 Recon Agent J で grep ヒット 0 だった機能を本実装で 3+ 件に。

VALID_STATE_TRANSITIONS = {
    ("draft", "ingested"): "ingest 完了 (Stage 2 → Stage 3 入口)",
    ("draft", "publishing"): "legacy publish 開始 (Stage 1 → publishing)",
    ("ingested", "ready"): "publish 完了 (Stage 3 → Ready)",
    ("ingested", "publishing"): "ingest 後の本 publish 開始",
    ("publishing", "ready"): "publish 完了",
    ("publishing", "failed"): "publish 失敗",
    ("publishing", "stopped"): "publish 中断",
    ("failed", "draft"): "失敗からのリトライ",
    ("ready", "draft"): "再 ingest のための差し戻し",
}


def transition_collection_state(col_id: str, from_state: str, to_state: str, conn=None) -> bool:
    """Smart Ingestion 状態遷移ヘルパー (Stage 2/3 経路)。

    Stage R7 C-4 で新設。VALID_STATE_TRANSITIONS の合法遷移のみ許可する。
    """
    if (from_state, to_state) not in VALID_STATE_TRANSITIONS:
        return False
    own_conn = conn is None
    if own_conn:
        conn = get_db()
    try:
        cur = conn.execute(
            "UPDATE collections SET status = ? WHERE id = ? AND status = ?",
            (to_state, col_id, from_state),
        )
        if own_conn:
            conn.commit()
        return cur.rowcount > 0
    finally:
        if own_conn:
            conn.close()


@router.get("/api/collections/{collection_id}/provenance", response_model=None)
def get_collection_provenance(request: Request, collection_id: str):
    """Collection の Provenance 履歴を返す (filename, version 降順).
    存在しない collection_id を指定した場合は 404 を返す。"""
    _require_admin(request)
    conn = get_db()
    try:
        col = conn.execute("SELECT id FROM collections WHERE id = ?", (collection_id,)).fetchone()
        if not col:
            raise api_error("COLLECTION_NOT_FOUND", f"Collection not found: {collection_id}", 404)
        rows = conn.execute(
            """SELECT filename, sha256, file_size, version,
                      published_at, published_by, is_current
               FROM document_provenance
               WHERE collection_id = ?
               ORDER BY filename ASC, version DESC""",
            (collection_id,),
        ).fetchall()
    finally:
        conn.close()
    return {
        "collection_id": collection_id,
        "provenance": [dict(r) for r in rows],
    }


@router.patch("/api/collections/{col_id}/archive", response_model=None)
def archive_collection(col_id: str, request: Request):
    from core.auth import _require_admin

    user = _require_admin(request)
    conn = get_db()
    try:
        row = conn.execute("SELECT id FROM collections WHERE id = ?", (col_id,)).fetchone()
        if not row:
            raise api_error("NOT_FOUND", "collection not found", status=404)
        conn.execute(
            "UPDATE collections SET archived_at = ?, archived_by = ? WHERE id = ?",
            (datetime.now().isoformat(timespec="seconds"), user["id"], col_id),
        )
        _log_audit(conn, "collection_archived", col_id, f"by={user['id']}")
        conn.commit()
    finally:
        conn.close()
    log_admin_change(user["id"], "collection", col_id, "archive")
    return {"id": col_id, "status": "archived"}


@router.patch("/api/collections/{col_id}/unarchive", response_model=None)
def unarchive_collection(col_id: str, request: Request):
    from core.auth import _require_admin

    user = _require_admin(request)
    conn = get_db()
    try:
        conn.execute(
            "UPDATE collections SET archived_at = NULL, archived_by = NULL WHERE id = ?",
            (col_id,),
        )
        _log_audit(conn, "collection_unarchived", col_id, f"by={user['id']}")
        conn.commit()
    finally:
        conn.close()
    log_admin_change(user["id"], "collection", col_id, "unarchive")
    return {"id": col_id, "status": "unarchived"}


@router.get("/api/collections", response_model=None)
def list_collections(
    request: Request,
    workspace_id: str = None,
    include_archived: bool = False,
    limit: int | None = None,
    offset: int = 0,
    q: str | None = None,
):
    """UX-4: include_archived=true でアーカイブ済み Collection も返す."""
    from server import rows_to_list

    user = _require_authenticated(request)
    if limit is not None and limit not in (10, 20, 50, 100):
        raise HTTPException(status_code=400, detail="limitは10/20/50/100のいずれかです")
    if offset < 0:
        raise HTTPException(status_code=400, detail="offsetは0以上です")
    conn = get_db()
    try:
        where_parts: list[str] = []
        params: list = []
        if workspace_id:
            where_parts.append("workspace_id = ?")
            params.append(workspace_id)
        # authz-fix-v1: 非admin は自分の所属WSの collection のみに絞る (admin は全件=広域維持)。
        # レスポンス形は不変・件数のみ変化。手本: list_workspaces のスコープ絞り。
        if (user or {}).get("role") != "admin":
            where_parts.append("workspace_id IN (SELECT workspace_id FROM workspace_users WHERE user_id = ?)")
            params.append((user or {}).get("id"))
        if not include_archived:
            where_parts.append("archived_at IS NULL")
        if q:
            where_parts.append("name LIKE ?")
            params.append(f"%{q}%")
        where_sql = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""

        total = None
        if limit is not None:
            total = conn.execute(
                f"SELECT COUNT(*) FROM collections {where_sql}",
                params,
            ).fetchone()[0]

        pagination_sql = ""
        pagination_params: list = []
        if limit is not None:
            pagination_sql = " LIMIT ? OFFSET ?"
            pagination_params = [limit, offset]
        collections = rows_to_list(
            conn.execute(
                f"SELECT * FROM collections {where_sql} " f"ORDER BY created_at DESC {pagination_sql}",
                params + pagination_params,
            ).fetchall()
        )

        for col in collections:
            col["file_ids"] = [
                r["file_id"]
                for r in conn.execute(
                    "SELECT file_id FROM collection_files WHERE collection_id = ?", (col["id"],)
                ).fetchall()
            ]
            # rawmode-partC: raw_only 列不在の旧DBでも bool で必ず返す
            col["raw_only"] = bool(col.get("raw_only") or 0)
    finally:
        conn.close()
    if limit is None:
        return collections
    return {"items": collections, "total": total, "limit": limit, "offset": offset}


@router.post("/api/collections", response_model=None)
async def create_collection(request: Request):
    user = _require_admin(request)
    body = await parse_body_pydantic(request)
    name = body.get("name")
    workspace_id = body.get("workspace_id")
    file_ids = body.get("file_ids", [])
    access_level = body.get("access_level", "public")
    allowed_roles = body.get("allowed_roles") or ["admin", "viewer"]
    if not isinstance(allowed_roles, list):
        raise HTTPException(400, "allowed_roles must be a list")
    rag_strategy = (body.get("rag_strategy") or "hybrid_bm25").strip()
    if rag_strategy not in RAG_STRATEGIES:
        raise HTTPException(400, f"rag_strategy は {sorted(RAG_STRATEGIES)} のいずれか")
    # masked-only §9-7 (vector-tier-masked-only-20260724): 伏字なし取り込み (raw_only) は
    # 廃止。API の受け口も外す: 引数を直接渡しても伏字を経由しない取り込みは行われない。
    if bool(body.get("raw_only", False)):
        raise HTTPException(400, "raw_only (伏字なし取り込み) は廃止されました")
    # ga-finish-P4 (rawmode-receptor-close-20260727): 伏字を迂回する受け口は raw_only と
    # raw_mode の 2 系統あった。raw_only は上で廃止済みだが、raw_mode は
    # collections.rag_mode='raw' を書き、chat 側の「rawモード Collection は Guardrail を
    # バイパス」分岐 (routers/chat.py の rag_mode='raw' 判定) へ到達していた。
    # 本受け口もここで閉じる。列 (collections.rag_mode) と過去データは保全する
    # (migration は行わない)。外部提示側の伏字済みへ倒す守りは不変。
    if bool(body.get("raw_mode", False)):
        raise HTTPException(400, "raw_mode (伏字なし取り込み) は廃止されました")

    if not name or not workspace_id:
        raise HTTPException(400, "name and workspace_id are required")

    conn = get_db()
    try:
        ws_row = conn.execute("SELECT id FROM workspaces WHERE id = ?", (workspace_id,)).fetchone()
        if not ws_row:
            conn.close()
            raise HTTPException(404, f"Workspace not found: {workspace_id}")
        classification_filter = body.get("classification_filter") or []
        if classification_filter and isinstance(classification_filter, list):
            ws_src_rows = conn.execute(
                "SELECT source_id FROM workspace_sources WHERE workspace_id = ?",
                (workspace_id,),
            ).fetchall()
            ws_src_ids = [r["source_id"] for r in ws_src_rows]
            if ws_src_ids:
                placeholders = ",".join(["?"] * len(ws_src_ids))
                file_rows = conn.execute(
                    f"SELECT id, classification FROM files WHERE source_id IN ({placeholders})",
                    ws_src_ids,
                ).fetchall()
                filter_set = set(classification_filter)
                matched_ids: list = []
                for fr in file_rows:
                    cls_raw = fr["classification"]
                    if not cls_raw:
                        continue
                    try:
                        cls = json.loads(cls_raw)
                    except Exception:
                        continue
                    if cls.get("category") in filter_set:
                        matched_ids.append(fr["id"])
                file_ids = list({*file_ids, *matched_ids})
        valid_file_ids: list = []
        for fid in file_ids or []:
            if conn.execute("SELECT 1 FROM files WHERE id = ?", (fid,)).fetchone():
                valid_file_ids.append(fid)

        cid = new_id()
        try:
            _acl_json = json.dumps(allowed_roles, ensure_ascii=False)
            # ga-finish-P4: raw_mode 受け口を閉じたため、新規作成の rag_mode は常に NULL。
            # 列へ 'raw' を書く経路は存在しない (列と過去データは保全)。
            _rag_mode = None
            # masked-only §9-7: raw_only 列は残す (過去データ保全) が、新規作成は常に既定値
            # (=0) のまま。列へ 1 を書く経路は存在しない。
            conn.execute(
                "INSERT INTO collections (id, name, workspace_id, access_level, "
                "allowed_roles_json, acl_roles, rag_strategy, rag_mode) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (cid, name, workspace_id, access_level, _acl_json, _acl_json, rag_strategy, _rag_mode),
            )
            for fid in valid_file_ids:
                conn.execute(
                    "INSERT OR IGNORE INTO collection_files (collection_id, file_id) VALUES (?, ?)",
                    (cid, fid),
                )
            conn.commit()
        except HTTPException:
            raise
        except Exception as e:
            conn.close()
            raise HTTPException(400, f"Collection作成失敗: {e}")
    finally:
        conn.close()
    return {
        "id": cid,
        "name": name,
        "status": "draft",
        "access_level": access_level,
        "allowed_roles": allowed_roles,
        "rag_strategy": rag_strategy,
        # ga-finish-P4: 受け口を閉じたので常に False (応答キーは互換のため残す)。
        "raw_mode": False,
    }


@router.get("/api/collections/{col_id}", response_model=None)
def get_collection_by_id(request: Request, col_id: str):
    """PHASE 0-C: Collection 単体取得"""
    _require_admin(request)
    conn = get_db()
    try:
        col = conn.execute("SELECT * FROM collections WHERE id = ?", (col_id,)).fetchone()
        if not col:
            conn.close()
            raise HTTPException(404, "Collection not found")
        out = dict(col)
        out["file_ids"] = [
            r["file_id"]
            for r in conn.execute("SELECT file_id FROM collection_files WHERE collection_id = ?", (col_id,)).fetchall()
        ]
        # rawmode-partC: raw_only 列不在の旧DBでも bool で必ず返す
        out["raw_only"] = bool(out.get("raw_only") or 0)
    finally:
        conn.close()
    return out


@router.get("/api/collections/{col_id}/publish-summary", response_model=None)
def get_collection_publish_summary(request: Request, col_id: str):
    """v3.5.0 Phase2 (完了ログ用): masked tier の chunks.pii_summary を集計して
    マスキング件数・ラベル別内訳・除外数・ファイル数を返す読み取り専用 EP。

    - DB スキーマ非変更／既存 API 非改変（新規 additive EP）。
    - 伏字・暗号化ロジックには一切触れず、既に保存済みの集計値を読むだけ。
    - raw との二重計上を避けるため masked tier のみを一次ソースにする。
    """
    _require_admin(request)
    conn = get_db()
    try:
        col = conn.execute("SELECT * FROM collections WHERE id = ?", (col_id,)).fetchone()
        if not col:
            conn.close()
            raise HTTPException(404, "Collection not found")
        # rawmode-partC: raw_only Collection は masked tier を持たないため、masked 由来の
        # 件数は「偽の0」ではなく null を返す (列不在の旧DBでは常に False = 従来挙動)。
        raw_only_flag = bool(dict(col).get("raw_only") or 0)
        placeholder_only_files: list = []
        skipped_details: list = []
        if raw_only_flag:
            labels = None
            pii_chunks = None
            chunk_count = None
            excluded_count = None
        else:
            # ga-close-v3 PartD D-3: 数え方は guardrail.pii_counts_from_db に集約した。
            #   旧実装は masked 層を 5 種の許可リスト
            #   {PERSON_JP,PHONE_JP,EMAIL,MYNUMBER,CREDIT} でだけ数えており、
            #   URL / IPV4 / PHONE_LAND / PASSPORT / SSN / IBAN / 資格情報しか当たって
            #   いない塊は伏字が効いていても 0 件として落ちていた
            #   (公開済み「デモ資料一式」実測: 旧 361 / 全型 2121)。
            #   ここで数え直さない = 許可リストを復活させないこと。
            _counts = pii_counts_from_db(conn, collection_id=col_id)
            labels = _counts["labels"]
            pii_chunks = _counts["pii_chunks"]
            chunk_count = _counts["chunk_count"]
            excluded_count = conn.execute(
                "SELECT COUNT(*) AS n FROM chunks WHERE collection_id = ? AND tier = ? AND excluded = 1",
                (col_id, PII_COUNT_TIER),
            ).fetchone()["n"]
        # vision-placeholder-warn-20260727: 中身が1文字も入らなかったファイル。
        #   chunks.content は暗号文で保存されるため、索引から数え直すことはできない
        #   (平文と誤認して常に0を返す＝この Part が塞ごうとしている「やっていないのに
        #   成功を返す」を自分で作ることになる)。判定は平文がある取り込みの瞬間に一度だけ
        #   行い、その結果を取り込み操作ログへ残してここで読み出す。
        try:
            _plog = conn.execute(
                "SELECT metadata_json FROM processing_logs "
                "WHERE log_type = 'ingest' AND metadata_json LIKE ? "
                "ORDER BY id DESC LIMIT 1",
                (f'%"stage": "done"%{col_id}%',),
            ).fetchone()
            if _plog and _plog["metadata_json"]:
                _pm = json.loads(_plog["metadata_json"]) or {}
                if _pm.get("collection_id") == col_id:
                    placeholder_only_files = list(_pm.get("placeholder_only_files") or [])
                    # DD-CYN-0091 C: 飛ばしたファイルの一覧 (done イベント由来・additive)
                    skipped_details = list(_pm.get("skipped_details") or [])
        except Exception:
            placeholder_only_files = []
        file_count = conn.execute(
            "SELECT COUNT(*) AS n FROM collection_files WHERE collection_id = ?",
            (col_id,),
        ).fetchone()["n"]
        # receiptfix-20260723: 受領書の「所要時間 0.0s」是正。この Collection の最新 completed
        #   publish job の実経過秒を additive に返す (publish_history は workspace 単位で
        #   collection_id を持たないため publish_jobs の created_at/updated_at から算出)。
        elapsed_seconds = None
        try:
            _job = conn.execute(
                "SELECT created_at, updated_at FROM publish_jobs "
                "WHERE collection_id = ? AND status = 'completed' "
                "ORDER BY updated_at DESC LIMIT 1",
                (col_id,),
            ).fetchone()
            if _job and _job["created_at"] and _job["updated_at"]:
                from datetime import datetime as _dt
                _fmt = "%Y-%m-%d %H:%M:%S"
                elapsed_seconds = round(
                    (_dt.strptime(_job["updated_at"], _fmt) - _dt.strptime(_job["created_at"], _fmt)).total_seconds(),
                    1,
                )
        except Exception:
            elapsed_seconds = None
    finally:
        conn.close()
    return {
        "collection_id": col_id,
        "chunk_count": chunk_count,
        "excluded_count": excluded_count,
        "file_count": file_count,
        "pii_count": pii_chunks,
        "pii_labels": labels,
        "raw_only": raw_only_flag,
        "elapsed_seconds": elapsed_seconds,
        # vision-placeholder-warn-20260727 (additive・既存キー不変)
        "placeholder_only_count": len(placeholder_only_files),
        "placeholder_only_files": [os.path.basename(_f) for _f in placeholder_only_files[:50]],
        # DD-CYN-0091 C (additive): 飛ばしたファイルの一覧 (ファイル名+理由)
        "skipped_details": skipped_details[:50],
    }


@router.put("/api/collections/{col_id}", response_model=None)
async def update_collection(col_id: str, request: Request):
    _require_admin(request)
    body = await parse_body_pydantic(request)
    conn = get_db()
    try:
        col = conn.execute("SELECT * FROM collections WHERE id = ?", (col_id,)).fetchone()
        if not col:
            conn.close()
            raise HTTPException(404, "Collection not found")
        # DD-CYN-0091 C: file_ids の付け替えだけは公開済み(ready/error)でも許す。
        # クイックスタートが既存のまとまりを更新するとき、再スキャンで増減したファイルを
        # 紐づけ直してから再publishするためである。他の項目は従来どおり draft のみ。
        _non_file_keys = [k for k in body.keys() if k != "file_ids"]
        if col["status"] != "draft" and _non_file_keys:
            conn.close()
            raise HTTPException(400, "Can only update draft collections")
        if col["status"] == "publishing" and "file_ids" in body:
            conn.close()
            raise HTTPException(409, "Publish進行中はファイル構成を変更できません")

        if "name" in body:
            conn.execute("UPDATE collections SET name = ? WHERE id = ?", (body["name"], col_id))
        if "access_level" in body:
            conn.execute("UPDATE collections SET access_level = ? WHERE id = ?", (body["access_level"], col_id))
        if "allowed_roles" in body:
            ar = body["allowed_roles"]
            if not isinstance(ar, list):
                conn.close()
                raise HTTPException(400, "allowed_roles must be a list")
            conn.execute(
                "UPDATE collections SET allowed_roles_json = ? WHERE id = ?",
                (json.dumps(ar), col_id),
            )
        if "rag_strategy" in body:
            rs = (body["rag_strategy"] or "").strip()
            if rs not in RAG_STRATEGIES:
                conn.close()
                raise HTTPException(400, f"rag_strategy は {sorted(RAG_STRATEGIES)} のいずれか")
            conn.execute(
                "UPDATE collections SET rag_strategy = ? WHERE id = ?",
                (rs, col_id),
            )
        for _bk, _col in (("chunk_size", "chunk_size"), ("chunk_overlap", "chunk_overlap")):
            if _bk in body:
                v = body[_bk]
                if v in (None, ""):
                    conn.execute(f"UPDATE collections SET {_col} = NULL WHERE id = ?", (col_id,))
                else:
                    try:
                        iv = int(v)
                        if iv < 0:
                            raise ValueError("negative")
                        conn.execute(
                            f"UPDATE collections SET {_col} = ? WHERE id = ?",
                            (iv, col_id),
                        )
                    except (TypeError, ValueError):
                        conn.close()
                        raise HTTPException(400, f"{_bk} は 0 以上の整数を指定してください")
        if "rag_mode" in body:
            rm = body["rag_mode"]
            if rm in (None, ""):
                conn.execute("UPDATE collections SET rag_mode = NULL WHERE id = ?", (col_id,))
            else:
                rm_s = str(rm).strip().lower()
                if rm_s not in ("lite", "standard", "hq"):
                    conn.close()
                    raise HTTPException(400, "rag_mode は lite/standard/hq または空欄")
                conn.execute(
                    "UPDATE collections SET rag_mode = ? WHERE id = ?",
                    (rm_s, col_id),
                )
        if bool(body.get("raw_only", False)):
            # masked-only §9-7: 伏字なし取り込み (raw_only) は廃止。更新の受け口も外す。
            raise HTTPException(400, "raw_only (伏字なし取り込み) は廃止されました")
        if bool(body.get("raw_mode", False)):
            # ga-finish-P4: raw_mode も廃止。更新の受け口でも明示的に拒否する
            # (従来は無視されて 200 を返していた)。
            raise HTTPException(400, "raw_mode (伏字なし取り込み) は廃止されました")
        if "file_ids" in body:
            conn.execute("DELETE FROM collection_files WHERE collection_id = ?", (col_id,))
            for fid in body["file_ids"]:
                # dbconn-fix: FK 違反 (存在しない file_id) は 500 ではなく 400 で返す。
                # 例外時も外側の finally が conn.close() を保証する (ロック滞留防止)。
                try:
                    conn.execute(
                        "INSERT INTO collection_files (collection_id, file_id) VALUES (?, ?)",
                        (col_id, fid),
                    )
                except sqlite3.IntegrityError:
                    raise HTTPException(400, "存在しないfile_idが含まれています")

        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "id": col_id}


@router.delete("/api/collections/{col_id}", response_model=None)
def delete_collection(request: Request, col_id: str):
    from server import _purge_chunks_for_collection, _purge_chunks_for_source

    _require_admin(request)
    conn = get_db()
    try:
        # fix-v3 (A2-F2): BM25 索引再構築のため削除前に workspace_id を取得しておく。
        _ws_row = conn.execute("SELECT workspace_id FROM collections WHERE id = ?", (col_id,)).fetchone()
        _ws_id = _ws_row["workspace_id"] if _ws_row else None
        # cascade-source-cleanup (key-vector-fix-20260721): 削除前に、この collection が
        # 使っていた取り込み元 (source) の候補を控える。削除後にどこからも使われて
        # いない source だけを連鎖削除する (他 collection が使う source は残す)。
        _cand_sources = [
            r["source_id"]
            for r in conn.execute(
                "SELECT DISTINCT f.source_id FROM collection_files cf "
                "JOIN files f ON f.id = cf.file_id WHERE cf.collection_id = ?",
                (col_id,),
            ).fetchall()
        ]
        _purge_chunks_for_collection(conn, col_id)
        conn.execute("DELETE FROM collection_files WHERE collection_id = ?", (col_id,))
        conn.execute("DELETE FROM collections WHERE id = ?", (col_id,))
        # fix-v3 (A2-F5): Collection 削除の監査ログ (delete_workspace/delete_source と対称化)。
        _log_audit(conn, "collection_deleted", col_id)
        for _sid in _cand_sources:
            _still = conn.execute(
                "SELECT COUNT(*) AS n FROM collection_files cf "
                "JOIN files f ON f.id = cf.file_id WHERE f.source_id = ?",
                (_sid,),
            ).fetchone()["n"]
            if _still == 0:
                _purge_chunks_for_source(conn, _sid)
                conn.execute("DELETE FROM sources WHERE id = ?", (_sid,))
                _log_audit(conn, "source_cascade_deleted", _sid)
        conn.commit()
    finally:
        conn.close()
    # fix-v3 (A2-F2): 削除コミット後に BM25 索引を再構築する。従来は delete 経路が
    # rebuild_bm25_from_db を呼ばず in-memory BM25 索引が stale のままで、同一 WS に生
    # コレクションが残る限り削除済みチャンクが RAG 回答に残留する漏洩があった (実機再現済)。
    # publish 経路 (rag.py:1662) と同型の再構築をコミット後に行い索引を最新化する。
    if _ws_id:
        try:
            from rag import rebuild_bm25_from_db
            rebuild_bm25_from_db(_ws_id)
        except Exception:
            pass
    return {"ok": True}


# ─── Publish endpoints ──────────────────────────────────────


@router.get("/api/collections/{col_id}/publish-diff", response_model=None)
# ingest-eventloop-unblock-20260727: 対象ファイル全件の sha256 を取るため、コーパスが
#   大きいとイベントループ上で GB 単位の読み込みが走る。await は1つも無いので `def` にして
#   スレッドプールへ回す (挙動不変)。
def publish_diff(request: Request, col_id: str):
    """PORTABILITY FIX 20260527 Stage2 D-1: 再 Publish 前の差分チェック。

    file_hashes に記録された前回 Publish 時の sha256 とファイルシステム上の
    現在の sha256 を比較し、new/modified/deleted の件数を返す。
    フロントはこれを見て「差分なし」なら確認ダイアログを出す。
    """
    _require_admin(request)
    import hashlib as _hl
    import os as _os

    conn = get_db()
    try:
        col = conn.execute("SELECT * FROM collections WHERE id = ?", (col_id,)).fetchone()
        if not col:
            raise HTTPException(404, "Collection not found")
        files = conn.execute(
            "SELECT f.id, f.path FROM files f JOIN collection_files cf ON f.id = cf.file_id "
            "WHERE cf.collection_id = ?",
            (col_id,),
        ).fetchall()
        stored = {
            r["file_path"]: r["sha256"]
            for r in conn.execute(
                "SELECT file_path, sha256 FROM file_hashes WHERE collection_id = ?",
                (col_id,),
            ).fetchall()
        }
        current_fs: dict[str, str] = {}
        for f in files:
            fpath = f["path"]
            if not fpath or not _os.path.exists(fpath):
                continue
            try:
                with open(fpath, "rb") as fp:
                    current_fs[fpath] = _hl.sha256(fp.read()).hexdigest()
            except Exception:
                continue
        new_files = sum(1 for p in current_fs if p not in stored)
        modified_files = sum(1 for p, h in current_fs.items() if p in stored and stored[p] != h)
        deleted_files = sum(1 for p in stored if p not in current_fs)
        return {
            "has_changes": (new_files + modified_files + deleted_files) > 0,
            "new_files": new_files,
            "modified_files": modified_files,
            "deleted_files": deleted_files,
        }
    finally:
        conn.close()


# DD-CYN-0091 B: dup-publish-guard-20260710 (同一ファイルの別コレクション重複publishの
# 遮断) は撤去した。主キー (chunks.chunk_id) にまとまりの識別子を含めたため、同じ
# ファイルが別のまとまりに在っても主キーはぶつからない。同一まとまりへの再publishは
# 従来どおり file_hashes の差分で更新される。
@router.post("/api/collections/{col_id}/publish", response_model=None)
# ingest-eventloop-unblock-20260727 (GA ブロッカー①):
#   この関数は publish_collection_iter を await 無しで最後まで回す。PDF 抽出・チャンク化・
#   伏字・埋め込み・保存のすべてがイベントループ上で動くため、大型 PDF の取り込み中は
#   / も /api/ready も応答できなくなっていた (前走行 falcon 約34分・90サンプル中 89 が HTTP 000)。
#   本文に await は1つも無いので `async def` を `def` にするだけでよい。FastAPI が
#   同期の経路操作をスレッドプールへ回すため、実行内容・応答形・ガード・履歴記録は不変で
#   イベントループだけが解放される。SSE 版 publish_stream (下) は元から `def` で同じ実行模型。
def publish(request: Request, col_id: str):
    from server import (
        compute_exclude_paths_for_collection,
        _resolve_collection_chunking,
        _finalize_publish_success,
        row_to_dict,
        logger,
    )
    from rag import publish_collection
    from pipeline_types import PipelineResult

    _require_admin(request)
    conn = get_db()
    try:
        col = conn.execute("SELECT * FROM collections WHERE id = ?", (col_id,)).fetchone()
        if not col:
            conn.close()
            raise HTTPException(404, "Collection not found")

        file_rows = conn.execute(
            "SELECT f.path FROM files f JOIN collection_files cf ON f.id = cf.file_id WHERE cf.collection_id = ?",
            (col_id,),
        ).fetchall()
        file_paths = [r["path"] for r in file_rows]

        if not file_paths:
            conn.close()
            raise HTTPException(400, "Collectionにファイルがありません。ファイルを追加してからPublishしてください。")

        # sync-publish-guard-20260725: 進行中の publish があるとき同期版は待たせず明示的に断る (async 版 409 と同じ扱い)。
        #   同期版はイベントループ上で publish を走らせるため、進行中 publish の書き込みロックを
        #   待ち始めるとサーバ全体が応答不能になる。同一コレクションに限らず全体で遮断する。
        #   第一判定はプロセス内レジストリ (DB 非依存)。publish 中の DB writer ロック競合下でも
        #   ここで即座に 409 を返せる (自動 publish・SSE・async いずれの経路も登録される)。
        from rag import get_active_publishes as _get_active_publishes

        _active = _get_active_publishes()
        if _active:
            raise HTTPException(
                409,
                f"Publish が進行中です (collection={_active[0]})。完了を待ってから実行してください。",
            )
        _busy = conn.execute(
            "SELECT collection_id FROM publish_jobs WHERE status IN ('pending','running') LIMIT 1"
        ).fetchone()
        if _busy is None:
            _busy = conn.execute(
                "SELECT id AS collection_id FROM collections WHERE status = 'publishing' LIMIT 1"
            ).fetchone()
        if _busy:
            conn.close()
            raise HTTPException(
                409,
                f"Publish が進行中です (collection={_busy['collection_id']})。完了を待ってから実行してください。",
            )

        excluded_paths = compute_exclude_paths_for_collection(conn, col_id)
        workspace_id = col["workspace_id"]
        _ws_acl = conn.execute("SELECT acl_config FROM workspaces WHERE id = ?", (workspace_id,)).fetchone()
        _pdf_mode = "fast"
        if _ws_acl and _ws_acl["acl_config"]:
            try:
                _pdf_mode = (json.loads(_ws_acl["acl_config"]) or {}).get("pdf_mode") or "fast"
            except Exception:
                _pdf_mode = "fast"

        conn.execute("UPDATE collections SET status = 'publishing' WHERE id = ?", (col_id,))
        conn.commit()

        import time as _time

        t_start = _time.perf_counter()
        publish_error = None
        _done_event = None
        try:
            _cs, _co = _resolve_collection_chunking(col_id)
            # allinone A4: 表示用 pipeline_result を SSE 経路と同じ per-publish 値に揃えるため done event を捕捉する。
            #   ラッパ publish_collection は chunk_count しか返さず、表示は _finalize_publish_success の
            #   workspace 全体累積になり SSE(per-publish) と食い違っていた(同期 excluded_count=43 vs SSE=1 等)。
            #   本ループは publish_collection と同一挙動(ラッパは本 iterator を drain するだけ・除外判定/履歴記録は不変)。
            from rag import publish_collection_iter as _publish_collection_iter
            for _ev in _publish_collection_iter(
                col_id, file_paths, chunk_size=_cs, chunk_overlap=_co, excluded_paths=excluded_paths, pdf_mode=_pdf_mode
            ):
                if _ev.get("stage") == "error":
                    raise Exception(_ev.get("message", "Publish失敗"))
                if _ev.get("stage") == "done":
                    _done_event = _ev
            chunk_count = int((_done_event or {}).get("chunk_count", 0) or 0)
            conn.execute(
                "UPDATE collections SET status = 'ready', chunk_count = ?, last_published_at = ? WHERE id = ?",
                (chunk_count, datetime.now().isoformat(timespec="seconds"), col_id),
            )
            _log_audit(conn, "collection_published", target=col_id, detail=f"Published with {chunk_count} chunks")
        except Exception as e:
            publish_error = str(e)
            conn.execute("UPDATE collections SET status = 'failed' WHERE id = ?", (col_id,))
            _log_audit(conn, "collection_publish_failed", target=col_id, detail=str(e), result="failure")
            logger.exception(f"publish failed: {e}")

        elapsed = _time.perf_counter() - t_start
        conn.commit()

        history_row = None
        if publish_error is None:
            history_row = _finalize_publish_success(conn, col_id, workspace_id or "", file_paths, elapsed)
            conn.commit()

        result = row_to_dict(conn.execute("SELECT * FROM collections WHERE id = ?", (col_id,)).fetchone())
    finally:
        conn.close()
    if history_row is not None:
        # allinone A4: 表示は per-publish(done event) を優先し SSE と一致させる。
        #   _finalize_publish_success(=workspace 全体累積) は publish_history 記録用に不変のまま使い、
        #   ここでの「今回の publish」表示だけを done event の per-publish 値で上書きする(スキーマ不変・値訂正)。
        _de = _done_event or {}
        pipeline_result = PipelineResult(
            workspace_id=history_row["workspace_id"],
            doc_count=history_row["doc_count"],
            chunk_count=int(_de.get("chunk_count", history_row["chunk_count"]) or 0),
            pii_count=int(_de.get("pii_count", history_row["pii_count"]) or 0),
            excluded_count=int(_de.get("excluded_count", history_row["excluded_count"]) or 0),
            avg_chunk_chars=history_row["avg_chunk_chars"],
            elapsed_seconds=history_row["elapsed_seconds"],
        )
        result["pipeline_result"] = pipeline_result.to_display()
    # vision-placeholder-warn-20260727: 同期版 publish でも、中身が入らなかったファイルを
    #   応答へ返し、取り込み操作ログへ残す (publish-summary はここから読む)。
    _ph_files = list((_done_event or {}).get("placeholder_only_files") or [])
    result["placeholder_only_count"] = len(_ph_files)
    result["placeholder_only_files"] = _ph_files
    if (_done_event or {}).get("placeholder_warning"):
        result["placeholder_warning"] = _done_event["placeholder_warning"]
    try:
        from server import _log_processing as _lp

        _lp(
            "ingest",
            f"完了(同期): {int((_done_event or {}).get('chunk_count', 0) or 0)} チャンクを索引化",
            level="success", job_id=f"sync-{col_id}",
            metadata={
                "stage": "done",
                "chunk_count": int((_done_event or {}).get("chunk_count", 0) or 0),
                "collection_id": col_id,
                "placeholder_only_files": _ph_files,
            },
        )
    except Exception:
        pass
    return result


@router.get("/api/collections/{col_id}/publish/stream", response_model=None)
def publish_stream(request: Request, col_id: str):
    """SSEでPublish進捗をリアルタイム配信する。"""
    from server import (
        compute_exclude_paths_for_collection,
        _resolve_collection_chunking,
        _finalize_publish_success,
    )
    from rag import publish_collection_iter

    _require_admin(request)
    conn = get_db()
    try:
        col = conn.execute("SELECT * FROM collections WHERE id = ?", (col_id,)).fetchone()
        if not col:
            conn.close()
            raise HTTPException(404, "Collection not found")
        file_rows = conn.execute(
            "SELECT f.path FROM files f JOIN collection_files cf ON f.id = cf.file_id WHERE cf.collection_id = ?",
            (col_id,),
        ).fetchall()
        file_paths = [r["path"] for r in file_rows]
        excluded_paths = compute_exclude_paths_for_collection(conn, col_id)
        _ws_acl = conn.execute("SELECT acl_config FROM workspaces WHERE id = ?", (col["workspace_id"],)).fetchone()
        _pdf_mode = "fast"
        if _ws_acl and _ws_acl["acl_config"]:
            try:
                _pdf_mode = (json.loads(_ws_acl["acl_config"]) or {}).get("pdf_mode") or "fast"
            except Exception:
                _pdf_mode = "fast"
    finally:
        conn.close()

    if not file_paths:
        raise HTTPException(400, "Collectionにファイルがありません。ファイルを追加してからPublishしてください。")

    def event_generator():
        import time as _time

        t_start = _time.perf_counter()
        c = get_db()
        try:
            c.execute("UPDATE collections SET status = 'publishing' WHERE id = ?", (col_id,))
            c.commit()
        finally:
            c.close()

        final_event = None
        try:
            _cs, _co = _resolve_collection_chunking(col_id)
            for event in publish_collection_iter(
                col_id, file_paths, chunk_size=_cs, chunk_overlap=_co, excluded_paths=excluded_paths, pdf_mode=_pdf_mode
            ):
                final_event = event
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                if event.get("stage") in ("error", "stopped"):
                    break

            elapsed = _time.perf_counter() - t_start
            c = get_db()
            try:
                stage = (final_event or {}).get("stage")
                if stage == "done":
                    chunk_count = final_event.get("chunk_count", 0)
                    c.execute(
                        "UPDATE collections SET status = 'ready', chunk_count = ?, last_published_at = ? WHERE id = ?",
                        (chunk_count, datetime.now().isoformat(timespec="seconds"), col_id),
                    )
                    _log_audit(c, "collection_published", target=col_id, detail=f"Published with {chunk_count} chunks")
                    ws_row = c.execute("SELECT workspace_id FROM collections WHERE id = ?", (col_id,)).fetchone()
                    ws_id = ws_row["workspace_id"] if ws_row else ""
                    _finalize_publish_success(c, col_id, ws_id, file_paths, elapsed)
                elif stage == "stopped":
                    c.execute("UPDATE collections SET status = 'draft' WHERE id = ?", (col_id,))
                    _log_audit(
                        c,
                        "collection_publish_stopped",
                        target=col_id,
                        detail=final_event.get("message", "stopped"),
                        result="failure",
                    )
                else:
                    c.execute("UPDATE collections SET status = 'failed' WHERE id = ?", (col_id,))
                    detail = (final_event or {}).get("message", "unknown error")
                    _log_audit(c, "collection_publish_failed", target=col_id, detail=detail, result="failure")
                c.commit()
            finally:
                c.close()
        except Exception as e:
            # FIX-019: SSE エラーメッセージ汎用化 (内部パス/SQL リテラル漏洩防止)
            import logging as _logging_for_err
            import uuid as _uuid_for_err

            error_id = _uuid_for_err.uuid4().hex[:12]
            _logging_for_err.getLogger("cynovela.collections").exception(
                f"publish stream 内部エラー error_id={error_id} col_id={col_id}: {e}"
            )
            err = {"stage": "error", "message": "内部エラー", "error_id": error_id}
            yield f"data: {json.dumps(err, ensure_ascii=False)}\n\n"
            try:
                c = get_db()
                try:
                    c.execute("UPDATE collections SET status = 'failed' WHERE id = ?", (col_id,))
                    c.commit()
                finally:
                    c.close()
            except Exception:
                pass
        finally:
            # FIX-046: SSE クライアント切断時の status='publishing' 固着回避 (safety-net)。
            # 正常完了 / stopped / failed のいずれにも遷移していない場合のみ failed に戻す。
            try:
                _c_safety = get_db()
                try:
                    _row = _c_safety.execute("SELECT status FROM collections WHERE id = ?", (col_id,)).fetchone()
                    if _row and _row["status"] == "publishing":
                        _c_safety.execute(
                            "UPDATE collections SET status = 'failed' WHERE id = ?",
                            (col_id,),
                        )
                        _c_safety.commit()
                finally:
                    _c_safety.close()
            except Exception:
                pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/api/collections/{col_id}/publish/stop", response_model=None)
def stop_publish(request: Request, col_id: str):
    """P2-C: 進行中のPublishに停止フラグを立てる。"""
    from rag import request_publish_stop

    _require_admin(request)
    if request_publish_stop(col_id):
        return {"status": "stopping", "collection_id": col_id}
    return {"status": "not_running", "collection_id": col_id}


@router.post("/api/collections/{col_id}/publish/recover", response_model=None)
def recover_publishing_collection(request: Request, col_id: str):
    """Phase 0c B-2(i): "publishing" で固着した Collection を draft に戻す。"""
    from rag import request_publish_stop

    _require_admin(request)
    conn = get_db()
    try:
        col = conn.execute("SELECT * FROM collections WHERE id = ?", (col_id,)).fetchone()
        if not col:
            conn.close()
            raise HTTPException(404, "Collection not found")
        if col["status"] != "publishing":
            conn.close()
            return {
                "ok": True,
                "collection_id": col_id,
                "previous_status": col["status"],
                "recovered": False,
                "message": f"recover 不要: status={col['status']}",
            }

        try:
            request_publish_stop(col_id)
        except Exception:
            pass

        conn.execute("UPDATE collections SET status = 'draft' WHERE id = ?", (col_id,))
        affected = conn.execute(
            "UPDATE publish_jobs SET status = 'failed', "
            "error = COALESCE(error, 'recovered from stuck publishing'), "
            "updated_at = datetime('now') "
            "WHERE collection_id = ? AND status IN ('pending', 'running')",
            (col_id,),
        ).rowcount
        _log_audit(
            conn,
            "collection_publish_recovered",
            target=col_id,
            detail=f"recovered from publishing → draft (affected jobs: {affected})",
        )
        conn.commit()
    finally:
        conn.close()
    return {
        "ok": True,
        "collection_id": col_id,
        "previous_status": "publishing",
        "recovered": True,
        "affected_jobs": affected,
    }


@router.post("/api/collections/{col_id}/publish/async", response_model=None)
async def publish_async(request: Request, col_id: str):
    """非同期 Publish: job_id を発行して即座に返す。"""
    from server import (
        compute_exclude_paths_for_collection,
        _resolve_collection_chunking,
        _run_publish_background,
    )

    _require_admin(request)
    conn = get_db()
    try:
        col = conn.execute("SELECT * FROM collections WHERE id = ?", (col_id,)).fetchone()
        if not col:
            conn.close()
            raise HTTPException(404, "Collection not found")

        file_rows = conn.execute(
            "SELECT f.path FROM files f JOIN collection_files cf ON f.id = cf.file_id " "WHERE cf.collection_id = ?",
            (col_id,),
        ).fetchall()
        file_paths = [r["path"] for r in file_rows]
        if not file_paths:
            conn.close()
            raise HTTPException(400, "Collectionにファイルがありません。ファイルを追加してからPublishしてください。")

        _existing = conn.execute(
            "SELECT id FROM publish_jobs WHERE collection_id = ? AND status IN ('pending','running')",
            (col_id,),
        ).fetchone()
        if _existing:
            conn.close()
            raise HTTPException(409, "Publish already in progress for this collection")

        excluded_paths = compute_exclude_paths_for_collection(conn, col_id)
        _cs, _co = _resolve_collection_chunking(col_id)
        # P1-5: 非同期 publish でも Workspace の pdf_mode を反映する (手動 publish と同じ取得方法)
        _ws_acl = conn.execute("SELECT acl_config FROM workspaces WHERE id = ?", (col["workspace_id"],)).fetchone()
        _pdf_mode = "fast"
        if _ws_acl and _ws_acl["acl_config"]:
            try:
                _pdf_mode = (json.loads(_ws_acl["acl_config"]) or {}).get("pdf_mode") or "fast"
            except Exception:
                _pdf_mode = "fast"

        job_id = new_id()
        conn.execute(
            "INSERT INTO publish_jobs (id, collection_id, status, total, message) " "VALUES (?, ?, 'pending', ?, ?)",
            (job_id, col_id, len(file_paths), "Queued"),
        )
        conn.commit()
    finally:
        conn.close()

    threading.Thread(
        target=_run_publish_background,
        args=(job_id, col_id, file_paths, excluded_paths, _cs, _co, _pdf_mode),
        daemon=True,
    ).start()

    return {"job_id": job_id, "collection_id": col_id, "status": "pending"}


# ─── Collection lock ────────────────────────────────────────


@router.post("/api/collections/{col_id}/lock", response_model=None)
def acquire_collection_lock(col_id: str, request: Request):
    """PHASE UX-3: Publish 同時実行防止のためのコレクションロック取得。"""
    from datetime import timedelta

    _require_admin(request)
    c = get_db()
    try:
        existing = c.execute(
            "SELECT locked_by, locked_at FROM collection_locks WHERE collection_id = ?",
            (col_id,),
        ).fetchone()
        if existing:
            try:
                locked_at = datetime.fromisoformat(existing["locked_at"])
            except Exception:
                locked_at = datetime.now() - timedelta(hours=3)
            if datetime.now() - locked_at < timedelta(hours=2):
                raise HTTPException(
                    status_code=423,
                    detail=f"既に locked_by={existing['locked_by']} がロック中 (locked_at={existing['locked_at']})",
                )
        locked_by = request.client.host if request.client else "unknown"
        c.execute(
            "INSERT INTO collection_locks (collection_id, locked_by) VALUES (?, ?) "
            "ON CONFLICT(collection_id) DO UPDATE SET "
            "locked_by=excluded.locked_by, locked_at=datetime('now')",
            (col_id, locked_by),
        )
        c.commit()
    finally:
        c.close()
    return {"ok": True, "collection_id": col_id, "locked_by": locked_by}


@router.delete("/api/collections/{col_id}/lock", response_model=None)
def release_collection_lock(request: Request, col_id: str):
    """PHASE UX-3: コレクションロック解放。"""
    _require_admin(request)
    c = get_db()
    try:
        c.execute("DELETE FROM collection_locks WHERE collection_id = ?", (col_id,))
        c.commit()
    finally:
        c.close()
    return {"ok": True}
