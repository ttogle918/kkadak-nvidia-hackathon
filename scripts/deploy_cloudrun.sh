#!/usr/bin/env bash
# K-Context 백엔드 Cloud Run 배포 (D27) — 빌드(linux/amd64) → Artifact Registry push → gcloud run deploy.
#
#   bash scripts/deploy_cloudrun.sh --project P --cors-origin https://운영도메인 \
#        --nvidia-secret-version 1 --tourapi-secret-version 1 [--dry-run]
#
# - --dry-run 은 gcloud·docker 를 부르지 않고(계정 불필요) 실행할 명령만 출력하고 0 으로 끝난다.
# - 비밀 값은 다루지 않는다. 이름:숫자 버전 참조만 넘긴다. 버전은 숫자만 허용, latest 거부 (D27 ⑥).
# - KC_TRUSTED_PROXY_HOPS 는 첫 배포에 넣지 않는다 (IP 제한 꺼진 채 시작, D24 ④). T426 실측 뒤에는 재배포할 때마다
#   --trusted-proxy-hops N 을 함께 준다 — 이 스크립트는 --set-env-vars 로 env 를 통째로 바꾸므로 빠뜨리면 IP 제한이 꺼진다.
# - 빌드 컨텍스트는 레포 루트 Dockerfile (T423, deploy/cloudrun/README.md 와 맞출 것).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

PROJECT=""
REGION="us-central1"
SERVICE="kcontext-api"
REPO="kcontext"
TAG="release"
IMAGE=""
CORS_ORIGIN=""
NVIDIA_SECRET="kc-nvidia-api-key"
TOURAPI_SECRET="kc-data-go-kr-service-key"
NVIDIA_VER=""
TOURAPI_VER=""
LLM_UNITS="300"
HOPS=""
SKIP_BUILD=0
DRY_RUN=0

die() { echo "오류: $*" >&2; exit 2; }
usage() { sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; }

need_val() { [ $# -ge 2 ] && [ -n "${2:-}" ] || die "$1 에 값이 필요합니다"; }

while [ $# -gt 0 ]; do
  case "$1" in
    --project) need_val "$@"; PROJECT="$2"; shift 2 ;;
    --region) need_val "$@"; REGION="$2"; shift 2 ;;
    --service) need_val "$@"; SERVICE="$2"; shift 2 ;;
    --repo) need_val "$@"; REPO="$2"; shift 2 ;;
    --tag) need_val "$@"; TAG="$2"; shift 2 ;;
    --image) need_val "$@"; IMAGE="$2"; shift 2 ;;
    --cors-origin) need_val "$@"; CORS_ORIGIN="$2"; shift 2 ;;
    --nvidia-secret-name) need_val "$@"; NVIDIA_SECRET="$2"; shift 2 ;;
    --tourapi-secret-name) need_val "$@"; TOURAPI_SECRET="$2"; shift 2 ;;
    --nvidia-secret-version) need_val "$@"; NVIDIA_VER="$2"; shift 2 ;;
    --tourapi-secret-version) need_val "$@"; TOURAPI_VER="$2"; shift 2 ;;
    --llm-daily-units) need_val "$@"; LLM_UNITS="$2"; shift 2 ;;
    --trusted-proxy-hops) need_val "$@"; HOPS="$2"; shift 2 ;;
    --skip-build) SKIP_BUILD=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "알 수 없는 인자: $1" ;;
  esac
done

[ -n "$PROJECT" ] || die "--project 필수"
[ -n "$CORS_ORIGIN" ] || die "--cors-origin 필수 (운영 도메인 하나, 예 https://example.netlify.app)"
[ -n "$NVIDIA_VER" ] || die "--nvidia-secret-version 필수 (숫자)"
[ -n "$TOURAPI_VER" ] || die "--tourapi-secret-version 필수 (숫자)"

