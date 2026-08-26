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


# multi-ingest-roots-20260728: 設定キー ingest.roots (JSON 文字列 [{name,host_path,label}]) による
# 表示専用の写像。/app/ingest/<name> (または配下) に前方一致すれば該当 root の host_path + 残りを返す。
# 写像できなければ None (呼び出し側は従来文言のまま)。表示専用・保存値不変。
def _map_ingest_roots(src_path: str) -> str | None:
    _box = "/app/ingest"
    if not (src_path == _box or src_path.startswith(_box + os.sep)):
        return None
    try:
        _c = get_db()
        try:
            _row = _c.execute("SELECT value FROM settings WHERE key = ?", ("ingest.roots",)).fetchone()
        finally:
            _c.close()
        roots = json.loads((_row["value"] or "[]") if _row else "[]")
    except Exception:
        return None
    if not isinstance(roots, list):
        return None
    rest = src_path[len(_box):].lstrip(os.sep)  # "<name>" or "<name>/..." or ""
    for r in roots:
        if not isinstance(r, dict):
            continue
        name = str(r.get("name") or "")
        host = str(r.get("host_path") or "").rstrip("/")
        if not name or not host:
            continue
        if rest == name or rest.startswith(name + os.sep):
            return host + rest[len(name):]
    return None


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
    # connleak-fix-20260709: 例外時も必ず close する (接続リークで書き込みロック残留を防ぐ)
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
    # connleak-fix-20260709: 例外時も必ず close する (接続リークで書き込みロック残留を防ぐ)
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
    _existing = None
    conn = get_db()
    # connleak-fix-20260709 (アプリ版検証済み修正の逐語ポート):
    # 旧実装は INSERT が例外 (例: UNIQUE constraint failed: sources.name) を投げると
    # conn を close せずに抜けていた。SQLite は INSERT 時に暗黙 BEGIN で書き込み
    # トランザクションを開くため、close 漏れ = 書き込みロック残留となり、以後の
    # 全書き込みが busy_timeout(30s) 超過の "database is locked" になっていた
    # (フロントでは「追加失敗: Failed to fetch」)。同名 source は 409 で穏当に弾く。
    try:
        # DD-CYN-0151 §7: 同じ場所を二重に登録させない。
        #   従来 UNIQUE が効いていたのは name だけだったため、名前を変えれば同じフォルダを
        #   何本でも登録でき、走査も公開も二重に走っていた。
        #   場所の見分けは実体のパス (シンボリックリンクと末尾の / を解いたもの) で行う。
        # DD-CYN-0168 (欠陥§179 版3 / §181): 同じ場所が既に在るときに 409 で断ると、
        #   クイックスタートも `source` の追加もそこで行き止まりになり、画面には
        #   「この場所は既に登録されています」だけが残っていた。二重登録を防ぐ目的は
        #   「新しい行を作らない」ことで足りる。∴ 断らずに、既に在る source をそのまま
        #   返す (冪等)。UI 側の再利用判定は path の文字列一致で行うため、実体パスは
        #   同じでも文字列が違う (末尾の / ・~ ・シンボリックリンク) と再利用に乗らず、
        #   ここへ落ちてくる。
        _want = os.path.realpath(os.path.expanduser(_normalized))
        for _row in conn.execute("SELECT id, name, path FROM sources").fetchall():
            _have = os.path.realpath(os.path.expanduser(os.path.normpath(_row["path"] or "")))
            if _have and _have == _want:
                _existing = {"id": _row["id"], "name": _row["name"], "path": _row["path"]}
                break
        if _existing is not None:
            _log_audit(conn, "source_reused", _existing["id"], _existing["name"])
            conn.commit()
        else:
            conn.execute(
                "INSERT INTO sources (id, name, path) VALUES (?, ?, ?)",
                (sid, name, path),
            )
            _log_audit(conn, "source_created", sid, name)
            conn.commit()
    except sqlite3.IntegrityError as e:
        raise HTTPException(409, f"同名のソースが既に存在します: {name}") from e
    # 例外で接続を開いたまま抜けると暗黙BEGINの書き込みトランザクションが残留し、
    # 以後の全書き込みが busy_timeout(30s) 超過の "database is locked" になるため、
    # finally で必ず close する (close は未コミットの変更をロールバックする)。
    finally:
        conn.close()
    if _existing is not None:
        # DD-CYN-0168: 既に在る source を返す。auto_scan が真なら、その source を
        #   `scan` し直す。
        # DD-CYN-0169 (欠陥§181): 発行時点の `falcon` の _do_scan には排他が無く、
        #   「既に走っていれば黙って戻す」という上の前提は成り立っていなかった
        #   (`chewie` にしか排他が無かった)。DD-CYN-0169 で `falcon/server.py` の
        #   _do_scan へ排他を移したため、いまは成り立つ。
        if auto_scan:
            threading.Thread(target=_do_scan, args=(_existing["id"],), daemon=True).start()
        return {
            "id": _existing["id"],
            "name": _existing["name"],
            "path": _existing["path"],
            "auto_scan": auto_scan,
            "already_registered": True,
        }
    if auto_scan:
        threading.Thread(target=_do_scan, args=(sid,), daemon=True).start()
    return {"id": sid, "name": name, "path": path, "auto_scan": auto_scan}


