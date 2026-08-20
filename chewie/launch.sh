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
#    1. いま動いている Cynovela を全数調べて表示し、止める / つなぐ / やめる を
#       選ばせる (N-6)
#    2. conda・Python・自分で指定 を同列に並べて選ばせる (N-1・決定 14-1〜14-5)。
#       見つけたものへ黙って進む形にしない (決定 30-2 と同じ考え方)
#    3. これから何が起きるかを出して Y/N/C で確かめる (N-3)
#    4. 環境がまだ無ければ作り (本体の --setup を呼ぶ)、記録の保存先を出して、
#       本体をターミナルから切り離して起動する (このターミナルを閉じても本体は落ちません)
#    5. 立ち上がりを待ち、開く場所と止め方を出して終わる (N-7)
#       起動に失敗したときは、理由と記録の場所を出して終わる (画面はそのまま残る)
# ============================================================
set -u
WRAP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BODY="$WRAP_DIR/tools/launch-body.sh"
LOG="$WRAP_DIR/store/launch-app.log"
SHARED_ENV="cynovela"
DIST_ENV="cynovela-dist"

# ── A-3 (DD-CYN-0142 §5-C): 配布物に付いた印 (拡張属性) を自分で全部落とす ──
#   com.apple.quarantine を含め、種類を狙わず全部落とす。対象はこの配布物の中だけ。
#   部品を入れる処理 (--setup の pip) より前 = この入口の先頭で行う。
#   落とせないもの (非 ASCII 名で OS 側が失敗する等) は名前を出して先へ進む。1件で止めない。
_drop_marks() {
    [ -x /usr/bin/xattr ] || return 0
    local _err
    _err="$(/usr/bin/xattr -rc "$WRAP_DIR" 2>&1 >/dev/null | head -20 || true)"
    if [ -n "$_err" ]; then
        echo "注意: 次の印 (拡張属性) は落とせませんでした。そのまま起動を続けます:"
        printf '%s\n' "$_err" | sed 's/^/    /'
    fi
}

# ── A-4 (DD-CYN-0142 §5-D): 置き場所がクラウド同期の下かを、起動の前に判定して伝える ──
#   止めるのではなく、何が起きるかと逃がし方を伝えたうえで進む。
_warn_if_cloud_synced() {
    local _hit=""
    case "$WRAP_DIR" in
        *"/Library/Mobile Documents"*)      _hit="iCloud Drive" ;;
        *"/Library/CloudStorage"*)          _hit="クラウド同期 (CloudStorage 配下)" ;;
        *"/Dropbox/"*|*"/Dropbox")          _hit="Dropbox" ;;
        *"/OneDrive"*)                      _hit="OneDrive" ;;
        *"/Google Drive"*|*"/GoogleDrive"*) _hit="Google Drive" ;;
    esac
    [ -n "$_hit" ] || return 0
    echo "──────────────────────────────────────────────"
    echo " 注意: この配布物は ${_hit} の同期フォルダの下に置かれています。"
    echo "   何が起きるか:"
    echo "     - 部品一式 (数GB) がまるごと同期に乗り、容量と時間を食います"
    echo "     - 同期がファイルの実体を退避すると、._ の掃除・印 (拡張属性) の処理・"
    echo "       アンインストールが終わらないことがあります"
    echo "   どうすればよいか: 同期の対象外の場所 (例: ホーム直下の ~/Cynovela) へ"
    echo "   フォルダごと移してから起動することを勧めます。このまま進めることもできます。"
    echo "──────────────────────────────────────────────"
}

