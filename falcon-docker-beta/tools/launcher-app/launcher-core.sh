#!/bin/bash
# Cynovela 起動の入口の中身 (DD-CYN-0044 §5-2)
#   Cynovela-start.command / Cynovela-stop.command が呼ぶ。端末からも同じものを叩ける。
#   DD-CYN-0066 F-8: ここに書いてあった「Cynovela をはじめる.app」は DD-CYN-0050 で
#   退けた入口である。いま在るのは 2 つの .command だけなので、名前を実物へ改めた。
#   画面(ダイアログ)側は選ぶだけにし、待つ処理・状態の管理はすべてここで背景に持つ。
#   ∴ 画面が出ている間も、起動を待っている間も、他のアプリの操作を妨げない。
set -u

FORM="container"              # container = コンテナで動かす / host = この Mac に直接入れる

CORE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$CORE_DIR/../.." && pwd)"

# DD-CYN-0053: 決めごとは cynovela.yaml 1本から読む。環境変数では受け取らない。
#   コンテナの名前はここで1度だけ決め、止める・見る・組み立てる のすべてで同じ値を使う。
CONF_REPO="$REPO"
. "$REPO/tools/conf.sh"
DEFPORT="$(conf_get_num server port 8801)"
CNAME="$(conf_get_or container name "$CONF_DEFAULT_CNAME")"
STATE_FILE="$REPO/store/launch-app.state"
LOG="$REPO/store/launch-app.log"
mkdir -p "$REPO/store"

