"""The embedding status banner in frontend/index.html polls
GET /api/settings/embedding. That endpoint is for administrators only, and every
unauthenticated or forbidden request writes one auth_failed row to the audit
log. The poll must therefore run only with a token, only for administrators,
and stop for a token that received 403.
"""
import re
from pathlib import Path

INDEX = (Path(__file__).resolve().parent.parent / "frontend" / "index.html").read_text(encoding="utf-8")


def _func_body(src: str, header_regex: str) -> str:
    m = re.search(header_regex, src)
    assert m, header_regex
    i = src.index("{", m.end() - 1)
    depth = 0
    for j in range(i, len(src)):
        if src[j] == "{":
            depth += 1
        elif src[j] == "}":
            depth -= 1
            if depth == 0:
                return src[i:j + 1]
    raise AssertionError("no closing brace")


def _check_body() -> str:
    # the check() that belongs to the embedding banner
    start = INDEX.index("embed-state-banner")
    return _func_body(INDEX[start:], r"async function check\(\)\s*\{")


def test_no_request_without_token():
    body = _check_body()
    call = body.index("/api/settings/embedding")
    guard = re.search(r"if\(\s*!_a\s*\|\|\s*!_a\.token\s*\)\s*return", body)
    assert guard and guard.start() < call


def test_no_request_for_non_admin():
    body = _check_body()
    call = body.index("/api/settings/embedding")
    role = re.search(r"State\.user\.role\s*!==\s*'admin'\)\s*return", body)
    assert role and role.start() < call


def test_stops_after_403_for_that_token():
    body = _check_body()
    call = body.index("/api/settings/embedding")
    skip = re.search(r"deniedToken\s*===\s*_a\.token\)\s*return", body)
    assert skip and skip.start() < call
    assert re.search(r"res\.status\s*===\s*403\)\s*\{\s*deniedToken\s*=\s*_tok", body[call:])


def test_only_one_request_site_in_check():
    body = _check_body()
    assert body.count("/api/settings/embedding") == 1
    assert "_a.get(" not in body


# --- behaviour, run in Node.js when it is installed -------------------------

import json  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402

import pytest  # noqa: E402

_NODE_HARNESS = r"""
const vm = require('vm');
const src = require('fs').readFileSync(0, 'utf8');
const calls = [];
let status = 200;
const ctx = {
  console,
  window: {},
  document: { readyState: 'complete', getElementById: () => null, addEventListener() {} },
  setInterval: () => 0, clearInterval() {}, setTimeout: () => 0,
  fetch: async (url, opts) => { calls.push(url); return { status, ok: status === 200, json: async () => ({}) }; },
  API: { base: 'http://x', token: null, get() { throw new Error('API.get must not be used'); },
         headers() { return {}; }, _handleSessionExpired() {} },
  State: { user: null },
};
vm.createContext(ctx);
vm.runInContext(src, ctx);
(async () => {
  const check = ctx.window._checkEmbeddingState;
  const out = {};
  await check(); out.no_token = calls.length;
  ctx.API.token = 't-viewer'; ctx.State.user = { role: 'viewer' };
  await check(); out.viewer = calls.length;
  ctx.State.user = { role: 'admin' };
  await check(); out.admin_first = calls.length;
  status = 403;
  await check(); out.after_403_call = calls.length;
  await check(); await check(); out.after_403_more = calls.length;
  ctx.API.token = 't-other';
  await check(); out.new_token = calls.length;
  process.stdout.write(JSON.stringify(out));
})();
"""


def _banner_script() -> str:
    start = INDEX.index("embed-state-banner")
    s = INDEX.index("<script>", start) + len("<script>")
    e = INDEX.index("</script>", s)
    return INDEX[s:e]


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")
def test_poll_behaviour_in_node():
    proc = subprocess.run(
        ["node", "-e", _NODE_HARNESS], input=_banner_script(), capture_output=True, text=True, timeout=60
    )
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert out["no_token"] == 0          # before login: no request
    assert out["viewer"] == 0            # viewer screen: no request
    assert out["admin_first"] == 1       # admin: one request
    assert out["after_403_call"] == 2    # the request that got 403
    assert out["after_403_more"] == 2    # nothing more for that token
    assert out["new_token"] == 3         # a new sign-in starts again
