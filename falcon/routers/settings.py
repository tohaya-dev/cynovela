"""設定系エンドポイント。

server.py から /api/settings/* を段階的に切り出した集約ルーター。
ヘルパー (_validate_llm_endpoint / _get_reranker_top_n) と settings 専用の
mutable state (_data_sync_state) も併せて管理する。
"""

from __future__ import annotations

import os
import re

from core.api_schema import parse_body_pydantic
from fastapi import APIRouter, HTTPException, Request

from db import get_db
from core.auth import _require_admin
from core.llm import get_current_adapter

import state as _state
import vault_enc


router = APIRouter(tags=["settings"])


# ─────────────────────────────────────────────
# 設定系ヘルパー (settings 専用)
# ─────────────────────────────────────────────


def _validate_llm_endpoint(url: str) -> str:
    """STEP 4: SSRF 防止 - llm_endpoint に危険な URL を設定できないようにする"""
    if not isinstance(url, str):
        raise HTTPException(400, "llm_endpoint は文字列である必要があります")
    u = url.strip()
    if not u:
        raise HTTPException(400, "llm_endpoint が空です")
    if not u.startswith(("http://", "https://")):
        raise HTTPException(400, "llm_endpoint は http:// または https:// で始まる必要があります")
    forbidden = [
        (r"^file://", "file:// は使用できません"),
        (r"169\.254\.", "リンクローカル/メタデータアドレスは使用できません"),
        (r"metadata\.google\.internal", "GCP メタデータアドレスは使用できません"),
        (r"^https?://0\.0\.0\.0", "0.0.0.0 は使用できません"),
        (r"^https?://\[?::1?\]?(:|/|$)", "IPv6 ローカルホストは別表記で指定してください"),
        (r"\.amazonaws\.com.*169\.254", "AWS メタデータ参照は使用できません"),
    ]
    for pat, msg in forbidden:
        if re.search(pat, u, re.IGNORECASE):
            raise HTTPException(400, msg)
    return u


def _get_reranker_top_n() -> int:
    try:
        from core.config import CYNOVELA_CONFIG as _cfg

        return int((_cfg.get("reranker") or {}).get("top_n", 5) or 5)
    except Exception:
        return 5


# ─────────────────────────────────────────────
# エンドポイント
# ─────────────────────────────────────────────


