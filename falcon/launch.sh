#!/bin/bash
# ============================================================
#  Cynovela 入口の包み (M-5・追記274 274-2/274-3・決定 29-3)
#
#  受け取り手がターミナルから叩く入口はこの1本です。起動の本体は
#  tools/launch-body.sh にそのまま在り、この包みは確かめて・伝えて・
#  切り離して呼ぶだけです。本体を置き換えていません。
#
#  使い方:
#    ./launch.sh            本番 (中身が空のデータベース) で起動します
#    ./launch.sh --demo     同梱のダミー資料が載った状態で起動します
#    ./launch.sh --follow   起動後もこのターミナルに出力を流し続けます (作る側向け)
#    ./launch.sh --pro      細かい指定の一覧を出します (起動の種類は増えません)
#  止め方: bash stop.sh
#
#  この包みがすること (順・):
#    1. いま動いている Cynovela を全数調べて表示し、止める / 起こし直す /
#       つなぐ / やめる を選ばせる (N-6)
#    2. Podman・Docker・自分で指定 を同列に並べて選ばせる (N-1・決定 30-1〜30-3)。
#       見つけたものへ黙って進む形は全廃した (決定 30-2)
#    3. これから何が起きるかを出して Y/N/C で確かめる (N-3)
#    4. 記録の保存先を画面へ出し、本体をターミナルから切り離して起動する
#       (このターミナルを閉じても本体は落ちません)
#    5. 立ち上がりを待ち、開く場所と止め方を出して終わる (N-7)
#       起動に失敗したときは、理由と記録の場所を出して終わる (画面はそのまま残る)
# ============================================================
set -u
WRAP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BODY="$WRAP_DIR/tools/launch-body.sh"
LOG="$WRAP_DIR/store/launch-app.log"

# ── 透過の道 ──────────────────────────────────────────────
# 次のものは本体へそのまま渡す (この包みは何も足さず・何も変えない):
#   1. 凍結済みの操作手順 (Cynovela-start.command → launcher-core.sh) が付ける --no-prompt
#   2. 端末が繋がっていない呼び出し (聞く・待つ・流すの扱いができない)
#   3. 起動でない用件 (--list / --add / --check / --setup 単独 など)。包みが受け持つのは
#      起動の形 (引数なし=本番 / --demo=デモ) と、包みだけの指定 (--follow / --pro) である。
_PASSTHRU=0
_expect_val=""
for _a in "$@"; do
    if [ -n "$_expect_val" ]; then _expect_val=""; continue; fi
    case "$_a" in
        --no-prompt) _PASSTHRU=1 ;;
        --demo|--follow|--pro|--local-only|--lan) : ;;
        --port) _expect_val=1 ;;
        *) _PASSTHRU=1 ;;
    esac
done
if [ "$_PASSTHRU" = "1" ] || [ ! -t 0 ] || [ ! -t 1 ]; then
    exec bash "$BODY" "$@"
fi

# ── 包みだけが読む指定 (--follow / --pro) を、本体へ渡す指定と分ける ─────
FOLLOW=0
PASS=()
for _a in "$@"; do
    case "$_a" in
        --follow) FOLLOW=1 ;;
        --pro)
            echo "細かい指定の一覧です。起動の種類は 引数なし=本番 / --demo=デモ の2通りのまま増えません (決定 7-1)。"
            echo ""
            bash "$BODY" --help-all
            exit 0
            ;;
        *) PASS+=("$_a") ;;
    esac
done

