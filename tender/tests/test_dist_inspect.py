"""The pre-packaging inspection of tools/build-dist.sh (`build-dist.sh inspect`).

The packaging step writes auth.*_initial_password_hash ("32 hex : 64 hex") into
the package's cynovela.yaml. Check (c-2) looks for 32-hex identifiers of
internal documents, so it must accept exactly those two lines and nothing else.
The passwords used here are generated in the test and never printed.
"""
import hashlib
import importlib.util
import os
import secrets
import subprocess
from pathlib import Path

import pytest

TENDER = Path(__file__).resolve().parents[1]
SCRIPT = TENDER / "tools" / "build-dist.sh"


def _hash_password():
    spec = importlib.util.spec_from_file_location("db_for_inspect_test", TENDER / "db.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.hash_password


def _make_stage(tmp_path):
    hp = _hash_password()
    stage = tmp_path / "stage"
    (stage / "docs").mkdir(parents=True)
    ah, vh = hp(secrets.token_urlsafe(9)), hp(secrets.token_urlsafe(9))
    yaml_text = (
        "auth:\n"
        "  admin_initial_password: ''\n"
        "  viewer_initial_password: ''\n"
        f"  admin_initial_password_hash: '{ah}'\n"
        f"  viewer_initial_password_hash: '{vh}'\n"
    )
    (stage / "cynovela.yaml").write_text(yaml_text, encoding="utf-8")
    (stage / "docs" / "a.md").write_text("# plain document\n", encoding="utf-8")
    values = tmp_path / "values.local"
    tok = secrets.token_urlsafe(12)
    values.write_text(f"T9\t{len(tok)}\t{hashlib.sha256(tok.encode()).hexdigest()}\n", encoding="utf-8")
    return stage, values, ah


def _inspect(stage, values):
    env = {k: v for k, v in os.environ.items() if not k.startswith("CYNOVELA_")}
    return subprocess.run(
        ["bash", str(SCRIPT), "inspect", str(stage), str(values)],
        capture_output=True, text=True, env=env, timeout=120,
    )


def test_hash_lines_in_yaml_are_accepted(tmp_path):
    stage, values, _ = _make_stage(tmp_path)
    p = _inspect(stage, values)
    assert p.returncode == 0, p.stdout + p.stderr
    assert "(c-2) 中身に残った内部の文書への参照: 0件" in p.stdout
    assert "auth.*_initial_password_hash の行 2 行" in p.stdout


@pytest.mark.parametrize("where", ["other_line_in_yaml", "other_key_in_yaml", "other_file"])
def test_other_32_hex_values_still_stop(tmp_path, where):
    stage, values, ah = _make_stage(tmp_path)
    y = stage / "cynovela.yaml"
    if where == "other_line_in_yaml":
        y.write_text(y.read_text(encoding="utf-8") + f"note: {secrets.token_hex(16)}\n", encoding="utf-8")
    elif where == "other_key_in_yaml":
        y.write_text(y.read_text(encoding="utf-8") + f"  other_hash: '{ah}'\n", encoding="utf-8")
    else:
        (stage / "docs" / "a.md").write_text(f"page {secrets.token_hex(16)}\n", encoding="utf-8")
    p = _inspect(stage, values)
    assert p.returncode != 0
    assert "(c-2) 中身に残った内部の文書への参照を検出" in p.stderr
