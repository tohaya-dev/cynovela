#!/bin/bash
# Cynovela を止める入口 (N-7)
#   ダブルクリックするとターミナルが開き、止め方と結果をこの画面に出します。
#   止めるだけです。資料と設定は消えません。
set -u
cd "$(dirname "$0")"
CONF_REPO="$(pwd)"
. tools/conf.sh
NAME="$(conf_get_or container name "$CONF_DEFAULT_CNAME")"
VOLPREFIX="$(conf_get_or container volume_prefix "$CONF_DEFAULT_VOLPREFIX")"
ENG="$(conf_get container engine_command)"
[ -z "$ENG" ] && ENG="$(conf_get container engine)"
[ -z "$ENG" ] && ENG="podman"

echo "止め方は次のとおりです。この場で同じことを行います。"
echo "  bash stop.sh   （中身は: $ENG stop ${NAME}）"
echo ""
bash stop.sh

# 本当に止まったかを実測して出す ($ENG はコマンド列のことがあるため意図して引用しない)
_st="$($ENG container inspect "$NAME" --format '{{.State.Running}}' 2>/dev/null || echo false)"
if [ "$_st" = "true" ]; then
    echo ""
    echo "まだ動いています。$ENG stop $NAME をもう一度叩くか、記録 (store/launch-app.log) を確かめてください。"
    exit 1
fi
echo ""
echo "止まっています。資料と設定は消えていません。"
echo "手元から取り除くときは bash uninstall.sh を叩いてください。資料と設定も一緒に消えます。"
echo "もう一度使うときは Cynovela-start.command をダブルクリックしてください。"
exit 0
