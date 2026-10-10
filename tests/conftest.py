"""테스트는 레포의 진짜 `.env` 를 읽지 않는다 — 기본 `.env` 경로를 존재하지 않는 곳으로 돌린다.

`.env` 에 실제 키가 있어도 테스트가 실제 비밀·외부 호출에 닿지 않게 한다. `.env` 를 직접 만들어 쓰는 테스트는
자기 경로를 인자로 넘긴다(기본 경로를 쓰는 테스트만 이 격리 아래에 있다).
"""

from __future__ import annotations

import pytest

from core.llm.envfile import DOTENV_PATH_ENV


@pytest.fixture(autouse=True)
def _isolate_dotenv(tmp_path_factory, monkeypatch):
    monkeypatch.delenv("DATA_GO_KR_SERVICE_KEY", raising=False)  # TourAPI 실호출 차단(T434) — 키를 셸 env 에서도 못 읽게
    monkeypatch.setenv(DOTENV_PATH_ENV, str(tmp_path_factory.getbasetemp() / "no-such-dir" / ".env"))
    # 자동 좌표 파일(var/places, D25)은 PC 마다 다르다 — 기본은 없는 경로, 필요한 테스트만 직접 지정한다
    monkeypatch.setenv("KC_AUTO_PLACES", str(tmp_path_factory.getbasetemp() / "no-such-dir" / "auto_places.json"))
