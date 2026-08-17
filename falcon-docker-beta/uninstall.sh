#!/bin/bash
# Cynovela を手元から取り除くための道 ()
#
#   ターミナルから叩きます:  bash uninstall.sh
#
#   この道がすること (順):
#     1. 何を取り除くかを全部画面へ出し、1回目の確認をします
#     2. 取り返しがつかないことを示し、2回目の確認をします
#     3. 以後は一括で行い、途中で問い直しません
#     4. 外部の推論サーバ (Mac Accelerator Service) を止めます
#     5. コンテナを止めて消します
#     6. 名前つきの保存領域を消します
#     7. イメージを消します
#     8. このフォルダをゴミ箱へ入れます
#
#   消す相手の名前は cynovela.yaml から読みます。決め打ちしていません。
#   ∴ 別の Cynovela をお持ちでも、そちらは対象になりません。
#
#   Podman は取り除きません。他の用途でお使いになるためです。
#
#   最後はゴミ箱へ入れるだけです。ゴミ箱を空にするまで、ディスクの容量は戻りません。
set -u

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONF_REPO="$REPO"
. "$REPO/tools/conf.sh"

# ── 1. 相手の名前を設定から読む (決め打ちしない) ──────────────
NAME="$(conf_get_or container name "$CONF_DEFAULT_CNAME")"
IMG="$(conf_get_or container image "$CONF_DEFAULT_IMAGE")"
VOLPREFIX="$(conf_get_or container volume_prefix "$CONF_DEFAULT_VOLPREFIX")"
ENG="$(conf_get container engine)"
[ -n "$ENG" ] || ENG="podman"
command -v "$ENG" >/dev/null 2>&1 || ENG="podman"

MAS_ENV_DIR="$REPO/.mas-env"

# ── 2. 実際に在るものを調べる ───────────────────────────────
_have_container=0
_have_image=0
_vols_found=()
_vols_missing=()
_mas_pid=""

if command -v "$ENG" >/dev/null 2>&1; then
    "$ENG" container exists "$NAME" 2>/dev/null && _have_container=1
    if "$ENG" image exists "$IMG" 2>/dev/null || "$ENG" image exists "localhost/$IMG" 2>/dev/null; then
        _have_image=1
    fi
    for _suffix in db vec bk; do
        _v="${VOLPREFIX}-${_suffix}"
        if "$ENG" volume exists "$_v" 2>/dev/null; then
            _vols_found+=("$_v")
        else
            _vols_missing+=("$_v")
        fi
    done
fi

# 外部の推論サーバは、この配布物の中の python で動いているものだけを対象にする
if [ -x "$MAS_ENV_DIR/bin/python" ]; then
    _mas_pid="$(/bin/ps -Ao pid=,command= 2>/dev/null \
        | /usr/bin/grep -F "$MAS_ENV_DIR/bin/python" \
        | /usr/bin/grep -F "mas_server.py" \
        | /usr/bin/awk '{print $1}' | head -1)"
fi

# ── 3. 1回目の確認 ─────────────────────────────────────────
echo ""
echo "============================================================"
echo " Cynovela を手元から取り除きます"
echo "============================================================"
echo ""
echo "設定 (cynovela.yaml) から読み取った名前:"
echo "  コンテナ           : ${NAME}"
echo "  イメージ           : ${IMG}"
echo "  保存領域の名前の頭  : ${VOLPREFIX}"
echo "  使う実行ファイル    : ${ENG}"
echo ""
echo "実際に在るものと突き合わせた結果:"
if [ "$_have_container" = "1" ]; then
    echo "  コンテナ ${NAME} : 在ります → 止めて消します"
else
    echo "  コンテナ ${NAME} : ありません → 何もしません"
fi
if [ "${#_vols_found[@]}" -gt 0 ]; then
    for _v in "${_vols_found[@]}"; do echo "  保存領域 ${_v} : 在ります → 消します"; done
fi
if [ "${#_vols_missing[@]}" -gt 0 ]; then
    for _v in "${_vols_missing[@]}"; do echo "  保存領域 ${_v} : ありません → 何もしません"; done
