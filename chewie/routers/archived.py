"""Archived items endpoints (/api/archived/*)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Request

from db import get_db
from core.auth import _require_admin
from core.audit import _log_audit

router = APIRouter(tags=["archived"])


@router.get("/api/archived", response_model=None)
def list_archived(request: Request):
    """アーカイブ済みアイテムをまとめて返す。"""
    _require_admin(request)
    out: dict = {"sources": [], "workspaces": [], "collections": []}
    conn = get_db()
    try:
        for kind_plural in ("sources", "workspaces", "collections"):
            try:
                rows = conn.execute(
                    f"SELECT id, name, archived_at FROM {kind_plural} "
                    f"WHERE archived_at IS NOT NULL ORDER BY archived_at DESC LIMIT 200"
                ).fetchall()
                out[kind_plural] = [dict(r) for r in rows]
            except Exception:
                pass
    finally:
        conn.close()
    return out


@router.post("/api/archived/{kind}/{item_id}/archive", response_model=None)
async def archive_item(request: Request, kind: str, item_id: str):
    """指定アイテムを論理削除（archived_at にタイムスタンプを書き込む）。"""
    from core.constants import _ARCHIVABLE

    _require_admin(request)
    if kind not in _ARCHIVABLE:
        raise HTTPException(400, f"unknown kind {kind}")
    table = _ARCHIVABLE[kind]
    conn = get_db()
    try:
        row = conn.execute(f"SELECT id FROM {table} WHERE id = ?", (item_id,)).fetchone()
        if not row:
            raise HTTPException(404, f"{kind} not found")
        now = datetime.now().isoformat(timespec="seconds")
        conn.execute(f"UPDATE {table} SET archived_at = ? WHERE id = ?", (now, item_id))
        _log_audit(conn, f"{kind}_archived", item_id, "")
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "kind": kind, "id": item_id, "archived_at": now}


@router.post("/api/archived/{kind}/{item_id}/restore", response_model=None)
async def restore_item(request: Request, kind: str, item_id: str):
    """アーカイブ済みアイテムを復元する。"""
    from core.constants import _ARCHIVABLE

    _require_admin(request)
    if kind not in _ARCHIVABLE:
        raise HTTPException(400, f"unknown kind {kind}")
    table = _ARCHIVABLE[kind]
    conn = get_db()
    try:
        row = conn.execute(f"SELECT id FROM {table} WHERE id = ?", (item_id,)).fetchone()
        if not row:
            raise HTTPException(404, f"{kind} not found")
        conn.execute(f"UPDATE {table} SET archived_at = NULL WHERE id = ?", (item_id,))
        _log_audit(conn, f"{kind}_restored", item_id, "")
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "kind": kind, "id": item_id}


@router.delete("/api/archived/{kind}/{item_id}", response_model=None)
async def purge_archived(request: Request, kind: str, item_id: str):
    """アーカイブ済みアイテムを完全削除する。既存DELETE経路に委譲して chunk/Chroma も掃除。"""
    from core.constants import _ARCHIVABLE
    from routers.sources import delete_source
    from routers.workspaces import delete_workspace
    from routers.collections import delete_collection

    _require_admin(request)
    if kind not in _ARCHIVABLE:
        raise HTTPException(400, f"unknown kind {kind}")
    if kind == "source":
        # routers/sources.py の delete_source は (request, source_id) を期待するが
        # 元コードは item_id のみ渡している (元々のバグ互換)。current request を渡す。
        return delete_source(request, item_id)
    if kind == "workspace":
        return delete_workspace(item_id)
    return delete_collection(item_id)
