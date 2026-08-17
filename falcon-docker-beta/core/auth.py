"""認証ヘルパー。

server.py から以下を切り出した:
- get_user_from_token: Authorization ヘッダーからユーザーを解決
- _audit_auth_failure: 認証/認可失敗を audit_logs に記録
- _require_admin: 管理者APIで使用（demo bypass 対応）

_state.config 経由で demo bypass を判定する。
mutable session 辞書は state.sessions に集約。
"""

from __future__ import annotations

import jwt as _pyjwt

from fastapi import HTTPException, Request

import config
from db import get_db

import state as _state
from core.audit import _log_audit, set_audit_actor


def _remember_audit_actor(request: Request, user: dict | None) -> None:
    """ga-close-v3 PartB (B-1): 認証が済んだ時点で「誰が・どこから」を実行文脈に置く。

    以降 `_log_audit()` が、呼出側の明示指定が無い欄をこれで埋める。
    権限判定・監査の判定ロジックには一切関与しない (失敗してもサイレント継続)。
    """
    try:
        set_audit_actor(
            user_id=(user or {}).get("id") or (user or {}).get("user_id"),
            ip_address=(request.client.host if getattr(request, "client", None) else None),
        )
    except Exception:
        pass


# 認証不要 EP の正本集合。`server.py` の custom_openapi() で
# 「この path には 401/403 を documented に注入しない」判定に使う。
# `tests/test_schemathesis.py` も同集合を import して PUBLIC_PATHS として参照する（重複定義回避）。
# 追加・削除は本ファイルで一元管理する。
PUBLIC_PATHS: frozenset[str] = frozenset({
    # health (5)
    "/api/health",
    "/api/health/db",
    "/api/health/vector",
    "/api/health/guardrails",
    "/api/health/detailed",
    # auth: login / logout は schemathesis 上 unauthenticated 扱い
    "/api/auth/login",
    "/api/auth/logout",
    # demo / mode
    "/api/demo/role-switch",
    "/api/mode",
    # 一部 GET 系（POST/PUT は admin だが GET は public）
    "/api/sessions",
    "/api/pii-detections",
    "/api/guardrails/blocked-topics",
    "/api/cost/estimate",
    "/api/llm/list-models",
    "/api/settings/classifier",
    "/api/settings/pii-mode",
    "/api/settings/reranker/test",
    # 静的・ドキュメント
    "/",
    "/chat-popup",
    "/openapi.json",
    "/docs",
    "/docs/oauth2-redirect",
    "/redoc",
})


def get_user_from_token(request: Request) -> dict | None:
    """Extract user from Authorization header.
    Supported token format:
    - 'Bearer {hex32}': state.sessions から引く

    fix-security-batch-v2 (2026-05-28) Sub-2G-1 (CRIT-3): 削除済み (is_active=0) ユーザーの
    トークン継続利用を防ぐため、DB 取得後に is_active チェックを追加。
    is_active=0 のときは None を返し、呼出側 (_require_admin/_require_authenticated) で 401 が発火する。

    C-B5 (2026-07-29): 固定トークン受理経路 'Bearer demo-token-{user_id}' を封鎖した。
    従来は --demo 起動時に限り、後続文字列を users.id として引き当てて認証を通していたため、
    配布パッケージの既定である --demo 起動では demo-token-user-admin だけで管理者APIに
    到達できた（実測: GET/POST /api/settings/llm が 200）。パスワードを知らない相手に
    管理者権限が渡るため、--demo 起動であっても受理しない。
    正規の認証経路は /api/auth/login が発行する JWT のみ。
    """
    auth = request.headers.get("Authorization", "")
    # C-B5: demo-token-* は起動形態によらず一律拒否（--demo でも通さない）
    if auth.startswith("Bearer demo-token-"):
        return None
    if auth.startswith("Bearer "):
        token = auth[7:]
        sess = _state.sessions.get(token)
        if sess:
            conn = get_db()
            try:
                user = conn.execute(
                    "SELECT * FROM users WHERE id = ? AND COALESCE(is_active, 1) = 1",
                    (sess["user_id"],),
                ).fetchone()
            finally:
                conn.close()
            if user:
                _remember_audit_actor(request, dict(user))
                return dict(user)
            # 削除済みユーザーのトークンは state.sessions からも除去 (housekeeping)
            _state.sessions.pop(token, None)
    return None


