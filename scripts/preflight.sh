#!/bin/sh
# 대회 전 점검 — 이 머신이 NVIDIA 스택을 돌릴 준비가 됐는지 확인한다 (읽기 전용).
# 두 사람 노트북에서 각각 한 번씩 돌린다:  scripts/preflight.sh [--live]
#
# - 기본은 네트워크 호출을 하지 않는다. 키는 "설정됨/없음"만 보고하고 값은 절대 출력하지 않는다.
# - --live: build.nvidia.com 에 키마다 최소 채팅 호출(max_tokens=1, 토큰 1개 분량)을 한 번 보내 키가 유효한지 확인한다.
#   /v1/models 는 인증 없이도 200 이라 키 검증에 쓸 수 없다(가짜 키로 200 이 나오는 것을 실측, 채팅 호출은 401).
#   키는 원래 목적지인 NVIDIA 로만 간다. 응답 본문은 출력하지 않고 HTTP 코드만 본다. 모델은 PREFLIGHT_MODEL 로 바꾼다.
# - 종료 코드: 필수(FAIL)가 하나라도 있으면 1. WARN 은 종료 코드에 영향이 없다.
# - 아무것도 만들거나 바꾸지 않는다(샌드박스·provider·파일 생성 없음).
#   단 openshell·brev 하위 명령(gateway info·provider list·sandbox list·brev ls)이 상태를 바꾸지 않는다는 점은
#   문서로 확인하지 못했다(규칙 4, nemoclaw-docs searchDocs 로 확인 필요). 조회용 명령만 쓰고 출력은 첫·마지막 열만 쓴다.
#
# 필수 키: NVIDIA_API_KEY. 선택: NVIDIA_API_KEY_A/_B(기능별 키, D5), NGC_API_KEY, BREV 로그인.
set -u
LIVE=0
MODEL="${PREFLIGHT_MODEL:-nvidia/nemotron-3-super-120b-a12b}"
[ "${1:-}" = "--live" ] && LIVE=1
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FAILS=0
WARNS=0

pass() { printf '  [PASS] %-22s %s\n' "$1" "$2"; }
warn() { printf '  [WARN] %-22s %s\n' "$1" "$2"; WARNS=$((WARNS + 1)); }
fail() { printf '  [FAIL] %-22s %s\n' "$1" "$2"; FAILS=$((FAILS + 1)); }

have() { command -v "$1" >/dev/null 2>&1; }
ver() { "$@" 2>&1 | head -1; }

# 키가 셸 env 에 있거나 .env 에 비어 있지 않게 적혀 있으면 설정된 것으로 본다. 값은 읽어도 출력하지 않는다.
key_state() {
  name="$1"
  eval "val=\${$name:-}"
  if [ -n "$val" ]; then echo env; return; fi
  if [ -f "$ROOT/.env" ] && grep -Eq "^[[:space:]]*(export[[:space:]]+)?$name=[^[:space:]#]" "$ROOT/.env"; then
    echo dotenv; return
  fi
  echo none
}

echo "== 도구"
for t in git uv docker node npm; do
  if have "$t"; then pass "$t" "$(ver "$t" --version)"; else fail "$t" "없음"; fi
done
if have python3; then pass python3 "$(ver python3 --version)"; else fail python3 "없음"; fi
if have openshell; then pass openshell "$(ver openshell --version)"; else fail openshell "없음 (게이트웨이·샌드박스 불가)"; fi
if have nemoclaw; then pass nemoclaw "$(ver nemoclaw --version)"; else fail nemoclaw "없음"; fi
if have brev; then pass brev "$(ver brev --version)"; else warn brev "CLI 없음 — Brev 인스턴스를 쓰려면 설치·로그인 필요"; fi
if have gh; then pass gh "$(ver gh --version)"; else warn gh "없음 — 레포 클론·푸시에 필요"; fi

echo "== Docker · GPU · 자원"
if have docker && docker info >/dev/null 2>&1; then pass docker-daemon "응답함"; else fail docker-daemon "데몬 응답 없음"; fi
if have nvidia-smi && nvidia-smi >/dev/null 2>&1; then
  pass gpu "$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | head -1)"
else
  warn gpu "GPU 없음 — 로컬 Nemotron 불가, API 백엔드(LLM_BACKEND=api)로 간다"
fi
mem_gb=$(awk '/MemTotal/ {printf "%d", $2/1024/1024}' /proc/meminfo 2>/dev/null || echo 0)
disk_gb=$(df -Pk "$ROOT" | awk 'NR==2 {printf "%d", $4/1024/1024}')
[ "${mem_gb:-0}" -ge 8 ] && pass memory "${mem_gb}GB" || warn memory "${mem_gb}GB (8GB 미만)"
[ "${disk_gb:-0}" -ge 20 ] && pass disk-free "${disk_gb}GB" || warn disk-free "${disk_gb}GB (20GB 미만)"

