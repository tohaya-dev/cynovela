"""The pre-packaging inspection of tools/build-dist.sh (`build-dist.sh inspect`).

The packaging step writes the fixed first passwords in plaintext into the
package's cynovela.yaml (auth.admin_initial_password / viewer_initial_password).
Check (a) must accept them there (and report how many it accepted) and still
stop the build when they appear anywhere else in the package, including the
package's own README.md. The passwords used here are generated in the test and
never printed.
"""
import hashlib
import os
import secrets
import subprocess
from pathlib import Path

import pytest

TENDER = Path(__file__).resolve().parents[1]
SCRIPT = TENDER / "tools" / "build-dist.sh"


def _make_stage(tmp_path):
    stage = tmp_path / "stage"
    (stage / "docs").mkdir(parents=True)
    a, v = secrets.token_urlsafe(9), secrets.token_urlsafe(7)
    yaml_text = (
        "auth:\n"
        f"  admin_initial_password: '{a}'\n"
        f"  viewer_initial_password: '{v}'\n"
    )
    (stage / "cynovela.yaml").write_text(yaml_text, encoding="utf-8")
    (stage / "docs" / "a.md").write_text("# plain document\n", encoding="utf-8")
    values = tmp_path / "values.local"
    rows = [("T3", a), ("T4", v)]
    values.write_text("".join(f"{s}\t{len(x)}\t{hashlib.sha256(x.encode()).hexdigest()}\n" for s, x in rows),
                      encoding="utf-8")
    return stage, values, a, v


def _inspect(stage, values):
    env = {k: v for k, v in os.environ.items() if not k.startswith("CYNOVELA_")}
    return subprocess.run(
        ["bash", str(SCRIPT), "inspect", str(stage), str(values)],
        capture_output=True, text=True, env=env, timeout=120,
    )


def test_plaintext_first_passwords_accepted_in_packaged_yaml(tmp_path):
    stage, values, a, v = _make_stage(tmp_path)
    p = _inspect(stage, values)
    out = p.stdout + p.stderr
    assert a not in out and v not in out
    assert p.returncode == 0, "inspect failed"
    assert "許可: 記号 T3 1 箇所 cynovela.yaml" in p.stdout
    assert "許可: 記号 T4 1 箇所 cynovela.yaml" in p.stdout
    assert "(a) 既知の資格情報: 0件" in p.stdout


@pytest.mark.parametrize("where", ["docs/a.md", "README.md", "store/logs/x.log"])
@pytest.mark.parametrize("which", ["admin", "viewer"])
def test_plaintext_first_passwords_elsewhere_still_stop(tmp_path, where, which):
    stage, values, a, v = _make_stage(tmp_path)
    value = a if which == "admin" else v
    f = stage / where
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(f"password: {value}\n", encoding="utf-8")
    p = _inspect(stage, values)
    out = p.stdout + p.stderr
    assert value not in out
    assert p.returncode != 0
    sym = "T3" if which == "admin" else "T4"
    assert f"検出: 記号 {sym} 1 箇所 {where}" in out
