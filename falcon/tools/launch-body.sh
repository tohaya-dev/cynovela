#!/bin/bash
# ============================================================
#  Cynovela 入口 (entry-unify-20260802 / DD-CYN-0020 S-1〜S-4)
#
#  受け取り手が実行するのはこの1本だけです。
#  この系統は「コンテナ (コンテナ) で動かす形」の1本道です。ホストで直接動かす道は
#  持ちません (start.sh は廃止しました)。中で使う組み立て用のスクリプトは
#  deploy/container/run-container.sh へ降ろし、この入口からだけ呼びます。
#
#  使い方:
#    ./launch.sh                 本番 (空のデータベース) で起動する
#    ./launch.sh --demo          同梱のダミー資料が載ったデモで起動する
#    ./launch.sh --local-only    公開を自マシン内だけに絞る
#    ./launch.sh --port <番号>   ホスト側のポートを変える (既定 8801)
#    ./launch.sh <モード>        text|lite|lite-en (既定 text)
#
#    ./launch.sh --check         起動せずに動く条件だけを調べ、結果を1本のファイルへ書く
#    ./launch.sh --setup         足りないもののうち、この配布物の中で用意できるものを
#                                用意してから起動する
#
#    ./launch.sh --add                     取り込み元にするフォルダを選ぶ
#    ./launch.sh --add-path <パス>         取り込み元を足す
#    ./launch.sh --list                    取り込み元の一覧
#    ./launch.sh --remove <中の名前>       取り込み元を外す
#    ./launch.sh --ingest <パス>           取り込み元を足してから起動する (複数指定可)
#    ./launch.sh --sync-labels <トークン>  取り込み元の表示名を動いている本体へ合わせる
#
#  停止: podman stop <コンテナの名前>  (名前は cynovela.yaml の container: の name: に書いてある)
#
#  環境チェックの3つのモード:
#    既定    足りないものを並べて止まる (何も入れない・何も書き換えない)
#    --setup この配布物の中だけで用意できるもの (鍵の保存先など) を用意して起動まで進む
#    --check 読み取りだけで同じ検査を回し、結果を store/env-check.txt へ書いて終わる
#
#  共有の conda 環境 'cynovela' は使いません。書き込みもしません。
#  (この形態の部品はすべてコンテナの中に入っています。)
#
#  実行エンジンの選択について (DD-CYN-0031):
#    この形態には「選ぶ実行エンジン」がありません。本体を動かす python はコンテナ (イメージ) の
#    中に入っており、ホスト側の python も conda も使いません。
#    ∴ 他の2系統にある --base / --env-name (conda 環境を作るか、配布物の中に作るか) は
#      この形態には置きません。置いても選ぶものが無く、嘘の選択肢になるためです。
#    この形態の --setup がホスト側に用意するのは、金庫の鍵の保存先だけです。
# ============================================================
set -e

# DD-CYN-0069 M-5: 本体は tools/ の下の部品になった (決定 12-2)。保存先の基準は配布物のルートディレクトリのまま。
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTAINER_PART="$SCRIPT_DIR/deploy/container/run-container.sh"
REPORT_FILE="$SCRIPT_DIR/store/env-check.txt"
INGEST_ROOTS_HELPER="$SCRIPT_DIR/scripts/ingest_roots.py"
INGEST_ROOTS_FILE="$SCRIPT_DIR/store/ingest-roots.json"
KEYFILE="$SCRIPT_DIR/keys/secret.key"

MODE_CHECK=0
MODE_SETUP=0
# DD-CYN-0053: 決めごとは cynovela.yaml 1本から読む。環境変数では受け取らない。
CONF_REPO="$SCRIPT_DIR"
. "$SCRIPT_DIR/tools/conf.sh"
# DD-CYN-0107 F-c: 取り込み元のバックアップは、動作要件 (3.12 以上) を満たす python でのみ読み書きする。
#   素の python3 (版の検査なし) へは倒れない。満たすものが無いときは理由と、その場で効く
#   操作を出す。
# DD-CYN-0117 R-1: 版は名前で当てず、conf_pick_py がその python 自身に答えさせる。
#   ∴ 名前に版の付かない python3 も、中身が 3.12 以上なら候補に入る。
ROOTS_PY="$(conf_pick_py "$SCRIPT_DIR" || true)"
_roots_py() {
    if [ -z "$ROOTS_PY" ]; then
        # DD-CYN-0117 R-4: いま失敗した入口 (Cynovela-start.command は ./launch.sh を
        #   呼ぶだけの同じ道) をもう一度押せ、とは言わない。この形態はコンテナで動くため、
        #   押し直しても Mac 側に python は作られない。∴ その場で効く操作だけを出す。
        echo "エラー: 3.12 以上の python がこの Mac にありません。取り込み元のバックアップ (store/ingest-roots.json) を扱えません。" >&2
        echo "       直し方: https://www.python.org/downloads/ から 3.12 以上を入れてください。" >&2
        echo "       コンテナの中の部品はこれとは別です。コンテナを作り直す必要はありません。" >&2
        return 1
    fi
    "$ROOTS_PY" "$@"
}
HOSTPORT_DEFAULT="$(conf_get_num server port 8801)"
HOSTPORT="$HOSTPORT_DEFAULT"
CNAME_DEFAULT="$(conf_get_or container name "$CONF_DEFAULT_CNAME")"
# DD-CYN-0074 Q-1: モデルの保存先は cynovela.yaml の paths: の models_dir: から読む。
#   空なら従来どおり、この配布物の中の store/models を使う。
#   コンテナへ渡す元も同じ1つの値である (deploy/container/run-container.sh も同じ行を読む)。
#   ∴ ここで「あり」と言ったのにコンテナの中から見えない、ということは起きない。
MODEL_ROOT="$(conf_get paths models_dir)"
if [ -z "$MODEL_ROOT" ]; then
    MODEL_ROOT="$SCRIPT_DIR/store/models"
