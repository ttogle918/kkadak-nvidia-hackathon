# Cloud Run 배포 가이드 (D27)

백엔드를 Cloud Run(us-central1)에 올린다. 화면은 Netlify(별도). 근거: `docs/DECISIONS.md` D27·D24·D29, `docs/spikes/cloud_run.md`.
이 문서의 명령은 **사람이 직접** 실행한다. 비밀 값은 이 문서·스크립트·로그·커밋 어디에도 쓰지 않는다(규칙 1).

## 1. 준비 (1회)
```bash
gcloud auth login
gcloud config set project <PROJECT>
gcloud services enable run.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com
gcloud artifacts repositories create kcontext --repository-format=docker --location=us-central1
```
결제 계정 연결과 **예산 알림**(콘솔 결제 > 예산 및 알림)은 사람이 건다. 알림은 사용을 막지 않는다 — 1차 방어는 `max-instances 1`과 일일 상한이다.

## 2. 비밀 등록 (표준입력, 버전 번호 기록)
키를 명령줄 인자나 파일에 쓰지 않는다. 프롬프트에서 붙여 넣고(화면 에코 없음) 파이프로 넘긴다.
```bash
read -rs -p "NVIDIA_API_KEY: " V && echo
printf %s "$V" | gcloud secrets create kc-nvidia-api-key --data-file=-
unset V
read -rs -p "DATA_GO_KR_SERVICE_KEY: " V && echo
printf %s "$V" | gcloud secrets create kc-data-go-kr-service-key --data-file=-
unset V
gcloud secrets versions list kc-nvidia-api-key        # 숫자 버전 확인 → 기록
gcloud secrets versions list kc-data-go-kr-service-key
```
실행 서비스 계정(기본: 컴퓨트 기본 계정)에 `roles/secretmanager.secretAccessor` 를 두 비밀에 준다.
**기록할 것**: 비밀 이름과 *숫자 버전*(값 아님). 비밀 이름 기본값은 스크립트 `--nvidia-secret-name`·`--tourapi-secret-name`.
`describe`·`versions list` 출력에는 값이 없다. `versions access` 는 값을 찍으므로 쓰지 않는다.

## 3. 배포
데이터(색인·25개 구 카탈로그)와 이미지 빌드는 `deploy/cloudrun/README.md`(T423)를 따른다. 먼저 명령만 확인한다.
```bash
bash scripts/deploy_cloudrun.sh --project <PROJECT> --cors-origin https://<운영도메인> \
  --nvidia-secret-version <N> --tourapi-secret-version <M> --dry-run
```
`--dry-run` 은 계정 없이 0 으로 끝나고 실행할 명령만 보인다. 확인 뒤 `--dry-run` 을 빼면 `docker build --platform linux/amd64` → Artifact Registry push → `gcloud run deploy` 를 순서대로 한다. 이미지를 이미 올렸으면 `--skip-build --image <URL>`.

스크립트가 거부하는 것: 버전 인자 누락, `latest`·비숫자 버전, `--cors-origin` 이 https 원점 하나가 아닌 경우(미리보기·쉼표 목록 불가 — D27 ②).

