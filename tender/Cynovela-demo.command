#!/bin/bash
# Cynovela を同梱のサンプル資料で試す入口 (demo-access-20260901)
#   ダブルクリックするとターミナルが開き、--demo を付けて起動します。
#   同梱のサンプル資料 (dummy-corpus/) は初回起動時に自動で取り込まれます。
#   起動の理屈は ./launch.sh (包み) と tools/launch-body.sh (本体) に在り、
#   このファイルは同じフォルダへ移動して --demo 付きで包みを呼ぶだけです。
#   引数なし＝本番で起動するには Cynovela-start.command を使ってください。
#   止めるときは Cynovela-stop.command をダブルクリックしてください。
set -u
cd "$(dirname "$0")"
exec ./launch.sh --demo "$@"
