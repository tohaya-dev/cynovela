#!/usr/bin/env python3
"""build_bundled_data.py — 配布物に同梱する索引とデータベースを「梱包の場で」作る。

bundled-data-20260731 (DD-CYN-0007 B0):
  従来の tools/build-dist.sh は、同梱する store/db/demo.db と store/vector を
  **開発機の作業ツリーからそのまま複製**していた。作業ツリーの中身は開発の過程で
  溜まったもの (旧世代の資料・撤去したはずの作業場所・開発機の利用者名) を含むため、
  配布物の中身の出どころを言えなかった。実測では梱包直前の検査が実際に停止していた。

  本スクリプトは、配布物の中に同梱されるダミー資料 (dummy-corpus/) だけを入力にして、
  ステージの中で索引とデータベースを作る。よって同梱データの出どころは
  「この配布物の中の dummy-corpus」だけになる。作業ツリーは読まない。

使い方 (tools/build-dist.sh から呼ばれる):
    python tools/build_bundled_data.py <ステージのツリー>

前提:
  - <ステージのツリー>/dummy-corpus/ に資料が在ること
  - <ステージのツリー>/store/secret.key に金庫鍵が置かれていること
    (この鍵で暗号化するので、同梱する鍵と中身が必ず噛み合う)
  - <ステージのツリー>/store/models に埋め込みモデルが在ること
    (軽量版では同梱しないので、呼び出し側が梱包中だけ読み取り専用で繋ぎ、
     作り終えたら外す)

決まった値 (乱数にしない):
  取り込み元 / 作業場所 / コレクションの id は固定文字列にする。db.py の初期化処理が
  デモ起動のたびに INSERT OR IGNORE する取り込み元と同じ id ('src-dummy') にしてある
  ため、受け取り手の環境で同じ置き場が二重に登録されない。

出力: 標準出力へ「作った中身の数え上げ」を1行の JSON で書く。
      呼び出し側はこれを一覧文書の件数に使う。
"""
import json
import os
import sys
import time

# 固定の識別子 (乱数にしない。db.py の demo_sources と id を合わせる)
SRC_ID = "src-dummy"
WS_ID = "ws-dummy"
COL_ID = "col-dummy"
SRC_NAME = "ダミー資料 (アオゾラ商事)"
WS_NAME = "アオゾラ資料"
COL_NAME = "デモ資料一式"


