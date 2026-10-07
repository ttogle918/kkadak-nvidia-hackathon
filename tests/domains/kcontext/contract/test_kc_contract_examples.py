"""공통 예제(examples/*.json, examples/bad/*.json)를 Python 검증기로 돌린다. JS 쪽은
frontend/k-context/tests/contract.examples.test.js 가 같은 파일을 읽는다."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from domains.kcontext.contract import (
    ensure_valid,
    validate_card,
    validate_route,
    validate_situation,
    validate_source,
    validate_verdict,
)

EX = Path(__file__).resolve().parents[4] / "domains" / "kcontext" / "contract" / "examples"
CARD_IDS = {"card_example_story", "card_example_now"}


def _load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


GOOD = [
    ("card_story.json", "card"),
    ("card_now.json", "card"),
    ("route.json", "route"),
    ("verdict.json", "verdict"),
    ("situation.json", "situation"),
    ("source.json", "source"),
]


@pytest.mark.parametrize(("name", "kind"), GOOD)
def test_good_examples_have_no_problems(name: str, kind: str) -> None:
    ensure_valid(kind, _load(EX / name))  # type: ignore[arg-type]


def test_route_example_refs_existing_cards() -> None:
    assert validate_route(_load(EX / "route.json"), CARD_IDS) == []
    assert validate_route(_load(EX / "route.json"), {"other"}) != []


def test_examples_are_marked_synthetic() -> None:
    for name in ("card_story.json", "card_now.json", "route.json"):
        text = (EX / name).read_text(encoding="utf-8")
        assert "○○" in text, name
    for name in ("card_story.json", "card_now.json"):
        card = _load(EX / name)
        assert card["synthetic"] is True and card["geometry"]["synthetic"] is True


BAD = sorted((EX / "bad").glob("*.json"))


def test_bad_examples_exist() -> None:
    assert len(BAD) >= 5


@pytest.mark.parametrize("path", BAD, ids=lambda p: p.name)
def test_bad_examples_contain_expected_problems(path: Path) -> None:
    d = _load(path)
    assert set(d) == {"kind", "obj", "expect"}
    fn = {"card": validate_card, "route": validate_route, "source": validate_source}[d["kind"]]
    if d["kind"] == "route":
        problems = validate_route(d["obj"], {"card_example_story"})
    else:
        problems = fn(d["obj"])
    assert problems, path.name
    joined = "\n".join(problems)
    for part in d["expect"]:
        assert part in joined, f"{path.name}: {part!r} 없음 -> {problems}"


def test_other_validators_reject_garbage() -> None:
    assert validate_verdict([]) and validate_situation("x") and validate_card(None)  # type: ignore[arg-type]
