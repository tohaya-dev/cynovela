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
BUILD_PREFIX="/private/tmp/cynovela-macos-app-build-$$"
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
bash "$ROOT/tools/build-dist.sh" "$PAYLOAD_OUT" all-in-one "$REF"
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
say "2/7 同梱の環境を作る (毎回まっさらから作る)"
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
ENV_TGZ="$WORK/.env.tar.gz"
PACK=("$CONDA_BIN" run -n base conda-pack)
if ! "${PACK[@]}" -p "$BUILD_PREFIX" --dest-prefix "$ENV_DEST" -o "$ENV_TGZ" \
      --exclude '*.pyc' --exclude '*/__pycache__' --exclude '__pycache__' >&2; then
  say "  conda-pack が止まった。--ignore-missing-files を付けて一度だけやり直す。"
  rm -f "$ENV_TGZ"
  "${PACK[@]}" -p "$BUILD_PREFIX" --dest-prefix "$ENV_DEST" -o "$ENV_TGZ" \
      --exclude '*.pyc' --exclude '*/__pycache__' --exclude '__pycache__' \
      --ignore-missing-files >&2
fi

say "  (4/4) Contents/Resources/env へ展開する"
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

# 組み立てのときの置き場を指す LC_RPATH を外す
_rp_fixed=0
while IFS= read -r -d '' _so; do
  _rp="$(otool -l "$_so" 2>/dev/null | awk '/LC_RPATH/{f=1} f&&/ path /{print $2; f=0}' || true)"
  case "$_rp" in
    */cynovela-macos-app-build-*)
      install_name_tool -delete_rpath "$_rp" "$_so" 2>/dev/null && _rp_fixed=$((_rp_fixed+1)) ;;
  esac
done < <(find "$ENV_DIR" \( -name '*.so' -o -name '*.dylib' \) -print0 2>/dev/null)
say "  組み立て時の置き場を指す LC_RPATH を外した: $_rp_fixed 本"

# ── 3. 署名の壊れた Mach-O を数えて、ad-hoc で署名し直す ──────
say "──────────────────────────────────────────────"
say "3/7 署名の壊れた Mach-O を直す (--dest-prefix は署名し直さないため)"
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
say "  Mach-O のファイル数: $MACHO_N"
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
say "  同梱の python を動かして確かめる"
"$ENV_DIR/bin/python" -c 'import sys; print("[app]   python", sys.version.split()[0])' \
  || die "同梱の python が動きません (署名の直しが効いていない可能性)"
"$ENV_DIR/bin/python" -c 'import fastapi, uvicorn, chromadb, torch; print("[app]   fastapi/uvicorn/chromadb/torch: 読み込めました")' \
  || die "同梱の環境で必要な部品を読み込めません"

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
# 印 (拡張属性) は署名の前に全部落とす。残ると署名の封に混ざる。
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
_dest_n="$( { grep -rl "$ENV_DEST" "$GATE" --binary-files=text 2>/dev/null || true; } | wc -l | tr -d ' ')"
_build_n="$( { grep -rl "$BUILD_PREFIX" "$GATE" --binary-files=text 2>/dev/null || true; } | wc -l | tr -d ' ')"
say "  入れる先の道を含むファイル: $_dest_n 件 / 作る場所の道を含むファイル: $_build_n 件"
if [ "$_dest_n" -eq 0 ]; then
  echo "[app] 入れる先の道が 1 件も書かれていません。--dest-prefix が効いていません。" >&2
  gate_fail=1
fi
if [ "$_build_n" -ne 0 ]; then
  echo "[app] 作る場所の道が残っています (先頭20件):" >&2
  { grep -rl "$BUILD_PREFIX" "$GATE" --binary-files=text 2>/dev/null || true; } \
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

rm -rf "$GATE"

if [ "$gate_fail" -ne 0 ]; then
  echo "[app] 関門に通らなかったため、この成果物は配れません。" >&2
  echo "[app] 成果物は残してあります: $OUT_PKG" >&2
  exit 1
fi
say "関門 通過"
say "──────────────────────────────────────────────"
say "出来上がり: $OUT_PKG"
