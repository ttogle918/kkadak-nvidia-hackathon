"""데모 장소 사전 로더 — 이름 → 검증된 좌표. 사전에 없는 장소의 좌표는 만들지 않는다(호출 쪽이 null 로 둔다).

사전 파일은 ``data/places/*.json`` (기본 ``demo_places.json``)이고 지명은 코드에 두지 않는다.
알아 둘 것: 카카오맵 검색(PlayMCP)은 위·경도를 주지 않고 이름·주소·링크만 준다.
사전을 늘리려면 카카오 JS SDK Places 검색 결과의 좌표나 길찾기 응답의 sp/ep 를 사람이 확인해 파일에 한 줄 추가한다.
이 모듈은 네트워크를 쓰지 않는다. 파일 형식: [{name, aliases[], lat, lng, source, verified_at, note}].
"""

from __future__ import annotations

import json
import os
import unicodedata
import warnings
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from domains.kcontext.paths import data_dir, var_dir

__all__ = ["Place", "PlaceBook", "PlacesConfigError", "auto_path", "default_path", "load_places", "norm"]

_REQUIRED = {"name", "aliases", "lat", "lng", "source", "verified_at", "note"}  # 전부 필수 — note 는 빈 문자열이어도 된다
_AUTO_KEYS = {"auto", "origin"}  # 자동 사전(D25) 항목에만 허용
_KEYS = _REQUIRED | _AUTO_KEYS
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
    auto: bool = False  # 서울 API 좌표에서 자동 생성한 항목(D25) — 화면에 "공공 데이터 좌표" 로 밝힌다
    origin: tuple[str, ...] = ()


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


def auto_path() -> Path:
    """자동 사전 위치: env KC_AUTO_PLACES, 기본 <var>/places/auto_places.json (커밋하지 않는다, D25 ⑤)."""
    env = os.environ.get("KC_AUTO_PLACES")
    return Path(env) if env else var_dir() / "places" / "auto_places.json"


def _is_num(v: object) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _str(v: object, what: str, where: str, *, allow_empty: bool = False) -> str:
    if not isinstance(v, str) or (not allow_empty and not v.strip()) or len(v) > MAX_STR:
        raise PlacesConfigError(f"{where}: {what} 는 {MAX_STR}자 이하 문자열이어야 한다")
    return v


def _parse_one(raw: object, where: str, *, auto: bool = False) -> Place:
    if not isinstance(raw, dict):
        raise PlacesConfigError(f"{where}: 항목이 객체가 아니다")
    unknown = set(raw) - (_KEYS if auto else _REQUIRED)
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
    origin: tuple[str, ...] = ()
    if auto:
        if raw.get("auto") is not True:
            raise PlacesConfigError(f"{where}: 자동 사전 항목은 auto: true 여야 한다")
        og = raw.get("origin")
        if not isinstance(og, list) or not og:
            raise PlacesConfigError(f"{where}: origin 은 비어 있지 않은 목록이어야 한다")
        origin = tuple(_str(o, "origin 항목", where) for o in og)
    return Place(name, al, float(lat), float(lng), source, verified, note, auto, origin)


def _read_places(p: Path, *, auto: bool) -> list[Place]:
    fname = p.name
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise PlacesConfigError(f"{fname}: 읽을 수 없다 ({type(e).__name__})") from e
    if not isinstance(raw, list):
        raise PlacesConfigError(f"{fname}: 최상위가 목록이 아니다")
    places = [_parse_one(r, f"{fname}[{i}]", auto=auto) for i, r in enumerate(raw)]
    seen: dict[str, str] = {}
    for pl in places:
        for n in (pl.name, *pl.aliases):
            k = norm(n)
            if k in seen:
                raise PlacesConfigError(f"{fname}: 이름·별칭 중복 ({seen[k]} / {pl.name})")
            seen[k] = pl.name
    return places


def load_places(path: Path | str | None = None, *, auto: Path | str | None = "default") -> PlaceBook:
    """사람 사전을 읽어 검증한다(이름·별칭이 정규화 후 겹치면 거부). 자동 사전(D25)이 있으면 덧붙인다.

    ``auto``: "default" 는 ``path`` 를 따로 주지 않았을 때만 ``auto_path()`` 를 쓴다(path 를 준 호출은 그 파일만),
    None 은 쓰지 않음, 경로는 그 파일. 자동 파일이 없으면 조용히 사람 사전만, 깨졌으면 경고 1줄 + 사람 사전만.
    사람 이름·별칭과 겹치는 자동 항목은 버린다(사람 값 우선, D25 ④).
    """
    p = Path(path) if path is not None else default_path()
    manual = _read_places(p, auto=False)
    ap: Path | None
    if auto == "default":
        ap = auto_path() if path is None else None
    else:
        ap = Path(auto) if auto else None  # type: ignore[arg-type]
    extra: list[Place] = []
    if ap is not None and ap.exists():
        try:
            extra = _read_places(ap, auto=True)
        except PlacesConfigError as e:
            warnings.warn(f"자동 장소 사전을 쓰지 않음: {e}", stacklevel=2)
    if extra:
        taken = {norm(n) for pl in manual for n in (pl.name, *pl.aliases)}
        extra = [pl for pl in extra if not any(norm(n) in taken for n in (pl.name, *pl.aliases))]
    return PlaceBook([*manual, *extra])
