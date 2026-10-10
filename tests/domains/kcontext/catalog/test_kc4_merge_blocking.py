"""T416 — 월 버킷 + 외부 id 블로킹 _group 이 이전(모든 그룹과 비교) 구현과 같은 그룹을 만든다.

근거: same_event 가 참이면 (a) 외부 id 공유 또는 (b) 날짜 교집합 -> 같은 달 키 공유. 그룹 진입은 모든 구성원과 참이어야
하므로 첫 구성원과 키를 공유한다 -> 대상 그룹은 후보 안에 있고, 후보를 그룹 생성 순으로 돌면 "첫 그룹" 도 같다.
계측(dev): 이전 구현 2,000건 4.9초 -> 서울 총 19,586행(T408) 수 분, 3만 건 약 18분.
"""

import random
from collections.abc import Sequence
from datetime import date, timedelta

from kc_catalog_helpers import obs, session

from domains.kcontext.catalog.merge import _group, same_event


def _old_group(items: Sequence) -> list[list]:
    groups: list[list] = []
    for o in sorted(items, key=lambda x: x.obs_id):
        for g in groups:
            if all(same_event(o, x) for x in g):
                g.append(o)
                break
        else:
            groups.append([o])
    return groups


def _ids(groups):
    return [[o.obs_id for o in g] for g in groups]


def _iso(d):
    return d.isoformat()


def _make(seed=416, n=300):
    rnd = random.Random(seed)
    out = []
    base = date(2026, 1, 1)
    venues = ["○○ 홀", "△△ 극장", "□□ 박물관"]
    titles = ["○○ 가을 음악회", "○○ 가을 음악회 2부", "△△ 전시", "□□ 축제"]
    i = 0

    def add(**kw):
        nonlocal i
        i += 1
        kw.setdefault("venue_name", rnd.choice(venues))
        kw.setdefault("title", rnd.choice(titles))
        out.append(obs(obs_id=f"s:{i:04d}", **kw))

    # 긴 기간(2년) 두 개 + 그 사이 임의 날짜의 하루짜리들
    add(start="2026-01-01", end="2027-12-31", venue_name="○○ 홀", title="○○ 가을 음악회")
    add(start="2026-03-01", end="2028-02-28", venue_name="○○ 홀", title="○○ 가을 음악회")
    for _ in range(60):
        d = base + timedelta(days=rnd.randrange(0, 700))
        add(start=_iso(d), end=_iso(d), venue_name="○○ 홀", title="○○ 가을 음악회")
    # 긴 기간 x 기간 밖(2029 이후, 2025)
    for _ in range(20):
        d = date(2029, 1, 1) + timedelta(days=rnd.randrange(0, 300))
        add(start=_iso(d), end=_iso(d), venue_name="○○ 홀", title="○○ 가을 음악회")
        d = date(2025, 1, 1) + timedelta(days=rnd.randrange(0, 300))
        add(start=_iso(d), end=_iso(d), venue_name="○○ 홀", title="○○ 가을 음악회")
    # 날짜 없음 + 외부 id 공유 / 공유 없음
    for k in range(15):
        add(start=None, end=None, external_ids=(f"x:{k}",), title="○○ 가을 음악회")
        add(start=_iso(base + timedelta(days=k * 9)), end=None, external_ids=(f"x:{k}",))
    for _ in range(15):
        add(start=None, end=None, title="○○ 가을 음악회", venue_name="○○ 홀")
    # 같은 체계 다른 id + 같은 장소·날짜
    for k in range(20):
        d = _iso(base + timedelta(days=k))
        add(start=d, end=d, venue_name="○○ 홀", title="○○ 가을 음악회", external_ids=("seoul_cult:A",))
        add(start=d, end=d, venue_name="○○ 홀", title="○○ 가을 음악회", external_ids=("seoul_cult:B",))
    # 달 경계, 해 경계
    for a, b in [("2026-01-31", "2026-01-31"), ("2026-02-01", "2026-02-01"), ("2026-02-28", "2026-03-01"),
                 ("2026-12-31", "2026-12-31"), ("2027-01-01", "2027-01-01"), ("2026-01-31", "2026-02-01")]:
        for t in ("□□ 축제", "□□ 축제"):
            add(start=a, end=b, venue_name="□□ 박물관", title=t)
    # 끝이 시작보다 앞섬(날짜 없음 취급), 시작만/끝만
    add(start="2026-05-10", end="2026-05-01", venue_name="△△ 극장", title="△△ 전시")
    add(start="2026-05-10", end=None, venue_name="△△ 극장", title="△△ 전시")
    add(start=None, end="2026-05-10", venue_name="△△ 극장", title="△△ 전시")
    # 세션 날짜만
    for k in range(25):
        d = _iso(base + timedelta(days=rnd.randrange(0, 700)))
        add(start=None, end=None, sessions=(session(date=d), session(date="2026-06-15")),
            venue_name="△△ 극장", title="△△ 전시")
    # demo 섞임(같은 장소·제목·날짜)
    for k in range(20):
        d = _iso(base + timedelta(days=k * 3))
        add(start=d, end=d, venue_name="○○ 홀", title="○○ 가을 음악회", demo=bool(k % 2))
    # 무작위 채우기
    while len(out) < n:
        a = base + timedelta(days=rnd.randrange(0, 700))
        b = a + timedelta(days=rnd.choice([0, 0, 1, 5, 40, 200]))
        ext = rnd.choice([(), (), (f"seoul_cult:{rnd.randrange(8)}",), (f"k:{rnd.randrange(5)}",)])
        add(start=_iso(a), end=_iso(b), external_ids=ext, demo=rnd.random() < 0.05)
    return out