@router.get("/api/settings/presets", response_model=None)
def get_settings_presets(request: Request):
    """PHASE S-1: 推奨プリセット定義を返す (フロントエンド ドロップダウン用)。"""
    _require_admin(request)
    return {
        "rag_params": [
            {
                "id": "rag_standard",
                "label": "RAG標準（事実重視）",
                "values": {"temperature": 0.1, "top_p": 0.9, "repeat_penalty": 1.1},
            },
            {
                "id": "balanced",
                "label": "バランス",
                "values": {"temperature": 0.3, "top_p": 0.95, "repeat_penalty": 1.05},
            },
            {
                "id": "creative",
                "label": "創造的回答",
                "values": {"temperature": 0.7, "top_p": 1.0, "repeat_penalty": 1.0},
            },
            {"id": "custom", "label": "カスタム", "values": {}},
        ],
        "chunking": [
            # PHASE UI-5: 12 種のパイプラインプリセット (rag_mode は preset と連動)
            {
                "id": "tech_manual",
                "label": "📖 技術マニュアル",
                "values": {
                    "child_chunk_size": 512,
                    "parent_chunk_size": 1024,
                    "child_chunk_overlap": 64,
                    "bm25_weight": 0.45,
                    "rag_mode": "hq",
                },
            },
            {
                "id": "table_data",
                "label": "📊 表・データ資料",
                "values": {
                    "child_chunk_size": 128,
                    "parent_chunk_size": 256,
                    "child_chunk_overlap": 0,
                    "bm25_weight": 0.55,
                    "rag_mode": "lite",
                },
            },
            {
                "id": "business_doc",
                "label": "📝 ビジネス文書",
                "values": {
                    "child_chunk_size": 256,
                    "parent_chunk_size": 1024,
                    "child_chunk_overlap": 32,
                    "bm25_weight": 0.30,
                    "rag_mode": "standard",
                },
            },
            {
                "id": "communication",
                "label": "💬 コミュニケーション",
                "values": {
                    "child_chunk_size": 128,
                    "parent_chunk_size": 512,
                    "child_chunk_overlap": 16,
                    "bm25_weight": 0.20,
                    "rag_mode": "lite",
                },
            },
            {
                "id": "code_config",
                "label": "💻 コード・設定ファイル",
                "values": {
                    "child_chunk_size": 512,
                    "parent_chunk_size": 2048,
                    "child_chunk_overlap": 64,
                    "bm25_weight": 0.60,
                    "rag_mode": "standard",
                },
            },
            {
                "id": "confidential",
                "label": "🔒 機密・法務文書",
                "values": {
                    "child_chunk_size": 256,
                    "parent_chunk_size": 1024,
                    "child_chunk_overlap": 64,
                    "bm25_weight": 0.35,
                    "rag_mode": "standard",
                },
            },
            {
                "id": "transcript",
                "label": "🎙️ 書き起こし・議事録",
                "values": {
                    "child_chunk_size": 256,
                    "parent_chunk_size": 1024,
                    "child_chunk_overlap": 64,
                    "bm25_weight": 0.20,
                    "rag_mode": "standard",
                },
            },
            {
                "id": "logfile",
                "label": "🪵 ログファイル",
                "values": {
                    "child_chunk_size": 64,
                    "parent_chunk_size": 256,
                    "child_chunk_overlap": 0,
                    "bm25_weight": 0.70,
                    "rag_mode": "lite",
                },
            },
            {
                "id": "structured",
                "label": "🗂️ 構造化データ",
                "values": {
                    "child_chunk_size": 256,
                    "parent_chunk_size": 512,
                    "child_chunk_overlap": 0,
                    "bm25_weight": 0.60,
                    "rag_mode": "lite",
                },
            },
            {
                "id": "mixed",
                "label": "🌐 混在・雑多ファイル",
                "values": {
                    "child_chunk_size": 256,
                    "parent_chunk_size": 1024,
                    "child_chunk_overlap": 32,
                    "bm25_weight": 0.40,
                    "rag_mode": "standard",
                },
            },
            {
                "id": "research_paper",
                "label": "📚 研究論文・学術文書",
                "values": {
                    "child_chunk_size": 384,
                    "parent_chunk_size": 1536,
                    "child_chunk_overlap": 48,
                    "bm25_weight": 0.35,
                    "rag_mode": "hq",
                },
            },
            {
                "id": "quickstart",
                "label": "⚡ クイックスタート",
                "values": {
                    "child_chunk_size": 256,
                    "parent_chunk_size": 1024,
                    "child_chunk_overlap": 32,
                    "bm25_weight": 0.40,
                    "rag_mode": "standard",
                },
            },
            {"id": "custom", "label": "カスタム", "values": {}},
        ],
        "rag_modes": [
            {
                "id": "lite",
                "label": "🚀 パフォーマンス",
                "flags": {
                    "mmr_enabled": False,
                    "multi_query_enabled": False,
                    "crag_enabled": False,
                    "hyde_enabled": False,
                },
            },
            {
                "id": "standard",
                "label": "⚖️ バランス",
                "flags": {
                    "mmr_enabled": True,
                    "multi_query_enabled": True,
                    "crag_enabled": True,
                    "hyde_enabled": False,
                },
            },
            {
                "id": "hq",
                "label": "🎯 品質優先",
                "flags": {"mmr_enabled": True, "multi_query_enabled": True, "crag_enabled": True, "hyde_enabled": True},
            },
        ],
        "reranker_backends": [
            {"id": "none", "label": "無効"},
            {"id": "flashrank", "label": "FlashRank (~75MB)"},
            {"id": "cross_encoder", "label": "SentenceTransformers (~550MB)"},
            {"id": "cohere", "label": "Cohere API (要APIキー)"},
            {"id": "jina", "label": "Jina API (要APIキー)"},
        ],
    }


@router.get("/api/settings/remote-access", response_model=None)
def get_remote_access_info(request: Request):
    """PHASE B-1: 現在のバインドアドレス・ポート・TailScale IP・許可サブネットを返す。"""
    from server import _detect_tailscale_ip

    _require_admin(request)
    cfg = _state.config
    info = {
        "host": cfg.host if cfg else "0.0.0.0",
        "port": cfg.port if cfg else 8765,
        "allow_tailscale": cfg.allow_tailscale if cfg else False,
        "allow_subnets": list(cfg.allow_subnet) if cfg else [],
        "tailscale_ip": _detect_tailscale_ip(),
        "active_allowlist": [str(s) for s in (_state.allowed_subnets or [])],
    }
    info["url_localhost"] = f"http://127.0.0.1:{info['port']}"
    if info["tailscale_ip"]:
        info["url_tailscale"] = f"http://{info['tailscale_ip']}:{info['port']}"
    return info


@router.get("/api/settings", response_model=None)
def get_settings(request: Request):
    _require_admin(request)
    conn = get_db()
    # connleak-fix-20260709: 例外時も必ず close する (接続リークで書き込みロック残留を防ぐ)
    try:
        settings = {}
        for row in conn.execute("SELECT key, value FROM settings").fetchall():
            settings[row["key"]] = row["value"]
    finally:
        conn.close()
    return settings


@router.put("/api/settings", response_model=None)
async def update_settings(request: Request):
    _require_admin(request)
    body = await parse_body_pydantic(request)
    # STEP 4: llm_endpoint 更新時に SSRF バリデーション
    if "llm_endpoint" in body:
        body["llm_endpoint"] = _validate_llm_endpoint(body["llm_endpoint"])
    # PHASE M-2 lm_studio 拡張: 画像モード変更を即座に CYNOVELA_CONFIG に反映する
    from core.config import apply_image_setting as _apply_img

    conn = get_db()
    # connleak-fix-20260709: 例外時も必ず close する (書き込み txn 残留 = "database is locked" を防ぐ)
    try:
        for key, value in body.items():
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, str(value)),
            )
            _apply_img(key, str(value))
        conn.commit()
    finally:
        conn.close()
    return {"ok": True}


