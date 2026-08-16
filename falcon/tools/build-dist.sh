#!/usr/bin/env bash
# build-dist.sh — 配布物を「クリーンな取り出し」から組み立てる
#
# dist-reproducible-20260727:
#   従来は作業ツリーをそのまま固めていたため、ツリーで python を1回動かすだけで
#   config.py が store/secret.key と store/logs/ を作り、それが配布物に混入した
#   (前走行で実際に2本作り直している)。除外条件を足すだけでは、次に増える
#   未追跡ファイルには効かない。
#
#   本スクリプトは追跡ファイルだけを git archive で取り出し、同梱すべき追跡外の
#   ものを名指しで足す。よって「ツリーで何を実行したか」は結果に影響しない。
#
#   tar は決定論的に作る (所有者・時刻・並び順を固定し gzip はタイムスタンプ無し)
#   ため、同じ入力からは同じ指紋が出る。
#
# bundled-data-20260731 (DD-CYN-0007 B0):
#   同梱する索引 (store/vector) とデータベース (store/db/demo.db) は、**梱包の場で**
#   配布物内の dummy-corpus/ から作る。従来は作業ツリーのものを名指しで複製していたが、
#   作業ツリーは開発の過程で溜まったもの (旧世代の資料・撤去したはずの作業場所・
#   開発機の利用者名) を含み、配布物の中身の出どころを言えなかった。
#   実測では梱包直前の検査が実際に終了コード 1 で止まっていた。
#   作業ツリーから複製するのは store/models だけになった (提供元の公開配布物の写しで、
#   検査でも利用者名・資格情報とも 0 件)。
#
# 使い方:
#   tools/build-dist.sh <出力先ディレクトリ|出力先.tar.gz> <all-in-one|lightweight> [git-ref] [未使用] [金庫鍵]
#
# dist-date-20260729: 出力名の日付は手入力させず実行日から導出する
#   (過去に未来日付の手入力が配布物名に混入した)。第1引数がディレクトリなら
#   cynovela-<リポ名>-<形態>-<実行日YYYYMMDD>.tar.gz をその中へ自動生成する。
#   .tar.gz のフルネームを渡した場合、名前に含まれる 8 桁の数字列が実行日と
#   一致しないときは止まる。
#
# 前提: リポジトリのルートで実行する。demo.db は tools/build_clean_demo_db.py で
#       クリーン化したものを同梱する (会話履歴0行・監査残渣なし)。
#
# 第4引数は使わない (bundled-data-20260731 で「作り置きの demo.db を渡す」経路を廃止した。
# 同梱データは索引と対で作らなければ噛み合わないため)。第5引数の位置を保つために残してある。
# クリーン化はパスワードの塩を作り直すため、走らせるたびに DB のバイト列が変わる
# (塩を固定するのは論外)。よって**同じ配布物を2回作っても指紋は一致しない。**
# 同等性の判定は、塊の数・取り込み元・復号後の本文・埋め込みの一致で行うこと
# (詳しくは tools/build_bundled_data.py の頭書きと DD-CYN-0007 の記録)。
#
# 第5引数に金庫鍵 (store/secret.key) のパスを渡すと、それを同梱する。省略時の探索順は
# 下の resolve_vault_key() を参照。**新しい環境変数は 1 つも増やさない**。

set -euo pipefail

# ── 梱包直前の検査 (pretar-inspect-20260729) ─────────────────────────────
# tar で固める直前に、入ってはいけないものが STAGE に無いことを機械で確かめる。
# 1 件でも当たれば exit 非 0 で止まる (set -e 配下なので梱包はそこで終わる)。
# 検査は 3 種:
#   (a) 既知の資格情報。値そのものはこのリポジトリのどこにも置かず、
#       tools/dist-check-values.local (1 行 = 記号 TAB 文字数 TAB sha256全桁、
#       git 追跡外・mode 600) に文字数とハッシュだけを置いて照合する。
#       このファイルが無いときは検査ができないので梱包を止める (フェイルクローズ)。
#   (b) 開発機の利用者名。1 件でも当たれば止める。初期化後は 0 件が正であり、
#       既知除外は置かない (残すと次の混入を見逃す。旧 chroma.sqlite3 の
#       既知除外は dist-date-20260729 の走行で撤去)。
#   (c) 開発中の文書のファイル名。instructions/・docs/spec-raw/ のパス、
#       名前が instr-*・*指示書* のものが在れば止める。
# 出力には記号・箇所数・相対パスだけを書き、値そのものは決して書かない。
# 単体実行: tools/build-dist.sh inspect <ステージのディレクトリ> <検査値ファイル>
# 開発機の利用者名は実行時に導出する。リテラルで書くと本スクリプト自身が
# ステージに同梱されて検査(b)が自分を検出し、梱包が常に止まる(実測 20260729)。
DIST_DEV_USER="$(id -un)"

