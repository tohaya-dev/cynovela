#!/bin/bash
# ============================================================
#  Cynovela 入口 (entry-unify-20260802 / S-1〜S-4)
#
#  受け取り手が実行するのはこの1本だけです。start.sh は廃止し、
#  中身はこのファイルの関数として吸収しました。
#
#  使い方:
#    ./launch.sh                 本番 (空のデータベース) で起動する
#    ./launch.sh --demo          同梱のダミー資料が載ったデモで起動する
#    ./launch.sh --local-only    待ち受けを自マシン内だけに絞る
#
#    ./launch.sh --check         起動せずに動く条件だけを調べ、結果を1本のファイルへ書く
#    ./launch.sh --setup         実行エンジンを選んで、足りないものを入れる (入れたら止まります)
#
#    ./launch.sh --base <conda|venv|none>  --setup で聞かずに実行エンジンを決める
#    ./launch.sh --env-name <名前>         conda 環境の名前を変える (既定 cynovela-dist)
#    ./launch.sh --verbose                 入れている間の素の出力をそのまま出す
#
#    ./launch.sh --add                     取り込み元にするフォルダを選ぶ
#    ./launch.sh --add-path <パス>         取り込み元を足す
#    ./launch.sh --list                    取り込み元の一覧
#    ./launch.sh --remove <中の名前>       取り込み元を外す
#    ./launch.sh --ingest <パス>           取り込み元を足してから起動する (複数指定可)
#
#  停止: bash stop.sh
#
#  環境チェックの3つのモード:
#    既定    足りないものを並べて止まる (何も入れない・何も書き換えない)
#    --setup 実行エンジンを選んでから、足りないものをそこへ入れる。入れたら止まる
#    --check 読み取りだけで同じ検査を回し、結果を store/env-check.txt へ書いて終わる
#
#  --setup が実行エンジンを決める順番 ():
#    1. まず conda を見に行く。使えるなら、この配布物専用の conda 環境を新しく作る。
#       名前の既定は 'cynovela-dist' で、--env-name で変えられる。
#    2. conda が使えないときだけ、この配布物の中 (.venv-cynovela) へ倒す。
#    3. どちらにするかは番号で選ばせる。--base で先に決めておくこともできる。
#
#  共有の conda 環境 'cynovela' は読むだけで、書き換えません。
#  既に在る環境の名前を指定された場合は、書き足さずに止まります。
#  (旧 launch.sh は 2回目以降の起動のたびに `pip install -q -r requirements.txt` を
#   共有環境に対して実行していました。受け取り手の他の作業ごと版を動かす経路でした。)
# ============================================================
set -e

# M-5: 本体は tools/ の下の部品になった (決定 12-2)。保存先の基準は配布物のルートディレクトリのまま。
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SHARED_ENV_NAME="cynovela"
DIST_ENV_NAME="cynovela-dist"
ENV_FILE="$SCRIPT_DIR/environment.yml"
VENV_DIR="$SCRIPT_DIR/.venv-cynovela"
REPORT_FILE="$SCRIPT_DIR/store/env-check.txt"
REQ_FILE="$SCRIPT_DIR/requirements.txt"
INGEST_ROOTS_HELPER="$SCRIPT_DIR/scripts/ingest_roots.py"
INGEST_ROOTS_FILE=""   # 保存先が決まってから入れる ()
MODEL_DIR="$SCRIPT_DIR/store/models/models--BAAI--bge-m3"
DEFAULT_PORT_FALLBACK=8765   # 設定が読めないときにだけ使う値

