"""First passwords of the two initial users (administrator cynovela, viewer demo).

Policy:
- The packaging script (tools/build-dist.sh) writes the fixed first passwords,
  read from tools/dist-initial-credentials.local, in plaintext into the
  package's cynovela.yaml (auth.admin_initial_password /
  auth.viewer_initial_password). The repository's cynovela.yaml keeps them empty.
  Without the .local file the build stops.
- On a fresh install the administrator is created with must_change_password = 1
  and the viewer with must_change_password = 0.
- The first start prints the administrator's value once on the terminal.
- An existing installation keeps the passwords it has (nothing is reset).

The test passwords are generated here and never printed.
"""
import json
import os
import re
import secrets
import subprocess
import sys
from pathlib import Path

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


def _run(run_server_snippet, tmp_path, cfg):
    (tmp_path / "cfg.json").write_text(json.dumps(cfg), encoding="utf-8")
    return run_server_snippet(SEED)


def test_fresh_install_admin_must_change_viewer_not(run_server_snippet, tmp_path):
    a, v = _pw(), _pw()
    cfg = {
        "auth": {"admin_initial_password": a, "viewer_initial_password": v},
        "probe": {"a": a, "v": v},
    }
    r = _run(run_server_snippet, tmp_path, cfg)
    assert r["user-admin"]["username"] == "cynovela"
    assert r["user-scientist"]["username"] == "demo"
    assert r["user-admin"]["checks"]["a"] is True
    assert r["user-scientist"]["checks"]["v"] is True
    assert r["user-admin"]["must_change"] == 1
    assert r["user-scientist"]["must_change"] == 0


def test_fresh_install_without_values_uses_random(run_server_snippet, tmp_path):
    cfg = {"auth": {}, "probe": {}}
    r = _run(run_server_snippet, tmp_path, cfg)
    assert r["user-admin"]["must_change"] == 1
    assert r["user-scientist"]["must_change"] == 0


def test_existing_installation_is_not_reset(run_server_snippet, tmp_path):
    a, v, a2, v2 = _pw(), _pw(), _pw(), _pw()
    cfg = {
        "auth": {"admin_initial_password": a, "viewer_initial_password": v},
        "pre_existing": {"admin": a2, "viewer": v2},   # passwords the users changed to
        "probe": {"a": a, "v": v, "a2": a2, "v2": v2},
    }
    r = _run(run_server_snippet, tmp_path, cfg)
    assert r["user-admin"]["checks"]["a2"] is True and r["user-admin"]["checks"]["a"] is False
    assert r["user-scientist"]["checks"]["v2"] is True and r["user-scientist"]["checks"]["v"] is False
    assert r["user-admin"]["must_change"] == 0
    assert r["user-scientist"]["must_change"] == 0


SIGN_IN_API = r'''
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
out = {}
for who, user, pw in (("viewer", "demo", cfg["probe"]["v"]), ("admin", "cynovela", cfg["probe"]["a"])):
    r = c.post("/api/auth/login", json={"username": user, "password": pw})
    body = r.json()
    out[who] = {"login": r.status_code, "must_change": body.get("must_change_password")}
print("RESULT " + json.dumps(out))
'''


def test_sign_in_viewer_not_asked_admin_asked(run_server_snippet, tmp_path):
    a, v = _pw(), _pw()
    cfg = {"auth": {"admin_initial_password": a, "viewer_initial_password": v}, "probe": {"a": a, "v": v}}
    (tmp_path / "cfg.json").write_text(json.dumps(cfg), encoding="utf-8")
    r = run_server_snippet(SIGN_IN_API)
    assert r["viewer"]["login"] == 200 and r["viewer"]["must_change"] is False
    assert r["admin"]["login"] == 200 and r["admin"]["must_change"] is True


# --- packaging: tools/build-dist.sh writes the plaintext values under auth: ---

def _cred_and_yaml_block() -> str:
    # from reading the .local up to the comment after the second yaml write
    src = (TENDER / "tools" / "build-dist.sh").read_text(encoding="utf-8")
    start = src.index('CRED_FILE=""')
    end = src.index("# パスワードは同梱の文書に書かない", start)
    return src[start:end]


