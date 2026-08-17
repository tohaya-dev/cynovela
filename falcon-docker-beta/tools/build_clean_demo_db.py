#!/usr/bin/env python3
"""build_clean_demo_db.py — 配布用 demo.db クリーン生成 (Cynovela Phase 1)

目的: 出荷 store/db/demo.db に残る「閲覧者ログイン不可 (旧テスト由来の陳腐化ハッシュ)」
      とテスト残渣 (102 ユーザー / 23k 監査ログ等) を、正規 RAG コーパス
      (chunks / parent_chunks / collections / files / デモ WS) を温存したまま除去する。

方針 (CLAUDE.md 準拠):
  - INSERT OR REPLACE 禁止 → 既存行更新は UPDATE / ON CONFLICT を使う
  - ChromaDB と SQLite を desync させないため source 行は削除しない
    (source 削除は CASCADE で files/collection_files を巻き込むがベクトルは残るため)
  - hash_password は db.py:733 の実装を逐語複製 (import 副作用回避・想像でなく検証済み)

使い方:
  python tools/build_clean_demo_db.py <SRC demo.db> <OUT demo.db> [削除行の保全先dir] \
      [--admin-password 値] [--viewer-password 値] [--admin-password-out 書き出し先]

初期パスワード (pw-out-of-code-20260727 / pw-not-on-screen-20260727 /
                pw-out-of-code-20260729 C-B9):
  管理者・デモ用閲覧者とも平文をコードに書かない。--admin-password / --viewer-password で
  受け取り、指定が無ければその場で乱数を生成する。
  生成した値は **標準出力に出さない**。--admin-password-out で指定したファイルへ 0600 で
  「資格情報のバックアップ」としてまとめて書き出すだけにする
  (画面・端末の記録・作業ログに平文が残らないようにするため)。
  いずれかを生成する場合に --admin-password-out が無ければエラーで止める (逃げ道を作らない)。
  バックアップは配布物 tar の外に置かれるので、配る人はこのファイルだけを見て初期パスワードを知る。
  管理者は must_change_password=1 で初回ログイン時に変更を強制する。
"""
import os
import re
import sqlite3
import sys
import hashlib
import secrets
import shutil

# --- db.py:733-736 を逐語複製 (PBKDF2-HMAC-SHA256, 100000, "salt:hex") ---
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return f"{salt}:{h.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    if not stored_hash or ":" not in stored_hash:
        return False
    salt, expected = stored_hash.split(":", 1)
    h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return secrets.compare_digest(h.hex(), expected)


CANON_USERS = ("user-admin", "user-scientist")
# 利用者名は秘密ではないので定数で持つ (秘密なのはパスワードだけ)。
ADMIN_USERNAME = "cynovela"
VIEWER_USERNAME = "demo"

# 実行時/テスト残渣テーブル (RAG コーパスへの inbound FK なし → 安全に空にできる)
# key-vector-fix-20260721 (Part E): messages / message_rag_refs / sessions は全消去を
# やめ、テスト由来のみ選別除去する (_selective_conversation_cleanup)。デモ由来の
# 会話記録は取り込み・マスキングのデモ材料として配布物に残す (迷うものは残す側に倒す)。
RUNTIME_RESIDUE = (
    "audit_logs", "admin_change_log",
    "refresh_tokens", "processing_logs", "feedback", "reports",
    "publish_jobs", "collection_locks",
)

# シード撤去で新DBから消えたデモ作業場所 (seed-ws-removal-20260730)。
# ws-protect-by-name-20260727 の「元DBの WS が1つも欠けていない」検査は、
# 過去に作られた DB を src に使うとこの3件で必ず落ちる。撤去は意図した変更なので
# 判定から除外する (それ以外の WS が欠けたら従来どおり FAIL にする)。
SEED_WS_REMOVED = ("ws-sales", "ws-tech", "ws-hr")


