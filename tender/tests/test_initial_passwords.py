"""First passwords of the two initial users (administrator cynovela, viewer demo).

- cynovela.yaml may hold only hashes (auth.*_initial_password_hash); the
  packaging script writes them, and no plaintext goes into the package.
- On a fresh install both users are created with must_change_password = 1.
- An existing installation keeps the passwords it has (nothing is reset).

The test passwords are generated here and never printed.
"""
import json
import os
import re
import secrets
import subprocess
from pathlib import Path

import pytest

TENDER = Path(__file__).resolve().parent.parent

SEED = r'''
import json, os, sys
data = os.environ["CYNOVELA_DATA_ROOT"]
os.makedirs(os.path.dirname(os.environ["CYNOVELA_DB"]), exist_ok=True)
cfg = json.loads(open(os.path.join(os.path.dirname(data), "cfg.json")).read())
import core.config as cc
_orig = cc.get_yaml_config
def _patched():
    d = dict(_orig() or {})
    d["auth"] = cfg["auth"]
    return d
cc.get_yaml_config = _patched
import db
db.init_db()
pre = cfg.get("pre_existing")
if pre:
    c = db.get_db()
    c.execute("UPDATE users SET password_hash = ?, must_change_password = 0 WHERE id = ?",
              (db.hash_password(pre["viewer"]), "user-scientist"))
    c.execute("UPDATE users SET password_hash = ?, must_change_password = 0 WHERE id = ?",
              (db.hash_password(pre["admin"]), "user-admin"))
    c.commit(); c.close()
    db.init_db()   # second start with the same configuration
c = db.get_db()
rows = {r["id"]: dict(r) for r in c.execute(
    "SELECT id, username, password_hash, must_change_password FROM users WHERE id IN ('user-admin','user-scientist')")}
c.close()
out = {}
for uid, r in rows.items():
    out[uid] = {
        "username": r["username"],
        "must_change": r["must_change_password"],
        "checks": {k: db.verify_password(v, r["password_hash"]) for k, v in cfg["probe"].items()},
    }
print("RESULT " + json.dumps(out))
'''


def _pw():
    return secrets.token_urlsafe(12)


def _hash(pw):
    import hashlib

    salt = secrets.token_hex(16)
    return salt + ":" + hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 100000).hex()


def _run(run_server_snippet, tmp_path, cfg):
    (tmp_path / "cfg.json").write_text(json.dumps(cfg), encoding="utf-8")
    return run_server_snippet(SEED)


def test_fresh_install_from_hashes_both_must_change(run_server_snippet, tmp_path):
    a, v = _pw(), _pw()
    cfg = {
        "auth": {
            "admin_initial_password": "",
            "viewer_initial_password": "",
            "admin_initial_password_hash": _hash(a),
            "viewer_initial_password_hash": _hash(v),
        },
        "probe": {"a": a, "v": v},
    }
    r = _run(run_server_snippet, tmp_path, cfg)
    assert r["user-admin"]["username"] == "cynovela"
    assert r["user-scientist"]["username"] == "demo"
    assert r["user-admin"]["checks"]["a"] is True
    assert r["user-scientist"]["checks"]["v"] is True
    assert r["user-admin"]["must_change"] == 1
    assert r["user-scientist"]["must_change"] == 1


def test_fresh_install_from_plaintext_viewer_must_change(run_server_snippet, tmp_path):
    a, v = _pw(), _pw()
    cfg = {
        "auth": {"admin_initial_password": a, "viewer_initial_password": v},
        "probe": {"a": a, "v": v},
    }
    r = _run(run_server_snippet, tmp_path, cfg)
    assert r["user-admin"]["checks"]["a"] and r["user-scientist"]["checks"]["v"]
    assert r["user-admin"]["must_change"] == 1
    assert r["user-scientist"]["must_change"] == 1


