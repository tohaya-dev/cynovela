"""ファイル系エンドポイント。

- /api/documents/{id}/metadata (PATCH): ビジネスメタデータ更新
- /api/browse (GET): フォルダブラウザ
- /api/folder-scan-preview (POST): フォルダ走査プレビュー
- /api/files/{id}/preview (GET): ファイル内容プレビュー (先頭2000文字)

ga-close-v3 PartA (2026-07-27): /api/upload (POST) を撤去した。
受け取ったファイルを store/uploads/ にアプリ内部の生ファイルとして書き出す唯一の経路で、
暗号化もマスキングもされず、ワークスペース削除でも消えず、K8s では受け口 Pod と処理 Pod が
別なので構造的に必ず失敗していた。取り込みは取り込みフォルダ経由に一本化する。
"""

from __future__ import annotations

import os
from pathlib import Path

from core.api_schema import parse_body_pydantic
from fastapi import APIRouter, HTTPException, Request

from db import get_db
from core.auth import _require_admin, _require_authenticated
from core.errors import api_error
from core.audit import _log_audit, log_admin_change


router = APIRouter(tags=["files"])


# ------------------------------------------------------------
# B4: 取り込み元 (ルート) のバックアップを毎回読む。
#   書く側は3つ: 入口スクリプト (./launch.sh --add ほか)・本体の起動時・画面 (/api/ingest-roots)。
#   読む側をここ1か所に揃えることで、画面から足したものが起動し直さずに効く。
#   読めない/無いときは None を返し、呼ぶ側が従来の道 (起動時に確定した一覧) に退く。
# ------------------------------------------------------------
def _ingest_roots_now():
    import json as _json

    _base = os.environ.get("CYNOVELA_DATA_DIR") or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "store"
    )
    _p = os.path.join(_base, "ingest-roots.json")
    if not os.path.isfile(_p):
        return None
    try:
        with open(_p, encoding="utf-8") as _f:
            _d = _json.load(_f)
        return [r for r in (_d.get("roots") or []) if isinstance(r, dict) and r.get("host_path")]
    except Exception:
        return None




@router.patch("/api/documents/{document_id}/metadata", response_model=None)
async def update_document_metadata(document_id: str, request: Request):
    """ビジネスメタデータ + 自動分類を更新.

    Stage R5-fix P1 #9: sensitivity_level / doc_type 変更は admin 限定。
    owner / department / project は認証済みユーザー全員可。
    """
    from core.auth import _require_authenticated

    user = _require_authenticated(request)
    body = await parse_body_pydantic(request)
    allowed = {"owner", "department", "project", "sensitivity_level", "doc_type"}
    updates = {k: v for k, v in (body or {}).items() if k in allowed}
    # Stage R5-fix P1 #9: sensitivity_level / doc_type は admin のみ変更可
    privileged_fields = {"sensitivity_level", "doc_type"}
    if any(k in updates for k in privileged_fields):
        if user.get("role") != "admin":
            raise api_error(
                "PERMISSION_DENIED",
                "sensitivity_level / doc_type の変更は admin のみ可能です",
                status=403,
            )
    if not updates:
        raise api_error("NO_VALID_FIELDS", "No valid fields to update", status=400)
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    conn = get_db()
    try:
        before = conn.execute(
            "SELECT owner, department, project, sensitivity_level, doc_type " "FROM files WHERE id = ?",
            (document_id,),
        ).fetchone()
        if not before:
            raise api_error("NOT_FOUND", "document not found", status=404)
        # MED-1 (authz-fix-v1): オブジェクト所属検査。非admin はこの document の source が
        # 自分の所属WSに紐づく場合のみ更新可 (他WSの doc メタデータ改ざんを 403 で閉じる)。
        # admin は広域維持。多段解決 (files→source→workspace_sources→workspace_users) は
        # catalog.py のメンバーシップ・スコープと同型 (1ソース複数WS所属を IN で正しく扱う)。
        if user.get("role") != "admin":
            _member = conn.execute(
                "SELECT 1 FROM files f WHERE f.id = ? AND f.source_id IN "
                "(SELECT source_id FROM workspace_sources WHERE workspace_id IN "
                "(SELECT workspace_id FROM workspace_users WHERE user_id = ?))",
                (document_id, user.get("id")),
            ).fetchone()
            if not _member:
                raise api_error(
                    "PERMISSION_DENIED",
                    "このドキュメントを変更する権限がありません",
                    status=403,
                )
        conn.execute(
            f"UPDATE files SET {set_clause} WHERE id = ?",
            list(updates.values()) + [document_id],
        )
        conn.commit()
    finally:
        conn.close()
    log_admin_change(user["id"], "document", document_id, "update", dict(before), updates)
    return {"id": document_id, "status": "updated", "updates": updates}