def main() -> int:
    if len(sys.argv) < 2:
        print("使い方: build_bundled_data.py <ステージのツリー>", file=sys.stderr)
        return 2
    app = os.path.abspath(sys.argv[1])
    corpus = os.path.join(app, "dummy-corpus")
    store = os.path.join(app, "store")

    if not os.path.isdir(corpus):
        print(f"[bundled] ダミー資料が見つかりません: {corpus}", file=sys.stderr)
        return 1
    if not os.path.isfile(os.path.join(store, "secret.key")):
        print(f"[bundled] 金庫鍵が見つかりません: {store}/secret.key", file=sys.stderr)
        return 1
    if not os.path.isdir(os.path.join(store, "models")):
        print(f"[bundled] 埋め込みモデルが見つかりません: {store}/models", file=sys.stderr)
        return 1

    # 置き場をステージの中へ固定する。
    # DD-CYN-0069 M-2: 「server.py は setdefault で置くので、先に置けば勝つ」は
    #   DD-CYN-0053 以後の現行と食い違う。server.py は import 時に cynovela.yaml の
    #   paths と sys.argv の --demo の有無から置き場を決め、下の環境変数を無条件に
    #   入れ直す (server.py の DD-CYN-0053 注記)。--demo が立っていないと索引が
    #   store/vector/default (引数なし側) へ作られ、同梱データ (store/db/demo.db =
    #   --demo 側) と別の側に落ちる。DD-CYN-0068 の受け入れで、受け取り手の --demo
    #   起動が空の索引を読み、出典つきの回答が返らないことが実測されている。
    #   ∴ server を読む前に sys.argv へ --demo を立て、索引をデモ側
    #   (store/vector/demo) へ作らせる。第1引数 (ステージ) は既に読み終えている。
    #   下の環境変数は server import までの db.py 初期化が読むため残す。
    os.environ["CYNOVELA_DATA_DIR"] = store
    os.environ["CYNOVELA_DB"] = os.path.join(store, "db", "demo.db")
    os.environ["CYNOVELA_CHROMA"] = os.path.join(store, "vector", "demo", "chroma")
    os.environ["CYNOVELA_LOG_DIR"] = os.path.join(store, "logs")
    os.environ["CYNOVELA_BACKUP_DIR"] = os.path.join(store, "backups")
    for d in ("db", "vector/demo", "logs", "backups"):
        os.makedirs(os.path.join(store, d), exist_ok=True)

    os.chdir(app)
    sys.path.insert(0, app)
    sys.argv = [sys.argv[0], "--demo"]

    import db as _db
    from db import get_db

    _db.init_db()

    import server  # noqa: E402  (置き場を決めたあとに読む)
    from rag import publish_collection  # noqa: E402

    # DD-CYN-0069 M-2 連動: 梱包の埋め込みは、受け取り手と同じローカルの経路で行う。
    #   開発機の cynovela.yaml が外の口 (external) を指していると、梱包は EF (embedding
    #   function) を注入せずにコレクションを作り、その設定が索引へ永続化される。
    #   受け取り手の実行時はローカル埋め込みで EF を注入するため、chroma 1.5 系の
    #   整合検査が「persisted: default vs new: sentence_transformer」で例外を出し、
    #   照会は0件に握り潰され、公開のし直しは失敗する (DD-CYN-0069 §7 で実測)。
    #   ここで既定 (= ローカル bge-m3) のプロバイダへ明示的に切り替え、
    #   受け取り手と同じ形でコレクションを作らせる。server.py には触れていない。
    import rag as _rag_mod  # noqa: E402
    from providers.embedding import get_embedding_provider as _gep  # noqa: E402

    _rag_mod.set_embedding_provider(_gep({}))
    print("[bundled] 埋め込みは受け取り手と同じローカルの経路で行う (外の口は使わない)")

    conn = get_db()
    try:
        # 取り込み元は**絶対**で書く。そのあと tools/build_clean_demo_db.py が
        # 「取り込み元の絶対パス → ./<最後の名前>」の対応表を作り、その対応表を
        # files / file_hashes / document_lineage へ波及させて相対化する。ここを相対で
        # 入れると対応表が空になり、files 系に取り込み時の絶対パスが残る
        # (実測: 7 ファイル × 3 表 = 21 件が残り、梱包が検査で止まった)。
        conn.execute(
            "INSERT OR IGNORE INTO sources (id, name, path, status) VALUES (?, ?, ?, 'idle')",
            (SRC_ID, SRC_NAME, corpus),
        )
        conn.execute("INSERT OR IGNORE INTO workspaces (id, name) VALUES (?, ?)", (WS_ID, WS_NAME))
        conn.execute(
            "INSERT OR IGNORE INTO workspace_sources (workspace_id, source_id) VALUES (?, ?)",
            (WS_ID, SRC_ID),
        )
        for uid in [r["id"] for r in conn.execute("SELECT id FROM users").fetchall()]:
            conn.execute(
                "INSERT OR IGNORE INTO workspace_users (workspace_id, user_id) VALUES (?, ?)",
                (WS_ID, uid),
            )
        conn.commit()
    finally:
        conn.close()

    # 取り込み元を読み、files 行を作る
    server._do_scan(SRC_ID)

    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT id, path FROM files WHERE source_id = ? ORDER BY name", (SRC_ID,)
        ).fetchall()
        file_ids = [r["id"] for r in rows]
        file_paths = [r["path"] for r in rows]
        conn.execute(
            "INSERT OR IGNORE INTO collections (id, name, workspace_id, access_level, allowed_roles_json) "
            "VALUES (?, ?, ?, 'public', ?)",
            (COL_ID, COL_NAME, WS_ID, json.dumps(["admin", "viewer"])),
        )
        for fid in file_ids:
            conn.execute(
                "INSERT OR IGNORE INTO collection_files (collection_id, file_id) VALUES (?, ?)",
                (COL_ID, fid),
            )
        conn.commit()
    finally:
        conn.close()

    if not file_paths:
        print("[bundled] 取り込めた資料が 0 件です", file=sys.stderr)
        return 1

    # 刻みは既定引数 (500/50) ではなくアプリ本体と同じ経路で解く (cynovela.yaml の 256/32)
    cs, co = server._resolve_collection_chunking(COL_ID)
    print(f"[bundled] 刻み chunk_size={cs} chunk_overlap={co}")
    t0 = time.time()
    # gui-fix-20260803 (DD-CYN-0022): publish_collection は塊の数を返す。
    #   ここはその戻り値を捨てて status だけを書いていたため、collections.chunk_count が
    #   作られたときの既定値 0 のまま残り、画面のコレクション一覧が 0 と出ていた
    #   (chunks 表には実体が入っているので「0 なのに引ける」状態だった)。
    #   画面から publish した場合と同じ書き方に揃える (routers/collections.py の
    #   "UPDATE collections SET status='ready', chunk_count=?" と同じ値・同じ意味)。
    _chunk_count = publish_collection(COL_ID, file_paths, chunk_size=cs, chunk_overlap=co)
    elapsed = time.time() - t0

    conn = get_db()
    try:
        conn.execute(
            "UPDATE collections SET status='ready', chunk_count = ? WHERE id = ?",
            (int(_chunk_count or 0), COL_ID),
        )
        server._finalize_publish_success(conn, COL_ID, WS_ID, file_paths, elapsed)
        conn.commit()
    finally:
        conn.close()

    # 数え上げ (一覧文書の件数と、受け入れの検査に使う)
    conn = get_db()
    try:
        counts = {}
        for t in ("workspaces", "sources", "collections", "files", "chunks", "parent_chunks"):
            counts[t] = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        # publish_history は collection_id を持たない (workspace_id 単位の記録)
        ph = conn.execute(
            "SELECT doc_count, chunk_count, pii_count FROM publish_history "
            "WHERE workspace_id = ? ORDER BY id DESC LIMIT 1",
            (WS_ID,),
        ).fetchone()
        if ph is not None:
            counts["doc_count"] = ph["doc_count"]
            counts["pii_count"] = ph["pii_count"]
    finally:
        conn.close()

    print("[bundled] 作った中身: " + json.dumps(counts, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
