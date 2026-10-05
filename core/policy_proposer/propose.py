"""audit/v1 이벤트 → PolicyDraft (D4). 순수 함수, 파일 I/O 없음(jsonl 읽기 제외).

최소 권한: 와일드카드로 일반화하지 않고, 허용 주체(binary)를 특정할 수 없으면 제안하지 않는다.
"""

from __future__ import annotations

import hashlib
import posixpath
import re
from collections.abc import Iterable
from pathlib import Path

from core.audit import AuditEvent, AuditFormatError, read_jsonl, redact_text
from core.policy_proposer import baseline
from core.policy_proposer.model import (
    Evidence,
    FsEntry,
    NetworkEntry,
    PolicyDraft,
    Skipped,
)

_META = set("*?[]{}")
_HTTP_METHODS = frozenset({"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"})
# 경로·binary 문자 허용 목록(ASCII). ; \\ 공백 비ASCII 등은 서버·파서마다 해석이 달라 거부한다.
_PATH_CHARS = re.compile(r"[A-Za-z0-9._~/@+%-]+")
_UPPER = {c: c - 32 for c in range(ord("a"), ord("z") + 1)}
_LABEL = r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
_HOSTNAME = re.compile(rf"{_LABEL}(?:\.{_LABEL})*")
_OCT = r"(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])"
_IPV4 = re.compile(rf"{_OCT}(?:\.{_OCT}){{3}}")


def _unsafe(v: str, *, absolute: bool = False) -> str | None:
    """정책 본문에 쓸 수 없는 값이면 사유, 안전하면 None (fail-closed).

    redact 로 바뀌는 값·REDACTED·glob/메타 문자·제어/공백 문자는 정책 값이 될 수 없다.
    """
    if not isinstance(v, str) or not v:
        return "빈 값 또는 문자열이 아님"
    if redact_text(v) != v or "REDACTED" in v:
        return "비밀로 보이거나 마스킹된 값"
    if any(c in _META for c in v):
        return "glob/메타 문자 포함"
    if any((not c.isprintable()) or c.isspace() for c in v):
        return "제어·공백 문자 포함"
    if absolute:
        if not v.startswith("/"):
            return "절대 경로가 아님"
        if _normpath(v) != v:
            return "정규화되지 않은 경로"
        if not _PATH_CHARS.fullmatch(v):
            return "허용 문자 집합 밖(ASCII 영숫자·._~/@+%- 만)"
    return None


def _normpath(path: str) -> str:
    """AuditLog.observe_file 과 같은 규칙."""
    norm = posixpath.normpath(path)
    if norm.startswith("//"):
        norm = "/" + norm.lstrip("/")
    return norm


def _norm_host(host: str) -> str:
    return host.strip().lower().rstrip(".")


def _upper_ascii(s: str) -> str:
    """ASCII 만 대문자로(ß→SS, ı→I 같은 유니코드 변환 금지)."""
    return s.translate(_UPPER)


def _host_bad(host: str) -> str | None:
    """소문자 ASCII hostname 또는 IPv4 만 허용(정규화 이후 값). 거부 사유 또는 None."""
    if len(host) > 253:
        return "hostname 이 너무 김"
    if re.fullmatch(r"[0-9.]+", host):  # 숫자뿐이면 올바른 IPv4 여야 한다
        if not _IPV4.fullmatch(host):
            return "hostname/IPv4 형식이 아님"
        first, second = (int(x) for x in host.split(".")[:2])
        if host == "0.0.0.0" or first == 127 or (first, second) == (169, 254):
            return "특수 주소(unspecified·loopback·link-local 메타데이터)"
        return None
    if not _HOSTNAME.fullmatch(host):
        return "hostname/IPv4 형식이 아님"
    if host == "localhost" or host.endswith(".localhost"):
        return "특수 주소(localhost)"
    last = host.rsplit(".", 1)[-1]
    if last.isdigit() or last.startswith("0x"):
        return "숫자·16진 표기 주소로 해석될 수 있는 hostname"
    return None


