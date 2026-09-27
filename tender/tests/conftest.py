"""Shared helpers for the tests under tender/tests.

Tests that import server.py run it in a child process. The child gets its own
data directory (CYNOVELA_DATA_ROOT, the same variable the macOS app launcher
uses) and its own HOME under pytest's tmp_path, so the database, keys, indexes
and logs never land in the source tree, and the rate-limit counters start at 0.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

TENDER_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture
def run_server_snippet(tmp_path):
    """Run a Python snippet in a child process that can `import server`.

    The snippet must print one JSON line prefixed with "RESULT " as its last
    result line. Returns the decoded object.
    """

    def _run(code: str, timeout: int = 300):
        home = tmp_path / "home"
        data = tmp_path / "data"
        home.mkdir(exist_ok=True)
        data.mkdir(exist_ok=True)
        env = {
            k: v
            for k, v in os.environ.items()
            if not k.startswith("CYNOVELA_") and k != "_CYNOVELA_PATHS_PID"
        }
        env.update(
            {
                "HOME": str(home),
                "CYNOVELA_DATA_ROOT": str(data),
                # Modules imported without server.py (db, config) and the logging set-up
                # that runs before server.py reads CYNOVELA_DATA_ROOT use these names.
                # server.py itself sets the same values from CYNOVELA_DATA_ROOT.
                "CYNOVELA_DATA_DIR": str(data),
                "CYNOVELA_DB": str(data / "db" / "cynovela.db"),
                "CYNOVELA_CHROMA": str(data / "vector" / "default" / "chroma"),
                "CYNOVELA_BACKUP_DIR": str(data / "backups"),
                "CYNOVELA_LOG_DIR": str(data / "logs"),
                "PYTHONDONTWRITEBYTECODE": "1",
                "HF_HUB_OFFLINE": "1",
                "TRANSFORMERS_OFFLINE": "1",
                "PYTHONPATH": str(TENDER_DIR),
            }
        )
        script = tmp_path / "snippet.py"
        script.write_text(code, encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(tmp_path),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        lines = [ln for ln in proc.stdout.splitlines() if ln.startswith("RESULT ")]
        if proc.returncode != 0 or not lines:
            # The child prints generated initial passwords on first start; keep them out of reports.
            out = re.sub(r"(?i)(password\S*[=:]\s*)\S+", r"\1<redacted>", proc.stdout[-3000:])
            err = re.sub(r"(?i)(password\S*[=:]\s*)\S+", r"\1<redacted>", proc.stderr[-3000:])
            pytest.fail(f"child failed rc={proc.returncode}\nSTDOUT tail:\n{out}\nSTDERR tail:\n{err}")
        return json.loads(lines[-1][len("RESULT "):])

    return _run
