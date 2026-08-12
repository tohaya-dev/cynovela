"""Pipeline preset + execution-config + chunking-config endpoints."""

from __future__ import annotations

import json as _json

from core.api_schema import parse_body_pydantic
from fastapi import APIRouter, HTTPException, Request

from db import get_db, new_id
from core.auth import _require_admin
from core.audit import _log_audit

router = APIRouter(tags=["pipeline-config"])


# ─── /api/pipeline-presets ───


@router.get("/api/pipeline-presets", response_model=None)
def list_pipeline_presets(request: Request):
    """PHASE UX-1: パイプラインプリセット一覧 (組み込み + ユーザー定義)。"""
    _require_admin(request)
    builtins = [
        {
            "id": "tech_doc",
            "name": "📄 技術文書",
            "description": "技術文書・マニュアル・仕様書向け (Standard モード)",
            "config_json": '{"chunking": "tech_doc", "rag_mode": "standard", "guardrail": "default"}',
            "is_builtin": 1,
        },
        {
            "id": "confidential",
            "name": "🔒 機密文書",
            "description": "PII含む社内文書 (mask + Viewer制限 + Standard)",
            "config_json": '{"chunking": "general", "rag_mode": "standard", "guardrail": "mask"}',
            "is_builtin": 1,
        },
        {
            "id": "personal_memo",
            "name": "📝 個人メモ",
            "description": "日常メモ・議事録 (log_only + Lite)",
            "config_json": '{"chunking": "email_minutes", "rag_mode": "lite", "guardrail": "log_only"}',
            "is_builtin": 1,
        },
        {
            "id": "multimedia",
            "name": "🖼️ マルチメディア",
            "description": "画像・Office 混在 (mlx-vlm 有効)",
            "config_json": '{"chunking": "tech_doc", "rag_mode": "standard", "image_mode": "caption"}',
            "is_builtin": 1,
        },
        {
            "id": "quickstart",
            "name": "⚡ クイックスタート",
            "description": "全部おまかせ初心者向け",
            "config_json": '{"chunking": "tech_doc", "rag_mode": "standard"}',
            "is_builtin": 1,
        },
    ]
    c = get_db()
    try:
        rows = c.execute(
            "SELECT id, name, description, config_json, is_builtin " "FROM pipeline_presets ORDER BY created_at DESC"
        ).fetchall()
    finally:
        c.close()
    return {"builtins": builtins, "user_defined": [dict(r) for r in rows]}


@router.post("/api/pipeline-presets", response_model=None)
async def save_pipeline_preset(request: Request):
    """PHASE UX-1: ユーザープリセットを保存する。"""
    _require_admin(request)
    body = await parse_body_pydantic(request)
    name = (body.get("name") or "").strip()
    if not name:
        raise HTTPException(400, "name は必須です")
    pid = body.get("id") or new_id()
    cfg = body.get("config") or {}
    c = get_db()
    try:
        c.execute(
            "INSERT INTO pipeline_presets (id, name, description, config_json, is_builtin) "
            "VALUES (?, ?, ?, ?, 0) "
            "ON CONFLICT(id) DO UPDATE SET name=excluded.name, "
            "description=excluded.description, config_json=excluded.config_json",
            (pid, name, body.get("description") or "", _json.dumps(cfg, ensure_ascii=False)),
        )
        c.commit()
    finally:
        c.close()
    return {"ok": True, "id": pid}


@router.delete("/api/pipeline-presets/{preset_id}", response_model=None)
def delete_pipeline_preset(request: Request, preset_id: str):
    """PHASE UX-1: ユーザープリセット削除 (組み込みは削除不可)。"""
    _require_admin(request)
    c = get_db()
    try:
        row = c.execute("SELECT is_builtin FROM pipeline_presets WHERE id = ?", (preset_id,)).fetchone()
        if not row:
            raise HTTPException(404, f"preset {preset_id} が見つかりません")
        if int(row["is_builtin"] or 0):
            raise HTTPException(400, "組み込みプリセットは削除できません")
        c.execute("DELETE FROM pipeline_presets WHERE id = ?", (preset_id,))
        c.commit()
    finally:
        c.close()
    return {"ok": True}


# ─── /api/execution-config ───


@router.get("/api/execution-config", response_model=None)
def get_execution_config_api(request: Request):
    """P4-15: 実行モード設定を返す。APIキー類はマスクする。"""
    _require_admin(request)
    from core.config import get_execution_config as _gec, detect_multimodal_environment as _dm

    cfg = _gec()
    mm_raw = cfg.get("multimodal", "off")
    mm_str = "on" if (mm_raw is True or str(mm_raw).lower() in ("on", "true", "1", "yes")) else "off"
    return {
        "llm_provider": cfg.get("llm_provider", "local"),
        "llm_base_url": cfg.get("llm_base_url", ""),
        "openrouter_api_key_set": bool(cfg.get("openrouter_api_key")),
        "claude_api_key_set": bool(cfg.get("claude_api_key")),
        "multimodal": mm_str,
        "vlm_model": cfg.get("vlm_model", ""),
        "environment": _dm(),
    }


