#!/bin/bash
# DD-CYN-0140 §5-J-4 / §5-K-2 + DD-CYN-0141 §5-G: CLI と MCP の動作確認を1本で回す。
# パッケージ版とソース版の両方へ、Python と接続先だけ替えて使う。
#
# 使い方:
#   bash tools/check-cli-mcp.sh <python> [base_url] [token]
#     <python>   使う Python (例: ./.venv-cynovela/bin/python3)
#     [base_url] 既定 http://127.0.0.1:8765
#     [token]    ログインで発行されたトークン。無ければ認証つき命令は
#                「認証失敗(3)を正しく返すか」の検査に切り替わる。
#
# サーバの状態は変えない (読むだけの命令と、MCP の一覧・エラー経路のみ。
# settings set は --dry-run と「--yes 無しは実行しない」の検査だけで、書き込まない)。
# 出力は「主張 → 生出力」の並び。最後に PASS/FAIL の数を出す。
set -u
PY="${1:?usage: check-cli-mcp.sh <python> [base_url] [token]}"
BASE="${2:-http://127.0.0.1:8765}"
TOKEN="${3:-}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
CLI="$HERE/cynovela-cli.py"
MCP="$HERE/mcp_server.py"
PASS=0; FAIL=0

say()  { printf '\n== %s ==\n' "$1"; }
chk()  { # chk <expected_exit> <label> -- cmd...
  local want="$1" label="$2"; shift 2; shift # drop --
  "$@"; local got=$?
  if [ "$got" = "$want" ]; then PASS=$((PASS+1)); echo "[PASS] $label (exit=$got)";
  else FAIL=$((FAIL+1)); echo "[FAIL] $label (exit=$got, expected $want)"; fi
}

say "0) 前提"
"$PY" --version || { echo "python が動きません"; exit 1; }
echo "CLI=$CLI"; echo "BASE=$BASE"; echo "TOKEN=$([ -n "$TOKEN" ] && echo '(given)' || echo '(none)')"

say "1) doctor はサーバの状態に関わらず落ちない"
chk 0 "doctor" -- "$PY" "$CLI" doctor

say "2) status"
if "$PY" "$CLI" --url "$BASE" status >/dev/null 2>&1; then
  chk 0 "status (server up)" -- "$PY" "$CLI" --url "$BASE" status
  SERVER_UP=1
else
  chk 2 "status (server down -> 2)" -- "$PY" "$CLI" --url "$BASE" status
  SERVER_UP=0
fi

say "3) 到達できない接続先は 2"
chk 2 "unreachable -> 2" -- "$PY" "$CLI" --url "http://127.0.0.1:59999" status

say "4) 入力の誤りは 1"
chk 1 "unknown command -> 1" -- "$PY" "$CLI" frobnicate
chk 1 "missing required arg -> 1" -- "$PY" "$CLI" search --workspace x
chk 1 "settings show bogus -> 1" -- "$PY" "$CLI" settings show bogus
chk 1 "settings set without --set -> 1" -- "$PY" "$CLI" settings set llm

if [ "$SERVER_UP" = 1 ]; then
  say "5) 認証"
  chk 3 "bad token -> 3" -- "$PY" "$CLI" --url "$BASE" --token bad-token-value workspaces
  chk 3 "settings show (bad token) -> 3" -- "$PY" "$CLI" --url "$BASE" --token bad-token-value settings show
  if [ -n "$TOKEN" ]; then
    chk 0 "workspaces" -- "$PY" "$CLI" --url "$BASE" --token "$TOKEN" workspaces
    chk 0 "collections" -- "$PY" "$CLI" --url "$BASE" --token "$TOKEN" collections
    chk 0 "index-status" -- "$PY" "$CLI" --url "$BASE" --token "$TOKEN" index-status
    say "5b) settings (DD-CYN-0141 §5-A。admin token のときだけ 0、viewer token なら 3 が正)"
    if "$PY" "$CLI" --url "$BASE" --token "$TOKEN" settings show >/dev/null 2>&1; then
      chk 0 "settings show" -- "$PY" "$CLI" --url "$BASE" --token "$TOKEN" settings show
      chk 0 "settings show reranker" -- "$PY" "$CLI" --url "$BASE" --token "$TOKEN" settings show reranker
      chk 0 "settings models" -- "$PY" "$CLI" --url "$BASE" --token "$TOKEN" settings models
      chk 0 "settings test" -- "$PY" "$CLI" --url "$BASE" --token "$TOKEN" settings test
      chk 0 "settings providers" -- "$PY" "$CLI" --url "$BASE" --token "$TOKEN" settings providers
      chk 0 "settings set --dry-run (書かない)" -- "$PY" "$CLI" --url "$BASE" --token "$TOKEN" settings set llm --set model=check-cli-mcp-dryrun --dry-run
      chk 1 "settings set without --yes -> 1 (書かない)" -- "$PY" "$CLI" --url "$BASE" --token "$TOKEN" settings set llm --set model=check-cli-mcp-noyes
      "$PY" "$CLI" --url "$BASE" --token "$TOKEN" --json settings show > /tmp/cynovela-cli-check-settings.json
      chk 0 "settings show --json は APIキーの値を含まない" -- "$PY" -c "
