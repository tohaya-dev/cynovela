#!/bin/bash
# Cynovela を手元から取り除くための道 (・chewie 版)
#
#   ターミナルから叩きます:  bash uninstall.sh
#
#   この道がすること (順):
#     1. 何を取り除くかを全部画面へ出し、1回目の確認をします
#     2. 取り返しがつかないことを示し、2回目の確認をします
#     3. 以後は一括で行い、途中で問い直しません
#     4. この配布物から起こした本体を止めます
#     5. 外部の推論サーバ (Mac Accelerator Service) を止めます
#     6. この配布物のために作った python の環境を消します
#     7. このフォルダをゴミ箱へ入れます
#
#   この形 (chewie) は、この Mac の上で直接動きます。コンテナ (コンテナ) はありません。
#   ∴ 取り除く相手は「この配布物のために作った python の環境」と「このフォルダ」です。
#
#   環境の名前は決め打ちしていません。cynovela.yaml に書いてあればそれを、
#   無ければ launch.sh が持っている名前を読みます。
#
#   共有の conda 環境 (base ほか、この配布物が作っていないもの) は取り除きません。
#   conda そのものも取り除きません。他の用途でお使いになるためです。
#
#   最後はゴミ箱へ入れるだけです。ゴミ箱を空にするまで、ディスクの容量は戻りません。
set -u

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONF_REPO="$REPO"
. "$REPO/tools/conf.sh"

# ── 1. 相手の名前を設定から読む (決め打ちしない) ──────────────
#   1) cynovela.yaml に python: env_name: が在ればそれを使う
#   2) 無ければ launch.sh が持っている名前を読む (起動と取り除きで食い違わないようにする)
#   3) どちらも読めなければ最後の受け皿
DIST_ENV="$(conf_get python env_name)"
if [ -z "$DIST_ENV" ]; then
    DIST_ENV="$(/usr/bin/sed -n 's/^DIST_ENV="\(.*\)"$/\1/p' "$REPO/launch.sh" 2>/dev/null | head -1)"
fi
[ -n "$DIST_ENV" ] || DIST_ENV="cynovela-dist"

SHARED_ENV="$(/usr/bin/sed -n 's/^SHARED_ENV="\(.*\)"$/\1/p' "$REPO/launch.sh" 2>/dev/null | head -1)"
[ -n "$SHARED_ENV" ] || SHARED_ENV="cynovela"

