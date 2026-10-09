import pytest


@pytest.fixture(autouse=True)
def _isolated_var_dir(tmp_path, monkeypatch):
    """CLI 테스트가 레포의 var/cache 를 건드리지 않게 한다(일정 이해 캐시)."""
    monkeypatch.setenv("KC_VAR_DIR", str(tmp_path / "_var"))