def _get_jwt_secret() -> str:
    """JWT 署名シークレット。金庫（Fernet）の鍵とは別実体の署名専用鍵を参照する。
    事実19追補(K8s幹 3616e2e 相当): 公知フォールバック文字列を撤去し fail-closed 化。
    鍵不在時は config 側が暗号乱数で生成・永続化するため「鍵なし署名」は発生しない。
    auth.py 側に新規 env 読みは追加しない（config の既存解決結果を消費するのみ）。

    part6-20260726（二役分離）: 参照先を config._KEY（金庫鍵）から
    config._JWT_SIGNING_KEY（署名専用鍵・<CYNOVELA_DATA_DIR>/db/jwt/secret.key）へ移した。
    2026-07-05 に一鍵二役へ寄せた際の残件の実施であり、公知フォールバックは復活させない
    （署名鍵が無いときは config 側が暗号乱数で生成・chmod 600 する。金庫鍵と同じ作り）。
    署名鍵を替えても金庫の中身（暗号文）とパスワード再発行の経路には影響しない。
    """
    key = config._JWT_SIGNING_KEY
    return key.decode() if isinstance(key, bytes) else key


def _audit_auth_failure(request: Request, reason: str) -> None:
    """認証/認可失敗を audit_logs に記録する。失敗自体はサイレントに継続。"""
    try:
        ip = request.client.host if request.client else None
        path = str(getattr(request, "url", "")) if request else ""
        conn = get_db()
        try:
            _log_audit(
                conn,
                "auth_failed",
                target=path,
                detail=f'{{"reason": "{reason}"}}',
                ip_address=ip,
                result="failure",
                category="security",
            )
        finally:
            conn.close()
    except Exception:
        pass


def _require_admin(request: Request) -> dict:
    """管理者APIで使用。Batch-B S1-3: JWT 対応のため _require_authenticated 経由に統一。"""
    user = _require_authenticated(request)
    if user.get("role") != "admin":
        _audit_auth_failure(request, "admin_required")
        raise HTTPException(403, "管理者権限が必要です")
    # must-change-gate (pre-ga-fix-all-20260720): 初回パスワード変更が必要な管理者は、変更を済ませるまで
    # 管理操作を通さない (配布物の固定初期PW対策・「変更以外の操作を通さない」)。change-password は
    # _require_authenticated 経由なので本ゲートを通らず変更できる。must_change=0 の稼働/テストは無影響。
    if user.get("must_change_password"):
        raise HTTPException(403, "初回パスワードの変更が必要です。パスワードを変更してから操作してください。")
    return user


def _require_authenticated(request: Request) -> dict:
    """Batch-B S1-3: JWT トークンを検証する。

    返却 dict は user 行全体に加え `user_id` キーを含める（既存呼び出し元との互換性維持）。

    C-B5 (2026-07-29): demo-token-* の後方互換受理を撤去した（--demo 起動でも受理しない）。
    """
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        _audit_auth_failure(request, "unauthenticated")
        raise HTTPException(401, "認証が必要です")
    token = auth[7:]

    # C-B5: demo-token-* は起動形態によらず 401（固定トークンでの到達を封鎖）
    if token.startswith("demo-token-"):
        _audit_auth_failure(request, "demo_token_rejected")
        raise HTTPException(401, "認証が必要です")

    # JWT 形式（`xxx.yyy.zzz`）の検証
    if token.count(".") == 2:
        try:
            payload = _pyjwt.decode(
                token, _get_jwt_secret(), algorithms=["HS256"]
            )
        except _pyjwt.ExpiredSignatureError:
            _audit_auth_failure(request, "token_expired")
            raise HTTPException(401, "Token expired")
        except _pyjwt.InvalidTokenError:
            _audit_auth_failure(request, "invalid_token")
            raise HTTPException(401, "Invalid token")
        from db import get_db as _get_db
        conn = _get_db()
        try:
            row = conn.execute(
                "SELECT * FROM users WHERE id = ? AND COALESCE(is_active, 1) = 1",
                (payload["sub"],),
            ).fetchone()
        finally:
            conn.close()
        if not row:
            _audit_auth_failure(request, "user_deactivated")
            raise HTTPException(401, "User deactivated")
        result = dict(row)
        result["user_id"] = row["id"]
        _remember_audit_actor(request, result)
        return result

    # 旧 hex32 セッショントークン: 既存の state.sessions 経由
    user = get_user_from_token(request)
    if not user:
        _audit_auth_failure(request, "unauthenticated")
        raise HTTPException(401, "認証が必要です")
    result = dict(user)
    result["user_id"] = user.get("id")
    _remember_audit_actor(request, result)
    return result


