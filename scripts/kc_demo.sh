#!/usr/bin/env bash
# K-Context 데모 실행 — backend(8000) + 정적 화면 서버(8766)를 띄우고, 종료하면 자기가 띄운 것만 정리한다.
#
#   bash scripts/kc_demo.sh                    # 기동 (Ctrl-C 로 종료)
#   bash scripts/kc_demo.sh --check            # 점검만 (uv · 색인 · 키 있음/없음 · 행사 카탈로그)
#   bash scripts/kc_demo.sh --restore-snapshot # 행사 스냅샷(D19)을 var/catalog 로 복원 (대상이 있으면 거부)
#   bash scripts/kc_demo.sh --smoke            # 띄워서 8000·8766 응답만 확인하고 종료 (LLM 호출 없음)
#
# - 키 값은 읽거나 출력하지 않는다. 셸 env 또는 .env 에 "있음/없음"만 본다 (규칙 1).
# - 포트가 이미 쓰이면 안내하고 끝낸다. 다른 프로세스는 죽이지 않는다.
# - 이 스크립트는 LLM 을 부르지 않는다. 일정 문장을 보낼 때만 backend 가 LLM(또는 캐시)을 쓴다.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BACKEND_PORT=8000
STATIC_PORT=8766
INDEX_DB="var/index/kcontext.db"
CATALOG_DIR="var/catalog"
SNAPSHOT_DIR="domains/kcontext/data/snapshots/catalog"
REGIONS="jung,jongno,mapo,gangnam"

MODE="run"
case "${1:-}" in
  "") ;;
  --check) MODE="check" ;;
  --restore-snapshot) MODE="restore" ;;
  --smoke) MODE="smoke" ;;
  -h|--help) sed -n '2,10p' "$0"; exit 0 ;;
  *) echo "알 수 없는 옵션: $1  (--check · --restore-snapshot · --smoke)" >&2; exit 2 ;;
esac

have_uv() { command -v uv >/dev/null 2>&1; }

# 키가 셸 env 에 있거나 .env 에 비어 있지 않게 적혀 있으면 있음. 값은 읽어도 출력하지 않는다.
key_state() {
  if [ -n "${NVIDIA_API_KEY:-}" ]; then echo "셸 env"; return; fi
  if [ -f .env ] && grep -Eq '^[[:space:]]*(export[[:space:]]+)?NVIDIA_API_KEY=[^[:space:]#]' .env; then
    echo ".env"; return
  fi
  echo "없음"
}

port_busy() {
  python3 - "$1" <<'PY'
import socket, sys
s = socket.socket()
s.settimeout(0.5)
busy = s.connect_ex(("127.0.0.1", int(sys.argv[1]))) == 0
s.close()
sys.exit(0 if busy else 1)
PY
}

snapshot_hint() {
  if [ ! -e "$CATALOG_DIR" ] && [ -d "$SNAPSHOT_DIR" ]; then
    echo "  [안내] $CATALOG_DIR 없음 · 스냅샷 있음 — 행사 카드를 보려면: bash scripts/kc_demo.sh --restore-snapshot"
  fi
}

do_check() {
  local rc=0
  if have_uv; then echo "  [OK]   uv: 있음"; else echo "  [FAIL] uv: 없음 — https://docs.astral.sh/uv/ 설치"; rc=1; fi
  if command -v python3 >/dev/null 2>&1; then echo "  [OK]   python3: 있음 (정적 서버용)"; else echo "  [FAIL] python3: 없음"; rc=1; fi
  if [ -f "$INDEX_DB" ]; then
    echo "  [OK]   색인: $INDEX_DB"
  else
    echo "  [FAIL] 색인 없음: $INDEX_DB"
    echo "         만들기: uv run python -m domains.kcontext.ingest.sillok --src <실록 XML 폴더> --db $INDEX_DB --collected-at \$(date +%F)"
    echo "         (README \"환경 설치 방법\" 참고)"
    rc=1
  fi
  local ks; ks="$(key_state)"
  if [ "$ks" = "없음" ]; then
    echo "  [WARN] NVIDIA_API_KEY: 없음 — 새 일정 문장 이해는 안 되고, 캐시된 문장·화면 예시(?api=mock)만 동작"
  else
    echo "  [OK]   NVIDIA_API_KEY: 있음 ($ks)"
  fi
  if [ -d "$CATALOG_DIR" ]; then echo "  [OK]   행사 카탈로그: $CATALOG_DIR"; else echo "  [WARN] 행사 카탈로그 없음: $CATALOG_DIR"; fi
  snapshot_hint
  for p in "$BACKEND_PORT" "$STATIC_PORT"; do
    if port_busy "$p"; then echo "  [WARN] 포트 $p 사용 중 — 기동하려면 먼저 비워야 한다 (이 스크립트는 다른 프로세스를 죽이지 않는다)"; fi
  done
  if [ "$rc" -eq 0 ]; then echo "점검 통과"; else echo "점검 실패 — 위 FAIL 항목을 고친다"; fi
  return "$rc"
}