else
    case "$MODEL_ROOT" in "~/"*) MODEL_ROOT="$HOME/${MODEL_ROOT#\~/}" ;; esac
fi
MODEL_DIR="$MODEL_ROOT/models--BAAI--bge-m3"
MODEL_MISSING=0
NO_PROMPT=0
FETCH_MODEL=0
PART_ARGS=()

# ---------- コンテナの実行エンジン (実行体) の解決 (DD-CYN-0048) ----------
#   決める順: ①設定/指定での明示 (在れば探索しない) ②podman → docker の探索。
#   探索は 受け継いだ PATH → ログインシェル → 決まった保存先 の3段。
#   採った実行体は store/engine-bin/podman の橋渡しに置き、PATH の先頭に足す
#   (組み立て・停止のスクリプトは podman の名前で呼ぶため)。
#   tools/launcher-app/launcher-core.sh 側と同一の実装を保つこと。
ENGINE_PATH=""; ENGINE_NAME=""
_engine_find_one() {  # $1=名前 → 絶対パスを出力
    # 自分が置いた橋渡し (store/engine-bin) を候補に拾うと自分自身を呼ぶ輪になるため必ず除く
    local p d _shimdir
    _shimdir="$SCRIPT_DIR/store/engine-bin"
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
        # Docker・自分で指定は、入口 (launch.sh) の選択で container.engine /
        # engine_command に書かれてから、上の明示指定の道で使われる。
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
engine_activate() {  # 橋渡しを置き、PATH の先頭に足し、起動の記録へ1行残す
    local bindir="$SCRIPT_DIR/store/engine-bin"
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
    echo "[engine] 使うもの: $ENGINE_NAME ($ENGINE_PATH)"
}

# DD-CYN-0037 §7-5-3: ヘルプは2段。
#   先に出るのは「受け取り手が使うもの」だけ。試験・開発用は --help-all の下へ隔離する。
#   隠すだけで、名前も挙動も変えない (外から叩いている手順書と記録が壊れるため)。
usage() {
    cat <<'USAGE'
Cynovela 入口 — 受け取り手が叩くのはこの1本だけです。
この系統はコンテナ (コンテナ) で動きます。

● 何も付けないとき
  ./launch.sh                     聞かれたことに番号で答えるだけで起動します。
                                  (何を読ませるか)

● 番号で答えずに、はじめから決めて起動する
  ./launch.sh --demo              同梱のダミー資料が載った状態で起動します。
  ./launch.sh --add               読み込むフォルダを選ぶ画面を出して足します。
  ./launch.sh --list              いま足してあるフォルダを一覧で出します。
  ./launch.sh --remove <名前>     足したフォルダを外します (名前は --list に出るもの)。
                                  ※ 画面でも 設定 → 取り込み元 から見る・外せます。
                                  ※ この系統はコンテナで動くため、足したものが読めるように
                                    なるのは、もう一度 ./launch.sh を叩いたあとです。

● 入れる / 点検する
  ./launch.sh --setup             この配布物の中で用意できるものを用意します。
  ./launch.sh --check             起動せず、動く条件だけを調べて1本のファイルへ書きます。

● そのほか
  ./launch.sh --port <番号>       開く番号を変えます (既定 8801)。
                                  何も付けないときは、空いている番号を自分で選びます。
  ./launch.sh --local-only        開く先を自分のマシンの中だけに絞ります。
  ./launch.sh --engine <値>       コンテナに使う実行ファイルを指定します (名前または絶対パス)。
                                  同じ意味の設定: cynovela.yaml の container: の engine:
  ./launch.sh --engine-command <値>
                                  起動に使うコマンドそのものを差し替えます (既定は空)。
                                  同じ意味の設定: cynovela.yaml の container: の engine_command:
  bash stop.sh                    止めます (消しません)。

● 開く場所と入り方
  開く場所 : http://127.0.0.1:8801   (--port を使ったときはその番号)
  入り方   : 管理者 cynovela / 閲覧者 demo
             最初のパスワードは同梱の STARTUP.md の「ログイン」の節にあります。
             管理者は最初に入ったときにパスワードの変更を求められます。
             変え終わるまで管理の操作は通りません。

この系統には選ぶ実行エンジンがありません (本体を動かす python はコンテナの中にあり、
ホスト側の python も conda も使いません)。

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
  ./launch.sh --sync-labels <トークン>
                                  取り込み元の表示名を、動いている本体へ合わせます。
  ./launch.sh <モード>            text|lite|lite-en (既定 text)。
                                  読み取りの精度は変わりません (構成の説明と同じ)。
USAGE_ALL
}

# 知らない指定を渡されたときは、黙って落ちずにヘルプを出す (DD-CYN-0032 B2)。
KNOWN_PART_FLAGS=" --demo --local-only "
KNOWN_PART_WORDS=" full text lite lite-en minimal "
unknown_arg() {
    echo "知らない指定です: $1" >&2
    echo "" >&2
    usage >&2
    exit 2
}

# ------------------------------------------------------------
# 引数の振り分け
#   取り込み元の管理引数はここで受ける (以前は deploy/container/run-container.sh が
#   受けていた。受け取り手が2本のスクリプトを使い分ける形をやめる)。
# ------------------------------------------------------------
# DD-CYN-0037 §7-5-2: 引数が1つも無いときは、番号で答えるだけで進める形にする。
ARGC_AT_START=$#

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
        --port)
            if [ -z "${2:-}" ]; then
                echo "使い方: ./launch.sh --port <番号>"
                exit 2
            fi
            HOSTPORT="$2"
            shift
            ;;
        --engine)
            if [ -z "${2:-}" ]; then
                echo "使い方: ./launch.sh --engine <名前または絶対パス>"
                exit 2
            fi
            conf_set container engine "$2" || { echo "設定を書けませんでした"; exit 2; }
            echo "設定に覚えました: container.engine=$2"
            shift
            ;;
        --engine-command)
            if [ -z "${2:-}" ]; then
                echo "使い方: ./launch.sh --engine-command <コマンド>"
                exit 2
            fi
            conf_set container engine_command "$2" || { echo "設定を書けませんでした"; exit 2; }
            echo "設定に覚えました: container.engine_command=$2"
            shift
            ;;
        --add-path)
            if [ -z "${2:-}" ]; then
                echo "使い方: ./launch.sh --add-path <フォルダのパス>"
                exit 2
            fi
            NAME="$(_roots_py "$INGEST_ROOTS_HELPER" --file "$INGEST_ROOTS_FILE" add "$2")"
            echo "取り込み元を追加しました (中の名前: $NAME / コンテナの中では /app/ingest/$NAME)"
            echo "反映には起動し直し (./launch.sh) が必要です"
            exit 0
            ;;
        --add)
            SEL="$(osascript -e 'POSIX path of (choose folder with prompt "取り込み元にするフォルダを選んでください")')" || {
                echo "フォルダ選択がキャンセルされました"
                exit 1
            }
            NAME="$(_roots_py "$INGEST_ROOTS_HELPER" --file "$INGEST_ROOTS_FILE" add "$SEL")"
            echo "取り込み元を追加しました (中の名前: $NAME / コンテナの中では /app/ingest/$NAME)"
            echo "反映には起動し直し (./launch.sh) が必要です"
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
            echo "反映には起動し直し (./launch.sh) が必要です"
            exit 0
            ;;
        --sync-labels)
            if [ -z "${2:-}" ]; then
                echo "使い方: ./launch.sh --sync-labels <ログインで得たトークン>"
                exit 2
            fi
            bash "$CONTAINER_PART" --from-entry --hostport "$HOSTPORT" --sync-labels "$2"
            exit $?
            ;;
        --ingest)
            if [ -z "${2:-}" ]; then
                echo "使い方: ./launch.sh --ingest <フォルダのパス>"
                exit 2
            fi
            PART_ARGS+=(--ingest "$2")
            shift
            ;;
        --mode)
            # DD-CYN-0095 §3-D: 手引きは --mode <名前> と書いており、裸の語 (text 等) しか
            #   受けない従来の形と食い違っていた。--mode <名前> も同じ意味で受ける。
            if [ -z "${2:-}" ]; then
                echo "使い方: ./launch.sh --mode <text|lite|lite-en>"
                exit 2
            fi
            case "$KNOWN_PART_WORDS" in
                *" $2 "*) PART_ARGS+=("$2") ;;
                *) unknown_arg "--mode $2" ;;
            esac
            shift
            ;;
        *)
            # DD-CYN-0032 B2: 組み立て用の部品が受ける指定・モードだけを通し、
            #   それ以外はヘルプを出して止まる (部品側の "unknown arg" まで行かせない)。
            case "$KNOWN_PART_FLAGS" in
                *" $1 "*) PART_ARGS+=("$1"); shift; continue ;;
            esac
            case "$KNOWN_PART_WORDS" in
                *" $1 "*) PART_ARGS+=("$1"); shift; continue ;;
            esac
            unknown_arg "$1"
            ;;
    esac
    shift