_warn_if_cloud_synced
_drop_marks

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
#   調べる先は本体のプロセス (server.py) と待ち受けの番号。この配布物から起こした
#   ものだけに絞らない。語頭を固定した " server\.py" で探す (mas_server.py の
#   ような別物に当てないため・tools/launch-body.sh の _is_our_server と同じ判定)。
#   受け取り手が選ぶまで、止めない・起こさない・作らない。
FOUND=""            # 1行1件: pid|port
ACTION="new"        # new / stop_new
STOP_TARGETS=""     # 「止めて、新しく起こす」が選ばれたときの止める対象 (PID)
_collect_running() {
    FOUND=""
    local _p _cmd _port
    for _p in $(pgrep -f " server\.py" 2>/dev/null); do
        _cmd="$(ps -o command= -p "$_p" 2>/dev/null || true)"
        case "$_cmd" in *" server.py"*) : ;; *) continue ;; esac
        _port="$(lsof -nP -a -p "$_p" -iTCP -sTCP:LISTEN 2>/dev/null | awk 'NR>1{sub(".*:","",$9); print $9; exit}')"
        FOUND="${FOUND}${_p}|${_port:-不明}
"
    done
}
_stop_listed_running() {  # 表示済みの動いているものを止める (止めるだけ)
    local _p _rest
    printf '%s' "$FOUND" | while IFS='|' read -r _p _rest; do
        [ -n "$_p" ] || continue
        echo "止めています: PID $_p"
        kill "$_p" 2>/dev/null || true
    done
    sleep 2
    printf '%s' "$FOUND" | while IFS='|' read -r _p _rest; do
        [ -n "$_p" ] || continue
        kill -0 "$_p" 2>/dev/null && kill -9 "$_p" 2>/dev/null || true
    done
}
_verify_stopped() {  # 止まったことを実測して画面へ出す
    local _p _rest
    printf '%s' "$FOUND" | while IFS='|' read -r _p _rest; do
        [ -n "$_p" ] || continue
        if kill -0 "$_p" 2>/dev/null; then
            echo "PID $_p : まだ動いています。bash stop.sh を叩くか、記録 ($LOG) を確かめてください。"
        else
            echo "PID $_p : 止まりました。資料と設定は消えていません。"
        fi
    done
}
_confirm_stop_exit() {  # 止めて終わる の確認 → 0=Y / 1=N (C/EOF は終了)
    local ans
    while true; do
        echo ""
        echo "これから行うことを確かめてください。"
        echo "  使うもの      : いま動かしているもの"
        echo "  作られるもの   : ありません（止めるもの: PID $(printf '%s' "$FOUND" | while IFS='|' read -r _p _r; do [ -n "$_p" ] && printf '%s ' "$_p"; done)。止めるだけです。資料と設定は消えません）"
        echo "  残る場所      : このフォルダの中の store/"
        echo "  消し方        : ここでは何も消しません（手元から取り除く道は bash uninstall.sh です）"
        echo "  外から        : 止めたあとは、どこからも開けなくなります"
        echo "  初回          : 待ちはありません"
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
    local ans _cnt _first
    _collect_running
    echo ""
    echo "先に、いま動いているものを調べました。"
    if [ -z "$FOUND" ]; then
        echo "  動いているものは 0個 でした。"
        echo "このまま進みます。"
        return 0
    fi
    printf '%s' "$FOUND" | while IFS='|' read -r _p _port; do
        [ -n "$_p" ] || continue
        echo "  server.py（PID ${_p}）  : 動いています（待ち受け ${_port}）"
    done
    echo "このまま新しく起こすと、同じものが二重に立ち上がります。"
    _cnt="$(printf '%s' "$FOUND" | /usr/bin/grep -c . || true)"
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
                ACTION="stop_new"
                STOP_TARGETS="$(printf '%s' "$FOUND" | while IFS='|' read -r _p _r; do [ -n "$_p" ] && printf '%s ' "$_p"; done)"
                return 0
                ;;
            2)
                # この形の本体は止まると消える (プロセス)。止まったまま残るものは無い。
                echo "  → 止まっているものは 0個 です。"
                continue
                ;;
            3)
                _first="$(printf '%s' "$FOUND" | head -1)"
                echo ""
                echo "開くところ : http://127.0.0.1:${_first#*|}/"
                echo "新しくは起こしていません。何も止めていません。"
                exit 0
                ;;
            4)
                if _confirm_stop_exit; then
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