import json;d=json.load(open('/tmp/cynovela-cli-check-settings.json'))
s=d['data']['settings']
assert d['ok'] is True and 'api_key' not in s and isinstance(s.get('api_key_set'), bool)"
      rm -f /tmp/cynovela-cli-check-settings.json
    else
      chk 3 "settings show (viewer token) -> 3" -- "$PY" "$CLI" --url "$BASE" --token "$TOKEN" settings show
      chk 3 "settings set (viewer token) -> 3" -- "$PY" "$CLI" --url "$BASE" --token "$TOKEN" settings set llm --set model=x --yes
    fi
    say "6) --json は機械で読める"
    "$PY" "$CLI" --url "$BASE" --token "$TOKEN" --json workspaces > /tmp/cynovela-cli-check.json
    chk 0 "--json parses" -- "$PY" -c "import json;d=json.load(open('/tmp/cynovela-cli-check.json'));assert d['ok'] is True and 'data' in d"
    rm -f /tmp/cynovela-cli-check.json
  else
    echo "(token 無し: 認証つき命令の正常系は飛ばします)"
  fi
fi

say "7) MCP: server/discover / tools/list / エラー経路 (stdio)"
MCPOUT="$("$PY" "$MCP" --cynovela-url "$BASE" <<'EOF'
{"jsonrpc":"2.0","id":1,"method":"server/discover"}
{"jsonrpc":"2.0","id":2,"method":"tools/list"}
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"no_such_tool","arguments":{}}}
{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"search_collection","arguments":{"workspace_id":"w"}}}
{"jsonrpc":"2.0","id":5,"method":"nonexistent/method"}
{"jsonrpc":"2.0","id":6,"method":"tools/call","params":{"name":"settings_show","arguments":{"name":"bogus"}}}
{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":"settings_set","arguments":{"values":{"model":"x"}}}}
EOF
)"
echo "$MCPOUT"
echo "$MCPOUT" | "$PY" -c '
import json, sys
lines = [json.loads(l) for l in sys.stdin if l.strip()]
by_id = {d.get("id"): d for d in lines}
ok = True
def need(cond, label):
    global ok
    print(("[PASS] " if cond else "[FAIL] ") + label)
    ok = ok and cond
need(by_id[1]["result"]["protocolVersion"] == "2026-07-28", "discover: protocolVersion 2026-07-28")
tools = by_id[2]["result"]["tools"]
need(len(tools) == 16, f"tools/list: 16 tools (got {len(tools)})")
need(all(t["inputSchema"].get("$schema","").endswith("2020-12/schema") for t in tools), "all inputSchema declare 2020-12")
need(all("outputSchema" in t for t in tools), "all tools declare outputSchema")
need(by_id[3]["error"]["code"] == -32602, "unknown tool -> -32602")
need(by_id[4]["error"]["code"] == -32602, "missing required arg -> -32602")
need(by_id[5]["error"]["code"] == -32601, "unknown method -> -32601")
need(by_id[6]["error"]["code"] == -32602, "settings_show bad name (enum) -> -32602")
r7 = by_id[7]["result"]
need(r7["isError"] is True and "閉じています" in r7["content"][0]["text"],
     "settings_set is closed by default (isError + explanation)")
sys.exit(0 if ok else 1)
'
if [ $? = 0 ]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi

if [ "$SERVER_UP" = 1 ] && [ -n "$TOKEN" ]; then
  say "8) MCP: 実データの道具 (list_workspaces, structuredContent)"
  OUT="$(CYNOVELA_TOKEN="$TOKEN" "$PY" "$MCP" --cynovela-url "$BASE" <<'EOF'
{"jsonrpc":"2.0","id":10,"method":"tools/call","params":{"name":"list_workspaces","arguments":{}}}
EOF
)"
  echo "$OUT"
  echo "$OUT" | "$PY" -c '
import json, sys
d = json.loads(sys.stdin.read())
r = d["result"]
assert r["isError"] is False and "structuredContent" in r and "workspaces" in r["structuredContent"]
print("[PASS] list_workspaces returns structuredContent.workspaces")
'
  if [ $? = 0 ]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); echo "[FAIL] list_workspaces structuredContent"; fi
fi

say "結果"
echo "PASS=$PASS FAIL=$FAIL"
[ "$FAIL" = 0 ]