@router.get("/api/settings/models", response_model=None)
async def list_models(request: Request):
    _require_admin(request)
    models = await get_current_adapter().list_models()
    return {"data": models}


@router.get("/api/settings/system-prompt", response_model=None)
def get_system_prompt(request: Request):
    from server import _get_effective_system_prompt, DEFAULT_SYSTEM_PROMPT

    _require_admin(request)
    value = _get_effective_system_prompt()
    return {"value": value, "is_default": value == DEFAULT_SYSTEM_PROMPT}


@router.post("/api/settings/system-prompt", response_model=None)
async def save_system_prompt(request: Request):
    from server import DEFAULT_SYSTEM_PROMPT

    _require_admin(request)
    body = await parse_body_pydantic(request)
    value = body.get("value")
    conn = get_db()
    # connleak-fix-20260709: 分岐ごとの手動 close を try/finally に一本化する
    # (例外時の close 漏れ = 書き込み txn 残留 = "database is locked" を防ぐ)
    try:
        if value is None or (isinstance(value, str) and not value.strip()):
            # 空文字または null なら削除（=デフォルトにリセット）
            conn.execute("DELETE FROM settings WHERE key = ?", ("system_prompt",))
            conn.commit()
            return {"value": DEFAULT_SYSTEM_PROMPT, "is_default": True}
        if not isinstance(value, str):
            raise HTTPException(400, "value は文字列である必要があります")
        if "{context}" not in value:
            raise HTTPException(400, "システムプロンプトには {context} プレースホルダーが必要です")
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            ("system_prompt", value),
        )
        conn.commit()
    finally:
        conn.close()
    return {"value": value, "is_default": value == DEFAULT_SYSTEM_PROMPT}


@router.post("/api/settings/test-connection", response_model=None)
async def test_connection(request: Request):
    _require_admin(request)
    # llmprovider-simplify-20260628: 接続テストは保存値ではなく画面の入力値 (provider/base_url/api_key/model)
    #   で一時アダプタを作って叩く。適用前でも OpenRouter+入力トークンで本物の接続テストができ、
    #   「テスト緑なのに一覧だけ空」(保存 LM Studio を叩いていた非対称) を解消する。
    #   一時アダプタは _server._adapter / _state.adapter に代入しない (保存値を汚さない=未適用を保つ)。
    #   ボディに base_url / provider が無い (空 {} など) ときだけ従来どおり保存アダプタにフォールバック。
    try:
        body = await parse_body_pydantic(request)
    except Exception:
        body = None
    if isinstance(body, dict) and (body.get("base_url") or body.get("provider")):
        from server import get_llm_adapter

        provider = body.get("provider", "lmstudio")
        base_url = _validate_llm_endpoint(body.get("base_url", "http://localhost:1234"))
        model = body.get("model", "") or ""
        api_key = body.get("api_key", "") or ""
        if api_key == "****":
            api_key = ""
        # クラウド (openai_compat) で鍵欄が空 (マスク '****' 未編集) のときは、保存済み暗号トークンを
        #   復号して当回のテストに使う (適用後の再テストでも緑になる)。適用経路と同じ vault_enc。
        if provider == "openai_compat" and not api_key:
            try:
                _c0 = get_db()
                try:
                    _r0 = _c0.execute("SELECT value FROM settings WHERE key = 'llm_api_key_enc'").fetchone()
                finally:
                    _c0.close()
                if _r0 and _r0[0]:
                    api_key = vault_enc.dec_raw(_r0[0]) or ""
            except Exception:
                pass
        adapter = get_llm_adapter(base_url=base_url, provider=provider, model=model, api_key=api_key)
        result = await adapter.test_connection()
        # 実際に叩いた宛先を返却に含める (実宛先 openrouter かどうかを画面で確認できるように)。
        try:
            if isinstance(result, dict):
                result.setdefault("endpoint", f"{base_url}/v1")
        except Exception:
            pass
        return result
    return await get_current_adapter().test_connection()


