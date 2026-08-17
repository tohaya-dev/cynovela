#!/bin/bash
# Mac Accelerator Service (外部の推論サーバ) を用意するフェーズ — launch.sh から読み込んで使う
#
#   保存先の考え方 (決定 29-3):
#     既存の起動スクリプトを置き換えない。launch.sh がこのファイルを読み込み、
#     3択 (Podman / Docker / 自分で指定) より前に mas_phase_ask を、
#     選択が確定したあとに mas_phase_apply を呼ぶ。本体 (tools/launch-body.sh)
#     には手を入れない。
#
#   なぜ3択より前か:
#     MAS が立たないままコンテナを起こすと、埋め込みはコンテナの中の CPU へ退避する。
#     退避したあとで実行ファイルを選び直しても、その取り込みには効かない。
#     ∴ MAS はコンテナより先に立てる。
#
#   なぜ launch.sh の中か:
#     launch.sh は本体を --no-prompt で切り離して呼ぶ。本体の側の問いかけは
#     NO_PROMPT で塞がれるため、受け取り手へ問えるのは launch.sh の中だけである。
#
#   環境の作り先 (決定 14-5):
#     配布物の中の .mas-env だけに作る。conda の共有の場所 (envs) には作らない。
#     environment.yml は name: cynovela の形で共有の場所へ作るものなので使わない。
#     使うのは mas/mas-requirements.txt (4件) である。
#
#   探す順 (決定 14-4):
#     conda が使えるなら conda を先に出す。無い場合に venv を出す。
#
#   既定 (決定 14-5):
#     提示だけ。黙って作らない。受け取り手が選んだときだけ作る。

# ── この節が使う値 ────────────────────────────────────────
MAS_PORT="18850"
MAS_ENV_DIR="$WRAP_DIR/.mas-env"
MAS_REQ="$WRAP_DIR/mas/mas-requirements.txt"
MAS_SERVER="$WRAP_DIR/mas/mas_server.py"
MAS_LOG="$WRAP_DIR/store/mas.log"

MAS_PLAN=""        # none / use-running / conda / venv / custom / skip
MAS_PYTHON=""      # custom で受け取り手が書いた場所
MAS_DISP=""        # 確認の画面に出す一行
MAS_STATE="未確認"  # 確認の画面に出す状態

# ── 18850 の様子を見る ───────────────────────────────────
# 標準出力へ device の値を出す。立っていなければ何も出さない。
mas_device() {
    curl -s --max-time 4 "http://127.0.0.1:${MAS_PORT}/health" 2>/dev/null \
        | /usr/bin/grep -o '"device"[[:space:]]*:[[:space:]]*"[^"]*"' \
        | head -1 \
        | sed 's/.*"\([^"]*\)"$/\1/'
}

# ── 配布物の中に既に環境が在るか ─────────────────────────
mas_env_python() {
    if [ -x "$MAS_ENV_DIR/bin/python" ]; then
        echo "$MAS_ENV_DIR/bin/python"
    fi
}

# ── venv を作れる python を探す (新しい版から順に) ──────────
# 標準出力へ場所を出す。見つからなければ何も出さない。
mas_venv_base() {
    local c
    for c in python3.13 python3.12 python3.11 python3.10; do
        if command -v "$c" >/dev/null 2>&1; then command -v "$c"; return 0; fi
    done
    # 版のついた名前が無いときは python3 の版を見る
    if command -v python3 >/dev/null 2>&1; then
        if python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)' 2>/dev/null; then
            command -v python3; return 0
        fi
    fi
    return 1
}

# ── 渡された python が MAS を動かせるか (4部品が在るか) ─────
mas_python_ok() {
    [ -x "$1" ] || return 1
    "$1" - <<'PY' >/dev/null 2>&1
import importlib
for m in ("torch", "sentence_transformers", "fastapi", "uvicorn"):
    importlib.import_module(m)
PY
}