# ── 0. いま動いている Cynovela を全数調べて表示する (N-6) ──
#   調べる先はコンテナ (動いているものと止まっているものの両方)。この配布物が
#   作ったものだけに絞らない (Cynovela のマーカー org.cynovela.artifact で見る)。
#   受け取り手が選ぶまで、止めない・起こさない・作らない。
#   コンテナを消す操作 (rm) は、この道のどこにも置かない。
FOUND=""            # 1行1件: engine|name|state|port
ACTION="new"        # new / stop_new / restart
STOP_TARGETS=""     # 「止めて、新しく起こす」が選ばれたときの止める対象
RESTART_ENG=""; RESTART_NAME=""; RESTART_PORT=""
_collect_running() {
    FOUND=""
    local _e _line _n _s _p _port
    for _e in podman docker; do
        command -v "$_e" >/dev/null 2>&1 || continue
        while IFS= read -r _line; do
            [ -n "$_line" ] || continue
            _n="${_line%%|*}"; _line="${_line#*|}"
            _s="${_line%%|*}"; _p="${_line#*|}"
            _port="$(printf '%s' "$_p" | sed -n 's/.*:\([0-9][0-9]*\)->.*/\1/p' | head -1)"
            FOUND="${FOUND}${_e}|${_n}|${_s}|${_port:-8801}
"
        done <<EOF_PS
$("$_e" ps -a --filter label=org.cynovela.artifact=cynovela-container --format '{{.Names}}|{{.State}}|{{.Ports}}' 2>/dev/null)
EOF_PS
    done
}
_found_each() {  # $1=running|stopped → 「engine|name|port」を1行ずつ出す
    printf '%s' "$FOUND" | while IFS='|' read -r _e _n _s _p; do
        [ -n "$_n" ] || continue
        case "$1" in
            running) [ "$_s" = "running" ] && printf '%s|%s|%s\n' "$_e" "$_n" "$_p" ;;
            stopped) [ "$_s" != "running" ] && printf '%s|%s|%s\n' "$_e" "$_n" "$_p" ;;
        esac
    done
}
_stop_listed_running() {  # 表示済みの動いているものを止める (止めるだけ。rm はしない)
    local _e _n _p
    while IFS='|' read -r _e _n _p; do
        [ -n "$_n" ] || continue
        echo "止めています: $_n ($_e stop $_n)"
        "$_e" stop "$_n" >/dev/null 2>&1 || echo "  → 止められませんでした: $_n"
    done <<EOF_ST
$(_found_each running)
EOF_ST
}
_verify_stopped() {  # 止まったことを実測して画面へ出す
    local _e _n _p _st
    while IFS='|' read -r _e _n _p; do
        [ -n "$_n" ] || continue
        _st="$("$_e" container inspect "$_n" --format '{{.State.Running}}' 2>/dev/null || echo false)"
        if [ "$_st" = "true" ]; then
            echo "$_n : まだ動いています。$_e stop $_n をもう一度叩くか、記録 ($LOG) を確かめてください。"
        else
            echo "$_n : 止まりました。資料と設定は消えていません。"
        fi
    done <<EOF_VF
$(_found_each running)
EOF_VF
}
_confirm_simple() {  # $1=使うもの $2=作られるものの行 $3=初回の行 → 0=Y / 1=N (C/EOF は終了)
    local ans
    while true; do
        echo ""
        echo "これから行うことを確かめてください。"
        echo "  使うもの      : $1"
        echo "  作られるもの   : $2"
        echo "  残る場所      : このフォルダの中の store/ と、名前つきの保存領域（${VOLPREFIX}-db ほか）"
        echo "  消し方        : ここでは何も消しません（手元から取り除く道は bash uninstall.sh です）"
        echo "  外から        : このコンテナを作ったときの決めがそのまま続きます"
        echo "  初回          : $3"
        echo "進めますか。"
        echo "  Y) はい、進めます"
        echo "  N) いいえ、選び直します"
        echo "  C) キャンセル（何もせずに終わります）"
        printf '[Y/N/C]: '
        if ! IFS= read -r ans; then
            echo ""
            echo "入力が閉じたため、何もせずに終わります。"
            exit 0
        fi
        case "$ans" in
            Y|y) return 0 ;;
            N|n) return 1 ;;
            C|c) echo "キャンセルしました。何もせずに終わります。"; exit 0 ;;
            *) echo "  → Y か N か C を入れてください。" ;;
        esac
    done
}
running_menu() {
    local ans _cnt_r _cnt_s _first_r _first_s
    _collect_running
    echo ""
    echo "先に、いま動いているものを調べました。"
    if [ -z "$FOUND" ]; then
        echo "  動いているものは 0個 でした。"
        echo "このまま進みます。"
        return 0
    fi
    printf '%s' "$FOUND" | while IFS='|' read -r _e _n _s _p; do
        [ -n "$_n" ] || continue
        if [ "$_s" = "running" ]; then
            echo "  $_n  : 動いています（待ち受け ${_p}・${_e}）"
        else
            echo "  $_n  : 止まっています（資料と設定は残っています・${_e}）"
        fi
    done
    _cnt_r="$(_found_each running | /usr/bin/grep -c . || true)"
    _cnt_s="$(_found_each stopped | /usr/bin/grep -c . || true)"
    [ "${_cnt_r:-0}" -gt 0 ] && echo "このまま新しく起こすと、同じものが二重に立ち上がります。"
    while true; do
        echo "どうしますか。"
        echo "  1) 動いているものを止めて、新しく起こす"
        echo "     止めるだけです。資料と設定は消えません。"
        echo "  2) 止まっているものを、そのまま起こし直す"
        echo "     作り直しません。資料と設定はそのまま使えます。"
        echo "  3) 動いているものへ、そのままつなぐ"
        echo "     画面のアドレスを出します。新しくは起こしません。"
        echo "  4) 動いているものを止めて、終わる"
        echo "  5) 何もせずに終わる"
        printf '番号を入れてください [1/2/3/4/5]: '
        if ! IFS= read -r ans; then
            echo ""
            echo "入力が閉じたため、何もせずに終わります。"
            exit 0
        fi
        case "$ans" in
            1)
                if [ "${_cnt_r:-0}" -eq 0 ]; then echo "  → 動いているものは 0個 です。"; continue; fi
                ACTION="stop_new"
                STOP_TARGETS="$(_found_each running | while IFS='|' read -r _e _n _p; do printf '%s ' "$_n"; done)"
                return 0
                ;;
            2)
                if [ "${_cnt_s:-0}" -eq 0 ]; then echo "  → 止まっているものは 0個 です。"; continue; fi
                _first_s="$(_found_each stopped | head -1)"
                RESTART_ENG="${_first_s%%|*}"
                _first_s="${_first_s#*|}"
                RESTART_NAME="${_first_s%%|*}"
                RESTART_PORT="${_first_s#*|}"
                ACTION="restart"
                return 0
                ;;
            3)
                if [ "${_cnt_r:-0}" -eq 0 ]; then echo "  → 動いているものは 0個 です。"; continue; fi
                _first_r="$(_found_each running | head -1)"
                _first_r="${_first_r#*|}"
                echo ""
                echo "開くところ : http://127.0.0.1:${_first_r#*|}/"
                echo "新しくは起こしていません。何も止めていません。"
                exit 0
                ;;
            4)
                if [ "${_cnt_r:-0}" -eq 0 ]; then echo "  → 動いているものは 0個 です。"; continue; fi
                if _confirm_simple "いま動かしているもの" "ありません（止めるもの: $(_found_each running | while IFS='|' read -r _e _n _p; do printf '%s ' "$_n"; done)。止めるだけです。資料と設定は消えません）" "待ちはありません"; then
                    _stop_listed_running
                    _verify_stopped
                    exit 0
                fi
                continue
                ;;
            5)
                echo "何もせずに終わります。"
                exit 0
                ;;
            *) echo "  → 番号を入れてください。" ;;
        esac
    done
}