done

# 実行エンジンの解決は引数を読み終えてから行う (--engine / --engine-command を効かせるため)
engine_resolve && engine_activate


# ============================================================
# DD-CYN-0037 §7-5-2: 引数なしのときの問いかけ
#   聞くのは2つまで。開く番号は聞かず、こちらで決める。
#   分からなければ Enter で必ず先へ進める。
# ============================================================

# この配布物が前に起動したコンテナが使っている番号なら、掛け直せるので空きとみなす。
_port_is_usable() {
    local _p="$1" _pcname _powner _prun _pports
    # DD-CYN-0095: LISTEN だけを見る (残存クライアント接続で「使用中」と誤検知しない)
    lsof -nP -iTCP:"$_p" -sTCP:LISTEN >/dev/null 2>&1 || return 0
    _pcname="$CNAME_DEFAULT"
    command -v podman >/dev/null 2>&1 || return 1
    podman container exists "$_pcname" 2>/dev/null || return 1
    _powner="$(podman inspect "$_pcname" --format '{{index .Config.Labels "org.cynovela.artifact"}}' 2>/dev/null || true)"
    _prun="$(podman inspect "$_pcname" --format '{{.State.Running}}' 2>/dev/null || echo false)"
    _pports="$(podman inspect "$_pcname" --format '{{range $p, $cs := .NetworkSettings.Ports}}{{range $cs}}{{.HostPort}} {{end}}{{end}}' 2>/dev/null || true)"
    [ "$_powner" = "cynovela-container" ] && [ "$_prun" = "true" ] || return 1
    case " $_pports " in *" $_p "*) return 0 ;; esac
    return 1
}

_pick_port() {
    local _p="${HOSTPORT_DEFAULT:-8801}" _n=0
    while [ "$_n" -lt 50 ]; do
        if _port_is_usable "$_p"; then echo "$_p"; return 0; fi
        _p=$((_p + 1)); _n=$((_n + 1))
    done
    echo "${HOSTPORT_DEFAULT:-8801}"
}

