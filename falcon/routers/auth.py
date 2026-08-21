"""Authentication endpoints (/api/auth/*)."""

from __future__ import annotations

import re
import secrets
import hashlib as _hashlib
import uuid as _uuid
import jwt as _pyjwt
from datetime import datetime, timedelta as _td, timezone as _tz

from core.api_schema import parse_body_pydantic
from fastapi import APIRouter, Body, HTTPException, Request

from db import get_db, verify_password

import state as _state
from core.api_schema import BaseResponseSchema as _PilotResp
from core.auth import _audit_auth_failure, _require_admin, _require_authenticated

router = APIRouter(tags=["auth"])


def _auth_rate_limit():
    """fix-security-batch-v2 (2026-05-28) Sub-2G-2 (MED-4): /api/auth/login のブルートフォース防止用
    レートリミットデコレータ (5/minute/IP)。

    chat.py:_chat_rate_limit と同じパターンで server モジュールの `limiter` を sys.modules 経由で参照。
    slowapi 未インストール時は no-op で透過 (既存挙動と整合)。
    """
    import sys

    _srv = sys.modules.get("__main__")
    if not _srv or not hasattr(_srv, "limiter"):
        _srv = sys.modules.get("server")
    _lim = getattr(_srv, "limiter", None) if _srv else None
    if _lim is not None:
        return _lim.limit("5/minute")

    def _noop(fn):
        return fn

    return _noop


def _requested_expiry_seconds(body) -> int | None:
    """DD-CYN-0151 §5: 呼ぶ側が期間を渡したときだけ、その期間で切れるようにする。

    受け取る形は2つ。どちらも省略できる。
      expires_in_hours    : 時間で渡す（小数可）
      expires_in_seconds  : 秒で渡す

    どちらも無い/空なら None を返す。None は「有効期限を入れない」を意味する。
    0 以下や数に読めない値は 400 で断る（黙って無制限にしない）。
    """
    if not isinstance(body, dict):
        return None
    raw_h = body.get("expires_in_hours")
    raw_s = body.get("expires_in_seconds")
    if raw_h in (None, "") and raw_s in (None, ""):
        return None
    try:
        secs = int(float(raw_s)) if raw_s not in (None, "") else int(float(raw_h) * 3600)
    except (TypeError, ValueError):
        raise HTTPException(400, "expires_in_hours / expires_in_seconds には数を指定してください")
    if secs <= 0:
        raise HTTPException(400, "expires_in_hours / expires_in_seconds には 0 より大きい数を指定してください")
    return secs


@router.get("/api/auth/users", response_model=None)
def list_users(request: Request):
    # 2026-05-23 sec4 v4.1 項目①: 旧 fix060 B の demo 未認証許可を撤廃。常時 admin 認証必須。
    # ワンクリック入室 (user-cards 表示) は完全撤去したため、未認証で users 一覧を返す必要なし。
    _require_admin(request)
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT id, username, display_name, role, avatar, " "COALESCE(is_active, 1) AS is_active FROM users"
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


