#!/bin/bash
# Cynovela 設定の読み取り (DD-CYN-0053)
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

# DD-CYN-0074 Q-2: コンテナ・名札・保存領域の「無いときの値」は、この1本にだけ書く。
#   起動の道すじの各段は、この値を conf_get_or の第3引数へ渡す。∴ 名前の綴りが
#   スクリプトへ散らばらない。cynovela.yaml に値が在れば必ずそちらが勝つ。
#   ここは cynovela.yaml が欠けた・空だったときの受け皿にすぎない。
#   配布物ごとの実際の名前は cynovela.yaml の container: に書いてある。
CONF_DEFAULT_CNAME="cynovela"
CONF_DEFAULT_IMAGE="cynovela:latest"
CONF_DEFAULT_VOLPREFIX="cyn"

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

conf_pick_py() {  # DD-CYN-0107 F-c: $1=ディレクトリツリーのルート → 動作要件 (3.12 系) を満たす python の絶対パスを出す
    # 操作手順 (tools/mas-phase.sh) が作る .mas-env を最優先で使う。無ければ名前で探す。
    # 素の python3 (版の検査なし) へは倒れない。見つからなければ 1 を返し、呼ぶ側がガイドを出す。
    local _root="$1" _c
    if [ -x "$_root/.mas-env/bin/python3" ]; then
        printf '%s\n' "$_root/.mas-env/bin/python3"
        return 0
    fi
    for _c in python3.12 python3.13; do
        if command -v "$_c" >/dev/null 2>&1; then
            command -v "$_c"
            return 0
        fi
    done
    return 1
}