# 部品 (bge-m3) を Hugging Face から curl でダウンロードする。
#   python の部品 (huggingface_hub) に頼らない (受け取った人の Mac には無い)。
#   置き方は同梱版と同じ形 (snapshots/<版>/ に実ファイル) にそろえる。
#   途中で切れたダウンロードが「在る」と誤認されないよう、一時保存先で受けてから最後に移す。
_fetch_model() {
    # conda 環境では SSL_CERT_FILE が実在しない証明書を指すことがあり、
    # その場合 curl が繋がらない。実在しないときだけ外す (chewie の起動と同じ扱い)。
    if [ -n "${SSL_CERT_FILE:-}" ] && [ ! -f "$SSL_CERT_FILE" ]; then
        unset SSL_CERT_FILE
    fi
    local _rev="5617a9f61b028005a4858fdac845db406aefb181"
    local _base="https://huggingface.co/BAAI/bge-m3/resolve/$_rev"
    local _tmp="$MODEL_ROOT/.fetch-tmp.$$"
    local _dst="$MODEL_DIR/snapshots/$_rev"
    local _f _curlopt
    if [ -t 1 ]; then _curlopt="-fL#"; else _curlopt="-fsSL"; fi
    rm -rf "$_tmp"
    mkdir -p "$_tmp/1_Pooling"
    for _f in         config.json config_sentence_transformers.json modules.json         sentence_bert_config.json special_tokens_map.json tokenizer_config.json         tokenizer.json sentencepiece.bpe.model colbert_linear.pt sparse_linear.pt         1_Pooling/config.json pytorch_model.bin; do
        echo "  ダウンロード中: $_f"
        if ! curl $_curlopt --retry 2 --connect-timeout 10 -o "$_tmp/$_f" "$_base/$_f"; then
            rm -rf "$_tmp"
            return 1
        fi
    done
    mkdir -p "$MODEL_DIR/refs" "$MODEL_DIR/snapshots"
    printf '%s' "$_rev" > "$MODEL_DIR/refs/main"
    rm -rf "$_dst"
    mv "$_tmp" "$_dst"
    return 0
}

# 選ばれたフォルダを「モデルの保存先」として cynovela.yaml へ書き留める (DD-CYN-0074 Q-1)。
#   受け取り手が選ぶのは models--BAAI--bge-m3 そのものか、その親のどちらでもよい。
#   中身 (snapshots の下に実ファイル) が在ることを確かめてからでないと書かない。
#   0=つないだ / 1=つなげなかった
_link_model_dir() {  # $1=選ばれたフォルダ
    local _p="$1" _root="" _cand _s
    [ -n "$_p" ] || return 1
    _p="${_p%/}"
    case "$(basename "$_p")" in
        models--BAAI--bge-m3) _root="$(dirname "$_p")" ;;
        *)                    _root="$_p" ;;
    esac
    _cand="$_root/models--BAAI--bge-m3"
    [ -d "$_cand" ] || return 1
    for _s in "$_cand"/snapshots/*/; do
        if [ -d "$_s" ] && [ -n "$(ls -A "$_s" 2>/dev/null || true)" ]; then
            conf_set paths models_dir "$_root" || return 1
            MODEL_ROOT="$_root"
            MODEL_DIR="$_cand"
            return 0
        fi
    done
    return 1
}

# 次に何をすればよいかを画面へ出す (DD-CYN-0074 Q-1)。
#   効き目は断言しない。ダウンロードは相手先とネットの具合で変わる。
_print_model_next_steps() {
    echo ""
    echo "  資料を読み取るための部品 (bge-m3) が、まだ手元にありません。"
    echo "  この配布物はモデルを同梱していません。次のどちらかで進められます。"
    echo ""
    echo "  A) ダウンロードする (約 2.2 GB・インターネットにつなぎます)"
    echo "       ./launch.sh --fetch-model"
    echo "     ※ ダウンロード元 (Hugging Face) とネットの具合によっては失敗することがあります。"
    echo "  B) すでに持っているフォルダをつなぐ"
    echo "       cynovela.yaml の paths: の models_dir: に、"
    echo "       models--BAAI--bge-m3 が入っているフォルダの場所を書いてください。"
    echo "     ※ 端末から叩くと、フォルダを選ぶ画面から選ぶこともできます。"
    echo ""
    echo "  どちらも、保存先の形は SETUP-ACCELERATOR.md の手順に合わせてください。"
}

# 部品 (bge-m3) が手元に無いときは、黙って取りに行かない。必ず一度止めて聞く。
#   保存先は cynovela.yaml の paths: の models_dir: の1つだけである (既定は配布物の中)。
_ask_model_if_missing() {
    local _s _found=""
    if [ -d "$MODEL_DIR" ]; then
        for _s in "$MODEL_DIR"/snapshots/*/; do
            if [ -d "$_s" ] && [ -n "$(ls -A "$_s" 2>/dev/null || true)" ]; then _found="$_s"; break; fi
        done
    fi
    [ -n "$_found" ] && return 0

    echo ""
    echo "  資料を読み取るための部品が、この配布物の中にまだありません。"
    echo "  どうしますか？"
    echo "    1) いまダウンロードする"
    echo "       ・大きさ: 約 2.2 GB"
    echo "       ・インターネットにつなぎます (ダウンロード元: Hugging Face)"
    echo "       ・ダウンロード元とネットの具合によっては失敗することがあります"
    echo "    2) すでに持っているフォルダをつなぐ"
    echo "    3) やめる (あとで置いてから、もう一度叩く)"
    echo ""
    echo "  ※ 選ぶまで、通信は始めません。"
    printf "  選んでください [1-3] (Enter は 3): "
    local _c=""
    read -r _c || _c=""
    case "$_c" in
        1)
            echo "  → ダウンロードします (数分かかります)。"
            mkdir -p "$MODEL_ROOT"
            _fetch_model || {
                echo "  AIモデルのダウンロード元に繋がりませんでした。"
                echo "  インターネットに繋がっているかをご確認ください。"
                echo "  繋がっているのに失敗する場合は、同梱の LICENSES-MODELS の一覧にある入手先から手で受け取り、"
                echo "  下の B) の道でつないでから、もう一度お試しください。"
                _print_model_next_steps
                exit 2
            }
            ;;
        2)
            # DD-CYN-0074 Q-1: 選ばれた場所を cynovela.yaml へ書き留めて、そのまま使う。
            #   コンテナへ渡す元も同じ値を読むので、コピー替えなくても中から見える。
            local _sel
            _sel="$(osascript -e 'POSIX path of (choose folder with prompt "bge-m3 が入っているフォルダを選んでください")' 2>/dev/null || true)"
            echo "  → 選ばれた場所: ${_sel:-(選ばれませんでした)}"
            if _link_model_dir "$_sel"; then
                echo "     つなぎました。cynovela.yaml の paths: の models_dir: に書き留めました。"
                echo "     保存先: $MODEL_DIR"
            else
                echo "     そのフォルダの中に models--BAAI--bge-m3 の中身が見つかりませんでした。"
                _print_model_next_steps
                exit 2
            fi
            ;;
        *)
            echo "  → やめます。"
            _print_model_next_steps
            exit 2
            ;;
    esac
}