def _require_role(request: Request, allowed_roles) -> dict:
    """allowed_roles のいずれかに合致するロールを要求する。

    Stage R5-3 で routers/ の inline `role != "admin"` パターンを統一する用途。
    allowed_roles は set / list / tuple のいずれでも可。
    """
    # fix-bug1: _require_authenticated 経由に統一し JWT トークンを受理する。
    # 従来は get_user_from_token のみで JWT 非対応 → reports 系 EP 等が JWT で 401 になっていた。
    # (_require_admin と同じ「Batch-B S1-3: JWT 対応」方針に揃える)
    user = _require_authenticated(request)
    allowed = set(allowed_roles)
    role = user.get("role")
    if role not in allowed:
        _audit_auth_failure(request, f"role_not_allowed:{role}")
        raise HTTPException(403, "権限がありません")
    return user


def _require_admin_or_self(request: Request, target_user_id: str) -> dict:
    """admin もしくは target_user_id 本人のみを許可する。

    FIX-030 で `routers/users.py` 等の「admin OR self」in-line パターンを統一。
    role 変更等の特権操作判定は呼出側で `user.get("role") == "admin"` で別途実施。
    """
    # fix-kenobi: _require_authenticated 経由に統一し JWT トークンを受理する。
    # 従来は get_user_from_token のみで JWT 非対応 → PATCH /api/users/{id} が
    # JWT の admin/self でも常に 401 になっていた (_require_role の fix-bug1 /
    # _require_admin の Batch-B S1-3 と同じ JWT 対応がここだけ漏れていた)。
    user = _require_authenticated(request)
    is_admin = user.get("role") == "admin"
    is_self = user.get("id") == target_user_id
    if not is_admin and not is_self:
        _audit_auth_failure(request, f"admin_or_self_required:target={target_user_id}")
        raise HTTPException(403, "他のユーザーの情報を変更できません")
    return user


# ── オブジェクト/テナント単位の認可ヘルパー (authz-fix-v1) ───────────────────
# ロール境界 (anon/viewer/admin) の上に、オブジェクト所有権・WS所属を足す共通インターフェース。
# 既存の散在実装 (workspaces.py:649-661 get_workspace_chunks / list_workspaces /
# sessions.py のメンバーシップ・所有権検査) を 1 箇所に集約し、各アクセス点へ
# 機械的に 1 行差し込む。admin は従来どおり広域アクセスを保持する (検査スキップ)。
def require_ws_membership(user: dict, workspace_id: str, conn) -> None:
    """要求者が当該 workspace のメンバーか admin であることを検証する。

    admin は広域アクセスを保持 (検査スキップ)。非 admin が workspace_users に
    未所属なら 403。conn は呼出側が管理する (本関数は close しない)。
    """
    if (user or {}).get("role") == "admin":
        return
    member = conn.execute(
        "SELECT 1 FROM workspace_users WHERE workspace_id = ? AND user_id = ?",
        (workspace_id, (user or {}).get("id")),
    ).fetchone()
    if not member:
        raise HTTPException(403, "このワークスペースへのアクセス権がありません")


def require_session_owner(user: dict, session_id: str, conn) -> None:
    """要求者が当該 session の所有者か admin であることを検証する。

    admin は広域アクセスを保持。非 admin が他人の session_id を指定したら 403。
    存在しない session は「これから自分用に作られる」ため許容 (チェックを通す)。
    予測可能な暗黙 session_id (ws_{wsid}_{uid}) を悪用した cross-user 履歴
    read+write を閉じる。session_id 生成方式自体は変更しない (所有権検査のみ)。
    """
    if not session_id or (user or {}).get("role") == "admin":
        return
    row = conn.execute(
        "SELECT user_id FROM sessions WHERE id = ?", (session_id,)
    ).fetchone()
    if row is not None and row["user_id"] != (user or {}).get("id"):
        raise HTTPException(403, "このセッションへのアクセス権がありません")