@router.post(
    "/api/auth/login",
    response_model=_PilotResp,
    responses={
        400: {"description": "Invalid login payload"},
        401: {"description": "Authentication failed"},
        429: {"description": "Too Many Requests (rate limited)"},
    },
)  # FIX-052 パイロット
@_auth_rate_limit()  # fix-security-batch-v2 (2026-05-28) Sub-2G-2 (MED-4): ブルートフォース防止 5/min/IP
async def login(request: Request):
    """ログイン: username + password で password_hash 検証し新規セッション発行。
    2026-05-23 sec4 v4.1 項目①: user_id 単独のレガシーパス (demo モードで demo-token-* 発行)
    を完全撤去。パスワード不要の入口は無し。username/password 必須。
    後方互換: user_id 単独で来た古い呼び出しは 401 で明示拒否 (旧テストの「user_id-only login は
    非 demo で 401」期待を維持)。
    """
    body = await parse_body_pydantic(request)
    user_id_legacy = body.get("user_id")
    username = (body.get("username") or "").strip()
    password = body.get("password") or ""

    # 旧 user_id-only login は完全撤去済。明示的に 401 を返す (互換: 旧経路は弾く)。
    if user_id_legacy and not username:
        _audit_auth_failure(request, "user_id_only_login_removed")
        raise HTTPException(401, "ユーザー名とパスワードが必要です")

    if not username:
        _audit_auth_failure(request, "missing_credentials")
        raise HTTPException(400, "username と password を指定してください")

    conn = get_db()
    try:
        user = conn.execute(
            "SELECT * FROM users WHERE (username = ? OR id = ?) AND COALESCE(is_active, 1) = 1",
            (username, username),
        ).fetchone()
    finally:
        conn.close()
    # [2B-A] auth_failed 監査追加: パスワード平文は detail に絶対書かない。
    # reason は固定文字列 (bad_password / user_not_found) のみ。
    if not user:
        _audit_auth_failure(request, "user_not_found")
        raise HTTPException(401, "ユーザー名またはパスワードが正しくありません")
    if not verify_password(password, user["password_hash"] or ""):
        _audit_auth_failure(request, "bad_password")
        raise HTTPException(401, "ユーザー名またはパスワードが正しくありません")

    # DD-CYN-0151 §5: アクセストークンの既定を無制限にした（従来は 8時間 固定）。
    # 呼ぶ側が expires_in_hours / expires_in_seconds を渡したときだけ exp を入れる。
    from core.auth import _get_jwt_secret
    now = datetime.now(_tz.utc)
    _exp_secs = _requested_expiry_seconds(body)
    access_payload = {
        "sub": str(user["id"]),
        "role": user["role"],
        "iat": int(now.timestamp()),
    }
    if _exp_secs is not None:
        access_payload["exp"] = int((now + _td(seconds=_exp_secs)).timestamp())
    access_token = _pyjwt.encode(
        access_payload, _get_jwt_secret(), algorithm="HS256"
    )

    # Batch-B S1-3: リフレッシュトークン（30日）
    raw_refresh = secrets.token_urlsafe(32)
    refresh_hash = _hashlib.sha256(raw_refresh.encode()).hexdigest()
    rt_expires = (now + _td(days=30)).strftime("%Y-%m-%dT%H:%M:%S")
    conn2 = get_db()
    try:
        conn2.execute(
            "INSERT INTO refresh_tokens (id, user_id, token_hash, expires_at)"
            " VALUES (?, ?, ?, ?)",
            (_uuid.uuid4().hex, str(user["id"]), refresh_hash, rt_expires),
        )
        # Batch-B S1-1: must_change_password フラグ取得
        mcpw_row = conn2.execute(
            "SELECT must_change_password FROM users WHERE id = ?",
            (str(user["id"]),),
        ).fetchone()
        must_change = bool(mcpw_row and mcpw_row["must_change_password"])
        # E2(b) allinone: ログイン成功を監査ログに記録（従来は失敗のみ記録）。user_id も明示して NULL を防ぐ。
        try:
            from core.audit import _log_audit as _la_login
            # ga-close-v3 PartB (B-1): ログイン成功にも接続元IPを残す
            # (ログイン時点では未認証のため実行文脈が空。ここだけは明示指定する)。
            _la_login(conn2, "login_success", str(user["id"]),
                      detail=f"role={user['role']}", user_id=str(user["id"]),
                      ip_address=(request.client.host if request.client else None))
        except Exception:
            pass
        conn2.commit()
    finally:
        conn2.close()

    user_dict = {k: v for k, v in dict(user).items() if k not in ("password_hash", "salt")}
    return {
        "user": user_dict,
        "token": access_token,  # 後方互換
        "access_token": access_token,
        "refresh_token": raw_refresh,
        "token_type": "bearer",
        "user_id": str(user["id"]),
        "role": user["role"],
        "must_change_password": must_change,
        # DD-CYN-0151 §5: 期限なしなら null。渡された期間で切れるなら、その秒数。
        "expires_in": _exp_secs,
    }


