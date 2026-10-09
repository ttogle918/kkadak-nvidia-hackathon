"""카탈로그 대상 지역 해석. 지역이 하나든 여럿이든 Region 하나로 돌려준다.

``"+"`` 로 합치고 쪼개는 규칙은 이 파일에만 둔다. 합친 Region 은 메모리에서만 만들고
``load_regions()`` 결과에는 넣지 않는다. 지역 이름·구·키워드는 data/regions/*.json 에서만 읽는다.
"""

from __future__ import annotations

import os
from collections.abc import Mapping

from domains.kcontext.regions import Region, load_regions

__all__ = ["DEFAULT_ID", "ENV", "region_ids", "target_region"]

ENV = "KC_TARGET_REGION"  # 쉼표 목록. 없으면 DEFAULT_ID
DEFAULT_ID = "jung"
_JOIN = "+"


def _union(seqs: list[tuple[str, ...]]) -> tuple[str, ...]:
    out: list[str] = []
    for seq in seqs:
        for x in seq:
            if x not in out:
                out.append(x)
    return tuple(out)


def target_region(spec: str | None = None, regions: Mapping[str, Region] | None = None) -> Region:
    """spec(쉼표 목록, None 이면 env KC_TARGET_REGION, 그것도 없으면 기본 지역)을 Region 으로.

    하나면 그 Region 그대로, 여럿이면 합친 Region(id 는 정렬한 id 를 "+" 로 이음, bbox·center 는 None).
    모르는 id·빈 문자열은 ValueError.
    """
    raw = spec if spec is not None else os.environ.get(ENV, DEFAULT_ID)
    ids = [p.strip() for p in raw.split(",")]
    if not raw.strip() or any(not p for p in ids):
        raise ValueError("대상 지역이 비었다")
    known = regions if regions is not None else load_regions()
    unknown = sorted({p for p in ids if p not in known})
    if unknown:
        raise ValueError(f"지역 {unknown} 이 data/regions/ 에 없다")
    uniq = sorted(set(ids))
    if len(uniq) == 1:
        return known[uniq[0]]
    picked = [known[i] for i in uniq]
    return Region(
        id=_JOIN.join(uniq),
        name={k: "·".join(r.name[k] for r in picked) for k in ("ko", "en")},
        gu=_union([r.gu for r in picked]),
        bbox=None,
        center=None,
        keywords=_union([r.keywords for r in picked]),
        sillok_keywords=(),
    )


def region_ids(region: Region) -> tuple[str, ...]:
    """Region 이 덮는 원래 지역 id 들(하나짜리는 자기 id 하나)."""
    return tuple(region.id.split(_JOIN))
