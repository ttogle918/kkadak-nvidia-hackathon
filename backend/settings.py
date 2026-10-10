"""backend 설정. env 에서만 읽는다. `domains`·`mcp_server` 를 import 하지 않는다 (D3·D10)."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _is_agent(rid: str) -> bool:
    return rid.strip().casefold().startswith("agent:")


def _int(e: Mapping[str, str], name: str, default: int | None) -> int | None:
    raw = (e.get(name) or "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        raise ValueError(f"{name} 는 정수여야 한다") from None


def _float(e: Mapping[str, str], name: str, default: float) -> float:
    raw = (e.get(name) or "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        raise ValueError(f"{name} 는 숫자여야 한다") from None


def _public(e: Mapping[str, str]) -> bool:
    raw = (e.get("KC_PUBLIC_MODE") or "").strip()
    if raw not in ("", "0", "1"):  # 오타("true")가 조용히 로컬 모드가 되지 않게 시작 실패
        raise ValueError("KC_PUBLIC_MODE 는 1 또는 0 이어야 한다")
    return raw == "1"


@dataclass(frozen=True)
class Settings:
    hitl_db: Path
    audit_dir: Path
    output_dir: Path  # T218 이 쓴다
    reviewer_id: str
    reviewer_auth_source: str = "backend-local-demo"
    cors_origins: tuple[str, ...] = ("http://localhost:8766", "http://127.0.0.1:8766")
    catalog_dir: Path | None = None  # 행사 카탈로그(수집 프로세스가 쓰고 이 프로세스는 별도 프로세스로 읽는다)
    admin_token: str = ""  # 관리자 화면·API 용. 비어 있으면 관리자 API 는 닫혀 있다
    screen_fixture_dir: Path = REPO_ROOT / "backend" / "fixtures" / "screen"  # 화면용 카드·출처·근거 JSON(D10)
    index_db: Path = REPO_ROOT / "var" / "index" / "kcontext.db"  # 실록 색인(읽기 전용, 파이프라인 프로세스가 연다)
    # ---- 공개 모드(D24) ----
    public_mode: bool = False  # KC_PUBLIC_MODE=1 일 때만
    trusted_proxy_hops: int | None = None  # 기본 없음 — 없으면 IP 제한을 끈다(D24 ④). 1~3
    llm_daily_units: int = 300
    story_concurrency: int = 2  # 1~8
    catalog_concurrency: int = 2  # 1~8 (D24 ②)
    session_ttl_s: int = 7200
    session_max: int = 1000
    # ---- TourAPI 실시간(D29 ⑤) ----
    tourapi_daily_calls: int = 300  # 전역 일일 소프트 상한
    tourapi_timeout_s: float = 5.0

    def __post_init__(self) -> None:
        rid = self.reviewer_id.strip() if isinstance(self.reviewer_id, str) else ""
        if not rid or _is_agent(rid):
            raise ValueError("reviewer_id 는 비어 있지 않아야 하고 'agent:' 로 시작할 수 없다 (D2)")
        if not isinstance(self.reviewer_auth_source, str) or not self.reviewer_auth_source.strip():
            raise ValueError("reviewer_auth_source 가 비어 있다")
        if self.admin_token and len(self.admin_token) < 16:
            raise ValueError("KC_ADMIN_TOKEN 은 16자 이상이어야 한다(관리자 API 는 이 토큰 하나로 열린다)")
        hops = self.trusted_proxy_hops
        if hops is not None and not 1 <= hops <= 3:
            raise ValueError("KC_TRUSTED_PROXY_HOPS 는 1~3 이어야 한다(없으면 IP 제한을 끈다)")
        if self.llm_daily_units < 0:
            raise ValueError("KC_LLM_DAILY_UNITS 는 0 이상이어야 한다")
        if not 1 <= self.story_concurrency <= 8:
            raise ValueError("KC_STORY_CONCURRENCY 는 1~8 이어야 한다")
        if not 1 <= self.catalog_concurrency <= 8:
            raise ValueError("KC_CATALOG_CONCURRENCY 는 1~8 이어야 한다")
        if self.session_ttl_s < 1 or self.session_max < 1:
            raise ValueError("KC_SESSION_TTL_S·KC_SESSION_MAX 는 1 이상이어야 한다")
        if self.tourapi_daily_calls < 0:
            raise ValueError("KC_TOURAPI_DAILY_CALLS 는 0 이상이어야 한다")
        if not 0 < self.tourapi_timeout_s <= 30:
            raise ValueError("KC_TOURAPI_TIMEOUT_S 는 0 초과 30 이하여야 한다")
        object.__setattr__(self, "reviewer_id", rid)

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        e = os.environ if env is None else env
        var = REPO_ROOT / "var"
        origins = tuple(
            o.strip() for o in e.get("KC_CORS_ORIGINS", "").split(",") if o.strip()
        ) or ("http://localhost:8766", "http://127.0.0.1:8766")
        return cls(
            hitl_db=Path(e.get("KC_HITL_DB") or var / "hitl.db"),
            audit_dir=Path(e.get("KC_AUDIT_DIR") or var / "audit"),
            output_dir=Path(e.get("KC_OUTPUT_DIR") or var / "output"),
            reviewer_id=e.get("KC_REVIEWER_ID") or "human:demo",
            reviewer_auth_source="backend-local-demo",
            cors_origins=origins,
            catalog_dir=Path(e["KC_CATALOG_DIR"]) if e.get("KC_CATALOG_DIR") else var / "catalog",
            admin_token=e.get("KC_ADMIN_TOKEN", ""),
            screen_fixture_dir=Path(e.get("KC_SCREEN_FIXTURE_DIR") or REPO_ROOT / "backend" / "fixtures" / "screen"),
            index_db=Path(e.get("KC_INDEX_DB") or var / "index" / "kcontext.db"),
            public_mode=_public(e),
            trusted_proxy_hops=_int(e, "KC_TRUSTED_PROXY_HOPS", None),
            llm_daily_units=_int(e, "KC_LLM_DAILY_UNITS", 300),
            story_concurrency=_int(e, "KC_STORY_CONCURRENCY", 2),
            catalog_concurrency=_int(e, "KC_CATALOG_CONCURRENCY", 2),
            session_ttl_s=_int(e, "KC_SESSION_TTL_S", 7200),
            session_max=_int(e, "KC_SESSION_MAX", 1000),
            tourapi_daily_calls=_int(e, "KC_TOURAPI_DAILY_CALLS", 300),
            tourapi_timeout_s=_float(e, "KC_TOURAPI_TIMEOUT_S", 5.0),
        )
