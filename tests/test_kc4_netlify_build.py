"""T424 — scripts/netlify_build.sh (직접 CORS). 출력은 tmp 에만 만든다."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "netlify_build.sh"
SRC = ROOT / "frontend" / "k-context"
KEY = "abcdef0123456789abcdef0123456789"
ORIGIN = "https://kc-api-xyz.a.run.app"


def _run(out: Path, key: str | None = KEY, origin: str | None = ORIGIN):
    env = {"PATH": os.environ["PATH"]}
    if key is not None:
        env["KC_KAKAO_JS_KEY"] = key
    if origin is not None:
        env["KC_BACKEND_ORIGIN"] = origin
    return subprocess.run(
        ["bash", str(SCRIPT), str(out)], env=env, capture_output=True, text=True, check=False
    )


def _snapshot() -> dict[str, bytes]:
    return {
        str(p.relative_to(SRC)): p.read_bytes() for p in sorted(SRC.rglob("*")) if p.is_file()
        and "node_modules" not in p.parts
    }


def test_dist_structure_and_config(tmp_path):
    out = tmp_path / "dist"
    r = _run(out)
    assert r.returncode == 0, r.stderr
    assert (out / "index.html").is_file() and (out / "events.html").is_file()
    assert (out / "src").is_dir()
    assert not (out / "admin.html").exists()
    assert not (out / "src" / "events" / "admin.js").exists()  # 관리자 화면 JS 도 공개 배포물에 없다
    assert not (out / "tests").exists()
    assert not (out / "README.md").exists()
    cfg = (out / "config.local.js").read_text()
    assert f"window.KC_KAKAO_JS_KEY = '{KEY}';" in cfg
    assert f"window.KC_API_BASE = '{ORIGIN}/api';" in cfg
    assert not (out / "_redirects").exists() and not (out / "_headers").exists()


def test_events_csp_has_origin_and_index_has_none(tmp_path):
    out = tmp_path / "dist"
    assert _run(out).returncode == 0
    ev = (out / "events.html").read_text()
    assert f"connect-src 'self' {ORIGIN};" in ev  # 운영 원점만 — 개발용 로컬 원점은 빠진다
    assert "localhost" not in ev and "127.0.0.1" not in ev
    assert "Content-Security-Policy" in ev
    assert "Content-Security-Policy" not in (out / "index.html").read_text()


def test_invalid_values_fail(tmp_path):
    bad_origins = [
        "http://a.example.com", "https://a.example.com/", "https://a.example.com/x",
        "https://a.example.com:8080", "https://a b.com", "", "ftp://x.com",
        "https://a.com; script-src *",
    ]
    for o in bad_origins:
        out = tmp_path / "d"
        r = _run(out, origin=o)
        assert r.returncode != 0, o
        assert not out.exists() or not (out / "config.local.js").exists()
    for k in ["", "a b", "a'b", "a<b", "a&b", "x" * 129]:
        assert _run(tmp_path / "k", key=k).returncode != 0, k
    assert _run(tmp_path / "n", key=None).returncode != 0
    assert _run(tmp_path / "m", origin=None).returncode != 0


def test_output_never_contains_values(tmp_path):
    r = _run(tmp_path / "dist")
    assert KEY not in r.stdout + r.stderr and ORIGIN not in r.stdout + r.stderr
    r = _run(tmp_path / "bad", key="a'b" + KEY, origin=ORIGIN)
    assert r.returncode != 0
    assert KEY not in r.stdout + r.stderr
    r = _run(tmp_path / "bad2", origin="http://secret-host.example.com")
    assert "secret-host" not in r.stdout + r.stderr


def test_source_unchanged(tmp_path):
    before = _snapshot()
    assert _run(tmp_path / "dist").returncode == 0
    assert _snapshot() == before
