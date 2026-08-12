#!/bin/bash
# Cynovela の読み込むフォルダを足す入口 (DD-CYN-0071・決定 31-2)
#   ダブルクリックするとターミナルが開き、フォルダを選ぶ画面が出ます。
#   選ぶ画面と控えへの書き込みは ./launch.sh --add (tools/launch-body.sh) の
#   既にある道をそのまま使い、このファイルは結果を案内へ直すだけの薄い層です。
#   このファイルは起動しません。控えに書くだけです (決定 7-1・起動の種類は増えない)。
#   起動は Cynovela-start.command、停止は Cynovela-stop.command をダブルクリックしてください。
set -u
cd "$(dirname "$0")"

# 形態の見分け: deploy/container が在れば入れ物 (コンテナ) で動く形。
#   在れば「起動し直すと読み込める」、無ければ「すぐに選べる」を出し分ける。
_IN_CONTAINER_FORM=0
[ -d deploy/container ] && _IN_CONTAINER_FORM=1

# 足す前の控えの顔ぶれ (同じフォルダの再追加 = すでに足してある、を見分けるため)
_BEFORE="$(./launch.sh --list 2>/dev/null || echo '[]')"

_OUT="$(./launch.sh --add 2>&1)"
_RC=$?

if [ $_RC -ne 0 ]; then
    if printf '%s' "$_OUT" | /usr/bin/grep -q "キャンセル"; then
        echo "フォルダを選びませんでした。何も足していません。"
        echo "このターミナルは閉じてかまいません。"
        exit 0
    fi
    # 想定していない失敗: 本体の出力をそのまま見せる (理由を隠さない)
    printf '%s\n' "$_OUT"
    echo "このターミナルは閉じてかまいません。"
    exit 1
fi

# 中の名前を本体の出力から取り出す
_NAME="$(printf '%s\n' "$_OUT" | /usr/bin/sed -n 's/^取り込み元を追加しました (中の名前: \([^ )]*\).*$/\1/p' | head -1)"
if [ -z "$_NAME" ]; then
    printf '%s\n' "$_OUT"
    echo "このターミナルは閉じてかまいません。"
    exit 1
fi

# 場所は控えから実測で引く (--list は JSON を返す。python3 は --add 自体が使うものと同じ)
_PLACE="$(./launch.sh --list 2>/dev/null | python3 -c 'import json,sys
name = sys.argv[1]
roots = json.load(sys.stdin)
print(next((r.get("host_path", "") for r in roots if r.get("name") == name), ""))' "$_NAME")"

# 足す前から同じ名前が居たなら、控えには何も書かれていない (足す側が冪等なため)
if printf '%s' "$_BEFORE" | python3 -c 'import json, sys
name = sys.argv[1]
try:
    roots = json.load(sys.stdin)
except Exception:
    roots = []
sys.exit(0 if any(r.get("name") == name for r in roots) else 1)' "$_NAME" 2>/dev/null; then
    echo "同じ名前のフォルダが、すでに足されています。"
    echo "  すでにあるもの : ${_NAME}（${_PLACE}）"
    echo "足しませんでした。別の名前のフォルダを選んでください。"
    echo "このターミナルは閉じてかまいません。"
    exit 0
fi

echo "読み込むフォルダを足しました。"
echo "  足したフォルダ : ${_PLACE}"
echo "  中での呼び名   : ${_NAME}"
if [ "$_IN_CONTAINER_FORM" = "1" ]; then
    echo "まだ読み込まれていません。"
    echo "Cynovela-start.command をダブルクリックして起動し直すと、読み込めるようになります。"
else
    echo "いま動いている Cynovela の画面から、すぐに選べます。"
fi
echo "このターミナルは閉じてかまいません。"
exit 0