@router.get("/api/settings/llm", response_model=None)
def get_llm_settings(request: Request):
    """現在のLLM設定を返す。api_key は値ではなく is_set フラグのみ。"""
    import server as _server
    from server import MockAdapter, OpenAICompatibleAdapter
    # provider-default-url-20260627: コンテナ対応の既定 Base URL を単一定義から取得し、追加フィールド
    #   default_base_url で返す。フロントのプロバイダー選択時の自動入力(B-2)が二重ハードコードせず共有する。
    from core.llm import default_llm_endpoint as _dle
    _default_base_url = _dle()

    _require_admin(request)
    a = _server._adapter
    if isinstance(a, MockAdapter):
        return {"provider": "mock", "base_url": "mock://localhost", "model": "mock-model", "api_key_set": False, "default_base_url": _default_base_url}
    if isinstance(a, OpenAICompatibleAdapter):
        return {
            "provider": "openai_compat",
            "base_url": a.base_url,
            "model": a.model,
            "api_key_set": bool(a.api_key),
            "default_base_url": _default_base_url,
        }
    # fix-llm-endpoint-unify-20260618: 起動時キャッシュ _server._adapter ではなく、
    # 実効 endpoint (DB settings.llm_endpoint = get_current_adapter().base_url) を表示し、
    # Base URL 表示 (②) を接続テスト/モデル一覧と同じ実効値に一本化する (コンテナでは host.containers.internal)。
    try:
        from core.llm import get_current_adapter as _gca

        base_url = getattr(_gca(), "base_url", None) or getattr(a, "base_url", "http://localhost:1234")
    except Exception:
        base_url = getattr(a, "base_url", "http://localhost:1234")
    # fix061 A2: LM Studio adapter の現在モデル名を返す (空文字列回避)。
    # 優先順: adapter.model 属性 → settings DB の llm_model → "auto" 既定値。
    _model = getattr(a, "model", None)
    if not _model:
        try:
            _conn = get_db()
            # connleak-fix-20260709: 例外時も必ず close する (外側 except は握り潰しのため内側で保証)
            try:
                _row = _conn.execute("SELECT value FROM settings WHERE key = ?", ("llm_model",)).fetchone()
            finally:
                _conn.close()
            _model = _row["value"] if _row and _row["value"] else "auto"
        except Exception:
            _model = "auto"
    # fix2-A: 永続化された provider を DB から反映 (再起動後も保持を表示)。
    #         in-session の openai_compat 等は上の早期 return で拾われ、再起動後はこの分岐で DB を読む。
    # fix2-v4-A: api_key は DB/環境変数に保存しないため、有無は現在の RAM 上 adapter からのみ判定する
    #         (セッション限定: 再起動後は未設定表示になるのが正しい挙動)。
    _provider = "lmstudio"
    _api_key_set = bool(getattr(_state.adapter, "api_key", ""))
    # token-persist-fix-20260628: 再起動後 _state.adapter に鍵が無くても、保存済み暗号トークン
    #   (llm_api_key_enc) があれば「設定済み」を正直に返す (生鍵は返さない・有無のみ)。
    if not _api_key_set:
        try:
            _cg = get_db()
            try:
                _rg = _cg.execute("SELECT value FROM settings WHERE key = 'llm_api_key_enc'").fetchone()
            finally:
                _cg.close()
            _api_key_set = bool(_rg and _rg[0])
        except Exception:
            pass
    try:
        _conn2 = get_db()
        # connleak-fix-20260709: 例外時も必ず close する (同関数上方の _cg と同型の内側 try/finally)
        try:
            _rows2 = {
                r["key"]: r["value"]
                for r in _conn2.execute(
                    "SELECT key, value FROM settings WHERE key = 'llm_provider'"
                ).fetchall()
            }
        finally:
            _conn2.close()
        _provider = _rows2.get("llm_provider") or "lmstudio"
    except Exception:
        pass
    return {"provider": _provider, "base_url": base_url, "model": _model, "api_key_set": _api_key_set, "default_base_url": _default_base_url}


@router.get("/api/settings/reranker", response_model=None)
def get_reranker_settings(request: Request):
    from server import get_reranker_provider_current

    _require_admin(request)
    p = get_reranker_provider_current()
    cls = type(p).__name__
    info = {
        "provider": "none",
        "model": getattr(p, "model_name", getattr(p, "model", "")),
        "base_url": getattr(p, "base_url", ""),
        "api_key_set": bool(getattr(p, "api_key", "")),
        "top_n": _get_reranker_top_n(),
    }
    if cls == "CrossEncoderReranker":
        info["provider"] = "cross_encoder"
    elif cls == "MLXReranker":
        info["provider"] = "mlx"
    elif cls == "OllamaReranker":
        info["provider"] = "ollama"
    elif cls == "CohereReranker":
        info["provider"] = "cohere"
    elif cls == "JinaReranker":
        info["provider"] = "jina"
    elif cls == "VoyageReranker":
        info["provider"] = "voyage"
    elif cls == "OpenAICompatibleReranker":
        info["provider"] = "openai_compat"
        info["base_url"] = getattr(p, "api_url", "").replace("/v1/rerank", "")
    elif cls == "HttpReranker":
        info["provider"] = "http_tei"
        info["base_url"] = getattr(p, "endpoint", "")
    elif cls == "ExternalAcceleratorReranker":
        info["provider"] = "external_accelerator"
    # ga-finish-20260727: 再ランクの実行場所と退避状態を返す (埋め込みの mas-status と同型)。
    #   execution: external (外部の推論サーバ) / in_process (本体内) / none (再ランクなし)
    #   fallback: 外部の推論サーバへ届かず退避が起きているか (target = 実際の退避経路)
    try:
        from providers.reranker import get_rerank_fallback_state as _grfs

        info["fallback"] = _grfs()
    except Exception:
        info["fallback"] = {"active": False}
    if info["provider"] == "external_accelerator":
        _fb = info.get("fallback") or {}
        if _fb.get("active"):
            info["execution"] = "in_process" if "in-process" in (_fb.get("target") or "") else "none"
        else:
            info["execution"] = "external"
        if info.get("base_url"):
            try:
                import httpx as _httpx

                _hr = _httpx.get(f"{info['base_url']}/health", timeout=2.0)
                info["accelerator"] = {"reachable": _hr.status_code == 200}
                if _hr.status_code == 200:
                    try:
                        info["accelerator"]["detail"] = _hr.json()
                    except Exception:
                        pass
            except Exception as _hex:
                info["accelerator"] = {"reachable": False, "error": str(_hex)}
    elif info["provider"] == "none":
        info["execution"] = "none"
    else:
        info["execution"] = "in_process"
    return info