def _bash_env(tmp_path):
    env = {k: val for k, val in os.environ.items() if not k.startswith("CYNOVELA_")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    if not (bindir / "python").exists():
        (bindir / "python").symlink_to(sys.executable)   # the script calls `python`
    env["PATH"] = str(bindir) + os.pathsep + env.get("PATH", "")
    return env


def _stage(tmp_path):
    stage = tmp_path / "stage" / "tender"
    stage.mkdir(parents=True)
    (stage / "cynovela.yaml").write_text((TENDER / "cynovela.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    root = tmp_path / "root"
    (root / "tools").mkdir(parents=True)
    repo = tmp_path / "repo"
    (repo / "tools").mkdir(parents=True)
    return stage, root, repo


def _script(tmp_path, root, repo):
    return (
        "set -e\n"
        f'STAGE="{tmp_path / "stage"}"\nNAME=tender\nROOT="{root}"\nREPO="{repo}"\n'
        + _cred_and_yaml_block()
    )


def test_build_dist_writes_plaintext_under_auth(tmp_path):
    stage, root, repo = _stage(tmp_path)
    a, v = _pw(), _pw()
    (root / "tools" / "dist-initial-credentials.local").write_text(f"admin\t{a}\nviewer\t{v}\n", encoding="utf-8")
    proc = subprocess.run(["bash", "-c", _script(tmp_path, root, repo)],
                          capture_output=True, text=True, env=_bash_env(tmp_path), timeout=120)
    out = proc.stdout + proc.stderr
    assert proc.returncode == 0, re.sub(re.escape(a) + "|" + re.escape(v), "<redacted>", out)
    assert a not in out and v not in out            # the build never prints the values
    import yaml

    auth = yaml.safe_load((stage / "cynovela.yaml").read_text(encoding="utf-8"))["auth"]
    assert auth["admin_initial_password"] == a
    assert auth["viewer_initial_password"] == v
    assert not any(k.endswith("_hash") for k in auth)


def test_build_dist_stops_without_local_file(tmp_path):
    stage, root, repo = _stage(tmp_path)
    before = (stage / "cynovela.yaml").read_text(encoding="utf-8")
    proc = subprocess.run(["bash", "-c", _script(tmp_path, root, repo)],
                          capture_output=True, text=True, env=_bash_env(tmp_path), timeout=120)
    assert proc.returncode != 0
    assert "フェイルクローズ" in proc.stderr
    assert (stage / "cynovela.yaml").read_text(encoding="utf-8") == before


def test_repository_yaml_holds_no_initial_password():
    import yaml

    auth = yaml.safe_load((TENDER / "cynovela.yaml").read_text(encoding="utf-8"))["auth"]
    assert auth.get("admin_initial_password") == ""
    assert auth.get("viewer_initial_password") == ""
    assert not any(k.endswith("_hash") for k in auth)


# --- launch screen: the first start prints the administrator's value once ---

def _first_login_func() -> str:
    src = (TENDER / "tools" / "launch-body.sh").read_text(encoding="utf-8")
    start = src.index("print_first_login() {")
    end = src.index("\n}\n", start) + 3
    return src[start:end]


def _run_first_login(tmp_path, admin_value, db_exists=False):
    yaml_text = (TENDER / "cynovela.yaml").read_text(encoding="utf-8")
    yaml_text = re.sub(r"(?m)^(  admin_initial_password:).*$", r"\1 '" + admin_value + "'", yaml_text)
    (tmp_path / "cynovela.yaml").write_text(yaml_text, encoding="utf-8")
    if db_exists:
        (tmp_path / "store" / "db").mkdir(parents=True)
        (tmp_path / "store" / "db" / "cynovela.db").write_bytes(b"")
    script = (
        f'. "{TENDER / "tools" / "conf.sh"}"\n'
        f'CONF_FILE="{tmp_path / "cynovela.yaml"}"\n'
        f'DATA_DIR="{tmp_path / "store"}"\nPORT=8765\nAPP_ARGS=()\n'
        + _first_login_func()
        + "print_first_login\n"
    )
    proc = subprocess.run(["bash", "-c", script], capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def test_first_start_prints_admin_value_once(tmp_path):
    value = _pw()
    out = _run_first_login(tmp_path, value)
    shown_once = out.count(value) == 1   # compared without printing the value
    assert shown_once
    assert "cynovela" in out and "http://localhost:8765" in out


def test_second_start_prints_nothing(tmp_path):
    out = _run_first_login(tmp_path, _pw(), db_exists=True)
    assert out.strip() == ""


def test_first_login_frame_silent_without_values(tmp_path):
    out = _run_first_login(tmp_path, "")
    assert out.strip() == ""
