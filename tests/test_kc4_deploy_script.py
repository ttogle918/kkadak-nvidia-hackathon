"""T425 — scripts/deploy_cloudrun.sh 인자 검사·dry-run (gcloud·docker 를 부르지 않는다)."""

import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "deploy_cloudrun.sh"

BASE = [
    "--project", "kc-demo-1234",
    "--cors-origin", "https://kc.example.app",
    "--nvidia-secret-version", "3",
    "--tourapi-secret-version", "4",
]


def _run(args, env_extra=None):
    # PATH 를 비워 gcloud·docker 가 호출되면 실패하게 한다 (dry-run 은 부르지 않아야 함)
    env = {"PATH": "/usr/bin:/bin", "HOME": "/nonexistent"}
    env.update(env_extra or {})
    return subprocess.run(
        ["bash", str(SCRIPT), *args], capture_output=True, text=True, env=env, timeout=30, check=False
    )


def _without(flag):
    out = list(BASE)
    i = out.index(flag)
    del out[i : i + 2]
    return out


def _with(flag, value):
    out = list(BASE)
    out[out.index(flag) + 1] = value
    return out


def test_dry_run_exits_zero_with_expected_flags():
    r = _run([*BASE, "--dry-run"])
    assert r.returncode == 0, r.stderr
    o = r.stdout
    for frag in ("--region us-central1", "--memory 2Gi", "--cpu 1", "--timeout 120",
                 "--max-instances 1", "--min-instances 0", "--concurrency 20",
                 "KC_PUBLIC_MODE=1", "KC_TARGET_REGION=all", "KC_CATALOG_CONCURRENCY=2",
                 "KC_CORS_ORIGINS=https://kc.example.app", "KC_LLM_DAILY_UNITS=300",
                 "KC_TOURAPI_DAILY_CALLS=300", "linux/amd64",
                 "NVIDIA_API_KEY=kc-nvidia-api-key:3",
                 "DATA_GO_KR_SERVICE_KEY=kc-data-go-kr-service-key:4"):
        assert frag in o, frag
    assert "KC_TRUSTED_PROXY_HOPS" not in o


def test_dry_run_does_not_leak_secret_values():
    fake = "sk-FAKE-SECRET-VALUE-123"
    r = _run([*BASE, "--dry-run"], {"NVIDIA_API_KEY": fake, "DATA_GO_KR_SERVICE_KEY": fake})
    assert r.returncode == 0
    assert fake not in r.stdout + r.stderr


@pytest.mark.parametrize("bad", ["latest", "LATEST", "abc", "0", "01", "1.2", "-1", "1,2", ""])
@pytest.mark.parametrize("flag", ["--nvidia-secret-version", "--tourapi-secret-version"])
def test_non_numeric_or_latest_version_rejected(flag, bad):
    r = _run([*_with(flag, bad), "--dry-run"])
    assert r.returncode != 0
    assert "gcloud run deploy" not in r.stdout


@pytest.mark.parametrize(
    "flag",
    ["--project", "--cors-origin", "--nvidia-secret-version", "--tourapi-secret-version"],
)
def test_missing_required_arg_fails(flag):
    r = _run([*_without(flag), "--dry-run"])
    assert r.returncode != 0
    assert "gcloud run deploy" not in r.stdout


@pytest.mark.parametrize(
    "origin",
    ["http://kc.example.app", "https://a.app,https://b.app", "https://a.app/path", "*"],
)
def test_cors_origin_must_be_single_https_origin(origin):
    r = _run([*_with("--cors-origin", origin), "--dry-run"])
    assert r.returncode != 0


def test_unknown_arg_rejected():
    assert _run([*BASE, "--bogus", "--dry-run"]).returncode != 0


def test_region_overridable():
    r = _run([*BASE, "--region", "asia-northeast1", "--dry-run"])
    assert r.returncode == 0
    assert "--region asia-northeast1" in r.stdout


def test_trusted_proxy_hops_optional_and_validated():
    """재배포가 --set-env-vars 로 env 를 통째로 바꾸므로 hops 는 인자로 다시 넣는다(D24 ④)."""
    r = _run([*BASE, "--dry-run"])
    assert "KC_TRUSTED_PROXY_HOPS" not in r.stdout and "IP 제한 꺼짐" in r.stderr
    r = _run([*BASE, "--trusted-proxy-hops", "2", "--dry-run"])
    assert r.returncode == 0 and "KC_TRUSTED_PROXY_HOPS=2" in r.stdout
    for bad in ("0", "4", "x", "1,2"):
        assert _run([*BASE, "--trusted-proxy-hops", bad, "--dry-run"]).returncode != 0, bad
