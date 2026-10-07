"""행사 장소 주변의 검증된 이야기 연결. 구조: 공간의 이야기 → 해볼 만한 경험 → 남길 기록.

- 이야기는 ``data/stories/*.json`` 의 ``StoryRecord`` 만 쓴다. 근거(출처·인용)가 있는 주장만 나간다.
- **역사적 사실(fact)·전설·속설(lore)·서비스의 제안(suggestion)** 을 서로 다른 칸에 둔다. 속설은 전승 출처가 있을 때만
  "속설"로 소개하고, 체험의 효과처럼 쓰지 않는다. 출처 없는 이야기는 만들지 않는다.
- 합성 이야기(``synthetic``)는 데모 모드에서만 나간다. 특정 상업 매장은 연결하지 않는다.
- 경험·기록 문구는 이야기 내용과 무관한 중립 템플릿이다(길·성곽·광장·공원·문화공간 중심).
"""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from pathlib import Path

from domains.kcontext.contract.records import StoryRecord, story_from_dict
from domains.kcontext.contract.text import pick
from domains.kcontext.paths import data_dir

from .model import EventEntry

__all__ = ["link_stories", "load_stories"]

OFFICIAL_TIERS = ("S", "A", "B")
_EXPERIENCE = {
    "segment": ("이 구간을 천천히 걸으며 위 이야기가 나온 방향을 따라가 본다.",
                "Walk this stretch slowly and follow the direction mentioned above."),
    "area": ("이 일대를 한 바퀴 돌며 위 이야기가 가리키는 자리를 찾아본다.",
             "Take a loop around this area and look for the spot the story refers to."),
    "point": ("이 자리에 서서 위 이야기가 가리키는 방향을 바라본다.",
              "Stand at this spot and look in the direction the story refers to."),
    "approx": ("이 근처를 둘러보며 위 이야기의 흔적을 찾아본다 (위치는 대략적이다).",
               "Look around this area for traces of the story (the location is approximate)."),
}
_RECORD = ("사진 한 장이나 한 문장으로 남겨 보세요.", "Leave a photo or a single sentence.")


def load_stories(directory: Path | None = None) -> list[StoryRecord]:
    base = Path(directory) if directory is not None else data_dir() / "stories"
    return [story_from_dict(json.loads(p.read_text(encoding="utf-8"))) for p in sorted(base.glob("*.json"))]


def _haversine_m(a, b) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6_371_000 * math.asin(math.sqrt(h))


def _claim(c, lang: str) -> dict | None:
    ev = [e for e in c.evidence if e.stance == "support" and e.source.quote and e.source.locator]
    if not ev:
        return None  # 근거(인용·위치)가 없는 주장은 내지 않는다
    kinds = {e.claim_kind for e in ev}
    kind = "lore" if kinds == {"lore"} else ("inference" if "fact" not in kinds else "fact")
    return {"kind": kind, "text": pick(c.text, lang),
            "label": {"fact": "역사적 사실", "lore": "전설·속설", "inference": "추정"}[kind],
            "sources": [{"tier": e.source.tier, "name": e.source.name, "locator": e.source.locator,
                         "url": e.source.url, "quote": e.source.quote, "collected_at": e.source.collected_at}
                        for e in ev]}


def link_stories(
    entry: EventEntry, stories: Sequence[StoryRecord], *, radius_m: float = 400, lang: str = "ko",
    include_synthetic: bool = False,
) -> list[dict]:
    """행사장 좌표에서 ``radius_m`` 안의 검증된 이야기. 좌표가 없으면 연결하지 않는다."""
    if entry.venue.lat is None or entry.venue.lng is None:
        return []
    here = (entry.venue.lat, entry.venue.lng)
    out = []
    for s in stories:
        if s.synthetic and not include_synthetic:
            continue
        coords = s.geometry.get("coords") or []
        if not coords or min(_haversine_m(here, (c[0], c[1])) for c in coords) > radius_m:
            continue
        claims = [c for c in (_claim(c, lang) for c in s.claims) if c]
        if not claims or not any(src["tier"] in OFFICIAL_TIERS for c in claims for src in c["sources"]):
            continue  # 공식·학술 출처(S·A·B)가 하나도 없으면 이야기로 소개하지 않는다
        g = s.geometry.get("type", "approx")
        ko, en = _EXPERIENCE.get(g, _EXPERIENCE["approx"])
        out.append({
            "id": s.id, "title": pick(s.title, lang), "era": s.era, "alignment": s.alignment,
            "synthetic": s.synthetic, "location_basis": s.geometry.get("basis", ""),
            "facts": [c for c in claims if c["kind"] == "fact"],
            "lore": [c for c in claims if c["kind"] == "lore"],
            "inference": [c for c in claims if c["kind"] == "inference"],
            "experience": {"kind": "service_suggestion", "text": en if lang == "en" else ko},
            "record_prompt": {"kind": "service_suggestion", "text": _RECORD[1] if lang == "en" else _RECORD[0]},
        })
    return out