# DD-CYN-0074 Q-1: モデルが無いときの一手。run_probe のあとに呼ぶ。
#   端末が在れば聞く (ダウンロードする / つなぐ / やめる)。
#   端末が無いとき (アイコンからの起動・手順書・試験) は聞けないので、
#   足りないものとして積み、次に何をすればよいかを並べてから止める。
#   --check は読み取りだけなので聞かない。
_resolve_model_or_block() {
    [ "$MODEL_MISSING" = "1" ] || return 0
    if [ "$MODE_CHECK" != "1" ] && [ -t 0 ] && [ "$NO_PROMPT" != "1" ]; then
        _ask_model_if_missing
        MODEL_MISSING=0
        return 0
    fi
    add_blocker "埋め込みモデル bge-m3 がありません: $MODEL_DIR"
}

run_interactive() {
    local _c=""
    echo ""
    echo "はじめる前に、1つだけ聞きます。分からなければ Enter を押してください。"
    echo ""

    echo "1. 何を読ませますか？"
    echo "    1) 同梱のお試し資料で始める"
    echo "    2) 自分のフォルダを足す (フォルダを選ぶ画面が出ます)"
    printf "  選んでください [1-2] (Enter は 1): "
    read -r _c || _c=""
    case "$_c" in
        2)
            local _sel _name
            _sel="$(osascript -e 'POSIX path of (choose folder with prompt "読ませるフォルダを選んでください")' 2>/dev/null || true)"
            if [ -n "$_sel" ]; then
                _name="$(_roots_py "$INGEST_ROOTS_HELPER" --file "$INGEST_ROOTS_FILE" add "$_sel")"
                echo "  → 足しました: $_sel"
                echo "     (この中の名前: $_name)"
            else
                echo "  → 選ばれませんでした。同梱のお試し資料で始めます。"
                PART_ARGS+=(--demo)
            fi
            ;;
        *)
            echo "  → 同梱のお試し資料で始めます。"
            PART_ARGS+=(--demo)
            ;;
    esac

    # DD-CYN-0097 §5-A (決定 40-2・40-4): 構成の問いを撤去した。示す形が text の
    #   1つだけになったため、尋ねずにそのまま text で進む。引数 (--mode 等) で渡す道は
    #   従来どおり残っている (server.py の受け付けは変えていない)。
    PART_ARGS+=(text)

    _ask_model_if_missing

    local _picked
    _picked="$(_pick_port)"
    if [ "$_picked" != "${HOSTPORT_DEFAULT:-8801}" ]; then
        echo ""
        echo "  ※ いつもの番号 (${HOSTPORT_DEFAULT:-8801}) は別のものが使っていました。"
        echo "     $_picked を使います。"
    fi
    HOSTPORT="$_picked"
    echo ""
    echo "  開く場所: http://localhost:$HOSTPORT"
    echo ""
}

# ------------------------------------------------------------
# 環境チェック
# ------------------------------------------------------------
REPORT=()
BLOCKERS=()
WARNINGS=()

add_report() { REPORT+=("$1"); }
add_blocker() { BLOCKERS+=("$1"); }
add_warning() { WARNINGS+=("$1"); }