dist_inspect() {   # dist_inspect <STAGE/$NAME 相当のディレクトリ> <検査値ファイル>
  local stage="$1" values="$2" fail=0 n

  if [ ! -f "$values" ]; then
    echo "[inspect] 検査値ファイルが不在: $values" >&2
    echo "[inspect] フェイルクローズ: 検査ができないため梱包を止める" >&2
    return 1
  fi

  # (c) 開発中の文書のファイル名 ------------------------------------------
  local c_hits
  c_hits="$( (cd "$stage" && find . \
        \( -path './instructions' -o -path './instructions/*' \
        -o -path './docs/spec-raw' -o -path './docs/spec-raw/*' \
        -o -name 'instr-*' -o -name '*指示書*' \) -print) | sed 's|^\./||' || true)"
  if [ -n "$c_hits" ]; then
    n="$(printf '%s\n' "$c_hits" | wc -l | tr -d ' ')"
    echo "[inspect] (c) 開発中の文書のファイル名を検出: $n 件 (表示は先頭20件まで)" >&2
    printf '%s\n' "$c_hits" | head -20 | sed 's/^/[inspect]     /' >&2
    fail=1
  else
    echo "[inspect] (c) 開発中の文書のファイル名: 0件"
  fi

  # (b) 開発機の利用者名 --------------------------------------------------
  # 既知除外なし。初期化後は全ファイル 0 件が正で、除外を残すと次の混入を見逃す。
  local b_files f cnt
  b_files="$( (cd "$stage" && find . -type f -print0 \
        | xargs -0 grep -l --binary-files=text -e "$DIST_DEV_USER" -- /dev/null) \
        | sed 's|^\./||' || true)"
  if [ -n "$b_files" ]; then
    n="$(printf '%s\n' "$b_files" | wc -l | tr -d ' ')"
    echo "[inspect] (b) 開発機の利用者名を検出: $n ファイル (表示は先頭20件まで)" >&2
    while IFS= read -r f; do
      cnt="$( { grep -o --binary-files=text -e "$DIST_DEV_USER" -- "$stage/$f" || true; } | wc -l | tr -d ' ')"
      echo "[inspect]     $f: $cnt 箇所" >&2
    done < <(printf '%s\n' "$b_files" | head -20)
    fail=1
  else
    echo "[inspect] (b) 開発機の利用者名: 0件"
  fi

  # (a) 既知の資格情報 ----------------------------------------------------
  # テキスト系ファイルは行を直接読み、バイナリ (sqlite3・モデル等) は strings
  # 経由で英数記号の並びを取り出す。区切り文字で token に分け、検査値と同じ
  # 文字数の token だけを sha256 して照合する (値の平文はどこにも出さない)。
  # 記号 T5 は値がアプリ名と同一文字列のため、パスワード文脈 (前走行 N-12 と
  # 同じ限定式) に当たるときだけ検出とする (裸のアプリ名で誤検出させない)。
  if ! python3 - "$values" "$stage" <<'PYINSPECT'
import hashlib, os, re, subprocess, sys

values_path, stage = sys.argv[1], sys.argv[2]

targets = {}            # sha256(hex) -> 記号
lengths = set()
ctx_syms = {"T5"}       # パスワード文脈が要る記号 (値がアプリ名と同一文字列)
with open(values_path, encoding="utf-8") as fh:
    for ln in fh:
        ln = ln.rstrip("\n")
        if not ln or ln.startswith("#"):
            continue
        sym, length, digest = ln.split("\t")
        targets[digest.lower()] = sym
        lengths.add(int(length))
if not targets:
    print("[inspect] (a) 検査値ファイルに有効な行が無い (フェイルクローズ)")
    sys.exit(1)

minlen = min(lengths)
run_re = re.compile(r"[!-~]+")
delim_re = re.compile(r"""[\s"'`=:;,()<>\[\]{}|/\\]+""")
ctx_re = re.compile(r"""(?i)(password|passwd|\bpw\b|パスワード)[^\n]{0,20}?[=:：][ \t]*["'`]?$""")
word_re = re.compile(r"[\w.\-]")
# fixed-initial-credentials-20260802 (DD-CYN-0021 §3-2):
#   初期の合言葉は固定値になり、受け取り手が入れるように配布物の中の案内へ明記する。
#   ∴ その2つは「案内 (STARTUP.md)」と「設定 (cynovela.yaml)」に限って許す。
#   それ以外の場所 (データベース・記録・コード・作業の残りかす) に出たら従来どおり止める。
#   許した箇所も件数と場所を必ず画面へ出す (黙って通さない)。
allowed_paths = {          # 記号 -> 出てよい相対パスの集合
    "T3": {"STARTUP.md", "cynovela.yaml"},   # 管理者の初期の合言葉
    # DD-CYN-0070 N-4 連動: 閲覧者の値も設定 (auth.viewer_initial_password) に書く形に
    #   なったため、管理者と同じく cynovela.yaml を許す。他の場所は従来どおり止める。
    "T4": {"STARTUP.md", "cynovela.yaml"},   # 閲覧者の初期の合言葉
}
hits = {}               # (記号, 相対パス) -> 箇所数
allowed_hits = {}       # (記号, 相対パス) -> 箇所数 (許した分。止めないが必ず出す)

def scan_line(line, rel):
    # 1 行の全 run からまず候補集合を作る (同じ token を行内で二重に数えない)
    cands = set()
    for run in run_re.findall(line):
        cands.add(run)
        cands.update(delim_re.split(run))
    for c in list(cands):
        cands.add(c.strip(".,;"))
    for cand in cands:
        if len(cand) not in lengths:
            continue
        sym = targets.get(hashlib.sha256(cand.encode()).hexdigest())
        if sym is None:
            continue
        if sym in ctx_syms:
            ok, start = False, 0
            while True:
                i = line.find(cand, start)
                if i < 0:
                    break
                after = line[i + len(cand): i + len(cand) + 1]
                if ctx_re.search(line[:i]) and not (after and word_re.match(after)):
                    ok = True
                    break
                start = i + 1
            if not ok:
                continue
        key = (sym, rel)
        if rel in allowed_paths.get(sym, ()):
            allowed_hits[key] = allowed_hits.get(key, 0) + 1
            continue
        hits[key] = hits.get(key, 0) + 1

def looks_binary(path):
    with open(path, "rb") as fh:
        return b"\0" in fh.read(8192)

nfiles = 0
for dirpath, dirnames, filenames in os.walk(stage):
    dirnames.sort(); filenames.sort()
    for fn in filenames:
        path = os.path.join(dirpath, fn)
        if os.path.islink(path):
            continue
        nfiles += 1
        rel = os.path.relpath(path, stage)
        if looks_binary(path):
            p = subprocess.Popen(["strings", "-n", str(minlen), "--", path],
                                 stdout=subprocess.PIPE)
            for raw in p.stdout:
                scan_line(raw.decode("utf-8", "replace"), rel)
            p.stdout.close()
            p.wait()
        else:
            with open(path, "rb") as fh:
                for raw in fh:
                    scan_line(raw.decode("utf-8", "replace"), rel)

print("[inspect] (a) 走査: %d ファイル / 検査値 %d 件 (照合はハッシュのみ)" % (nfiles, len(targets)))
# 許した分は必ず出す。0 件なら「案内に合言葉が入っていない」ということなので、それも出す。
for (sym, rel), cnt in sorted(allowed_hits.items()):
    print("[inspect] (a)     許可: 記号 %s %d 箇所 %s (案内に明記する既定の合言葉)" % (sym, cnt, rel))
if not allowed_hits:
    print("[inspect] (a)     許可した箇所: 0件 (案内に既定の合言葉が入っていない)")
if hits:
    for i, ((sym, rel), cnt) in enumerate(sorted(hits.items())):
        if i >= 20:
            print("[inspect] (a)     … ほか %d 組 (表示は先頭20件まで)" % (len(hits) - 20))
            break
        print("[inspect] (a)     検出: 記号 %s %d 箇所 %s" % (sym, cnt, rel))
    print("[inspect] (a) 既知の資格情報を検出: %d 組 (記号×ファイル)" % len(hits))
    sys.exit(1)
print("[inspect] (a) 既知の資格情報: 0件")
PYINSPECT
  then
    fail=1
  fi

  if [ "$fail" -ne 0 ]; then
    echo "[inspect] 検査で停止: 上記を取り除いてから作り直すこと" >&2
    return 1
  fi
  echo "[inspect] 3種の検査をすべて通過"
  return 0
}