if [ "$MODE" = "check" ]; then
  do_check
  exit $?
fi

if [ "$MODE" = "restore" ]; then
  have_uv || { echo "uv 가 없다" >&2; exit 1; }
  if [ -e "$CATALOG_DIR" ]; then
    echo "$CATALOG_DIR 가 이미 있다 — 덮어쓰지 않는다. 바꾸려면 직접 치운 뒤 다시 실행하거나 scripts/snapshot_catalog.py --restore --force 를 쓴다." >&2
    exit 1
  fi
  [ -d "$SNAPSHOT_DIR" ] || { echo "스냅샷이 없다: $SNAPSHOT_DIR" >&2; exit 1; }
  uv run python scripts/snapshot_catalog.py --restore --from "$SNAPSHOT_DIR" --to "$CATALOG_DIR"
  exit $?
fi

# ---- 기동 ----
do_check >/dev/null 2>&1 || { do_check; exit 1; }
for p in "$BACKEND_PORT" "$STATIC_PORT"; do
  if port_busy "$p"; then
    echo "포트 $p 가 이미 쓰이고 있다. 쓰던 프로세스를 직접 종료한 뒤 다시 실행한다 (이 스크립트는 죽이지 않는다)." >&2
    exit 1
  fi
done
snapshot_hint

PIDS=()
cleanup() {
  trap - EXIT INT TERM
  local pid
  for pid in "${PIDS[@]:-}"; do
    [ -n "$pid" ] && kill "$pid" 2>/dev/null || true
  done
  for pid in "${PIDS[@]:-}"; do
    [ -n "$pid" ] && wait "$pid" 2>/dev/null || true
  done
}
trap cleanup EXIT INT TERM

KC_TARGET_REGION="$REGIONS" uv run uvicorn backend.app:app --host 127.0.0.1 --port "$BACKEND_PORT" --log-level warning &
PIDS+=("$!")
python3 -m http.server "$STATIC_PORT" --bind 127.0.0.1 --directory frontend/k-context >/dev/null 2>&1 &
PIDS+=("$!")

wait_up() {  # url
  local i
  for i in $(seq 1 60); do
    python3 - "$1" <<'PY' && return 0
import sys, urllib.request
try:
    urllib.request.urlopen(sys.argv[1], timeout=1).read(1)
except Exception:
    sys.exit(1)
PY
    sleep 0.5
  done
  return 1
}

wait_up "http://127.0.0.1:$STATIC_PORT/" || { echo "화면 서버($STATIC_PORT)가 뜨지 않았다" >&2; exit 1; }
wait_up "http://127.0.0.1:$BACKEND_PORT/api/messages" || { echo "backend($BACKEND_PORT)가 뜨지 않았다" >&2; exit 1; }
for pid in "${PIDS[@]}"; do
  kill -0 "$pid" 2>/dev/null || { echo "이 스크립트가 띄운 프로세스($pid)가 이미 끝났다 — 같은 포트를 다른 프로세스가 잡았을 수 있다" >&2; exit 1; }
done
echo "응답 확인: backend $BACKEND_PORT · 화면 $STATIC_PORT"

echo
echo "실제 서버 화면:   http://localhost:$STATIC_PORT/"
echo "예시(MOCK) 화면:  http://localhost:$STATIC_PORT/?api=mock"
echo "여행 기간 지정:   http://localhost:$STATIC_PORT/?trip=2026-10-15..2026-10-18"
echo
echo "데모 팁: 데모 전에 대표 일정 문장을 한 번 보내 캐시를 채워 두면, 같은 문장은 LLM 없이 바로 나온다."

if [ "$MODE" = "smoke" ]; then
  exit 0
fi
echo "종료: Ctrl-C (이 스크립트가 띄운 프로세스만 정리한다)"
wait