MODE_CHECK=0
MODE_SETUP=0
# 決めごとは cynovela.yaml 1本から読む。環境変数では受け取らない。
CONF_REPO="$SCRIPT_DIR"
. "$SCRIPT_DIR/tools/conf.sh"
# F-c: 取り込み元のバックアップは、動作要件 (3.12 以上) を満たす python でのみ読み書きする。
#   素の python3 (版の検査なし) へは倒れない。満たすものが無いときは理由と、その場で効く
#   操作を出す。
# R-1: 版は名前で当てず、conf_pick_py がその python 自身に答えさせる。
#   ∴ 配布物専用の conda 環境の python (名前は python) も候補に入る。
ROOTS_PY="$(conf_pick_py "$SCRIPT_DIR" || true)"
_roots_py() {
    if [ -z "$ROOTS_PY" ]; then
        # R-4: いま失敗した入口 (Cynovela-start.command は ./launch.sh を
        #   呼ぶだけの同じ道) をもう一度押せ、とは言わない。その場で効く操作を出す。
        echo "エラー: 3.12 以上の python が見つかりません。取り込み元のバックアップ (store/ingest-roots.json) を扱えません。" >&2
        echo "       直し方: ./launch.sh --setup を叩いてください。この配布物の中に python の保存先が作られ、以後この操作が通ります。" >&2
        echo "       いま在るものを確かめる: ./launch.sh --check" >&2
        return 1
    fi
    "$ROOTS_PY" "$@"
}
DATA_DIR="$(conf_get_or paths data_dir "$SCRIPT_DIR/store")"
case "$DATA_DIR" in ./*) DATA_DIR="$SCRIPT_DIR/${DATA_DIR#./}" ;; esac
# 取り込み元のバックアップは保存先の下に置く。本体 (server.py) が見る場所と揃える。
#   揃えないと、保存先を移したときに入口と本体が別々のバックアップを見て食い違う。
INGEST_ROOTS_FILE="$DATA_DIR/ingest-roots.json"
DEFAULT_PORT="$(conf_get_num server port "$DEFAULT_PORT_FALLBACK")"
DEFAULT_HOST="$(conf_get_or server host 0.0.0.0)"
NO_PROMPT=0
FETCH_MODEL=0
BASE_CHOICE=""      # --base で先に決められる: conda / venv / none
ENV_NAME=""         # --env-name。空なら DIST_ENV_NAME を使う
VERBOSE=0           # --verbose。1 なら pip/conda の素の出力をそのまま出す
BASE_LOCKED=0       # --setup で選び終わったら 1。以後 resolve_python は上書きしない
CUSTOM_PY=""        # --python。N-1 の「自分で指定する」の受け口
APP_ARGS=()

# §7-5-3: ヘルプは2段。
#   先に出るのは「受け取り手が使うもの」だけ。試験・開発用は --help-all の下へ隔離する。
#   隠すだけで、名前も挙動も変えない (外から叩いている手順書と記録が壊れるため)。
usage() {
    cat <<'USAGE'
Cynovela 入口 — 受け取り手が叩くのはこの1本だけです。

● 何も付けないとき
  ./launch.sh                     聞かれたことに番号で答えるだけで起動します。
                                  (何を読ませるか)

● 番号で答えずに、はじめから決めて起動する
  ./launch.sh --demo              同梱のダミー資料が載った状態で起動します。
  ./launch.sh --add               読み込むフォルダを選ぶ画面を出して足します。
  ./launch.sh --list              いま足してあるフォルダを一覧で出します。
  ./launch.sh --remove <名前>     足したフォルダを外します (名前は --list に出るもの)。
                                  ※ 画面でも 設定 → 取り込み元 から足す・見る・外せます。

● 入れる / 点検する
  ./launch.sh --setup             動かすのに要るものを入れます (入れたら止まります)。
  ./launch.sh --check             起動せず、動く条件だけを調べて1本のファイルへ書きます。
  ./launch.sh --base conda|venv|none
                                  python を用意する場所を先に決めます (--setup と一緒に使います)。

● そのほか
  ./launch.sh --port <番号>       待ち受ける番号を変えます (既定 8765)。
                                  何も付けないときは、空いている番号を自分で選びます。
  ./launch.sh --local-only        待ち受けを自分のマシンの中だけに絞ります。
  bash stop.sh                    止めます。

● 開く場所と入り方
  開く場所 : http://localhost:8765   (--port を使ったときはその番号)
  入り方   : 管理者 cynovela / 閲覧者 demo
             最初のパスワードは同梱の STARTUP.md の「ログイン」の節にあります。
             管理者は最初に入ったときにパスワードの変更を求められます。
             変え終わるまで管理の操作は通りません。

共有の conda 環境 'cynovela' は読むだけで、書き換えません。

試験・開発のための指定は ./launch.sh --help-all で見られます。
USAGE
}

usage_all() {
    usage
    cat <<'USAGE_ALL'

────────────────────────────────────────────────────────────
● ここから下は試験・開発のための指定です。受け取り手は使いません。

  ./launch.sh --add-path <パス>   場所を文字で指定して足します (画面を出しません)。
  ./launch.sh --ingest <パス>     足して、そのまま起動します。
  ./launch.sh --env-name <名前>   conda 環境の名前を変えます (既定 cynovela-dist)。
  ./launch.sh --python <場所>     使う Python を自分で指定します (動作は約束しません)。
  ./launch.sh --verbose           入れている間の素の出力をそのまま出します。
  ./launch.sh --mode <名前>       text|lite|lite-en (既定 text)。
                                  読み取りの精度は変わりません (構成の説明と同じ)。
  ./launch.sh --lmstudio-url <URL>  回答を作る LLM の宛先を変えます。
  ./launch.sh --host <アドレス>   待ち受けるアドレスを直に指定します。
  ./launch.sh --lan               LAN 公開 (--local-only を付けないときと同じ。後方互換)。
  ./launch.sh --allow-tailscale   TailScale の網からの接続を許します。
  ./launch.sh --allow-subnet <網> 許す網を足します (複数指定可)。
  ./launch.sh --reset-admin       管理者のパスワードを作り直して表示し、終わります。
USAGE_ALL
}

# 知らない指定を渡されたときは、黙って落ちずにヘルプを出す (B2)。
#   値 (先頭が - でないもの) は直前の指定の値として本体へそのまま渡す。
#   先頭が - で、下の一覧に無いものだけを「知らない指定」として扱う。
KNOWN_APP_FLAGS=" --demo --lmstudio-url --mode --host --lan --local-only --port --allow-tailscale --allow-subnet --reset-admin "
unknown_arg() {
    echo "知らない指定です: $1" >&2
    echo "" >&2
    usage >&2
    exit 2
}

# §7-5-2: 引数が1つも無いときは、番号で答えるだけで進める形にする。
#   端末から人が叩いたときだけ聞く (非対話では従来どおり黙って既定で進む)。
ARGC_AT_START=$#

# 取り込み元を足したあとのガイド。形態を見て出し分ける (S-1)。
#   見分け方は Cynovela-add-folder.command と同じで、deploy/container の有無を見る。
#   在ればコンテナ (コンテナ) で動く形。束縛は起動時にしか張れないため起動し直しが要る。
#   無ければこの Mac で直接動く形。バックアップは参照のたびに読み直されるため要らない
#   (読む側は routers/files.py。サーバも restart_required_to_apply に偽を返す)。
#   文面は画面 (frontend/js/ingest_roots_ui.js) と Cynovela-add-folder.command に合わせる。
_print_add_applied() {
    if [ -d "$SCRIPT_DIR/deploy/container" ]; then
        echo "反映には起動し直し (./launch.sh) が必要です"
    else
        echo "いま動いている Cynovela の画面から、すぐに選べます。"
    fi
}

# ------------------------------------------------------------
# 引数の振り分け
#   取り込み元の管理引数はここで処理して終わる (本体には渡さない)。
#   --check / --setup は環境チェックのモードで、本体には渡さない。
#   それ以外 (--demo / --local-only / --port など) はそのまま本体へ渡す。
# ------------------------------------------------------------
while [ $# -gt 0 ]; do
    case "$1" in
        -h|--help)
            usage
            exit 0
            ;;
        --help-all)
            usage_all
            exit 0
            ;;
        --check)
            MODE_CHECK=1
            ;;
        --setup)
            MODE_SETUP=1
            ;;
        --no-prompt)
            # 聞かずに進める (アイコンの道・手順書・試験から使う)
            NO_PROMPT=1
            ;;
        --fetch-model)
            # AIモデルが無いときにダウンロードする (画面が確認を取ってから渡す)
            FETCH_MODEL=1
            ;;
        --base)
            case "${2:-}" in
                conda|venv|none)
                    BASE_CHOICE="$2"
                    shift
                    ;;
                *)
                    echo "使い方: ./launch.sh --base <conda|venv|none>"
                    exit 2
                    ;;
            esac
            ;;
        --env-name)
            if [ -z "${2:-}" ]; then
                echo "使い方: ./launch.sh --env-name <conda 環境の名前>"
                exit 2
            fi
            ENV_NAME="$2"
            shift
            ;;
        --python)
            # N-1: 「自分で指定する」の受け口。入口 (launch.sh) の選択が渡す。
            #   受け取り手が直接使ってもよい。指した Python をそのまま使う。動作は約束しない。
            if [ -z "${2:-}" ] || [ ! -x "${2:-}" ]; then
                echo "使い方: ./launch.sh --python <実行できる Python の場所>"
                exit 2
            fi
            CUSTOM_PY="$2"
            shift
            ;;
        --verbose)
            VERBOSE=1
            ;;
        --add-path)
            if [ -z "${2:-}" ]; then
                echo "使い方: ./launch.sh --add-path <フォルダのパス>"
                exit 2
            fi
            NAME="$(_roots_py "$INGEST_ROOTS_HELPER" --file "$INGEST_ROOTS_FILE" add "$2")"
            echo "取り込み元を追加しました (中の名前: $NAME)"
            _print_add_applied
            exit 0
            ;;
        --add)
            SEL="$(osascript -e 'POSIX path of (choose folder with prompt "取り込み元にするフォルダを選んでください")')" || {
                echo "フォルダ選択がキャンセルされました"
                exit 1
            }
            NAME="$(_roots_py "$INGEST_ROOTS_HELPER" --file "$INGEST_ROOTS_FILE" add "$SEL")"
            echo "取り込み元を追加しました (中の名前: $NAME)"
            _print_add_applied
            exit 0
            ;;
        --list)
            _roots_py "$INGEST_ROOTS_HELPER" --file "$INGEST_ROOTS_FILE" list
            exit 0
            ;;
        --remove)
            if [ -z "${2:-}" ]; then
                echo "使い方: ./launch.sh --remove <中の名前>"
                exit 2
            fi
            _roots_py "$INGEST_ROOTS_HELPER" --file "$INGEST_ROOTS_FILE" remove "$2"
            exit 0
            ;;
        --ingest)
            # 起動時に取り込み元を足す。本体 (server.py) の --ingest へそのまま渡す。
            if [ -z "${2:-}" ]; then
                echo "使い方: ./launch.sh --ingest <フォルダのパス>"
                exit 2
            fi
            APP_ARGS+=(--ingest "$2")
            shift
            ;;
        -*)
            # B2: 本体が受ける指定だけを通し、それ以外はヘルプを出して止まる。
            case "$KNOWN_APP_FLAGS" in
                *" $1 "*) APP_ARGS+=("$1") ;;
                *)        unknown_arg "$1" ;;
            esac
            ;;
        *)
            # 直前の指定の値 (例: --port の 8900)。そのまま本体へ渡す。
            APP_ARGS+=("$1")
            ;;
    esac
    shift
done

# 使うポート (本体へ渡す --port を先に読む。指定が無ければ 8765)
PORT="$DEFAULT_PORT"
PORT_GIVEN=0
_prev=""
for _a in ${APP_ARGS[@]+"${APP_ARGS[@]}"}; do
    if [ "$_prev" = "--port" ]; then PORT="$_a"; PORT_GIVEN=1; fi
    _prev="$_a"
done

# ============================================================
# §7-5-2: 引数なしのときの問いかけ
#   聞くのは3つまで。待ち受ける番号は聞かず、こちらで決める。
#   分からなければ Enter で必ず先へ進める。
# ============================================================

# この配布物が前に上げた本体が使っている番号なら、掛け直せるので空きとみなす。
_port_is_usable() {
    local _p="$1" _pid
    # LISTEN だけを見る (残存クライアント接続で「使用中」と誤検知しない)
    lsof -nP -iTCP:"$_p" -sTCP:LISTEN >/dev/null 2>&1 || return 0
    for _pid in $(lsof -t -i ":$_p" 2>/dev/null || true); do
        _is_our_server "$_pid" || return 1
    done
    return 0
}

_pick_port() {
    local _p="$DEFAULT_PORT" _n=0
    while [ "$_n" -lt 50 ]; do
        if _port_is_usable "$_p"; then
            echo "$_p"
            return 0
        fi
        _p=$((_p + 1))
        _n=$((_n + 1))
    done
    echo "$DEFAULT_PORT"
}

# 部品 (bge-m3) が手元に無いときは、黙って取りに行かない。必ず一度止めて聞く。
_ask_model_if_missing() {
    local _cand _s _found=""
    for _cand in \
        "$MODEL_DIR" \
        "$SCRIPT_DIR/store/models/BAAI/bge-m3" \
        "$HOME/.cache/huggingface/hub/models--BAAI--bge-m3"; do
        [ -d "$_cand" ] || continue
        for _s in "$_cand"/snapshots/*/; do
            if [ -d "$_s" ] && [ -n "$(ls -A "$_s" 2>/dev/null || true)" ]; then _found="$_s"; break; fi
        done
        [ -n "$_found" ] && break
    done
    [ -n "$_found" ] && return 0

    echo ""
    echo "  資料を読み取るための部品が、この機械にまだありません。"
    echo "  どうしますか？"
    echo "    1) いまダウンロードする"
    echo "       ・大きさ: 約 2.2 GB"
    echo "       ・インターネットにつなぎます (ダウンロード元: Hugging Face)"
    echo "    2) すでに持っているフォルダを選ぶ"
    echo "    3) ダウンロードせずに、いちばん軽い設定で始める"
    echo ""
    echo "  ※ 選ぶまで、通信は始めません。"
    printf "  選んでください [1-3] (Enter は 3): "
    local _c=""
    read -r _c || _c=""
    case "$_c" in
        1)
            echo "  → 起動したあとにダウンロードします。画面に確認が出ます。"
            ;;
        2)
            local _sel
            _sel="$(osascript -e 'POSIX path of (choose folder with prompt "bge-m3 が入っているフォルダを選んでください")' 2>/dev/null || true)"
            if [ -n "$_sel" ]; then
                echo "  → 選ばれた場所: $_sel"
                echo "     この場所を読ませるには SETUP-ACCELERATOR.md の手順で"
                echo "     $MODEL_DIR/snapshots/<版>/ へ置いてください。"
            else
                echo "  → 選ばれませんでした。いちばん軽い設定で始めます。"
                APP_ARGS+=(--mode minimal)
            fi
            ;;
        *)
            echo "  → ダウンロードしません。いちばん軽い設定で始めます。"
            APP_ARGS+=(--mode minimal)
            ;;
    esac
}