if [ "${1:-}" = "inspect" ]; then
  dist_inspect "${2:?検査対象のディレクトリを指定してください}" \
               "${3:?検査値ファイルを指定してください}"
  exit 0
fi

OUT_ARG="${1:?出力先ディレクトリまたは出力先 .tar.gz を指定してください}"
FLAVOR="${2:?all-in-one または lightweight を指定してください}"
REF="${3:-HEAD}"
PREBUILT_DB="${4:-}"
VAULT_KEY_ARG="${5:-}"

case "$FLAVOR" in
  all-in-one|lightweight) ;;
  *) echo "FLAVOR は all-in-one か lightweight" >&2; exit 2 ;;
esac

# DD-CYN-0117 (版7): 配布物の木は、リポジトリの根と同じとは限らない。
#   いまの本流は 1 つのリポジトリの下に chewie/ と falcon/ が並ぶ形である。
#   旧: ROOT=リポジトリの根 → NAME が "Cynovela" になり、出力名が
#       cynovela-Cynovela-… となる。さらに `git archive "$REF"` がリポジトリ全体を
#       取るため chewie+falcon+falcon-docker-beta が 1 本に混ざり、直後に
#       `欠落: mas` ($ROOT/mas を見るが実体は chewie/mas) で落ちていた。
#   新: ROOT=この build-dist.sh が置かれている配布物の木 (tools/ の 1 つ上)。
#       取り出しは `"$REF:$SUBDIR"` でその木だけに絞る。
#       リポジトリの根と同じ場合は SUBDIR が空になり、従来と同じ動きになる。
REPO="$(git rev-parse --show-toplevel)"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
NAME="$(basename "$ROOT")"
# リポジトリの根から見た、この木の位置 (根そのものなら空)
SUBDIR="$(git rev-parse --show-prefix)"
SUBDIR="${SUBDIR%/}"
# git archive / git ls-tree に渡す木 (SUBDIR が空なら $REF そのもの)
if [ -n "$SUBDIR" ]; then
  REF_TREE="$REF:$SUBDIR"
else
  REF_TREE="$REF"
fi

# ── 出力名の日付は実行日から導出する (dist-date-20260729) ─────────────────
# 従来は呼び出し側の第1引数がそのまま出力名になり、日付は手入力だった
# (未来日付の混入事故あり)。ディレクトリを渡されたら名前ごと自動生成し、
# .tar.gz のフルネームを渡されたら名前中の 8 桁数字列を実行日と照合して、
# 一致しないときは止める (固定文字列・未来日付の混入防止)。
DIST_DATE="$(date +%Y%m%d)"
if [ -d "$OUT_ARG" ]; then
  OUT="${OUT_ARG%/}/cynovela-${NAME}-${FLAVOR}-${DIST_DATE}.tar.gz"
  echo "[dist] 出力名を実行日から自動生成: $OUT"
else
  case "$OUT_ARG" in
    *.tar.gz) ;;
    *) echo "[dist] 出力先はディレクトリか .tar.gz のフルネーム: $OUT_ARG" >&2; exit 2 ;;
  esac
  for d8 in $(basename "$OUT_ARG" | grep -oE '[0-9]{8}' || true); do
    if [ "$d8" != "$DIST_DATE" ]; then
      echo "[dist] 出力名の 8 桁数字 $d8 が実行日 $DIST_DATE と一致しません" >&2
      echo "[dist] 日付は手入力せず、出力先ディレクトリを渡して自動生成させること" >&2
      exit 2
    fi
  done
  OUT="$OUT_ARG"
fi

# 決定論のための固定値。中身が同じなら指紋も同じになる。
export LC_ALL=C
SOURCE_EPOCH="$(git log -1 --format=%ct "$REF")"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

echo "[dist] ref=$REF flavor=$FLAVOR name=$NAME root=$ROOT subdir=${SUBDIR:-(リポジトリの根)}"

# ga-close-v3 PartG: 取り出しは $REF の中身であって机の上ではない。追跡ファイルに
#   未コミットの手直しが残っていると「直したつもりのものが配布物に入っていない」と
#   いう食い違いが起きるため、作る前に必ず読み上げる (止めはしない)。
DIRTY="$(git status --porcelain --untracked-files=no || true)"
if [ -n "$DIRTY" ]; then
  echo "[dist] 注意: 追跡ファイルに未コミットの変更があります。配布物には入りません:" >&2
  printf '%s\n' "$DIRTY" | sed 's/^/[dist]        /' >&2
fi

echo "[dist] 追跡ファイルのみを取り出す (未追跡は原理的に入らない)"
mkdir -p "$STAGE/$NAME"
# `git archive "$REF:$SUBDIR"` は cwd 依存で、この木の中から叩くと空になる
# (chewie の中では chewie/chewie を探して 0 項目。実測 20260817)。
# ∴ git はリポジトリの根に固定して呼ぶ。
git -C "$REPO" archive --format=tar "$REF_TREE" | tar -x -C "$STAGE/$NAME"

