import json
import subprocess
import sys
from pathlib import Path

from domains.kcontext.catalog.__main__ import status as catalog_status
from domains.kcontext.catalog.envkeys import CATALOG_KEY_NAMES, key_origin, resolve_catalog_env
from domains.kcontext.catalog.sources import load_sources
from domains.kcontext.catalog.store import CatalogStore

REPO = Path(__file__).resolve().parents[4]
DOTENV = (
    "# 주석\n"
    "NVIDIA_API_KEY=nv-should-not-appear\n"
    "SECRET_UNRELATED=do-not-read\n"
    "export SEOUL_OPENAPI_KEY='seoul-from-file'\n"
    'TAVILY_SEARCH_KEY="tv-from-file"  \n'
    "DATA_GO_KR_SERVICE_KEY=\n"
)


def write(tmp_path):
    p = tmp_path / ".env"
    p.write_text(DOTENV, encoding="utf-8")
    return p


def test_only_the_catalog_names_are_taken_from_dotenv(tmp_path):
    env = resolve_catalog_env(dotenv_path=write(tmp_path), environ={})
    assert env == {"SEOUL_OPENAPI_KEY": "seoul-from-file", "TAVILY_SEARCH_KEY": "tv-from-file"}
    assert "NVIDIA_API_KEY" not in env and "SECRET_UNRELATED" not in env  # 허용 밖 이름은 읽지 않는다
    assert "DATA_GO_KR_SERVICE_KEY" not in env  # 값이 비어 있으면 없는 것


def test_shell_env_wins_and_only_requested_names_are_looked_up(tmp_path):
    env = resolve_catalog_env(dotenv_path=write(tmp_path), environ={"SEOUL_OPENAPI_KEY": "from-shell", "PATH": "/x"})
    assert env["SEOUL_OPENAPI_KEY"] == "from-shell" and "PATH" not in env
    only = resolve_catalog_env(("TAVILY_SEARCH_KEY",), dotenv_path=write(tmp_path), environ={})
    assert only == {"TAVILY_SEARCH_KEY": "tv-from-file"}


def test_missing_file_gives_nothing_and_never_raises(tmp_path):
    assert resolve_catalog_env(dotenv_path=tmp_path / "none", environ={}) == {}
    assert set(CATALOG_KEY_NAMES) == {"SEOUL_OPENAPI_KEY", "DATA_GO_KR_SERVICE_KEY", "TAVILY_SEARCH_KEY"}


def test_key_origin_reports_location_not_value(tmp_path):
    p = write(tmp_path)
    assert key_origin("SEOUL_OPENAPI_KEY", dotenv_path=p, environ={}) == "dotenv"
    assert key_origin("SEOUL_OPENAPI_KEY", dotenv_path=p, environ={"SEOUL_OPENAPI_KEY": "x"}) == "shell"
    assert key_origin("DATA_GO_KR_SERVICE_KEY", dotenv_path=p, environ={}) == "missing"
    assert key_origin("NVIDIA_API_KEY", dotenv_path=p, environ={}) == "missing"  # 이 로더는 그 이름을 찾지도 않는다


def test_status_lists_key_locations_but_no_values(tmp_path, monkeypatch):
    monkeypatch.setattr("domains.kcontext.catalog.envkeys.repo_root", lambda: tmp_path)
    write(tmp_path)
    monkeypatch.delenv("APP_DOTENV_PATH", raising=False)  # 이 테스트는 자기 tmp 의 .env 를 쓴다
    for n in CATALOG_KEY_NAMES:
        monkeypatch.delenv(n, raising=False)
    out = catalog_status(CatalogStore(tmp_path / "cat"), load_sources())
    by = {s["id"]: s for s in out["sources"]}
    assert by["seoul_openapi"]["keys"] == {"SEOUL_OPENAPI_KEY": "dotenv"}
    assert by["tourapi_kto"]["keys"] == {"DATA_GO_KR_SERVICE_KEY": "missing"}
    blob = json.dumps(out)
    assert "seoul-from-file" not in blob and "tv-from-file" not in blob


def test_cli_never_loads_unrelated_dotenv_names(tmp_path):
    """실제 CLI 프로세스에서 `.env` 의 무관한 이름이 환경에 올라오지 않는다."""
    code = (
        "import sys\n"
        "from pathlib import Path\n"
        "import domains.kcontext.catalog.envkeys as ek\n"
        "ek.repo_root = lambda: Path(sys.argv[1])\n"
        "from domains.kcontext.catalog.__main__ import _env\n"
        "e = _env()\n"
        "print(sorted(k for k in ('NVIDIA_API_KEY','SECRET_UNRELATED','SEOUL_OPENAPI_KEY') if k in e))\n"
    )
    write(tmp_path)
    p = subprocess.run([sys.executable, "-c", code, str(tmp_path)], cwd=REPO, capture_output=True, text=True,
                       check=False, env={"PYTHONPATH": str(REPO), "PATH": __import__("os").environ["PATH"]})
    assert p.stdout.strip() == "['SEOUL_OPENAPI_KEY']", p.stderr[-300:]


def test_names_outside_the_catalog_allow_list_are_never_looked_up(tmp_path):
    p = write(tmp_path)
    env = resolve_catalog_env(("NVIDIA_API_KEY", "SECRET_UNRELATED", "SEOUL_OPENAPI_KEY"), dotenv_path=p,
                              environ={"NVIDIA_API_KEY": "shell-nv"})
    assert env == {"SEOUL_OPENAPI_KEY": "seoul-from-file"}


def test_agent_role_never_reads_dotenv(tmp_path):
    env = tmp_path / ".env"
    env.write_text("SEOUL_OPENAPI_KEY=abc\n")
    assert resolve_catalog_env(dotenv_path=env, environ={"APP_PROCESS_ROLE": "agent"}) == {}
    assert key_origin("SEOUL_OPENAPI_KEY", dotenv_path=env, environ={"APP_PROCESS_ROLE": "agent"}) == "missing"
