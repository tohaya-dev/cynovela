"""cynovela-cli.py keeps the bearer token in ~/.cynovela_cli.env.
The file must have mode 600 from the moment it exists (no write-then-chmod)."""
import importlib.util
import os
import stat
import sys
from pathlib import Path

import pytest

CLI = Path(__file__).resolve().parent.parent / "cynovela-cli.py"

pytestmark = pytest.mark.skipif(sys.platform.startswith("win"), reason="POSIX file modes")


@pytest.fixture
def cli(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    (tmp_path / "home").mkdir()
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("cynovela_cli_under_test", CLI)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _mode(p: Path) -> int:
    return stat.S_IMODE(p.stat().st_mode)


def test_new_file_is_created_with_mode_600(cli, tmp_path, monkeypatch):
    target = tmp_path / "home" / ".cynovela_cli.env"
    seen = []
    real_open = os.open

    def spy_open(path, flags, mode=0o777, *a, **kw):
        fd = real_open(path, flags, mode, *a, **kw)
        if str(path) == str(target):
            # state of the file at the moment it first exists, before any byte is written
            seen.append((mode, _mode(target), target.stat().st_size))
        return fd

    monkeypatch.setattr(cli.os, "open", spy_open)
    old = os.umask(0o022)
    try:
        cli._save_env_file(target, {"CYNOVELA_URL": "http://127.0.0.1:1", "CYNOVELA_TOKEN": "test-token-value"})
    finally:
        os.umask(old)
    assert seen, "the file was not created through os.open"
    mode_arg, mode_at_create, size_at_create = seen[0]
    assert mode_arg == 0o600
    assert mode_at_create == 0o600
    assert size_at_create == 0
    assert _mode(target) == 0o600
    assert "CYNOVELA_TOKEN=test-token-value" in target.read_text(encoding="utf-8")


def test_existing_file_becomes_600_and_keeps_other_lines(cli, tmp_path):
    target = tmp_path / "home" / ".cynovela_cli.env"
    target.write_text("# comment\nOTHER=1\nCYNOVELA_TOKEN=old\n", encoding="utf-8")
    os.chmod(target, 0o644)
    cli._save_env_file(target, {"CYNOVELA_TOKEN": "new"})
    assert _mode(target) == 0o600
    text = target.read_text(encoding="utf-8")
    assert "# comment" in text and "OTHER=1" in text
    assert "CYNOVELA_TOKEN=new" in text and "CYNOVELA_TOKEN=old" not in text
    cli._save_env_file(target, {"CYNOVELA_TOKEN": None})
    assert "CYNOVELA_TOKEN" not in target.read_text(encoding="utf-8")
    assert _mode(target) == 0o600


def test_no_write_then_chmod_in_source():
    src = CLI.read_text(encoding="utf-8")
    body = src[src.index("def _save_env_file"):]
    body = body[: body.index("\ndef ", 10)]
    assert "write_text(" not in body
    assert "os.O_CREAT" in body and "0o600" in body