# ── 1. conda・Python・自分で指定 を同列に並べて選ばせる (N-1) ──
#   決定 14-1〜14-5: conda を先に見る・共有の環境には書かない。
#   決定 30-2 と同じ考え方で、見つけたものへ黙って進む形にしない。選ばれるまで起動しない。
#   調べた結果は、見つからなかったものも含めて全部出す。行そのものを消さない。
CONDA_BASE=""
CONDA_BIN=""
_find_conda() {
    local _c
    for _c in "$HOME/miniforge3" "$HOME/miniconda3" "/opt/homebrew/Caskroom/miniforge/base" \
              "$HOME/opt/anaconda3" "$HOME/anaconda3" "/usr/local/anaconda3"; do
        if [ -x "$_c/bin/conda" ]; then CONDA_BASE="$_c"; CONDA_BIN="$_c/bin/conda"; return 0; fi
    done
    if command -v conda >/dev/null 2>&1; then
        CONDA_BIN="$(command -v conda)"
        CONDA_BASE="$("$CONDA_BIN" info --base 2>/dev/null || true)"
        [ -n "$CONDA_BASE" ] && return 0
    fi
    return 1
}
HAVE_CONDA=0
_find_conda && HAVE_CONDA=1
# 3.12 以上の python を探す (新しい版から順に)
_find_python() {
    # DD-CYN-0140: 要件は 3.12 以上である (pyproject.toml requires-python = ">=3.12" /
    #   environment.yml が python=3.12.13 を固定 / tools/conf.sh の _conf_py_meets も 3.12 以上)。
    #   旧: ここだけ 3.10 以上を通しており、選択肢2 を選ぶと launch-body.sh 側が 3.12 未満を
    #   弾いて止まるのに、この画面は「3.10 以上」と「3.12 を入れてください」を並べて出していた。
    #   ∴ 判定と文言を、宣言した要件 (3.12 以上) に揃える (launch-body.sh の venv_base_python と同じ)。
    #   版は名前で決めつけず、その python 自身に答えさせる。
    local c p
    for c in python3.13 python3.12; do
        if p="$(command -v "$c" 2>/dev/null)" \
           && "$p" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 12) else 1)' >/dev/null 2>&1; then
            printf '%s\n' "$p"; return 0
        fi
    done
    # 版のついた名前が無いときは python3 の版を見る
    if p="$(command -v python3 2>/dev/null)" \
       && "$p" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 12) else 1)' >/dev/null 2>&1; then
        printf '%s\n' "$p"; return 0
    fi
    return 1
}
HAVE_PY=0
FOUND_PY=""
FOUND_PY="$(_find_python)" && HAVE_PY=1