def _clear_all_conversations(conn, dump_dir: str | None) -> dict:
    """dist-no-history-20260727: 配布物の会話記録を全消去する。

    従来は「テスト由来のみ選別除去し、デモ由来の会話はマスキングデモの材料として残す」方針
    (key-vector-fix-20260721 Part E) だったが、配布物では次の2つの理由で成立しない。

    1. 他人の会話履歴が配布物に入る。前実行の配布物には falcon 2行・chewie 4行
       (計 4,716文字) が残っていた。
    2. **配布物は secret.key を同梱しない。** 残った本文は `enc:` の暗号文のまま
       復号できず、管理者経路のプロンプトへそのまま流れる。chewie ではこれで回答が
       「該当なし」に落ちた (事実108-6)。マスキングデモの材料になるどころか壊す。

    セッションの器も消す。本文の無いセッションは画面上「題だけあって中身が空の会話」
    として並び、受け取り手には取りこぼしにしか見えないため (迷うものは残す、の対象外)。
    実行順: refs → messages → sessions (削除後では JOIN が引けなくなるため)。
    dump_dir 指定時は、消す対象の全行を JSONL で書き出してから消す。
    """
    import json as _json
    import os as _os

    out: dict = {}

    def _dump_all(table: str):
        if not dump_dir:
            return
        rows = [dict(r) for r in conn.execute(f"SELECT * FROM {table}").fetchall()]
        _os.makedirs(dump_dir, exist_ok=True)
        with open(_os.path.join(dump_dir, f"removed-{table}.jsonl"), "w", encoding="utf-8") as f:
            for r in rows:
                f.write(_json.dumps(r, ensure_ascii=False, default=str) + "\n")
        out[f"dumped_{table}"] = len(rows)

    for _t in ("message_rag_refs", "messages", "sessions"):
        _dump_all(_t)
    out["refs_removed"] = conn.execute("DELETE FROM message_rag_refs").rowcount
    out["messages_removed"] = conn.execute("DELETE FROM messages").rowcount
    out["sessions_removed"] = conn.execute("DELETE FROM sessions").rowcount
    out["messages_kept"] = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    out["sessions_kept"] = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    out["refs_kept"] = conn.execute("SELECT COUNT(*) FROM message_rag_refs").fetchone()[0]

    # bundled-config-20260731: 形態によって正解が変わる設定値を同梱 DB に焼き込まない。
    #   settings.llm_endpoint は db.py が core.llm.default_llm_endpoint() で種を入れるが、
    #   その評価はこの DB を作る機械 (ホスト) の上で起きるため localhost が固定されてしまう。
    #   INSERT OR IGNORE なので受け取り手の環境で再評価されることは二度と無く、コンテナ形態
    #   では自コンテナを指して最初の質問が必ず失敗していた。
    #   行を落としておけば、受け取り手の初回起動時に db.py が形態を見て正しい値を入れる
    #   (直起動なら localhost、コンテナなら host.containers.internal)。
    #   起動の選択肢は増やさない。値を固定せず、起動時に解決させるだけ。
    out["llm_endpoint_removed"] = conn.execute(
        "DELETE FROM settings WHERE key = 'llm_endpoint'"
    ).rowcount
    return out


