"""데모 재현용 행사 스냅샷 (D19).

    python scripts/snapshot_catalog.py --from var/catalog --to domains/kcontext/data/snapshots/catalog
    python scripts/snapshot_catalog.py --restore --from domains/kcontext/data/snapshots/catalog \
        --to var/catalog [--force]

만들기: 서울 열린데이터광장(``seoul_openapi``, 공공누리 1유형) 관찰값만 남기고 ``build_entries`` 로 다시 묶는다.
검색(Tavily 등)·제보 유래는 하나도 섞지 않는다(D12 ⑦). 수집 기록은 같은 출처 것만, 키·URL 키 파라미터는 지운다.
되돌리기: 대상 폴더가 있으면 거부하고 ``--force`` 면 교체한다.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from domains.kcontext.catalog.envkeys import CATALOG_KEY_NAMES, resolve_catalog_env
from domains.kcontext.catalog.merge import build_entries
from domains.kcontext.catalog.rules import to_kst
from domains.kcontext.catalog.store import CatalogStore

__all__ = ["SOURCE_ID", "main", "make_snapshot", "restore_snapshot"]

SOURCE_ID = "seoul_openapi"
SOURCE_NAME = "서울 열린데이터광장 문화행사 정보"
LICENSE_LINE = "공공누리 제1유형(출처표시) — 출처: 서울특별시, 서울 열린데이터광장"
FILES = ("observations.json", "entries.json", "runs.json", "SNAPSHOT.md")
# 비밀 파라미터 이름은 정확히 일치할 때만 지운다(uidKey·bnkey 같은 일반 파라미터는 보존).
SECRET_PARAMS = ("servicekey", "apikey", "api_key", "access_token", "token")
_QUERY_SECRET = re.compile(
    r"(?i)([?&;](?:" + "|".join(SECRET_PARAMS) + r")=)[^&#\s\"']*")
_SECRETISH = re.compile(r"(?i)(?:api[_-]?key|service[_-]?key|token|secret)[\"']?\s*[:=]\s*[\"']?(?!REDACTED)[A-Za-z0-9%+/_-]{8,}")


class SnapshotError(Exception):
    pass


def _env_secrets() -> list[str]:
    return [v for v in resolve_catalog_env(CATALOG_KEY_NAMES).values() if len(v) >= 8]


def _scrub(v):
    """문자열 안의 키 파라미터·비밀 패턴을 지운다(구조 유지)."""
    if isinstance(v, str):
        for secret in _env_secrets():  # 서울 API 는 키가 URL 경로에도 들어간다
            v = v.replace(secret, "REDACTED")
        return _QUERY_SECRET.sub(r"\1REDACTED", v)
    if isinstance(v, dict):
        return {k: _scrub(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_scrub(x) for x in v]
    return v


def _now_iso(now: datetime) -> str:
    return to_kst(now).strftime("%Y-%m-%dT%H:%M")


def make_snapshot(
    src: Path, dst: Path, *, now: datetime, command: str, force: bool = False, since: str | None = None,
) -> dict:
    src_store = CatalogStore(src)
    if not (src / "observations.json").exists():
        raise SnapshotError(f"관찰값 파일이 없다: {src}/observations.json")
    if dst.exists() and any(dst.iterdir()) and not force:
        raise SnapshotError(f"대상이 이미 있다: {dst} (--force 로 교체)")
    obs = {
        k: v for k, v in src_store.load_observations().items()
        if v["observation"].evidence is not None and v["observation"].evidence.source_id == SOURCE_ID
    }
    if not obs:
        raise SnapshotError(f"{SOURCE_ID} 관찰값이 없다")
    since = since or to_kst(now).strftime("%Y-%m-%d")
    old = src_store.load_entries()
    prior = {k: e.id for e in old for k in e.external_ids}
    seen = {k: v["last_seen_at"] for k, v in obs.items()}
    entries = build_entries([v["observation"] for v in obs.values()], now=now,
                            verified_at=_now_iso(now), prior=prior, seen_at=seen)
    total_entries = len(entries)
    # 스냅샷 날짜에 이미 끝난 행사는 뺀다(종료일이 없으면 남긴다). 관찰값은 남긴 항목에 딸린 것만.
    # D23: 종료일·회차가 없고 시작한 지 1년이 넘은 항목도 뺀다(검색에서 제외되는 것과 같은 규칙).
    cutoff = (date.fromisoformat(since) - timedelta(days=365)).isoformat()

    def _keep(e) -> bool:
        sc = e.schedule
        if sc.end_date:
            return sc.end_date >= since
        if sc.sessions or not sc.start_date:
            return True
        return sc.start_date >= cutoff

    n_before = len(entries)
    ended = [e for e in entries if e.schedule.end_date and e.schedule.end_date < since]
    entries = [e for e in entries if _keep(e)]
    stale = n_before - len(entries) - len(ended)  # D23 로 빠진 수
    keep_ids = {i for e in entries for i in e.external_ids}
    obs = {k: v for k, v in obs.items()
           if keep_ids.intersection(v["observation"].external_ids) or k in keep_ids}
    if not entries:
        raise SnapshotError(f"{since} 이후에 끝나는 행사가 없다")
    runs = {k: _scrub(v) for k, v in src_store.load_runs().items() if k == SOURCE_ID}
    for r in runs.values():  # 오류 문구는 URL 을 품을 수 있어 예외 이름만 남긴다
        if r.get("last_error"):
            r["last_error"] = str(r["last_error"]).split(":", 1)[0][:80]

    tmp = dst.with_name(dst.name + ".tmp")
    shutil.rmtree(tmp, ignore_errors=True)
    out = CatalogStore(tmp)
    out.save_observations(obs)
    out.save_entries(entries, _now_iso(now))
    out.save_runs(runs)
    for p in tmp.glob("*.json"):  # URL 의 키 파라미터 제거(원문 링크가 항목에도 들어간다)
        data = _scrub(json.loads(p.read_text(encoding="utf-8")))
        p.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    dates = sorted({v["observation"].evidence.collected_at for v in obs.values()})
    (tmp / "SNAPSHOT.md").write_text(_snapshot_md(len(obs), len(entries), dates, now, command, since,
                                                  total_entries - len(entries), stale),
                                     encoding="utf-8")
    try:
        _assert_no_secret(tmp)
    except SnapshotError:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    if dst.exists():
        shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp.rename(dst)
    return {"observations": len(obs), "entries": len(entries), "dates": dates,
            "dropped_entries": total_entries - len(entries), "since": since}


def _assert_no_secret(folder: Path) -> None:
    values = _env_secrets()
    for p in folder.rglob("*"):
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        if any(v in text for v in values) or _SECRETISH.search(text):
            raise SnapshotError(f"비밀로 보이는 값이 남았다: {p.name}")


def _snapshot_md(
    n_obs: int, n_entries: int, dates: list[str], now: datetime, command: str, since: str, dropped: int, stale: int = 0,
) -> str:
    span = dates[0] if len(dates) == 1 else f"{dates[0]} ~ {dates[-1]}"
    return (
        "# 행사 카탈로그 스냅샷\n\n"
        f"- 출처: {SOURCE_NAME} (`{SOURCE_ID}`)\n"
        f"- 이용 조건: {LICENSE_LINE}\n"
        f"- 수집일: {span} (스냅샷 생성 {now.strftime('%Y-%m-%d')})\n"
        f"- 건수: 관찰값 {n_obs}건 · 행사 항목 {n_entries}건\n"
        f"- 범위: 스냅샷 날짜에 끝나지 않은 행사만 (종료일 {since} 이후이거나, 종료일이 없으면 시작한 지 1년 이내 — D23). "
        f"걸러낸 항목 {dropped}건 (그중 종료일 없이 1년 넘은 항목 {stale}건)\n"
        "- 포함하지 않은 것: 검색(Tavily 등) 유래 자료, 제보, 원응답, 키 (D12 ⑦, D19)\n\n"
        "스냅샷은 수집 시점 자료이며 이후 바뀌었을 수 있다.\n\n"
        f"생성 명령:\n\n```\n{command}\n```\n\n"
        "되돌리기: `python scripts/snapshot_catalog.py --restore --from <이 폴더> --to var/catalog`\n"
    )


def restore_snapshot(src: Path, dst: Path, *, force: bool = False) -> None:
    if not (src / "observations.json").exists():
        raise SnapshotError(f"스냅샷이 아니다: {src}")
    if dst.exists():
        if not force:
            raise SnapshotError(f"대상이 이미 있다: {dst} (--force 로 교체)")
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    for name in FILES:
        if (src / name).exists():
            shutil.copy2(src / name, dst / name)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="행사 카탈로그 스냅샷 만들기·되돌리기 (D19)")
    ap.add_argument("--from", dest="src", required=True, type=Path)
    ap.add_argument("--to", dest="dst", required=True, type=Path)
    ap.add_argument("--since", help="이 날짜(YYYY-MM-DD) 이후에 끝나는 행사만. 기본은 오늘(KST)")
    ap.add_argument("--restore", action="store_true")
    ap.add_argument("--force", action="store_true", help="되돌리기 대상이 있으면 교체")
    a = ap.parse_args(argv)
    try:
        if a.restore:
            restore_snapshot(a.src, a.dst, force=a.force)
            print(f"복원: {a.src} -> {a.dst}")
        else:
            cmd = f"python scripts/snapshot_catalog.py --from {a.src} --to {a.dst}"
            if a.since:
                cmd += f" --since {a.since}"
            r = make_snapshot(a.src, a.dst, now=datetime.now().astimezone(), command=cmd, force=True,
                              since=a.since)
            print(f"스냅샷: 관찰값 {r['observations']} · 항목 {r['entries']} -> {a.dst}")
    except SnapshotError as e:
        print(f"실패: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