# ── ここから「追跡外だが同梱すべきもの」を名指しで足す ─────────────────
add_named() {   # add_named <ツリー内の相対パス> <説明>
  local rel="$1" desc="$2"
  if [ ! -e "$ROOT/$rel" ]; then
    echo "[dist] 欠落: $rel ($desc)" >&2
    return 1
  fi
  mkdir -p "$STAGE/$NAME/$(dirname "$rel")"
  # dist-nesting-fix-20260727: 宛先が既にディレクトリとして在ると `cp -R src dst` は
  #   dst の「中へ」入れてしまい store/vector/vector/... のように二重にネストする。
  #   chewie は store/vector や store/uploads が追跡下にあり git archive が先に作るため、
  #   これが起きて索引と原本がアプリの読まないパスに入っていた（受け取り手からは
  #   資料は並ぶのに検索が空を返す）。宛先を消してから複製する。
  rm -rf "$STAGE/$NAME/$rel"
  cp -R "$ROOT/$rel" "$STAGE/$NAME/$rel"
  echo "[dist] 同梱: $rel ($desc)"
}

add_if_untracked() {   # add_if_untracked <ツリー内の相対パス> <説明>
  # $REF に入っているものは git archive 側で既に入っているので触らない
  # (作業ツリーの手直しで上書きすると「取り出しは $REF の中身」の原則が崩れる)。
  # 追跡外のときだけ名指しで足す。
  local rel="$1" desc="$2"
  if [ -n "$(git -C "$REPO" ls-tree -r --name-only "$REF_TREE" -- "$rel")" ]; then
    echo "[dist] 追跡下: $rel は git archive 側で入る (名指し追加はしない)"
    return 0
  fi
  add_named "$rel" "$desc"
}

resolve_vault_key() {   # 金庫鍵 (store/secret.key) の実体を探す。見つけたパスを標準出力へ。
  # 探索順 (環境変数は使わない):
  #   1. 第5引数で明示されたパス
  #   2. リポジトリの隣の <名前>-keys/secret.key
  #      (falcon はコンテナへ読み取り専用 bind するため鍵をツリー外に置いてある)
  #   3. ツリー内 store/secret.key (chewie はこちらが実体)
  local c
  for c in "$VAULT_KEY_ARG" "$ROOT/../$NAME-keys/secret.key" "$ROOT/store/secret.key"; do
    [ -n "$c" ] && [ -f "$c" ] && { echo "$c"; return 0; }
  done
  return 1
}

# 外の推論サーバ (Mac Accelerator Service) と、その立て方の 1 ページ。
# 追跡下ならこの呼び出しは何もしない (git archive 側で入っている)。
add_if_untracked "mas" "外の推論サーバ (Mac Accelerator Service)"
add_if_untracked "SETUP-ACCELERATOR.md" "外の推論サーバの立て方 (受け取り手向け)"

# ── 金庫の鍵を同梱する (dist-vault-key-20260729) ──────────────────────
# 同梱する demo.db のチャンクは金庫鍵で暗号化されている。鍵が無いと受け取り手の
# 起動時に config.py が**別の鍵を新規生成**してしまい、資料は並ぶのに中身が
# 復号できない (画面に暗号文が素通しで出る) という状態になる。
# 起動時の「既に在れば生成しない」判定は config.py の _load_or_create_secret_key()
# に既にあるため、鍵を置いておくだけで足りる。コード側の変更は不要。
#
# bundled-data-20260731 (DD-CYN-0007 B0): 鍵は**同梱データを作る前**に置く。
#   同梱データはこの鍵で暗号化されるので、鍵と中身が噛み合わないという事態が
#   構造的に起こらなくなる (従来は作業ツリーで作られた中身と、別に選ばれた鍵を
#   後から突き合わせていた)。
VAULT_KEY_SRC="$(resolve_vault_key || true)"
if [ -z "$VAULT_KEY_SRC" ]; then
  echo "[dist] 金庫鍵が見つかりません。第5引数で明示するか store/secret.key を置いてください" >&2
  exit 1
fi
mkdir -p "$STAGE/$NAME/store"
cp "$VAULT_KEY_SRC" "$STAGE/$NAME/store/secret.key"
chmod 600 "$STAGE/$NAME/store/secret.key"
echo "[dist] 同梱: store/secret.key (金庫鍵) <- $VAULT_KEY_SRC"
echo "[dist]        指紋 sha256=$(shasum -a 256 "$STAGE/$NAME/store/secret.key" | cut -c1-16)…"

# ── 埋め込み・リランクのモデル ────────────────────────────────────
# ga-close-v3 PartA (2026-07-27): store/uploads の同梱を廃止。
#   アップロード受け口の撤去でアプリ内部に資料の写しを作らなくなったため、
#   配布物にも「アプリの中の原本」を同梱しない。資料は取り込みフォルダから読む。
#
# bundled-data-20260731: モデルだけは引き続き作業ツリーから複製する。これは
#   提供元が公開している配布物の写し (Hugging Face のキャッシュ形式) であって
#   開発機で作られたものではなく、梱包直前の検査でも利用者名・資格情報とも 0 件で
#   あることを確認している。軽量版は同梱しないが、索引を作るには要るので、
#   梱包のあいだだけ読み取り専用で繋ぎ、作り終えたら外す。
MODELS_LINKED=0
if [ "$FLAVOR" = "all-in-one" ]; then
  add_named "store/models" "埋め込み・リランクのモデル (全部入りのみ)"
else
  if [ ! -d "$ROOT/store/models" ]; then
    echo "[dist] 欠落: store/models (索引を作るのに要る)" >&2
    exit 1
  fi
  ln -sfn "$ROOT/store/models" "$STAGE/$NAME/store/models"
  MODELS_LINKED=1
  echo "[dist] 索引を作るあいだだけ store/models を読み取り専用で繋ぐ (軽量版には同梱しない)"
fi

# ── 同梱データを梱包の場で作る (bundled-data-20260731 / DD-CYN-0007 B0) ──
# 従来はここで作業ツリーの store/db/demo.db と store/vector をそのまま複製していた。
# 作業ツリーは開発の過程で溜まったもの (旧世代の資料・撤去したはずの作業場所・
# 開発機の利用者名) を含むため、配布物の中身の出どころを言えなかった。実測では
# 梱包直前の検査が実際に停止していた (終了コード 1)。
# これ以後、同梱される索引とデータベースの出どころは、この配布物の中の
# dummy-corpus/ だけである。作業ツリーの store/db・store/vector は読まない。
echo "[dist] 同梱データを梱包の場で作る (入力は配布物内の dummy-corpus/ のみ)"
BUNDLED_COUNTS="$(python tools/build_bundled_data.py "$STAGE/$NAME" | tee /dev/stderr \
                  | sed -n 's/^\[bundled\] 作った中身: //p')"