@router.post("/api/settings/reranker", response_model=None)
async def update_reranker_settings(request: Request):
    from server import get_reranker_provider, set_reranker_provider

    _require_admin(request)
    body = await parse_body_pydantic(request)
    cfg = {
        "reranker": {
            "provider": body.get("provider", "none"),
            "model": body.get("model", ""),
            "base_url": body.get("base_url", ""),
            # ga-finish-20260727: 外部の推論サーバ (external/external_accelerator) への切替は埋め込みと
            # 同じ device キーで受ける (provider=external_accelerator も同義)。
            "device": body.get("device", ""),
            "api_key": body.get("api_key", ""),  # DD-CYN-0067 G-2: env バックアップを撤去
            "top_n": int(body.get("top_n", 5) or 5),
        }
    }
    new = get_reranker_provider(cfg)
    set_reranker_provider(new)
    # Phase F: メモリ上の CYNOVELA_CONFIG にも反映（プロセス内永続化）
    try:
        from core.config import CYNOVELA_CONFIG as _cfg

        _cfg.setdefault("reranker", {}).update(cfg["reranker"])
    except Exception:
        pass
    return {
        "ok": True,
        "provider": cfg["reranker"]["provider"],
        "model": cfg["reranker"]["model"],
        "top_n": cfg["reranker"]["top_n"],
    }


@router.post("/api/settings/reranker/test", response_model=None)
async def test_reranker_connection(request: Request):
    """Stage R5-fix P1 #15: admin 限定."""
    from core.auth import _require_admin
    from server import get_reranker_provider_current

    _require_admin(request)
    return await get_reranker_provider_current().test_connection()


@router.get("/api/settings/classifier", response_model=None)
def get_classifier_settings(request: Request):
    """Stage R5-fix P1 #15: admin 限定."""
    from core.auth import _require_admin

    _require_admin(request)
    import server as _server
    from server import APIClassifier

    p = _server._classifier
    if isinstance(p, APIClassifier):
        return {"provider": "api", "api_url": p.api_url, "api_key_set": bool(p.api_key)}
    return {"provider": "rule_based", "api_key_set": False}


@router.post("/api/settings/classifier", response_model=None)
async def update_classifier_settings(request: Request):
    from core.auth import _require_admin

    _require_admin(request)
    import server as _server
    from server import get_classifier_provider

    body = await parse_body_pydantic(request)
    cfg = {
        "classifier": {
            "provider": body.get("provider", "rule_based"),
            "api_url": body.get("api_url", ""),
            "api_key": body.get("api_key", ""),  # DD-CYN-0067 G-2: env バックアップを撤去
        }
    }
    _server._classifier = get_classifier_provider(cfg)
    return {"ok": True, "provider": cfg["classifier"]["provider"]}


@router.get("/api/settings/pii-mode", response_model=None)
def get_pii_mode(request: Request):
    """Stage R5-fix P1 #15: admin 限定."""
    from core.auth import _require_admin

    _require_admin(request)
    try:
        from utils.metadata.pii import get_pii_detection_mode

        return {"mode": get_pii_detection_mode()}
    except Exception:
        # フォールバック: yamlから直接読む
        try:
            import yaml as _yaml
            from pathlib import Path as _P

            _yaml_path = _P(__file__).resolve().parent.parent / "cynovela.yaml"
            with open(_yaml_path, "r", encoding="utf-8") as f:
                _cfg = _yaml.safe_load(f) or {}
            return {"mode": _cfg.get("pii_mode", "standard")}
        except Exception:
            return {"mode": "standard"}


@router.put("/api/settings/pii-mode", response_model=None)
async def set_pii_mode(request: Request):
    from server import logger

    _require_admin(request)
    body = await parse_body_pydantic(request)
    mode = (body.get("mode") or "standard").strip()
    # pii-mode-two-tier-20260727: 旧 quality は standard と同一の挙動しか無く、受理しても
    # 何も変わらないまま 200 を返していた。区別できる2種だけを受理する。
    if mode not in ("lite", "standard"):
        raise HTTPException(400, "mode は lite / standard のいずれか")
    try:
        from utils.metadata.pii import set_pii_detection_mode

        set_pii_detection_mode(mode)
        # cynovela.yaml の pii_mode キーに永続化（次回起動でも反映）
        try:
            import yaml as _yaml
            from pathlib import Path as _P

            _yaml_path = _P(__file__).resolve().parent.parent / "cynovela.yaml"
            if _yaml_path.exists():
                with open(_yaml_path, "r", encoding="utf-8") as f:
                    _cfg = _yaml.safe_load(f) or {}
                _cfg["pii_mode"] = mode
                with open(_yaml_path, "w", encoding="utf-8") as f:
                    _yaml.safe_dump(_cfg, f, allow_unicode=True, sort_keys=False)
        except Exception as _ye:
            logger.warning(f"pii_mode yaml persist failed (continue): {_ye}")
        return {"mode": mode, "status": "ok"}
    except Exception as e:
        raise HTTPException(500, f"mode設定失敗: {e}")


