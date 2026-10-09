"""pipeline CLI 의 T_llm 읽기 — 키 없이 설정 값을 읽고, 실패하면 기본 45초(fail-closed)."""

from domains.kcontext.pipeline import __main__ as cli


def test_attempt_timeout_read_from_config_without_keys(monkeypatch):
    for k in ("NVIDIA_API_KEY",):
        monkeypatch.delenv(k, raising=False)
    assert cli._attempt_timeout_s() == 40.0


def test_attempt_timeout_defaults_to_45_when_unreadable(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "repo_root", lambda: tmp_path)  # deploy/llm.chat.yaml 없음
    assert cli._attempt_timeout_s() == 45.0 == cli.DEFAULT_ATTEMPT_TIMEOUT_S