### 설정과 근거
| 항목 | 값 | 근거 |
|---|---|---|
| 리전 | us-central1 (`--region` 으로 변경 가능) | Tier 1 무료량·북미발 송출 월 1GiB (D27 ③). 서울 대비 지연 +0.15~0.2초 |
| 메모리·CPU | 2Gi · 1 | `/tmp`(인메모리)와 자식 프로세스가 합산 (D27 ③⑦) |
| timeout | 120초 | 일정 흐름 최대 약 100초 |
| max/min instances | 1 / 0 | 제한·상한이 메모리 기반이라 인스턴스 하나가 전제 (D27 ③, 요청 기반 청구) |
| concurrency | 20 | 앱 동시성 상한이 일정 2·카탈로그 2라 그 이상은 대기만 늘린다. T426 에서 확인 |
| env | `KC_PUBLIC_MODE=1` `KC_TARGET_REGION=all` `KC_CATALOG_CONCURRENCY=2` `KC_CORS_ORIGINS` `KC_LLM_DAILY_UNITS`(기본 300, H7) `KC_TOURAPI_DAILY_CALLS=300` | D24·D29 |
| `KC_TRUSTED_PROXY_HOPS` | **넣지 않음** | IP 제한 꺼진 채 시작. T426 에서 요청 로그 `remoteIp` 와 XFF 항목 위치를 실측한 뒤 `gcloud run services update <SERVICE> --update-env-vars KC_TRUSTED_PROXY_HOPS=<1~3>` (D24 ④) |
| 비밀 | `--update-secrets NVIDIA_API_KEY=<이름>:<숫자>,DATA_GO_KR_SERVICE_KEY=<이름>:<숫자>` | 숫자 고정 (D27 ⑥). 이미지·빌드 컨텍스트엔 비밀 없음 |

`--allow-unauthenticated`: 브라우저가 직접 부르는 공개 API 이므로 켠다. 남용 방어는 앱의 세션·요청·일일 상한(D24)이 맡는다.

## 4. 비밀 교체 절차
1. 새 버전 추가(표준입력): `read -rs V; printf %s "$V" | gcloud secrets versions add <이름> --data-file=-; unset V`
2. 새 숫자 버전으로 재배포: 스크립트를 새 `--*-secret-version` 으로 다시 실행(`--skip-build --image <현재 이미지>` 가능, hops 를 정했으면 `--trusted-proxy-hops` 도 — 5절)
3. 확인: 새 리비전의 `/api/meta` 응답, `gcloud run services describe <SERVICE>` 에 새 버전 번호(값 없음)
4. 옛 버전 삭제: `gcloud secrets versions destroy <옛 번호> --secret=<이름>`

Secret Manager 무료 한도는 **활성 버전 6개**이고 비활성(disabled)도 활성으로 센다. 그래서 disable 이 아니라 destroy 한다.

## 5. 점검과 한계
- **송출량**: 북미발 월 1GiB 가 무료다. 콘솔(Cloud Run > 지표/결제 보고서)에서 월 송출을 가끔 본다. 응답은 gzip. 넘으면 과금되니 예산 알림을 본다.
- **max-instances 초과**: 트래픽 급증 때 인스턴스가 잠깐 둘이 될 수 있다(D27 ⑧). 그동안 세션·요청 제한·일일 상한이 인스턴스마다 따로 세어지고(최대 2배), 새 탭이 다른 인스턴스로 가면 대화가 안 보일 수 있다. 데모 범위에서 감수한다.
- **재시작 초기화**: 일일 상한·세션·`/tmp` 상태는 재시작하면 0 이다. 실제 비용 상한은 NVIDIA 크레딧이다.
- **IP 제한**은 hops 설정 전까지 꺼져 있다. T426 에서 hops 를 정한 뒤에는 **재배포할 때마다** `--trusted-proxy-hops N` 을 함께 준다 — 배포 스크립트는 `--set-env-vars` 로 env 를 통째로 바꾸므로 빠뜨리면 IP 제한이 조용히 꺼진다(스크립트가 알림을 낸다).

## 6. 이미지 데이터 갱신 절차
색인·카탈로그·좌표 사전은 이미지에 들어 있다(런타임 수집 없음, D7). 갱신하려면 호스트에서 데이터를 다시 만들고(`scripts/build_image_data.sh`, T423 — 서울 API 유래만) 이미지를 다시 빌드·push 한 뒤 3절 스크립트로 재배포한다(비밀 버전은 현재 값 그대로, hops 를 정했으면 `--trusted-proxy-hops` 도). 이미지 전체 크기는 Artifact Registry 무료 0.5GiB 안이어야 한다(D27 ⑨, D28 ④).