@router.patch("/api/execution-config", response_model=None)
async def update_execution_config_api(request: Request):
    """P4-15: 実行モード設定を更新する。"""
    _require_admin(request)
    from core.config import set_runtime_exec_override, get_execution_config as _gec

    body = await parse_body_pydantic(request)
    if not isinstance(body, dict):
        raise HTTPException(400, "オブジェクト形式で指定してください")
    allowed = {
        "llm_provider",
        "llm_base_url",
        "openrouter_api_key",
        "claude_api_key",
        "multimodal",
        "vlm_model",
    }
    if body.get("llm_provider") and body["llm_provider"] not in ("local", "openrouter", "claude_api"):
        raise HTTPException(400, "llm_provider は local / openrouter / claude_api のいずれかを指定してください")
    if body.get("multimodal") and str(body["multimodal"]).lower() not in ("on", "off", "true", "false"):
        raise HTTPException(400, "multimodal は on / off で指定してください")

    conn = get_db()
    try:
        for k, v in body.items():
            if k not in allowed:
                raise HTTPException(400, f"未知のキー: {k}")
            if k == "multimodal":
                v = "on" if str(v).lower() in ("on", "true", "1", "yes") else "off"
            conn.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (f"exec.{k}", "" if v is None else str(v)),
            )
            set_runtime_exec_override(k, v if v is not None else "")
        _log_audit(
            conn,
            "execution_config_updated",
            "",
            ",".join(k for k in body.keys() if k not in ("openrouter_api_key", "claude_api_key")),
        )
        conn.commit()
    finally:
        conn.close()
    cfg = _gec()
    return {
        "llm_provider": cfg.get("llm_provider"),
        "llm_base_url": cfg.get("llm_base_url"),
        "openrouter_api_key_set": bool(cfg.get("openrouter_api_key")),
        "claude_api_key_set": bool(cfg.get("claude_api_key")),
        "multimodal": cfg.get("multimodal"),
        "vlm_model": cfg.get("vlm_model"),
    }


# ─── /api/chunking-config ───


@router.get("/api/chunking-config", response_model=None)
def get_chunking_config(request: Request):
    """フェーズ2: Contextual Chunking 設定の取得。"""
    _require_admin(request)
    from core.config import get_yaml_config as _gyc

    cfg = _gyc().get("chunking") or {}
    conn = get_db()
    try:
        row = conn.execute("SELECT value FROM settings WHERE key = 'chunking.contextual'").fetchone()
    finally:
        conn.close()
    contextual = bool(cfg.get("contextual", False))
    if row is not None:
        contextual = str(row["value"]).lower() in ("1", "true", "yes", "on")
    return {
        "contextual": contextual,
        "chunk_size": int(cfg.get("chunk_size", 300)),
        "chunk_overlap": int(cfg.get("chunk_overlap", 50)),
    }


@router.patch("/api/chunking-config", response_model=None)
async def update_chunking_config(request: Request):
    """フェーズ2: Contextual Chunking ON/OFF をDBに保存し、ランタイムに即反映する。"""
    _require_admin(request)
    body = await parse_body_pydantic(request)
    if not isinstance(body, dict):
        raise HTTPException(400, "object required")
    if "contextual" in body:
        enabled = bool(body["contextual"])
        conn = get_db()
        try:
            _running_jobs = conn.execute(
                "SELECT COUNT(*) FROM publish_jobs WHERE status IN ('pending','running')"
            ).fetchone()[0]
            if _running_jobs > 0:
                conn.close()
                raise HTTPException(409, "Cannot change chunking config while publish is in progress")
            try:
                conn.execute(
                    "INSERT INTO settings (key, value) VALUES (?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                    ("chunking.contextual", "1" if enabled else "0"),
                )
                _log_audit(conn, "chunking_contextual_updated", "", str(enabled))
                conn.commit()
            except HTTPException:
                raise
            except Exception as _db_e:
                # FIX-D1: 500 unhandled → 503 service unavailable へ置換
                import logging as _logging_d1

                _logging_d1.getLogger("cynovela.pipeline_config").exception(f"chunking-config DB 書き込み失敗: {_db_e}")
                raise HTTPException(
                    503,
                    "chunking 設定の保存に失敗しました。時間をおいて再試行してください。",
                )
        finally:
            conn.close()
        try:
            from core.config import get_yaml_config as _gyc

            _y = _gyc()
            _y.setdefault("chunking", {})["contextual"] = enabled
        except Exception:
            pass
    return get_chunking_config(request)