if [ -z "$BUNDLED_COUNTS" ]; then
  echo "[dist] 同梱データの作成に失敗しました" >&2
  exit 1
fi
echo "[dist] 同梱データの数え上げ: $BUNDLED_COUNTS"

# ── 既定の取り込み元を配布物の中へ向ける (portable-roots-20260808 / DD-CYN-0066 F-2) ──
# 決定 9-3: 同梱デモの取り込み元は、配布物の中に置いたダミー資料の場所を指す。
#   従来はこの控え (store/ingest-roots.json) を梱包の場で 1 度も書いていなかったため、
#   受け取り手の側では取り込み元 0 件で立ち上がり、一覧が空のまま行き止まりになっていた。
#   作る側の絶対パスを書くわけにはいかないので (受け取り手の機材には存在せず、
#   falcon はその場所を入れ物へ繋げないため起動そのものが失敗する)、
#   配布物の根からの相対 "@app/dummy-corpus" で書く。解くのは起動時である
#   (scripts/ingest_roots.py が自分の置き場から根を実測して解く)。
# 受け取り手が自分で足したものは、従来どおりその機材の絶対パスで保存される。
echo "[dist] 既定の取り込み元を配布物の中のダミー資料へ向ける (決定 9-3)"
rm -f "$STAGE/$NAME/store/ingest-roots.json" "$STAGE/$NAME/store/ingest-roots.json.tmp"
python3 "$STAGE/$NAME/scripts/ingest_roots.py" \
  --file "$STAGE/$NAME/store/ingest-roots.json" \
  --repo "$STAGE/$NAME" \
  add --portable --label "dummy-corpus" "$STAGE/$NAME/dummy-corpus" >/dev/null
echo "[dist] 既定の取り込み元 (控えに書かれたそのままの値):"
sed 's/^/[dist]     /' "$STAGE/$NAME/store/ingest-roots.json"
# 作る側の絶対パスが 1 文字も入っていないことを、ここで機械で確かめる (フェイルクローズ)。
if grep -q '"/' "$STAGE/$NAME/store/ingest-roots.json"; then
  echo "[dist] 既定の取り込み元に絶対パスが残っています。梱包を止めます。" >&2
  exit 1
fi
echo "[dist] 既定の取り込み元に絶対パス: 0件"

# ── 保存領域の名前を配布物ごとに分ける (dist-volume-identity-20260808 / DD-CYN-0066 F-3) ──
# falcon の保存領域は Podman の名前つき保存領域 (${volume_prefix}-db / -vec / -bk) であって、
# 配布物のディレクトリの中には無い。接頭辞が全配布物で同じ既定値 (cyn) だったため、
# 以前の配布物・以前の走行が作った cyn-db がその機材に残っていると podman はそれを黙って
# 再利用し、この配布物が同梱した demo.db は保存領域へ写されない。
# ∴ 画面までは開けるのに、案内 (STARTUP.md) に書いた合言葉が通らない。
# 配布物の身元 (名前・形態・作った日) から決めた接頭辞を梱包の場で焼き込み、
# 別の配布物の保存領域を引き当てないようにする。値は手入力しない。
# chewie にはこの節が無い (この Mac の中で直接動き、保存領域は store/ の下である)。
if grep -q '^  volume_prefix:' "$STAGE/$NAME/cynovela.yaml"; then
  DIST_VOLPREFIX="cyn-${NAME}-$(printf '%s' "$FLAVOR" | cut -c1)-${DIST_DATE}"
  python3 - "$STAGE/$NAME/cynovela.yaml" "$DIST_VOLPREFIX" <<'PYVOL'
import re, sys
path, prefix = sys.argv[1], sys.argv[2]
src = open(path, encoding="utf-8").read()
new, n = re.subn(r"(?m)^(  volume_prefix:[ \t]*).*$", lambda m: m.group(1) + prefix, src)
if n != 1:
    print("[dist] cynovela.yaml の container.volume_prefix を書き換えられなかった (%d 箇所)" % n)
    sys.exit(1)
open(path, "w", encoding="utf-8").write(new)
print("[dist] 保存領域の名前の頭をこの配布物専用にした: container.volume_prefix=%s" % prefix)
PYVOL
else
  echo "[dist] container.volume_prefix はこの系統に無い (この Mac の中で直接動く形態のため)"
fi

# ── 初期の合言葉を固定値にする (fixed-initial-credentials-20260802・DD-CYN-0021 §3-2) ──
#   受け取り手が入れない配布物を作らないため、管理者と閲覧者の初期の合言葉は固定値にし、
#   配布物の中の案内 (STARTUP.md) に書く。乱数は使わない。
#   平文はこのリポジトリのどこにも置かない。tools/dist-initial-credentials.local
#   (1 行 = 記号 TAB 値・git 追跡外・mode 600) から読み、ここで staging へ書き込む。
#   このファイルが無いときは決められないので止める (フェイルクローズ)。
# DD-CYN-0117 (版7): 検査値と同じく、この木の下 → リポジトリの根 の順で探す。
#   1 つのリポジトリに木が複数並ぶ形では、根の tools/ に 1 本だけ置く運用である。
CRED_FILE=""
for _cf in "$ROOT/tools/dist-initial-credentials.local" "$REPO/tools/dist-initial-credentials.local"; do
  [ -f "$_cf" ] && { CRED_FILE="$_cf"; break; }
done
if [ -z "$CRED_FILE" ]; then
  echo "[dist] 初期の合言葉の元ファイルが不在" >&2
  echo "[dist]   探した先: $ROOT/tools/ と $REPO/tools/" >&2
  echo "[dist] フェイルクローズ: 固定値を決められないため作るのを止める" >&2
  exit 1
