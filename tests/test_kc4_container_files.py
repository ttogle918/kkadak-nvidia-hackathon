"""T423 — 컨테이너 파일 점검: 비밀 없음 · 구조 · entrypoint 설정."""

import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCKERFILE = (ROOT / "Dockerfile").read_text(encoding="utf-8")
ENTRY = (ROOT / "deploy" / "cloudrun" / "entrypoint.sh").read_text(encoding="utf-8")
DOCKERIGNORE = (ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
GITIGNORE = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()


def test_dockerignore_excludes_secrets_and_big_dirs():
    # .dockerignore 는 루트 기준이라 하위 폴더까지 막으려면 **/ 가 필요하다(COPY backend/ 등 안의 .env·키 파일)
    for line in ("**/.env", "**/.env.*", "**/*.pem", "**/*.key", "**/*.db", ".git", "var/", "docs/", "frontend/",
                 "eval/", "tests/", "test_condition/", "domains/kcontext/data/raw/", "dist/", "!image-data/**"):
        assert line in DOCKERIGNORE, line
    assert DOCKERIGNORE[-1] == "!image-data/**"  # 예외는 맨 뒤에 와야 먹는다


def test_dockerfile_has_no_secrets():
    assert not re.search(r"(?im)^\s*(ENV|ARG)\b.*(KEY|TOKEN|SECRET|PASSWORD)", DOCKERFILE)
    assert "NVIDIA_API_KEY" not in DOCKERFILE and "DATA_GO_KR" not in DOCKERFILE
    assert not re.search(r"nvapi-|AIza", DOCKERFILE)


def test_dockerfile_shape():
    assert re.search(r"(?m)^FROM python:3\.12-slim-\S+", DOCKERFILE)  # 태그 고정
    assert "uv sync --frozen --no-dev" in DOCKERFILE
    assert re.search(r"(?m)^USER app", DOCKERFILE)
    assert re.search(r"(?m)^COPY .*image-data/ /app/var/", DOCKERFILE)
    assert "mcp_server" not in DOCKERFILE  # D3


def test_entrypoint_settings():
    assert "KC_PUBLIC_MODE:-1" in ENTRY and "KC_TARGET_REGION:-all" in ENTRY
    assert "--workers 1" in ENTRY and "exec uvicorn backend.app:app" in ENTRY
    assert '"${PORT:-8080}"' in ENTRY
    assert not re.search(r"(?m)^\s*(export\s+)?KC_TRUSTED_PROXY_HOPS=", ENTRY)  # 기본값 금지
    for name in ("KC_HITL_DB", "KC_AUDIT_DIR", "KC_VAR_DIR", "KC_OUTPUT_DIR", "KC_CATALOG_DIR"):
        assert re.search(rf"export {name}=\"\$W", ENTRY), name  # 쓰기는 /tmp/kc 아래
    assert "W=/tmp/kc" in ENTRY
    assert not re.search(r"API_KEY|SERVICE_KEY", ENTRY)


def test_entrypoint_syntax_and_executable():
    assert (ROOT / "deploy" / "cloudrun" / "entrypoint.sh").stat().st_mode & 0o111
    sh = shutil.which("sh")
    assert subprocess.run([sh, "-n", str(ROOT / "deploy" / "cloudrun" / "entrypoint.sh")], check=False).returncode == 0


def test_gitignore_has_deploy_outputs():
    assert "image-data/" in GITIGNORE and "dist/" in GITIGNORE


def test_pipeline_child_receives_auto_places_path():
    """entrypoint 가 정한 자동 좌표 경로(/app/var/places)가 파이프라인 자식에 넘어가야 채팅 앵커에 좌표가 붙는다(D25·D30)."""
    from backend import story_runner

    assert 'KC_AUTO_PLACES="${KC_AUTO_PLACES:-/app/var/places/auto_places.json}"' in ENTRY
    assert "KC_AUTO_PLACES" in story_runner._ENV_ALLOW
