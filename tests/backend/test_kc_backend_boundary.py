import ast
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def test_backend_imports_no_domains_or_mcp_server():
    bad = []
    for p in (REPO / "backend").rglob("*.py"):
        for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            names = []
            if isinstance(n, ast.Import):
                names = [a.name for a in n.names]
            elif isinstance(n, ast.ImportFrom):
                names = [n.module or ""]
            bad += [(str(p), x) for x in names if x.split(".")[0] in ("domains", "mcp_server")]
    assert bad == []


def _run(role: str | None):
    env = {k: v for k, v in os.environ.items() if k != "APP_PROCESS_ROLE"}
    if role:
        env["APP_PROCESS_ROLE"] = role
    return subprocess.run(
        [sys.executable, "-c", "import backend.app"],
        cwd=REPO, env=env, capture_output=True, text=True, timeout=60, check=False,
    )


def test_role_agent_refuses_to_start():
    r = _run("agent")
    assert r.returncode != 0
    assert "APP_PROCESS_ROLE" in r.stderr


def test_import_ok_without_role(tmp_path):
    env_db = tmp_path / "h.db"
    env = {**os.environ, "KC_HITL_DB": str(env_db), "KC_AUDIT_DIR": str(tmp_path / "a")}
    env.pop("APP_PROCESS_ROLE", None)
    r = subprocess.run(
        [sys.executable, "-c", "import backend.app"],
        cwd=REPO, env=env, capture_output=True, text=True, timeout=60, check=False,
    )
    assert r.returncode == 0, r.stderr[-300:]