run_interactive() {
    local _c=""
    echo ""
    echo "はじめる前に、1つだけ聞きます。分からなければ Enter を押してください。"
    echo ""

    # 問い1: 何を読ませるか
    echo "1. 何を読ませますか？"
    echo "    1) 同梱のお試し資料で始める"
    echo "    2) 自分のフォルダを足す (フォルダを選ぶ画面が出ます)"
    printf "  選んでください [1-2] (Enter は 1): "
    read -r _c || _c=""
    case "$_c" in
        2)
            local _sel
            _sel="$(osascript -e 'POSIX path of (choose folder with prompt "読ませるフォルダを選んでください")' 2>/dev/null || true)"
            if [ -n "$_sel" ]; then
                local _name
                _name="$(_roots_py "$INGEST_ROOTS_HELPER" --file "$INGEST_ROOTS_FILE" add "$_sel")"
                echo "  → 足しました: $_sel"
                echo "     (この中の名前: $_name)"
            else
                echo "  → 選ばれませんでした。同梱のお試し資料で始めます。"
                APP_ARGS+=(--demo)
            fi
            ;;
        *)
            echo "  → 同梱のお試し資料で始めます。"
            APP_ARGS+=(--demo)
            ;;
    esac

    # §5-A (決定 40-2・40-4): 構成の問いを撤去した。示す形が text の
    #   1つだけになったため、尋ねずにそのまま text で進む。引数 (--mode 等) で渡す道は
    #   従来どおり残っている (server.py の受け付けは変えていない)。
    APP_ARGS+=(--mode text)

    # 部品が無いときだけ、もう1つ聞く
    _ask_model_if_missing

    # 待ち受ける番号は聞かない。こちらで決め、ふさがっていたときだけ知らせる。
    local _picked
    _picked="$(_pick_port)"
    if [ "$_picked" != "$DEFAULT_PORT" ]; then
        echo ""
        echo "  ※ いつもの番号 ($DEFAULT_PORT) は別のものが使っていました。"
        echo "     $_picked を使います。"
    fi
    PORT="$_picked"
    APP_ARGS+=(--port "$PORT")
    echo ""
    echo "  開く場所: http://localhost:$PORT"
    echo ""
}

# ------------------------------------------------------------
# B3: 取り込み元が1件も足されていないときの既定
#   何も渡されないときは、この配布物の中のダミー資料の場所を取り込み元にする (決定 9-3)。
#   場所は起動のたびにここで解き直す ($SCRIPT_DIR 基準)。バックアップへ展開先の絶対の場所を
#   焼き付けないため、配布物を別の場所へ移しても同じように効く。
#   受け取り手が --ingest を渡したときは、渡された側だけを使う (既定は足さない)。
#   既に1件でも足してあるときは何もしない (受け取り手が外した結果を勝手に戻さない)。
# ------------------------------------------------------------
DEFAULT_INGEST_DIR="$SCRIPT_DIR/dummy-corpus"
DEFAULT_INGEST_USED=0
NO_ROOTS_AND_NO_DEFAULT=0

# portable-roots-20260808 (F-2): 数えるだけなので生読みでも件数は合うが、
#   バックアップの読み口を1か所へ寄せるため、ここも scripts/ingest_roots.py に読ませる。
_roots_count() {
    python3 "$INGEST_ROOTS_HELPER" --file "$INGEST_ROOTS_FILE" --repo "$SCRIPT_DIR" list 2>/dev/null \
        | python3 -c 'import json,sys
try:
    print(len(json.load(sys.stdin) or []))
except Exception:
    print(0)'
}

_user_gave_ingest=0
for _a in ${APP_ARGS[@]+"${APP_ARGS[@]}"}; do
    [ "$_a" = "--ingest" ] && _user_gave_ingest=1
done
if [ "$_user_gave_ingest" = "0" ] && [ "$(_roots_count)" = "0" ]; then
    if [ -d "$DEFAULT_INGEST_DIR" ]; then
        APP_ARGS+=(--ingest "$DEFAULT_INGEST_DIR")
        DEFAULT_INGEST_USED=1
    else
        NO_ROOTS_AND_NO_DEFAULT=1
    fi
fi

# ------------------------------------------------------------
# B5: 掛け直しを必ず効かせる
#   落とす相手は「この配布物が起動した本体」だけ。まとめて落とす形 (pkill 等) は使わない。
#   バックアップ (store/server.pid) が無い・古いときでも、使っている番号から相手を1つずつ確かめる。
#   落とせなかったときは黙って進まない。何が上がっているかと手で止める方法を画面に出す。
# ------------------------------------------------------------
_is_our_server() {   # $1=番号。0 を返したら「この配布物の本体」
    local _p="${1:-}" _cmd _cwd
    [ -n "$_p" ] || return 1
    case "$_p" in (*[!0-9]*) return 1 ;; esac
    kill -0 "$_p" 2>/dev/null || return 1
    _cmd="$(ps -o command= -p "$_p" 2>/dev/null || true)"
    # 語頭を固定して見る (mas_server.py のような別物に当てない)
    case "$_cmd" in
        *" server.py"*) : ;;
        *)              return 1 ;;
    esac
    # この配布物の保存先から起動したものだけを相手にする (start_app は cd "$SCRIPT_DIR" 済み)
    _cwd="$(lsof -a -p "$_p" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p' | head -1)"
    [ "$_cwd" = "$SCRIPT_DIR" ]
}

_our_running_pids() {
    local _pidfile="$DATA_DIR/server.pid" _p _out=""
    if [ -f "$_pidfile" ]; then
        _p="$(cat "$_pidfile" 2>/dev/null || true)"
        if _is_our_server "$_p"; then
            _out="$_p"
        fi
    fi
    if command -v lsof >/dev/null 2>&1; then
        for _p in $(lsof -t -i ":$PORT" 2>/dev/null || true); do
            _is_our_server "$_p" || continue
            case " $_out " in *" $_p "*) continue ;; esac
            _out="$_out $_p"
        done
    fi
    echo "$_out"
}