VENV_DIR="$REPO/.venv-cynovela"
MAS_ENV_DIR="$REPO/.mas-env"
DATA_DIR="$(conf_get_or paths data_dir "$REPO/store")"
case "$DATA_DIR" in ./*) DATA_DIR="$REPO/${DATA_DIR#./}" ;; esac

# ── 2. 共有の環境を消さないための遮断 ────────────────────────
#   読み取った名前が共有の環境と同じだったときは、その場で止める。
for _protected in "$SHARED_ENV" base root; do
    if [ "$DIST_ENV" = "$_protected" ]; then
        echo ""
        echo "設定から読み取った環境の名前が '$DIST_ENV' でした。"
        echo "これは共有の環境の名前です。取り除きません。ここで止めます。"
        echo "cynovela.yaml の python: env_name: を確かめてください。"
        exit 1
    fi
done

# ── 3. 実際に在るものを調べる ───────────────────────────────
CONDA_BASE=""
CONDA_BIN=""
for _c in "$HOME/miniforge3" "$HOME/miniconda3" "/opt/homebrew/Caskroom/miniforge/base" \
          "$HOME/opt/anaconda3" "$HOME/anaconda3" "/usr/local/anaconda3"; do
    if [ -x "$_c/bin/conda" ]; then CONDA_BASE="$_c"; CONDA_BIN="$_c/bin/conda"; break; fi
done
if [ -z "$CONDA_BIN" ] && command -v conda >/dev/null 2>&1; then
    CONDA_BIN="$(command -v conda)"
    CONDA_BASE="$("$CONDA_BIN" info --base 2>/dev/null || true)"
fi

CONDA_ENV_DIR=""
_have_conda_env=0
if [ -n "$CONDA_BASE" ] && [ -d "$CONDA_BASE/envs/$DIST_ENV" ]; then
    CONDA_ENV_DIR="$CONDA_BASE/envs/$DIST_ENV"
    _have_conda_env=1
fi

_have_venv=0
[ -d "$VENV_DIR" ] && _have_venv=1
_have_masenv=0
[ -d "$MAS_ENV_DIR" ] && _have_masenv=1

# この配布物から起こした本体だけを対象にする。
#   判定: そのプロセスの命令の綴りに、このフォルダの場所と server.py の両方が在ること。
#   ∴ 別の場所の Cynovela や、たまたま同じ名前の別物には当たらない。
_app_pids=""
_app_pids="$(/bin/ps -Ao pid=,command= 2>/dev/null \
    | /usr/bin/grep -F "$REPO" \
    | /usr/bin/grep -F "server.py" \
    | /usr/bin/grep -v -F "mas_server.py" \
    | /usr/bin/awk '{print $1}')"
# 記録に残っている番号も拾う (画面から起こしたときはこちらに在る)
if [ -f "$DATA_DIR/server.pid" ]; then
    _rec="$(cat "$DATA_DIR/server.pid" 2>/dev/null)"
    if [ -n "$_rec" ] && kill -0 "$_rec" 2>/dev/null; then
        if /bin/ps -o command= -p "$_rec" 2>/dev/null | /usr/bin/grep -q "server.py"; then
            case " $_app_pids " in *" $_rec "*) : ;; *) _app_pids="$_app_pids $_rec" ;; esac
        fi
    fi
fi
_app_pids="$(printf '%s' "$_app_pids" | tr ' ' '\n' | /usr/bin/grep -v '^$' | sort -u | tr '\n' ' ')"

# 外部の推論サーバも、この配布物の中の python で動いているものだけを対象にする
_mas_pid=""
if [ -x "$MAS_ENV_DIR/bin/python" ]; then
    _mas_pid="$(/bin/ps -Ao pid=,command= 2>/dev/null \
        | /usr/bin/grep -F "$MAS_ENV_DIR/bin/python" \
        | /usr/bin/grep -F "mas_server.py" \
        | /usr/bin/awk '{print $1}' | head -1)"
fi

# ── 4. 1回目の確認 ─────────────────────────────────────────
echo ""
echo "============================================================"
echo " Cynovela を手元から取り除きます"
echo "============================================================"
echo ""
echo "読み取った名前:"
echo "  この配布物のための conda 環境 : ${DIST_ENV}"
echo "  この配布物の中の保存先        : ${VENV_DIR}"
echo "  このフォルダ                 : ${REPO}"
echo ""
echo "実際に在るものと突き合わせた結果:"
if [ -n "$_app_pids" ]; then
    for _p in $_app_pids; do
        echo "  動いている本体 (番号 ${_p}) : 在ります → 止めます"
    done
else
    echo "  動いている本体 : ありません → 何もしません"
fi
if [ -n "$_mas_pid" ]; then
    echo "  外部の推論サーバ (このフォルダの python で動いているもの・番号 ${_mas_pid}) : 在ります → 止めます"
else
    echo "  外部の推論サーバ (このフォルダの python で動いているもの) : ありません → 何もしません"
fi
if [ "$_have_conda_env" = "1" ]; then
    echo "  conda 環境 ${DIST_ENV} : 在ります (${CONDA_ENV_DIR}) → 消します"
else
    echo "  conda 環境 ${DIST_ENV} : ありません → 何もしません"
fi
if [ "$_have_venv" = "1" ]; then
    echo "  保存先 .venv-cynovela : 在ります → 下のフォルダごとゴミ箱へ入ります"
else
    echo "  保存先 .venv-cynovela : ありません → 何もしません"
fi
if [ "$_have_masenv" = "1" ]; then
    echo "  外部の推論サーバの python の環境 .mas-env : 在ります → 下のフォルダごとゴミ箱へ入ります"
else
    echo "  外部の推論サーバの python の環境 .mas-env : ありません → 何もしません"
fi
echo "  このフォルダ       : ${REPO}"
echo "                     → ゴミ箱へ入れます (取り込んだ資料と設定も、この中に在ります)"
echo ""
echo "取り除かないもの:"
echo "  conda そのもの     : そのまま残します (他の用途でお使いになるためです)"
echo "  共有の conda 環境  : 触りません (この配布物が作っていないものは対象になりません)"
echo "  上に出ていない名前の環境・フォルダ : 触りません"
echo ""
echo "  1) 進む"
echo "  2) やめる"
printf '番号を入れてください [1/2]: '
if ! IFS= read -r _ans; then
    echo ""
    echo "入力が閉じたため、やめました。何もしていません。"
    exit 0
fi
case "$_ans" in
    1) : ;;
    *) echo "やめました。何もしていません。"; exit 0 ;;
esac

# ── 5. 2回目の確認 ─────────────────────────────────────────
echo ""
echo "------------------------------------------------------------"
echo " もう一度お尋ねします"
echo "------------------------------------------------------------"
echo "  取り込んだ資料と、画面で行った設定も一緒に無くなります。"
echo "  conda 環境を消すと、その中身は戻せません。"
echo "  このフォルダはゴミ箱へ入ります。ゴミ箱から戻すことはできます。"
echo "  ディスクの容量は、ゴミ箱を空にするまで戻りません。"
echo ""
echo "  進める場合は、次の語をそのまま入れてください: uninstall"
printf '入力: '
if ! IFS= read -r _ans2; then
    echo ""
    echo "入力が閉じたため、やめました。何もしていません。"
    exit 0
fi
if [ "$_ans2" != "uninstall" ]; then
    echo "入力が違うため、やめました。何もしていません。"
    exit 0
fi

# ── 6. ここから一括で行う。途中で問い直さない ────────────────
echo ""
echo "[1/4] 動いている本体を止めます"
if [ -n "$_app_pids" ]; then
    for _p in $_app_pids; do
        kill -TERM "$_p" 2>/dev/null || true
    done
    sleep 2
    for _p in $_app_pids; do
        if kill -0 "$_p" 2>/dev/null; then
            kill -9 "$_p" 2>/dev/null || true
        fi
    done
    for _p in $_app_pids; do
        if kill -0 "$_p" 2>/dev/null; then
            echo "      止められませんでした (番号 ${_p})"
        else
            echo "      止めました (番号 ${_p})"
        fi
    done
    rm -f "$DATA_DIR/server.pid" 2>/dev/null || true
else
    echo "      動いていません"
fi

echo "[2/4] 外部の推論サーバを止めます"
if [ -n "$_mas_pid" ]; then
    kill -TERM "$_mas_pid" 2>/dev/null && echo "      止めました (番号 ${_mas_pid})" || echo "      止められませんでした (番号 ${_mas_pid})"
else
    echo "      動いていません"
fi

echo "[3/4] この配布物のための conda 環境を消します"
if [ "$_have_conda_env" = "1" ]; then
    _conda_err=""
    if [ -n "$CONDA_BIN" ]; then
        # A-6 (DD-CYN-0142 §5-F): 結果を捨てない。失敗の理由を受け取って出す。
        _conda_err="$("$CONDA_BIN" env remove -n "$DIST_ENV" --yes 2>&1 >/dev/null || true)"
    fi
    if [ -d "$CONDA_ENV_DIR" ]; then
        echo "      消せませんでした: ${DIST_ENV} (${CONDA_ENV_DIR})"
        [ -n "$_conda_err" ] && printf '%s\n' "$_conda_err" | head -3 | sed 's/^/      理由: /'
        echo "      次の一手: 手で消す場合は conda env remove -n ${DIST_ENV}"
    else
        echo "      消しました: ${DIST_ENV}"
    fi
else
    echo "      ありません"
fi

echo "[4/4] このフォルダをゴミ箱へ入れます"
echo "      ${REPO}"
# この道そのものがゴミ箱へ入る対象に含まれる。∴ 走っている shell から切り離し、
# 自分が読み終わったあとに動く別の仕組み (osascript) へ渡す。
# Finder に頼むため、別のディスクに置かれている場合も、そのディスクのゴミ箱へ入る。
# .venv-cynovela と .mas-env と store/ は、このフォルダの中に在るので一緒に入る。
# A-6 (DD-CYN-0142 §5-F): Finder へ渡した結果 (終了コードと標準エラー) を捨てずに受け取り、
# 失敗したときは理由と次の一手を出す。成否の最終判定は従来どおり「実際に消えたか」で行う。
_trash_err="$(/usr/bin/osascript -e "tell application \"Finder\" to move POSIX file \"${REPO}\" to trash" 2>&1 >/dev/null)"
_trash_rc=$?
_TRASH_OK=1
if [ -d "$REPO" ]; then
    _TRASH_OK=0
    echo "      ゴミ箱へ入れられませんでした。"
    if [ -n "$_trash_err" ] || [ "$_trash_rc" != "0" ]; then
        echo "      Finder が返した理由: ${_trash_err:-終了コード ${_trash_rc}}"
    fi
    case "$_trash_err" in
        *"-1743"*|*"not allowed"*|*"許可"*)
            echo "      見立て: ターミナルから Finder を操作する許可がありません。"
            echo "      次の一手: システム設定 > プライバシーとセキュリティ > オートメーション で"
            echo "                ターミナルに Finder の操作を許可し、もう一度 bash uninstall.sh を実行してください。"
            ;;
        *)
            echo "      次の一手: Finder でこのフォルダを手でゴミ箱へ移してください: ${REPO}"
            ;;
    esac
    case "$REPO" in
        *"/Library/Mobile Documents"*|*"/Library/CloudStorage"*|*"/Dropbox/"*|*"/OneDrive"*|*"/Google Drive"*|*"/GoogleDrive"*)
            echo "      注意: このフォルダはクラウド同期の下にあります。同期がファイルの実体を手元から"
            echo "            退避している (雲マークのファイルがある) と、ゴミ箱への移動が終わらないことが"
            echo "            あります。先に同期側で実体をこの機械へ戻すか、同期の管理画面から削除してください。"
            ;;
    esac
else
    echo "      ゴミ箱へ入れました"
fi

echo ""
echo "------------------------------------------------------------"
if [ "$_TRASH_OK" = "1" ]; then
    echo " 終わりました"
else
    echo " 一部が残っています (上の [4/4] の理由と次の一手を見てください)"
fi
echo "------------------------------------------------------------"
echo "  ディスクの容量は、ゴミ箱を空にするまで戻りません。"
echo "  conda はそのまま残しています。取り除く場合は、お使いの入れ方に合わせて行ってください。"
echo ""