def test_fresh_install_without_values_uses_random_and_must_change(run_server_snippet, tmp_path):
    cfg = {"auth": {}, "probe": {}}
    r = _run(run_server_snippet, tmp_path, cfg)
    assert r["user-admin"]["must_change"] == 1
    assert r["user-scientist"]["must_change"] == 1


def test_malformed_hash_is_not_used(run_server_snippet, tmp_path):
    v = _pw()
    cfg = {"auth": {"viewer_initial_password_hash": "not-a-hash:zz"}, "probe": {"v": v}}
    r = _run(run_server_snippet, tmp_path, cfg)
    assert r["user-scientist"]["checks"]["v"] is False
    assert r["user-scientist"]["must_change"] == 1


def test_existing_installation_is_not_reset(run_server_snippet, tmp_path):
    a, v, a2, v2 = _pw(), _pw(), _pw(), _pw()
    cfg = {
        "auth": {"admin_initial_password_hash": _hash(a), "viewer_initial_password_hash": _hash(v)},
        "pre_existing": {"admin": a2, "viewer": v2},   # passwords the users changed to
        "probe": {"a": a, "v": v, "a2": a2, "v2": v2},
    }
    r = _run(run_server_snippet, tmp_path, cfg)
    assert r["user-admin"]["checks"]["a2"] is True and r["user-admin"]["checks"]["a"] is False
    assert r["user-scientist"]["checks"]["v2"] is True and r["user-scientist"]["checks"]["v"] is False
    assert r["user-admin"]["must_change"] == 0
    assert r["user-scientist"]["must_change"] == 0


VIEWER_API = r'''
import json, os
cfg = json.loads(open(os.path.join(os.path.dirname(os.environ["CYNOVELA_DATA_ROOT"]), "cfg.json")).read())
import core.config as cc
_orig = cc.get_yaml_config
def _patched():
    d = dict(_orig() or {}); d["auth"] = cfg["auth"]; return d
cc.get_yaml_config = _patched
import server, db
from fastapi.testclient import TestClient
db.init_db()
c = TestClient(server.app, raise_server_exceptions=False)
r = c.post("/api/auth/login", json={"username": "demo", "password": cfg["probe"]["v"]})
body = r.json()
tok = body.get("access_token")
h = {"Authorization": "Bearer " + tok} if tok else {}
ws = c.get("/api/workspaces", headers=h).status_code
print("RESULT " + json.dumps({"login": r.status_code, "must_change": body.get("must_change_password"), "workspaces": ws}))
'''


def test_viewer_is_asked_to_change_on_first_sign_in(run_server_snippet, tmp_path):
    v = _pw()
    cfg = {"auth": {"viewer_initial_password_hash": _hash(v)}, "probe": {"v": v}}
    (tmp_path / "cfg.json").write_text(json.dumps(cfg), encoding="utf-8")
    r = run_server_snippet(VIEWER_API)
    assert r["login"] == 200
    assert r["must_change"] is True
    assert r["workspaces"] == 403


# --- packaging: tools/build-dist.sh writes hashes only ---------------------

def _dist_hash_block() -> str:
    src = (TENDER / "tools" / "build-dist.sh").read_text(encoding="utf-8")
    start = src.index('python -B - "$STAGE/$NAME" "$STAGE/$NAME/cynovela.yaml"')
    end = src.index("unset ADMIN_PW VIEWER_PW", start)
    return src[start:end]