stop_previous() {
    local _pidfile="$DATA_DIR/server.pid"
    local _targets _p _left _i

    # 古いバックアップはここで片づける (書く側と読む側の保存先は同じ = store/server.pid)
    if [ -f "$_pidfile" ]; then
        _p="$(cat "$_pidfile" 2>/dev/null || true)"
        if ! _is_our_server "$_p"; then
            echo "[掛け直し] バックアップが古いので片づけます (書かれていた番号: ${_p:-空})"
            rm -f "$_pidfile"
        fi
    fi

    _targets="$(_our_running_pids)"
    _targets="$(echo "$_targets" | tr -s ' ' | sed 's/^ //;s/ $//')"
    if [ -z "$_targets" ]; then
        return 0
    fi

    echo ""
    echo "[掛け直し] 先に上がっているものを止めます (番号: $_targets)"
    for _p in $_targets; do
        kill "$_p" 2>/dev/null || true
    done
    _i=0
    while [ "$_i" -lt 30 ]; do
        _left=""
        for _p in $_targets; do
            kill -0 "$_p" 2>/dev/null && _left="$_left $_p"
        done
        [ -z "$(echo "$_left" | tr -d ' ')" ] && break
        sleep 0.5
        _i=$((_i + 1))
    done
    # 15秒待っても残っているものだけ、番号を1つずつ指定して強く止める
    _left=""
    for _p in $_targets; do
        kill -0 "$_p" 2>/dev/null && _left="$_left $_p"
    done
    if [ -n "$(echo "$_left" | tr -d ' ')" ]; then
        echo "[掛け直し] 15秒では止まらなかったので、番号を指定して強く止めます:$_left"
        for _p in $_left; do
            kill -9 "$_p" 2>/dev/null || true
        done
        sleep 1
    fi

    # ここまでで落ちていなければ、黙って進まない
    _left=""
    for _p in $_targets; do
        kill -0 "$_p" 2>/dev/null && _left="$_left $_p"
    done
    if [ -n "$(echo "$_left" | tr -d ' ')" ]; then
        echo "" >&2
        echo "止められませんでした。いま上がっているものは次のとおりです。" >&2
        for _p in $_left; do
            echo "  番号 $_p : $(ps -o command= -p "$_p" 2>/dev/null || echo '(見えません)')" >&2
        done
        echo "" >&2
        echo "  手で止めるには:  kill $_left" >&2
        echo "  別の番号で上げるには:  ./launch.sh --port <別の番号>" >&2
        exit 1
    fi

    rm -f "$_pidfile"
    echo "[掛け直し] 止まりました。続けて起動します。"
}

# ------------------------------------------------------------
# 環境チェック
#   REPORT[] に測った中身を積み、BLOCKERS[] に「これが無いと動かない」を積む。
#   ここでは何も入れず、何も書き換えない。
# ------------------------------------------------------------
REPORT=()
BLOCKERS=()
WARNINGS=()
PY=""
PY_SRC=""
CONDA_BASE=""
CONDA_BIN=""

add_report() { REPORT+=("$1"); }
add_blocker() { BLOCKERS+=("$1"); }
add_warning() { WARNINGS+=("$1"); }

find_conda_base() {
    # conda は shell の関数として入っていることがあり、その関数は
    # 対話的でない shell では動かないことがある (中で呼ぶ __conda_exe が
    # 解決できず「permission denied」で落ちる)。
    # ∴ 場所を突き止めたら、以後は実体のファイルを直接叩く。
    if [ -n "${CONDA_EXE:-}" ] && [ -x "${CONDA_EXE}" ]; then
        CONDA_BIN="$CONDA_EXE"
        CONDA_BASE="$("$CONDA_BIN" info --base 2>/dev/null || true)"
    fi
    if [ -z "$CONDA_BASE" ] && command -v conda >/dev/null 2>&1; then
        CONDA_BASE="$(conda info --base 2>/dev/null || true)"
    fi
    if [ -z "$CONDA_BASE" ]; then
        for candidate in \
            "$HOME/miniforge3" \
            "$HOME/mambaforge" \
            "/opt/homebrew/Caskroom/miniforge/base" \
            "/opt/homebrew/Caskroom/mambaforge/base" \
            "$HOME/opt/anaconda3" \
            "$HOME/anaconda3" \
            "/usr/local/anaconda3"; do
            if [ -d "$candidate" ]; then
                CONDA_BASE="$candidate"
                break
            fi
        done
    fi
    # 実体のファイルを決める。これが無ければ conda は「使えない」と判定する。
    if [ -z "$CONDA_BIN" ] || [ ! -x "$CONDA_BIN" ]; then
        CONDA_BIN=""
        if [ -n "$CONDA_BASE" ] && [ -x "$CONDA_BASE/bin/conda" ]; then
            CONDA_BIN="$CONDA_BASE/bin/conda"
        elif command -v conda >/dev/null 2>&1 && conda --version >/dev/null 2>&1; then
            CONDA_BIN="$(command -v conda)"
        fi
    fi
}

# conda が「本当に使えるか」= 実体のファイルがあって、実際に版を答えること。
conda_usable() {
    [ -n "$CONDA_BIN" ] && [ -x "$CONDA_BIN" ] && "$CONDA_BIN" --version >/dev/null 2>&1
}

# その名前の conda 環境が既に在るか。
conda_env_exists() {
    conda_usable || return 1
    "$CONDA_BIN" env list 2>/dev/null \
        | awk '!/^#/ && NF { print $1 }' \
        | grep -qx -- "$1"
}

# 使う conda 環境の名前 (--env-name が優先。無ければ配布物専用の既定)
effective_env_name() {
    printf '%s' "${ENV_NAME:-$DIST_ENV_NAME}"
}

# 本体を動かす python を決める。
#   1) 配布物専用の conda 環境 (既定 cynovela-dist)  ← --setup が作る
#   2) 配布物専用の保存先 (.venv-cynovela)           ← --setup が作る
#   3) 共有の conda 環境 'cynovela'                  ← 読むだけ。書き換えない
#   4) システムの python3
resolve_python() {
    local _dist
    # N-1: --python で指定されたときは、それをそのまま使う。
    #   入口 (launch.sh) は選ばれた形 (conda / 配布物の中 / 自分で指定) の python を
    #   この指定で渡す。∴ 受け取り手が選んだとおりのもので立ち上がる。
    if [ -n "$CUSTOM_PY" ]; then
        PY="$CUSTOM_PY"
        PY_SRC="入口で選ばれた Python ($CUSTOM_PY)"
        return 0
    fi
    # --setup で選んだ直後は、その選択を上書きしない。
    # (選ばなかった方が先に見つかると、選んだ側と食い違うガイドを出してしまう。)
    if [ "$BASE_LOCKED" = "1" ] && [ -n "$PY" ]; then
        return 0
    fi
    _dist="$(effective_env_name)"
    if [ -n "$CONDA_BASE" ] && [ -x "$CONDA_BASE/envs/$_dist/bin/python" ]; then
        PY="$CONDA_BASE/envs/$_dist/bin/python"
        PY_SRC="この配布物専用の conda 環境 '$_dist'"
        return 0
    fi
    if [ -x "$VENV_DIR/bin/python" ]; then
        PY="$VENV_DIR/bin/python"
        PY_SRC="配布物専用の保存先 ($VENV_DIR)"
        return 0
    fi
    if [ -n "$CONDA_BASE" ] && [ -x "$CONDA_BASE/envs/$SHARED_ENV_NAME/bin/python" ]; then
        PY="$CONDA_BASE/envs/$SHARED_ENV_NAME/bin/python"
        PY_SRC="共有の conda 環境 '$SHARED_ENV_NAME' (読むだけ・書き換えません)"
        return 0
    fi
    if command -v python3 >/dev/null 2>&1; then
        PY="$(command -v python3)"
        PY_SRC="システムの python3"
        return 0
    fi
    PY=""
    PY_SRC="見つかりません"
    return 1
}

# requirements.txt と、選んだ python に入っているものを突き合わせる。
# 標準ライブラリだけで動く (部品が足りない python でも実行できる)。
missing_packages() {
    "$PY" - "$REQ_FILE" <<'PYEOF' 2>/dev/null || echo "PROBE_FAILED"
import re, sys
try:
    from importlib.metadata import version, PackageNotFoundError
except Exception:
    print("PROBE_FAILED"); raise SystemExit(0)

path = sys.argv[1]
missing, mismatch = [], []
name_re = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)")
try:
    lines = open(path, encoding="utf-8").read().splitlines()
except OSError:
    print("PROBE_FAILED"); raise SystemExit(0)

for raw in lines:
    line = re.split(r"\s+#", raw)[0].strip()
    if not line or line.startswith("#") or line.startswith("-"):
        continue
    if " @ " in line:
        name, op, want = line.split(" @ ")[0].strip(), "", ""
    else:
        m = name_re.match(line)
        if not m:
            continue
        name = m.group(1)
        rest = line[len(name):].strip()
        if rest.startswith("=="):
            op, want = "==", rest[2:].split(";")[0].strip()
        else:
            op, want = "", ""
    got = None
    for cand in (name, name.replace("_", "-"), name.replace("-", "_")):
        try:
            got = version(cand)
            break
        except PackageNotFoundError:
            continue
        except Exception:
            continue
    if got is None:
        missing.append(name)
    elif op == "==" and want and got != want:
        mismatch.append("%s 必要=%s 実際=%s" % (name, want, got))

print("MISSING\t" + ",".join(missing))
print("MISMATCH\t" + ",".join(mismatch))
PYEOF
}

