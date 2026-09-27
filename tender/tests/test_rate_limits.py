"""Per-path rate limits applied by the HTTP middleware in server.py.

The limits count per client address and per path, in the memory of one
process. Each test runs server.py in a fresh child process (see conftest.py),
so the counters start at 0. The suite does not switch rate limiting off:
server.py has no switch for it.
"""

LOGIN = r'''
import json, server, db
from fastapi.testclient import TestClient
db.init_db()
c = TestClient(server.app, raise_server_exceptions=False)
codes = [c.post("/api/auth/login", json={"username": "no-such-user", "password": "wrong-pw-x"}).status_code
         for _ in range(8)]
print("RESULT " + json.dumps({"codes": codes}))
'''

FOLLOWUPS = r'''
import json, server, db
from fastapi.testclient import TestClient
db.init_db()
c = TestClient(server.app, raise_server_exceptions=False)
codes = [c.post("/api/chat/followups", json={"answer": "x", "query": "y"}).status_code for _ in range(33)]
body = c.post("/api/chat/followups", json={}).json()
print("RESULT " + json.dumps({"codes": codes, "body": body}))
'''

TABLE = r'''
import json, server
keys = {k: str(v) for k, v in server._strict_rl_items.items()}
probe = {p: server._strict_rl_key(p) for p in [
    "/api/workspaces/abc123/chat/stream", "/api/workspaces/abc123/chat/stream/",
    "/api/admin/users/u1/reset-password", "/api/chat/", "/api/chat/history", "/api/workspaces/abc123"]}
print("RESULT " + json.dumps({"keys": keys, "probe": probe}))
'''


def test_login_is_refused_from_the_6th_attempt(run_server_snippet):
    r = run_server_snippet(LOGIN)
    codes = r["codes"]
    assert codes[:5] == [401] * 5
    assert codes[5] == 429
    assert set(codes[5:]) == {429}


def test_followups_is_refused_from_the_31st_call_even_without_a_token(run_server_snippet):
    r = run_server_snippet(FOLLOWUPS)
    codes = r["codes"]
    assert 429 not in codes[:30], codes[:30]
    assert codes[30] == 429
    assert set(codes[30:]) == {429}
    assert "30 per 1 minute" in r["body"].get("error", "")


def test_strict_limit_table(run_server_snippet):
    r = run_server_snippet(TABLE)
    keys = r["keys"]
    five = {"/api/auth/login", "/api/auth/change-password", "/api/auth/verify-password"}
    thirty = {
        "/api/auth/refresh",
        "/api/chat",
        "/api/rag/query",
        "/api/chat/compare",
        "/api/chat/compare-collections",
        "/api/chat/summarize",
        "/api/chat/followups",
        "/api/agent/chat",
        "/api/workspaces/*/chat/stream",
    }
    for k in five:
        assert keys[k] == "5 per 1 minute", k
    for k in thirty:
        assert keys[k] == "30 per 1 minute", k
    assert keys["/api/admin/users/*/reset-password"] == "10 per 1 minute"
    assert set(keys) == five | thirty | {"/api/admin/users/*/reset-password"}
    p = r["probe"]
    assert p["/api/workspaces/abc123/chat/stream"] == "/api/workspaces/*/chat/stream"
    assert p["/api/workspaces/abc123/chat/stream/"] == "/api/workspaces/*/chat/stream"
    assert p["/api/admin/users/u1/reset-password"] == "/api/admin/users/*/reset-password"
    assert p["/api/chat/"] == "/api/chat"
    assert p["/api/chat/history"] is None
    assert p["/api/workspaces/abc123"] is None