@router.get("/api/sources/{source_id}/open-in-finder", response_model=None)
def open_source_in_finder(request: Request, source_id: str):
    """Open the source path in OS file manager (macOS Finder / Windows Explorer / Linux xdg-open)."""
    _require_admin(request)
    conn = get_db()
    # connleak-fix-20260709: 例外時も必ず close する
    try:
        source = conn.execute("SELECT * FROM sources WHERE id = ?", (source_id,)).fetchone()
    finally:
        conn.close()
    if not source:
        raise HTTPException(404, "Source not found")
    src_path = os.path.abspath(os.path.expanduser(source["path"]))
    if not os.path.exists(src_path):
        # multi-ingest-roots-20260728: 404 文言も写像後のパスを出す (写像できない場合のみ従来文言)。
        _miss_disp = _map_ingest_roots(src_path) or src_path
        raise HTTPException(
            404,
            f"このソースのパスが現在の環境に存在しません。別のマシンで登録されたソースの可能性があります（path={_miss_disp}）。",
        )
    # fix2-D: コンテナ実行時は OS ファイルマネージャーを起動できない (xdg-open 不在・そもそも
    #   コンテナから Mac の Finder は開けない)。subprocess を呼ばず、ホスト側の場所を示すだけにして
    #   500/未捕捉例外を出さない。standalone (非コンテナ) は従来どおり Finder/Explorer/xdg-open。
    if os.path.exists("/run/.containerenv") or os.path.exists("/.dockerenv"):
        _box = "/app/ingest"
        # pathdisplay-20260706: 固定文言の決め打ちを廃し、管理者が Settings で申告した
        # 「取り込みフォルダの実際の場所」(settings key: ingest.host_path) を参照する。
        # 未申告時はパスを含まない中立文言（申告環境で嘘のガイドをしない）。表示専用・保存値不変。
        _host_base = ""
        try:
            _c2 = get_db()
            # connleak-fix-20260709: 例外時も必ず close する (外側 except は握り潰しのため内側で保証)
            try:
                _row = _c2.execute("SELECT value FROM settings WHERE key = ?", ("ingest.host_path",)).fetchone()
            finally:
                _c2.close()
            _host_base = (_row["value"] or "").strip() if _row else ""
        except Exception:
            _host_base = ""
        # multi-ingest-roots-20260728: 複数ルート (settings key: ingest.roots) の写像を優先し、
        # 写像できない場合のみ従来の ingest.host_path / 中立文言へ落とす。表示専用・保存値不変。
        _roots_hint = _map_ingest_roots(src_path)
        if src_path == _box or src_path.startswith(_box + os.sep):
            if _roots_hint:
                _msg = f"コンテナ実行のため Finder は開けません。実際の場所: {_roots_hint}"
            elif _host_base:
                _host_hint = _host_base.rstrip("/") + src_path[len(_box):]
                _msg = f"コンテナ実行のため Finder は開けません。実際の場所: {_host_hint}"
            else:
                _msg = "コンテナ実行のため Finder は開けません。取り込みフォルダ（起動時に指定した場所）内の該当フォルダを開いてください。"
        else:
            _msg = f"コンテナ実行のため Finder は開けません。コンテナ内パス: {_roots_hint or src_path}"
        return {"ok": True, "path": src_path, "opened_with": "container", "container": True, "message": _msg}
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
    # connleak-fix-20260709: 例外時も必ず close する
    try:
        src = conn.execute("SELECT id FROM sources WHERE id = ?", (source_id,)).fetchone()
        if not src:
            raise HTTPException(404, "Source not found")
        # 欠陥修正: 上のフラグはプロセス内メモリのみで、監視するスレッドが既に
        # 死んでいれば何も起きない。falcon には scan_jobs テーブルが存在しない
        # ため（chewie とは異なる。実装確認済み）、sources.status のみを直接
        # idle へ戻す。
        conn.execute(
            "UPDATE sources SET status='idle' WHERE id = ? AND status='scanning'",
            (source_id,),
        )
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "status": "cancel_requested", "source_id": source_id}


@router.post("/api/sources/{source_id}/scan", response_model=None)
def scan_source(request: Request, source_id: str):
    from server import _do_scan, row_to_dict

    _require_admin(request)
    conn = get_db()
    # connleak-fix-20260709: 例外時も必ず close する
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
    # connleak-fix-20260709: 例外時も必ず close する
    try:
        files = rows_to_list(conn.execute("SELECT * FROM files WHERE source_id = ? ORDER BY name", (source_id,)).fetchall())
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
    # connleak-fix-20260709: 例外時も必ず close する (書き込み txn 残留 = "database is locked" を防ぐ)
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
# B4: 取り込み元 (ルート) を画面から足す・見る・外す
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

    portable-roots-20260808 (F-2): バックアップには配布物のルートディレクトリからの相対の書き方
    ("@app/…") が入りうる。ここで生の JSON を直に読むと、その書き方のまま画面へ出て
    しまう。∴ 入口スクリプトと同じ部品 (scripts/ingest_roots.py) で読み、解いた
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
        # P-4: コンテナの中ではバックアップの host_path (機械側の場所) は必ず見えないため、
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
    # DD-CYN-0146 §150: 名前の割り当てが尽きた場合、name_for は SystemExit ではなく
    # ValueError を投げる（サーバは落とさない）。ここで受けて読める文言で断る。
    try:
        _name = _h.assign_name(_data, _real)
    except ValueError as _ne:
        raise HTTPException(409, f"取り込み元の名前を付けられませんでした: {_ne}") from _ne
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
