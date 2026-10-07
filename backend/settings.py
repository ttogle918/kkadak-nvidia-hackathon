"""backend 설정. env 에서만 읽는다. `domains`·`mcp_server` 를 import 하지 않는다 (D3·D10)."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _is_agent(rid: str) -> bool:
    return rid.strip().casefold().startswith("agent:")


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

    def __post_init__(self) -> None:
        rid = self.reviewer_id.strip() if isinstance(self.reviewer_id, str) else ""
        if not rid or _is_agent(rid):
            raise ValueError("reviewer_id 는 비어 있지 않아야 하고 'agent:' 로 시작할 수 없다 (D2)")
        if not isinstance(self.reviewer_auth_source, str) or not self.reviewer_auth_source.strip():
            raise ValueError("reviewer_auth_source 가 비어 있다")
        if self.admin_token and len(self.admin_token) < 16:
            raise ValueError("KC_ADMIN_TOKEN 은 16자 이상이어야 한다(관리자 API 는 이 토큰 하나로 열린다)")
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
        )
