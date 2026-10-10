"""서울 API 행사 장소 좌표 → 자동 장소 사전(D25). 로컬 파일만 읽고 네트워크를 쓰지 않는다.

관찰값(observations.json)에서 ``seoul_openapi`` 유래의 장소명·위경도·자치구(source_gu)만 쓴다.
이상치는 데이터로 거른다(사람이 정한 범위 값 없음): 구 중앙값에서 ``max_gu_dist_km`` 초과 → 버림,
같은 이름의 좌표가 중앙값에서 ``max_spread_m`` 를 넘게 흩어지면 모호로 버림.
출력은 ``var/places/auto_places.json`` (커밋하지 않는다).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
import tempfile
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from domains.kcontext.places import MAX_STR, PlaceBook, norm

__all__ = ["build_from_observations", "load_rules", "main"]

SOURCE_ID = "seoul_openapi"
MIN_GU_SAMPLES = 3
SUMMARY_KEYS = ("names_seen", "accepted", "ambiguous", "far_from_gu", "no_gu", "shadowed_by_manual")


def load_rules(path: Path | str) -> dict[str, float]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    out = {}
    for k in ("max_spread_m", "max_gu_dist_km"):
        v = raw.get(k) if isinstance(raw, dict) else None
        if isinstance(v, bool) or not isinstance(v, (int, float)) or v <= 0:
            raise ValueError(f"auto_rules: {k} 는 양수여야 한다")
        out[k] = float(v)
    return out


def _dist_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    (la1, lo1), (la2, lo2) = a, b
    p1, p2 = math.radians(la1), math.radians(la2)
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lo2 - lo1) / 2) ** 2
    return 2 * 6371008.8 * math.asin(math.sqrt(h))


def _median(pts: list[tuple[float, float]]) -> tuple[float, float]:
    return statistics.median(p[0] for p in pts), statistics.median(p[1] for p in pts)


def _num(v: Any) -> float | None:
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        return None
    return float(v)


def _rows(entries: Iterable[Mapping]) -> list[tuple[str, tuple[float, float] | None, str]]:
    """(이름, 좌표 또는 None, 구) — seoul_openapi 유래이고 이름이 있는 것만."""
    out = []
    for e in entries:
        if not isinstance(e, Mapping) or e.get("source_id") != SOURCE_ID:
            continue
        o = e.get("observation")
        v = o.get("venue") if isinstance(o, Mapping) else None
        if not isinstance(v, Mapping):
            continue
        name = v.get("name")
        if not isinstance(name, str) or not name.strip() or len(name) > MAX_STR:
            continue
        lat, lng = _num(v.get("lat")), _num(v.get("lng"))
        ok = lat is not None and lng is not None and -90 <= lat <= 90 and -180 <= lng <= 180
        gu = v.get("district") if v.get("district_basis") == "source_gu" else ""
        out.append((name, (lat, lng) if ok else None, gu.strip() if isinstance(gu, str) else ""))  # type: ignore[arg-type]
    return out


def build_from_observations(
    observations: Iterable[Mapping],
    rules: Mapping[str, float],
    manual: PlaceBook | None,
    collected_at: str,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """관찰값 기록(``{source_id, observation}``) → (자동 항목 목록(이름순), 요약).

    요약 수치는 장소 이름(정규화) 단위: 좌표가 있던 이름이 구 없음·구 중앙값 이상치·모호·사람 사전과 겹침으로
    빠진 수. 구가 없는 좌표와 표본 3개 미만 구의 좌표는 쓰지 않는다(전자는 no_gu, 후자는 far_from_gu 로 센다).
    """
    max_gu_m = float(rules["max_gu_dist_km"]) * 1000
    max_spread = float(rules["max_spread_m"])
    rows = _rows(observations)
    summary = dict.fromkeys(SUMMARY_KEYS, 0)
    summary["names_seen"] = len({norm(n) for n, _, _ in rows})

    by_gu: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for _, ll, gu in rows:
        if ll is not None and gu:
            by_gu[gu].append(ll)
    center = {gu: _median(p) for gu, p in by_gu.items() if len(p) >= MIN_GU_SAMPLES}

    kept: dict[str, list[tuple[float, float]]] = defaultdict(list)
    spelling: dict[str, Counter[str]] = defaultdict(Counter)
    lost: dict[str, set[str]] = defaultdict(set)  # 이름 -> 좌표가 버려진 사유
    for name, ll, gu in rows:
        if ll is None:
            continue
        k = norm(name)
        if not gu:
            lost[k].add("no_gu")
        elif gu not in center or _dist_m(ll, center[gu]) > max_gu_m:
            lost[k].add("far_from_gu")
        else:
            kept[k].append(ll)
            spelling[k][name] += 1
    for k, why in lost.items():
        if k not in kept:  # 쓸 수 있는 좌표가 하나도 없는 이름만 센다
            summary["no_gu" if why == {"no_gu"} else "far_from_gu"] += 1

    items: list[dict[str, Any]] = []
    for k, pts in kept.items():
        med = _median(pts)
        if any(_dist_m(p, med) > max_spread for p in pts):
            summary["ambiguous"] += 1
            continue
        shown = min(spelling[k].items(), key=lambda kv: (-kv[1], kv[0]))[0]
        if manual is not None and manual.lookup(shown) is not None:
            summary["shadowed_by_manual"] += 1
            continue
        items.append({
            "name": shown, "aliases": [], "lat": round(med[0], 6), "lng": round(med[1], 6),
            "source": f"서울 열린데이터광장 문화행사 장소 좌표 (행 {len(pts)}건)",
            "verified_at": collected_at, "note": "자동 생성(D25)", "auto": True, "origin": [SOURCE_ID],
        })  # fmt: skip
    items.sort(key=lambda d: d["name"])
    summary["accepted"] = len(items)
    return items, summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m domains.kcontext.places_build", description=__doc__)
    ap.add_argument("--catalog", required=True, help="observations.json 이 든 카탈로그 폴더")
    ap.add_argument("--rules", default="domains/kcontext/data/places/auto_rules.json")
    ap.add_argument("--out", default="var/places/auto_places.json")
    ap.add_argument("--collected-at", required=True, help="YYYY-MM-DD")
    a = ap.parse_args(argv)
    from datetime import date

    date.fromisoformat(a.collected_at)
    from domains.kcontext.places import load_places

    obs = json.loads((Path(a.catalog) / "observations.json").read_text(encoding="utf-8"))
    entries = list(obs.values()) if isinstance(obs, dict) else list(obs)
    items, summary = build_from_observations(
        entries, load_rules(a.rules), load_places(auto=None), a.collected_at)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=out.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)
    os.replace(tmp, out)
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