# ---------- コンテナの実行エンジン (実行体) の解決 (DD-CYN-0048) ----------
#   アイコンから起動すると PATH が素の値になり、端末では見つかる podman が見つからない。
#   決める順: ①設定/指定での明示 (在れば探索しない) ②podman → docker の探索 ③画面側で選んでもらう。
#   探索は 受け継いだ PATH → ログインシェル → 決まった保存先 の3段。
#   採った実行体は store/engine-bin/podman の橋渡しに置き、PATH の先頭に足す
#   (下流の組み立て・停止スクリプトは podman の名前で呼ぶため)。
#   launch.sh 側と同一の実装を保つこと。
ENGINE_PATH=""; ENGINE_NAME=""
_engine_find_one() {  # $1=名前 → 絶対パスを出力
    # 自分が置いた橋渡し (store/engine-bin) を候補に拾うと自分自身を呼ぶ輪になるため必ず除く
    local p d _shimdir
    _shimdir="$REPO/store/engine-bin"
    p="$(command -v "$1" 2>/dev/null || true)"
    case "$p" in "$_shimdir"/*) p="" ;; esac
    if [ -z "$p" ]; then
        p="$(/bin/zsh -lc "command -v $1" 2>/dev/null | tail -n 1 || true)"
        case "$p" in "$_shimdir"/*) p="" ;; esac
    fi
    if [ -z "$p" ] || [ ! -x "$p" ]; then
        p=""
        for d in /opt/homebrew/bin /usr/local/bin /opt/podman/bin "$HOME/.local/bin" "/Applications/Docker.app/Contents/Resources/bin"; do
            if [ -x "$d/$1" ]; then p="$d/$1"; break; fi
        done
    fi
    [ -n "$p" ] && printf '%s\n' "$p"
    return 0
}
engine_resolve() {  # 0=使える (ENGINE_PATH/ENGINE_NAME が入る) / 1=見つからない
    local spec cmd
    cmd="$(conf_get container engine_command)"
    if [ -n "$cmd" ]; then
        # 起動に使うコマンドそのものの差し替え (Podman・Docker 以外を使う人の口)。
        # 値をそのまま実行する。動作は約束しない。
        ENGINE_PATH="$cmd"; ENGINE_NAME="(コマンド指定)"
        return 0
    fi
    spec="$(conf_get container engine)"
    if [ -n "$spec" ]; then
        # 明示指定が在れば探索を行わない。見つからなければそのまま「無い」扱い。
        case "$spec" in
            /*) [ -x "$spec" ] && ENGINE_PATH="$spec" ;;
            *)  ENGINE_PATH="$(_engine_find_one "$spec")" ;;
        esac
    else
        # 指定が無いときの既定は Podman だけを探す (決定 24-1)。
        # Docker へ黙って倒れる分岐は撤去した (DD-CYN-0070 N-1・決定 30-2)。
        ENGINE_PATH="$(_engine_find_one podman)"
    fi
    [ -z "$ENGINE_PATH" ] && return 1
    ENGINE_NAME="$(basename "$ENGINE_PATH")"
    # 使う前に1回だけ動作を確かめる (version が返ること)。返らなければ「無い」扱いへ落とす。
    if [ -z "$("$ENGINE_PATH" version 2>/dev/null || true)" ]; then
        ENGINE_PATH=""; ENGINE_NAME=""
        return 1
    fi
    return 0
}
engine_activate() {  # 橋渡しを置き、PATH の先頭に足し、記録へ1行残す
    local bindir="$REPO/store/engine-bin"
    mkdir -p "$bindir"
    if [ "$ENGINE_NAME" = "(コマンド指定)" ]; then
        printf '#!/bin/sh\nexec %s "$@"\n' "$ENGINE_PATH" > "$bindir/podman"
    else
        printf '#!/bin/sh\nexec "%s" "$@"\n' "$ENGINE_PATH" > "$bindir/podman"
    fi
    chmod +x "$bindir/podman"
    case ":$PATH:" in
        *":$bindir:"*) : ;;
        *) if [ "$ENGINE_NAME" = "(コマンド指定)" ]; then
               PATH="$bindir:$PATH"
           else
               # 実行エンジンは補助の実行体を隣から呼ぶため、実行体の親ディレクトリも先頭に足す
               PATH="$bindir:$(dirname "$ENGINE_PATH"):$PATH"
           fi
           export PATH ;;
    esac
    echo "[engine] 使うもの: $ENGINE_NAME ($ENGINE_PATH)" >> "$LOG"
}
if [ "$FORM" = "container" ]; then
    engine_resolve && engine_activate
fi

# ---------- 状態ファイル ----------
state_get() {  # state_get KEY
    [ -f "$STATE_FILE" ] || return 0
    awk -F= -v k="$1" '$1==k{print substr($0, length(k)+2)}' "$STATE_FILE" | tail -n 1
}
state_write() {  # state_write KEY=VALUE ...
    local tmp="$STATE_FILE.tmp.$$" k v line
    : > "$tmp"
    if [ -f "$STATE_FILE" ]; then
        for line in "$@"; do :; done
        while IFS= read -r line; do
            k="${line%%=*}"
            local keep=1 a
            for a in "$@"; do [ "${a%%=*}" = "$k" ] && keep=0; done
            [ "$keep" = 1 ] && printf '%s\n' "$line" >> "$tmp"
        done < "$STATE_FILE"
    fi
    for line in "$@"; do printf '%s\n' "$line" >> "$tmp"; done
    mv "$tmp" "$STATE_FILE"
}

# ---------- 実際に動いているかは形態ごとの実体で見る ----------
is_running() {
    if [ "$FORM" = "container" ]; then
        [ "$(podman inspect "$CNAME" --format '{{.State.Running}}' 2>/dev/null || echo false)" = "true" ]
    else
        # 保存先を移して起動した場合、pid ファイルもそちらへ出る (server.py は
        # 設定 paths.data_dir の下に書く)。状態を見る側も同じ場所を見る。
        local dd pid
        dd="$(state_get DATA_DIR)"
        pid="$(cat "${dd:-$REPO/store}/server.pid" 2>/dev/null || true)"
        [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null
    fi
}

pick_port() {
    local p="$DEFPORT" n=0
    while [ "$n" -lt 50 ]; do
        if ! lsof -nP -iTCP:"$p" -sTCP:LISTEN >/dev/null 2>&1; then echo "$p"; return 0; fi
        p=$((p + 1)); n=$((n + 1))
    done
    echo "$DEFPORT"
}

elapsed_str() {
    local s0 s d
    s0="$(state_get STARTED_AT)"; [ -n "$s0" ] || { echo "0分0秒"; return; }
    s="$(date +%s)"; d=$((s - s0)); [ "$d" -lt 0 ] && d=0
    echo "$((d / 60))分$((d % 60))秒"
}

cmd_status() {
    # 起動中は「立ち上がった」ではなく「開けるようになった」で稼働中に変える。
    # プロセス (pid) は画面が開ける前に出来るため、pid だけで見ると、まだ開けない
    # ものを稼働中と表示してしまう。開けたかどうかは _monitor が HTTP で確かめ、
    # STATE=running を書く。ここではその判定を追い越さない。
    local st port
    st="$(state_get STATE)"; port="$(state_get PORT)"
    if [ "$st" = "starting" ]; then
        local mp; mp="$(state_get MONITOR_PID)"
        if [ -n "$mp" ] && kill -0 "$mp" 2>/dev/null; then
            st="starting"
        elif is_running; then
            st="running"; state_write "STATE=running"
        else
            st="stopped"; state_write "STATE=stopped"
        fi
    elif is_running; then
        st="running"
        state_write "STATE=running"
    else
        st="stopped"
        [ "$(state_get STATE)" = "running" ] && state_write "STATE=stopped"
    fi
    echo "STATE=$st"
    echo "PORT=${port:-$DEFPORT}"
    echo "STARTED_AT=$(state_get STARTED_AT)"
    echo "ELAPSED=$(elapsed_str)"
    echo "MODE=$(state_get MODE)"
    echo "SOURCE=$(state_get SOURCE)"
    echo "EXTERNAL=$(state_get EXTERNAL)"
    echo "DATA_DIR=$(state_get DATA_DIR)"
    echo "LAST=$(tail -n 1 "$LOG" 2>/dev/null | cut -c1-120)"
}

cmd_start() {
    local demo=0 empty=0 mode="full" port="auto" external="allow" data_dir="" browser="auto" fetch=0
    while [ $# -gt 0 ]; do
        case "$1" in
            --demo) demo=1 ;;
            --empty) empty=1 ;;
            --fetch-model) fetch=1 ;;
            --mode) mode="$2"; shift ;;
            --port) port="$2"; shift ;;
            --no-external) external="deny" ;;
            --data-dir) data_dir="$2"; shift ;;
            --no-browser) browser="no" ;;
        esac
        shift
    done
    if is_running; then echo "already-running"; return 3; fi
    [ "$port" = "auto" ] && port="$(pick_port)"

    local src="folders"; [ "$demo" = 1 ] && src="demo"; [ "$empty" = 1 ] && src="empty"
    local args=""
    [ "$demo" = 1 ] && args="$args --demo"
    if [ "$FORM" = "container" ]; then
        args="$args $mode --port $port"
    else
        args="$args --mode $mode --port $port"
    fi
    [ "$external" = "deny" ] && args="$args --local-only"

    : >> "$LOG"
    local lpid
    # DD-CYN-0053: 環境変数では何も渡さない。聞かずに進めることと、コンテナの名前と、
    # 保存先は、いずれも設定ファイル (cynovela.yaml) と指定 (--no-prompt) で伝える。
    # DD-CYN-0053: 背景に投げたものを、この場から切り離す (disown)。
    #   切り離さないと、この入口のプロセスが本体の終わりまで居残る
    #   (アイコンで起動したあと、使い終わっても1本ずつ溜まっていく)。
    ( cd "$REPO" && { nohup ./launch.sh --no-prompt $args >> "$LOG" 2>&1 &
                      echo $! > "$STATE_FILE.lpid"
                      disown %% 2>/dev/null || true; } )
    lpid="$(cat "$STATE_FILE.lpid" 2>/dev/null || true)"; rm -f "$STATE_FILE.lpid"

    state_write "STATE=starting" "PORT=$port" "STARTED_AT=$(date +%s)" \
        "MODE=$mode" "SOURCE=$src" "EXTERNAL=$external" "DATA_DIR=$data_dir" \
        "BROWSER=$browser" "LAUNCH_PID=$lpid"

    nohup "$CORE_DIR/launcher-core.sh" _monitor >> "$LOG" 2>&1 &
    state_write "MONITOR_PID=$!"
    disown %% 2>/dev/null || true
    echo "started PORT=$port"
}

cmd_monitor() {
    local port i code dead=0 lp
    port="$(state_get PORT)"
    for i in $(seq 1 1200); do
        sleep 2
        # 起動の実体 (launch.sh) が死に、動く実体も無いなら、待ち続けない。
        # 一瞬の入れ替わりを失敗と誤らないため、2回続けて確認してから止める。
        lp="$(state_get LAUNCH_PID)"
        if [ -n "$lp" ] && ! kill -0 "$lp" 2>/dev/null && ! is_running; then
            dead=$((dead + 1))
        else
            dead=0
        fi
        if [ "$dead" -ge 2 ]; then
            state_write "STATE=stopped"
            if tail -n 20 "$LOG" 2>/dev/null | grep -q 'ダウンロード元に繋がりませんでした'; then
                osascript -e 'display notification "ダウンロード元に繋がりませんでした。記録: store/launch-app.log" with title "Cynovela"' >/dev/null 2>&1 || true
            else
                osascript -e 'display notification "時間内に用意ができませんでした。記録: store/launch-app.log" with title "Cynovela"' >/dev/null 2>&1 || true
            fi
            exit 0
        fi
        code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "http://localhost:$port/" 2>/dev/null || true)"
        if [ "$code" = "200" ]; then
            state_write "STATE=running"
            if [ "$(state_get BROWSER)" = "auto" ]; then
                open "http://localhost:$port" || true
            fi
            osascript -e 'display notification "用意ができました。ブラウザを開きます。" with title "Cynovela"' >/dev/null 2>&1 || true
            exit 0
        fi
        if [ "$(state_get STATE)" != "starting" ]; then exit 0; fi
    done
    state_write "STATE=stopped"
    osascript -e 'display notification "時間内に用意ができませんでした。記録: store/launch-app.log" with title "Cynovela"' >/dev/null 2>&1 || true
}

cmd_abort() {
    local mp lp
    mp="$(state_get MONITOR_PID)"; lp="$(state_get LAUNCH_PID)"
    state_write "STATE=stopped"
    [ -n "$mp" ] && kill "$mp" 2>/dev/null
    # 中断も stop.sh に任せる (この配布物が作ったものかを stop.sh がマーカーで確かめる)
    ( cd "$REPO" && bash stop.sh >> "$LOG" 2>&1 ) || true
    [ -n "$lp" ] && kill "$lp" 2>/dev/null
    echo "aborted"
}

cmd_stop() {
    local mp; mp="$(state_get MONITOR_PID)"
    [ -n "$mp" ] && kill "$mp" 2>/dev/null
    # 止める相手も設定ファイルから決まる (stop.sh が同じ1本を読む)
    ( cd "$REPO" && bash stop.sh >> "$LOG" 2>&1 ) || true
    state_write "STATE=stopped"
    echo "stopped"
}

cmd_restart() {
    # 前回と同じ構成で立て直す。ポート番号も引き継ぐ (引き継がないと既定へ落ち、
    # 「アドレスをコピー」で配ったアドレスが再起動で変わってしまう)。
    local mode src ext ddir browser port args=""
    mode="$(state_get MODE)"; src="$(state_get SOURCE)"; ext="$(state_get EXTERNAL)"
    ddir="$(state_get DATA_DIR)"; browser="$(state_get BROWSER)"; port="$(state_get PORT)"
    cmd_stop >/dev/null
    sleep 2
    [ "$src" = "demo" ] && args="$args --demo"
    [ "$src" = "empty" ] && args="$args --empty"
    [ -n "$mode" ] && args="$args --mode $mode"
    [ -n "$port" ] && args="$args --port $port"
    [ "$ext" = "deny" ] && args="$args --no-external"
    [ -n "$ddir" ] && args="$args --data-dir $ddir"
    [ "$browser" = "no" ] && args="$args --no-browser"
    cmd_start $args
}

cmd_address() {
    local port; port="$(state_get PORT)"; [ -n "$port" ] || port="$DEFPORT"
    echo "http://localhost:$port"
}

cmd_list_roots() { ( cd "$REPO" && ./launch.sh --list 2>&1 ); }
cmd_root_names() { cmd_list_roots | grep -o '"name": "[^"]*"' | cut -d'"' -f4; }
cmd_add_root()   { ( cd "$REPO" && ./launch.sh --add-path "$1" 2>&1 ); }
cmd_remove_root(){ ( cd "$REPO" && ./launch.sh --remove "$1" 2>&1 ); }

# 実行エンジンの状態を1行で返す (DD-CYN-0048)。画面 (launcher.applescript) が読む。
#   ENGINE=ok NAME=<名前> / ENGINE=not-running NAME=<名前> / ENGINE=not-found
#   "engine set <パス>" は「場所を選ぶ」で指された実行ファイルを設定へ覚える。
cmd_engine() {
    if [ "${1:-}" = "set" ]; then
        shift
        # 設定は cynovela.yaml の container.engine に覚える (保存先を2本に分けない)
        conf_set container engine "$1" || { echo "設定を書けませんでした"; return 1; }
        echo "saved container.engine=$1"
        return 0
    fi
    if ! engine_resolve; then
        echo "ENGINE=not-found"
        return 0
    fi
    engine_activate
    if podman info >/dev/null 2>&1; then
        echo "ENGINE=ok NAME=$ENGINE_NAME"
        return 0
    fi
    if [ "$ENGINE_NAME" = "podman" ]; then
        # 従来どおり、一度だけ実行エンジンの仮想機械を起こしてみる (起こせればそのまま進む)
        podman machine start >> "$LOG" 2>&1 || true
        if podman info >/dev/null 2>&1; then
            echo "ENGINE=ok NAME=$ENGINE_NAME"
            return 0
        fi
    fi
    echo "ENGINE=not-running NAME=$ENGINE_NAME"
}

cmd_check() {
    ( cd "$REPO" && ./launch.sh --check >> "$LOG" 2>&1 ) || true
    cat "$REPO/store/env-check.txt" 2>/dev/null || echo "(検査の結果ファイルがありません)"
}

cmd_doc() {  # cmd_doc welcome|about|env|cleanup|notice
    local f mark
    case "$1" in
        notice) f="$REPO/NOTICE.md"; mark="notice" ;;
        *)      f="$REPO/README.md"; mark="$1" ;;
    esac
    awk -v m="$mark" '
        $0 ~ "cynovela:" m ":start" {on=1; next}
        $0 ~ "cynovela:" m ":end"   {on=0}
        on {gsub(/\*\*/, ""); print}
    ' "$f"
}

case "${1:-}" in
    status)      cmd_status ;;
    engine)      shift; cmd_engine "$@" ;;
    start)       shift; cmd_start "$@" ;;
    _monitor)    cmd_monitor ;;
    abort)       cmd_abort ;;
    stop)        cmd_stop ;;
    restart)     cmd_restart ;;
    address)     cmd_address ;;
    open)        open "$(cmd_address)" ;;
    list-roots)  cmd_list_roots ;;
    root-names)  cmd_root_names ;;
    add-root)    shift; cmd_add_root "$1" ;;
    remove-root) shift; cmd_remove_root "$1" ;;
    check)       cmd_check ;;
    doc)         shift; cmd_doc "$1" ;;
    elapsed)     elapsed_str ;;
    *)
        echo "使い方: launcher-core.sh status|start|stop|abort|restart|address|open|list-roots|root-names|add-root|remove-root|check|doc|elapsed" >&2
        exit 2
        ;;
esac