@router.get("/api/browse", response_model=None)
def browse_folders(request: Request, path: str = ""):
    """Task 5: フォルダブラウザ。指定パス配下のサブフォルダ一覧を返す。

    クエリ:
      path: 探索対象のフルパス。省略時は $HOME。

    レスポンス:
      {current_path, parent_path | null, home_path, folders: [{name, path, type}]}

    セキュリティ:
      - 管理者専用 (_require_admin)。閲覧者は従来どおり拒否
      - フォルダのみ列挙 (ファイル・symlink・隠しフォルダは除外)
      - browse-root-unlock-20260728: ホーム外 403 の範囲制限は撤廃
        (/api/sources が範囲外パスを受理する決裁済み挙動と整合させ、
        取り込み元を /Volumes 等の任意の絶対パスから選べるようにする)

    route-admin-sweep-20260727: ホストのファイルシステムを列挙する経路のため管理者専用へ寄せた
    (判定基準③)。2026-07-06 に「要決裁・軽微」として起票されたまま残っていた決裁事項をここで閉じる。
    画面側の呼び出し元は「ソース追加」と「クイックスタート」のフォルダ参照の2つで、
    どちらも取り込み設定＝管理者の作業であり閲覧者の経路ではない。
    """
    _require_admin(request)
    # fix-folder-ingest-20260618: 取り込みフォルダ /app/ingest が存在すればそれをルートにする (新規 env 不使用)。
    # 無ければ従来どおり $HOME (スタンドアロン挙動は不変)。
    # browse-root-unlock-20260728: home は既定の開始地点と home_path 表示のみに用い、範囲制限には使わない。
    _ingest_box = "/app/ingest"
    if os.path.isdir(_ingest_box):
        home = os.path.realpath(_ingest_box)
    else:
        home = os.path.realpath(os.path.expanduser("~"))
    target_input = path or home
    try:
        target = os.path.realpath(os.path.abspath(os.path.expanduser(target_input)))
    except Exception as e:
        raise HTTPException(400, f"Invalid path: {e}")

    # multi-ingest-roots-20260728: browse-root-unlock-20260728 で撤廃した境界を復元する。
    # 取り込み元は起動時マウント (/app/ingest 配下のルート) で選ぶ方式に改めたため、
    # 参照範囲は home (= /app/ingest があればそれ、なければ ~) 配下に戻す。
    # ホーム外アクセス禁止 (home + os.sep で前方一致の偽陽性 (/Users/me2 vs /Users/me) を回避)
    if target != home and not target.startswith(home + os.sep):
        raise HTTPException(403, "この場所を使うには起動時に追加してください")
    if not os.path.isdir(target):
        raise HTTPException(404, f"Folder not found: {target}")

    folders: list[dict] = []
    files: list[dict] = []
    try:
        for entry in sorted(os.listdir(target)):
            if entry.startswith("."):
                continue  # 隠しエントリはスキップ
            full = os.path.join(target, entry)
            try:
                if os.path.islink(full):
                    continue  # symlink は除外 (箱の外へ逃げる経路を断つ・従来挙動踏襲)
                if os.path.isdir(full):
                    folders.append({"name": entry, "path": full, "type": "directory"})
                elif os.path.isfile(full):
                    # fix-folder-ingest-20260618: 目視確認用にファイルも返す (非選択・取り込み単位はフォルダのまま)。
                    files.append({"name": entry, "path": full, "type": "file"})
            except OSError:
                continue
    except PermissionError:
        raise HTTPException(403, f"Permission denied: {target}")

    # multi-ingest-roots-20260728: 境界復元に合わせ、親無し = home (ルート) に戻す。
    parent_path = None if target == home else os.path.dirname(target)
    resp = {
        "current_path": target,
        "parent_path": parent_path,
        "home_path": home,
        "folders": folders,
        "files": files,
    }
    # multi-ingest-roots-20260728: 取り込み元のルートが1件も無い (= /app/ingest が存在して中身が空) とき、
    # 画面が「起動時に追加してください」とガイドできるよう no_roots を返す (既存キーは不変)。
    try:
        if os.path.isdir(_ingest_box) and not os.listdir(os.path.realpath(_ingest_box)):
            resp["no_roots"] = True
    except OSError:
        pass
    return resp