fi
if [ "$_have_image" = "1" ]; then
    echo "  イメージ ${IMG} : 在ります → 消します"
else
    echo "  イメージ ${IMG} : ありません → 何もしません"
fi
if [ -n "$_mas_pid" ]; then
    echo "  外部の推論サーバ (このフォルダの python で動いているもの・番号 ${_mas_pid}) : 在ります → 止めます"
else
    echo "  外部の推論サーバ (このフォルダの python で動いているもの) : ありません → 何もしません"
fi
if [ -d "$MAS_ENV_DIR" ]; then
    echo "  外部の推論サーバの python の環境 ${MAS_ENV_DIR} : 在ります → 下のフォルダごとゴミ箱へ入ります"
else
    echo "  外部の推論サーバの python の環境 (.mas-env) : ありません → 何もしません"
fi
echo "  このフォルダ       : ${REPO}"
echo "                     → ゴミ箱へ入れます"
echo ""
echo "取り除かないもの:"
echo "  Podman            : そのまま残します (他の用途でお使いになるためです)"
echo "  上に出ていない名前のコンテナ・保存領域・イメージ : 触りません"
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

# ── 4. 2回目の確認 ─────────────────────────────────────────
echo ""
echo "------------------------------------------------------------"
echo " もう一度お尋ねします"
echo "------------------------------------------------------------"
echo "  取り込んだ資料と、画面で行った設定も一緒に無くなります。"
echo "  保存領域を消すと、その中身は戻せません。"
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

# ── 5. ここから一括で行う。途中で問い直さない ────────────────
echo ""
echo "[1/5] 外部の推論サーバを止めます"
if [ -n "$_mas_pid" ]; then
    kill -TERM "$_mas_pid" 2>/dev/null && echo "      止めました (番号 ${_mas_pid})" || echo "      止められませんでした (番号 ${_mas_pid})"
else
    echo "      動いていません"
fi

echo "[2/5] コンテナを止めて消します"
if [ "$_have_container" = "1" ]; then
    "$ENG" stop "$NAME" >/dev/null 2>&1 || true
    "$ENG" rm "$NAME" >/dev/null 2>&1 && echo "      消しました: ${NAME}" || echo "      消せませんでした: ${NAME}"
else
    echo "      ありません"
fi

echo "[3/5] 名前つきの保存領域を消します"
if [ "${#_vols_found[@]}" -gt 0 ]; then
    for _v in "${_vols_found[@]}"; do
        "$ENG" volume rm "$_v" >/dev/null 2>&1 && echo "      消しました: ${_v}" || echo "      消せませんでした: ${_v}"
    done
else
    echo "      ありません"
fi

echo "[4/5] イメージを消します"
if [ "$_have_image" = "1" ]; then
    "$ENG" rmi "$IMG" >/dev/null 2>&1 || "$ENG" rmi "localhost/$IMG" >/dev/null 2>&1
    if "$ENG" image exists "$IMG" 2>/dev/null || "$ENG" image exists "localhost/$IMG" 2>/dev/null; then
        echo "      消せませんでした: ${IMG}"
    else
        echo "      消しました: ${IMG}"
    fi
else
    echo "      ありません"
fi

echo "[5/5] このフォルダをゴミ箱へ入れます"
echo "      ${REPO}"
# この道そのものがゴミ箱へ入る対象に含まれる。∴ 走っている shell から切り離し、
# 自分が読み終わったあとに動く別の仕組み (osascript) へ渡す。
# Finder に頼むため、別のディスクに置かれている場合も、そのディスクのゴミ箱へ入る。
/usr/bin/osascript -e "tell application \"Finder\" to move POSIX file \"${REPO}\" to trash" >/dev/null 2>&1
if [ -d "$REPO" ]; then
    echo "      ゴミ箱へ入れられませんでした。手で移してください: ${REPO}"
else
    echo "      ゴミ箱へ入れました"
fi

echo ""
echo "------------------------------------------------------------"
echo " 終わりました"
echo "------------------------------------------------------------"
echo "  ディスクの容量は、ゴミ箱を空にするまで戻りません。"
echo "  Podman はそのまま残しています。取り除く場合は Podman Desktop から行ってください。"
echo ""
