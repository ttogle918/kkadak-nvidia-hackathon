"""실록 키워드 측정·자동 후보 도구 (D28 ②). 호스트에서만 실행한다(D7).

- `count`      키워드가 기사 제목·본문에 몇 건 나오는지 센다.
- `places`     `<index type="지명">` 태그 빈도 상위 N 개.
- `dongs`      (보조) 서울 열린데이터광장 응답 파일 → `{구 이름: [동 이름]}` 변환. 네트워크를 쓰지 않는다.
- `candidates` 지명 태그를 한글 독음으로 읽어 구별 행정동 이름의 어근과 완전 일치하면 후보로 낸다.

도구는 후보와 건수만 출력한다. 지역 파일(`data/regions/*.json`)은 읽지도 고치지도 않는다(구 이름 연결만 `load_regions` 로 읽는다).
어떤 후보를 `sillok_keywords` 에 넣을지는 사람이 고른다. 일반명사 동명(방위·관청 이름 등)도 걸러내지 않는다.
실록 XML 은 `sillok.parse_file` 로만 읽는다 — D14 검사에 걸린 파일은 `_meta.skipped_files` 에 남는다.
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
from collections import Counter
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path

from domains.kcontext.ingest.sillok import SillokArticle, SillokFormatError, parse_file
from domains.kcontext.regions import Region, load_regions

__all__ = [
    "count_keywords",
    "dong_root",
    "dongs_from_seoul_rows",
    "load_unihan_hangul",
    "main",
    "make_candidates",
    "reading_combos",
    "top_place_tags",
]

MAX_COMBOS = 8
_HANGUL = re.compile(r"[가-힣]+")
_UNIHAN_LINE = re.compile(r"^U\+([0-9A-Fa-f]{4,6})\tkHangul\t(.+)$")
_NUM_SUFFIX = re.compile(r"제?[\d·,.\-~]+가?$")


def _files(src: Path) -> list[Path]:
    p = Path(src)
    if p.is_dir():
        return sorted(p.glob("*.xml"))
    if p.is_file():
        return [p]
    raise ValueError("src 는 XML 파일이나 폴더여야 한다")


def _scan(src: Path, skipped: list[tuple[str, str]]) -> Iterator[SillokArticle]:
    """파일 단위로 읽는다. D14 등으로 읽지 못한 파일은 그 기사를 하나도 내보내지 않는다."""
    for path in _files(src):
        buf: list[SillokArticle] = []
        try:
            buf.extend(a for a in parse_file(path) if a.article_id)
        except SillokFormatError as e:
            skipped.append((path.name, str(e)))
            continue
        yield from buf


def count_keywords(src: Path, candidates: Mapping[str, Iterable[str]]) -> dict:
    """{region: [kw..]} → {region: {kw: {title, body, articles}}, "_meta": {...}}.

    title/body 는 그 키워드가 제목/본문에 들어 있는 기사 수, articles 는 둘 중 하나라도 있는 기사 수다.
    """
    kws = {rid: list(dict.fromkeys(k for k in ks if isinstance(k, str) and k)) for rid, ks in candidates.items()}
    out: dict = {rid: {k: {"title": 0, "body": 0, "articles": 0} for k in ks} for rid, ks in kws.items()}
    skipped: list[tuple[str, str]] = []
    files = len(_files(src))
    total = 0
    for a in _scan(Path(src), skipped):
        total += 1
        title, body = a.title or "", a.text_orig or ""
        for rid, ks in kws.items():
            for k in ks:
                in_t, in_b = k in title, k in body
                if in_t or in_b:
                    c = out[rid][k]
                    c["title"] += in_t
                    c["body"] += in_b
                    c["articles"] += 1
    out["_meta"] = {
        "files": files, "files_read": files - len(skipped), "articles": total,
        "skipped_files": [list(x) for x in skipped],
    }  # fmt: skip
    return out


def top_place_tags(src: Path, top: int = 500) -> list[tuple[str, int]]:
    """`<index type="지명">` 태그를 기사 단위로(한 기사에서 여러 번 나와도 1) 세어 상위 top 개."""
    if top < 1:
        raise ValueError("top 은 1 이상이어야 한다")
    c: Counter[str] = Counter()
    for a in _scan(Path(src), []):
        c.update(a.places)  # SillokArticle.places 는 기사 안에서 이미 중복이 없다
    return sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:top]


# ---- 독음 ---------------------------------------------------------------------------------
def load_unihan_hangul(path: Path) -> dict[str, tuple[str, ...]]:
    """Unihan_Readings.txt 의 kHangul 줄만 읽는다. 값 `한:0E 칸:0N` → ("한", "칸"). 다른 필드·주석은 무시."""
    out: dict[str, tuple[str, ...]] = {}
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            m = _UNIHAN_LINE.match(line.rstrip("\n"))
            if not m:
                continue
            rs = tuple(dict.fromkeys(
                r for tok in m.group(2).split() if (r := tok.split(":", 1)[0]) and _HANGUL.fullmatch(r)
            ))  # fmt: skip
            if rs:
                out[chr(int(m.group(1), 16))] = rs
    return out


def reading_combos(tag: str, readings: Mapping[str, tuple[str, ...]], limit: int = MAX_COMBOS) -> list[str]:
    """태그를 한글로 읽은 조합. 글자별 독음의 곱을 첫 독음 우선 순서로 최대 limit 개. 독음 없는 글자가 있으면 []."""
    if not tag:
        return []
    per_char = []
    for ch in tag:
        rs = readings.get(ch)
        if not rs:
            return []
        per_char.append(rs)
    return list(dict.fromkeys("".join(c) for c in itertools.islice(itertools.product(*per_char), limit)))



def dongs_from_seoul_rows(
    rows: Iterable[Mapping[str, object]], gu_codes: Mapping[str, str]
) -> dict[str, list[str]]:
    """서울 열린데이터광장 행(ADSTRD_CD·ADSTRD_CD_NM·STDR_YYQU_CD) → {구 이름: [동 이름]}.

    분기 코드가 있으면 가장 최근 분기의 행만 쓴다. 코드 앞 5자리(시군구)가 gu_codes({"11110": "구 이름"}) 에 없으면 버린다.
    구 코드표는 코드에 지역 이름을 박지 않으려고 파일로 받는다(docs/spikes/sillok_candidates.md).
    """
    rs = [r for r in rows if isinstance(r.get("ADSTRD_CD"), str) and isinstance(r.get("ADSTRD_CD_NM"), str)]
    quarters = [q for r in rs if isinstance(q := r.get("STDR_YYQU_CD"), str)]
    if quarters:
        latest = max(quarters)
        rs = [r for r in rs if r.get("STDR_YYQU_CD") == latest]
    out: dict[str, set[str]] = {}
    for r in rs:
        gu = gu_codes.get(str(r["ADSTRD_CD"])[:5])
        if gu and str(r["ADSTRD_CD_NM"]).strip():
            out.setdefault(gu, set()).add(str(r["ADSTRD_CD_NM"]).strip())
    return {gu: sorted(v) for gu, v in sorted(out.items())}


def dong_root(dong: str) -> str:
    """'○○1동' → '○○', '○1·2·3·4가동' → '○', '○○동' → '○○'. 어근이 비면 ''."""
    s = dong.strip()
    if s.endswith("동") and len(s) > 1:
        s = s[:-1]
    return _NUM_SUFFIX.sub("", s)


def make_candidates(
    tags: Iterable[tuple[str, int]],
    dongs_by_gu: Mapping[str, Iterable[str]],
    readings: Mapping[str, tuple[str, ...]],
    regions: Mapping[str, Region],
) -> dict[str, list[dict]]:
    """지명 태그 (tag, 기사 수) → {region_id: [후보]}.

    후보 = 태그의 독음 조합이 어떤 동의 어근과 완전 일치. 구 이름이 어느 지역 파일의 `gu` 에도 없으면 구 이름을 키로 쓴다.
    한 태그가 여러 구에 걸리면 모두 후보로 내고 `ambiguous: true`. 건수 내림차순.
    """
    gu_to_key = {g: rid for rid, r in regions.items() for g in r.gu}
    root_index: dict[str, list[tuple[str, str, str]]] = {}  # 어근 → [(키, 구, 동)]
    for gu, dongs in dongs_by_gu.items():
        for dong in dongs:
            root = dong_root(dong)
            if root:
                root_index.setdefault(root, []).append((gu_to_key.get(gu, gu), gu, dong))
    out: dict[str, list[dict]] = {}
    for tag, n in tags:
        for reading in reading_combos(tag, readings):
            hits = root_index.get(reading, [])
            ambiguous = len({gu for _, gu, _ in hits}) > 1
            for key, _gu, dong in hits:
                row = {"tag": tag, "reading": reading, "dong": dong, "articles": n}
                if ambiguous:
                    row["ambiguous"] = True
                lst = out.setdefault(key, [])
                if row not in lst:
                    lst.append(row)
    for lst in out.values():
        lst.sort(key=lambda r: (-r["articles"], r["tag"], r["dong"]))
    return out


# ---- CLI ----------------------------------------------------------------------------------
def _load_json(path: str, what: str) -> object:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ValueError(f"{what} 를 읽을 수 없다 ({type(e).__name__})") from e


def _emit(obj: object, out: str | None) -> None:
    text = json.dumps(obj, ensure_ascii=False, indent=2)
    if out:
        p = Path(out)
        if "regions" in p.parts and p.suffix == ".json" and "data" in p.parts:
            raise ValueError("지역 파일(data/regions)에는 쓰지 않는다 — 후보는 사람이 골라 넣는다")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def _str_map(obj: object, what: str) -> dict[str, list[str]]:
    if not isinstance(obj, dict) or not all(
        isinstance(k, str) and isinstance(v, list) and all(isinstance(x, str) for x in v) for k, v in obj.items()
    ):
        raise ValueError(f'{what} 는 {{"이름": ["문자열", ...]}} 형식이어야 한다')
    return obj


def _str_dict(obj: object) -> dict[str, str]:
    if not isinstance(obj, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in obj.items()):
        raise ValueError('gu-codes 는 {"코드": "이름"} 형식이어야 한다')
    return obj


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m domains.kcontext.ingest.sillok_keywords")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("count")
    c.add_argument("--src", required=True)
    c.add_argument("--candidates", required=True)
    c.add_argument("--out")
    pl = sub.add_parser("places")
    pl.add_argument("--src", required=True)
    pl.add_argument("--top", type=int, default=500)
    pl.add_argument("--out")
    dg = sub.add_parser("dongs")
    dg.add_argument("--from-seoul", required=True, help="서울 열린데이터광장 JSON 응답 파일")
    dg.add_argument("--gu-codes", required=True, help='{"11110": "구 이름", ...} 시군구 코드표')
    dg.add_argument("--out")
    ca = sub.add_parser("candidates")
    ca.add_argument("--src", required=True)
    ca.add_argument("--dongs", required=True)
    ca.add_argument("--readings", required=True)
    ca.add_argument("--top", type=int, default=2000)
    ca.add_argument("--out")
    a = p.parse_args(argv)
    try:
        if a.cmd == "count":
            result: object = count_keywords(Path(a.src), _str_map(_load_json(a.candidates, "candidates"), "candidates"))
        elif a.cmd == "places":
            result = [{"tag": t, "articles": n} for t, n in top_place_tags(Path(a.src), a.top)]
        elif a.cmd == "dongs":
            raw = _load_json(a.from_seoul, "from-seoul")
            rows = next((v["row"] for v in raw.values() if isinstance(v, dict) and "row" in v), []) if isinstance(raw, dict) else []
            result = dongs_from_seoul_rows(rows, _str_dict(_load_json(a.gu_codes, "gu-codes")))
            if not result:
                raise ValueError("행정동 행이 없다 (응답 형식 확인)")
        else:
            dongs = _str_map(_load_json(a.dongs, "dongs"), "dongs")
            readings = load_unihan_hangul(Path(a.readings))
            tags = top_place_tags(Path(a.src), a.top)
            cands = make_candidates(tags, dongs, readings, load_regions())
            uniq = sorted({r["tag"] for rows in cands.values() for r in rows})
            stats = count_keywords(Path(a.src), {"_": uniq})["_"] if uniq else {}
            for rows in cands.values():
                for r in rows:
                    r["count"] = stats.get(r["tag"], {})
            result = cands
        _emit(result, a.out)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