def _subject(v: object) -> str:
    """Skipped.subject 용: redact → 비출력 문자 제거 → 절단."""
    s = redact_text(str(v))
    return "".join(c if c.isprintable() else " " for c in s)[:200]


def _under(p: str, base: str) -> bool:
    return p == base or p.startswith(base.rstrip("/") + "/")


def _under_any(p: str, bases: Iterable[str]) -> bool:
    return any(_under(p, b) for b in bases)


def _evidence(events: list[AuditEvent]) -> Evidence:
    decisions = [e.data.get("decision") for e in events]
    raws = sorted(
        ((e.seq, e.run_id, e.data["raw"]) for e in events if e.data.get("raw") is not None),
        key=lambda t: (t[0], t[1]),
    )
    is_net = events[0].kind == "net"
    return Evidence(
        count=len(events),
        allowed=decisions.count("allowed"),
        denied=decisions.count("denied"),
        # file 이벤트에는 decision 이 없어 전부 observed 로 센다
        observed=decisions.count("observed") if is_net else len(events),
        first_seq=min(e.seq for e in events),
        run_ids=tuple(sorted({e.run_id for e in events})),
        sources=tuple(sorted({e.source for e in events})),
        sample_raw=raws[0][2] if raws else None,
    )


def _clean_path(path: str | None) -> str | None:
    if path is None:
        return None
    path = re.split(r"[?#]", path, maxsplit=1)[0]
    return path or "/"


def _base_key(host: str, port: int) -> str:
    base = re.sub(r"[^a-z0-9]+", "_", host).strip("_") or "host"
    return f"{base}_{port}"


def _rule_of(e: AuditEvent) -> tuple[str, str | None]:
    return _upper_ascii(e.data["method"]), _clean_path(e.data["path"])


def _l7_kind(e: AuditEvent) -> str:
    """l7(method·path 둘 다) | half(하나만) | none(둘 다 없음)."""
    has_m = bool(e.data.get("method"))
    has_p = e.data.get("path") is not None
    return "l7" if has_m and has_p else ("half" if has_m or has_p else "none")


def _writable_locations(extra: Iterable[str]) -> tuple[str, ...]:
    return (*baseline.READ_WRITE, *baseline.WRITE_PROPOSAL_ROOTS, *extra)