# ─────────────────────────────────────────────────────────
#  フェーズ前半: 調べて、受け取り手に選ばせる (ここでは何も作らない)
# ─────────────────────────────────────────────────────────
mas_phase_ask() {
    local dev have_conda=0 have_venv=0 venv_base="" env_py="" ans

    echo ""
    echo "== 埋め込みを動かす外部の推論サーバ (Mac Accelerator Service) =="
    echo "   この配布物は、資料を数値に直す仕事を、この Mac の上で動く外部の推論サーバへ渡す作りです。"
    echo "   外部の推論サーバが立っていないと、その仕事はコンテナの中の CPU で行われます。処理は止まりませんが遅くなります。"

    # 1. 既に立っているか
    dev="$(mas_device)"
    if [ -n "$dev" ]; then
        echo ""
        echo "   外部の推論サーバ: 既に立っています (device: $dev)"
        MAS_PLAN="use-running"
        MAS_STATE="既に立っています (device: $dev)"
        return 0
    fi
    echo ""
    echo "   外部の推論サーバ: 立っていません (127.0.0.1:${MAS_PORT} に応答がありません)"

    # 2. 配布物の中に環境が在るか
    env_py="$(mas_env_python)"
    if [ -n "$env_py" ] && mas_python_ok "$env_py"; then
        echo "   この配布物の中の環境: 見つかりました ($MAS_ENV_DIR)"
        MAS_PLAN="use-env"
        MAS_STATE="この配布物の中の環境で立てます"
        MAS_PYTHON="$env_py"
        return 0
    fi

    # 3. 何で作れるかを調べる (決定 14-4: conda を先に見る)
    command -v conda >/dev/null 2>&1 && have_conda=1
    venv_base="$(mas_venv_base)" && have_venv=1

    while true; do
        echo ""
        echo "   外部の推論サーバを動かすための場所を、この配布物の中に作れます。"
        echo "   作る先: $MAS_ENV_DIR  (この配布物の中だけです。共有の環境には何も書きません)"
        echo "   入れるもの: $MAS_REQ に書いた4件"
        echo ""
        if [ "$have_conda" = "1" ]; then
            echo "  1) conda で作る"
            echo "     見つかりました ($(conda info --base 2>/dev/null || echo '場所は読めませんでした'))"
            echo "     共有の環境 (envs) には作りません。上の場所を指定して作ります。"
        else
            echo "  1) conda で作る"
            echo "     conda が見つかりませんでした。この番号は選べません。"
        fi
        if [ "$have_venv" = "1" ]; then
            echo "  2) venv で作る"
            echo "     使う python: $venv_base ($("$venv_base" -V 2>&1))"
        else
            echo "  2) venv で作る"
            echo "     3.10 以上の python3 が見つかりませんでした。この番号は選べません。"
        fi
        echo "  3) 自分で指定する"
        echo "     既に4件が入っている python の場所を入力します。新しくは作りません。"
        echo "  4) 外部の推論サーバを使わずに進む"
        echo "     埋め込みはコンテナの中の CPU で行われます。処理は止まりませんが遅くなります。"
        echo "  5) やめる"
        printf '番号を入れてください [1/2/3/4/5]: '
        if ! IFS= read -r ans; then
            echo ""
            echo "入力が閉じたため、やめました。何も作っていません。"
            exit 0
        fi
        case "$ans" in
            1)
                if [ "$have_conda" = "1" ]; then
                    MAS_PLAN="conda"; MAS_STATE="conda で作ってから立てます"; return 0
                fi
                echo ""
                echo "conda が見つかりませんでした。"
                echo "  入れ方: https://conda-forge.org/download/ から Miniforge を入れてください"
                echo "  入れたくない場合は 2) の venv を選んでください"
                ;;
            2)
                if [ "$have_venv" = "1" ]; then
                    MAS_PLAN="venv"; MAS_PYTHON="$venv_base"
                    MAS_STATE="venv で作ってから立てます"; return 0
                fi
                echo ""
                echo "3.10 以上の python3 が見つかりませんでした。"
                echo "  入れ方: https://www.python.org/downloads/ から 3.12 を入れてください"
                echo "  または 1) の conda を選んでください"
                ;;
            3)
                printf '使う python の場所を入れてください: '
                if ! IFS= read -r MAS_PYTHON; then
                    echo ""
                    echo "入力が閉じたため、やめました。何も作っていません。"
                    exit 0
                fi
                if [ -z "$MAS_PYTHON" ]; then continue; fi
                if mas_python_ok "$MAS_PYTHON"; then
                    MAS_PLAN="custom"; MAS_STATE="指定された python で立てます: $MAS_PYTHON"; return 0
                fi
                echo ""
                echo "その python では外部の推論サーバを動かせませんでした。"
                echo "  次の4件が入っている必要があります: torch / sentence-transformers / fastapi / uvicorn"
                echo "  確かめ方: $MAS_PYTHON -c 'import torch, sentence_transformers, fastapi, uvicorn'"
                ;;
            4)
                MAS_PLAN="skip"; MAS_STATE="使いません (埋め込みはコンテナの中の CPU で行われます)"; return 0
                ;;
            5)
                echo "やめました。何も作っていません。"
                exit 0
                ;;
            *) echo "  → 番号を入れてください。" ;;
        esac
    done
}