fi
echo "[dist] 初期の合言葉の元: $CRED_FILE"
ADMIN_PW="$(awk -F'\t' '$1=="admin"{print $2}' "$CRED_FILE")"
VIEWER_PW="$(awk -F'\t' '$1=="viewer"{print $2}' "$CRED_FILE")"
if [ -z "$ADMIN_PW" ] || [ -z "$VIEWER_PW" ]; then
  echo "[dist] $CRED_FILE に admin / viewer の行が揃っていない" >&2
  exit 1
fi
echo "[dist] 初期の合言葉: 固定値を使う (値は画面に出さない。長さ 管理者=${#ADMIN_PW} 閲覧者=${#VIEWER_PW})"

echo "[dist] demo.db をクリーン化 (会話履歴の全消去・利用者の初期化・参照先の相対化)"
python tools/build_clean_demo_db.py \
  "$STAGE/$NAME/store/db/demo.db" "$STAGE/$NAME/store/db/demo.db.clean" \
  --admin-password "$ADMIN_PW" --viewer-password "$VIEWER_PW"
mv "$STAGE/$NAME/store/db/demo.db.clean" "$STAGE/$NAME/store/db/demo.db"

# 本番 (引数なし・空のデータベース) 側も同じ合言葉で入れるようにする。
#   ここを空のままにすると、db.py が起動のたびに乱数を作って画面へ出す形になり、
#   案内に書いた値では入れない。設定の1行だけを staging に書き込む。
python - "$STAGE/$NAME/cynovela.yaml" "$ADMIN_PW" <<'PYYAML'
import re, sys
path, pw = sys.argv[1], sys.argv[2]
src = open(path, encoding="utf-8").read()
# DD-CYN-0117 (版7): 空 ('') のときだけでなく、既に値が書かれているときも揃える。
#   追跡下の cynovela.yaml に値が入ったまま commit された状態では、旧式 ('' だけを
#   狙う) は 0 箇所となり梱包がフェイルクローズで止まっていた (実測 20260817)。
#   梱包は「元が何であれ、正本の値に揃える」のが正しい。
new, n = re.subn(r"(?m)^(auth:\n(?:[ \t]+.*\n)*?[ \t]+admin_initial_password:[ \t]*)'[^'\n]*'[ \t]*$",
                 lambda m: m.group(1) + "'" + pw.replace("'", "''") + "'", src)
if n != 1:
    print("[dist] cynovela.yaml の auth.admin_initial_password を書き換えられなかった (%d 箇所)" % n)
    sys.exit(1)
open(path, "w", encoding="utf-8").write(new)
print("[dist] 同梱の設定に管理者の初期の合言葉を書いた (cynovela.yaml auth.admin_initial_password)")
PYYAML

# DD-CYN-0070 N-4: 閲覧者の初期の合言葉も同じ形で書く。従来は管理者だけを書いており、
#   引数なし (本番) の閲覧者 seed (db.py・N-4 で demo 分岐の外へ移した) が乱数へ倒れ、
#   案内 (STARTUP.md) に書いた値では入れなかった。新しい値は作らない (案内と同じ値)。
python - "$STAGE/$NAME/cynovela.yaml" "$VIEWER_PW" <<'PYYAML'
import re, sys
path, pw = sys.argv[1], sys.argv[2]
src = open(path, encoding="utf-8").read()
# DD-CYN-0117 (版7): 管理者側と同じく、既に値が入っていても正本へ揃える。
new, n = re.subn(r"(?m)^([ \t]+viewer_initial_password:[ \t]*)'[^'\n]*'[ \t]*$",
                 lambda m: m.group(1) + "'" + pw.replace("'", "''") + "'", src)
if n != 1:
    print("[dist] cynovela.yaml の auth.viewer_initial_password を書き換えられなかった (%d 箇所)" % n)
    sys.exit(1)
open(path, "w", encoding="utf-8").write(new)
print("[dist] 同梱の設定に閲覧者の初期の合言葉を書いた (cynovela.yaml auth.viewer_initial_password)")
PYYAML

# 案内 (STARTUP.md) の目印を、実際の値の書かれた2行へ置き換える。
python - "$STAGE/$NAME/STARTUP.md" "$ADMIN_PW" "$VIEWER_PW" <<'PYDOC'
import sys
path, apw, vpw = sys.argv[1], sys.argv[2], sys.argv[3]
# DD-CYN-0117 (版7): 目印が在るとき (雛形のまま) と、既に値の2行へ置き換わって
#   commit されているときの両方で通す。旧式は目印だけを狙い、置き換え済みの
#   STARTUP.md では 0 個となって梱包がフェイルクローズで止まっていた (実測 20260817)。
#   梱包は「元が何であれ、正本の2行に揃える」のが正しい。
import re as _re
MARK = "<!-- dist:initial-credentials -->"
NEWLINES = [
    "- 管理者: ユーザー名 `cynovela` / パスワード: `%s`" % apw,
    "- 閲覧者: ユーザー名 `demo` / パスワード: `%s`" % vpw,
]
lines = open(path, encoding="utf-8").read().split("\n")
idx = [i for i, ln in enumerate(lines) if MARK in ln]
if len(idx) == 1:
    # 目印の在る行を丸ごと差し替える (目印だけ消すと、本流での読みやすさのために
    # 同じ行へ添えた説明が配布物側に残ってしまうため)
    lines[idx[0]: idx[0] + 1] = NEWLINES
    print("[dist] 案内の目印を実際の値へ置き換えた (STARTUP.md)")
elif len(idx) == 0:
    a_re = _re.compile(r"^- 管理者: ユーザー名 `[^`]*` / パスワード: `[^`]*`\s*$")
    v_re = _re.compile(r"^- 閲覧者: ユーザー名 `[^`]*` / パスワード: `[^`]*`\s*$")
    a_idx = [i for i, ln in enumerate(lines) if a_re.match(ln)]
    v_idx = [i for i, ln in enumerate(lines) if v_re.match(ln)]
    if len(a_idx) != 1 or len(v_idx) != 1:
        print("[dist] STARTUP.md に目印も、置き換え済みの2行も見つからない "
              "(目印 %d 個 / 管理者行 %d 個 / 閲覧者行 %d 個)" % (len(idx), len(a_idx), len(v_idx)))
        sys.exit(1)
    lines[a_idx[0]] = NEWLINES[0]
    lines[v_idx[0]] = NEWLINES[1]
    print("[dist] 案内の既存の2行を正本の値へ揃えた (STARTUP.md)")
