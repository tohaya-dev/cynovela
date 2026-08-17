"""Data sources endpoints (/api/sources/*)."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import threading

from core.api_schema import parse_body_pydantic
from fastapi import APIRouter, HTTPException, Request

from db import get_db, new_id
from core.auth import _require_admin, _require_authenticated
from core.audit import _log_audit

# ga-close-v3 PartA (2026-07-27): アップロード保存先 (_uploads_root) と
# /api/sources/upload を撤去した。取り込みは取り込みフォルダ経由に一本化する。

router = APIRouter(tags=["sources"])


@router.get("/api/sources", response_model=None)
def list_sources(
    request: Request,
    limit: int | None = None,
    offset: int = 0,
    q: str | None = None,
    workspace_id: str | None = None,
    sort: str = "created_at_desc",
):
    """GUI修正2 #35: archived_at IS NULL のもののみ返す。
    BETA-pagination: limit/offset/q/workspace_id でページネーション・検索を有効化。"""
    from server import rows_to_list

    user = _require_authenticated(request)
    if limit is not None and limit not in (10, 20, 50, 100):
        raise HTTPException(status_code=400, detail="limitは10/20/50/100のいずれかです")
    if offset < 0:
        raise HTTPException(status_code=400, detail="offsetは0以上です")
    conn = get_db()
    # connleak-fix-v1: 例外時も必ず close する (残留接続が WAL 書込ロックを保持し
    # "database is locked" を誘発するのを防ぐ)。
    try:
        where_parts: list[str] = ["s.archived_at IS NULL"]
        params: list = []
        if q:
            where_parts.append("s.name LIKE ?")
            params.append(f"%{q}%")
        if workspace_id:
            where_parts.append("s.id IN (SELECT source_id FROM workspace_sources WHERE workspace_id = ?)")
            params.append(workspace_id)
        # authz-fix-v1: 非admin は自分の所属WSに紐づく source のみ (admin は全件=広域維持)。
        if (user or {}).get("role") != "admin":
            where_parts.append(
                "s.id IN (SELECT source_id FROM workspace_sources WHERE workspace_id IN "
                "(SELECT workspace_id FROM workspace_users WHERE user_id = ?))"
            )
            params.append((user or {}).get("id"))
        where_sql = "WHERE " + " AND ".join(where_parts)

        total = None
        if limit is not None:
            total = conn.execute(f"SELECT COUNT(*) FROM sources s {where_sql}", params).fetchone()[0]

        pagination_sql = ""
        pagination_params: list = []
        if limit is not None:
            pagination_sql = " LIMIT ? OFFSET ?"
            pagination_params = [limit, offset]
        # P1-7: sort はSQLインジェクション防止のためホワイトリストで解決する（生値は絶対に埋め込まない）
        _SORT_MAP = {
            "created_at_desc": "s.created_at DESC",
            "created_at_asc": "s.created_at ASC",
            "name_asc": "s.name ASC",
            "name_desc": "s.name DESC",
        }
        order_clause = _SORT_MAP.get(sort, "s.created_at DESC")
        sources = rows_to_list(
            conn.execute(
                f"SELECT s.* FROM sources s {where_sql} " f"ORDER BY {order_clause} {pagination_sql}",
                params + pagination_params,
            ).fetchall()
        )
    finally:
        conn.close()
    if limit is None:
        return sources
    return {"items": sources, "total": total, "limit": limit, "offset": offset}


@router.get("/api/sources/{source_id}", response_model=None)
def get_source(request: Request, source_id: str):
    _require_admin(request)
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM sources WHERE id = ?", (source_id,)).fetchone()
        if not row:
            raise HTTPException(404, "source not found")
        out = dict(row)
        # fix062 A5: 1 source は workspace_sources 中間テーブルで複数 workspace に所属可能。
        # workspace_id 単数ではなく workspace_ids 配列で返す。
        ws_rows = conn.execute(
            "SELECT workspace_id FROM workspace_sources WHERE source_id = ?",
            (source_id,),
        ).fetchall()
        out["workspace_ids"] = [r["workspace_id"] for r in ws_rows]
    finally:
        conn.close()
    return out


@router.post("/api/sources", response_model=None)
async def create_source(request: Request):
    from server import _do_scan

    _require_admin(request)
    body = await parse_body_pydantic(request)
    name = body.get("name")
    path = body.get("path")
    auto_scan = body.get("auto_scan", True)
    if not name or not path:
        raise HTTPException(400, "name and path are required")
    # PHASE A: パストラバーサル / 機密パス拒否
    _lower = path.strip().lower()
    _forbidden_schemes = ("file://", "data://", "ftp://", "javascript:")
    if any(_lower.startswith(s) for s in _forbidden_schemes):
        raise HTTPException(400, "URL scheme is not allowed in path")
    if "\\" in path:
        raise HTTPException(400, "Windows path separator is not allowed")
    _normalized = os.path.normpath(path)
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
    if ".." in path.split(os.sep):
        raise HTTPException(400, "relative path traversal is not allowed")
    sid = new_id()
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO sources (id, name, path) VALUES (?, ?, ?)",
            (sid, name, path),
        )
        _log_audit(conn, "source_created", sid, name)
        conn.commit()
    except sqlite3.IntegrityError as e:
        raise HTTPException(409, f"同名のソースが既に存在します: {name}") from e
    finally:
        # 例外で接続を開いたまま抜けると暗黙BEGINの書き込みトランザクションが残留し、
        # 以後の全書き込みが busy_timeout(30s) 超過の "database is locked" になる
        conn.close()
    if auto_scan:
        threading.Thread(target=_do_scan, args=(sid,), daemon=True).start()
    return {"id": sid, "name": name, "path": path, "auto_scan": auto_scan}


@router.get("/api/sources/{source_id}/open-in-finder", response_model=None)
def open_source_in_finder(request: Request, source_id: str):
    """Open the source path in OS file manager (macOS Finder / Windows Explorer / Linux xdg-open)."""
    _require_admin(request)
    conn = get_db()
    try:
        source = conn.execute("SELECT * FROM sources WHERE id = ?", (source_id,)).fetchone()
    finally:
        conn.close()
    if not source:
        raise HTTPException(404, "Source not found")
    src_path = os.path.abspath(os.path.expanduser(source["path"]))
    if not os.path.exists(src_path):
        raise HTTPException(
            404,
            f"このソースのパスが現在の環境に存在しません。別のマシンで登録されたソースの可能性があります（path={src_path}）。",
        )
    try:
        if sys.platform == "darwin":
            if os.path.isdir(src_path):
                subprocess.run(["open", src_path], check=False)
            else:
                subprocess.run(["open", "-R", src_path], check=False)
            label = "Finder"
        elif sys.platform.startswith("win"):
            if os.path.isdir(src_path):
                subprocess.run(["explorer", src_path], check=False)
            else:
                subprocess.run(["explorer", "/select,", src_path], check=False)
            label = "エクスプローラー"
        else:
            target = src_path if os.path.isdir(src_path) else os.path.dirname(src_path)
            subprocess.run(["xdg-open", target], check=False)
            label = "ファイルマネージャー"
    except FileNotFoundError as e:
        raise HTTPException(500, f"OSのファイルマネージャーコマンドが見つかりません: {e}")
    except Exception as e:
        raise HTTPException(500, f"フォルダを開けませんでした: {e}")
    return {"ok": True, "path": src_path, "opened_with": label}


@router.post("/api/sources/{source_id}/scan/cancel", response_model=None)
def cancel_scan(request: Request, source_id: str):
    """BLOCK B-6: 進行中のスキャンに停止フラグをセットする。"""
    import server

    _require_admin(request)
    server._scan_cancel_flags[source_id] = True
    conn = get_db()
    try:
        src = conn.execute("SELECT id FROM sources WHERE id = ?", (source_id,)).fetchone()
    finally:
        conn.close()
    if not src:
        raise HTTPException(404, "Source not found")
    return {"ok": True, "status": "cancel_requested", "source_id": source_id}


@router.post("/api/sources/{source_id}/scan", response_model=None)
def scan_source(request: Request, source_id: str):
    from server import _do_scan, row_to_dict

    _require_admin(request)
    conn = get_db()
    try:
        source = conn.execute("SELECT * FROM sources WHERE id = ?", (source_id,)).fetchone()
    finally:
        conn.close()
    if not source:
        raise HTTPException(404, "Source not found")

    _do_scan(source_id)

    conn = get_db()
    try:
        source = conn.execute("SELECT * FROM sources WHERE id = ?", (source_id,)).fetchone()
    finally:
        conn.close()
    return row_to_dict(source)


@router.get("/api/sources/{source_id}/files", response_model=None)
def list_source_files(request: Request, source_id: str):
    from server import rows_to_list

    _require_admin(request)
    conn = get_db()
    try:
        files = rows_to_list(
            conn.execute("SELECT * FROM files WHERE source_id = ? ORDER BY name", (source_id,)).fetchall()
        )
    finally:
        conn.close()
    for f in files:
        if isinstance(f.get("categories"), str):
            try:
                f["categories"] = json.loads(f["categories"])
            except Exception:
                f["categories"] = []
        if isinstance(f.get("classification"), str):
            try:
                f["classification"] = json.loads(f["classification"])
            except Exception:
                f["classification"] = None
    return files


@router.delete("/api/sources/{source_id}", response_model=None)
def delete_source(request: Request, source_id: str):
    """source 削除: DB 行とチャンクを削除する。

    ga-close-v3 PartA (2026-07-27): 旧実装はアップロード保管領域
    `store/uploads/{source_id}/` を rmtree していたが、アップロード受け口の撤去に伴い
    アプリ内部に資料のコピーが作られなくなったため不要になった。取り込みフォルダ側の
    原本は従来どおり一切触らない。
    """
    from server import _purge_chunks_for_source

    _require_admin(request)
    conn = get_db()
    # connleak-fix-v1: 例外時も必ず close する (書き込みトランザクション残留で
    # "database is locked" になるのを防ぐ)。
    try:
        # 削除前にパスを取得（アップロード由来か判定するため）
        src_row = conn.execute("SELECT path FROM sources WHERE id = ?", (source_id,)).fetchone()
        src_path = src_row["path"] if src_row else None
        # fix-v3 (A2-F2): BM25 再構築のため、削除前に影響を受ける workspace_id を取得しておく
        # (sources 削除で workspace_sources が FK CASCADE で消えるため事前にバックアップる)。
        _affected_ws = [r["workspace_id"] for r in conn.execute(
            "SELECT workspace_id FROM workspace_sources WHERE source_id = ?", (source_id,)
        ).fetchall()]
        _purge_chunks_for_source(conn, source_id)
        conn.execute("DELETE FROM sources WHERE id = ?", (source_id,))
        _log_audit(conn, "source_deleted", source_id)
        conn.commit()
    finally:
        conn.close()
    # fix-v3 (A2-F2): 削除コミット後に影響 WS の BM25 インデックスを再構築 (delete 経路の stale インデックス
    # 経由で削除済みチャンクが RAG 回答に残留する漏洩を防ぐ。delete_collection と同型)。
    for _wsid in _affected_ws:
        try:
            from rag import rebuild_bm25_from_db
            rebuild_bm25_from_db(_wsid)
        except Exception:
            pass
    # ga-close-v3 PartA (2026-07-27): store/uploads/{source_id}/ の rmtree を撤去した。
    # アップロード受け口が無くなり、アプリが自分の中に資料のコピーを作ることが無くなったため、
    # 削除連鎖でアプリ内部のコピーを消す処理は不要になった。取り込みフォルダ側の原本は
    # 従来どおり一切触らない (ユーザー指定パスの source は元ファイルを保持する)。
    return {"ok": True}


# ============================================================
# DD-CYN-0032 B4: 取り込み元 (ルート) を画面から足す・見る・外す
# ------------------------------------------------------------
#   受け取り手が端末を叩かずに済むようにするための受け口。決定 3-4 に従い、
#   足すときは「フォルダを辿って選ぶ」形だけを用意し、フルパスの手入力は受け付けない
#   (受け取った値が、直前に返した一覧に在るものと一致しない限り足さない)。
#   同時に複数は選ばせない (1回に1件だけ)。
#
#   管理者だけが使える (_require_admin)。閲覧者には一覧も出さない・受け付けない。
#   足していない場所を断る作りは従来のまま (ここで境界を緩めない)。
#
#   コンテナ (コンテナ) で動く形態では、受け取り手の機械のフォルダを画面から辿れない
#   (本体はコンテナの中にいる)。その形態では「見る・外す」だけを画面から行い、
#   「足す」は入口の1行を画面に出して示す。can_add_from_screen でそれを伝える。
# ============================================================


def _ingest_roots_file() -> str:
    """バックアップの場所。書く側 (入口スクリプト) と読む側 (ここ) で同じ場所を指す。"""
    _base = os.environ.get("CYNOVELA_DATA_DIR") or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "store"
    )
    return os.path.join(_base, "ingest-roots.json")


def _in_container() -> bool:
    """コンテナ (コンテナ) の中で動いているか。中なら機械のフォルダを辿れない。"""
    return os.path.isdir("/app/ingest") and os.path.abspath("/app") == os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )


def _load_ingest_roots() -> list:
    """バックアップを読んでルートの一覧を返す。読めなければ空。

    portable-roots-20260808 (DD-CYN-0066 F-2): バックアップには配布物のルートディレクトリからの相対の書き方
    ("@app/…") が入りうる。ここで生の JSON を直に読むと、その書き方のまま画面へ出て
    しまう。∴ 入口スクリプトと同じ部品 (scripts/ingest_roots.py) に読ませ、解いた
    絶対パスだけを受け取る。読めないときだけ従来どおり生読みへ落ちる。
    """
    _p = _ingest_roots_file()
    if not os.path.isfile(_p):
        return []
    try:
        _d = _ingest_roots_helper()._load(_p)
        _r = _d.get("roots") or []
        return [x for x in _r if isinstance(x, dict) and x.get("host_path")]
    except Exception:
        pass
    try:
        with open(_p, encoding="utf-8") as _f:
            _d = json.load(_f)
        _r = _d.get("roots") or []
        return [x for x in _r if isinstance(x, dict) and x.get("host_path")]
    except Exception:
        return []


def _ingest_roots_helper():
    """入口スクリプトと同じ部品を使う (中の名前の付け方・書式を1か所に保つ)。"""
    _repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _repo not in sys.path:
        sys.path.insert(0, _repo)
    from scripts import ingest_roots as _h  # noqa: PLC0415

    return _h


def _browse_start_dir() -> str:
    """新しいルートを選ぶときの出発点。

    A2 の実測に従って決めた: 端末側の `./launch.sh --add` は、いまも機械のどのフォルダでも
    ルートにできる (osascript のフォルダ選択に範囲の制限が無い)。∴ 画面側の出発点を家 ($HOME)
    にしても、管理者が既に持っている力は広がらない。ここで見せるのはフォルダの名前だけで、
    中の資料はルートとして足すまで一切読めない (読む側の境界は従来どおりルートの集合である)。
    """
    return os.path.realpath(os.path.expanduser("~"))


def _list_subdirs(target: str) -> list:
    _out = []
    try:
        for _n in sorted(os.listdir(target)):
            if _n.startswith("."):
                continue
            _p = os.path.join(target, _n)
            try:
                if os.path.isdir(_p) and not os.path.islink(_p):
                    _out.append({"name": _n, "path": os.path.realpath(_p)})
            except OSError:
                continue
    except PermissionError:
        raise HTTPException(403, "このフォルダは読めません")
    except FileNotFoundError:
        raise HTTPException(404, "このフォルダはありません")
    return _out


@router.get("/api/ingest-roots", response_model=None)
def list_ingest_roots(request: Request):
    """いま足してある取り込み元の一覧 (管理者のみ)。"""
    _require_admin(request)
    _roots = _load_ingest_roots()
    _out = []
    for _r in _roots:
        _hp = _r.get("host_path") or ""
        # DD-CYN-0071 P-4: コンテナの中ではバックアップの host_path (機械側の場所) は必ず見えないため、
        #   コンテナの中から見える場所 /app/ingest/<中の名前> で在るかどうかを確かめる
        #   (マウントは deploy/container/run-container.sh が中の名前ごとに張る)。
        #   ホスト直で動く形態では _in_container() が偽になり、従来どおり host_path を見る。
        if _in_container():
            _name = _r.get("name") or ""
            _exists = bool(_name) and os.path.isdir(os.path.join("/app/ingest", _name))
        else:
            _exists = bool(_hp) and os.path.isdir(_hp)
        _out.append(
            {
                "name": _r.get("name"),
                "label": _r.get("label") or _r.get("name"),
                "host_path": _hp,
                "exists": _exists,
            }
        )
    return {
        "roots": _out,
        # 画面から足せるか。コンテナの中では機械のフォルダを辿れないため足せない。
        "can_add_from_screen": not _in_container(),
        # 足したものがすぐ読めるか。コンテナでは起動し直しが要る (束縛は起動時にしか張れない)。
        "restart_required_to_apply": _in_container(),
        "add_from_terminal": "./launch.sh --add",
        "start_dir": _browse_start_dir() if not _in_container() else "",
    }


@router.get("/api/ingest-roots/browse", response_model=None)
def browse_for_ingest_root(request: Request, path: str | None = None):
    """新しいルートを選ぶためのフォルダ辿り (管理者のみ・フォルダ名だけを返す)。

    手入力を受け付けないための取り決め: 画面はここが返した path しか
    POST /api/ingest-roots へ送れない。サーバ側でも、受け取った値が実在する
    フォルダであることと、家の下であることを必ず見る。
    """
    _require_admin(request)
    if _in_container():
        raise HTTPException(
            400, "この形態では画面からフォルダを辿れません。入口の ./launch.sh --add を使ってください。"
        )
    _home = _browse_start_dir()
    _target = os.path.realpath(os.path.abspath(os.path.expanduser(path or _home)))
    if _target != _home and not _target.startswith(_home + os.sep):
        raise HTTPException(403, "ここから外は選べません")
    if not os.path.isdir(_target):
        raise HTTPException(404, "このフォルダはありません")
    _parent = None if _target == _home else os.path.dirname(_target)
    return {
        "current_path": _target,
        "parent_path": _parent,
        "home_path": _home,
        "folders": _list_subdirs(_target),
    }


@router.post("/api/ingest-roots", response_model=None)
async def add_ingest_root(request: Request):
    """取り込み元を1件足す (管理者のみ・1回に1件だけ)。"""
    _require_admin(request)
    if _in_container():
        raise HTTPException(
            400, "この形態では画面から足せません。入口の ./launch.sh --add を使ってください。"
        )
    _body = await parse_body_pydantic(request)
    _path = _body.get("path")
    if not _path or not isinstance(_path, str):
        raise HTTPException(400, "path が要ります")
    # 決定 3-4: 同時に複数は選ばせない。配列で来たら断る。
    if isinstance(_body.get("paths"), list):
        raise HTTPException(400, "一度に足せるのは1件だけです")
    _real = os.path.realpath(os.path.abspath(os.path.expanduser(_path)))
    _home = _browse_start_dir()
    if _real != _home and not _real.startswith(_home + os.sep):
        raise HTTPException(403, "ここから外は足せません")
    if not os.path.isdir(_real):
        raise HTTPException(400, "フォルダではありません")
    _h = _ingest_roots_helper()
    _f = _ingest_roots_file()
    os.makedirs(os.path.dirname(_f), exist_ok=True)
    _data = _h._load(_f)
    for _r in _data["roots"]:
        if _r.get("host_path") == _real:
            return {"ok": True, "name": _r.get("name"), "already": True}
    _name = _h.assign_name(_data, _real)
    _label = os.path.basename(_real.rstrip("/")) or _real
    _data["roots"].append({"name": _name, "host_path": _real, "label": _label})
    _h._save(_f, _data)
    _c = get_db()
    try:
        _log_audit(_c, "ingest_root_add", _name, _label)
        _c.commit()
    finally:
        _c.close()
    return {"ok": True, "name": _name, "label": _label, "already": False}


@router.delete("/api/ingest-roots/{name}", response_model=None)
def remove_ingest_root(request: Request, name: str):
    """取り込み元を1件外す (管理者のみ)。原本には触らない。"""
    _require_admin(request)
    _h = _ingest_roots_helper()
    _f = _ingest_roots_file()
    _data = _h._load(_f)
    _before = len(_data["roots"])
    _data["roots"] = [r for r in _data["roots"] if r.get("name") != name]
    if len(_data["roots"]) == _before:
        raise HTTPException(404, "その取り込み元はありません")
    _h._save(_f, _data)
    _c = get_db()
    try:
        _log_audit(_c, "ingest_root_remove", name, "")
        _c.commit()
    finally:
        _c.close()
    return {"ok": True, "restart_required_to_apply": _in_container()}