echo "== OpenShell 게이트웨이"
if have openshell; then
  if timeout 20 openshell gateway info 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | grep -qi 'healthy'; then
    pass gateway "healthy"
  else
    fail gateway "healthy 아님 (openshell gateway info 확인)"
  fi
  prov=$(timeout 20 openshell provider list 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | awk 'NR>1 && NF {print $1}' | tr '\n' ' ')
  if [ -n "$prov" ]; then pass providers "$prov"; else warn providers "없음 — scripts/gateway_setup.sh 필요"; fi
  sb=$(timeout 20 openshell sandbox list 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | awk 'NR>1 && NF {printf "%s(%s) ", $1, $NF}')
  [ -n "$sb" ] && pass sandboxes "$sb(다른 프로젝트 것은 건드리지 않는다)" || pass sandboxes "없음"
fi

echo "== 키 (값은 출력하지 않는다)"
case "$(key_state NVIDIA_API_KEY)" in
  env) pass NVIDIA_API_KEY "셸 env 에 설정됨" ;;
  dotenv) warn NVIDIA_API_KEY ".env 에만 있음 — 셸에 export 해야 게이트웨이 등록에 읽힌다" ;;
  *) fail NVIDIA_API_KEY "없음 (build.nvidia.com 에서 발급)" ;;
esac
for k in NVIDIA_API_KEY_A NVIDIA_API_KEY_B; do
  case "$(key_state $k)" in
    env|dotenv) pass "$k" "설정됨($(key_state $k))" ;;
    *) warn "$k" "없음 — 기능별 키(D5)를 쓸 때만 필요" ;;
  esac
done
case "$(key_state NGC_API_KEY)" in
  env|dotenv) pass NGC_API_KEY "설정됨" ;;
  *) warn NGC_API_KEY "없음 — NIM 컨테이너·NGC 카탈로그를 쓸 때 필요" ;;
esac
[ -f "$ROOT/.env" ] && pass ".env" "있음(gitignore 대상)" || warn ".env" "없음 (.env.example 참고)"

echo "== Git · GitHub · Brev 로그인"
if [ -d "$ROOT/.git" ]; then
  remote=$(git -C "$ROOT" remote -v | awk 'NR==1 {print $1}')
  [ -n "$remote" ] && pass git-remote "$remote" || warn git-remote "원격 없음 — 새 인스턴스에서 clone 불가"
  dirty=$(git -C "$ROOT" status --short | grep -vc '^?? frontend/' || true)
  [ "$dirty" = "0" ] && pass git-clean "깨끗함(frontend/ 제외)" || warn git-clean "커밋 안 된 변경 ${dirty}건"
fi
if have gh; then
  gh auth status >/dev/null 2>&1 && pass gh-auth "로그인됨" || warn gh-auth "로그인 안 됨 (gh auth login)"
fi
if have brev; then
  if timeout 20 brev ls </dev/null >/dev/null 2>&1; then pass brev-login "로그인됨"; else warn brev-login "로그인 안 됨 (brev login)"; fi
fi

if [ "$LIVE" = "1" ]; then
  echo "== 라이브 키 검증 (--live)"
  if ! have curl; then
    warn curl "없음 — 라이브 검증 건너뜀"
  else
    for k in NVIDIA_API_KEY NVIDIA_API_KEY_A NVIDIA_API_KEY_B; do
      eval "val=\${$k:-}"
      if [ -z "$val" ]; then
        [ "$(key_state $k)" = "dotenv" ] && warn "$k" "셸 env 에 없고 .env 에만 있어 라이브 검증 건너뜀 (export 후 재실행)"
        continue
      fi
      # 키를 curl 인자(-H)로 넘기면 ps·/proc/<pid>/cmdline 에 보인다 → printf(셸 내장)로 stdin 설정(-K -)에 넘긴다.
      code=$(printf 'header = "Authorization: Bearer %s"\n' "$val" | curl -s -o /dev/null \
        -w '%{http_code}' --max-time 30 -X POST -K - \
        https://integrate.api.nvidia.com/v1/chat/completions \
        -H 'Content-Type: application/json' \
        -d "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],\"max_tokens\":1}" \
        2>/dev/null) || code=000
      case "$code" in
        200) pass "$k" "인증된 호출 성공(HTTP 200, 모델 $MODEL)" ;;
        401|403) fail "$k" "거부됨(HTTP $code) — 키가 틀렸거나 만료" ;;
        404) warn "$k" "HTTP 404 — 모델 이름 확인 필요(PREFLIGHT_MODEL), 키는 판정 불가" ;;
        429) warn "$k" "HTTP 429 — 키는 유효하나 한도 초과" ;;
        000) warn "$k" "연결 실패 — 네트워크 확인" ;;
        *) warn "$k" "HTTP $code" ;;
      esac
    done
  fi
fi

echo
echo "FAIL $FAILS · WARN $WARNS"
[ "$FAILS" -eq 0 ]