@router.post("/api/auth/logout", response_model=_PilotResp)  # FIX-052 パイロット
async def logout(request: Request):
    """Stage R8-fix: 認証必須化 (未認証 logout は意味なし、401 で reject)."""
    _lo_user = _require_authenticated(request)
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer ") and not auth.startswith("Bearer demo-token-"):
        token = auth[7:]
        _state.sessions.pop(token, None)
        # Batch-B S1-3: JWT の場合はリフレッシュトークンも削除
        if not token.startswith("demo-token-") and token.count(".") == 2:
            try:
                from core.auth import _get_jwt_secret as _gjs
                payload = _pyjwt.decode(
                    token, _gjs(), algorithms=["HS256"],
                    options={"verify_exp": False},
                )
                conn_l = get_db()
                try:
                    conn_l.execute(
                        "DELETE FROM refresh_tokens WHERE user_id = ?",
                        (payload["sub"],),
                    )
                    conn_l.commit()
                finally:
                    conn_l.close()
            except Exception:
                pass
    # sokessan-fix-a8-20260711: ログアウト操作を監査に残す (従来 login_success のみで logout は無記録だった)。
    try:
        from core.audit import _log_audit as _la_logout

        _lo_ca = get_db()
        try:
            _la_logout(
                _lo_ca,
                "logout",
                detail="",
                ip_address=(request.client.host if request.client else None),
                user_id=(_lo_user.get("id") if isinstance(_lo_user, dict) else None),
            )
        finally:
            _lo_ca.close()
    except Exception:
        pass
    return {"ok": True}


@router.get("/api/auth/me", response_model=_PilotResp)  # FIX-052 パイロット
def auth_me(request: Request):
    # FIX-022: in-line 認可 → _require_authenticated helper 統一
    from core.auth import _require_authenticated

    user = _require_authenticated(request)
    role = user.get("role") or ""
    # UX-2: ロール名は職能名 (個人名は使わない)
    role_label_en = {
        "admin": "Administrator",
        "viewer": "Viewer",
    }.get(role, role)
    role_label_ja = {
        "admin": "管理者",
        "viewer": "閲覧者",
    }.get(role, role)

    # display_name 未設定 OR 個人名 (CJK 文字を含む) なら role 名にフォールバック.
    # spec: 個人名は使わず職能名 (Administrator / Viewer) を使う.
    def _is_personal_name(name: str) -> bool:
        if not name:
            return False
        # ひらがな・カタカナ・漢字を含むなら個人名 (デモ seed の "田中 誠" 等) と判定
        return bool(re.search(r"[぀-ゟ゠-ヿ一-鿿]", name))

    raw_dn = user.get("display_name") or user.get("name") or ""
    if not raw_dn or _is_personal_name(raw_dn):
        display_name = role_label_en or user.get("username") or user["id"]
    else:
        display_name = raw_dn
    return {
        "user_id": user["id"],
        "id": user["id"],
        "username": user.get("username") or user["id"],
        "display_name": display_name,
        "role": role,
        "role_label_en": role_label_en,
        "role_label_ja": role_label_ja,
    }


@router.get("/api/auth/session-config", response_model=None)
def auth_session_config(request: Request):
    """PHASE AUTH-1: セッション持続時間設定を返す。"""
    _require_admin(request)
    c = get_db()
    try:
        rows = {
            r["key"]: r["value"]
            for r in c.execute("SELECT key, value FROM settings WHERE key LIKE 'auth.%'").fetchall()
        }
    finally:
        c.close()
    return {
        "session_hours": int(rows.get("auth.session_hours", "8")),
        "idle_logout_minutes": int(rows.get("auth.idle_logout_minutes", "0")),
    }