FORM_SEL=""      # conda / venv / custom
FORM_DISP=""     # 画面に出す名前
CUSTOM_PY=""
choose_form() {
    local vc="" vpy="" ans
    [ "$HAVE_CONDA" = "1" ] && vc="$("$CONDA_BIN" --version 2>/dev/null | /usr/bin/grep -oE '[0-9]+(\.[0-9]+)+' | head -1)"
    [ "$HAVE_PY" = "1" ] && vpy="$("$FOUND_PY" --version 2>/dev/null | /usr/bin/grep -oE '[0-9]+(\.[0-9]+)+' | head -1)"
    while true; do
        echo ""
        echo "使えるものを調べました。"
        if [ "$HAVE_CONDA" = "1" ]; then
            echo "  conda       : 見つかりました（${vc:-版は読めませんでした}）"
        else
            echo "  conda       : 見つかりませんでした"
        fi
        if [ "$HAVE_PY" = "1" ]; then
            echo "  Python      : 見つかりました（${vpy:-版は読めませんでした}）"
        else
            echo "  Python      : 見つかりませんでした"
        fi
        echo "  自分で指定   : いつでも選べます"
        echo "どの形で動かしますか。"
        echo "  1) conda に専用の環境を作る"
        echo "     残るもの: conda の環境1つ（約 3.9 GB・名前: ${DIST_ENV}）"
        echo "     消し方  : bash uninstall.sh"
        echo "  2) この配布物の中だけに作る（Mac を汚しません）"
        echo "     残るもの: このフォルダの中に約 2.2 GB"
        echo "     消し方  : bash uninstall.sh"
        echo "  3) 自分で指定する"
        echo "     使う Python の場所を入力します。"
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
                if [ "$HAVE_CONDA" = "1" ]; then FORM_SEL="conda"; FORM_DISP="conda"; return 0; fi
                echo ""
                echo "conda が見つかりませんでした。"
                echo "  入れ方: https://github.com/conda-forge/miniforge/releases/latest から Miniforge を入れてください"
                echo "  入れ終えたら、もう一度このファイルを押してください"
                echo "このターミナルは開いたままにしてあります。"
                exit 1
                ;;
            2)
                if [ "$HAVE_PY" = "1" ]; then FORM_SEL="venv"; FORM_DISP="この配布物の中の Python"; return 0; fi
                echo ""
                echo "3.12 以上の python3 が見つかりませんでした。"
                echo "  入れ方: https://www.python.org/downloads/ から 3.12 以上を入れてください"
                echo "  または 1) の conda を選んでください"
                echo "  入れ終えたら、もう一度このファイルを押してください"
                echo "このターミナルは開いたままにしてあります。"
                exit 1
                ;;
            3)
                printf '使う Python の場所を入れてください: '
                if ! IFS= read -r CUSTOM_PY; then
                    echo ""
                    echo "入力が閉じたため、やめました。何も作っていません。"
                    exit 0
                fi
                if [ -z "$CUSTOM_PY" ]; then continue; fi
                if [ ! -x "$CUSTOM_PY" ]; then
                    echo "  → その場所に実行できる Python が見つかりませんでした: $CUSTOM_PY"
                    continue
                fi
                FORM_SEL="custom"
                FORM_DISP="$CUSTOM_PY"
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
# ── 2. 進める前の確認 (N-3) ─────────────────────────
#   選んだ直後に、これから何が起きるかを1画面で出し、Y/N/C で選ばせる。
#   Y=進める / N=選び直す (N-1 の画面へ戻る) / C と EOF=何もせずに終わる。
CONFIRM=""
NEED_SETUP=0
SEL_PY=""
_compute_selection() {
    NEED_SETUP=0
    case "$FORM_SEL" in
        conda)  SEL_PY="$CONDA_BASE/envs/$DIST_ENV/bin/python"; [ -x "$SEL_PY" ] || NEED_SETUP=1 ;;
        venv)   SEL_PY="$WRAP_DIR/.venv-cynovela/bin/python";   [ -x "$SEL_PY" ] || NEED_SETUP=1 ;;
        custom) SEL_PY="$CUSTOM_PY" ;;
    esac
}
confirm_launch() {
    local ans line_use line_make line_where line_del line_first
    case "$FORM_SEL" in
        conda)
            if [ "$NEED_SETUP" = "1" ]; then
                line_use="conda（専用の環境を作ります）"
                line_make="conda の環境 1つ（名前: ${DIST_ENV}）"
                line_first="部品の取得に時間がかかります"
            else
                line_use="conda（既に在る専用の環境 '$DIST_ENV' を使います）"
                line_make="ありません（既に在る環境を使います）"
                line_first="待ちはほとんどありません"
            fi
            line_where="conda の環境の保存先に約 3.9 GB"
            line_del="bash uninstall.sh"
            ;;
        venv)
            if [ "$NEED_SETUP" = "1" ]; then
                line_use="この配布物の中の Python（配布物の中だけに作ります）"
                line_make="このフォルダの中の保存先 1つ（.venv-cynovela）"
                line_first="部品の取得に時間がかかります"
            else
                line_use="この配布物の中の Python（既に在る保存先 .venv-cynovela を使います）"
                line_make="ありません（既に在る保存先を使います）"
                line_first="待ちはほとんどありません"
            fi
            line_where="このフォルダの中に約 2.2 GB"
            line_del="bash uninstall.sh"
            ;;
        custom)
            line_use="$CUSTOM_PY"
            line_make="ありません（入力された Python をそのまま使います）"
            line_where="このフォルダの中の store/"
            line_del="bash uninstall.sh"
            line_first="待ちはほとんどありません"
            ;;
    esac
    while true; do
        echo ""
        echo "これから行うことを確かめてください。"
        echo "  使うもの      : $line_use"
        if [ -n "$STOP_TARGETS" ]; then
            echo "                  （先に、動いているもの PID $STOP_TARGETS を止めます。止めるだけです）"
        fi
        echo "  作られるもの   : $line_make"
        echo "  残る場所      : $line_where"
        echo "  消し方        : $line_del"
        echo "  外から        : 同じネットワークの別の Mac から開けます"
        echo "                  この Mac だけに限りたいときは --local-only を付けてください"
        echo "  初回          : $line_first"
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