def _selective_conversation_cleanup(conn, dump_dir: str | None) -> dict:
    """テスト由来の会話記録のみを除く (key-vector-fix-20260721 Part E)。

    dist-no-history-20260727 以降、配布物の生成では使わない (_clear_all_conversations が
    全消去する)。稼働 DB の手入れ用として残す。

    判定条件 (Tier1・機械的に断定できるもののみ):
      (A) 削除済みユーザー由来のセッション (sessions.user_id が users に不在)
      (B) 削除済みワークスペース由来のセッション (sessions.workspace_id が workspaces に不在)
    テスト命名だが生存 WS のもの (Tier2) は「迷うものは残す」原則で残す。
    実行順: refs → messages → sessions (削除後では JOIN が引けなくなるため)。
    dump_dir 指定時は、消す対象の全行を JSONL で書き出してから消す。
    """
    import json as _json
    import os as _os

    cond_sessions = (
        "SELECT id FROM sessions WHERE user_id NOT IN (SELECT id FROM users) "
        "OR workspace_id NOT IN (SELECT id FROM workspaces)"
    )
    out: dict = {}

    def _dump(table: str, sql: str, params=()):
        if not dump_dir:
            return
        rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
        _os.makedirs(dump_dir, exist_ok=True)
        path = _os.path.join(dump_dir, f"removed-{table}.jsonl")
        with open(path, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(_json.dumps(r, ensure_ascii=False) + "\n")
        out[f"dumped_{table}"] = len(rows)

    _dump("message_rag_refs",
          f"SELECT * FROM message_rag_refs WHERE message_id IN "
          f"(SELECT id FROM messages WHERE session_id IN ({cond_sessions}))")
    _dump("messages", f"SELECT * FROM messages WHERE session_id IN ({cond_sessions})")
    _dump("sessions", cond_sessions.replace("SELECT id", "SELECT *", 1))

    out["refs_removed"] = conn.execute(
        f"DELETE FROM message_rag_refs WHERE message_id IN "
        f"(SELECT id FROM messages WHERE session_id IN ({cond_sessions}))"
    ).rowcount
    out["messages_removed"] = conn.execute(
        f"DELETE FROM messages WHERE session_id IN ({cond_sessions})"
    ).rowcount
    out["sessions_removed"] = conn.execute(
        "DELETE FROM sessions WHERE user_id NOT IN (SELECT id FROM users) "
        "OR workspace_id NOT IN (SELECT id FROM workspaces)"
    ).rowcount
    # 安全網: 孤立 refs を残さない (通常 0 件のはず)
    out["orphan_refs_removed"] = conn.execute(
        "DELETE FROM message_rag_refs WHERE message_id NOT IN (SELECT id FROM messages)"
    ).rowcount
    out["messages_kept"] = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    out["sessions_kept"] = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    out["refs_kept"] = conn.execute("SELECT COUNT(*) FROM message_rag_refs").fetchone()[0]
    return out


# 参照先の書き換え対象 (パスを持つ列)。demo.db 内でファイルパスを保持する列は
# この4つ (全表・全TEXT列の LIKE 走査で他列ヒット無しを実測済み・mba-launch-20260728)。
_PATH_COLUMNS = (
    ("sources", "path"),
    ("files", "path"),
    ("file_hashes", "file_path"),
    ("document_lineage", "source_path"),
)


def _relocate_source_paths(conn) -> dict:
    """mba-launch-20260728: 同梱デモデータの参照先を、配布物を展開したフォルダからの
    相対の位置に改める。

    配布物の demo.db には開発機の絶対パス (/Users/<開発機の利用者名>/... や、
    旧コンテナの /app/...) を指す sources.path が残っており、受け取り先では
    再取り込み (rescan) が「パスが見つかりません: /Users/<開発機の利用者名>/...」で
    失敗し、失敗表示に開発機の利用者名まで露出していた。

    書き換え規則 (絶対パスのみ対象・相対パスは触らない):
      - /store/uploads/ を含む絶対パス -> ./store/uploads/<以下同じ>
        (ga-close-v3 PartA で廃止した保管領域。原本は配布物に同梱しない方針のため
         受け取り先では引き続き資料は無いが、参照は展開フォルダ内の相対位置になり
         利用者名も出なくなる)
      - その他の絶対パス -> ./<最後の要素> (例: /Users/x/Downloads/foo -> ./foo)
    files.path / file_hashes.file_path / document_lineage.source_path は
    sources.path の旧値を接頭辞に持つ行を同じ置換で揃える (file_id は
    source_id|path から導出されるため、参照の食い違いを残さないため)。
    相対パスは実行時のカレント (start.sh が cd するアプリのルート) 基準で解決される。
    """
    def _new_path(p: str) -> str:
        if not p.startswith("/"):
            return p  # 相対参照 (./sample_data 等・同梱済みで動作実測済み) は触らない
        if "/store/uploads/" in p:
            return "./store/uploads/" + p.split("/store/uploads/", 1)[1]
        return "./" + p.rstrip("/").rsplit("/", 1)[1]

    mapping: dict[str, str] = {}
    for sid, p in conn.execute("SELECT id, path FROM sources").fetchall():
        np = _new_path(p)
        if np != p:
            conn.execute("UPDATE sources SET path = ? WHERE id = ?", (np, sid))
            mapping[p] = np
    updated = {"sources": len(mapping)}
    for table, col in _PATH_COLUMNS[1:]:
        n = 0
        for old, new in mapping.items():
            n += conn.execute(
                f"UPDATE {table} SET {col} = ? || substr({col}, ?) "
                f"WHERE {col} = ? OR {col} LIKE ? || '/%'",
                (new, len(old) + 1, old, old),
            ).rowcount
        updated[table] = n
    updated["mapping"] = mapping
    return updated



# ── N-1 (DD-CYN-0020): インデックス (chroma.sqlite3) に焼き込まれた絶対パスの正規化 ──────────
# demo.db 側 (_relocate_source_paths) は 2026-07-28 から相対化しているが、インデックスの
# embedding_metadata.file_path ほかには取り込み時の**絶対**パスがそのまま残る。
# 実測 2026-08-02 (本流の作業ツリー・読み取りのみ):
#   chewie 26,371 セル / falcon 26 セル / hansolo 0 セル (インデックス自体が空)
#   内訳 (chewie): embedding_metadata.string_value 25,752 /
#                  embeddings_queue.metadata 491 / embedding_fulltext_search 63 ×2 /
#                  collections.schema_str 2
# 取り込み元を相対で入れてもインデックスには絶対パスが焼き込まれる (ossinit-20260729 の知見)。
# そのため「全表・全 TEXT 列を走査して置換する」形を採る。列を名指しすると、
# chroma の版が変わって列が増えたときに取りこぼす。
_CHROMA_FTS_SHADOW = ("_data", "_idx", "_docsize", "_config", "_content")


def _chroma_text_columns(con):
    """chroma.sqlite3 の (表, 列) のうち文字列を持ちうるものを列挙する。

    FTS5 の影の表 (…_data / _idx / _docsize / _config / _content) は直接書かない。
    影を直接書くとインデックスと中身が食い違うため、仮想表そのものを更新する。
    """
    fts = set()
    tables = []
    for name, sql in con.execute(
        "SELECT name, sql FROM sqlite_master WHERE type IN ('table','view')"
    ).fetchall():
        if sql and "VIRTUAL TABLE" in sql.upper() and "FTS" in sql.upper():
            fts.add(name)
        tables.append(name)
    out = []
    for t in tables:
        if any(t.endswith(s) and t[: -len(s)] in fts for s in _CHROMA_FTS_SHADOW):
            continue
        if t.startswith("sqlite_"):
            continue
        try:
            cols = con.execute(f'PRAGMA table_info("{t}")').fetchall()
        except sqlite3.DatabaseError:
            continue
        for c in cols:
            cname, ctype = c[1], (c[2] or "").upper()
            if ctype == "" or "CHAR" in ctype or "TEXT" in ctype or "CLOB" in ctype:
                out.append((t, cname))
    return out


def _chroma_rules(mapping: dict, app_root: str) -> list:
    """置換規則を (長い順) で作る。demo.db と同じ書き換え規則に揃える。"""
    rules = [(old.rstrip("/"), new.rstrip("/")) for old, new in mapping.items()]
    # 廃止済みの保管領域 (ga-close-v3 PartA) を指す絶対パス。demo.db 側と同じ形にする。
    rules.append((app_root.rstrip("/") + "/store/uploads", "./store/uploads"))
    # 最後に、パッケージングを作った場所そのもの。ここまでで拾えなかった参照を展開フォルダ相対にする。
    rules.append((app_root.rstrip("/"), "."))
    rules.sort(key=lambda r: len(r[0]), reverse=True)
    return rules


# 資料本文そのものを持つ行 (chroma:document と全文検索のコピー) は書き換えない。
# 本文の中に絶対パスが書かれているのは資料の中身であって、道具が勝手に改めるものではない
# (実測 2026-08-02: 印刷footer に file:///Users/… を含む HTML が同梱資料に在る)。
_CHROMA_DOC_KEY = "chroma:document"
# 保存先 (store 配下) を指す絶対パスは、どの機材で作っても展開フォルダ相対にできる。
_CHROMA_STORE_RE = re.compile(r"""[^"'\s]*?/store/(uploads|models|vector|db)(?=[/"'\s]|$)""")


def _relocate_chroma_paths(chroma_sqlite: str, mapping: dict, app_root: str) -> dict:
    """インデックスの全 TEXT 列から作った機材の絶対パスを取り除き、展開フォルダ相対へ改める。

    戻り値:
      replaced        置換したセル数
      leftover_abs    参照 (メタデータ) 側に残った作った機材の絶対パスのセル数
                      → 0 件をパッケージングの合格条件にする (取りこぼしたら止める)
      leftover_in_doc 資料本文の中に書かれている絶対パスのセル数 (道具では書き換えない)
    """
    home = os.path.expanduser("~")
    res = {"file": chroma_sqlite, "replaced": 0, "leftover_abs": 0,
           "leftover_in_doc": 0, "leftover_in_queue": 0, "by_rule": {}}
    if not os.path.exists(chroma_sqlite):
        res["skipped"] = "インデックスが無い"
        return res
    con = sqlite3.connect(chroma_sqlite)
    try:
        cols = _chroma_text_columns(con)
        # 1) 対応表と作った場所そのものを、そのまま置き換える
        for old, new in _chroma_rules(mapping, app_root):
            n_rule = 0
            for t, c in cols:
                try:
                    cur = con.execute(
                        f'UPDATE "{t}" SET "{c}" = replace("{c}", ?, ?) WHERE "{c}" LIKE ?',
                        (old, new, f"%{old}%"),
                    )
                    n_rule += cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0
                except sqlite3.DatabaseError:
                    continue
            if n_rule:
                res["by_rule"][old] = n_rule
                res["replaced"] += n_rule
        con.commit()
        # 2) 取りこぼし (別の作業ツリーで作ったインデックスを持ち込んだ等) を正規表現で詰める。
        #    保存先 (store 配下) を指す絶対パスだけが対象。資料本文の行は触らない。
        n_re = 0
        for t, c in cols:
            if t.startswith("embedding_fulltext_search"):
                continue
            try:
                rows = con.execute(
                    f'SELECT rowid, "{c}" FROM "{t}" WHERE "{c}" GLOB ?', (f"*{home}*",)
                ).fetchall()
            except sqlite3.DatabaseError:
                continue
            for rid, val in rows:
                if not isinstance(val, str):
                    continue
                if t == "embedding_metadata":
                    krow = con.execute(
                        "SELECT key FROM embedding_metadata WHERE rowid = ?", (rid,)
                    ).fetchone()
                    if krow and krow[0] == _CHROMA_DOC_KEY:
                        continue
                nv = _CHROMA_STORE_RE.sub(lambda m: "./store/" + m.group(1), val)
                if nv != val:
                    con.execute(f'UPDATE "{t}" SET "{c}" = ? WHERE rowid = ?', (nv, rid))
                    n_re += 1
        if n_re:
            res["by_rule"]["<store 配下を指す絶対パス>"] = n_re
            res["replaced"] += n_re
        con.commit()
        # 3) 残りを数える。参照側と資料本文側を分けて数える。
        for t, c in cols:
            try:
                if t == "embedding_metadata":
                    res["leftover_abs"] += con.execute(
                        'SELECT COUNT(*) FROM embedding_metadata WHERE string_value GLOB ?'
                        ' AND key <> ?', (f"*{home}*", _CHROMA_DOC_KEY)
                    ).fetchone()[0]
                    res["leftover_in_doc"] += con.execute(
                        'SELECT COUNT(*) FROM embedding_metadata WHERE string_value GLOB ?'
                        ' AND key = ?', (f"*{home}*", _CHROMA_DOC_KEY)
                    ).fetchone()[0]
                elif t.startswith("embedding_fulltext_search"):
                    res["leftover_in_doc"] += con.execute(
                        f'SELECT COUNT(*) FROM "{t}" WHERE "{c}" GLOB ?', (f"*{home}*",)
                    ).fetchone()[0]
                elif t == "embeddings_queue":
                    # chroma 内部の書き込み待ち行列。資料本文のコピーを含むため別に数える。
                    res["leftover_in_queue"] += con.execute(
                        f'SELECT COUNT(*) FROM "{t}" WHERE "{c}" GLOB ?', (f"*{home}*",)
                    ).fetchone()[0]
                else:
                    res["leftover_abs"] += con.execute(
                        f'SELECT COUNT(*) FROM "{t}" WHERE "{c}" GLOB ?', (f"*{home}*",)
                    ).fetchone()[0]
            except sqlite3.DatabaseError:
                continue
        con.commit()
        con.execute("VACUUM")
        con.commit()
    finally:
        con.close()
    return res


def _default_chroma_path(out_db: str) -> str:
    """<store>/db/demo.db から <store>/vector/demo/chroma/chroma.sqlite3 を導く。"""
    store = os.path.dirname(os.path.dirname(os.path.abspath(out_db)))
    return os.path.join(store, "vector", "demo", "chroma", "chroma.sqlite3")

def write_secret_file(path: str, value: str) -> None:
    """生成した初期パスワードを 0600 のファイルへ書く (画面には出さない)。

    pw-not-on-screen-20260727: 先に 0600 で作ってから書く。作ってから chmod だと
    書いた瞬間から権限を絞るまでの間、他人に読める状態が生じる。
    """
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(value + "\n")
    os.chmod(path, 0o600)


def credentials_text(admin_username: str, admin_pw: str,
                     viewer_username: str, viewer_pw: str) -> str:
    """資格情報のバックアップの中身を組み立てる (pw-out-of-code-20260729 / C-B9)。

    書き出し先は tar の外なので配布物には入らない。配る人はこのファイルだけを見て
    管理者と閲覧者の初期パスワードを知る (画面にも作業ログにも出さない)。
    """
    return (
        "# Cynovela 配布物の初期資格情報 (このバックアップは配布物 tar の外です・取り扱い注意)\n"
        f"admin_username={admin_username}\n"
        f"admin_password={admin_pw}\n"
        "# 管理者は初回ログイン時にパスワード変更を強制されます\n"
        f"viewer_username={viewer_username}\n"
        f"viewer_password={viewer_pw}"
    )


def main(src: str, out: str, dump_dir: str | None = None,
         admin_password: str | None = None,
         admin_password_out: str | None = None,
         viewer_password: str | None = None,
         chroma: str | None = None) -> int:
    # pw-not-on-screen-20260727: 作り始める前に判定する (途中で止めて出来損ないを残さない)
    if (admin_password is None or viewer_password is None) and not admin_password_out:
        print("[error] 初期パスワードを生成する場合は --admin-password-out <書き出し先> が必要です"
              " (画面には出さないため)")
        return 2
    shutil.copy2(src, out)
    conn = sqlite3.connect(out)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    before_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    # ws-protect-by-name-20260727: 元DBの作業場所をバックアップておき、1つも欠けていないことを検査する
    # (seed-ws-removal-20260730: 撤去済みシード3件 SEED_WS_REMOVED は判定から除外する)
    before_ws = [r[0] for r in conn.execute("SELECT id FROM workspaces ORDER BY id")]

    # 0) 資格情報の決定 (pw-out-of-code-20260727 / pw-out-of-code-20260729 C-B9)。
    #    管理者・閲覧者とも平文をコードに書かない。引数で渡されなければその場で乱数を生成し、
    #    生成した値は標準出力に出さず 0600 のバックアップファイルへまとめて書くだけにする
    #    (pw-not-on-screen-20260727: 配布物を作る画面の記録に平文が残っていた)。
    admin_pw = admin_password if admin_password is not None else secrets.token_urlsafe(18)
    viewer_pw = viewer_password if viewer_password is not None else secrets.token_urlsafe(12)
    if admin_password is None or viewer_password is None:
        write_secret_file(
            admin_password_out,
            credentials_text(ADMIN_USERNAME, admin_pw, VIEWER_USERNAME, viewer_pw),
        )
        print(f"[credentials] 生成値を書き出しました: {admin_password_out} (mode 600・画面には出しません)")

    # 1) 閲覧者 (user-scientist) を再シード (陳腐化ハッシュ解消)。
    conn.execute(
        "UPDATE users SET username = ?, password_hash = ?, must_change_password = 0, "
        "name = 'Viewer', display_name = 'Viewer', role = 'viewer' WHERE id = ?",
        (VIEWER_USERNAME, hash_password(viewer_pw), "user-scientist"),
    )
    # 2) 管理者 (user-admin): 上で決めた初期パスワードで再シードする。
    #    元DBのハッシュを温存しない(稼働系の値のハッシュを配布物に持ち出さない)。
    #    must_change_password=1 で初回ログイン時に強制変更モーダル
    #    (state.js:2509 -> _showMustChangePasswordModal)を発火させる。secret.key には触れない。
    conn.execute(
        "UPDATE users SET username = COALESCE(NULLIF(username,''),'cynovela'), "
        "password_hash = ?, must_change_password = 1, "
        "name = 'Admin', display_name = 'Admin', role = 'admin' WHERE id = ?",
        (hash_password(admin_pw), "user-admin"),
    )
    # 4) 残渣ユーザー削除 (canonical 3 以外)。CASCADE は refresh_tokens のみ・コーパス非影響。
    placeholders = ",".join("?" for _ in CANON_USERS)
    # Part3 (ga-20260720): 職能シード user-engineer の廃止に伴い、workspace_users の
    # 非カノン参照行を先に落とす (users への FK は CASCADE でないため)。
    conn.execute(
        f"DELETE FROM workspace_users WHERE user_id NOT IN ({placeholders})", CANON_USERS
    )
    deleted = conn.execute(
        f"DELETE FROM users WHERE id NOT IN ({placeholders})", CANON_USERS
    ).rowcount

    # 4b) dist-no-history-20260727: 配布物に他人の会話履歴を入れない。全消去する。
    #     (旧 Part E の選別除去は _selective_conversation_cleanup として残置・稼働DB用)
    conv = _clear_all_conversations(conn, dump_dir)

    # 4c) mba-launch-20260728: 参照先 (sources.path ほか) を展開フォルダ相対へ改める
    relocated = _relocate_source_paths(conn)

    # 4d) N-1 (DD-CYN-0020): インデックス (chroma.sqlite3) 側の絶対パスも同じ規則で相対へ改める。
    #     demo.db だけ相対化しても、インデックスには取り込み時の絶対パスが焼き込まれたまま残る
    #     (実測 2026-08-02: 本流の作業ツリーで chewie 26,371 セル / falcon 26 セル)。
    _chroma_path = chroma if chroma is not None else _default_chroma_path(out)
    _store_root = os.path.dirname(os.path.dirname(os.path.abspath(out)))
    _app_root = os.path.dirname(_store_root)
    chroma_res = _relocate_chroma_paths(_chroma_path, relocated.get("mapping", {}), _app_root)

    # 5) 実行時/テスト残渣テーブルを空にする (オフライン初期化・API 改ざんではない)
    cleared = {}
    existing = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    for t in RUNTIME_RESIDUE:
        if t in existing:
            cleared[t] = conn.execute(f"DELETE FROM {t}").rowcount

    conn.commit()
    conn.execute("VACUUM")
    conn.commit()

    # --- 検証 ---
    vrow = conn.execute("SELECT username, password_hash FROM users WHERE id='user-scientist'").fetchone()
    arow = conn.execute("SELECT username, password_hash, must_change_password FROM users WHERE id='user-admin'").fetchone()
    # pw-out-of-code-20260729 (C-B9): 閲覧者も上でシードした値(引数または乱数)に対して検証する。
    viewer_ok = (vrow and vrow["username"] == VIEWER_USERNAME
                 and verify_password(viewer_pw, vrow["password_hash"]))
    # pw-out-of-code-20260727: 管理者は上でシードした値(引数または乱数)に対して検証する。
    # 平文をコードに書かない。配布物は must_change_password=1 で初回変更を強制する。
    admin_ok = arow and arow["username"] == ADMIN_USERNAME and verify_password(admin_pw, arow["password_hash"])
    admin_must_change = bool(arow and arow["must_change_password"] == 1)
    after_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    ws = [r[0] for r in conn.execute("SELECT id FROM workspaces ORDER BY id")]
    nchunks = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    nfiles = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
    ncols = conn.execute("SELECT COUNT(*) FROM collections").fetchone()[0]
    fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    # dist-no-history-20260727: 会話履歴が1行も残っていないことを合格条件にする
    n_msgs = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    n_sess = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    n_refs = conn.execute("SELECT COUNT(*) FROM message_rag_refs").fetchone()[0]
    history_clean = (n_msgs == 0 and n_sess == 0 and n_refs == 0)
    # mba-launch-20260728: 参照先に絶対パスが1件も残っていないことを合格条件にする
    # (開発機の絶対パス・利用者名を配布物に持ち出さない)
    leftover_abs = 0
    for _t, _c in _PATH_COLUMNS:
        leftover_abs += conn.execute(
            f"SELECT COUNT(*) FROM {_t} WHERE {_c} LIKE '/%'"
        ).fetchone()[0]
    conn.close()

    print(f"[clean] users {before_users} -> {after_users} (deleted {deleted})")
    print(f"[clean] conversation cleanup (全消去): {conv}")
    print(f"[clean] cleared runtime tables: {cleared}")
    print(f"[clean] workspaces preserved: {ws}")
    print(f"[clean] corpus preserved: chunks={nchunks} files={nfiles} collections={ncols}")
    print(f"[verify] viewer {VIEWER_USERNAME}/(初期パスワードは引数または乱数・再表示しない) = {viewer_ok}")
    print(f"[verify] admin {ADMIN_USERNAME}/(初期パスワードは引数または乱数・再表示しない) = {admin_ok}")
    print(f"[verify] admin must_change_password = {admin_must_change}")
    print(f"[verify] FK violations: {len(fk_violations)} {fk_violations[:5]}")
    _lost_ws = [w for w in before_ws if w not in ws and w not in SEED_WS_REMOVED]
    protected_ok = not _lost_ws
    print(f"[verify] 元DBの WS が欠けていない = {not _lost_ws} (元 {len(before_ws)}件 / 後 {len(ws)}件 / 欠落 {_lost_ws} / 判定除外 {list(SEED_WS_REMOVED)})")
    print(f"[verify] 会話履歴 0行 = {history_clean} (messages={n_msgs} sessions={n_sess} refs={n_refs})")
    print(f"[clean] 参照先を展開フォルダ相対へ変更: {relocated}")
    print(f"[verify] 参照先に絶対パス残り 0件 = {leftover_abs == 0} (残り {leftover_abs}件)")
    print(f"[clean] インデックス (chroma.sqlite3) の絶対パスを相対へ変更: {chroma_res}")
    print(f"[verify] インデックスの参照に絶対パス残り 0件 = {chroma_res['leftover_abs'] == 0}"
          f" (残り {chroma_res['leftover_abs']}件)")
    print(f"[note]   インデックスの資料本文の中に書かれた絶対パス = {chroma_res['leftover_in_doc']}件"
          f" / 書き込み待ち行列の中 = {chroma_res['leftover_in_queue']}件"
          f" (どちらも資料の中身のコピーのため道具では書き換えない)")
    ok = (
        viewer_ok
        and admin_ok
        and admin_must_change
        and not fk_violations
        and protected_ok
        and history_clean
        and leftover_abs == 0
        and chroma_res["leftover_abs"] == 0
        and after_users == len(CANON_USERS)
    )
    print(f"[RESULT] {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    _argv = sys.argv[1:]
    _admin_password = None
    _admin_password_out = None
    _viewer_password = None
    _chroma = None
    for _flag in ("--admin-password", "--admin-password-out", "--viewer-password", "--chroma"):
        if _flag in _argv:
            _i = _argv.index(_flag)
            if _i + 1 >= len(_argv):
                print(f"{_flag} には値が必要です")
                sys.exit(2)
            if _flag == "--admin-password":
                _admin_password = _argv[_i + 1]
            elif _flag == "--viewer-password":
                _viewer_password = _argv[_i + 1]
            elif _flag == "--chroma":
                # ディレクトリを渡されたら中の chroma.sqlite3 を見る
                _chroma = _argv[_i + 1]
                if os.path.isdir(_chroma):
                    _chroma = os.path.join(_chroma, "chroma.sqlite3")
            else:
                _admin_password_out = _argv[_i + 1]
            del _argv[_i:_i + 2]
    if len(_argv) not in (2, 3):
        print(__doc__)
        print("使い方: python tools/build_clean_demo_db.py <SRC demo.db> <OUT demo.db> [削除行の保全先dir]"
              " [--admin-password 値] [--viewer-password 値] [--admin-password-out 書き出し先]")
        sys.exit(2)
    sys.exit(main(_argv[0], _argv[1], _argv[2] if len(_argv) == 3 else None,
                  _admin_password, _admin_password_out, _viewer_password, _chroma))