def test_blocking_group_equals_old_group_on_300_observations():
    items = _make()
    assert len(items) == 300
    new, old = _group(items), _old_group(items)
    assert _ids(new) == _ids(old)  # 그룹 구성뿐 아니라 그룹 순서·구성원 순서까지
    assert len(new) < len(items) and any(len(g) > 1 for g in new)  # 합쳐진 것이 실제로 있다


def test_equivalence_across_seeds():
    for seed in range(5):
        items = _make(seed=seed, n=120)
        assert _ids(_group(items)) == _ids(_old_group(items))


def test_long_range_joins_short_event_inside_but_not_outside():
    a = obs("s:1", start="2026-01-01", end="2027-12-31", venue_name="○○ 홀")
    inside = obs("s:2", start="2027-06-10", end="2027-06-10", venue_name="○○ 홀")
    outside = obs("s:3", start="2029-06-10", end="2029-06-10", venue_name="○○ 홀")
    assert _ids(_group([a, inside, outside])) == [["s:1", "s:2"], ["s:3"]]


def test_month_boundary_and_no_date_cases():
    a = obs("s:1", start="2026-01-31", end="2026-02-01")
    b = obs("s:2", start="2026-02-01", end="2026-02-01")
    c = obs("s:3", start="2026-01-31", end="2026-01-31")
    assert _ids(_group([a, b, c])) == _ids(_old_group([a, b, c]))
    n1 = obs("s:4", start=None, end=None, external_ids=("x:1",))
    n2 = obs("s:5", start=None, end=None, external_ids=("x:1",))
    n3 = obs("s:6", start=None, end=None)
    assert _ids(_group([n1, n2, n3])) == [["s:4", "s:5"], ["s:6"]] == _ids(_old_group([n1, n2, n3]))


def test_demo_never_merges_with_real():
    r = obs("s:1", start="2026-10-16", end="2026-10-16")
    d = obs("s:2", start="2026-10-16", end="2026-10-16", demo=True)
    assert _ids(_group([r, d])) == [["s:1"], ["s:2"]]