# ─────────────────────────────────────────────────────────
#  フェーズ後半: 選ばれた道で作って、立てて、device を確かめる
# ─────────────────────────────────────────────────────────
mas_phase_apply() {
    local py="" dev i

    case "$MAS_PLAN" in
        use-running)
            return 0
            ;;
        skip)
            echo ""
            echo "[外部の推論サーバ] 使わずに進みます。埋め込みはコンテナの中の CPU で行われます。"
            echo "         あとで立てたいときは SETUP-ACCELERATOR.md を見てください。"
            return 0
            ;;
        use-env)
            py="$MAS_PYTHON"
            ;;
        custom)
            py="$MAS_PYTHON"
            ;;
        conda)
            echo ""
            echo "[外部の推論サーバ] conda で場所を作ります: $MAS_ENV_DIR"
            echo "         共有の環境 (envs) には何も書きません。"
            if ! conda create -y -p "$MAS_ENV_DIR" python=3.12; then
                echo "[外部の推論サーバ] 場所を作れませんでした。" >&2
                mas_report_missing; return 1
            fi
            py="$MAS_ENV_DIR/bin/python"
            echo "[外部の推論サーバ] 部品を入れます: $MAS_REQ"
            if ! "$py" -m pip install -r "$MAS_REQ"; then
                echo "[外部の推論サーバ] 部品を入れられませんでした。" >&2
                mas_report_missing; return 1
            fi
            ;;
        venv)
            echo ""
            echo "[外部の推論サーバ] venv で場所を作ります: $MAS_ENV_DIR"
            echo "         共有の環境には何も書きません。"
            if ! "$MAS_PYTHON" -m venv "$MAS_ENV_DIR"; then
                echo "[外部の推論サーバ] 場所を作れませんでした。" >&2
                mas_report_missing; return 1
            fi
            py="$MAS_ENV_DIR/bin/python"
            echo "[外部の推論サーバ] 部品を入れます: $MAS_REQ"
            if ! "$py" -m pip install --upgrade pip; then :; fi
            if ! "$py" -m pip install -r "$MAS_REQ"; then
                echo "[外部の推論サーバ] 部品を入れられませんでした。" >&2
                mas_report_missing; return 1
            fi
            ;;
        *)
            return 0
            ;;
    esac

    # 立てる (SETUP-ACCELERATOR.md の手順どおり)
    echo ""
    echo "[外部の推論サーバ] 立てます: $py mas/mas_server.py --preload"
    echo "         記録はこのファイルへ書きます: $MAS_LOG"
    mkdir -p "$WRAP_DIR/store"
    ( cd "$WRAP_DIR" && nohup "$py" mas/mas_server.py --preload >> "$MAS_LOG" 2>&1 & )
    echo "[外部の推論サーバ] 立ち上がりを待っています (初回は埋め込みモデルの読み込みに時間がかかります)"

    i=0
    dev=""
    while [ "$i" -lt 120 ]; do
        dev="$(mas_device)"
        [ -n "$dev" ] && break
        sleep 2
        i=$((i + 1))
    done

    if [ -z "$dev" ]; then
        echo "[外部の推論サーバ] 立ち上がりませんでした。" >&2
        echo "         記録を見てください: $MAS_LOG" >&2
        mas_report_missing
        return 1
    fi

    echo "[外部の推論サーバ] 立ちました (device: $dev)"
    MAS_STATE="立っています (device: $dev)"
    if [ "$dev" != "mps" ]; then
        echo "[外部の推論サーバ] device が mps ではありません。埋め込みは GPU ではなく $dev で行われます。"
        echo "         このまま進めても処理は止まりませんが、遅くなります。"
    fi
    return 0
}

# ── 立てられなかったときに、何が足りないかを画面に出す ──────
mas_report_missing() {
    echo ""
    echo "== 外部の推論サーバを立てられませんでした =="
    echo "   このままコンテナを起こすと、埋め込みはコンテナの中の CPU で行われます。"
    echo "   黙って遅くならないよう、ここで止めています。"
    echo ""
    echo "   要るもの:"
    echo "     - 3.10 以上の python (conda でも venv でも構いません)"
    echo "     - $MAS_REQ に書いた4件"
    echo "     - 埋め込みモデル bge-m3 の保存先: $WRAP_DIR/store/models"
    echo ""
    echo "   手で立てる手順は SETUP-ACCELERATOR.md に書いてあります。"
    echo "   外部の推論サーバを使わずに進めたいときは、もう一度このファイルを叩いて 4) を選んでください。"
    echo ""
}