# ── 1. Podman・Docker・自分で指定 を同列に並べて選ばせる (N-1) ──
#   決定 30-1: Podman は必須ではない。決定 30-2: 見つけたものへ黙って進む形を禁じる。
#   決定 30-3: どちらを見つけたときも、もう一方と「自分で指定する」を選べる。
#   自動で探すのは Podman と Docker の2つだけ (決定 19-3)。
#   選ばれた結果は cynovela.yaml (container.engine / engine_command) へ覚え、
#   本体 (tools/launch-body.sh) は同じ1本を読んで同じものを使う。
CONF_REPO="$WRAP_DIR"
. "$WRAP_DIR/tools/conf.sh"
CNAME="$(conf_get_or container name "$CONF_DEFAULT_CNAME")"
VOLPREFIX="$(conf_get_or container volume_prefix "$CONF_DEFAULT_VOLPREFIX")"

# ── 0-A. 埋め込みを動かす外部の推論サーバ (MAS) を用意するフェーズ () ──
#   本体を置き換えず、ここへ被せる形で読み込む (決定 29-3)。
#   3択 (Podman / Docker / 自分で指定) より前に mas_phase_ask を呼ぶ。
#   理由: 外部の推論サーバが立たないままコンテナを起こすと、埋め込みはコンテナの中の CPU へ
#         退避する。退避したあとで実行ファイルを選び直しても、その取り込みには
#         効かない。∴ 外部の推論サーバはコンテナより先に立てる。
. "$WRAP_DIR/tools/mas-phase.sh"

_ver_of() {  # $1=実行ファイル名 → 版の数字だけを出す
    "$1" --version 2>/dev/null | /usr/bin/grep -oE '[0-9]+(\.[0-9]+)+' | head -1
}