@router.post("/api/folder-scan-preview", response_model=None)
async def folder_scan_preview(request: Request):
    """PHASE M-3: 指定フォルダを再帰スキャンし、拡張子別件数と推定処理時間を返す。

    Request body: {"folder_path": "/path/to/folder", "recursive": true}
    Response:
      {
        "files": {"pdf": N, "docx": N, "xlsx": N, ..., "images": N,
                  "skipped": {"video": N, "audio": N, "other": N}},
        "estimated_time_sec": int,
        "image_processing_time_sec": int,
        "total_supported": int
      }
    """
    _require_admin(request)
    body = await parse_body_pydantic(request)
    folder_path = (body or {}).get("folder_path") or ""
    recursive = bool((body or {}).get("recursive", True))
    if not folder_path:
        raise HTTPException(400, "folder_path は必須です")

    # /api/sources と同等のパス検証 (Defense-in-Depth)
    _lower = folder_path.strip().lower()
    if any(_lower.startswith(s) for s in ("file://", "data://", "ftp://", "javascript:")):
        raise HTTPException(400, "URL scheme is not allowed in folder_path")
    if "\\" in folder_path:
        raise HTTPException(400, "Windows path separator is not allowed")
    if ".." in folder_path.split(os.sep):
        raise HTTPException(400, "relative path traversal is not allowed")
    _normalized = os.path.normpath(os.path.expanduser(folder_path))
    _forbidden_prefixes = (
        "/etc",
        "/var/root",
        "/var/db",
        "/private/etc",
        "/private/var/root",
        "/root",
        "/sys",
        "/proc",
        "/boot",
    )
    _forbidden_substrings = (
        "/.ssh",
        "/.aws",
        "/.gnupg",
        "/Library/Keychains",
        "/Library/Application Support/com.apple.sharedfilelist",
        "/.kube",
        "/.config/gh",
        "/.netrc",
    )
    if any(_normalized == p or _normalized.startswith(p + "/") for p in _forbidden_prefixes):
        raise HTTPException(400, f"system path is not allowed: {_normalized}")
    if any(s in _normalized for s in _forbidden_substrings):
        raise HTTPException(400, f"sensitive path is not allowed: {_normalized}")

    folder = Path(_normalized)
    if not folder.is_dir():
        raise HTTPException(400, f"フォルダが見つかりません: {folder}")

    counts: dict = {
        "pdf": 0,
        "docx": 0,
        "xlsx": 0,
        "pptx": 0,
        "txt": 0,
        "md": 0,
        "csv": 0,
        "html": 0,
        "eml": 0,
        "zip": 0,
        "images": 0,
        "skipped": {"video": 0, "audio": 0, "other": 0},
    }
    image_exts = {".jpg", ".jpeg", ".png", ".heic", ".webp", ".gif"}
    video_exts = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
    audio_exts = {".mp3", ".wav", ".flac", ".m4a", ".ogg"}
    map_ext = {
        ".pdf": "pdf",
        ".docx": "docx",
        ".doc": "docx",
        ".xlsx": "xlsx",
        ".xls": "xlsx",
        ".pptx": "pptx",
        ".txt": "txt",
        ".md": "md",
        ".csv": "csv",
        ".html": "html",
        ".htm": "html",
        ".eml": "eml",
        ".zip": "zip",
    }

    def _bump(ext: str) -> None:
        if ext in image_exts:
            counts["images"] += 1
        elif ext in video_exts:
            counts["skipped"]["video"] += 1
        elif ext in audio_exts:
            counts["skipped"]["audio"] += 1
        elif ext in map_ext:
            counts[map_ext[ext]] += 1
        else:
            counts["skipped"]["other"] += 1

    # os.walk + onerror=lambda で PermissionError を silent skip。
    # 旧実装の Path.rglob は権限エラーで途中停止し HTTP 500 化していた。
    try:
        if recursive:
            for _root, _dirs, filenames in os.walk(str(folder), onerror=lambda _e: None, followlinks=False):
                for fname in filenames:
                    try:
                        ext = os.path.splitext(fname)[1].lower()
                    except Exception:
                        continue
                    _bump(ext)
        else:
            for entry in folder.iterdir():
                try:
                    if not entry.is_file():
                        continue
                    ext = entry.suffix.lower()
                except OSError:
                    continue
                _bump(ext)
    except (PermissionError, OSError) as e:
        raise HTTPException(400, f"フォルダの走査に失敗しました: {e}")

    total_supported = sum(v for k, v in counts.items() if k not in ("skipped", "images")) + counts["images"]
    # 推定: テキスト系 0.3s/件、画像 (caption モード時) 3s/件 → 設定モードで切替
    img_per_file = 3
    try:
        from core.config import CYNOVELA_CONFIG as _CFG

        mode = (_CFG.get("image") or {}).get("processing_mode", "filename_only")
        if mode != "caption":
            img_per_file = 0.05
    except Exception:
        pass
    text_count = total_supported - counts["images"]
    estimated_text = int(text_count * 0.3)
    estimated_image = int(counts["images"] * img_per_file)
    return {
        "files": counts,
        "total_supported": total_supported,
        "estimated_time_sec": estimated_text + estimated_image,
        "image_processing_time_sec": estimated_image,
    }