@router.post("/api/auth/session-config", response_model=None)
async def update_auth_session_config(request: Request):
    """PHASE AUTH-1: セッション持続時間設定を更新する。"""
    _require_admin(request)
    body = await parse_body_pydantic(request)
    sh = body.get("session_hours")
    im = body.get("idle_logout_minutes")
    c = get_db()
    try:
        if sh is not None:
            c.execute(
                "INSERT INTO settings (key, value) VALUES ('auth.session_hours', ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (str(int(sh)),),
            )
        if im is not None:
            c.execute(
                "INSERT INTO settings (key, value) VALUES ('auth.idle_logout_minutes', ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (str(int(im)),),
            )
        c.commit()
    finally:
        c.close()
    return {"ok": True}


@router.post("/api/auth/refresh", response_model=None)
def refresh_access_token(
    refresh_token: str = Body(..., embed=True),
    expires_in_hours: float | None = Body(None, embed=True),
    expires_in_seconds: float | None = Body(None, embed=True),
):
    """Batch-B S1-3: リフレッシュトークンで新しいアクセストークンを発行する。

    DD-CYN-0151 §5: 既定は無制限（exp を入れない）。login と同じで、
    expires_in_hours / expires_in_seconds を渡したときだけ、その期間で切れる。
    """
    from core.auth import _get_jwt_secret
    token_hash = _hashlib.sha256(refresh_token.encode()).hexdigest()
    conn = get_db()
    try:
        row = conn.execute(
            """SELECT rt.user_id, u.role, COALESCE(u.is_active, 1) AS is_active
               FROM refresh_tokens rt
               JOIN users u ON rt.user_id = u.id
               WHERE rt.token_hash = ?
                 AND rt.expires_at > datetime('now')""",
            (token_hash,),
        ).fetchone()
    finally:
        conn.close()
    if not row or not row["is_active"]:
        raise HTTPException(401, "Invalid or expired refresh token")
    now = datetime.now(_tz.utc)
    _exp_secs = _requested_expiry_seconds(
        {"expires_in_hours": expires_in_hours, "expires_in_seconds": expires_in_seconds}
    )
    payload = {
        "sub": row["user_id"],
        "role": row["role"],
        "iat": int(now.timestamp()),
    }
    if _exp_secs is not None:
        payload["exp"] = int((now + _td(seconds=_exp_secs)).timestamp())
    return {
        "access_token": _pyjwt.encode(payload, _get_jwt_secret(), algorithm="HS256"),
        "token_type": "bearer",
        "expires_in": _exp_secs,
    }


@router.post("/api/auth/change-password", response_model=None)
async def change_password_endpoint(request: Request):
    """Batch-B S1-1: ログイン済みユーザーが自分のパスワードを変更する。current_password 検証必須。"""
    from core.auth import _require_authenticated as _ra
    user = _ra(request)
    body = await parse_body_pydantic(request)
    current_password = body.get("current_password") or ""
    new_password = body.get("new_password") or ""
    if len(new_password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters")
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE id = ?", (user["user_id"],)
        ).fetchone()
        if not row:
            raise HTTPException(404, "User not found")
        if not verify_password(current_password, row["password_hash"] or ""):
            raise HTTPException(401, "Current password is incorrect")
        from db import hash_password as _hp
        new_hash = _hp(new_password)
        conn.execute(
            "UPDATE users SET password_hash = ?, must_change_password = 0 WHERE id = ?",
            (new_hash, user["user_id"]),
        )
        conn.commit()
    finally:
        conn.close()
    return {"ok": True}


@router.post("/api/auth/verify-password", response_model=None)
async def verify_password_endpoint(request: Request):
    """Batch-B S1-3: パスワードを検証する（ロック画面解除用）。トークンは発行しない。"""
    from core.auth import _require_authenticated as _ra
    user = _ra(request)
    body = await parse_body_pydantic(request)
    password = body.get("password") or ""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE id = ?", (user["user_id"],)
        ).fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(404, "User not found")
    if not verify_password(password, row["password_hash"] or ""):
        raise HTTPException(401, "Wrong password")
    return {"ok": True}
