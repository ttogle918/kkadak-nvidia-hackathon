"""데모 장소 사전 로더 — 이름 → 검증된 좌표. 사전에 없는 장소의 좌표는 만들지 않는다(호출 쪽이 null 로 둔다).

사전 파일은 ``data/places/*.json`` (기본 ``demo_places.json``)이고 지명은 코드에 두지 않는다.
알아 둘 것: 카카오맵 검색(PlayMCP)은 위·경도를 주지 않고 이름·주소·링크만 준다.
사전을 늘리려면 카카오 JS SDK Places 검색 결과의 좌표나 길찾기 응답의 sp/ep 를 사람이 확인해 파일에 한 줄 추가한다.
이 모듈은 네트워크를 쓰지 않는다. 파일 형식: [{name, aliases[], lat, lng, source, verified_at, note}].
"""

from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from domains.kcontext.paths import data_dir

__all__ = ["Place", "PlaceBook", "PlacesConfigError", "default_path", "load_places"]

_KEYS = {"name", "aliases", "lat", "lng", "source", "verified_at", "note"}
_REQUIRED = _KEYS  # 전부 필수 — note 는 빈 문자열이어도 된다
MAX_STR = 200


class PlacesConfigError(ValueError):
    """장소 사전 오류. 메시지에 파일 이름과 항목 번호가 들어간다."""


@dataclass(frozen=True)
class Place:
    name: str
    aliases: tuple[str, ...]
    lat: float
    lng: float
    source: str
    verified_at: str
    note: str


def norm(name: str) -> str:
    """이름 비교 키: NFKC, 공백 정리, 소문자."""
    return " ".join(unicodedata.normalize("NFKC", name).split()).casefold()


class PlaceBook:
    def __init__(self, places: list[Place]) -> None:
        self.places = tuple(places)
        self._by_key: dict[str, Place] = {}
        for p in places:
            for n in (p.name, *p.aliases):
                self._by_key[norm(n)] = p

    def lookup(self, name: object) -> Place | None:
        if not isinstance(name, str):
            return None
        return self._by_key.get(norm(name))

    def __len__(self) -> int:
        return len(self.places)


def default_path() -> Path:
    return data_dir() / "places" / "demo_places.json"


def _is_num(v: object) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _str(v: object, what: str, where: str, *, allow_empty: bool = False) -> str:
    if not isinstance(v, str) or (not allow_empty and not v.strip()) or len(v) > MAX_STR:
        raise PlacesConfigError(f"{where}: {what} 는 {MAX_STR}자 이하 문자열이어야 한다")
    return v


def _parse_one(raw: object, where: str) -> Place:
    if not isinstance(raw, dict):
        raise PlacesConfigError(f"{where}: 항목이 객체가 아니다")
    unknown = set(raw) - _KEYS
    if unknown:
        raise PlacesConfigError(f"{where}: 모르는 키 {sorted(unknown)}")
    missing = _REQUIRED - set(raw)
    if missing:
        raise PlacesConfigError(f"{where}: 빠진 키 {sorted(missing)}")
    name = _str(raw["name"], "name", where)
    aliases = raw["aliases"]
    if not isinstance(aliases, list):
        raise PlacesConfigError(f"{where}: aliases 는 목록이어야 한다")
    al = tuple(_str(a, "aliases 항목", where) for a in aliases)
    lat, lng = raw["lat"], raw["lng"]
    if not (_is_num(lat) and _is_num(lng)):
        raise PlacesConfigError(f"{where}: lat·lng 는 숫자여야 한다")
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        raise PlacesConfigError(f"{where}: 좌표 범위 오류 (lat -90..90, lng -180..180)")
    source = _str(raw["source"], "source", where)
    verified = _str(raw["verified_at"], "verified_at", where)
    try:
        date.fromisoformat(verified)
    except ValueError as e:
        raise PlacesConfigError(f"{where}: verified_at 은 YYYY-MM-DD 여야 한다") from e
    note = _str(raw["note"], "note", where, allow_empty=True)
    return Place(name, al, float(lat), float(lng), source, verified, note)


def load_places(path: Path | str | None = None) -> PlaceBook:
    """사전 파일을 읽어 검증한다. 이름·별칭이 (정규화 후) 겹치면 거부한다."""
    p = Path(path) if path is not None else default_path()
    fname = p.name
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise PlacesConfigError(f"{fname}: 읽을 수 없다 ({type(e).__name__})") from e
    if not isinstance(raw, list):
        raise PlacesConfigError(f"{fname}: 최상위가 목록이 아니다")
    places = [_parse_one(r, f"{fname}[{i}]") for i, r in enumerate(raw)]
    seen: dict[str, str] = {}
    for pl in places:
        for n in (pl.name, *pl.aliases):
            k = norm(n)
            if k in seen:
                raise PlacesConfigError(f"{fname}: 이름·별칭 중복 ({seen[k]} / {pl.name})")
            seen[k] = pl.name
    return PlaceBook(places)