# ── A-5 (DD-CYN-0142 §5-E): 同梱の環境 (.venv-cynovela) が既に在り、その python が
#    動くときは、選択の画面を出さずにそのまま使う。在るのに壊れているときだけ選択へ。
_BUNDLED_PY="$WRAP_DIR/.venv-cynovela/bin/python"
[ -x "$_BUNDLED_PY" ] || _BUNDLED_PY="$WRAP_DIR/.venv-cynovela/bin/python3"
_BUNDLED_OK=0
if [ -x "$_BUNDLED_PY" ] \
   && "$_BUNDLED_PY" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 12) else 1)' >/dev/null 2>&1; then
    _BUNDLED_OK=1
fi
if [ "$_BUNDLED_OK" = "1" ]; then
    echo ""
    echo "同梱の環境 (.venv-cynovela) が見つかりました。選択の画面は出さず、これを使って起動します。"
    FORM_SEL="venv"; FORM_DISP="この配布物の中の Python"
    SEL_PY="$_BUNDLED_PY"; NEED_SETUP=0; CONFIRM="yes"
else
    if [ -d "$WRAP_DIR/.venv-cynovela" ]; then
        echo ""
        echo "同梱の環境 (.venv-cynovela) は在りますが、壊れているようです (python が動きません)。選択の画面を出します。"
    fi
    while true; do
        choose_form
        _compute_selection
        confirm_launch
        [ "$CONFIRM" = "yes" ] && break
    done
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

# ── 3. 環境がまだ無ければ、選ばれた形で作る (本体の --setup を呼ぶ) ─────
if [ "$NEED_SETUP" = "1" ]; then
    bash "$BODY" --setup --base "$FORM_SEL"
    if [ ! -x "$SEL_PY" ]; then
        echo "環境が用意されなかったため、起動しません。"
        echo "このターミナルは開いたままにしてあります。記録: $LOG"
        exit 1
    fi
fi
PASS+=(--python "$SEL_PY")