run_probe() {
    add_report "== 調べた時刻 =="
    add_report "$(date '+%Y-%m-%d %H:%M:%S %Z')"
    add_report "== 保存先 =="
    add_report "$SCRIPT_DIR"
    add_report "== 起動の形 =="
    add_report "コンテナ (コンテナ) で動かす形の1本道です。ホストで直接動かす道はありません。"

    # 1. 機械と OS
    add_report "== 機械と OS =="
    add_report "CPU 種別: $(uname -m) / $(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo '不明')"
    add_report "OS: $(sw_vers -productName 2>/dev/null || uname -s) $(sw_vers -productVersion 2>/dev/null || uname -r)"

    # 2. python (取り込み元のバックアップを読み書きする補助にだけ使う。本体の部品はコンテナの中)
    add_report "== python (補助にだけ使います) =="
    if command -v python3 >/dev/null 2>&1; then
        add_report "python3: $(command -v python3) / $(python3 -V 2>&1)"
    else
        add_report "python3: ありません"
    fi
    # DD-CYN-0107 F-c: バックアップに使うのは動作要件 (3.12 以上) を満たす python だけ。有無ではなく版まで見る。
    # DD-CYN-0117 R-1: 版は名前で当てない。上で出した python3 も、中身が 3.12 以上なら
    #   conf_pick_py が候補に入れる。∴ 「見つかりました」と出しながら「ありません」と
    #   言う食い違いが起きない。
    if [ -n "$ROOTS_PY" ]; then
        add_report "バックアップに使う python: $ROOTS_PY / $("$ROOTS_PY" -V 2>&1)"
    else
        add_report "バックアップに使う python: ありません (3.12 以上のものが見つかりません)"
        if [ -s "$INGEST_ROOTS_FILE" ]; then
            # DD-CYN-0117 R-2: これは起動を止める理由にならない。読めなくなるのは
            #   取り込み元のバックアップだけで、コンテナの中の本体は動く。∴ 気をつけること へ置く。
            # DD-CYN-0117 R-4: いま失敗した入口をもう一度押せ、とは言わない。
            add_warning "3.12 以上の python がこの Mac にありません。取り込み元のバックアップ (store/ingest-roots.json) を読めないため、足したフォルダは読み込まれません。コンテナの起動そのものは止まりません。直すには https://www.python.org/downloads/ から 3.12 以上を入れてください (コンテナの中の部品はこれとは別で、作り直しは要りません)。"
        fi
    fi

    # 3. conda (この形態では使いません。コピーとして記録します)
    add_report "== conda =="
    if command -v conda >/dev/null 2>&1; then
        add_report "conda: あり ($(conda info --base 2>/dev/null || echo '場所不明')) — この形態では使いません。書き込みもしません。"
    else
        add_report "conda: なし — この形態では不要です。"
    fi

    # 4. 本体の部品 (コンテナの中に入っているので、ホスト側には要りません)
    add_report "== 本体の部品 =="
    add_report "requirements.txt の部品はコンテナ (イメージ) の中に入っています。ホスト側へ入れる必要はありません。"

    # 5. Podman と仮想機械の有無・割り当て
    add_report "== Podman / 仮想機械 =="
    if command -v podman >/dev/null 2>&1; then
        add_report "podman: $(podman --version 2>&1)"
        _vm="$(podman machine list --format '{{.Name}} type={{.VMType}} cpu={{.CPUs}} mem={{.Memory}} disk={{.DiskSize}} running={{.Running}}' 2>/dev/null | tr '\n' ' ' || true)"
        if [ -n "$_vm" ]; then
            add_report "仮想機械: $_vm"
        else
            add_report "仮想機械: 1台もありません"
            add_blocker "podman の仮想機械がありません。'podman machine init' と 'podman machine start' を実行してください。"
        fi
        if ! podman info >/dev/null 2>&1; then
            add_report "podman info: 応答しません (仮想機械が止まっている可能性)"
            add_blocker "podman が応答しません。'podman machine start' で仮想機械を起動してください。"
        else
            add_report "podman info: 応答あり"
        fi
    else
        add_report "podman: ありません"
        add_blocker "podman がありません。この形態はコンテナで動くため podman が要ります: https://podman.io/"
    fi

    # 6. 使うポートの空き
    #    DD-CYN-0032 B5: 使っているのが「この配布物が前に起動したコンテナ」なら止める理由にしない。
    #      従来は使用中というだけで無条件に blocker を積み、コンテナを置き換える処理
    #      (run-container.sh) へ進む前に exit 1 していた。∴ 掛け直しが一度も通らなかった。
    add_report "== ポート =="
    if lsof -nP -iTCP:"$HOSTPORT" -sTCP:LISTEN >/dev/null 2>&1; then
        add_report "ポート $HOSTPORT: 使用中"
        _own=0
        _pcname="$CNAME_DEFAULT"
        if command -v podman >/dev/null 2>&1 && podman container exists "$_pcname" 2>/dev/null; then
            _powner="$(podman inspect "$_pcname" --format '{{index .Config.Labels "org.cynovela.artifact"}}' 2>/dev/null || true)"
            _prun="$(podman inspect "$_pcname" --format '{{.State.Running}}' 2>/dev/null || echo false)"
            _pports="$(podman inspect "$_pcname" --format '{{range $p, $cs := .NetworkSettings.Ports}}{{range $cs}}{{.HostPort}} {{end}}{{end}}' 2>/dev/null || true)"
            if [ "$_powner" = "cynovela-container" ] && [ "$_prun" = "true" ]; then
                case " $_pports " in
                    *" $HOSTPORT "*) _own=1 ;;
                esac
            fi
        fi
        if [ "$_own" = "1" ]; then
            add_report "使っているのは この配布物が前に起動したコンテナ ($_pcname) です。掛け直します。"
        else
            add_blocker "ポート $HOSTPORT を別のものが使っています。そちらを止めるか、./launch.sh --port <別の番号> を使ってください。"
        fi
    else
        add_report "ポート $HOSTPORT: 空き"
    fi

    # 7. コンテナの名前のぶつかり
    add_report "== コンテナの名前 =="
    _cname="$CNAME_DEFAULT"
    add_report "使う名前: $_cname"
    if command -v podman >/dev/null 2>&1 && podman container exists "$_cname" 2>/dev/null; then
        _owner="$(podman inspect "$_cname" --format '{{index .Config.Labels "org.cynovela.artifact"}}' 2>/dev/null || true)"
        if [ "$_owner" = "cynovela-container" ]; then
            add_report "同じ名前のコンテナ: あり (この配布物が作ったもの。消さずに、止まっていればそのまま起こします)"
        else
            add_report "同じ名前のコンテナ: あり (この配布物が作ったものではありません)"
            add_blocker "'$_cname' という名前のコンテナが既にあります。この配布物が作ったものではないため消しません。別の名前で起動するには: cynovela.yaml の container: の name: を変えてください。"
        fi
    else
        add_report "同じ名前のコンテナ: なし"
    fi

    # 8. モデル保存先の有無と中身
    #    探し先は「cynovela.yaml の paths: の models_dir: が指す1か所」だけにする (DD-CYN-0074 Q-1)。
    #    (1) コンテナへ渡すのも同じ1つの値で (run-container.sh の -v)、両者は同じ行を読む。
    #        ∴ 5か所を見て「あり」と言い、コンテナの中では見えない、という食い違いは起きない。
    #    (2) コンテナは画面を持たない起動 (podman run -d) なので、本体の
    #        「必要なモデルが見つかりません」の確認 (今すぐダウンロードして起動する ほか) は
    #        そもそも出せない。ここで受け取り手に届けるのが唯一の場所である。
    #    無いときは、ここでは止めない。印だけ立て、run_probe を抜けてから
    #    _resolve_model_or_block が聞く (端末が在るとき) か、次の一手を並べて止める。
    #    アプリの形 (chewie / hansolo) は画面を持つ起動なので、そちらは止めずに本体の確認へ渡す。
    add_report "== 埋め込みモデルの保存先 =="
    if [ -d "$MODEL_DIR" ]; then
        _snap="$(ls -d "$MODEL_DIR"/snapshots/*/ 2>/dev/null | head -1 || true)"
        if [ -n "$_snap" ] && [ -n "$(ls -A "$_snap" 2>/dev/null || true)" ]; then
            add_report "bge-m3: あり ($_snap)"
            add_report "中身: $(ls "$_snap" 2>/dev/null | tr '\n' ' ')"
        else
            add_report "bge-m3: 保存先はあるが中身が空です ($MODEL_DIR)"
            MODEL_MISSING=1
        fi
    else
        add_report "bge-m3: ありません ($MODEL_DIR)"
        MODEL_MISSING=1
    fi

    # 9. 外の推論サーバへの到達
    add_report "== 回答を作る LLM への到達 =="
    _llm="$(conf_get_or llm base_url http://localhost:1234)"
    _code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 4 "${_llm}/v1/models" 2>/dev/null || true)"
    add_report "ホストから $_llm/v1/models: HTTP ${_code:-000}"
    if [ "$_code" != "200" ]; then
        add_warning "回答を作る LLM ($_llm) にホストから届きません。取り込みと検索は動きますが、回答は作れません。画面の Settings で宛先を直せます (コンテナからは host.containers.internal 経由になります)。"
    else
        add_warning "コンテナの中からホストの LLM へは localhost では届きません。画面の Settings では http://host.containers.internal:1234 を使ってください。"
    fi

    # 10. 鍵の有無 (在るかどうかだけ。中身は読みません)
    add_report "== 金庫の鍵 =="
    if [ -f "$KEYFILE" ]; then
        add_report "keys/secret.key: あり (中身は読みません)"
    elif [ -f "$SCRIPT_DIR/store/secret.key" ]; then
        add_report "keys/secret.key: なし / store/secret.key: あり (起動時に keys/ へコピーします)"
    else
        add_report "keys/secret.key: なし / store/secret.key: なし"
        add_warning "金庫の鍵がありません。起動時に新しく作られますが、同梱のデモ本文はその鍵では読めません。"
    fi

    # 11. ディスクの空き
    add_report "== ディスクの空き =="
    add_report "$(df -h "$SCRIPT_DIR" 2>/dev/null | tail -1)"
    _avail_g="$(df -g "$SCRIPT_DIR" 2>/dev/null | awk 'NR==2{print $4}')"
    if [ -n "$_avail_g" ] && [ "$_avail_g" -lt 5 ] 2>/dev/null; then
        add_blocker "ディスクの空きが ${_avail_g}GB しかありません。コンテナの組み立てに 5GB 以上あけてください。"
    elif [ -n "$_avail_g" ] && [ "$_avail_g" -lt 20 ] 2>/dev/null; then
        add_warning "ディスクの空きが ${_avail_g}GB です。取り込みを行うなら 20GB 以上を勧めます。"
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
# --setup: この形態でホスト側に用意するものは「金庫の鍵の保存先」だけです。
#   本体の部品はコンテナの中にあり、共有の conda 環境は使いません。
# ------------------------------------------------------------
do_setup() {
    echo ""
    echo "[--setup] この形態でホスト側に用意するものを揃えます。"
    echo "          本体の部品はコンテナ (イメージ) の中に入っているため、"
    echo "          共有の conda 環境へは何も入れません (使いません)。"
    if [ ! -f "$KEYFILE" ] && [ -f "$SCRIPT_DIR/store/secret.key" ]; then
        mkdir -p "$SCRIPT_DIR/keys"
        cp "$SCRIPT_DIR/store/secret.key" "$KEYFILE"
        chmod 600 "$KEYFILE"
        echo "          金庫の鍵の保存先を作りました: $KEYFILE (同梱の鍵をコピーしました)"
    else
        echo "          金庫の鍵の保存先: 用意済み、または同梱の鍵がありません (起動時に作られます)"
    fi
    echo ""
}

