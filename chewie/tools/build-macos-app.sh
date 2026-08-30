#!/usr/bin/env bash
# build-macos-app.sh — Cynovela を macOS の .app + .pkg の形に組み立てる
#
# macos-app-20260830:
#   これは Portable 版の**外側の殻**を作る道具であって、起動のやり方を作り直す
#   ものではない。中身 (Resources/cynovela) は既存の梱包工程 build-dist.sh の
#   all-in-one をそのまま使う。∴ 「何が入るか」の決まりは 1 か所のままである。
#
# 出来上がるもの
#   <出力先>/Cynovela-<版>-macos-arm64.pkg
#
# 使い方
#   tools/build-macos-app.sh <出力先ディレクトリ> [git-ref]
#
# 組み立ての並び
#   1. 中身   : build-dist.sh <一時> all-in-one <ref>  → 展開して Resources/cynovela
#   2. 環境   : conda で作り、conda-pack --dest-prefix で **入れる先の場所へ**
#               書き換えて固める → 展開して Resources/env
#   3. 入口   : macos-app/main.swift を xcrun swiftc で組む → Contents/MacOS/Cynovela
#   4. 署名   : ad-hoc (codesign -s -)。中の Mach-O が先、包み全体が最後。
#   5. 検査   : build-dist.sh inspect を、組み上がった .app に対してもう一度
#   6. 梱包   : pkgbuild (置き場を動かさない形) → productbuild
#   7. 関門   : 出来上がった .pkg を展開して中身を確かめる
#
# 🔴 conda-pack --dest-prefix の落とし穴 (実測)
#   (a) 前置きの置き換えは**短くする方向にしかできない**。∴ 作る場所の道は、
#       入れる先の道より十分に長くなければならない。下の関門で機械で確かめる。
#   (b) --dest-prefix を使うと bin/conda-unpack は**作られない**。作られない
#       のが正しい (もう直す必要が無いため)。走らせてもいけない。
#   (c) conda-pack 0.9.2 の --dest-prefix の道は、置き換えたあとに**署名し直さない**
#       (conda-unpack の道は Darwin arm64 で codesign -s - -f を呼んでいる)。
#       ∴ arm64 では署名の壊れた Mach-O が残り、その python は exit 137 で
#       黙って死ぬ。ここで組み立て時に署名し直す。受け取り手の機械では何もしない
#       (署名はファイルの中に在り、固めても解いても保たれる)。
#
# 🔴 このスクリプトは配布物の中 (tools/) に入る。∴ 梱包直前の検査が使う語を
#   字のまま書いてはいけない。書くと検査が自分自身を見つけて、組み立てが必ず
#   止まる。build-dist.sh の頭書きに同じ注意があり、そこでは 3 度実際に起きた。
#   下の関門が使う語も、同じ理由で走るときに組み立てる。

set -euo pipefail

# ── 入れる先 (動かさない) ─────────────────────────────────────
APP_ID="dev.tohaya.cynovela"
APP_NAME="Cynovela"
APP_DEST="/Applications/${APP_NAME}.app"
ENV_DEST="${APP_DEST}/Contents/Resources/env"

CONDA_BIN="${CONDA_BIN:-$HOME/miniforge3/bin/conda}"

say() { echo "[app] $*"; }
die() { echo "[app] $*" >&2; exit 1; }

# ── 引数 ─────────────────────────────────────────────────────
OUT_DIR="${1:?出力先ディレクトリを指定してください}"
REF="${2:-HEAD}"
[ -d "$OUT_DIR" ] || die "出力先がディレクトリではありません: $OUT_DIR"
OUT_DIR="$(cd "$OUT_DIR" && pwd)"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO="$(cd "$ROOT" && git rev-parse --show-toplevel)"
cd "$ROOT"

# ── 前提 ─────────────────────────────────────────────────────
[ "$(uname -m)" = "arm64" ] || die "この道具は Apple Silicon (arm64) でしか組めません: $(uname -m)"
#   pkgutil だけ /usr/sbin に在る (/usr/bin ではない)。ここに並べていなかったため、
#   初回は 50 分かけて最後の関門まで来てから「無い」で落ちた。
for _t in /usr/bin/pkgbuild /usr/bin/productbuild /usr/bin/codesign /usr/bin/plutil \
          /usr/bin/xattr /usr/sbin/pkgutil; do
  [ -x "$_t" ] || die "$_t が見つかりません"
done
command -v xcrun >/dev/null 2>&1 || die "xcrun が見つかりません (Command Line Tools を入れてください)"
xcrun --find swiftc >/dev/null 2>&1 || die "swiftc が見つかりません (Command Line Tools を入れてください)"
[ -x "$CONDA_BIN" ] || die "conda が見つかりません: $CONDA_BIN"
[ -f "$ROOT/macos-app/main.swift" ] || die "入口の素が在りません: $ROOT/macos-app/main.swift"

# ── 版を読む道具 ────────────────────────────────────────────
#   VERSION と、走っているサーバが名乗る出どころ (core/version.py) の両方を見て、
#   食い違ったら止める。版を上げるとき VERSION だけを直して core/version.py を
#   忘れる事故が実際にあった。
read_version() {   # read_version <木のルート>
  local _t="$1" _v _c
  _v="$(awk -F': *' '/^version:/{print $2; exit}' "$_t/VERSION" | tr -d ' \r')"
  [ -n "$_v" ] || die "VERSION から版を読めません: $_t/VERSION"
  _c="$(awk -F'"' '/^APP_VERSION *=/{print $2; exit}' "$_t/core/version.py")"
  [ "$_v" = "$_c" ] || die "版が食い違っています ($_t): VERSION=$_v core/version.py=$_c"
  echo "$_v"
}
# ここで見るのは、組み立てを始める前の手元の確認だけである。
# 正として使う版は**取り出した木**のもので、展開の直後に読み直す。
VERSION="$(read_version "$ROOT")"
say "版 (手元): $VERSION (VERSION と core/version.py が一致)"