@router.get("/api/settings/vector-store", response_model=None)
def get_vector_store_settings(request: Request):
    import server as _server
    from server import QdrantVectorStore

    _require_admin(request)
    p = _server._vector_store
    if isinstance(p, QdrantVectorStore):
        return {"provider": "qdrant", "url": p.url, "api_key_set": bool(p.api_key)}
    return {"provider": "chromadb", "path": getattr(p, "path", "")}


@router.post("/api/settings/vector-store", response_model=None)
async def update_vector_store_settings(request: Request):
    import server as _server
    from server import get_vector_store_provider

    _require_admin(request)
    body = await parse_body_pydantic(request)
    provider = body.get("provider", "chromadb")
    cfg = {
        "vector_store": {
            "provider": provider,
            "path": body.get("path", ""),
            "qdrant_url": body.get("qdrant_url", "http://localhost:6333"),
            "qdrant_api_key": body.get("qdrant_api_key", ""),  # DD-CYN-0067 G-2: env バックアップを撤去
        }
    }
    _server._vector_store = get_vector_store_provider(cfg)
    return {"ok": True, "provider": provider, "warning": "既存データの再Publishが必要になります"}


@router.get("/api/settings/embedding", response_model=None)
def get_embedding_settings(request: Request):
    """現在のEmbedding Provider設定を返す。"""
    from server import get_embedding_provider_current

    _require_admin(request)
    p = get_embedding_provider_current()
    cls_name = type(p).__name__
    # DD-CYN-0020 U-4: モデル名の読み手は rag._current_embedding_model_name() に一本化した。
    #   ここで属性を直に読むと、外出し (openai_compat) の属性名の違いを各所で書き直すことになり、
    #   実際に画面の設定欄と開発者パネルで名前が食い違っていた。
    from rag import _current_embedding_model_name as _emb_model_name

    info = {
        "provider": "local",
        "model": _emb_model_name(),
        "base_url": getattr(p, "base_url", ""),
        "api_key_set": bool(getattr(p, "api_key", "")),
    }
    if cls_name == "MLXEmbeddingProvider":
        info["provider"] = "mlx"
    elif cls_name == "OpenAICompatibleEmbeddingProvider":
        info["provider"] = "openai_compat"
    # mas-status-20260725: 外部の推論サーバ (Mac Accelerator Service) の稼働状態と退避状態を返す。
    #   退避が起きたら黙って遅くならず画面に出すための供給元。
    try:
        import rag as _rag
        info["fallback"] = _rag.get_embedding_fallback_state()
        info["local_device"] = getattr(_rag, "_EF_DEVICE_SELECTED", None)
        # §9-4: インデックスの埋め込み識別との整合状態 (起動時/公開時に検査済みの値)
        info["identity"] = _rag.get_embedding_identity_state()
    except Exception:
        info["fallback"] = {"active": False}
        info["local_device"] = None
    if info["provider"] == "openai_compat" and info.get("base_url"):
        try:
            import httpx as _httpx
            _hr = _httpx.get(f"{info['base_url']}/health", timeout=2.0)
            info["accelerator"] = {"reachable": _hr.status_code == 200}
            if _hr.status_code == 200:
                try:
                    info["accelerator"]["detail"] = _hr.json()
                except Exception:
                    pass
        except Exception as _hex:
            info["accelerator"] = {"reachable": False, "error": str(_hex)}
    return info


@router.post("/api/settings/embedding", response_model=None)
async def update_embedding_settings(request: Request):
    from server import get_embedding_provider, set_embedding_provider

    _require_admin(request)
    body = await parse_body_pydantic(request)
    provider = body.get("provider", "local")
    model = body.get("model", "") or ""
    base_url = body.get("base_url", "") or ""
    api_key = body.get("api_key", "")  # DD-CYN-0067 G-2: env バックアップを撤去
    cfg = {
        "embedding": {
            "provider": provider,
            "model": model,
            "base_url": base_url,
            "api_key": api_key,
        }
    }
    new_provider = get_embedding_provider(cfg)
    set_embedding_provider(new_provider)
    # DD-CYN-0066 F-6: ここは差し替えた口を RAM に載せるだけで、どこにも書いていなかった。
    #   ∴ 画面から外の埋め込みの口を変えても、起動し直すと設定ファイルの値へ戻っていた。
    #   LLM の受け口 (update_llm_settings) と同じ書き方で settings 表へ残す。
    #   api_key は残さない (fix2-v4-A と同じ扱い。このセッションの RAM にだけ持つ)。
    conn = get_db()
    try:
        for _k, _v in (
            ("embedding_provider", provider or "local"),
            ("embedding_model", model),
            ("embedding_base_url", base_url),
        ):
            conn.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (_k, _v),
            )
        conn.commit()
    finally:
        conn.close()
    return {
        "ok": True,
        "provider": provider,
        "model": model,
        "base_url": base_url,
        "api_key_set": bool(api_key),
        "persisted": True,
        "warning": "既存ChromaDB Collectionは旧モデルで埋め込み済みです。再Publishを推奨します。",
    }