# ------------------------------------------------------------
# 要るものを枠で囲って出す (DD-CYN-0031 B4)
#   用意し終わったときと、起動したときの両方で出す。
#   パスワードの実値はここへ印字しない。同梱のバックアップの場所を示す。
#   この形態はコンテナを裏で動かすため、本体が出すガイドは受け取り手の画面へ
#   届かない。∴ この入口が出さないと、止め方も入り方も画面に出ない。
# ------------------------------------------------------------
print_next_steps() {
    local where="${1:-setup}"
    echo ""
    echo "┌──────────────────────────────────────────────────────────────┐"
    echo "│  Cynovela — 使いはじめるのに要るもの                          │"
    echo "└──────────────────────────────────────────────────────────────┘"
    echo ""
    echo "  ■ 開く場所"
    echo "      http://localhost:$HOSTPORT"
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
    echo "         (記録・鍵・記録のコンテナが $SCRIPT_DIR/store と $SCRIPT_DIR/keys の下に"
    echo "          作られます)"
    echo "      2. 鍵はこの機材で新しく作られます。他の機材で作られた鍵とは別のものです。"
    echo "         ∴ 他の機材で取り込んだ中身は、この機材では読めません。"
    if [ "$ENGINE_NAME" = "(コマンド指定)" ]; then
        echo "      3. 止め方: $ENGINE_PATH stop $CNAME_DEFAULT"
    else
        echo "      3. 止め方: ${ENGINE_NAME:-podman} stop $CNAME_DEFAULT"
    fi
    echo "         (bash stop.sh でも同じものが止まります)"
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
# 本編
# ------------------------------------------------------------
echo "============================================"
echo " Cynovela (コンテナで動かす形)"
echo " 保存先: $SCRIPT_DIR"
echo "============================================"

if [ "$MODE_CHECK" = "1" ] && [ "$MODE_SETUP" = "1" ]; then
    echo "❌ --check と --setup は同時に使えません。--check は読み取りだけ、--setup は用意してから起動します。"
    exit 2
fi

# DD-CYN-0037 §7-5-2: 引数が1つも無く、人が端末から叩いたときだけ番号で聞く。
#   非対話 (手順書・試験・アイコンからの起動) では聞かず、従来どおり既定で進む。
if [ "$ARGC_AT_START" = "0" ] && [ -t 0 ] && [ "$NO_PROMPT" != "1" ]; then
    run_interactive
fi

# DD-CYN-0046: アイコンの道 (非対話) で「ダウンロードする」が押されたときの取得。
#   対話の道は run_interactive 内の _ask_model_if_missing が同じ役を持つ。
#   画面 (launcher.applescript) が確認を取ってから印を立てるため、ここでは聞かずに取得する。
if [ "$FETCH_MODEL" = "1" ]; then
    _fm_found=""
    if [ -d "$MODEL_DIR" ]; then
        for _fm_s in "$MODEL_DIR"/snapshots/*/; do
            if [ -d "$_fm_s" ] && [ -n "$(ls -A "$_fm_s" 2>/dev/null || true)" ]; then _fm_found="$_fm_s"; break; fi
        done
    fi
    if [ -z "$_fm_found" ]; then
        echo "  → ダウンロードします (数分かかります)。"
        mkdir -p "$MODEL_ROOT"
        if ! _fetch_model; then
            echo "AIモデルのダウンロード元に繋がりませんでした。"
            echo "インターネットに繋がっているかをご確認ください。"
            echo "繋がっているのに失敗する場合は、同梱の LICENSES-MODELS の一覧にある入手先から手で受け取り、"
            echo "この配布物の store/models の中へ置いてから、もう一度お試しください。"
            exit 2
        fi
    fi
fi

if [ ! -f "$CONTAINER_PART" ]; then
    echo "❌ 中で使う組み立て用のスクリプトがありません: $CONTAINER_PART"
    exit 1
fi

if [ "$MODE_SETUP" = "1" ]; then
    do_setup
    run_probe
    _resolve_model_or_block

    # 版が違うもの・足りないものは知らせるだけで止めない (DD-CYN-0031 B6)
    if [ "${#WARNINGS[@]}" -gt 0 ]; then
        echo ""
        echo "== 気をつけること (止まりはしません) =="
        printf '  - %s\n' "${WARNINGS[@]}"
    fi
    if [ "${#BLOCKERS[@]}" -gt 0 ]; then
        echo ""
        echo "== まだ足りないもの =="
        printf '  - %s\n' "${BLOCKERS[@]}"
        if [ "$MODEL_MISSING" = "1" ]; then _print_model_next_steps; fi
    fi

    echo ""
    echo "[--setup] 用意し終わりました。ここでは起動しません。"
    print_next_steps setup
    exit 0
fi

run_probe
_resolve_model_or_block

if [ "$MODE_CHECK" = "1" ]; then
    mkdir -p "$(dirname "$REPORT_FILE")"
    print_probe_result > "$REPORT_FILE"
    echo ""
    echo "[--check] 読み取りだけで調べました。何も入れず、コンテナも作らず、何も起動していません。"
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
    echo "  用意して起動: ./launch.sh --setup"
    if [ "$MODEL_MISSING" = "1" ]; then _print_model_next_steps; fi
    exit 1
fi

# コンテナを組み立てて起動する。組み立て用のスクリプトはこの入口からだけ呼ぶ。
echo ""
echo "[起動] コンテナを組み立てて起動します (ホスト側ポート $HOSTPORT)"
print_next_steps launch
exec bash "$CONTAINER_PART" --from-entry --hostport "$HOSTPORT" ${PART_ARGS[@]+"${PART_ARGS[@]}"}
