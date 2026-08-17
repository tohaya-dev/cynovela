#!/bin/bash
# Cynovela 停止スクリプト
# 記録PID(server.py が書く <保存先>/server.pid)のみ停止する。
# PID 記録が無ければ何もしない。固定ポート/lsof/pkill による無差別 kill は行わない。
# 保存先は cynovela.yaml の paths.data_dir から決まる。環境変数では受け取らない。
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONF_REPO="$SCRIPT_DIR"
. "$SCRIPT_DIR/tools/conf.sh"
DATA_DIR="$(conf_get_or paths data_dir "$SCRIPT_DIR/store")"
case "$DATA_DIR" in ./*) DATA_DIR="$SCRIPT_DIR/${DATA_DIR#./}" ;; esac
PID_FILE="$DATA_DIR/server.pid"
if [ ! -f "$PID_FILE" ]; then
    echo "PIDファイル($PID_FILE)がありません。停止対象なし。"
    exit 0
fi
PID=$(cat "$PID_FILE")
if kill -0 "$PID" 2>/dev/null; then
    # 想定プロセス検証 (server.py 以外なら PID 使い回しの誤爆を防ぎ中止)
    if ! ps -o command= -p "$PID" | grep -q "server.py"; then
        echo "PID $PID は Cynovela ではありません。停止を中止します。"
        exit 0
    fi
    echo "Cynovela を停止します (PID: $PID)..."
    kill "$PID"
    sleep 2
    kill -0 "$PID" 2>/dev/null && kill -9 "$PID"
    echo "停止完了"
else
    echo "PIDファイルが古い可能性があります (PID: $PID)"
fi
rm -f "$PID_FILE"
