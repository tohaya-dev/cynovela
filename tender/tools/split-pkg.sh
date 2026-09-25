#!/bin/bash
# ============================================================
#  配る .pkg を、送るあいだだけ分ける (macos-app-20260830)
#
#  出来上がりは 1 本の .pkg である。分けるのは GitHub の Releases が
#  1 ファイル 2 GiB までしか受け取らないためで、それ以外の理由は無い。
#  受け取り手は Cynovela-assemble.command をダブルクリックすれば、
#  元の 1 本に戻したうえで検査を通り、そのまま入れる画面が開く。
#
#  刻み幅はモデルの配布と同じ 1,500,000,000 バイトに揃える。変えない。
#
#  使い方: tools/split-pkg.sh <出来上がった .pkg> <出力先ディレクトリ>
# ============================================================
set -eu

SRC="${1:?分ける .pkg を指定してください}"
OUTDIR="${2:?出力先ディレクトリを指定してください}"
CHUNK=1500000000
LIMIT=2147483648   # GitHub Releases の 1 ファイルの上限 (2 GiB)

[ -f "$SRC" ] || { echo "[split] 在りません: $SRC" >&2; exit 2; }
mkdir -p "$OUTDIR"

BASE="$(basename "$SRC")"
SIZE="$(stat -f%z "$SRC")"
FULL_SHA="$(shasum -a 256 "$SRC" | cut -d' ' -f1)"

echo "[split] 元: $SRC"
echo "[split]   $SIZE バイト / sha256=$FULL_SHA"

if [ "$SIZE" -lt "$LIMIT" ]; then
  echo "[split] 2 GiB 未満のため分けません。1 本のまま配ってください。"
  exit 0
fi

rm -f "$OUTDIR/$BASE".part[0-9][0-9] "$OUTDIR/Cynovela-assemble.command"
( cd "$OUTDIR" && split -b "$CHUNK" -a 2 -d "$SRC" "$BASE.part" )

PARTS=()
while IFS= read -r p; do PARTS+=("$(basename "$p")"); done < <(ls "$OUTDIR/$BASE".part[0-9][0-9] | sort)
echo "[split] ${#PARTS[@]} 本に分けました:"
for p in "${PARTS[@]}"; do
  printf '[split]   %-52s %13s バイト\n' "$p" "$(stat -f%z "$OUTDIR/$p")"
done

# ── 受け取り手が叩く結合の入口を作る ──────────────────────────
ASM="$OUTDIR/Cynovela-assemble.command"
{
  echo '#!/bin/bash'
  echo '# Cynovela — 分かれた片を元の 1 本に戻して、入れる画面を開きます。'
  echo '#   このファイルと片を同じフォルダに置いて、ダブルクリックしてください。'
  echo '#   戻したものが元と 1 バイトも違わないことを確かめてから開きます。'
  echo 'set -u'
  echo 'cd "$(dirname "$0")"'
  echo "PKG=\"$BASE\""
  echo "FULL_SHA=\"$FULL_SHA\""
  echo "FULL_SIZE=$SIZE"
  printf 'PARTS=('
  for p in "${PARTS[@]}"; do printf '"%s" ' "$p"; done
  echo ')'
  echo 'PART_SHA=('
  for p in "${PARTS[@]}"; do
    echo "  \"$(shasum -a 256 "$OUTDIR/$p" | cut -d' ' -f1)\""
  done
  echo ')'
  cat <<'ASMBODY'

echo "──────────────────────────────────────────────"
echo " Cynovela — 分かれた片を元に戻します"
echo "──────────────────────────────────────────────"

# 1. 片がそろっているか
missing=0
for p in "${PARTS[@]}"; do
  if [ ! -f "$p" ]; then echo "  在りません: $p"; missing=1; fi
done
if [ "$missing" != "0" ]; then
  echo ""
  echo "片がそろっていません。落とし直してから、もう一度叩いてください。"
  echo "要る片: ${PARTS[*]}"
  exit 1
fi
echo "  片は ${#PARTS[@]} 本そろっています。"

# 2. 片ごとに中身を確かめる
echo "  片の中身を確かめています…"
i=0
for p in "${PARTS[@]}"; do
  got="$(shasum -a 256 "$p" | cut -d' ' -f1)"
  if [ "$got" != "${PART_SHA[$i]}" ]; then
    echo ""
    echo "  $p が壊れています (落とし直してください)。"
    echo "    あるべき: ${PART_SHA[$i]}"
    echo "    実際    : $got"
    exit 1
  fi
  i=$((i+1))
done
echo "  片はすべて正しいものでした。"

# 3. つなぐ
echo "  つないでいます… (数分かかります)"
rm -f "$PKG"
cat "${PARTS[@]}" > "$PKG" || { echo "  つなぐのに失敗しました。"; exit 1; }

# 4. つないだものを、もう一度まるごと確かめる
got_size="$(stat -f%z "$PKG")"
if [ "$got_size" != "$FULL_SIZE" ]; then
  echo "  大きさが違います (あるべき $FULL_SIZE / 実際 $got_size)。"
  rm -f "$PKG"; exit 1
fi
got_full="$(shasum -a 256 "$PKG" | cut -d' ' -f1)"
if [ "$got_full" != "$FULL_SHA" ]; then
  echo "  つないだものが元と違います。"
  echo "    あるべき: $FULL_SHA"
  echo "    実際    : $got_full"
  rm -f "$PKG"; exit 1
fi
echo "  つないだものは元と 1 バイトも違いませんでした。"
echo ""
echo "──────────────────────────────────────────────"
echo " 出来上がり: $(pwd)/$PKG"
echo "──────────────────────────────────────────────"
echo ""
echo " このあと入れる画面が開きます。"
echo ""
echo " 🔴 「開発元が未確認のため開けません」と出たときは:"
echo "    Finder で $PKG を右クリック →「開く」→ もう一度「開く」"
echo "    この配布物には Apple の証明書による署名を付けていません。"
echo "    理由は配布の説明書に書いてあります。"
echo ""
open "$PKG"
ASMBODY
} > "$ASM"
chmod +x "$ASM"

echo "[split] 結合の入口: $ASM"
echo "[split] 片の SHA256:"
( cd "$OUTDIR" && shasum -a 256 "${PARTS[@]}" "$(basename "$ASM")" )