def test_build_dist_writes_hashes_and_no_plaintext(tmp_path):
    stage = tmp_path / "stage" / "tender"
    stage.mkdir(parents=True)
    (stage / "db.py").write_text((TENDER / "db.py").read_text(encoding="utf-8"), encoding="utf-8")
    (stage / "cynovela.yaml").write_text((TENDER / "cynovela.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    a, v = _pw(), _pw()
    script = (
        "set -e\n"
        f'STAGE="{tmp_path / "stage"}"\nNAME=tender\n'
        'ADMIN_PW="$1"\nVIEWER_PW="$2"\n'
        + _dist_hash_block()
    )
    env = {k: val for k, val in os.environ.items() if not k.startswith("CYNOVELA_")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    # the packaging script calls `python`; use the interpreter running the tests
    import sys

    bindir = tmp_path / "bin"
    bindir.mkdir()
    (bindir / "python").symlink_to(sys.executable)
    env["PATH"] = str(bindir) + os.pathsep + env.get("PATH", "")
    proc = subprocess.run(["bash", "-c", script, "build", a, v], capture_output=True, text=True, env=env, timeout=120)
    assert proc.returncode == 0, re.sub(re.escape(a) + "|" + re.escape(v), "<redacted>", proc.stdout + proc.stderr)
    text = (stage / "cynovela.yaml").read_text(encoding="utf-8")
    assert a not in text and v not in text
    import yaml

    auth = yaml.safe_load(text)["auth"]
    assert auth["admin_initial_password"] == "" and auth["viewer_initial_password"] == ""
    import importlib.util

    spec = importlib.util.spec_from_file_location("db_for_hash_check", stage / "db.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.verify_password(a, auth["admin_initial_password_hash"])
    assert mod.verify_password(v, auth["viewer_initial_password_hash"])
    assert not (stage / "__pycache__").exists()


def test_repository_yaml_holds_no_initial_password():
    import yaml

    auth = yaml.safe_load((TENDER / "cynovela.yaml").read_text(encoding="utf-8"))["auth"]
    assert auth.get("admin_initial_password") == ""
    assert auth.get("viewer_initial_password") == ""
    assert "admin_initial_password_hash" in auth and "viewer_initial_password_hash" in auth


# --- launch screen: points to README, never prints a value -----------------

def _first_login_func() -> str:
    src = (TENDER / "tools" / "launch-body.sh").read_text(encoding="utf-8")
    start = src.index("print_first_login() {")
    end = src.index("\n}\n", start) + 3
    return src[start:end]


@pytest.mark.parametrize("key", ["admin_initial_password_hash", "admin_initial_password"])
def test_first_login_frame_shows_no_value(tmp_path, key):
    value = _hash("x") if key.endswith("_hash") else _pw()
    yaml_text = (TENDER / "cynovela.yaml").read_text(encoding="utf-8")
    yaml_text = re.sub(r"(?m)^(  " + key + r":).*$", r"\1 '" + value + "'", yaml_text)
    (tmp_path / "cynovela.yaml").write_text(yaml_text, encoding="utf-8")
    script = (
        f'. "{TENDER / "tools" / "conf.sh"}"\n'
        f'CONF_FILE="{tmp_path / "cynovela.yaml"}"\n'
        f'DATA_DIR="{tmp_path / "store"}"\nPORT=8765\nAPP_ARGS=()\n'
        + _first_login_func()
        + "print_first_login\n"
    )
    proc = subprocess.run(["bash", "-c", script], capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout
    assert value not in out
    assert "README" in out
    sep = "─" * 48
    lines = out.splitlines()
    idx = [i for i, ln in enumerate(lines) if ln.strip() == sep]
    assert len(idx) == 2 and idx[1] - idx[0] == 8   # 7 lines inside (macos-app folds this frame)


def test_first_login_frame_silent_without_values(tmp_path):
    (tmp_path / "cynovela.yaml").write_text((TENDER / "cynovela.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    script = (
        f'. "{TENDER / "tools" / "conf.sh"}"\n'
        f'CONF_FILE="{tmp_path / "cynovela.yaml"}"\n'
        f'DATA_DIR="{tmp_path / "store"}"\nPORT=8765\nAPP_ARGS=()\n'
        + _first_login_func()
        + "print_first_login\n"
    )
    proc = subprocess.run(["bash", "-c", script], capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0 and proc.stdout.strip() == ""