ENGINE_SEL=""     # podman / docker / custom
ENGINE_DISP=""    # 画面に出す名前
CUSTOM_EXEC=""
CUSTOM_CMD=""

choose_engine() {
    local have_p=0 have_d=0 vp="" vd="" ans
    command -v podman >/dev/null 2>&1 && { have_p=1; vp="$(_ver_of podman)"; }
    command -v docker >/dev/null 2>&1 && { have_d=1; vd="$(_ver_of docker)"; }
    while true; do
        echo ""
        echo "使えるものを調べました。"
        if [ "$have_p" = "1" ]; then
            echo "  Podman     : 見つかりました（${vp:-版は読めませんでした}）"
        else
            echo "  Podman     : 見つかりませんでした"
        fi
        if [ "$have_d" = "1" ]; then
            echo "  Docker     : 見つかりました（${vd:-版は読めませんでした}）"
        else
            echo "  Docker     : 見つかりませんでした"
        fi
        echo "  自分で指定  : いつでも選べます"
        echo "どれで動かしますか。"
        echo "  1) Podman を使う"
        echo "     当方が動作を確かめているのは、これだけです。"
        echo "  2) Docker を使う"
        echo "     当方では確かめていません。ご自身での調整が要ります。"
        echo "  3) 自分で指定する"
        echo "     使う実行ファイルと、起動に使うコマンドを入力します。"
        echo "     当方では確かめていません。ご自身での調整が要ります。"
        echo "  4) やめる"
        printf '番号を入れてください [1/2/3/4]: '
        if ! IFS= read -r ans; then
            echo ""
            echo "入力が閉じたため、やめました。何も作っていません。"
            exit 0
        fi
        case "$ans" in
            1)
                if [ "$have_p" = "1" ]; then ENGINE_SEL="podman"; ENGINE_DISP="Podman"; return 0; fi
                echo ""
                echo "Podman が見つかりませんでした。"
                echo "  入れ方: https://podman.io/ から Podman Desktop を入れてください"
                echo "  入れ終えたら、もう一度このファイルを押してください"
                echo "このターミナルは開いたままにしてあります。"
                exit 1
                ;;
            2)
                if [ "$have_d" = "1" ]; then ENGINE_SEL="docker"; ENGINE_DISP="Docker"; return 0; fi
                echo ""
                echo "Docker が見つかりませんでした。"
                echo "  入れ方: https://www.docker.com/ から Docker Desktop を入れてください"
                echo "  入れ終えたら、もう一度このファイルを押してください"
                echo "このターミナルは開いたままにしてあります。"
                exit 1
                ;;
            3)
                printf '使う実行ファイルの場所を入れてください: '
                if ! IFS= read -r CUSTOM_EXEC; then
                    echo ""
                    echo "入力が閉じたため、やめました。何も作っていません。"
                    exit 0
                fi
                printf '起動に使うコマンドを入れてください (実行ファイルだけで良ければ空のまま Enter): '
                if ! IFS= read -r CUSTOM_CMD; then
                    echo ""
                    echo "入力が閉じたため、やめました。何も作っていません。"
                    exit 0
                fi
                if [ -z "$CUSTOM_EXEC" ] && [ -z "$CUSTOM_CMD" ]; then
                    continue
                fi
                ENGINE_SEL="custom"
                if [ -n "$CUSTOM_CMD" ]; then ENGINE_DISP="$CUSTOM_CMD"; else ENGINE_DISP="$CUSTOM_EXEC"; fi
                return 0
                ;;
            4)
                echo "やめました。何も作っていません。"
                exit 0
                ;;
            *) echo "  → 番号を入れてください。" ;;
        esac
    done
}

apply_engine_choice() {
    case "$ENGINE_SEL" in
        podman)  conf_set container engine "podman" && conf_set container engine_command "" ;;
        docker)  conf_set container engine "docker" && conf_set container engine_command "" ;;
        custom)  conf_set container engine "$CUSTOM_EXEC" && conf_set container engine_command "$CUSTOM_CMD" ;;
    esac || { echo "設定 (cynovela.yaml) を書けませんでした。"; exit 1; }
}