# ── 検査値 (梱包直前の検査に要る)。無ければ組まない (フェイルクローズ) ──
CHECK_VALUES=""
for _cv in "$ROOT/tools/dist-check-values.local" "$REPO/tools/dist-check-values.local"; do
  [ -f "$_cv" ] && { CHECK_VALUES="$_cv"; break; }
done
[ -n "$CHECK_VALUES" ] || die "検査値 (tools/dist-check-values.local) が見つかりません。組み立てを止めます。"
say "検査値: $CHECK_VALUES"

# ── 🔴 前置きの長さの関門 (フェイルクローズ) ──────────────────
#   conda-pack は前置きを**短くする方向にしか**置き換えられない。作る場所が
#   入れる先より短いと、書き換えが黙って行われず、受け取り手の機械で
#   作った側の場所を指したままの環境が出来上がる。
#   余裕は 32 文字とする (入れる先の道が将来伸びても効くようにする)。
PREFIX_MARGIN=32
PREFIX_NEED=$(( ${#ENV_DEST} + PREFIX_MARGIN ))
# 🔴 作る場所の道の幹は、字のまま書かない。8 進で組み立てる。
#    このファイルは配布物の tools/ に入る。下の関門は、出来上がった .pkg を
#    展開して「作る場所の道が残っていないか」を**幹で**当てる。幹を字のまま
#    書くと、関門が配布物の中のこのファイル自身を見つけて必ず止まる
#    (実測: 1 件を検出して落ちた)。頭書きの注意と同じ罠である。
BUILD_PREFIX_STEM="/private/tmp/$(printf 'cynovela\055macos\055app\055build\055')"
BUILD_PREFIX="${BUILD_PREFIX_STEM}$$"
while [ ${#BUILD_PREFIX} -lt "$PREFIX_NEED" ]; do BUILD_PREFIX="${BUILD_PREFIX}-pad"; done
if [ ${#BUILD_PREFIX} -lt "$PREFIX_NEED" ]; then
  die "作る場所が短すぎます: ${#BUILD_PREFIX} < $PREFIX_NEED"
fi
say "前置きの長さ: 入れる先 ${#ENV_DEST} / 作る場所 ${#BUILD_PREFIX} / 差 $(( ${#BUILD_PREFIX} - ${#ENV_DEST} )) (要 $PREFIX_MARGIN 以上)"
say "  入れる先: $ENV_DEST"
say "  作る場所: $BUILD_PREFIX"
case "$BUILD_PREFIX" in
  "$HOME"/*) die "作る場所に作った人の home が入っています。組み立てを止めます。" ;;
esac

WORK="$(mktemp -d /private/tmp/cynovela-macos-app-work-XXXXXX)"
BUILD_SPEC="/private/tmp/cynovela-macos-app-spec-$$"
cleanup() { rm -rf "$WORK" "$BUILD_PREFIX" "$BUILD_SPEC"; }
trap cleanup EXIT
say "作業場所: $WORK"

APP="$WORK/${APP_NAME}.app"
ENV_DIR="$APP/Contents/Resources/env"
TREE_DIR="$APP/Contents/Resources/cynovela"

# ── 1. 中身 = 既存の梱包工程の all-in-one をそのまま使う ──────
say "──────────────────────────────────────────────"
say "1/7 中身を作る (build-dist.sh all-in-one ref=$REF)"
PAYLOAD_OUT="$WORK/payload"; mkdir -p "$PAYLOAD_OUT"
# 🔴 中間の成果物なので、圧縮を最弱にする (2026-08-30 の走行)
#    この .tar.gz は、この 20 行あとで展開して**その場で捨てる**。配らない。
#    強さ 9 で固める意味は無く、実測で 4.5 倍の差が出ていた
#    (M4 Max・800MB: -9 が 51.87 秒 / -1 が 11.41 秒。全部入りは 4.8GB)。
#    既定 (9) を変えていないので、Portable の配布物のバイト列は 1 ビットも動かない。
export DIST_GZIP_LEVEL=1
say "  中間の成果物なので圧縮の強さを 1 にする (配る Portable の既定 9 は変えない)"
bash "$ROOT/tools/build-dist.sh" "$PAYLOAD_OUT" all-in-one "$REF"
unset DIST_GZIP_LEVEL
PAYLOAD_TGZ="$(ls -1 "$PAYLOAD_OUT"/*.tar.gz | head -1)"
[ -f "$PAYLOAD_TGZ" ] || die "中身の配布物が作られませんでした"
say "中身: $PAYLOAD_TGZ ($(stat -f%z "$PAYLOAD_TGZ") bytes)"

mkdir -p "$APP/Contents/Resources" "$APP/Contents/MacOS" "$WORK/extract"
TOP="$(tar -tzf "$PAYLOAD_TGZ" | head -1 | cut -d/ -f1)"
[ -n "$TOP" ] || die "配布物の中の一番上のディレクトリ名を読めません"
tar -xzf "$PAYLOAD_TGZ" -C "$WORK/extract"
mv "$WORK/extract/$TOP" "$TREE_DIR"
rm -rf "$WORK/extract" "$PAYLOAD_OUT"
say "展開: Contents/Resources/cynovela (元の名前は $TOP)"
# 🔴 ここから先で使う版と入口の素は、机の上ではなく**取り出した木**のものである。
#    従来はここが机の上を見ていた。ref を指定して組んだときや、手直しが残ったまま
#    組んだときに「中身は ref・入口は机の上」という食い違いが黙って出る。
VERSION="$(read_version "$TREE_DIR")"
say "版 (取り出した木): $VERSION ← 以後はこの値だけを使う"
SRC_DIR="$TREE_DIR/macos-app"
for _f in main.swift Info.plist.in Distribution.xml.in; do
  [ -f "$SRC_DIR/$_f" ] || die "取り出した木に入口の素が在りません: macos-app/$_f"
done
say "入口の素: 取り出した木の macos-app/ から採る"
# 🔴 モデルは Resources/models ではなく、この木の store/models に置く。
#    config.py の探索の 1 番目が {この木}/store/models/… であり、そこに在れば
#    コードを 1 行も変えずに見つかる。包みの中なので、包みを捨てれば一緒に消える。
[ -d "$TREE_DIR/store/models" ] || die "モデルが同梱されていません: store/models"
say "モデル: $TREE_DIR/store/models ($(du -sh "$TREE_DIR/store/models" | cut -f1))"

# ── 2. 環境を作って、入れる先の場所へ書き換えて固める ─────────
say "──────────────────────────────────────────────"
say "2/7 同梱の環境を作る"
# ── 🔴 固めた環境の使い回し (2026-08-30 の走行) ────────────────────
#   環境の中身を決めているのは environment.yml と requirements.txt の 2 つだけで、
#   組む ref には一切依存しない。∴ この 2 つが 1 バイトも変わっていなければ、
#   conda env create → pip install → conda-pack の結果は同じものになる。
#   毎回作り直していたため、直しを 1 行入れるたびに同じ 2.3GB を作り直していた。
#
#   合鍵に入れるもの (1 つでも変われば作り直す):
#     ・environment.yml の中身      ・requirements.txt の中身
#     ・入れる先の道 (--dest-prefix がこれを焼き込むため)
#     ・conda の版 (作られる中身が変わり得るため)
#   使い回しをやめたいときは CYNOVELA_ENV_CACHE=0 を渡す。
ENV_CACHE_DIR="${CYNOVELA_ENV_CACHE_DIR:-$HOME/.cache/cynovela-build}"
ENV_CACHE_KEY="$(
  { shasum -a 256 "$ROOT/environment.yml" "$ROOT/requirements.txt" | awk '{print $1}'
    printf '%s\n' "$ENV_DEST"
    "$CONDA_BIN" --version 2>/dev/null || echo "conda-unknown"
  } | shasum -a 256 | cut -c1-32
)"
ENV_CACHE_TGZ="$ENV_CACHE_DIR/env-$ENV_CACHE_KEY.tar.gz"
ENV_TGZ="$WORK/.env.tar.gz"
say "  使い回しの合鍵: $ENV_CACHE_KEY"
say "  使い回しの置き場: $ENV_CACHE_TGZ"

if [ "${CYNOVELA_ENV_CACHE:-1}" = "1" ] && [ -f "$ENV_CACHE_TGZ" ]; then
  say "  🟢 使い回せる環境が在った。conda env create / pip install / conda-pack を飛ばす"
  say "     ($(stat -f%z "$ENV_CACHE_TGZ") bytes / $(shasum -a 256 "$ENV_CACHE_TGZ" | cut -c1-16)…)"
  cp "$ENV_CACHE_TGZ" "$ENV_TGZ"
  ENV_FROM_CACHE=1
else
  ENV_FROM_CACHE=0
  say "  使い回せる環境が無い。まっさらから作る"
rm -rf "$BUILD_PREFIX" "$BUILD_SPEC"; mkdir -p "$BUILD_SPEC"
# 🔴 conda は叩いた命令をそのまま conda-meta/history に書く。定義ファイルの道を
#    そのまま渡すと、作った人の home がそこに残る。∴ 定義も先に写してから渡す。
cp "$ROOT/environment.yml" "$ROOT/requirements.txt" "$BUILD_SPEC/"
say "  (1/4) conda 層: environment.yml"
( cd "$BUILD_SPEC" && "$CONDA_BIN" env create -p "$BUILD_PREFIX" -f environment.yml -y ) >&2
say "  (2/4) pip 層: requirements.txt"
( cd "$BUILD_SPEC" && "$BUILD_PREFIX/bin/python" -m pip install --no-input -r requirements.txt ) >&2
rm -rf "$BUILD_SPEC"

say "  (3/4) conda-pack --dest-prefix で固める"
PACK=("$CONDA_BIN" run -n base conda-pack)
if ! "${PACK[@]}" -p "$BUILD_PREFIX" --dest-prefix "$ENV_DEST" -o "$ENV_TGZ" \
      --exclude '*.pyc' --exclude '*/__pycache__' --exclude '__pycache__' >&2; then
  say "  conda-pack が止まった。--ignore-missing-files を付けて一度だけやり直す。"
  rm -f "$ENV_TGZ"
  "${PACK[@]}" -p "$BUILD_PREFIX" --dest-prefix "$ENV_DEST" -o "$ENV_TGZ" \
      --exclude '*.pyc' --exclude '*/__pycache__' --exclude '__pycache__' \
      --ignore-missing-files >&2
fi

  # 次の走行のために控える。中身は入れる先の道だけを見て作られており、
  # 作った場所には依存しない (--dest-prefix が焼き込むのは入れる先の道である)。
  if [ "${CYNOVELA_ENV_CACHE:-1}" = "1" ]; then
    mkdir -p "$ENV_CACHE_DIR"
    cp "$ENV_TGZ" "$ENV_CACHE_TGZ.tmp" && mv "$ENV_CACHE_TGZ.tmp" "$ENV_CACHE_TGZ"
    say "  次の走行のために控えた: $ENV_CACHE_TGZ ($(stat -f%z "$ENV_CACHE_TGZ") bytes)"
  fi
fi

say "  (4/4) Contents/Resources/env へ展開する (使い回し=$ENV_FROM_CACHE)"
mkdir -p "$ENV_DIR"
tar -xzf "$ENV_TGZ" -C "$ENV_DIR"
rm -f "$ENV_TGZ"
rm -rf "$BUILD_PREFIX"

# 🔴 --dest-prefix の道では conda-unpack は作られない。作られていたら前提が
#    崩れている (受け取り手が走らせると、直す必要の無いものを直しに行く)。
if [ -e "$ENV_DIR/bin/conda-unpack" ]; then
  die "bin/conda-unpack が在ります。--dest-prefix の前提が崩れています。"
fi
say "  bin/conda-unpack: 無し (--dest-prefix なので正しい)"
[ -x "$ENV_DIR/bin/python" ] || die "同梱の python が在りません: $ENV_DIR/bin/python"

# 作った命令の控えは受け取り手には使い道が無く、作った人の場所が写る唯一の場所である
rm -f "$ENV_DIR/conda-meta/history"
# 展開の途中でも作られ得るので、ここでもう一度落とす
find "$ENV_DIR" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
find "$ENV_DIR" -name '*.pyc' -delete 2>/dev/null || true

# ── Mach-O の一覧を作る (この先の 2 つの段が同じ一覧を使う) ────
#   🔴 見分けは**先頭の魔法の数**で行う。file(1) の出力を ':' で切って道を
#      取り出してはいけない。ユニバーサルバイナリでは
#      「<道> (for architecture arm64)」が返り、道でないものを道として扱う。
#      実測で 1 つの数え上げがこれで誤っていた。
#   🔴 名前 (*.so / *.dylib) で拾ってもいけない。同梱環境の Mach-O には
#      bin/ の実行ファイルのように拡張子を持たないものが多数ある。
MACHO_LIST="$WORK/macho.txt"
python3 - "$ENV_DIR" > "$MACHO_LIST" <<'PYMACHO'
import os, sys
root = sys.argv[1]
# Mach-O の先頭 4 バイト。thin(64bit LE) と fat の両方を見る。
MAGIC = {b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe",
         b"\xca\xfe\xba\xbe", b"\xbe\xba\xfe\xca"}
out = []
for dirpath, dirnames, filenames in os.walk(root):
    for fn in filenames:
        p = os.path.join(dirpath, fn)
        if os.path.islink(p):
            continue
        try:
            with open(p, "rb") as fh:
                if fh.read(4) in MAGIC:
                    out.append(p)
        except OSError:
            pass
print("\n".join(out))
PYMACHO
MACHO_N="$(grep -c . "$MACHO_LIST" || true)"
say "  Mach-O のファイル数 (魔法の数で判別): $MACHO_N"

# ── 組み立てのときの置き場を指す LC_RPATH を外す ───────────────
#   🔴 外す相手は「この走りが作った置き場」だけではない。pip はホイールを
#      使い回すため、**この企ての別の梱包工程が別の走りで作った置き場**が
#      焼き込まれて出てくる。実測 (公開した .pkg):
#        _zlib_state…so と cbor/_cbor…so の LC_RPATH が
#        /private/tmp/cynovela-portable-build-<番号>/lib を指していた。
#      これは Portable 版の梱包工程 (tools/build-dist.sh) の置き場であって、
#      この道具が作ったものではない。作った人の名前も home も入らないので
#      身元の関門は素通りするが、受け取り手の機械には無い場所である。
#      ∴ この企ての置き場の**すべての形**を外す。build-dist.sh の同じ所と
#      やり方 (install_name_tool -delete_rpath・バイトは手で書かない) は
#      揃えてある。
_rp_fixed=0; _rp_files=0
while IFS= read -r _so; do
  [ -n "$_so" ] || continue
  _hit=0
  while IFS= read -r _rp; do
    [ -n "$_rp" ] || continue
    case "$_rp" in
      /private/tmp/cynovela-*|/tmp/cynovela-*)
        if install_name_tool -delete_rpath "$_rp" "$_so" 2>/dev/null; then
          _rp_fixed=$((_rp_fixed+1)); _hit=1
        fi ;;
    esac
  done < <(otool -l "$_so" 2>/dev/null \
             | awk '/^ *cmd LC_RPATH$/{f=1; next} f&&$1=="path"{print $2; f=0}' \
             | sort -u)
  if [ "$_hit" -eq 1 ]; then _rp_files=$((_rp_files+1)); fi
done < "$MACHO_LIST"
say "  組み立て時の置き場を指す LC_RPATH を外した: $_rp_fixed 本 ($_rp_files ファイル)"

# ── フェイルクローズ: 一時の置き場を指す積み荷命令が 1 つも無いこと ──
#   黙って外し損ねるのが、上の欠陥が一度通ってしまった理由である。∴ 外した
#   あとに機械で確かめ、1 つでも残っていたら組み立てを止める。
#   見るのは**積み荷命令 (LC_RPATH / LC_LOAD_DYLIB / LC_LOAD_WEAK_DYLIB)** で
#   あって、ファイルの中身に出てくる文字列ではない。上流 conda-forge の
#   バイナリは中身に CI の道を持っているが、それはここで見るものではない。
_LC_BAD="$WORK/lc-tmp.txt"; : > "$_LC_BAD"
while IFS= read -r _m; do
  [ -n "$_m" ] || continue
  otool -l "$_m" 2>/dev/null \
    | awk -v f="$_m" '
        /^ *cmd LC_RPATH$/           {k="LC_RPATH";           next}
        /^ *cmd LC_LOAD_DYLIB$/      {k="LC_LOAD_DYLIB";      next}
        /^ *cmd LC_LOAD_WEAK_DYLIB$/ {k="LC_LOAD_WEAK_DYLIB"; next}
        /^ *cmd LC_/                 {k="";                   next}
        k!="" && ($1=="path" || $1=="name") { print k"\t"$2"\t"f; k="" }
      ' \
    | grep -E "^[A-Z_]+"$'\t'"(/private)?/tmp/" >> "$_LC_BAD" || true
done < "$MACHO_LIST"
_lc_n="$(sort -u "$_LC_BAD" | grep -c . || true)"
if [ "$_lc_n" != "0" ]; then
  echo "[app] 一時の置き場を指す積み荷命令が残っています: $_lc_n 件" >&2
  sort -u "$_LC_BAD" | sed "s|$ENV_DIR/|env/|g;s|^|[app]     |" >&2
  die "積み荷命令の関門に通りませんでした。組み立てを止めます。"
fi
say "  一時の置き場 (/private/tmp・/tmp) を指す積み荷命令: 0 件"

# ── 3. 署名の壊れた Mach-O を数えて、ad-hoc で署名し直す ──────
say "──────────────────────────────────────────────"
say "3/7 署名の壊れた Mach-O を直す (--dest-prefix は署名し直さないため)"
say "  対象の Mach-O: $MACHO_N 本 (上で作った一覧をそのまま使う)"
_bad=0; _fixed=0; _failed=0
while IFS= read -r _m; do
  [ -n "$_m" ] || continue
  if ! /usr/bin/codesign -v "$_m" >/dev/null 2>&1; then
    _bad=$((_bad+1))
    if /usr/bin/codesign -s - -f "$_m" >/dev/null 2>&1; then
      _fixed=$((_fixed+1))
    else
      _failed=$((_failed+1)); echo "[app]   署名し直せませんでした: $_m" >&2
    fi
  fi
done < "$MACHO_LIST"
say "  署名が妥当でなかった Mach-O: $_bad / 直した: $_fixed / 直せなかった: $_failed"
[ "$_failed" -eq 0 ] || die "署名し直せない Mach-O が在ります。組み立てを止めます。"

# 直したうえで、同梱の python が本当に動くところまで見る (版だけでは足りない)
# 直したうえで、同梱の python が本当に動くところまで見る。版だけの判定では、
# 署名が壊れていても「使える」と答えてしまう (壊れた python は exit 137 で黙って死ぬ)。
# 🔴 ただし、動かすと python はバイトコードを書く。実測: この 2 行だけで
#    __pycache__ 319 件・.pyc 1,680 件が同梱環境の中に生まれ、関門で止まった。
#    公開中の v1.1.1 に 2 万件の .pyc が入っていたのと同じ型である
#    (環境を一度動かしてから包み直した)。∴ -B と環境変数の両方で書かせない。
#    環境変数の方は、この走りから枝分かれする子にも効かせるために要る。
say "  同梱の python を動かして確かめる (バイトコードは書かせない)"
export PYTHONDONTWRITEBYTECODE=1
"$ENV_DIR/bin/python" -B -c 'import sys; print("[app]   python", sys.version.split()[0])' \
  || die "同梱の python が動きません (署名の直しが効いていない可能性)"
"$ENV_DIR/bin/python" -B -c 'import fastapi, uvicorn, chromadb, torch; print("[app]   fastapi/uvicorn/chromadb/torch: 読み込めました")' \
  || die "同梱の環境で必要な部品を読み込めません"

# 念のためもう一度掃いて、0 件であることをここで確かめる。署名は次の段で
# 包み全体を封じるので、それより前に片づいていなければならない。
find "$ENV_DIR" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
find "$ENV_DIR" -name '*.pyc' -delete 2>/dev/null || true
_pyc_n="$(find "$APP" -name '*.pyc' 2>/dev/null | wc -l | tr -d ' ')"
_pycache_n="$(find "$APP" -name '__pycache__' -type d 2>/dev/null | wc -l | tr -d ' ')"
say "  バイトコード: .pyc $_pyc_n 件 / __pycache__ $_pycache_n 件"
if [ "$_pyc_n" != "0" ] || [ "$_pycache_n" != "0" ]; then
  die "バイトコードが残っています。署名の前に止めます。"
fi

# ── 4. 入口を組む ────────────────────────────────────────────
say "──────────────────────────────────────────────"
say "4/7 入口 (Swift) を組む"
xcrun swiftc -target arm64-apple-macos12.0 -O \
  -o "$APP/Contents/MacOS/${APP_NAME}" "$SRC_DIR/main.swift"
sed "s/__VERSION__/${VERSION}/g" "$SRC_DIR/Info.plist.in" > "$APP/Contents/Info.plist"
/usr/bin/plutil -lint "$APP/Contents/Info.plist" >/dev/null || die "Info.plist が壊れています"
printf 'APPL????' > "$APP/Contents/PkgInfo"
say "  Contents/MacOS/${APP_NAME} / Info.plist / PkgInfo"

# ── 5. 署名 (ad-hoc) ─────────────────────────────────────────
say "──────────────────────────────────────────────"
say "5/7 ad-hoc で署名する (中の Mach-O が先・包みが最後)"

# 🔴 署名の**前に**、包みの中の名前を NFD へ揃える。理由 (実測):
#    pkgbuild は、拡張属性を持つファイルに対して AppleDouble の相方
#    (`._<名前>`) を目録 (Bom) に足す。このとき相方の名前は **NFD** で書く。
#    ところが元のファイルの名前は APFS が受け取ったままの並び (git が置いた
#    NFC) である。∴ 名前が NFC のファイルだけ、相方と字が一致しなくなる。
#    一致しないと pkgbuild の後始末が両者を組にできず、
#      ・相方の mode が 0 (`?---------`) のまま埋まらない
#      ・本体の持ち主が root に書き換えられず、組んだ人の uid のまま残る
#    という 2 つが同時に起きる。公開した .pkg では、木の中で唯一 ASCII でない
#    名前を持つ dummy-corpus/00-…md の 1 件がこれに当たっていた
#    (93,155 件中 1 件が 501/0・相方 1 件が mode 0)。PackageInfo は
#    overwrite-permissions="true" なので、この持ち主はそのまま受け取り手の
#    機械に載る。root の包みの中に、その機械の最初の利用者が書ける穴が開く。
#    --ownership を recommended/preserve/preserve-other のどれにしても直らない
#    (実測)。∴ 名前の方を先に NFD へ揃えて、pkgbuild が組にできるようにする。
#    APFS は正規化を区別しないので、NFC の名前で開いても同じ物に届く (実測)。
#    署名は名前を封じるので、この付け替えは **必ず署名より前**に行う。
_nfd_n="$(python3 - "$APP" <<'PYNFD'
import os, sys, unicodedata
root = sys.argv[1]
n = 0
for dirpath, dirnames, filenames in os.walk(root, topdown=False):
    for name in filenames + dirnames:
        nfd = unicodedata.normalize("NFD", name)
        if nfd != name:
            os.rename(os.path.join(dirpath, name), os.path.join(dirpath, nfd))
            n += 1
print(n)
PYNFD
)"
say "  名前を NFD へ揃えた: $_nfd_n 件 (pkgbuild の AppleDouble と字を合わせるため)"

# 印 (拡張属性) は署名の前に全部落とす。残ると署名の封に混ざる。
# 🔴 com.apple.provenance だけは落ちない (この属性は消せない)。∴ 拡張属性を
#    持つファイルは残り、pkgbuild は相方を作り続ける。上の NFD 揃えは、
#    それを前提にした直しである。
/usr/bin/xattr -cr "$APP" 2>/dev/null || true
# 自分で組んだ入口を先に署名する
/usr/bin/codesign -s - -f "$APP/Contents/MacOS/${APP_NAME}" \
  || die "入口を署名できませんでした"
# --deep は非推奨。中は上で 1 本ずつ見て直してあるので、ここは包みだけを封じる。
/usr/bin/codesign -s - -f "$APP" || die "包みを署名できませんでした"
/usr/bin/codesign -v "$APP" >/dev/null 2>&1 \
  && say "  codesign -v: 通った" \
  || say "  注意: codesign -v が通りませんでした (中身の封は下の関門で見ます)"
/usr/bin/codesign -dv "$APP" 2>&1 | sed 's/^/[app]   /' || true

# ── 6. 組み上がった .app を、もう一度 3 種の検査にかける ──────
say "──────────────────────────────────────────────"
say "6/7 組み上がった .app を検査する (build-dist.sh inspect・3種)"
# 🔴 検査は .app のルートに直接当ててはいけない。dist_inspect の除外と許可は
#    **ルート直下からの相対パスで固定**されているためである。実測 (初回走行):
#      ・(c-2) の除外 './.condapack-cynovela/*' が当たらず、同梱環境の
#        conda-meta/*.json (conda が書く 32 桁の md5) と CPython の
#        secrets.py / uuid.py が 19 件の偽の検出になった。
#      ・(a) の許可 {"cynovela.yaml"} が当たらず、配布物に**わざと**書いてある
#        初期のパスワード 2 件が偽の検出になった。
#    ∴ 中身を Portable と同じ並び (木がルート・環境が .condapack-cynovela) へ
#    写してから当てる。写しは APFS の複製なので場所を食わない。
#    こうすると効く規則は Portable のときと 1 つも変わらない。加えて、この形態
#    だけのファイル (組んだ入口と Info.plist) も検査の対象に入る。
INSPECT_VIEW="$WORK/inspect-view"
rm -rf "$INSPECT_VIEW"
cp -Rc "$TREE_DIR" "$INSPECT_VIEW" 2>/dev/null || cp -R "$TREE_DIR" "$INSPECT_VIEW"
cp -Rc "$ENV_DIR" "$INSPECT_VIEW/.condapack-cynovela" 2>/dev/null \
  || cp -R "$ENV_DIR" "$INSPECT_VIEW/.condapack-cynovela"
mkdir -p "$INSPECT_VIEW/macos-app-built"
cp "$APP/Contents/MacOS/${APP_NAME}" "$APP/Contents/Info.plist" "$INSPECT_VIEW/macos-app-built/"
say "  検査の並び: 木=ルート / 環境=.condapack-cynovela / 組んだ入口=macos-app-built"
bash "$ROOT/tools/build-dist.sh" inspect "$INSPECT_VIEW" "$CHECK_VALUES"
rm -rf "$INSPECT_VIEW"

# ── 7. 梱包 ──────────────────────────────────────────────────
say "──────────────────────────────────────────────"
say "7/7 .pkg に梱包する (置き場を動かさない形)"
PKGROOT="$WORK/pkgroot"; mkdir -p "$PKGROOT"
mv "$APP" "$PKGROOT/"
# 🔴 動かしたら、そこから導いていた道もすべて付け直す。付け直さないと、
#    このあと木の中を読む所 (Distribution.xml.in) が消えた場所を見に行く。
APP="$PKGROOT/${APP_NAME}.app"
TREE_DIR="$APP/Contents/Resources/cynovela"
ENV_DIR="$APP/Contents/Resources/env"
SRC_DIR="$TREE_DIR/macos-app"

# ── 🔴 持ち主が root になることに、mode を合わせる (2026-08-30 の走行) ──
#   pkgbuild は目録の持ち主を 0/0 に付け替えるが、**mode は配布元のものを
#   そのまま引き継ぐ**。∴ 作った人の手元で 600/700 だったファイルは、
#   `600 root:wheel` = **root 以外は誰も読めない**ファイルになって配られる。
#
#   実測 (公開直前だった .pkg):
#     ・store/secret.key            0600 root:wheel → 保存先を作る写しが必ず失敗する
#     ・store/models/** の 18 本     0700 root:wheel → 埋め込みも再ランクも読めない
#       (うち 2 本は 2.27GB の重み本体。models は写さず包みの中から直接読む作り)
#   受け取り手の Mac では、この 19 本が一度も読めなかった。
#
#   直し = 梱包の直前に、包み全体へ「持ち主に読めるものは、その他にも読ませる」を
#   当てる。go+rX なので、実行権は元から実行できたものにしか付かず、
#   書き権は 1 つも足さない。
#
#   🔴 secret.key を 644 にしてよい理由:
#     ・.pkg は全利用者共通の /Applications に入り、鍵の実体は同梱されている。
#       ∴ 0600 は元から秘匿していない (root しか読めない = 誰も使えない、だけ)。
#     ・鍵を守っているのは所有権 (root:wheel・読み取り専用の包みの中) であり、
#       mode ではない。書き換えるには管理者権限が要る。
#     ・現状のほうが危険である。鍵が読めないとサーバは**新しい鍵を作り**、
#       同梱データが復号できなくなる (過去に実測した InvalidToken と同型)。
say "  持ち主が root になることに mode を合わせる (go+rX)"
_narrow_before="$(find "$PKGROOT" -type f ! -perm -004 2>/dev/null | wc -l | tr -d ' ')"
chmod -R go+rX "$PKGROOT"
_narrow_after="$(find "$PKGROOT" -type f ! -perm -004 2>/dev/null | wc -l | tr -d ' ')"
say "    その他が読めない通常ファイル: $_narrow_before 件 → $_narrow_after 件"
[ "$_narrow_after" = "0" ] || die "go+rX を当てても、その他が読めないファイルが $_narrow_after 件 残っています"
# 書き権を足していないことを、その場で確かめる (go+rX は w を足さないはずである)
_ww="$(find "$PKGROOT" \( -type f -o -type d \) -perm -022 2>/dev/null | wc -l | tr -d ' ')"
[ "$_ww" = "0" ] || die "その他に書き権の付いた項が $_ww 件 在ります (go+rX が w を足しました)"
say "    その他に書き権の付いた項: 0 件"

# 木がまだ在るうちに、組み立ての宣言を作っておく (下で木ごと消すため)
DIST_XML="$WORK/Distribution.xml"
sed "s/__VERSION__/${VERSION}/g" "$SRC_DIR/Distribution.xml.in" > "$DIST_XML"

COMPONENT_PLIST="$WORK/component.plist"
/usr/bin/pkgbuild --analyze --root "$PKGROOT" "$COMPONENT_PLIST" >&2
# 🔴 置き場を動かさないことの決め手は BundleIsRelocatable=false である。
#    入れ子の包みは 1 つの要素の ChildBundles の下に入るので、素の鍵 1 回で全部に効く。
/usr/bin/plutil -replace BundleIsRelocatable -bool NO "$COMPONENT_PLIST"
say "  BundleIsRelocatable=false を入れた"

COMPONENT_PKG="$WORK/component.pkg"
# 🔴 pkgbuild --component は使わない。--component-plist を受け付けないため、
#    その道では置き場を動かさない指定ができない。
/usr/bin/pkgbuild --identifier "$APP_ID" --version "$VERSION" \
  --root "$PKGROOT" --component-plist "$COMPONENT_PLIST" \
  --install-location /Applications "$COMPONENT_PKG" >&2

# 中身は component.pkg に入り切っている。ここで木を消して場所を空ける
# (このあと productbuild と、関門の展開で、それぞれ同じだけの場所が要る)。
rm -rf "$PKGROOT"
say "  梱包前の木を片づけた (空き $(df -g / | awk 'NR==2{print $4}')Gi)"

OUT_PKG="$OUT_DIR/${APP_NAME}-${VERSION}-macos-arm64.pkg"
rm -f "$OUT_PKG"
/usr/bin/productbuild --distribution "$DIST_XML" --package-path "$WORK" "$OUT_PKG" >&2
[ -f "$OUT_PKG" ] || die "productbuild が .pkg を作りませんでした"
rm -f "$COMPONENT_PKG"

say "完成: $OUT_PKG"
say "$(stat -f%z "$OUT_PKG") bytes"
shasum -a 256 "$OUT_PKG" | sed 's/^/[app] /'

# ── 関門: 出来上がった .pkg を展開して中身を確かめる ──────────
say "──────────────────────────────────────────────"
say "関門: 出来上がった .pkg を展開して確かめる"
GATE="$WORK/gate"; rm -rf "$GATE"
/usr/sbin/pkgutil --expand-full "$OUT_PKG" "$GATE" >&2
gate_fail=0

# (1) 置き場を動かさない形になっているか。決め手は relocate に bundle の子が
#     居ないことである。relocatable="false" はどの作り方でも付くので当てにならない。
PKGINFO="$(find "$GATE" -name PackageInfo | head -1)"
[ -n "$PKGINFO" ] || die "展開した中に PackageInfo が在りません"
if python3 - "$PKGINFO" <<'PYREL'
import sys, xml.etree.ElementTree as ET
root = ET.parse(sys.argv[1]).getroot()
rel = root.findall("relocate")
n_bundle = sum(len(r.findall("bundle")) for r in rel)
print("[app]   relocate の数=%d / その下の bundle の数=%d" % (len(rel), n_bundle))
sys.exit(0 if n_bundle == 0 else 1)
PYREL
then
  say "  置き場は動かない (relocate は空)"
else
  echo "[app] relocate に bundle の子が居ます。置き場が動く形です。" >&2
  gate_fail=1
fi

# (2) 作った人の身元。字のまま書くと自分自身が引っかかるので、走るときに組み立てる。
GATE_DEV_USER="$(id -un)"
GATE_WORK_PAT="$(printf 'cynovela\055work\055')"
gate_ident=0
for _pat in "$GATE_DEV_USER" "$HOME" "$GATE_WORK_PAT"; do
  [ -n "$_pat" ] || continue
  _hits="$(grep -rlF "$_pat" "$GATE" --binary-files=text 2>/dev/null || true)"
  if [ -n "$_hits" ]; then
    _n="$(printf '%s\n' "$_hits" | wc -l | tr -d ' ')"
    echo "[app] 作った人の身元を検出: $_n ファイル (先頭20件)" >&2
    printf '%s\n' "$_hits" | head -20 | sed "s|^$GATE/||;s|^|[app]     |" >&2
    gate_ident=1
  fi
done
if [ "$gate_ident" -ne 0 ]; then gate_fail=1; else say "  作った人の身元 (利用者名・home・作業場所の名前): 0件"; fi

# (2-b) /Users/ の総数。止めはしないが内訳を残す (大半は上流 conda-forge の CI の道)。
_u="$( { grep -rl "/Users/" "$GATE" --binary-files=text 2>/dev/null || true; } | wc -l | tr -d ' ')"
_r="$( { grep -rl "/Users/runner/" "$GATE" --binary-files=text 2>/dev/null || true; } | wc -l | tr -d ' ')"
say "  /Users/ を含むファイル: $_u 件 (うち上流の /Users/runner/ が $_r 件)"

# (3) バイトコード。受け取り手の機械で作り直されるものを配らない。
_pycache="$(find "$GATE" -name '__pycache__' -type d 2>/dev/null | wc -l | tr -d ' ')"
_pyc="$(find "$GATE" -name '*.pyc' 2>/dev/null | wc -l | tr -d ' ')"
say "  __pycache__: $_pycache 件 / .pyc: $_pyc 件"
if [ "$_pycache" != "0" ] || [ "$_pyc" != "0" ]; then gate_fail=1; fi

# (4) 入れる先の道が中に書かれているか (--dest-prefix が効いたか) と、
#     作る場所の道が残っていないか。
#     🔴 作る場所は「今回の $$」ではなく**幹で**当てる (2026-08-30 の走行)。
#        環境を使い回すようにしたため、包みの中の環境は**別の走行の**作る場所で
#        作られていることがある。今回の PID を含む道だけを当てていると、
#        使い回した環境に前の走行の道が残っていても素通りしてしまう。
#        ∴ PID を外した幹で当てる。幹は上で 8 進から組み立ててある
#        (ここで字のまま書くと、この関門がこのファイル自身を見つけて止まる)。
_dest_n="$( { grep -rl "$ENV_DEST" "$GATE" --binary-files=text 2>/dev/null || true; } | wc -l | tr -d ' ')"
_build_n="$( { grep -rl "$BUILD_PREFIX_STEM" "$GATE" --binary-files=text 2>/dev/null || true; } | wc -l | tr -d ' ')"
say "  入れる先の道を含むファイル: $_dest_n 件 / 作る場所の道を含むファイル: $_build_n 件 (幹で照合: $BUILD_PREFIX_STEM)"
if [ "$_dest_n" -eq 0 ]; then
  echo "[app] 入れる先の道が 1 件も書かれていません。--dest-prefix が効いていません。" >&2
  gate_fail=1
fi
if [ "$_build_n" -ne 0 ]; then
  echo "[app] 作る場所の道が残っています (先頭20件):" >&2
  { grep -rl "$BUILD_PREFIX_STEM" "$GATE" --binary-files=text 2>/dev/null || true; } \
    | head -20 | sed "s|^$GATE/||;s|^|[app]     |" >&2
  gate_fail=1
fi

# (5) conda-unpack が入っていないこと (--dest-prefix の道では作られない)
if find "$GATE" -name 'conda-unpack' | grep -q .; then
  echo "[app] conda-unpack が入っています。--dest-prefix の前提が崩れています。" >&2
  gate_fail=1
else
  say "  conda-unpack: 0件"
fi

# (6) 数えるだけのもの。角括弧の形なので、この行そのものは当たらない。
for _g in "$GATE_DEV_USER" "$GATE_WORK_PAT" "DD-CYN-[0-9]{4}"; do
  _n="$( { grep -rlE "$_g" "$GATE" --binary-files=text 2>/dev/null || true; } | wc -l | tr -d ' ')"
  say "  参考: 記号を含むファイル数 = $_n"
done

# (7) 目録 (Bom) の持ち主と mode。受け取り手の機械に実際に載るのはこの目録の
#     値である (PackageInfo が overwrite-permissions="true" のため)。1 件でも
#     root 以外が混ざれば、root の包みの中に、その機械の利用者が書ける穴が開く。
#     実測 (公開した .pkg): 名前が NFC のファイル 1 件が 501/0 で、その
#     AppleDouble の相方 1 件が mode 0 (`?---------`) だった。段 5 の NFD 揃えが
#     その直しであり、ここはそれが効いたことを機械で確かめる関門である。
#     mode は形も見る: 通常ファイル(100)・ディレクトリ(40)・記号リンク(120) の
#     どれかで、権限 3 桁が付いていること。
_bom="$(find "$GATE" -name 'Bom' -type f | head -1)"
if [ -z "$_bom" ]; then
  echo "[app] 展開した中に Bom が在りません。持ち主を確かめられません。" >&2
  gate_fail=1
else
  _bom_total="$(/usr/bin/lsbom -p mugf "$_bom" | grep -c . || true)"
  _bom_bad="$WORK/bom-bad.txt"
  /usr/bin/lsbom -p mugf "$_bom" \
    | awk -F'\t' '$2!="0" || $3!="0" || $1 !~ /^(100|40|120)[0-7][0-7][0-7]$/' \
    > "$_bom_bad" || true
  _bom_bad_n="$(grep -c . "$_bom_bad" || true)"
  say "  目録の件数: $_bom_total / 0/0 でないか mode の形が壊れている件数: $_bom_bad_n"
  if [ "$_bom_bad_n" != "0" ]; then
    echo "[app] 目録に root/wheel でない項、または壊れた mode の項が在ります (先頭50件):" >&2
    head -50 "$_bom_bad" | sed 's|^|[app]     |' >&2
    gate_fail=1
  fi
fi

# (8) 🔴 目録の mode を「その他が読めるか」で見る (2026-08-30 の走行)
#     (7) は持ち主が 0/0 か、mode が 3 桁の形をしているかしか見ていなかった。
#     `^(100|40|120)[0-7][0-7][0-7]$` は **0 も 6 も 7 も通す**。∴ 0600 と 0700 が
#     素通りし、root しか読めないファイルが 19 本入ったまま配られる寸前だった。
#     受け取り手はサーバを root では走らせない。∴ 持ち主が root の包みの中では、
#     「その他が読めない」は「誰も読めない」と同じである。
#       ・通常ファイル (100) … その他に読み権 (4) が要る
#       ・ディレクトリ (40)  … その他に読み権 (4) と入る権 (1) が要る
#       ・記号リンク (120)   … 中身は見ないので数えない
if [ -n "$_bom" ]; then
  _bom_narrow="$WORK/bom-narrow.txt"
  /usr/bin/lsbom -p mf "$_bom" | awk -F'\t' '
    {
      m = $1; p = $2
      d = substr(m, length(m), 1) + 0            # その他の 1 桁
      r = int(d / 4) % 2                          # 読み権
      x = d % 2                                   # 入る権 (ディレクトリ)
      t = substr(m, 1, length(m) - 3)             # 種類
      if (t == "100" && r == 0)              print m "\t" p
      else if (t == "40" && (r == 0 || x == 0)) print m "\t" p
    }' > "$_bom_narrow" || true
  _bom_narrow_n="$(grep -c . "$_bom_narrow" || true)"
  say "  その他が読めない項 (通常ファイル・ディレクトリ): $_bom_narrow_n 件"
  if [ "$_bom_narrow_n" != "0" ]; then
    echo "[app] 目録に、その他が読めない項が在ります。受け取り手の Mac で読めません (先頭50件):" >&2
    head -50 "$_bom_narrow" | sed 's|^|[app]     |' >&2
    gate_fail=1
  fi
fi

rm -rf "$GATE"

if [ "$gate_fail" -ne 0 ]; then
  echo "[app] 関門に通らなかったため、この成果物は配れません。" >&2
  echo "[app] 成果物は残してあります: $OUT_PKG" >&2
  exit 1
fi
say "関門 通過"
say "──────────────────────────────────────────────"
say "出来上がり: $OUT_PKG"
