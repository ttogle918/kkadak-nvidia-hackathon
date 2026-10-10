"""T416 — KC_TARGET_REGION=all 전체 별칭, 서울 API 쪽 상한."""

import httpx
import pytest

from domains.kcontext.catalog.seoul import SeoulApiError, fetch_rows
from domains.kcontext.catalog.target import ALL, ENV, region_ids, target_region
from domains.kcontext.regions import load_regions

KNOWN = load_regions()


def test_all_covers_every_region():
    r = target_region("all")
    assert ALL == "all"
    assert set(region_ids(r)) == set(KNOWN)
    assert r.bbox is None and r.center is None
    assert set(KNOWN["jung"].gu) <= set(r.gu)


def test_all_from_env_and_not_in_loaded_regions(monkeypatch):
    monkeypatch.setenv(ENV, " all ")
    assert set(region_ids(target_region())) == set(KNOWN)
    assert "all" not in load_regions()


@pytest.mark.parametrize("spec", ["all,jung", "jung,all", "all,all"])
def test_all_cannot_mix(spec):
    with pytest.raises(ValueError):
        target_region(spec)


def test_all_with_injected_regions():
    sub = {k: KNOWN[k] for k in ("jung", "mapo")}
    assert region_ids(target_region("all", sub)) == ("jung", "mapo")


def _client(total, key="SECRETKEY"):
    calls = []

    def handler(req):
        calls.append(str(req.url))
        return httpx.Response(200, json={"culturalEventInfo": {
            "list_total_count": total, "RESULT": {"CODE": "INFO-000", "MESSAGE": "ok"},
            "row": [{"TITLE": "○○"}]}})

    return httpx.Client(transport=httpx.MockTransport(handler)), calls


def test_over_page_cap_fails_instead_of_truncating():
    c, calls = _client(60_001)
    with pytest.raises(SeoulApiError) as e:
        fetch_rows("SECRETKEY", client=c)
    assert "total=60001" in str(e.value) and "max_pages=60" in str(e.value)
    assert "SECRETKEY" not in str(e.value) and len(calls) == 1


def test_at_cap_and_default_is_60_pages():
    c, _ = _client(60_000)
    rows, total = fetch_rows("k", client=c, max_pages=60)
    assert total == 60_000 and len(rows) == 60
    import inspect
    assert inspect.signature(fetch_rows).parameters["max_pages"].default == 60


def test_custom_cap_and_single_page_probe_exempt():
    c, _ = _client(5_000)
    with pytest.raises(SeoulApiError):
        fetch_rows("k", client=c, max_pages=4)
    c, _ = _client(19_586)
    rows, total = fetch_rows("k", client=c, page_size=5, max_pages=1)  # 표본·탐침은 일부만 받는 것이 목적
    assert total == 19_586 and len(rows) == 1