# ── 2. 進める前の確認 (N-3) ─────────────────────────
#   選んだ直後に、これから何が起きるかを1画面で出し、Y/N/C で選ばせる。
#   Y=進める / N=選び直す (N-1 の画面へ戻る) / C と EOF=何もせずに終わる。
#   N・C・EOF では何も書かない・何も作らない (設定への書き込みも Y の後だけ)。
CONFIRM=""
_delete_cmd() {
    local _e
    case "$ENGINE_SEL" in
        podman) _e="podman" ;;
        docker) _e="docker" ;;
        *)      _e="$ENGINE_DISP" ;;
    esac
    echo "$_e rm $CNAME と $_e volume rm ${VOLPREFIX}-db ${VOLPREFIX}-vec ${VOLPREFIX}-bk"
}
confirm_launch() {
    local ans
    while true; do
        echo ""
        echo "これから行うことを確かめてください。"
        echo "  使うもの      : $ENGINE_DISP"
        echo "  外部の推論サーバ (埋め込み): $MAS_STATE"
        if [ -n "$STOP_TARGETS" ]; then
            echo "  作られるもの   : コンテナ 1つ（名前: ${CNAME}。先に $STOP_TARGETS を止めます。止めるだけです）"
        else
            echo "  作られるもの   : コンテナ 1つ（名前: ${CNAME}）"
        fi
        echo "  残る場所      : このフォルダの中の store/ と、名前つきの保存領域（${VOLPREFIX}-db ほか）"
        echo "  消し方        : bash uninstall.sh"
        echo "                  何を取り除くかを画面に出し、2回お尋ねしてから一括で行います"
        echo "                  読み込んだ資料と設定も一緒に消えます"
        echo "  外から        : 同じネットワークの別の Mac から開けます"
        echo "                  この Mac だけに限りたいときは --local-only を付けてください"
        echo "  初回          : コンテナの組み立てに時間がかかります"
        echo "進めますか。"
        echo "  Y) はい、進めます"
        echo "  N) いいえ、選び直します"
        echo "  C) キャンセル（何もせずに終わります）"
        printf '[Y/N/C]: '
        if ! IFS= read -r ans; then
            echo ""
            echo "入力が閉じたため、何もせずに終わります。"
            exit 0
        fi
        case "$ans" in
            Y|y) CONFIRM="yes"; return 0 ;;
            N|n) CONFIRM="no";  return 0 ;;
            C|c) echo "キャンセルしました。何もせずに終わります。"; exit 0 ;;
            *) echo "  → Y か N か C を入れてください。" ;;
        esac
    done
}

# ── 実行の順 (N-6 → N-1 → N-3) ──────────────────────────────
running_menu
if [ "$ACTION" = "restart" ]; then
    if _confirm_simple "$RESTART_ENG" "ありません（起こし直すもの: ${RESTART_NAME}。作り直しません。資料と設定はそのまま使えます）" "組み立ては行いません"; then
        # 起こし直す道でも、コンテナより先に外部の推論サーバを用意する ()。
        # 新しく起こす道だけに置くと、この道が外部の推論サーバを素通りしてしまう。
        mas_phase_ask
        if ! mas_phase_apply; then
            exit 1
        fi
        mkdir -p "$WRAP_DIR/store"
        echo "起こし直しています: $RESTART_ENG start $RESTART_NAME"
        if ! "$RESTART_ENG" start "$RESTART_NAME" >/dev/null 2>&1; then
            echo "起こし直せませんでした。中身を確かめる: $RESTART_ENG logs $RESTART_NAME"
            exit 1
        fi
        i=0
        while [ "$i" -lt 90 ]; do
            if curl -s -o /dev/null --max-time 2 "http://127.0.0.1:${RESTART_PORT}/" 2>/dev/null; then
                echo ""
                echo "立ち上がりました。開く場所: http://127.0.0.1:${RESTART_PORT}/"
                echo "作り直していません。資料と設定はそのまま使えます。"
                exit 0
            fi
            sleep 2
            i=$((i + 1))
        done
        echo "時間内に開けるようになりませんでした。中身を確かめる: $RESTART_ENG logs $RESTART_NAME"
        exit 1
    fi
    # N (選び直し) → 新しく起こす道へ進む
    ACTION="new"
fi

# 外部の推論サーバ (MAS) を用意するフェーズ。3択より前に置く ()。
# ここでは調べて選ばせるだけで、まだ何も作らない。
mas_phase_ask

while true; do
    choose_engine
    confirm_launch
    [ "$CONFIRM" = "yes" ] && break
done
apply_engine_choice

