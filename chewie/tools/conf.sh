#!/bin/bash
# Cynovela 設定の読み取り (DD-CYN-0053)
#   設定の置き場は cynovela.yaml 1本だけとする。環境変数では受け取らない。
#   起動の道すじ (Cynovela-start.command → launcher-core.sh → launch.sh → run-container.sh) の
#   どの段からも、この1本を読む。
#
#   使い方: . "<配布物の根>/tools/conf.sh"      (先に CONF_REPO を入れておく)
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