check_ver() {
  case "$2" in
    latest|LATEST) die "$1: latest 는 거부합니다 — 숫자 버전으로 고정 (D27 ⑥)" ;;
  esac
  [[ "$2" =~ ^[1-9][0-9]*$ ]] || die "$1: 숫자 버전이어야 합니다 (받은 값 형식 오류)"
}
check_ver --nvidia-secret-version "$NVIDIA_VER"
check_ver --tourapi-secret-version "$TOURAPI_VER"

[[ "$PROJECT" =~ ^[a-z][a-z0-9-]{4,28}[a-z0-9]$ ]] || die "--project 형식 오류"
[[ "$REGION" =~ ^[a-z]+-[a-z]+[0-9]+$ ]] || die "--region 형식 오류"
[[ "$SERVICE" =~ ^[a-z][a-z0-9-]{0,48}[a-z0-9]$ ]] || die "--service 형식 오류"
[[ "$NVIDIA_SECRET" =~ ^[A-Za-z0-9_-]+$ ]] || die "--nvidia-secret-name 형식 오류"
[[ "$TOURAPI_SECRET" =~ ^[A-Za-z0-9_-]+$ ]] || die "--tourapi-secret-name 형식 오류"
[[ "$LLM_UNITS" =~ ^[1-9][0-9]*$ ]] || die "--llm-daily-units 는 양의 정수"
[ -z "$HOPS" ] || [[ "$HOPS" =~ ^[1-3]$ ]] || die "--trusted-proxy-hops 는 1~3 (T426 실측값)"
# 운영 도메인 하나만: https 원점, 경로·쉼표·공백 없음 (쉼표는 gcloud env 구분자와도 충돌)
[[ "$CORS_ORIGIN" =~ ^https://[A-Za-z0-9.-]+(:[0-9]+)?$ ]] || die "--cors-origin 은 https://호스트 형태의 원점 하나 (경로·쉼표 불가)"

[ -n "$IMAGE" ] || IMAGE="${REGION}-docker.pkg.dev/${PROJECT}/${REPO}/${SERVICE}:${TAG}"

run() {
  if [ "$DRY_RUN" = 1 ]; then
    printf '+'; printf ' %q' "$@"; printf '\n'
  else
    "$@"
  fi
}

[ "$DRY_RUN" = 1 ] && echo "# dry-run: 아래 명령은 실행되지 않았습니다 (계정·docker 불필요)"

if [ "$SKIP_BUILD" = 0 ]; then
  run docker build --platform linux/amd64 -f "$ROOT/Dockerfile" -t "$IMAGE" "$ROOT"
  run gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet
  run docker push "$IMAGE"
fi

ENV_VARS="KC_PUBLIC_MODE=1,KC_TARGET_REGION=all,KC_CATALOG_CONCURRENCY=2,KC_CORS_ORIGINS=${CORS_ORIGIN},KC_LLM_DAILY_UNITS=${LLM_UNITS},KC_TOURAPI_DAILY_CALLS=300"
[ -z "$HOPS" ] || ENV_VARS="${ENV_VARS},KC_TRUSTED_PROXY_HOPS=${HOPS}"
[ -n "$HOPS" ] || echo "# 알림: KC_TRUSTED_PROXY_HOPS 없음 — IP 제한 꺼짐(D24 ④). T426 실측 뒤에는 --trusted-proxy-hops 를 주세요" >&2
SECRETS="NVIDIA_API_KEY=${NVIDIA_SECRET}:${NVIDIA_VER},DATA_GO_KR_SERVICE_KEY=${TOURAPI_SECRET}:${TOURAPI_VER}"

run gcloud run deploy "$SERVICE" \
  --project "$PROJECT" --region "$REGION" --image "$IMAGE" \
  --memory 2Gi --cpu 1 --timeout 120 --concurrency 20 \
  --max-instances 1 --min-instances 0 \
  --allow-unauthenticated \
  --set-env-vars "$ENV_VARS" \
  --update-secrets "$SECRETS"