# ── 3.5 部品 (bge-m3) が無いときは、ダウンロードの前に必ず聞く () ──
#   本体は切り離し (--no-prompt・端末なし) で動くため、本体の確認は受け取り手に
#   届かない。∴ 人が見ているこの包みで、切り離す前に聞く (事実161 の二択を保つ)。
#   選ぶまで通信は始めない。1 を選ぶと、本体が起動の中でダウンロードする (進み具合は記録へ)。
_model_found=""
for _cand in \
    "$WRAP_DIR/store/models/models--BAAI--bge-m3" \
    "$WRAP_DIR/store/models/BAAI/bge-m3" \
    "$HOME/.cynovela/models/models--BAAI--bge-m3" \
    "$HOME/.cynovela/hf_cache/models--BAAI--bge-m3" \
    "$HOME/.cache/huggingface/hub/models--BAAI--bge-m3"; do
    [ -d "$_cand" ] || continue
    for _s in "$_cand"/snapshots/*/; do
        if [ -d "$_s" ] && [ -n "$(ls -A "$_s" 2>/dev/null || true)" ]; then _model_found="$_s"; break; fi
    done
    [ -n "$_model_found" ] && break
done
if [ -z "$_model_found" ]; then
    echo ""
    echo "資料を読み取るための部品 (埋め込みモデル bge-m3) が、この機械にまだありません。"
    echo "どうしますか？"
    echo "  1) いまダウンロードする"
    echo "     ・大きさ: 約 2.3 GB"
    echo "     ・インターネットにつなぎます (ダウンロード元: Hugging Face)"
    echo "     ・進み具合は記録 ($LOG) に出ます"
    echo "  2) すでに持っているフォルダを選ぶ"
    echo "  3) ダウンロードせずに、いちばん軽い設定で始める"
    echo ""
    echo "  ※ 選ぶまで、通信は始めません。"
    printf '  選んでください [1-3] (Enter は 3): '
    if ! IFS= read -r _mc; then
        echo ""
        echo "入力が閉じたため、いちばん軽い設定で始めます。"
        _mc=3
    fi
    case "$_mc" in
        1)
            echo "  → 起動の中でダウンロードします。進み具合は記録 ($LOG) に出ます。"
            ;;
        2)
            _msel="$(osascript -e 'POSIX path of (choose folder with prompt "bge-m3 が入っているフォルダを選んでください")' 2>/dev/null || true)"
            if [ -n "$_msel" ]; then
                echo "  → 選ばれた場所: $_msel"
                echo "     この場所を検索の対象にするには docs/SETUP-ACCELERATOR.md の手順で"
                echo "     $WRAP_DIR/store/models/models--BAAI--bge-m3/snapshots/<版>/ へ置いてください。"
                echo "     置き終えたら、もう一度 ./launch.sh を叩いてください。ここでは起動しません。"
                exit 0
            fi
            echo "  → 選ばれませんでした。いちばん軽い設定で始めます。"
            PASS+=(--mode minimal)
            ;;
        *)
            echo "  → ダウンロードしません。いちばん軽い設定で始めます。"
            PASS+=(--mode minimal)
            ;;
    esac
fi

# ── 4. 本体をターミナルから切り離して起動する ───────────────────────
: >> "$LOG"
LOG_MARK="$(wc -c < "$LOG" | tr -d ' ')"
nohup bash "$BODY" --no-prompt ${PASS[@]+"${PASS[@]}"} >> "$LOG" 2>&1 &
BODY_PID=$!
disown %% 2>/dev/null || true
echo "起動しています (本体はこのターミナルから切り離して動かします)"

# ── 5. 立ち上がりを待つ ─────────────────────────────────────
_port_from_log() {
    tail -c "+$((LOG_MARK + 1))" "$LOG" 2>/dev/null \
        | /usr/bin/grep -oE 'http://(0\.0\.0\.0|127\.0\.0\.1|localhost):[0-9]+' \
        | tail -n 1 | /usr/bin/grep -oE '[0-9]+$'
}
PORT=""
i=0
while [ "$i" -lt 600 ]; do
    sleep 2
    [ -z "$PORT" ] && PORT="$(_port_from_log || true)"
    if [ -n "$PORT" ] && curl -s -o /dev/null --max-time 2 "http://localhost:$PORT/api/health" 2>/dev/null; then
        # N-7: 止め方と消し方を、起動が終わったここで必ず画面へ出す。
        echo ""
        echo "立ち上がりました。"
        echo "  開くところ : http://127.0.0.1:$PORT/"
        echo "  記録       : $LOG"
        echo "止めるときは、次のように叩いてください。"
        echo "  bash stop.sh"
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