else:
    print("[dist] STARTUP.md の目印が %d 個 (1 個であること)" % len(idx))
    sys.exit(1)
open(path, "w", encoding="utf-8").write("\n".join(lines))
PYDOC

if [ "$MODELS_LINKED" = "1" ]; then
  rm -f "$STAGE/$NAME/store/models"
  echo "[dist] 索引を作り終えたので store/models の繋ぎを外した (軽量版)"
fi

# 鍵と中身が本当に噛み合うかをその場で確かめる。falcon のツリーには python を
# 1 回動かしただけで出来た**別物の** store/secret.key が居たことがあるため、
# 「鍵らしきものを入れた」で終わらせない。
echo "[dist] 金庫鍵と demo.db の噛み合わせを確認"
python - "$STAGE/$NAME/store/secret.key" "$STAGE/$NAME/store/db/demo.db" <<'PY'
import sqlite3, sys
from pathlib import Path
from cryptography.fernet import Fernet
key = Path(sys.argv[1]).read_text().strip().encode()
con = sqlite3.connect(f"file:{sys.argv[2]}?mode=ro", uri=True)
rows = con.execute("select content from chunks where content like 'enc:%' limit 5").fetchall()
con.close()
if not rows:
    print("[dist] 注意: 暗号化されたチャンクが 1 件も無いため噛み合わせは確認できません")
    sys.exit(0)
f = Fernet(key)
for (v,) in rows:
    f.decrypt(v[4:].encode())      # 失敗すれば例外で止まる (set -e)
print(f"[dist] 噛み合わせ OK ({len(rows)} 件を試験復号)")
PY

# ── 入ってはいけないものを最後に落とす (二重の守り) ─────────────────
# git archive で来る側には未追跡物は入らないので、この網が実際に効くのは
# 上の add_named で名指しで足した中身 (索引・モデル) に対してである。
# ga-close-v3 PartG (2026-07-27): SQLite の道連れファイルは -wal/-shm だけではない。
#   非WALのときは <db>-journal が出る (hansolo の .containerignore は同じ理由で
#   *-journal を除いている)。索引 (chroma.sqlite3) に付いてくるため同じ扱いにする。
#   .ruff_cache は .pytest_cache と同族、*.bak は死蔵の写しで、どちらも配る意味がない。
# dist-vault-key-20260729: `-name 'secret.key'` の一律削除はやめた。金庫鍵
#   (store/secret.key) は同梱するものになったため、名前で薙ぎ払うと上で入れた鍵まで
#   消える。落とすのは**通行証 (JWT) の署名鍵だけ**で、これは受け取り手ごとに
#   config.py の _load_or_create_jwt_signing_key() が自動生成するので配る必要がない
#   (共有すると他所で発行された通行証が通ってしまう)。パスを名指しで消す。
# ── DD-CYN-0050: ダブルクリックの入口は .command のファイルである ──
#   DD-CYN-0066 F-8: 以前ここに在った「ダイアログの .app」の説明を落とした。同梱をやめた
#   のは DD-CYN-0050 であり、その原稿 (tools/launcher-app/launcher.applescript) は
#   本流に残してある。受け取り手が押す入口は、下の 3 つの .command だけである
#   (DD-CYN-0071 決定 31-2 で、起動・停止に「取り込み元を足す」が加わった)。
#   3つの .command は追跡ファイルのため git archive がそのまま同梱する。
#   ダブルクリックで開くには実行ビットが必須のため、ここで確かめて確実に付ける。
for _cmdf in "Cynovela-start.command" "Cynovela-stop.command" "Cynovela-add-folder.command"; do
  if [ -f "$STAGE/$NAME/$_cmdf" ]; then
    chmod +x "$STAGE/$NAME/$_cmdf"
    echo "[dist] ダブルクリックの入口を同梱: $_cmdf"
  else
    echo "[dist] エラー: $_cmdf が見つかりません。同梱できないため中止します。"
    exit 1
  fi
done

echo "[dist] 秘密・実行時の残りかすを除去"
rm -f "$STAGE/$NAME/store/db/jwt/secret.key"
find "$STAGE/$NAME" \( \
      -path '*/db/jwt/secret.key' -o -name '*.log' -o -name '*.pid' \
   -o -name '*.db-wal' -o -name '*.db-shm' -o -name '*-journal' \
   -o -name '.DS_Store' -o -name '._*' -o -name '__pycache__' \
   -o -name '.pytest_cache' -o -name '.ruff_cache' \
   -o -name '.hypothesis' -o -name '.deepeval' -o -name '*.bak' \
  \) -print -exec rm -rf {} + 2>/dev/null || true
rm -rf "$STAGE/$NAME/store/logs" "$STAGE/$NAME/.git"
# bundled-data-20260731: 同梱データを作るときに出来る空の受け皿は配らない。
rmdir "$STAGE/$NAME/store/backups" 2>/dev/null || true

# oldname-struct-20260729: 作る側の机の上の記録は配らない。
#   baseline-report.md は 2026-05-15 の調査ログ (作る側の home パスと conda 環境名が
#   そのまま写っている)。受け取り手には使い道が無い。
#   中身は当時の事実なのでツリー側は書き換えない。配布物から外すだけにする。
# oldname-zero-20260731 (DD-CYN-0007): 退避先の覚え書き (旧名を含むファイル名) は
#   本流から外した。ここでその名前を書いていると、梱包処理そのものが配布物の中に
#   旧名を持ち込んでしまう (受け入れの旧名検査が、この 1 行に当たっていた)。
#   DEV-NOTE-mba.md は開発の覚え書きで、旧名と作る側のバックアップ先を含む。
rm -f "$STAGE/$NAME/baseline-report.md" "$STAGE/$NAME/DEV-NOTE-mba.md"

