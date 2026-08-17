#!/bin/bash
# Cynovela を止める入口 (DD-CYN-0070 N-7)
#   ダブルクリックするとターミナルが開き、止め方と結果をこの画面に出します。
#   止めるだけです。資料と設定は消えません。
set -u
cd "$(dirname "$0")"

echo "止め方は次のとおりです。この場で同じことを行います。"
echo "  bash stop.sh"
echo ""
bash stop.sh

# 本当に止まったかを実測して出す (この配布物の保存先から起動した本体だけを見る)
_left=""
for _p in $(pgrep -f " server\.py" 2>/dev/null); do
    _cwd="$(lsof -a -p "$_p" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p' | head -1)"
    [ "$_cwd" = "$(pwd)" ] && _left="$_left $_p"
done
if [ -n "$_left" ]; then
    echo ""
    echo "まだ動いています (PID$_left)。bash stop.sh をもう一度叩くか、記録 (store/launch-app.log) を確かめてください。"
    exit 1
fi
echo ""
echo "止まっています。資料と設定は消えていません。"
echo "手元から取り除くときは bash uninstall.sh を叩いてください。資料と設定も一緒に消えます。"
echo "もう一度使うときは Cynovela-start.command をダブルクリックしてください。"
exit 0