def _net_entries(
    groups: dict[tuple[str, int], list[AuditEvent]],
    skipped: list[Skipped],
    writable: tuple[str, ...],
) -> list[NetworkEntry]:
    # (host, port, protocol, rules, binaries, evidence)
    raw_entries: list[tuple[str, int, str, tuple, tuple, Evidence]] = []
    for (host, port), evs in groups.items():
        subject = _subject(f"{host}:{port}")
        if host in baseline.GATEWAY_HOSTS:
            skipped.append(Skipped(subject, "D1: 게이트웨이가 가로채는 추론 경로 — 정책에 적지 않음"))
            continue
        bad = _unsafe(host)
        if not bad:
            bad = _host_bad(host)
        if bad:
            skipped.append(Skipped(subject, f"host 거부({bad}) — 제안하지 않음(fail-closed)"))
            continue
        # binary 별로 근거를 나눈다: 유효한 binary 를 가진 이벤트만 rule·evidence 의 근거가 되고,
        # 한 binary 의 rule 이 다른 binary 에 붙지 않는다(교차곱 방지, W1)
        by_bin: dict[str, list[AuditEvent]] = {}
        bin_bad: dict[str, str | None] = {}
        n_anon = 0
        for e in evs:
            b = e.data.get("binary")
            if not b:
                n_anon += 1
                continue
            if b not in bin_bad:
                bin_bad[b] = _unsafe(b, absolute=True)
                if not bin_bad[b] and b == "/":
                    bin_bad[b] = "루트 경로"
                elif not bin_bad[b] and _under_any(b, writable):
                    bin_bad[b] = "쓰기 가능한 위치의 실행 파일"
                if bin_bad[b]:
                    skipped.append(
                        Skipped(
                            f"{subject} binary {_subject(b)}",
                            f"binary 거부({bin_bad[b]}) — fail-closed",
                        )
                    )
            if not bin_bad[b]:
                by_bin.setdefault(b, []).append(e)
        if n_anon:
            skipped.append(
                Skipped(
                    f"{subject} binary 없는 이벤트 {n_anon}건",
                    "허용 주체를 특정할 수 없어 근거에서 제외(fail-closed)",
                )
            )
        if not by_bin:
            skipped.append(Skipped(subject, "유효한 binary 없음 — 제안하지 않음(fail-closed)"))
            continue
        l7_seen = any(_l7_kind(e) == "l7" for b_evs in by_bin.values() for e in b_evs)
        # (protocol, rules) -> [(binary, adopted events)]
        buckets: dict[tuple[str, tuple], list[tuple[str, list[AuditEvent]]]] = {}
        for b, b_evs in by_bin.items():
            sub = f"{subject} binary {_subject(b)}"
            kinds = [_l7_kind(e) for e in b_evs]
            n_half = kinds.count("half")
            if n_half:
                skipped.append(
                    Skipped(sub, f"method/path 중 하나만 있는 이벤트 {n_half}건 — 제외(fail-closed)")
                )
            l7 = [e for e, k in zip(b_evs, kinds, strict=True) if k == "l7"]
            if l7:
                good = set()
                for m, p in {_rule_of(e) for e in l7}:
                    bad = None if m in _HTTP_METHODS else "HTTP 메서드가 아님"
                    bad = bad or _unsafe(p, absolute=True)
                    if bad:
                        subj = f"{sub} {_subject(m)} {_subject(p)}"
                        skipped.append(Skipped(subj, f"rule 거부({bad})"))
                    else:
                        good.add((m, p))
                if not good:  # tcp 로 낮추면 오히려 더 넓어진다
                    skipped.append(Skipped(sub, "유효한 L7 rule 없음 — 제안하지 않음(fail-closed)"))
                    continue
                adopted = [e for e in l7 if _rule_of(e) in good]
                buckets.setdefault(("rest", tuple(sorted(good))), []).append((b, adopted))
            elif l7_seen:
                skipped.append(
                    Skipped(sub, "L7 가 관찰된 엔드포인트에서 L7 정보 없는 binary — 제외(fail-closed)")
                )
            else:
                none = [e for e, k in zip(b_evs, kinds, strict=True) if k == "none"]
                if none:
                    buckets.setdefault(("tcp", ()), []).append((b, none))
        for (protocol, rules), members in buckets.items():
            binaries = tuple(sorted(b for b, _ in members))
            adopted = [e for _, b_evs in members for e in b_evs]  # B7: 채택된 이벤트의 binary 만
            raw_entries.append((host, port, protocol, rules, binaries, _evidence(adopted)))
    per_hp: dict[tuple[str, int], int] = {}
    for host, port, *_ in raw_entries:
        per_hp[(host, port)] = per_hp.get((host, port), 0) + 1

    def ident(host, port, protocol, rules, binaries) -> str:
        if per_hp[(host, port)] == 1:
            return f"{host}:{port}"
        return f"{host}:{port}|{protocol}|{rules}|{binaries}"

    by_key: dict[str, set[str]] = {}
    for host, port, protocol, rules, binaries, _ in raw_entries:
        k = _base_key(host, port)
        by_key.setdefault(k, set()).add(ident(host, port, protocol, rules, binaries))
    out = []
    for host, port, protocol, rules, binaries, ev in raw_entries:
        key = _base_key(host, port)
        if len(by_key[key]) > 1:
            h = hashlib.sha256(ident(host, port, protocol, rules, binaries).encode()).hexdigest()
            key = key + "_" + h[:8]
        out.append(
            NetworkEntry(key, key, host, port, protocol, rules, binaries, ev)
        )
    return sorted(out, key=lambda n: n.key)


