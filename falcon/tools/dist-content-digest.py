#!/usr/bin/env python3
"""配布物の「内容の一致」検査値を出す (dist-content-digest-20260731 / )。

使い方:
    python dist-content-digest.py <アプリのツリー> <demo.db> <chroma ディレクトリ>

出力は 1 行 1 項目の "名前<TAB>値"。2 回のパッケージングでこの出力が完全一致すれば
「内容としては同じもの」と判定できる。バイト単位の一致は要求しない。

なぜバイト単位で比べないか (実測で確定したこと):
  同じ入力から 2 回作っても、demo.db・chroma.sqlite3・HNSW のバイナリは必ず違う。
  違いの入手元は 6 つあり、いずれも直すべき欠陥ではない。
    ① 識別子が uuid4 (db.new_id)
    ② パスワードの塩と初期パスワードそのものが乱数
    ③ 時刻 (created_at / applied_at / publish_history.timestamp / elapsed_seconds)
    ④ 金庫の暗号化は同じ平文でも毎回違う暗号文を出す (初期化ベクトル)
    ⑤ 分類の並び順が list(set(...)) 由来で、文字列ハッシュの種に左右される
    ⑥ Chroma が書く metadata の JSON キー順
  一方で、塊の本文 (復号後)・埋め込みのベクトル・マスキングの件数・件数・取り込み元の
  相対パスは 3 回の実行で完全に一致した。よって同等性はこちらで判定する。

この検査が「同じに見えるが中身が違うもの」を捕まえることは、次の 4 通りの
陽性対照で確かめてある: 塊を1行消す / 本文を1文字書き換える (正しく再暗号化する) /
ベクトルを1本壊す / マスキングを1か所剥がす。いずれも出力が変わる。
"""
import hashlib, json, os, sqlite3, sys

APP, DB, CHROMA = (os.path.abspath(p) for p in sys.argv[1:4])
os.environ.setdefault("CYNOVELA_DATA_DIR", os.path.join(APP, "store"))
os.environ.setdefault("CYNOVELA_DB", DB)
os.environ.setdefault("CYNOVELA_CHROMA", CHROMA)
sys.path.insert(0, APP)
_cwd = os.getcwd(); os.chdir(APP)
from vault_enc import dec_raw          # noqa: E402
os.chdir(_cwd)

# 実行ごとに必ず変わる列/キー = 「内容」に数えないもの
VOLATILE_META = {"source_id", "workspace_id", "file_id", "file_path",
                 "parent_id", "logical_chunk_id", "vector_id"}

def h(parts):
    d = hashlib.sha256()
    for p in parts:
        d.update(p.encode("utf-8") if isinstance(p, str) else p)
        d.update(b"\x00")
    return d.hexdigest()

def emit(k, v): print(f"{k}\t{v}")

con = sqlite3.connect(DB); con.row_factory = sqlite3.Row

# ① 件数
for t in ["workspaces", "sources", "collections", "files",
          "chunks", "parent_chunks", "publish_history", "users"]:
    emit(f"count.{t}", con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])

# ② 取り込み元の相対パス (絶対パスはパッケージング先で変わるのでルートからの相対で見る)
roots = [r[0] for r in con.execute("SELECT path FROM sources ORDER BY path")]
def rel(p):
    for r in sorted(roots, key=len, reverse=True):
        if p == r: return "."
        if p.startswith(r.rstrip("/") + "/"): return p[len(r.rstrip("/")) + 1:]
    return p
emit("paths.sources", h(sorted(os.path.basename(r.rstrip("/")) for r in roots)))
emit("paths.files", h(sorted(rel(r[0]) for r in con.execute("SELECT path FROM files"))))
emit("paths.files.list", "|".join(sorted(rel(r[0]) for r in con.execute("SELECT path FROM files"))))

# ③ 塊の本文 (復号後・並べ替えて連結)
for tbl in ("chunks", "parent_chunks"):
    for tier in ("raw", "masked"):
        vals = sorted(dec_raw(r[0]) for r in
                      con.execute(f"SELECT content FROM {tbl} WHERE tier=?", (tier,)))
        emit(f"body.{tbl}.{tier}.n", len(vals))
        emit(f"body.{tbl}.{tier}.sha256", h(vals))

# ④ マスキングの件数と塊の統計
r = con.execute("SELECT doc_count, chunk_count, pii_count, excluded_count, "
                "avg_chunk_chars FROM publish_history ORDER BY id").fetchall()
emit("publish_history", h([json.dumps([dict(x) for x in r], sort_keys=True)]))
emit("chunks.dist", h([json.dumps([tuple(x) for x in con.execute(
    "SELECT tier, pii_detected, excluded, COUNT(*), SUM(char_count) "
    "FROM chunks GROUP BY tier, pii_detected, excluded ORDER BY 1,2,3")], sort_keys=True)]))

# ⑤ 分類 (順序に依らないよう並べ替える)
emit("files.categories", h(sorted(
    json.dumps(sorted(json.loads(r[1] or "[]")), ensure_ascii=False) + "@" + r[0]
    for r in con.execute("SELECT name, categories FROM files"))))
emit("files.meta", h(sorted(
    f"{r['name']}|{r['size']}|{r['mime_type']}|{r['doc_type']}|{r['sensitivity']}|"
    f"{r['sensitivity_score']}|{r['classification']}"
    for r in con.execute("SELECT * FROM files"))))

# ⑥ 金庫が効いているか (平文で入っていないこと)
emit("chunks.enc_prefix_ratio", "%d/%d" % (
    con.execute("SELECT COUNT(*) FROM chunks WHERE tier='raw' AND content LIKE 'enc:%'").fetchone()[0],
    con.execute("SELECT COUNT(*) FROM chunks WHERE tier='raw'").fetchone()[0]))

# ⑦ Chroma: 本文集合・ベクトル・メタデータ (可変キーを除く)
cq = sqlite3.connect(os.path.join(CHROMA, "chroma.sqlite3")); cq.row_factory = sqlite3.Row
rows = []
for r in cq.execute("SELECT vector, encoding, metadata FROM embeddings_queue"):
    m = json.loads(r["metadata"])
    rows.append((m.get("chroma:document", ""), bytes(r["vector"]), r["encoding"],
                 {k: v for k, v in m.items() if k not in VOLATILE_META}))
rows.sort(key=lambda x: x[0])
emit("chroma.n", len(rows))
emit("chroma.documents.sha256", h([x[0] for x in rows]))
emit("chroma.vectors.sha256", h([x[1] for x in rows]))
emit("chroma.encodings", h([x[2] for x in rows]))
emit("chroma.metadata.sha256", h([json.dumps(x[3], sort_keys=True, ensure_ascii=False) for x in rows]))
emit("chroma.collection_suffix", h(sorted(
    r[0].split("__", 1)[-1] for r in cq.execute("SELECT name FROM collections"))))
emit("chroma.embedding_identity", h([open(os.path.join(CHROMA, "embedding_identity.json"), "rb").read()]))
