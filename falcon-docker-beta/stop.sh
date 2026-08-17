#!/bin/bash
# Cynovela 停止スクリプト (コンテナで動かす形)
#
# entry-unify-20260802 (S-1):
#   この系統はコンテナ (コンテナ) で動く1本道になったため、止める相手もコンテナです。
#   従来ここに在ったホスト直起動用の停止処理 (store/server.pid を読んで kill する) は、
#   止める相手がホストに居なくなったので撤去した。
#
#   消す (rm) ことはしません。止めるだけです。データは名前つきのコンテナの外 (volume) に
#   残るため、もう一度 ./launch.sh を実行すればそのまま続きから使えます。
#
# 使い方: bash stop.sh            設定 (cynovela.yaml の container.name) のコンテナを止める
# 止める相手は設定ファイル1本から決まる。環境変数では受け取らない。
# N-1 連動: 止めるときも、選ばれた実行ファイル (cynovela.yaml の
#   container.engine / engine_command) を使う。podman 決め打ちでは、Docker や
#   自分で指定した実行ファイルで起こしたコンテナを止められない。
#   Docker には `container exists` が無いため、存在の確認は inspect で行う。
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONF_REPO="$SCRIPT_DIR"
. "$SCRIPT_DIR/tools/conf.sh"
NAME="$(conf_get_or container name "$CONF_DEFAULT_CNAME")"

ENG="$(conf_get container engine_command)"
if [ -z "$ENG" ]; then
    ENG="$(conf_get container engine)"
fi
[ -z "$ENG" ] && ENG="podman"
ENG_HEAD="${ENG%% *}"
if ! command -v "$ENG_HEAD" >/dev/null 2>&1 && [ ! -x "$ENG_HEAD" ]; then
    echo "$ENG_HEAD がありません。止める相手を確認できません。"
    exit 0
fi

# $ENG はコマンド列のことがあるため、意図して引用しない (語の分かれをそのまま使う)
if ! $ENG container inspect "$NAME" >/dev/null 2>&1; then
    echo "'$NAME' という名前のコンテナはありません。停止対象なし。"
    exit 0
fi

# 他人のコンテナを止めない。この配布物が作ったものだけを止める。
OWNER="$($ENG container inspect "$NAME" --format '{{index .Config.Labels "org.cynovela.artifact"}}' 2>/dev/null || true)"
if [ "$OWNER" != "cynovela-container" ]; then
    echo "'$NAME' はこの配布物が作ったコンテナではありません。止めずに終わります。"
    echo "そのコンテナを止めたい場合は、ご自身で $ENG stop '$NAME' を実行してください。"
    exit 0
fi

RUNNING="$($ENG container inspect "$NAME" --format '{{.State.Running}}' 2>/dev/null || echo false)"
if [ "$RUNNING" != "true" ]; then
    echo "'$NAME' は既に止まっています。"
    exit 0
fi

echo "Cynovela を止めます (コンテナ: $NAME)..."
$ENG stop "$NAME"
echo "停止完了 (消してはいません。./launch.sh でまた起動できます)"