# ── 開発向けの資料を配布物から外す (distclean-20260729・Tocchi 決定) ──────
# instructions/ と docs/spec-raw/ は開発中の文書そのもの。
# tests/ は開発用資材のため配布物からディレクトリごと除外する。受け入れ確認は
# scripts/test_comprehensive_e2e.py で行う (tests/ を一切参照しないことは確認済み。
# scripts/ は従来どおり同梱し、この e2e は絶対に除外しない)。
# falcon 限定の 2 ファイルには開発機の利用者名が残る。いずれも受け取り手には
# 使い道が無いためステージから落とす (中身は当時の事実なのでツリー側は書き換えない)。
# falcon 限定の 2 パスは chewie の追跡下に無く、rm -f は無いものには何もしない
# (両ツリーでこのスクリプトを同一内容に保つための書き方)。
echo "[dist] 開発向けの資料をステージから除去"
rm -rf "$STAGE/$NAME/instructions" "$STAGE/$NAME/docs/spec-raw" \
       "$STAGE/$NAME/tests"
rm -f "$STAGE/$NAME/MANIFEST-anchor-candidate-20260713.md" \
      "$STAGE/$NAME/deploy/k8s/20-deployment.yaml"
# bundled-data-20260731 (DD-CYN-0007 B11): 過去の走行の一覧文書は、当時の作業ツリーの
#   数え上げ (資料30本 / 47,106 塊) をそのまま書いており、いま同梱するもの (dummy-corpus
#   の資料と、そこから作った塊) とは別物である。過去の事実の記録なのでツリー側は
#   書き換えず、ステージから落として、代わりに**この配布物の実際の数え上げ**を書き出す。
rm -f "$STAGE/$NAME/MANIFEST-20260724-overnight.md" \
      "$STAGE/$NAME/MANIFEST-20260725-ga-mas.md"
python - "$STAGE/$NAME/BUNDLED-DATA.md" "$BUNDLED_COUNTS" "$NAME" "$FLAVOR" <<'PYMAN'
import json, sys
out, counts_json, name, flavor = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
c = json.loads(counts_json)
def g(k):
    return c.get(k, "(測っていません)")
with open(out, "w", encoding="utf-8") as fh:
    fh.write(f"""# 同梱データの内訳（{name} / {flavor}）

この文書は配布物を作るときに自動で書き出しています。数字は、この配布物に実際に入っている
ものを梱包の場で数えた値です。手で書いた値ではありません。

同梱データの出どころは、**この配布物の中の `dummy-corpus/` だけ**です。作る側の作業用の
資料や索引は一切入っていません。

| 項目 | 件数 |
|---|---|
| 資料（ファイル） | {g('files')} |
| 塊（チャンク） | {g('chunks')} |
| 親の塊 | {g('parent_chunks')} |
| 作業場所（ワークスペース） | {g('workspaces')} |
| 取り込み元 | {g('sources')} |
| コレクション | {g('collections')} |
| 取り込み時に伏せた箇所 | {g('pii_count')} |

塊は伏字前と伏字済みの二層で保管し、どちらも金庫の鍵で暗号化しています。検索に使う索引
（ベクター）は**伏字済みの層だけ**から作っています。

同梱の資料はすべて架空の企業「アオゾラ商事」を題材にした説明用のサンプルです。登場する
人物・組織・住所・電話番号・メールアドレスなどはすべて実在しません。
""")
print(f"[dist] 同梱データの内訳を書き出した: BUNDLED-DATA.md")
PYMAN
# oss-init-20260729: 旧同梱デモの原稿と取り込み試験の資材を配布物から外す。
#   falcon ingest/ (実在ベンダー文書の PDF を含む取り込み試験の資材)、
#   chewie sample_data/ と data/ (旧デモの原稿一式)。同梱資料は dummy-corpus/
#   へ全入れ替えしたため受け取り手には使い道が無い。ツリー側は開発資材
#   (pytest の基線) として残し、ステージから落とすだけにする。
#   欠損時の実挙動は確認済み: server.py の data/demo 投入は「無ければ何もしない」、
#   db.py のデモ Source 行はパス文字列のみで起動を妨げない。
rm -rf "$STAGE/$NAME/ingest" "$STAGE/$NAME/sample_data" "$STAGE/$NAME/data"

# ── 梱包直前の検査 (フェイルクローズ・pretar-inspect-20260729) ────────────
# 検査の中身と検査値ファイルの決まりはファイル先頭近くの dist_inspect を参照。
echo "[dist] 梱包直前の検査 (3種・フェイルクローズ)"
# DD-CYN-0117 (版7): 検査値はこの木の下 → リポジトリの根 の順で探す。
#   1 つのリポジトリに木が複数並ぶ形では、根の tools/ に 1 本だけ置く運用である。
CHECK_VALUES=""
for _cv in "$ROOT/tools/dist-check-values.local" "$REPO/tools/dist-check-values.local"; do
  [ -f "$_cv" ] && { CHECK_VALUES="$_cv"; break; }
done
if [ -z "$CHECK_VALUES" ]; then
  echo "[dist] 検査値 (tools/dist-check-values.local) が見つかりません。梱包を止めます。" >&2
  echo "[dist]   探した先: $ROOT/tools/ と $REPO/tools/" >&2
  exit 1
fi
echo "[dist] 検査値: $CHECK_VALUES"
dist_inspect "$STAGE/$NAME" "$CHECK_VALUES"

# ── 決定論的な tar ───────────────────────────────────────────────
# macOS の tar は bsdtar で --mtime を持たないため、固める前にステージ側の時刻を
# 揃える (ref のコミット時刻)。所有者・並び順も固定し、gzip は -n で時刻を書かない。
echo "[dist] 決定論的に固める (mtime=$SOURCE_EPOCH)"
TOUCH_STAMP="$(date -r "$SOURCE_EPOCH" +%Y%m%d%H%M.%S)"
find "$STAGE/$NAME" -exec touch -h -t "$TOUCH_STAMP" {} +
( cd "$STAGE" && find "$NAME" -print0 | LC_ALL=C sort -z \
    | tar --create --file - --null --files-from - --no-recursion \
          --format=ustar --numeric-owner --uid 0 --gid 0 --uname '' --gname '' \
) | gzip -9 -n > "$OUT"

echo "[dist] 完成: $OUT"
echo "[dist] $(stat -f%z "$OUT") bytes"
shasum -a 256 "$OUT"