run_probe() {
    add_report "== 調べた時刻 =="
    add_report "$(date '+%Y-%m-%d %H:%M:%S %Z')"
    add_report "== 保存先 =="
    add_report "$SCRIPT_DIR"

    # 1. 機械と OS
    add_report "== 機械と OS =="
    add_report "CPU 種別: $(uname -m) / $(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo '不明')"
    add_report "OS: $(sw_vers -productName 2>/dev/null || uname -s) $(sw_vers -productVersion 2>/dev/null || uname -r)"

    # 2. conda の有無と環境
    find_conda_base
    add_report "== conda =="
    if [ -n "$CONDA_BASE" ]; then
        add_report "conda の保存先: $CONDA_BASE"
        if [ -d "$CONDA_BASE/envs/$SHARED_ENV_NAME" ]; then
            add_report "共有の環境 '$SHARED_ENV_NAME': あり (読むだけ・書き換えません)"
        else
            add_report "共有の環境 '$SHARED_ENV_NAME': なし"
        fi
    else
        add_report "conda: なし"
    fi

    # 3. python の所在と版
    add_report "== python =="
    if resolve_python; then
        add_report "使う python: $PY"
        add_report "由来: $PY_SRC"
        add_report "版: $("$PY" -V 2>&1)"
    else
        add_report "使う python: 見つかりません"
        # R-5 (版7): ガイドを、いまこの機材に在るものに合わせて出し分ける。
        #   旧: 無条件に「conda (miniforge) を入れてから」と出していた。∴ conda が
        #   既に在る機材では、同じ書き出しの中で
        #     conda の保存先: /opt/homebrew/Caskroom/miniforge/base
        #     - python が見つかりません。conda (miniforge) を入れてから…
        #   と、在るものを入れろと言っていた (実測 20260817)。R-4 と同じ型である。
        #   ここで見ているのは「まだ用意していない」だけで、道具は揃っている。
        if [ -n "$CONDA_BASE" ]; then
            add_blocker "この配布物専用の環境がまだ作られていません。conda は見つかっています ($CONDA_BASE)。./launch.sh --setup を叩くと、専用の環境を作って起動できます。"
        elif command -v python3 >/dev/null 2>&1; then
            add_blocker "この配布物専用の保存先がまだ作られていません。python3 は見つかっています。./launch.sh --setup を叩くと、この配布物の中に保存先を作って起動できます。"
        else
            add_blocker "python が見つかりません。次のどちらかを入れてから ./launch.sh --setup を実行してください。conda (miniforge): https://github.com/conda-forge/miniforge/releases/latest  /  Python 3.12 以上: https://www.python.org/downloads/"
        fi
    fi
    # F-c: バックアップに使うのは動作要件 (3.12 以上) を満たす python だけ。有無ではなく版まで見る。
    # R-1: 使う python が決まった後で、バックアップに使う python を解き直す。
    #   解き直さないと、同じ書き出しの中で
    #     使う python      : .../envs/cynovela-dist/bin/python   版: Python 3.12.13
    #     バックアップに使う python: ありません (3.12 系が見つかりません)
    #   という食い違いが残る (M5 実測)。決まったものが要件を満たすなら、それをバックアップにも使う。
    ROOTS_PY="$(conf_pick_py "$SCRIPT_DIR" "${PY:-}" || true)"
    if [ -n "$ROOTS_PY" ]; then
        add_report "バックアップに使う python: $ROOTS_PY / $("$ROOTS_PY" -V 2>&1)"
    else
        add_report "バックアップに使う python: ありません (3.12 以上のものが見つかりません)"
        if [ -s "$INGEST_ROOTS_FILE" ]; then
            # R-2: これは起動を止める理由にならない。読めなくなるのは
            #   取り込み元のバックアップだけで、本体は動く。∴ 気をつけること へ置く。
            # R-4: いま失敗した入口をもう一度押せ、とは言わない。
            add_warning "3.12 以上の python が見つかりません。取り込み元のバックアップ (store/ingest-roots.json) を読めないため、足したフォルダは読み込まれません。起動そのものは止まりません。直すには ./launch.sh --setup を叩いてください (この配布物の中に python の保存先が作られます)。"
        fi
    fi

    # 4. venv で足りるか
    add_report "== venv (配布物専用の保存先) =="
    if [ -x "$VENV_DIR/bin/python" ]; then
        add_report "配布物専用の保存先: あり ($VENV_DIR)"
    else
        add_report "配布物専用の保存先: なし (--setup で作られます)"
    fi
    if [ -n "$PY" ] && "$PY" -c "import venv, ensurepip" >/dev/null 2>&1; then
        add_report "venv を作れるか: 作れる"
    else
        add_report "venv を作れるか: 作れない (ensurepip が無い)"
        [ "$MODE_SETUP" = "1" ] && add_blocker "この python では配布物専用の保存先を作れません (venv/ensurepip が無い)。conda (miniforge) を入れてください。"
    fi

    # 5. 必要な部品の有無と版差
    add_report "== 必要な部品 (requirements.txt) =="
    if [ ! -f "$REQ_FILE" ]; then
        add_report "requirements.txt: ありません"
        add_warning "requirements.txt がありません。部品の照合は行いませんでした。"
    elif [ -z "$PY" ]; then
        add_report "照合できません (python が無いため)"
    else
        _probe="$(missing_packages)"
        if [ "$_probe" = "PROBE_FAILED" ]; then
            add_report "照合できません (部品一覧の読み出しに失敗)"
            add_warning "部品の照合に失敗しました。"
        else
            _miss="$(printf '%s\n' "$_probe" | awk -F'\t' '$1=="MISSING"{print $2}')"
            _mism="$(printf '%s\n' "$_probe" | awk -F'\t' '$1=="MISMATCH"{print $2}')"
            if [ -n "$_miss" ]; then
                add_report "足りない部品: $_miss"
                add_blocker "部品が足りません: $_miss  → ./launch.sh --setup で、この配布物の中だけに入れて起動できます"
            else
                add_report "足りない部品: なし"
            fi
            if [ -n "$_mism" ]; then
                add_report "版が違う部品: $_mism"
                add_warning "版が違う部品があります: $_mism"
            else
                add_report "版が違う部品: なし"
            fi
        fi
        # マスキングに使う言語モデル (無くても起動はする。standard PII が正規表現に退く)
        if [ -n "$PY" ]; then
            for _m in ja_core_news_sm en_core_web_sm; do
                if "$PY" -c "import spacy; spacy.load('$_m')" >/dev/null 2>&1; then
                    add_report "spaCy モデル $_m: あり"
                else
                    add_report "spaCy モデル $_m: なし"
                    add_warning "spaCy モデル '$_m' がありません (standard PII が正規表現に退きます)。"
                fi
            done
        fi
    fi

    # 6. Podman と仮想機械 (この形態では使いませんが、環境のコピーとして記録します)
    add_report "== Podman / 仮想機械 =="
    if command -v podman >/dev/null 2>&1; then
        add_report "podman: $(podman --version 2>&1)"
        add_report "仮想機械: $(podman machine list --format '{{.Name}} {{.VMType}} {{.CPUs}}cpu {{.Memory}} {{.DiskSize}} running={{.Running}}' 2>/dev/null | tr '\n' ' ' || echo '一覧を取れません')"
    else
        add_report "podman: なし (この形態はホストで直接動かすため不要です)"
    fi

    # 7. 使うポートの空き
    add_report "== ポート =="
    if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
        add_report "ポート $PORT: 使用中"
        _own=0
        _pidfile="$DATA_DIR/server.pid"
        if [ -f "$_pidfile" ]; then
            _pid="$(cat "$_pidfile" 2>/dev/null || true)"
            if [ -n "$_pid" ] && kill -0 "$_pid" 2>/dev/null && ps -o command= -p "$_pid" 2>/dev/null | grep -q "server.py"; then
                _own=1
                add_report "使っているのは この配布物が前に起動したもの (PID $_pid) です"
            fi
        fi
        if [ "$_own" = "0" ]; then
            add_blocker "ポート $PORT を別のものが使っています。そちらを止めるか、./launch.sh --port <別の番号> を使ってください。"
        fi
    else
        add_report "ポート $PORT: 空き"
    fi

    # 8. モデル保存先の有無と中身
    #    探し先は本体と同じ5か所 (config.py の resolve_model_path と同じ順序)。
    #    この配布物の中の1か所だけを見ると、ホーム側の保存先にモデルがあっても
    #    「ありません」と言って止めてしまい、本体の判断と食い違う。
    add_report "== 埋め込みモデルの保存先 =="
    _model_snap=""
    for _cand in \
        "$SCRIPT_DIR/store/models/models--BAAI--bge-m3" \
        "$(dirname "$SCRIPT_DIR")/models--BAAI--bge-m3" \
        "$HOME/.cynovela/models/models--BAAI--bge-m3" \
        "$HOME/.cynovela/hf_cache/models--BAAI--bge-m3" \
        "$HOME/.cache/huggingface/hub/models--BAAI--bge-m3"; do
        [ -d "$_cand" ] || continue
        for _s in "$_cand"/snapshots/*/; do
            if [ -d "$_s" ] && [ -n "$(ls -A "$_s" 2>/dev/null || true)" ]; then
                _model_snap="$_s"
                break
            fi
        done
        [ -n "$_model_snap" ] && break
    done
    if [ -n "$_model_snap" ]; then
        add_report "bge-m3: あり ($_model_snap)"
        add_report "中身: $(ls "$_model_snap" 2>/dev/null | tr '\n' ' ')"
    else
        add_report "bge-m3: 5か所のどこにもありません (この配布物の中は $MODEL_DIR)"
        # 人が端末の前に居るときは、ここで止めない。止めると、この先で本体が出す
        # 「必要なモデルが見つかりません」の確認 (今すぐダウンロードして起動する /
        # 別のモードで起動する / やめる) へ届かなくなる。
        #
        # 聞ける相手が居ないとき (アイコンからの起動・手順書・試験) も、ここでは
        #   止めない。本体 (server.py) が非対話のときは確認を出さずにダウンロードへ進むように
        #   なったため ()、blocker で止めると軽量版が非対話で永遠に起動できない。
        #   ダウンロードに失敗したときは本体が exit 2 と進め方の名指しで知らせる。
        #   (旧 F-1 の blocker は、本体が入力の終わりで黙って落ちていた頃の塞ぎ)
        if [ ! -t 0 ] || [ "$NO_PROMPT" = "1" ]; then
            add_warning "埋め込みモデル bge-m3 が手元にありません。この起動の仕方では確認を出せないため、起動の中でダウンロードを試みます (インターネットにつなぎます)。先に自分で置く場合は SETUP-ACCELERATOR.md の手順で $MODEL_DIR/snapshots/<版>/ へ置いてください。"
        else
            add_warning "埋め込みモデル bge-m3 が手元にありません。このまま起動すると、ダウンロードするかどうかの確認が出ます。先に自分で置く場合は SETUP-ACCELERATOR.md の手順で $MODEL_DIR/snapshots/<版>/ へ置いてください。"
        fi
    fi

    # 9. 外の推論サーバへの到達
    add_report "== 回答を作る LLM への到達 =="
    _llm="$(conf_get_or llm base_url http://localhost:1234)"
    _code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 4 "${_llm}/v1/models" 2>/dev/null || true)"
    add_report "宛先 $_llm/v1/models: HTTP ${_code:-000}"
    if [ "$_code" != "200" ]; then
        add_warning "回答を作る LLM ($_llm) に届きません。取り込みと検索は動きますが、回答は作れません。画面の Settings で宛先を直せます。"
    fi

    # 10. 鍵の有無 (在るかどうかだけ。中身は読みません)
    add_report "== 金庫の鍵 =="
    if [ -f "$SCRIPT_DIR/store/secret.key" ]; then
        add_report "store/secret.key: あり (中身は読みません)"
    else
        add_report "store/secret.key: なし"
        add_warning "金庫の鍵がありません。起動時に新しく作られますが、同梱のデモ本文はその鍵では読めません。"
    fi

    # 11. ディスクの空き
    add_report "== ディスクの空き =="
    _avail_g="$(df -g "$SCRIPT_DIR" 2>/dev/null | awk 'NR==2{print $4}')"
    add_report "$(df -h "$SCRIPT_DIR" 2>/dev/null | tail -1)"
    if [ -n "$_avail_g" ] && [ "$_avail_g" -lt 2 ] 2>/dev/null; then
        add_blocker "ディスクの空きが ${_avail_g}GB しかありません。2GB 以上あけてください。"
    elif [ -n "$_avail_g" ] && [ "$_avail_g" -lt 10 ] 2>/dev/null; then
        add_warning "ディスクの空きが ${_avail_g}GB です。取り込みを行うなら 10GB 以上を勧めます。"
    fi
}

print_probe_result() {
    printf '%s\n' "${REPORT[@]}"
    echo ""
    if [ "${#WARNINGS[@]}" -gt 0 ]; then
        echo "== 気をつけること (止まりはしません) =="
        printf '  - %s\n' "${WARNINGS[@]}"
        echo ""
    fi
    if [ "${#BLOCKERS[@]}" -gt 0 ]; then
        echo "== 足りないもの (これが無いと動きません) =="
        printf '  - %s\n' "${BLOCKERS[@]}"
    else
        echo "== 足りないもの: ありません =="
    fi
}

# ------------------------------------------------------------
# 入れている間の進み具合 (B3)
#   全体で何件入れるかを先に出し、いま何件目かを1行で書き換える。
#   --verbose のとき、および画面が出せないとき (端末でない) は素の出力へ戻す。
#   pip の解き手はそのまま使う (1件ずつ入れると依存の解決が変わってしまうため)。
# ------------------------------------------------------------
count_requirements() {
    [ -f "$REQ_FILE" ] || { printf '0'; return; }
    grep -cvE '^[[:space:]]*(#|$)' "$REQ_FILE" 2>/dev/null || printf '0'
}

count_env_deps() {
    [ -f "$ENV_FILE" ] || { printf '0'; return; }
    grep -cE '^[[:space:]]+- ' "$ENV_FILE" 2>/dev/null || printf '0'
}

run_with_progress() {
    local total="$1"; shift
    local rc=0
    if [ "$VERBOSE" = "1" ] || [ ! -t 1 ]; then
        # 画面が出せない・素の出力が要る場合は、そのまま流す。
        "$@"
        return $?
    fi
    local n=0 line name mark
    "$@" 2>&1 | {
        # 付随して入るもの (依存の依存) があるため、実際に入る数は
        # 指定の数より多くなる。∴ 数え上げが指定の数を超えたら、
        # 分母を出すのをやめて「N 件目」に切り替える。
        # (超えたまま [177/39] と出すと、壊れているように見える。)
        while IFS= read -r line; do
            case "$line" in
                "Downloading and Extracting Packages"*|"Collecting package metadata"*)
                    # conda の見出し行。部品名ではないので数えない。
                    ;;
                Collecting*|"Requirement already satisfied:"*|"Building wheel for"*)
                    name="${line#Collecting }"
                    name="${name#Requirement already satisfied: }"
                    name="${name#Building wheel for }"
                    name="${name%% *}"; name="${name%%=*}"; name="${name%%[<>!;,]*}"
                    n=$((n + 1))
                    if [ "$total" -gt 0 ] && [ "$n" -le "$total" ]; then
                        mark="[$n/$total]"
                    else
                        mark="[$n 件目]"
                    fi
                    printf '\r\033[K  %s %s を入れています' "$mark" "$name"
                    ;;
                Downloading*)
                    # 大きい部品はダウンロードの進みを見せる
                    printf '\r\033[K  受け取り中 %s' "${line#Downloading }"
                    ;;
                ERROR*|error:*|"CondaError"*|"ResolvePackageNotFound"*)
                    printf '\r\033[K'
                    printf '  %s\n' "$line"
                    ;;
            esac
        done
        printf '\r\033[K'
    }
    rc=${PIPESTATUS[0]}
    return "$rc"
}

# ------------------------------------------------------------
# --setup の実行エンジン選び (B1・B2)
#   まず conda を見に行く。使えるなら専用の conda 環境を新しく作る。
#   使えないときだけ、この配布物の中の保存先へ倒す。
#   選ぶところは番号で選ばせる。--base があれば聞かない。
#   何も答えなかったときは「何もしない」に倒す (勝手に進めない)。
# ------------------------------------------------------------
choose_base() {
    find_conda_base
    local dist ans
    dist="$(effective_env_name)"

    # --base で先に決まっているなら聞かない (プロ向け・非対話の道)
    if [ -n "$BASE_CHOICE" ]; then
        echo "  --base $BASE_CHOICE で指定されています。聞かずに進みます。"
        return 0
    fi

    # 画面から選べない (端末でない) 場合は、勝手に進めずに終わる
    if [ ! -t 0 ]; then
        echo ""
        echo "  画面から選べないため、何もしませんでした。"
        echo "  引数で指定して、もう一度実行してください:"
        if conda_usable; then
            echo "    ./launch.sh --setup --base conda    (conda に専用の環境を作る)"
        fi
        echo "    ./launch.sh --setup --base venv     (この配布物の中だけに作る)"
        BASE_CHOICE="none"
        return 0
    fi

    # M-4 (決定 14-2・14-3・14-4・追記274 274-4):
    #   conda を先に見て、選択肢と「何がどこにどれだけ残るか・後で消す手順」を
    #   ターミナルへ出して選ばせる。数値は実測 (conda 環境 3.9GB = 同じ定義の環境の
    #   実測・venv 2.2GB = requirements.txt から実作成した実測・2026-08-08)。
    #   共有の conda 環境へは書かない (決定 14-5・setup_conda 側で遮断)。
    while true; do
        echo ""
        if conda_usable; then
            echo "どの形で動かしますか。"
            echo "  1) conda に専用の環境を作る"
            echo "     残るもの: conda の環境1つ（約 3.9 GB）"
            echo "     消し方  : bash uninstall.sh"
            echo "  2) この配布物の中だけに作る（Mac を汚しません）"
            echo "     残るもの: このフォルダの中に約 2.2 GB"
            echo "     消し方  : bash uninstall.sh"
            echo "  3) やめる"
            printf '番号を入れてください [1/2/3]: '
        else
            echo "conda が見つかりませんでした。"
            echo "どの形で動かしますか。"
            echo "  2) この配布物の中だけに作る（Mac を汚しません）"
            echo "     残るもの: このフォルダの中に約 2.2 GB"
            echo "     消し方  : bash uninstall.sh"
            echo "  3) やめる"
            printf '番号を入れてください [2/3]: '
        fi
        if ! IFS= read -r ans; then
            # 入力が閉じた (EOF)。聞き続けられないので「やめる」に倒す。
            echo ""
            echo "  入力が閉じたため、やめました。何も作っていません。"
            BASE_CHOICE="none"
            return 0
        fi
        case "$ans" in
            1)
                if conda_usable; then
                    BASE_CHOICE="conda"
                    return 0
                fi
                echo "  → 1) は選べません。conda が見つかりませんでした。"
                ;;
            2)
                BASE_CHOICE="venv"
                return 0
                ;;
            3)
                BASE_CHOICE="none"
                return 0
                ;;
            *)
                echo "  → 番号を入れてください。"
                ;;
        esac
    done
}

# 専用の conda 環境を新しく作る。既に在る名前へは書き足さない。
setup_conda() {
    local dist total
    dist="$(effective_env_name)"

    if [ "$dist" = "$SHARED_ENV_NAME" ]; then
        echo "❌ '$SHARED_ENV_NAME' は共有の環境の名前です。ここへは書き込みません。"
        echo "   別の名前を指定してください: ./launch.sh --setup --base conda --env-name <名前>"
        exit 1
    fi
    if conda_env_exists "$dist"; then
        echo "❌ conda 環境 '$dist' は既にあります。既に在る環境へは書き足しません。"
        echo "   別の名前を指定するか、その環境を自分で消してから、もう一度実行してください:"
        echo "     ./launch.sh --setup --base conda --env-name <別の名前>"
        exit 1
    fi
    if [ ! -f "$ENV_FILE" ]; then
        echo "❌ 環境の定義 (environment.yml) が見つかりません: $ENV_FILE"
        exit 1
    fi

    total="$(count_env_deps)"
    echo ""
    echo "  conda 環境 '$dist' を新しく作ります。"
    echo "  定義: $ENV_FILE"
    echo "  入れるもの: $total 件"
    echo "  共有の環境 '$SHARED_ENV_NAME' には書き込みません。"
    echo ""
    # -n で environment.yml の中の名前 (cynovela) を必ず上書きする。
    # これを付けないと共有の環境の名前で作られてしまう。
    if ! run_with_progress "$total" "$CONDA_BIN" env create -f "$ENV_FILE" -n "$dist" --yes; then
        echo "❌ conda 環境を作れませんでした。素の出力を見るには --verbose を付けてください。"
        exit 1
    fi
    echo "  作りました: conda 環境 '$dist'"

    PY="$CONDA_BASE/envs/$dist/bin/python"
    PY_SRC="この配布物専用の conda 環境 '$dist'"
    BASE_LOCKED=1
    if [ ! -x "$PY" ]; then
        echo "❌ 作ったはずの conda 環境に python が見つかりません: $PY"
        exit 1
    fi
    install_requirements
}

# venv を作れる python を探す (新しい版から順に。順序と書き方は falcon 側 tools/mas-phase.sh の原文と同じ)
venv_base_python() {
    # R-6 (版7): 要件は 3.12 以上である (pyproject.toml requires-python
    #   = ">=3.12" / environment.yml が python=3.12.13 を固定 / conf_pick_py も 3.12 以上)。
    #   旧: ここだけ 3.10 以上を通しており、「3.10 以上が見つかりません」と言いながら
    #   同じ画面で「3.12 を入れてください」と示す食い違いが出ていた (実測 20260817)。
    #   ∴ 判定とガイドを、宣言した要件 (3.12 以上) に揃える。
    #   版は名前で決めつけず、その python 自身に答えさせる。
    local c
    for c in python3.13 python3.12; do
        if command -v "$c" >/dev/null 2>&1 && _conf_py_meets "$(command -v "$c")"; then
            command -v "$c"; return 0
        fi
    done
    # 版のついた名前が無いときは python3 の版を見る
    if command -v python3 >/dev/null 2>&1 && _conf_py_meets "$(command -v python3)"; then
        command -v python3; return 0
    fi
    return 1
}

# この配布物の中だけに保存先を作る。
setup_venv() {
    local base_py=""
    echo ""
    echo "  この配布物の中に保存先を作ります: $VENV_DIR"
    echo "  共有の conda 環境 '$SHARED_ENV_NAME' には書き込みません。"
    base_py="$(venv_base_python || true)"
    if [ -n "$base_py" ]; then
        echo "  使う Python: $base_py ($("$base_py" -V 2>&1))"
    else
        echo "❌ 3.12 以上の python3 が見つかりませんでした。"
        echo "   入れ方: https://www.python.org/downloads/ から 3.12 以上を入れてください"
        echo "   または conda (miniforge) を入れて ./launch.sh --setup --base conda を使ってください"
        exit 1
    fi

    if [ ! -x "$VENV_DIR/bin/python" ]; then
        "$base_py" -m venv "$VENV_DIR"
        echo "  作りました: $VENV_DIR"
    else
        echo "  既にあります: $VENV_DIR"
    fi

    PY="$VENV_DIR/bin/python"
    PY_SRC="この配布物の中の保存先 ($VENV_DIR)"
    BASE_LOCKED=1
    install_requirements
}

# 足りない部品を入れる (実行エンジンの種類によらず共通)
install_requirements() {
    [ -f "$REQ_FILE" ] || return 0
    local probe miss mism total
    probe="$(missing_packages)"
    miss="$(printf '%s\n' "$probe" | awk -F'\t' '$1=="MISSING"{print $2}')"
    mism="$(printf '%s\n' "$probe" | awk -F'\t' '$1=="MISMATCH"{print $2}')"
    # R-3: 「足りない部品」だけを見て止めない。版が違う部品も入れ直しの理由になる。
    #   conda の道は environment.yml の pip 層で部品の名前が一通り揃うため、ここが
    #   MISSING だけを見ていると 2段目 (pip install -r requirements.txt) が一度も走らず、
    #   requirements.txt が求める版に届かないまま終わっていた (M5 実測で「版が違う部品」19 件)。
    if [ "$probe" = "PROBE_FAILED" ] || { [ -z "$miss" ] && [ -z "$mism" ]; }; then
        echo "  足りない部品も、版が違う部品もありません。何も入れませんでした。"
        return 0
    fi
    if [ -z "$miss" ]; then
        echo "  足りない部品はありませんが、版が違う部品があります: $mism"
        echo "  requirements.txt が求める版へ揃えます。"
    fi
    total="$(count_requirements)"
    echo ""
    echo "  足りない部品を入れます (指定は $total 件です)。"
    echo "  付随して入るものがあるため、実際に入る数はこれより多くなります。"
    run_with_progress "$total" "$PY" -m pip install --upgrade pip || true
    if ! run_with_progress "$total" "$PY" -m pip install -r "$REQ_FILE"; then
        echo "❌ 部品を入れられませんでした。素の出力を見るには --verbose を付けてください。"
        exit 1
    fi
    echo "  入れ終わりました。"
}

do_setup() {
    echo ""
    echo "[--setup] python を用意する場所を選んでから、足りないものを入れます。"
    echo "          共有の conda 環境 '$SHARED_ENV_NAME' には書き込みません。"
    choose_base
    case "$BASE_CHOICE" in
        conda)
            find_conda_base
            if ! conda_usable; then
                echo "❌ conda が使えません。--base venv を使ってください。"
                exit 1
            fi
            setup_conda
            ;;
        venv)
            setup_venv
            ;;
        none)
            echo ""
            echo "  何もしませんでした。何も作っていません。"
            echo ""
            exit 0
            ;;
    esac
    echo ""
}

# ------------------------------------------------------------
# 要るものを枠で囲って出す (B4)
#   入れ終わったときと、起動したときの両方で出す。
#   パスワードの実値はここへ印字しない。同梱のバックアップの場所を示す。
# ------------------------------------------------------------
print_next_steps() {
    local where="${1:-setup}"
    echo ""
    echo "┌──────────────────────────────────────────────────────────────┐"
    echo "│  Cynovela — 使いはじめるのに要るもの                          │"
    echo "└──────────────────────────────────────────────────────────────┘"
    echo ""
    echo "  ■ 開く場所"
    echo "      http://localhost:$PORT"
    echo ""
    echo "  ■ 入り方"
    echo "      管理者の利用者名: cynovela"
    echo "      閲覧者の利用者名: demo"
    echo "      最初のパスワードは、同梱の STARTUP.md の「ログイン」の節に書いてあります。"
    echo "      (この画面には印字しません。別便で受け取るファイルはありません。)"
    echo "      管理者は初回にパスワードの変更を求められます。"
    echo ""
    echo "  ■ 気をつけること"
    echo "      1. 起動すると、この配布物の中身が書き換わります。"
    echo "         (記録・鍵・記録のコンテナが $SCRIPT_DIR/store の下に作られます)"
    echo "      2. 鍵はこの機材で新しく作られます。他の機材で作られた鍵とは別のものです。"
    echo "         ∴ 他の機材で取り込んだ中身は、この機材では読めません。"
    echo "      3. 止め方: bash stop.sh"
    echo "      4. クラウド同期 (iCloud Drive・Dropbox・OneDrive・Google Drive) の下に"
    echo "         置くと、部品一式がまるごと同期に乗ります。同期の対象外の場所へ"
    echo "         置くことを勧めます。"
    echo ""
    if [ "$where" = "setup" ]; then
        echo "  ■ 次にすること"
        echo "      起動するには:  ./launch.sh --demo"
        echo "      --demo は同梱のダミー資料が載った状態で起動します。"
        echo "      引数なしの ./launch.sh は、中身が空の本番の状態で起動します。"
        echo ""
    fi
}

# ------------------------------------------------------------
# 本体の起動 (旧 start.sh をここへ吸収)
# ------------------------------------------------------------
start_app() {
    # B5: 前に上がっていたものは、点検より前の stop_previous で落とし済み。
    #   (従来はここで stop.sh を呼んでいたが、点検のポート判定がそれより先に走るため
    #    「別のものが使っています」で止まり、ここまで来られないことがあった。)

    # F-5: 証明書の指し先を外す処理は、本編の頭 (_drop_stale_ssl_cert_file) へ
    #   移した。ここに置いていたときは --setup の道が start_app を通らないため、
    #   部品を入れる pip が実在しない証明書を指したまま走っていた。

    cd "$SCRIPT_DIR"
    echo ""
    echo "============================================"
    echo " Cynovela を起動します (http://localhost:$PORT)"
    echo " 使う python: $PY"
    echo " 由来: $PY_SRC"
    echo " 停止するには: bash stop.sh"
    if [ "$DEFAULT_INGEST_USED" = "1" ]; then
        echo "--------------------------------------------"
        echo " 取り込み元が1件も足されていなかったので、"
        echo " この配布物の中のダミー資料を取り込み元にしました:"
        echo "   $DEFAULT_INGEST_DIR"
        echo " 自分の資料を足すには: 画面の 設定 → 取り込み元"
        echo "                    または ./launch.sh --add"
    elif [ "$NO_ROOTS_AND_NO_DEFAULT" = "1" ]; then
        echo "--------------------------------------------"
        echo " 取り込み元がまだ1件もありません。"
        echo " 足し方は次の2通りです:"
        echo "   画面から : 設定 → 取り込み元 → 「取り込み元を足す」"
        echo "   ターミナルから : ./launch.sh --add        (フォルダを選ぶ画面が出ます)"
        echo "              ./launch.sh --add-path <パス>"
    fi
    echo "============================================"
    print_next_steps launch
    exec "$PY" server.py ${APP_ARGS[@]+"${APP_ARGS[@]}"}
}

# ------------------------------------------------------------
# 本編
# ------------------------------------------------------------
# F-5: 証明書の指し先を、何かを取りに行くより先に外す。
#   conda 環境では SSL_CERT_FILE が実在しない証明書を指すことがあり、証明書を使う処理が
#   まとめて失敗する (旧 start.sh:16)。従来これを外していたのは start_app の中だったが、
#   --setup の道は do_setup を呼んで exit するため start_app を通らない。
#   ∴ 部品を入れる pip が、実在しない指し先のまま走っていた (無言で失敗しうる)。
#   本編の頭で 1 度だけ外し、以後どの道 (--setup / --check / 起動) でも同じ状態にする。
#   falcon 側はダウンロードの直前で同じことをしており、順序はもともと正しい。
_drop_stale_ssl_cert_file() {
    if [ -n "${SSL_CERT_FILE:-}" ]; then
        echo "[cert] SSL_CERT_FILE を外します (指し先: $SSL_CERT_FILE)"
        unset SSL_CERT_FILE
    fi
}
_drop_stale_ssl_cert_file

echo "============================================"
echo " Cynovela"
echo " 保存先: $SCRIPT_DIR"
echo "============================================"

if [ "$MODE_CHECK" = "1" ] && [ "$MODE_SETUP" = "1" ]; then
    echo "❌ --check と --setup は同時に使えません。--check は読み取りだけ、--setup は入れてから起動します。"
    exit 2
fi

# §7-5-2: 引数が1つも無く、人が端末から叩いたときだけ番号で聞く。
#   非対話 (手順書・試験・アイコンからの起動) では聞かず、従来どおり既定で進む。
if [ "$ARGC_AT_START" = "0" ] && [ -t 0 ] && [ "$NO_PROMPT" != "1" ]; then
    run_interactive
fi

# --setup は「入れる」ので、先に一度測ってから入れ、入れた結果でもう一度測る。
if [ "$MODE_SETUP" = "1" ]; then
    find_conda_base
    do_setup
    run_probe

    # 版が違う部品は知らせるだけで止めない (B6)
    if [ "${#WARNINGS[@]}" -gt 0 ]; then
        echo ""
        echo "== 気をつけること (止まりはしません) =="
        printf '  - %s\n' "${WARNINGS[@]}"
    fi
    if [ "${#BLOCKERS[@]}" -gt 0 ]; then
        echo ""
        echo "== まだ足りないもの =="
        printf '  - %s\n' "${BLOCKERS[@]}"
    fi

    echo ""
    echo "[--setup] 入れ終わりました。ここでは起動しません。"
    echo "          由来: $PY_SRC"
    echo "          使う python: $PY"
    print_next_steps setup
    exit 0
fi

# B5: 点検より先に落とす。
#   ポートの空きを見る点検 (run_probe) が先だと、前に上げたものが居るだけで
#   「別のものが使っています」と判定されて起動しないまま終わっていた。
#   --check は読み取りだけ、--setup は入れるだけなので、どちらでも落とさない。
if [ "$MODE_CHECK" != "1" ] && [ "$MODE_SETUP" != "1" ]; then
    stop_previous
fi

run_probe

if [ "$MODE_CHECK" = "1" ]; then
    mkdir -p "$(dirname "$REPORT_FILE")"
    print_probe_result > "$REPORT_FILE"
    echo ""
    echo "[--check] 読み取りだけで調べました。何も入れず、何も起動していません。"
    echo "[--check] 結果: $REPORT_FILE"
    echo ""
    cat "$REPORT_FILE"
    exit 0
fi

if [ "${#WARNINGS[@]}" -gt 0 ]; then
    echo ""
    echo "== 気をつけること (止まりはしません) =="
    printf '  - %s\n' "${WARNINGS[@]}"
fi

if [ "${#BLOCKERS[@]}" -gt 0 ]; then
    echo ""
    echo "== 足りないものがあるので起動しません =="
    printf '  - %s\n' "${BLOCKERS[@]}"
    echo ""
    echo "  詳しく見る:   ./launch.sh --check   (読み取りだけで調べて $REPORT_FILE へ書きます)"
    echo "  入れて起動:   ./launch.sh --setup   (この配布物の中だけに入れます)"
    exit 1
fi

start_app