def _fs_entries(groups: dict[str, list[AuditEvent]], skipped: list[Skipped]) -> list[FsEntry]:
    out = []
    covered_ro = baseline.READ_ONLY + baseline.READ_WRITE
    for path, evs in groups.items():
        bad = _unsafe(path, absolute=True)
        if bad:
            skipped.append(Skipped(_subject(path), f"경로 거부({bad}) — 제안하지 않음(fail-closed)"))
            continue
        if path == "/":
            skipped.append(Skipped("/", "루트 전체는 제안하지 않음(fail-closed)"))
            continue
        write = any(e.data["mode"] == "write" for e in evs)
        if _under_any(path, baseline.READ_WRITE if write else covered_ro):
            continue
        # 허용 목록: 명시한 루트 아래에서만 제안한다(B6). 나머지는 사람이 판단.
        if write:
            if not _under_any(path, baseline.WRITE_PROPOSAL_ROOTS):
                skipped.append(Skipped(_subject(path), "쓰기 허용 루트 밖 — 사람이 판단"))
                continue
            # 이중 방어: 허용 루트가 잘못 넓어져도 읽기 전용 베이스라인은 쓰지 못한다
            if any(_under(path, b) or _under(b, path) for b in baseline.NEVER_WRITE):
                skipped.append(Skipped(_subject(path), "읽기 전용 베이스라인 경로에 쓰기 제안 금지"))
                continue
        elif not _under_any(path, baseline.READ_PROPOSAL_ROOTS):
            skipped.append(Skipped(_subject(path), "읽기 허용 루트 밖 — 사람이 판단"))
            continue
        out.append(FsEntry(path, "read_write" if write else "read_only", _evidence(evs)))
    return sorted(out, key=lambda f: (f.access, f.path))


def propose(events: Iterable[AuditEvent]) -> PolicyDraft:
    net: dict[tuple[str, int], list[AuditEvent]] = {}
    fs: dict[str, list[AuditEvent]] = {}
    count = 0
    for e in events:
        if not isinstance(e, AuditEvent):
            raise TypeError(f"AuditEvent 가 아니다: {type(e).__name__}")
        # 메모리 객체도 외부 입력처럼 재검증한다. 실패는 AuditFormatError 로 올린다(한 줄이
        # 나빠도 전체 실패 — 조용히 버리면 근거가 사라진 채 초안이 나온다). 몇 번째인지 붙인다.
        try:
            e = AuditEvent.from_json(e.to_json())
        except AuditFormatError as exc:
            raise AuditFormatError(f"이벤트 #{count + 1} 재검증 실패: {exc}") from exc
        except (TypeError, ValueError) as exc:
            raise AuditFormatError(f"이벤트 #{count + 1} 직렬화 실패: {exc}") from exc
        count += 1
        if e.phase != "observe":
            continue  # tool 이벤트는 정책에 반영하지 않는다(집계는 T202-opt)
        if e.kind == "net":
            host = _norm_host(e.data["host"])
            net.setdefault((host, e.data["port"]), []).append(e)
        elif e.kind == "file":
            p = e.data["path"]
            if isinstance(p, str) and p.startswith("/"):
                p = _normpath(p)
            fs.setdefault(p, []).append(e)
    skipped: list[Skipped] = []
    filesystem = _fs_entries(fs, skipped)
    network = _net_entries(
        net, skipped, _writable_locations(f.path for f in filesystem if f.access == "read_write")
    )
    return PolicyDraft(
        network=tuple(network),
        filesystem=tuple(filesystem),
        skipped=tuple(sorted(skipped, key=lambda s: (s.subject, s.reason))),
        event_count=count,
    )


def propose_from_jsonl(path: str | Path) -> PolicyDraft:
    return propose(read_jsonl(path))