@router.get("/api/files/{file_id}/preview", response_model=None)
def file_preview(file_id: str, request: Request):
    """P2-2: ファイルプレビュー（先頭2000文字）"""
    # FIX-025: in-line role 検査 → _require_role helper 統一 (FIX-020 後の追加対応)
    from core.auth import _require_role

    _fp_user = _require_role(request, ("admin",))
    conn = get_db()
    try:
        row = conn.execute("SELECT id, name, path, mime_type FROM files WHERE id = ?", (file_id,)).fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="ファイルが見つかりません")
    path = row["path"] or ""
    name = row["name"] or ""
    # sokessan-fix-a8-20260711: 原本ファイルプレビュー(マスキング前本文の先頭2000字)閲覧を監査に残す。
    try:
        _fp_ca = get_db()
        try:
            _log_audit(
                _fp_ca,
                "file_preview",
                file_id,
                detail=(name or "")[:120],
                ip_address=(request.client.host if request.client else None),
                user_id=(_fp_user.get("id") if isinstance(_fp_user, dict) else None),
            )
        finally:
            _fp_ca.close()
    except Exception:
        pass
    ext = os.path.splitext(name)[1].lower()
    binary_exts = {
        ".pdf",
        ".docx",
        ".pptx",
        ".xlsx",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".bmp",
        ".zip",
        ".tar",
        ".gz",
        ".bin",
    }
    if ext in binary_exts:
        return {"preview": None, "reason": "binary", "name": name}
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read(2000)
        return {"preview": text, "name": name, "truncated": True}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="ファイルが見つかりません（パス不正）")
    except Exception as e:
        return {"preview": None, "reason": f"read_error: {e}", "name": name}