_EMBEDDING_RESTORED = False


def _restore_embedding_from_db() -> None:
    """DD-CYN-0066 F-6: 起動時に、画面で決めた埋め込みの口を settings 表から戻す。

    埋め込みの口は rag.py の読み込み時に設定ファイル (CYNOVELA_CONFIG) から作られる。
    画面での変更をそこへ届ける道が無かったため、起動し直すたびに設定ファイルの値へ
    戻っていた。ここでアプリの立ち上がりに 1 度だけ読み直して差し替える。

    保存されている値が 1 件も無ければ何もしない (設定ファイルの値がそのまま残る)。
    api_key は保存していないので、外部の推論サーバに鍵が要る構成では画面から入れ直す
    (この扱いは LLM 側と同じである)。読めない・作れないときは黙って設定ファイル側の
    ままにする。ここで落ちるとアプリが立ち上がらなくなるためである。

    立ち上がりの合図は 2 度届くことがある (実測: FastAPI 0.139.2 で
    include_router 経由の startup handler が 2 回呼ばれる)。差し替えは何度やっても
    同じ結果だが、記録に同じ行を 2 度出さないよう 1 度で止める。
    """
    global _EMBEDDING_RESTORED
    if _EMBEDDING_RESTORED:
        return
    _EMBEDDING_RESTORED = True
    try:
        from server import get_embedding_provider, set_embedding_provider  # noqa: PLC0415

        conn = get_db()
        try:
            rows = conn.execute(
                "SELECT key, value FROM settings "
                "WHERE key IN ('embedding_provider','embedding_model','embedding_base_url')"
            ).fetchall()
        finally:
            conn.close()
        saved = {r[0]: r[1] for r in rows}

        # DD-CYN-0088 §6-A: 実行エンジンは設定ファイル (cynovela.yaml) の embedding の節とし、
        # バックアップの表は「画面で決めた分だけ」その上に重ねる。
        #   以前はこの3鍵だけで cfg を組み立て直していたため、設定ファイルにしか無い
        #   device の鍵が落ちていた。providers/embedding.py は device を先に見て
        #   外部の推論サーバ (外部アクセラレータ) を選ぶ作りなので、device が無いと選ばれず、
        #   埋め込みが黙って CPU の口へ落ちる。退避ではないため画面にも警告が出ない。
        try:
            from core.config import CYNOVELA_CONFIG as _BASE_CFG  # noqa: PLC0415
        except Exception:  # noqa: BLE001
            _BASE_CFG = {}
        base = dict(((_BASE_CFG or {}).get("embedding") or {}))
        cfg_emb = dict(base)
        origin = {_k: "設定ファイル" for _k in cfg_emb}

        # バックアップの値が空、または既定を意味する値のときは重ねない。
        #   'default' は db.py の init_db が embedding_model へ最初に書き込む値であって、
        #   画面で決めた値ではない。重ねるとモデル名が文字列 'default' に化ける。
        _UNSET = ("", "default", "auto", "none", "null")
        _MAP = (
            ("embedding_provider", "provider"),
            ("embedding_model", "model"),
            ("embedding_base_url", "base_url"),
        )
        for _dbkey, _cfgkey in _MAP:
            if _dbkey not in saved:
                continue
            _val = saved.get(_dbkey)
            _val = "" if _val is None else str(_val).strip()
            if _val.lower() in _UNSET:
                continue
            cfg_emb[_cfgkey] = _val
            origin[_cfgkey] = "バックアップ"

        _overlaid = [_k for _k in origin if origin[_k] == "バックアップ"]
        if not _overlaid:
            # 画面で決めた値が1つも無い。設定ファイルの口をそのまま使う。
            # ここで作り直すと、同じ口をもう一度作るだけで得が無い。
            print(
                "[embedding] バックアップに画面で決めた値はありません。設定ファイルの口をそのまま使います "
                f"(provider={base.get('provider', '')} device={base.get('device', '')} "
                f"model={base.get('model', '')} base_url={base.get('base_url', '')})"
            )
            return

        # 画面から供給元そのものを選び直していたときだけ、実行エンジンの device を外す。
        #   device は providers/embedding.py で provider より先に効くため、外さないと
        #   画面で選び直した供給元が無視される。選び直していないときは device を残す。
        if origin.get("provider") == "バックアップ" and cfg_emb.get("provider") != base.get("provider"):
            cfg_emb.pop("device", None)
            origin["device"] = "画面で供給元を選び直したため外しました"

        cfg_emb.setdefault("api_key", base.get("api_key", "") or "")
        cfg = {"embedding": cfg_emb}
        set_embedding_provider(get_embedding_provider(cfg))
        print(
            "[embedding] 埋め込みの口を決めました "
            + " ".join(
                "%s=%r<-%s" % (_k, cfg_emb.get(_k, ""), origin.get(_k, "設定ファイル"))
                for _k in ("provider", "device", "model", "base_url")
            )
        )
    except Exception as _e:  # noqa: BLE001
        print(f"[embedding] バックアップからの復元は行いませんでした: {_e}")


router.add_event_handler("startup", _restore_embedding_from_db)


