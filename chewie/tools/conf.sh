#!/bin/bash
# Cynovela 設定の読み取り ()
#   設定の保存先は cynovela.yaml 1本だけとする。環境変数では受け取らない。
#   起動の道すじ (Cynovela-start.command → launcher-core.sh → launch.sh → run-container.sh) の
#   どの段からも、この1本を読む。
#
#   使い方: . "<配布物のルートディレクトリ>/tools/conf.sh"      (先に CONF_REPO を入れておく)
#           conf_get server port                 → 値を1行で返す。無ければ空
#           conf_get_or server port 8801         → 無いときに使う値を指定する
#
#   読み方は2段組みの yaml だけに絞ってある (例: server: の下の port:)。
#   外の部品を要らないよう awk だけで読む。値の前後の引用符と、行末の注釈は落とす。
CONF_FILE="${CONF_REPO:-.}/cynovela.yaml"

conf_get() {  # conf_get <上の名前> <下の名前>
    [ -f "$CONF_FILE" ] || return 0
    awk -v sec="$1" -v key="$2" '
        # 字下げの無い行は上の名前。目当ての節に入ったかどうかを持ち替える
        /^[A-Za-z_]/ { insec = ($0 == sec ":") ; next }
        insec {
            line = $0
            # 下の名前は字下げ2つ。さらに深いものは見ない
            if (line !~ "^  " key ":") next
            sub("^  " key ":", "", line)
            sub(/[ \t]+#.*$/, "", line)      # 行末の注釈を落とす
            sub(/^[ \t]+/, "", line)
            sub(/[ \t]+$/, "", line)
            gsub(/^["'"'"']|["'"'"']$/, "", line)   # 前後の引用符を落とす
            print line
            exit
        }
    ' "$CONF_FILE"
}

conf_get_or() {  # conf_get_or <上の名前> <下の名前> <無いときの値>
    local v
    v="$(conf_get "$1" "$2")"
    if [ -z "$v" ]; then printf '%s\n' "$3"; else printf '%s\n' "$v"; fi
}

conf_get_num() {  # conf_get_num <上の名前> <下の名前> <無いとき/読めないときの値>
    # 番号として読めない値 (空・綴り違い・数字でない) は、黙って既定へ戻す。
    local v
    v="$(conf_get "$1" "$2")"
    case "$v" in
        ''|*[!0-9]*) printf '%s\n' "$3" ;;
        *)           printf '%s\n' "$v" ;;
    esac
}

conf_set() {  # conf_set <上の名前> <下の名前> <値>   その行だけを書き替える (注釈は残す)
    [ -f "$CONF_FILE" ] || return 1
    local tmp="$CONF_FILE.tmp.$$"
    awk -v sec="$1" -v key="$2" -v val="$3" '
        /^[A-Za-z_]/ { insec = ($0 == sec ":") }
        {
            if (insec && $0 ~ "^  " key ":" && done != 1) {
                printf "  %s: %s\n", key, (val == "" ? "'"''"'" : val)
                done = 1
                next
            }
            print
        }
        END { if (done != 1) exit 3 }
    ' "$CONF_FILE" > "$tmp" || { rm -f "$tmp"; return 1; }
    mv "$tmp" "$CONF_FILE"
}

_conf_py_meets() {  # R-1: $1=python の場所 → 動作要件 (3.12 以上) を満たすなら 0
    # 名前で当てず、その python 自身に版を答えさせる。名前が python でも中身が 3.12 なら通る。
    [ -n "${1:-}" ] && [ -x "$1" ] || return 1
    "$1" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 12) else 1)' >/dev/null 2>&1
}

conf_pick_py() {  # F-c / R-1
    #   $1=ディレクトリツリーのルート、$2 以降=呼ぶ側が既に解いた python (任意・この順で先に見る)
    #   → 動作要件 (3.12 以上) を満たす python の絶対パスを出す。
    #
    # R-1: 版は名前で当てず、必ずその python に答えさせる。
    #   旧: 名前が python3.12 / python3.13 のものと、この形態の自前環境だけを見ていた。
    #       ∴ 配布物専用の conda 環境 'cynovela-dist' の python は、中身が 3.12.13 でも
    #       名前が python なので候補から外れ、同じ書き出しの中で
    #         使う python      : .../envs/cynovela-dist/bin/python   版: Python 3.12.13
    #         バックアップに使う python: ありません (3.12 系が見つかりません)
    #       という食い違いを出していた (M5 実測)。
    #   新: 呼ぶ側が既に解いた python を第一候補にし、要件を満たすならそこで探索を終える。
    #       名前に版の付かない python3 も、版を実測して満たすときだけ受ける。
    #       「素の python3 へ版の検査なしに倒れない」という F-c の縛りはそのまま保つ。
    local _root="$1" _c _b _e
    shift
    for _c in "$@"; do
        if _conf_py_meets "$_c"; then printf '%s\n' "$_c"; return 0; fi
    done
    # この配布物の中に作られる保存先 (形態によって名前が違うので両方見る)
    for _c in "$_root/.venv-cynovela/bin/python3" "$_root/.mas-env/bin/python3"; do
        if _conf_py_meets "$_c"; then printf '%s\n' "$_c"; return 0; fi
    done
    # 配布物専用の conda 環境。名前が python なので、版を実測しないと当てられない。
    for _b in "$HOME/miniforge3" "$HOME/miniconda3" "/opt/homebrew/Caskroom/miniforge/base" \
              "$HOME/opt/anaconda3" "$HOME/anaconda3" "/usr/local/anaconda3"; do
        for _e in cynovela-dist cynovela; do
            if _conf_py_meets "$_b/envs/$_e/bin/python"; then
                printf '%s\n' "$_b/envs/$_e/bin/python"
                return 0
            fi
        done
    done
    for _c in python3.12 python3.13 python3; do
        if command -v "$_c" >/dev/null 2>&1 && _conf_py_meets "$(command -v "$_c")"; then
            command -v "$_c"
            return 0
        fi
    done
    return 1
}