# 選ばれた道で外部の推論サーバを用意し、立てて、device を確かめる。
# 立てられなかったときは黙ってコンテナを起こさず、何が足りないかを出して止まる。
if ! mas_phase_apply; then
    exit 1
fi

# Podman を選んだとき、仮想機械が止まっていれば一度だけ起こしてみる
# (従来の操作手順 (launcher-core.sh cmd_engine) と同じ扱い。起こせなければ本体の点検が知らせる)
if [ "$ENGINE_SEL" = "podman" ] && ! podman info >/dev/null 2>&1; then
    echo "Podman の仮想機械を起こしています (podman machine start)"
    podman machine start >/dev/null 2>&1 || true
fi

# N-6 で「止めて、新しく起こす」が選ばれていたら、確認 (Y) の後にここで止める。
# 止めるだけであり、消さない。止まったことを実測して画面へ出す。
if [ "$ACTION" = "stop_new" ]; then
    _stop_listed_running
    _verify_stopped
fi

# ── 2. 記録の保存先を画面へ出す (ターミナルを閉じる前に必ず) ──────────
mkdir -p "$WRAP_DIR/store"
echo "記録はこのファイルへ書きます: $LOG"

# ── 3. 本体をターミナルから切り離して起動する ───────────────────────
: >> "$LOG"
LOG_MARK="$(wc -c < "$LOG" | tr -d ' ')"
nohup bash "$BODY" --no-prompt ${PASS[@]+"${PASS[@]}"} >> "$LOG" 2>&1 &
BODY_PID=$!
disown %% 2>/dev/null || true
echo "起動しています (本体はこのターミナルから切り離して動かします。初回は組み立てに5〜20分かかります)"

# ── 4. 立ち上がりを待つ ─────────────────────────────────────
_port_from_log() {
    tail -c "+$((LOG_MARK + 1))" "$LOG" 2>/dev/null \
        | /usr/bin/grep -oE 'http://(0\.0\.0\.0|127\.0\.0\.1|localhost):[0-9]+|PORT=[0-9]+' \
        | tail -n 1 | /usr/bin/grep -oE '[0-9]+$'
}
PORT=""
i=0
while [ "$i" -lt 900 ]; do
    sleep 2
    [ -z "$PORT" ] && PORT="$(_port_from_log || true)"
    if [ -n "$PORT" ] && curl -s -o /dev/null --max-time 2 "http://localhost:$PORT/api/health" 2>/dev/null; then
        # N-7: 止め方と消し方を、起動が終わったここで必ず画面へ出す。
        case "$ENGINE_SEL" in
            podman) _stopcmd="podman stop $CNAME" ;;
            docker) _stopcmd="docker stop $CNAME" ;;
            *)      _stopcmd="$ENGINE_DISP stop $CNAME" ;;
        esac
        echo ""
        echo "立ち上がりました。"
        echo "  開くところ : http://127.0.0.1:$PORT/"
        echo "  記録       : $LOG"
        echo "止めるときは、次のように叩いてください。"
        echo "  $_stopcmd   （bash stop.sh でも同じものが止まります）"
        echo "  止めるだけです。資料と設定は消えません。"
        echo "手元から取り除くときは、次のように叩いてください。"
        echo "  bash uninstall.sh"
        echo "  何を取り除くかを画面に出し、2回お尋ねしてから一括で行います。"
        echo "  読み込んだ資料と設定も一緒に消えます。"
        echo "このターミナルは閉じて構いません。本体は動き続けます。"
        if [ "$FOLLOW" = "1" ]; then
            echo "--follow が指定されたので、出力を流し続けます (やめるときは Ctrl+C。本体は止まりません)。"
            exec tail -f "$LOG"
        fi
        exit 0
    fi
    if ! kill -0 "$BODY_PID" 2>/dev/null && { [ -z "$PORT" ] || ! curl -s -o /dev/null --max-time 2 "http://localhost:$PORT/api/health" 2>/dev/null; }; then
        echo ""
        echo "起動できませんでした。本体からの知らせは次のとおりです:"
        echo "--------------------------------------------------------------"
        tail -c "+$((LOG_MARK + 1))" "$LOG" 2>/dev/null | sed '/^[[:space:]]*$/d' | tail -n 40
        echo "--------------------------------------------------------------"
        echo "記録の全文: $LOG"
        exit 1
    fi
    i=$((i + 1))
done
echo "時間内に用意ができませんでした。記録: $LOG"
exit 1
