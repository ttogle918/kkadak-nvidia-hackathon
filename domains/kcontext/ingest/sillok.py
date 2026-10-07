"""실록 수집기: XML → 기사 → 청크 → 로컬 색인. 호스트에서만 실행한다(D7).

- XML 은 표준 `ElementTree.iterparse` 로만 읽는다. DTD 를 가져오지 않고 엔티티를 풀지 않는다.
  DOCTYPE 은 D14 대로 `<!DOCTYPE 이름 SYSTEM "파일이름.dtd">` 하나만 허용하고, 파싱 전에 파일 앞 4KB 로 검사한다.
- 요소·속성 이름은 docs/spikes/sillok.md 의 표 그대로다. 국역이 없어 본문은 한문(`lang=orig`)이고,
  한글 제목은 한국사DB 편집자의 한 줄 요약이라 원문이 아니다(`meta["title_is_summary"]`).
- 청크 텍스트는 제목+본문(docs/spikes/sillok_embedding.md) — 인용(quote)은 항상 원문 구절만 쓴다.
- 지명 태그는 청크 meta 에 남기고, 지역 키워드와 같은 태그만 지명 사전(place_alias)에 적는다.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Literal
from xml.parsers import expat

from domains.kcontext.index import Chunk, LocalIndex, PlaceAlias, chunk_text, make_chunk_id
from domains.kcontext.regions import Region, load_regions, regions_in_text

__all__ = [
    "IngestReport",
    "SillokArticle",
    "SillokFormatError",
    "doctype_problem",
    "ingest",
    "main",
    "parse_file",
    "to_chunks",
]

SOURCE_NAME = "조선왕조실록"
URL_PREFIX = "https://sillok.history.go.kr/id/"  # 문자열만 만든다. 수집기는 호출하지 않는다.
HEAD_BYTES = 4096
MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_PLACES_PER_CHUNK = 30
CHUNK_CHARS = 800
QUOTE_CHARS = 300
BATCH = 1000

_DTD_NAME = re.compile(r"^(?!.*\.\.)[A-Za-z0-9_.\-]+\.dtd$")
_ARTICLE_ID = re.compile(r"^[A-Za-z0-9_]{1,64}$")  # 실측 형식(docs/spikes/sillok.md)
_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_LUNAR = re.compile(r"^\d{4}-\d{2}-\d{2}L[01]$")
_WS = re.compile(r"\s+")
# 원본 일부(5개 파일)는 보충 한자를 서로게이트 쌍 두 개의 문자 참조(&#55381;&#56892;)로 적어 XML 1.0 에서 잘못이다.
# 짝이 맞는 쌍만 하나의 코드포인트 참조로 합친다. 짝이 맞지 않는 서로게이트는 그대로 두어 파서가 거부한다.
_SURROGATE_PAIR = re.compile(r"&#(5[5-6]\d{3});&#(5[67]\d{3});")


class SillokFormatError(ValueError):
    """파일을 읽을 수 없거나 D14 검사를 통과하지 못했다."""


@dataclass(frozen=True)
class SillokArticle:
    article_id: str
    king: str | None
    date_label: str
    title: str | None
    text_ko: str | None
    text_orig: str | None
    url: str
    calendar: Literal["lunar", "solar", "unknown"]
    places: tuple[str, ...] = ()


@dataclass(frozen=True)
class IngestReport:
    files: int
    articles: int
    matched: int
    chunks: int
    skipped_files: tuple[tuple[str, str], ...]
    skipped_articles: int

    def as_dict(self) -> dict:
        d = self.__dict__ | {"skipped_files": [list(x) for x in self.skipped_files]}
        return d


class _Reject(Exception):
    pass


def doctype_problem(head: bytes | str) -> str | None:
    """D14 검사. 통과하면 None, 아니면 거부 이유. head 는 파일 앞 4KB.

    정규식이 아니라 expat 에게 문맥(주석·따옴표·내부 서브셋)을 판단시킨다. 선언 핸들러가 걸리면 즉시 거부하고,
    이 검사 파서는 DTD 를 읽지도 엔티티를 풀지도 않는다(외부 엔티티 핸들러 없음).
    """
    data = head.encode("utf-8") if isinstance(head, str) else head
    state = {"root": False}

    def reject(why: str):
        def _h(*_a: object) -> None:
            raise _Reject(why)

        return _h

    def xml_decl(_version: str, encoding: str | None, _standalone: int) -> None:
        if encoding is not None and encoding.lower().replace("_", "-") not in ("utf-8", "utf8"):
            raise _Reject("XML 선언의 encoding 이 UTF-8 이 아니다")

    def doctype(_name: str, system_id: str | None, public_id: str | None, has_internal: bool) -> None:
        if has_internal:
            raise _Reject("DOCTYPE 에 내부 서브셋이 있다")
        if public_id is not None:
            raise _Reject("PUBLIC 선언이다")
        if system_id is None or not _DTD_NAME.match(system_id):
            raise _Reject("SYSTEM 값이 '파일이름.dtd' 형태가 아니다(URL·경로 거부)")

    def start(_name: str, _attrs: object) -> None:
        state["root"] = True
        raise _Reject("")  # 루트 요소까지 왔다 — 더 읽을 필요 없다

    parser = expat.ParserCreate()
    parser.XmlDeclHandler = xml_decl
    parser.StartDoctypeDeclHandler = doctype
    parser.EntityDeclHandler = reject("ENTITY 선언이 있다")
    parser.ElementDeclHandler = reject("ELEMENT 선언이 있다")
    parser.AttlistDeclHandler = reject("ATTLIST 선언이 있다")
    parser.NotationDeclHandler = reject("NOTATION 선언이 있다")
    parser.StartElementHandler = start
    try:
        parser.Parse(data, False)
    except _Reject as e:
        return str(e) or None
    except expat.ExpatError as e:
        return f"프롤로그 구문 오류 ({e.code})"
    return None if state["root"] else "루트 요소를 4KB 안에서 찾지 못했다"


def _text(el: ET.Element | None) -> str:
    return _WS.sub(" ", "".join(el.itertext())).strip() if el is not None else ""


def _paragraphs(level5: ET.Element) -> str:
    paras = [_text(p) for p in level5.findall("text/content/paragraph")]
    return "\n\n".join(p for p in paras if p)


def _calendar(raw: str) -> Literal["lunar", "solar", "unknown"]:
    if _LUNAR.match(raw):
        return "lunar"  # 'L0' 가 음력 표지라는 것은 추정이다(docs/spikes/sillok.md). 양력 변환은 하지 않는다.
    if _ISO.match(raw):
        return "solar"
    return "unknown"


def _date_label(reign: str, raw: str, cal: str) -> str:
    base = reign or raw
    if cal == "lunar":
        return f"{base}(음력)"
    if cal == "unknown":
        return f"{base}(역법 미확인)" if base else "(날짜 미확인)"
    return base


def _join_pair(m: re.Match[str]) -> str:
    hi, lo = int(m.group(1)), int(m.group(2))
    if not (0xD800 <= hi <= 0xDBFF and 0xDC00 <= lo <= 0xDFFF):
        return m.group(0)
    return f"&#{0x10000 + ((hi - 0xD800) << 10) + (lo - 0xDC00)};"


def parse_file(path: Path) -> Iterator[SillokArticle]:
    """기사(level5) 단위로 읽는다. D14 검사에 실패하면 첫 기사 전에 SillokFormatError."""
    p = Path(path)
    try:
        if p.is_symlink():
            raise SillokFormatError("심볼릭 링크는 읽지 않는다")
        with p.open("rb") as f:
            blob = f.read(MAX_FILE_BYTES + 1)  # 검사와 파싱이 같은 바이트를 본다
    except OSError as e:
        raise SillokFormatError(f"읽을 수 없다 ({type(e).__name__})") from e
    if len(blob) > MAX_FILE_BYTES:
        raise SillokFormatError("파일이 너무 크다")
    problem = doctype_problem(blob[:HEAD_BYTES])
    if problem:
        raise SillokFormatError(problem)
    try:
        raw = blob.decode("utf-8")
    except UnicodeDecodeError as e:
        raise SillokFormatError("UTF-8 이 아니다") from e
    xml = io.BytesIO(_SURROGATE_PAIR.sub(_join_pair, raw).encode("utf-8"))
    try:
        for _, el in ET.iterparse(xml, events=("end",)):
            if el.tag != "level4":
                continue
            reign = _text(el.find("front/biblioData/date/dateOccured[@type='재위연도']"))
            king = reign.split(" ", 1)[0] if reign else None
            for l5 in el.findall("level5"):
                aid = (l5.get("id") or "").strip()
                if not _ARTICLE_ID.match(aid):  # 형식이 다르면 id 없는 기사로 센다(URL·source_id 에 쓰지 않는다)
                    yield SillokArticle("", king, "", None, None, None, "", "unknown")
                    continue
                solar = l5.find("front/biblioData/date/dateOccured[@type='서기']")
                raw = solar.get("date", "") if solar is not None else ""
                cal = _calendar(raw)
                places = tuple(dict.fromkeys(
                    n for i in l5.iter("index") if i.get("type") == "지명" and (n := _text(i)) and "|" not in n
                ))  # fmt: skip
                body = _paragraphs(l5)
                yield SillokArticle(
                    article_id=aid, king=king, date_label=_date_label(reign, raw, cal),
                    title=_text(l5.find("front/biblioData/title/mainTitle")) or None,
                    text_ko=None, text_orig=body or None, url=f"{URL_PREFIX}{aid}",
                    calendar=cal, places=places,
                )  # fmt: skip
            el.clear()
    except ET.ParseError as e:
        raise SillokFormatError(f"XML 구문 오류 ({e.code})") from e


def _region_field(regions: Mapping[str, Region]) -> Literal["keywords", "sillok_keywords"]:
    return "sillok_keywords" if any(r.sillok_keywords for r in regions.values()) else "keywords"


def to_chunks(a: SillokArticle, *, collected_at: str, regions: Mapping[str, Region]) -> list[Chunk]:
    """기사 하나를 청크로. 본문이 없으면 []. 국역이 있으면 국역, 없으면 원문(lang=orig)."""
    body, lang = (a.text_ko, "ko") if a.text_ko else (a.text_orig, "orig")
    if not body or not a.article_id:
        return []
    matched = regions_in_text(f"{a.title or ''}\n{body}", regions, field=_region_field(regions))
    pieces = chunk_text(body, max_chars=CHUNK_CHARS)
    locator = f"{a.date_label} · {a.article_id}"
    out = []
    for n, piece in enumerate(pieces, 1):
        loc = locator if len(pieces) == 1 else f"{locator} ({n}/{len(pieces)})"
        text = f"{a.title}\n{piece}" if a.title else piece
        meta = {
            "article_id": a.article_id, "calendar": a.calendar, "lang": lang,
            "chunk": f"{n}/{len(pieces)}", "title_is_summary": "true" if a.title else "false",
        }  # fmt: skip
        if a.king:
            meta["king"] = a.king
        if a.places:
            meta["places"] = "|".join(a.places[:MAX_PLACES_PER_CHUNK])
        source_id = f"sillok:{a.article_id}"
        out.append(Chunk(
            chunk_id=make_chunk_id(source_id, loc, text), source_id=source_id, tier="S",
            name=SOURCE_NAME, locator=loc, url=a.url, published=None, collected_at=collected_at,
            text=text, quote=piece[:QUOTE_CHARS], regions=tuple(matched), meta=meta,
        ))  # fmt: skip
    return out


def ingest(
    src: Path,
    index: LocalIndex,
    *,
    collected_at: str,
    regions: Mapping[str, Region],
    mode: Literal["regions", "all"] = "regions",
) -> IngestReport:
    """src 폴더의 *.xml 을 색인에 넣는다. 읽지 못한 파일은 건너뛰고 이유를 보고한다."""
    if mode not in ("regions", "all"):
        raise ValueError(f"mode: {mode}")
    try:
        date.fromisoformat(collected_at)
    except ValueError:
        raise ValueError("collected_at 은 YYYY-MM-DD 여야 한다") from None
    base = Path(src)
    if not base.is_dir():
        raise ValueError("src 는 폴더여야 한다")
    field = _region_field(regions)
    files = articles = matched = chunks = skipped_articles = 0
    skipped: list[tuple[str, str]] = []
    pending: list[Chunk] = []
    aliases: dict[tuple[str, str], PlaceAlias] = {}

    def flush() -> None:
        if pending:
            index.add(pending)
            pending.clear()

    for path in sorted(base.glob("*.xml")):
        buf: list[Chunk] = []
        file_aliases: dict[tuple[str, str], PlaceAlias] = {}
        n_art = n_skip = 0
        try:
            for a in parse_file(path):
                if not a.article_id or not a.text_orig:
                    n_skip += 1
                    continue
                n_art += 1
                cs = to_chunks(a, collected_at=collected_at, regions=regions)
                if not cs or (mode == "regions" and not cs[0].regions):
                    if cs:
                        n_skip += 1
                    continue
                buf.extend(cs)
                for rid in cs[0].regions:
                    kws = set(getattr(regions[rid], field))
                    for place in a.places:
                        if place in kws:
                            file_aliases[(place, place)] = PlaceAlias(place, place, "hanja", rid, "sillok:index")
        except SillokFormatError as e:
            skipped.append((path.name, str(e)))
            continue  # 이 파일의 기사는 하나도 반영하지 않는다
        aliases.update(file_aliases)  # 파일이 끝까지 읽힌 뒤에만 반영
        files += 1
        articles += n_art
        skipped_articles += n_skip
        matched += len({c.meta["article_id"] for c in buf})
        chunks += len(buf)
        pending.extend(buf)
        if len(pending) >= BATCH:
            flush()
    flush()
    if aliases:
        index.add_place_aliases(aliases.values())
    return IngestReport(files, articles, matched, chunks, tuple(skipped), skipped_articles)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m domains.kcontext.ingest.sillok")
    p.add_argument("--src", required=True)
    p.add_argument("--db", required=True)
    p.add_argument("--collected-at", required=True)
    p.add_argument("--mode", choices=("regions", "all"), default="regions")
    a = p.parse_args(argv)
    try:
        with LocalIndex(a.db) as idx:
            report = ingest(Path(a.src), idx, collected_at=a.collected_at, regions=load_regions(), mode=a.mode)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report.as_dict(), ensure_ascii=False))
    return 0 if report.files else 2


if __name__ == "__main__":
    raise SystemExit(main())
