"""T436 — 공개 모드 audit JSONL 회전(D27 ⑦). 최대 2개(현재 + .1), 로컬 모드는 회전 없음."""

import threading

from backend.chat import ChatService, _audit_max_bytes, _TeeSink
from backend.settings import Settings
from core.audit import AuditLog, JsonlSink


def _log(path, max_bytes):
    sink = _TeeSink(JsonlSink(path), path=path, max_bytes=max_bytes) if max_bytes else _TeeSink(
        JsonlSink(path))
    return sink, AuditLog(sink, run_id=path.stem, actor="t")


def _emit(log, n):
    for i in range(n):
        log.observe_file(f"/x/{i}", "read")


def _lines(p):
    return len(p.read_text(encoding="utf-8").splitlines())


def test_rotates_over_limit_keeps_two_files(tmp_path):
    p = tmp_path / "run.jsonl"
    sink, log = _log(p, 400)
    _emit(log, 60)
    one = tmp_path / "run.1.jsonl"
    assert p.exists() and one.exists()
    assert sorted(x.name for x in tmp_path.iterdir()) == ["run.1.jsonl", "run.jsonl"]
    assert p.stat().st_size <= 400 + 300  # 한 줄 정도 넘을 수 있다
    assert one.stat().st_size > 0
    # 메모리 이벤트(세션 응답용)는 회전과 무관하게 유지
    assert sink.mark() == 60 and len(sink.since(0)) == 60


def test_below_limit_does_not_rotate(tmp_path):
    p = tmp_path / "run.jsonl"
    _, log = _log(p, 10**6)
    _emit(log, 5)
    assert not (tmp_path / "run.1.jsonl").exists() and _lines(p) == 5


def test_old_dot_one_is_replaced(tmp_path):
    p = tmp_path / "run.jsonl"
    (tmp_path / "run.1.jsonl").write_text("OLD\n", encoding="utf-8")
    p.write_text("x" * 500 + "\n", encoding="utf-8")
    _, log = _log(p, 100)
    _emit(log, 1)  # 첫 쓰기 전에 회전
    assert "OLD" not in (tmp_path / "run.1.jsonl").read_text(encoding="utf-8")
    assert _lines(p) == 1


def test_no_limit_means_no_rotation(tmp_path):
    p = tmp_path / "run.jsonl"
    _, log = _log(p, None)
    _emit(log, 50)
    assert _lines(p) == 50 and not (tmp_path / "run.1.jsonl").exists()


def test_concurrent_writes_lose_nothing_in_memory_and_stay_bounded(tmp_path):
    p = tmp_path / "run.jsonl"
    sink, log = _log(p, 2000)
    ts = [threading.Thread(target=_emit, args=(log, 40)) for _ in range(4)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert sink.mark() == 160
    assert len(list(tmp_path.glob("*.jsonl"))) <= 2


def test_env_parse(monkeypatch):
    assert _audit_max_bytes({}) == 8 * 1024 * 1024
    assert _audit_max_bytes({"KC_AUDIT_MAX_BYTES": "123"}) == 123
    assert _audit_max_bytes({"KC_AUDIT_MAX_BYTES": "x"}) == 8 * 1024 * 1024
    assert _audit_max_bytes({"KC_AUDIT_MAX_BYTES": "0"}) == 8 * 1024 * 1024


def _svc(tmp_path, **o):
    tmp_path.mkdir(parents=True, exist_ok=True)
    idx = tmp_path / "idx.db"
    idx.write_bytes(b"x")
    s = Settings(hitl_db=tmp_path / "h.db", audit_dir=tmp_path / "a", output_dir=tmp_path / "o",
                 reviewer_id="human:t", index_db=idx, **o)
    return ChatService(s, env={"NVIDIA_API_KEY": "nvapi-" + "s" * 24})


def test_service_public_rotates_local_does_not(tmp_path, monkeypatch):
    monkeypatch.setenv("KC_AUDIT_MAX_BYTES", "300")
    pub = _svc(tmp_path / "pub", public_mode=True)
    loc = _svc(tmp_path / "loc")
    for svc in (pub, loc):
        _emit(svc._audit, 30)
    assert len(list((tmp_path / "pub" / "a").glob("*.jsonl"))) == 2
    assert len(list((tmp_path / "loc" / "a").glob("*.jsonl"))) == 1