# ─────────────────────────────────────────────
# Chunk 3: LLM(POST) / DataSync
# ─────────────────────────────────────────────


@router.post("/api/settings/llm", response_model=None)
async def update_llm_settings(request: Request):
    """LLM設定を動的更新。api_key はフォーム入力のみ (このセッションのRAM上の adapter に保持し、
    DB・設定ファイル・環境変数には一切保存しない)。"""
    import server as _server
    from server import get_llm_adapter

    _require_admin(request)
    body = await parse_body_pydantic(request)
    provider = body.get("provider", "lmstudio")
    base_url = body.get("base_url", "http://localhost:1234")
    # STEP 4: SSRF 防止
    base_url = _validate_llm_endpoint(base_url)
    model = body.get("model", "") or ""
    # fix2-v4-A: api_key はフォーム入力のみ (環境変数からは参照しない・セッション限定)。
    api_key = body.get("api_key", "") or ""
    # token-persist-fix-20260628: api_key 欄を送ったか否かで「設定/削除」と「保持」を分ける。
    _key_provided = "api_key" in body
    if provider == "openai_compat" and not _key_provided:
        # 未送信=保持。保存済み暗号トークンを復号して当セッション adapter に載せ直す
        #   (model 等だけ変えて適用したとき RAM 上トークンを落とさないため)。
        try:
            _c0 = get_db()
            try:
                _r0 = _c0.execute("SELECT value FROM settings WHERE key = 'llm_api_key_enc'").fetchone()
            finally:
                _c0.close()
            if _r0 and _r0[0]:
                api_key = vault_enc.dec_raw(_r0[0]) or ""
        except Exception:
            pass
    new_adapter = get_llm_adapter(
        base_url=base_url,
        provider=provider,
        model=model,
        api_key=api_key,
    )
    _server._adapter = new_adapter
    _state.adapter = new_adapter  # state との同期（既存バグ修正）
    # F1: get_current_adapter() / chat 経路が参照する DB キー (llm_endpoint / llm_model) に永続化する。
    #     従来 POST は DB を更新しておらず、LMStudio 型アダプターでは次の chat 要求で
    #     get_current_adapter() が settings.llm_endpoint を読み直して巻き戻していたため、
    #     プロバイダー切替（例: LM Studio → Ollama）が実効反映されなかった。
    _final_key_set = False
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            ("llm_endpoint", base_url),
        )
        if model:
            conn.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                ("llm_model", model),
            )
        # fix2-A: provider を DB に永続化 (従来 RAM のみ→再起動で LM Studio に縮退していた)。
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            ("llm_provider", provider or "lmstudio"),
        )
        # fix2-v4-A: api_key は DB に永続化しない (セッション限定: RAM 上の adapter にのみ保持)。
        #         万一以前の版が保存していた llm_api_key が残っていれば併せて掃除する。
        conn.execute("DELETE FROM settings WHERE key = 'llm_api_key'")
        # token-persist-fix-20260628: クラウド(openai_compat=OpenRouter)のトークンは既存金庫で
        #   暗号化し llm_api_key_enc に1行保存(平文は保存しない)。空送信=削除/provider切替=削除。
        if provider == "openai_compat":
            if _key_provided:
                if api_key:
                    conn.execute(
                        "INSERT INTO settings (key, value) VALUES (?, ?) "
                        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                        ("llm_api_key_enc", vault_enc.enc_raw(api_key)),
                    )
                else:
                    conn.execute("DELETE FROM settings WHERE key = 'llm_api_key_enc'")
            # 未送信=保持: enc 行はそのまま
        else:
            conn.execute("DELETE FROM settings WHERE key = 'llm_api_key_enc'")
        conn.commit()
        _rf = conn.execute("SELECT value FROM settings WHERE key = 'llm_api_key_enc'").fetchone()
        _final_key_set = bool(_rf and _rf[0]) and (provider == "openai_compat")
    finally:
        conn.close()
    return {
        "ok": True,
        "provider": provider,
        "base_url": base_url,
        "model": model,
        "api_key_set": _final_key_set,
    }


# ─── BLOCK D: DataSync 制御 ───


# ─── DataSync state ───
_data_sync_state: dict = {"enabled": False, "interval_sec": 60}


@router.get("/api/settings/datasync", response_model=None)
def get_datasync_settings(request: Request):
    _require_admin(request)
    return dict(_data_sync_state)


@router.post("/api/settings/datasync", response_model=None)
async def update_datasync_settings(request: Request):
    _require_admin(request)
    body = await parse_body_pydantic(request)
    enable = bool(body.get("enabled", False))
    interval = int(body.get("interval_sec", _data_sync_state["interval_sec"]) or 60)
    _data_sync_state["enabled"] = enable
    _data_sync_state["interval_sec"] = max(10, interval)
    # 開始 / 停止
    from db import DB_PATH
    from services.data_sync import start_service, stop_service

    try:
        if enable:
            await start_service(DB_PATH, _data_sync_state["interval_sec"])
        else:
            await stop_service()
    except Exception as e:
        return {"ok": False, "error": str(e), **_data_sync_state}
    return {"ok": True, **_data_sync_state}
