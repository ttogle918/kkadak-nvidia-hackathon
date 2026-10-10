확인 날짜: 2026-10-10 (T402, D27 ③). 공식 문서·가격 페이지를 `curl` 로 받아 읽었다. gcloud 는 실행하지 않았고 계정·결제 조작도 없다. 아래 값은 모두 그 페이지에서 읽은 것이며, 읽지 못한 값은 `[확인 필요]` 로 남겼다. `→` 로 시작하는 줄과 "산술" 표시는 문서 값으로 내가 계산한 것이다.

# T402 — Cloud Run · Artifact Registry · Secret Manager · Cloud Build

## 1. 출처 (모두 2026-10-10 확인)
| 약호 | URL |
|---|---|
| S1 | https://cloud.google.com/run/docs/configuring/request-timeout |
| S2 | https://cloud.google.com/run/docs/configuring/services/memory-limits |
| S3 | https://cloud.google.com/run/docs/configuring/services/cpu |
| S4 | https://cloud.google.com/run/pricing |
| S5 | https://cloud.google.com/run/docs/configuring/max-instances |
| S6 | https://cloud.google.com/run/docs/configuring/min-instances |
| S7 | https://cloud.google.com/run/docs/configuring/concurrency |
| S8 | https://cloud.google.com/run/docs/configuring/services/secrets |
| S9 | https://cloud.google.com/run/docs/container-contract |
| S10 | https://cloud.google.com/run/quotas |
| S11 | https://cloud.google.com/run/docs/configuring/billing-settings |
| S12 | https://cloud.google.com/run/docs/tips/general |
| S13 | https://cloud.google.com/artifact-registry/pricing |
| S14 | https://cloud.google.com/secret-manager/pricing |
| S15 | https://cloud.google.com/build/pricing |
| S16 | https://cloud.google.com/billing/docs/how-to/budgets |
| S17 | https://cloud.google.com/free/docs/free-cloud-features |
| S18 | https://cloud.google.com/run/docs/quickstarts/deploy-container |
| S19 | https://cloud.google.com/run/docs/triggering/https-request |
| S20 | https://cloud.google.com/load-balancing/docs/https (Cloud Run 문서가 아님 — ⑩ 참고용) |
| S21 | https://cloud.google.com/run/docs/configuring/healthchecks |

## 2. 요청 시간 한도 (S1, S10)
- 기본 **300초(5분)**, 최대 **60분(3600초)**. 한도 표(S10)도 "Maximum time before timeout 60 minutes per request".
- 플래그: `gcloud run services update SERVICE --timeout=TIMEOUT` / `gcloud run deploy --image IMAGE_URL --timeout=TIMEOUT` (S1). 값을 바꾸면 새 리비전이 만들어진다.
- 15분 넘게 잡으면 재시도·재접속에 견디게 설계하라고 권고(S1). 우리 일정 흐름 최대 100초 → **`--timeout=120`(D27 ③ "≥120초") 은 한도 안**이다.
- 언어 프레임워크에도 자체 요청 타임아웃이 있으면 더 짧은 쪽이 적용된다(S1). uvicorn 자체 한도 [확인 필요: 이 문서 범위 밖 — T425 에서 코드로 확인].
- HTTP/1 요청·응답 크기 한도 32 MiB (S10).

## 3. 메모리·CPU 선택지, 파일시스템과 메모리 (S2, S3, S9, S10)
- 기본: **메모리 512 MiB, CPU 1 vCPU** (S2, S3). 최대 메모리 32 GiB, 최대 8 vCPU, 최소 0.08 vCPU(S2, S3).
- 최소 메모리: 1세대 실행 환경 128 MiB, **2세대 512 MiB** (S2).
- CPU별 허용 메모리 (S2, S3):

| vCPU | 메모리 |
|---|---|
| 0.08 | 최대 512 MiB |
| 0.5 | 최대 1 GiB |
| 1 | 최대 4 GiB |
| 2 | 최대 8 GiB |
| 4 | 2~16 GiB |
| 6 | 4~24 GiB |
| 8 | 4~32 GiB |

- 1 vCPU 미만이면 동시성 1, 요청 기반 청구, 1세대 실행 환경이 강제된다(S3). 1 초과 vCPU 는 정수만(S3).
- 플래그: `--memory SIZE`(예 `1Gi`), `--cpu CPU` (S3: `gcloud run services update SERVICE --cpu CPU`, `gcloud run deploy --image IMAGE_URL --cpu CPU`).
- **쓰기 가능한 파일시스템은 메모리를 차지한다** (S9 "File system access"): 컨테이너 파일시스템은 인메모리이고 쓰면 **인스턴스 메모리를 쓴다**. 크기 제한을 지정할 수 없어 다 쓰면 인스턴스가 죽는다. 크기 제한이 있는 전용 인메모리 볼륨으로 피할 수 있다(S9). 한도 표: "Maximum writable, in-memory filesystem, limited by instance memory" 32 GiB(S10). S2 도 메모리 소비 항목에 "Writing files to the file system" 을 든다.
  → 우리의 `/tmp`(hitl·audit·캐시·세션, D27 ⑦)와 색인 복사본이 있다면 **메모리에 합산**해야 한다.
- **이미지 크기는 사용 가능 메모리에 포함되지 않는다** (S2, S12). 이미지에 든 색인 파일은 디스크 읽기 전용 층이므로 메모리를 차지하지 않는다. 단 프로세스가 읽어 올리는 캐시·mmap 페이지는 [확인 필요: 페이지 캐시가 컨테이너 메모리 한도에 잡히는지는 문서에서 찾지 못했다 — T426 실측].
- 메모리 한도를 넘으면 인스턴스가 종료된다(S2).

## 4. 무료 사용량 (S4, S17)
요청 기반 청구(기본, S11) 서비스의 월 무료량 (S4, S17 일치):
| 항목 | 월 무료량 |
|---|---|
| 요청 | 200만 건 |
| vCPU | 180,000 vCPU-초 |
| 메모리 | 360,000 GiB-초 |
| 아웃바운드 | 북미발 1 GiB (S4) / 1 GB (S17 — 표기 차이만 있음) |

- 인스턴스 기반 청구의 무료량은 240,000 vCPU-초·450,000 GiB-초이며 요청 수 무료량은 없다(S4). 우리는 요청 기반을 쓴다.
- 무료량은 **결제 계정 단위로 합산**되고 매월 초기화된다(S4).
- **리전 조건**: S4 는 무료량을 "us-central1 가격 기준"으로 적고, 무료 사용량은 "**Tier 1 가격을 쓰는 지출 기반 할인**으로 적용된다"고 한다. 서울(asia-northeast3)은 **Tier 2** 리전이다(S4 "Regional price tiers": asia-northeast3 는 Tier 2, 도쿄·오사카는 Tier 1).
  → 해석(산술이 아니라 문서 문장의 해석): 무료량이 초 단위가 아니라 **Tier 1 가격 기준 금액**이라면, Tier 2 인 서울에서는 같은 금액이 더 적은 초에 해당한다. 서울이 무료량에 포함되는지는 문서가 "포함된다/안 된다"로 명시하지 않았다. 서울 가격 값은 가격표가 동적 목록이라 텍스트로 읽지 못했다 `[확인 필요: 서울 vCPU-초·GiB-초 단가, 서울에서 무료량이 몇 초에 해당하는지]`.
  → D27 문안 권고: **무료 리전(Tier 1, 예: us-central1 / 도쿄 asia-northeast1 / 오사카 asia-northeast2)을 우선 후보로 하고 지연 증가를 감수**하는 쪽을 기본으로 쓴다. 서울은 위 확인이 끝나기 전에는 "무료 보장" 문구를 쓰지 않는다. (도쿄·오사카가 Tier 1 이라는 사실은 S4; 해당 리전이 실제 무료량 대상인지는 위 해석에 따른다.)
- 산술(us-central1 기준 초 수, 1 vCPU 가정, 요청 기반 청구로 요청을 처리 중인 시간만 셈): vCPU 180,000초 = 50시간. 메모리 360,000 GiB-초 ÷ 1 GiB = 100시간, ÷ 2 GiB = 50시간. 즉 메모리 2 GiB·1 vCPU 면 **월 약 50시간의 "요청 처리 중 인스턴스 시간"** 이 무료다. 동시 요청이 여럿이어도 인스턴스 한 개는 한 번만 센다(S4: 동시성 >1 이면 요청이 CPU·메모리를 공유).
- 시작·종료 시간도 청구에 들어간다(S11: "when they process requests, when they start, and when they shut down").

## 5. 결제 계정 · 예산 알림 (S17, S18, S16, S6)
- **결제 계정 필요**: Cloud Run 빠른 시작이 "Verify that billing is enabled for your Google Cloud project" 를 선행 조건으로 둔다(S18). 결제가 꺼지면 스케일이 멈추고 인스턴스가 종료될 수 있다(S6). **무료 사용량 안이어도 결제 계정 연결(카드 등록)이 필요**하다고 본다 — S18 의 선행 조건으로부터의 추론이며, 결제 수단 없이 가능한 예외는 문서에서 찾지 못했다 `[확인 필요: 카드 없는 계정 가능 여부는 H4 에서 사람이 확인]`.
- 신규 가입 무료 체험은 $300 웰컴 크레딧(S17). 체험 기간·조건 세부 `[확인 필요]`.
- **예산 알림은 사용량을 자동으로 막지 않는다** (S16: 예산 알림은 "doesn't automatically cap … usage", 알림만). Cloud Run 문서(S11)에는 "Budget spend caps"(**Preview**, Pre-GA)가 있어 콘솔에서 설정하면 Cloud Run 리소스에 적용된다고 한다. Pre-GA 라 "있는 그대로 제공, 지원 제한" — **의존하지 말고** `max-instances=1` 과 일일 상한(D24)을 1차 방어로 둔다. 예산 설정 위치·절차: 콘솔 결제 > 예산 및 알림 (S16 본문 절차 요약; 정확한 메뉴 이름 [확인 필요: H4 때 화면 확인]).

## 6. 이미지 크기 한도 · Artifact Registry 무료 저장 (S10, S12, S13, S17)
- **배포 가능한 컨테이너 이미지 크기에 직접 한도가 없다** (S10 "There is no direct limit for: The size of container images you can deploy"). 이미지 스트리밍 덕에 이미지 크기는 시작 시간·요청 처리 시간에 영향이 없다고 적혀 있다(S12). 그러나 S12 는 같은 곳에서 작은 이미지를 권장(보안 취약점 면). → **D28 ④ 의 "색인 파일 상한"은 Cloud Run 한도가 아니라 Artifact Registry 무료 저장 0.5 GiB 와 빌드·푸시 시간이 실질 상한**이다.
- Artifact Registry 저장: **월 0.5 GiB 까지 무료**, 초과분 $0.000136986 / GiB-시간 (S13, S17 "0.5 GB of storage per month"). 결제 계정 단위 합산(S13).
  → 산술: 초과 단가 × 730시간 ≈ $0.10 / GiB-월. 이미지 1 GiB 라면 초과 0.5 GiB ≈ $0.05/월 수준 `[산술, 확인 필요: 실제 청구는 H4 이후]`.
- 레지스트리가 Cloud Run 과 **같은 위치**이면 전송비 무료, 같은 대륙 내 리전↔멀티리전도 무료, 아시아 내 다른 리전 간은 $0.05/GiB (S13). → 이미지 저장소 리전은 서비스 리전과 같게.
- 이미지 형식: Docker Image Manifest V2 / OCI, Linux x86_64(S9). Apple Silicon 에서 만든 arm64 이미지는 그대로 못 쓴다 — 멀티 아키텍처 이미지는 별도 규칙(S9 본문) `[확인 필요: T423/T425 가 빌드 플랫폼 지정]`.
- 이미지 취약점 스캔을 켜면 비용이 따로 든다(S13: Vulnerability scanning 은 별도 과금 항목). 켜지 않는다.

## 7. Cloud Build (S15, S17, S4)
- 결제 계정당 **월 2,500 빌드 분 무료** (e2-standard-2, 기본 풀, "promotional … subject to change") (S15, S17). e2-standard-2 단가 $0.006/분(무료량 초과 시). 대기 시간은 빌드 분에 안 들어간다.
- 소스 배포(`--source`)는 Cloud Build + Artifact Registry 를 쓰며 둘의 가격은 Cloud Run 가격에 포함되지 않는다(S4).
- 대안: **호스트에서 `docker build` 후 `docker push`** 로 Cloud Build 를 아예 쓰지 않을 수 있다. 이 경우 Cloud Build 비용은 0, 필요한 것은 Artifact Registry 푸시 권한과 `gcloud auth configure-docker`. [확인 필요: 인증 헬퍼 정확한 명령은 T425 에서 문서로 확인]
- 권고: 무료 분이 충분하지만 "변경될 수 있는 프로모션 한도"이므로 D27 은 로컬 `docker build` + push 를 기본으로 하고 Cloud Build 는 선택으로 둔다. 로컬에 docker 가 없으면 Cloud Build 사용.

## 8. Secret Manager (S8, S14, S17)
- 무료(월, 결제 계정 단위 합산) : **활성 비밀 버전 6개, 접근 작업 10,000회**, 로테이션 알림 3회 (S14, S17). 초과 시 활성 버전 $0.06/월(S14 예시: $0.000082192/시간), 접근 1만 회당 $0.03.
- **접근 작업 수**: env 주입이면 **인스턴스 시작마다 1회**(시작 전에 값을 가져옴, S8). 인스턴스 1개·콜드 스타트 수회/일 수준이면 10,000회에 한참 못 미친다 `[산술 추정]`.
- **env 주입 플래그**: `gcloud run deploy SERVICE --image IMAGE_URL --update-secrets=ENV_VAR_NAME=SECRET_NAME:VERSION` (S8). 기존 비밀 전부 교체는 `gcloud run services update SERVICE --set-secrets="ENV_VAR_NAME=SECRET_NAME:VERSION"`. `VERSION` 은 `latest` 또는 숫자. 비밀은 **같은 프로젝트**에 있어야 한다(S8 "the secret name in the same project").
  → 우리 경우: `--update-secrets=NVIDIA_API_KEY=<비밀 이름>:latest` 형태. `latest` 는 인스턴스가 시작할 때 해석된다(S8: env 방식은 인스턴스 시작 전에 값을 가져온다). 키를 바꾸면 새 리비전 또는 새 인스턴스가 필요한 점 `[확인 필요: latest 를 기존 인스턴스가 다시 읽는지는 문서에서 "시작 전에 가져옴" 외에 명시를 찾지 못함 — 숫자 버전 고정이 더 명확]`.
- **env 방식은 가져오기 실패 시 인스턴스가 시작되지 않는다**(S8). 볼륨 방식은 읽기 시 실패. 우리는 env 를 쓴다(§0.2).
- 배포 시 Cloud Run 이 서비스 계정의 접근 권한을 검사한다(S8).
- **서비스 계정 권한 이름**: `Secret Manager Secret Accessor` = `roles/secretmanager.secretAccessor` (컨테이너를 실행하는 서비스 계정, S8). 배포하는 사람은 `Cloud Run Admin (roles/run.admin)` 과 `Service Account User (roles/iam.serviceAccountUser)` 가 필요(S8). Cloud Run 개발자 역할은 `roles/run.developer`(S2).
- 비밀 값은 env 변수 길이 32 KB 이하(S10 "Maximum variable length 32 Kb").
- 보안: 값을 `--set-env-vars` 로 평문 주입하지 않는다(규칙 1). 로그·`gcloud run services describe` 출력에 값이 아닌 비밀 **참조**만 나온다고 본다 `[확인 필요: describe 출력 확인은 T426]`.

## 9. max-instances · min-instances · concurrency (S5, S6, S7, S10)
| 항목 | 값 | 플래그 |
|---|---|---|
| max-instances 기본 | 리비전당 **100** (S5) | `gcloud run services update SERVICE --max-instances MAX-VALUE` (S5 명령 줄 219, 서비스 수준) / `gcloud run deploy --image IMAGE_URL --max MAX-VALUE` (S5 줄 124) |
| min-instances 기본 | **0** (S6) | `gcloud run services update SERVICE --min-instances MIN-VALUE` / `gcloud run deploy --image IMAGE_URL --min-instances MIN-VALUE` (S6; 짧은 형 `--min`) |
| concurrency 기본 | **80** (S7) | `--concurrency CONCURRENCY`, 기본 복귀 `--concurrency default` (S7) |
| concurrency 최대 | **1000** (S10 "Services … 1,000 per instance") | |

- S5: 최대 인스턴스 설정은 "트래픽 급증 등으로 **잠깐 초과될 수 있다**". 서비스 수준 최대를 권장(S5). → `max-instances=1` 이어도 짧은 시간 2개가 뜰 수 있어 D24 의 메모리 세션·제한이 그 순간 어긋날 수 있다. 문서가 말하는 예외를 D27 에 "알려진 한계"로 적는다.
- min-instances=0 이면 유휴 시 요금이 없다(요청 기반 청구, S6). min ≥ 1 이면 요청 기반 청구에서도 낮은 유휴 단가가 계속 든다(S6, S4 "Idle time (Min instance)" 행. 단가는 리전별 [확인 필요]). **D27 ⑧ 대로 쓰지 않는다.**
- 결제가 꺼져 있으면 min-instances 가 무시된다(S6).
- 동시성: 우리는 일정 흐름 동시 2건·전체 단일 프로세스(D24). Cloud Run `--concurrency` 를 낮춰 요청 자체를 제한하는 것은 다른 방어선이다. 값은 T409 의 동시성 한도와 맞춘다(제안: 기본 80 은 너무 높다 — T409 결정 후 정함 `[확인 필요: 값 선정은 T409]`). 1 vCPU 미만이면 concurrency 1 로 강제(S3).

## 10. `X-Forwarded-For` (D24 ④)
- **Cloud Run 공식 문서(S1~S12, S18, S19)에서 `X-Forwarded-For` 처리 방식을 찾지 못했다.** S19 는 `X-Forwarded-Proto` 만 언급한다. → `[확인 필요: Cloud Run 이 XFF 에 무엇을 몇 개 붙이는지 — 문서 미확인, T426 실측으로만 결정]`.
- 참고(Cloud Run 문서가 **아님**, S20 외부 애플리케이션 부하 분산기): 프록시가 `X-Forwarded-For: [<기존값>,]<클라이언트 IP>,<LB IP>` 로 붙이고, **앞부분의 기존값은 검증하지 않는다**(S20 "does not verify any IP addresses that precede …"). 즉 클라이언트가 보낸 XFF 값은 그대로 앞에 남는다. 이 원리가 Cloud Run 에 그대로 적용되는지는 확인 못 했다.
- 권고(D24 ④ 와 일치): 오른쪽에서 `KC_TRUSTED_PROXY_HOPS` 번째를 읽는 규칙은 **왼쪽 값을 신뢰하지 않으므로 안전한 방향**이다. 값은 문서가 아니라 T426 에서 실제 요청으로 측정한다(직접 호출 vs Netlify 프록시 경유 각각). 기본값을 문서 근거 없이 정하지 말 것 — 읽지 못하면 연결 주소로 폴백하는 현재 설계를 유지.
- 직접 연결 IP 는 Cloud Run 앞단 프록시 주소이므로 폴백 상태에서는 **모든 방문자가 같은 IP 로 보여 IP 별 제한이 전체 제한으로 변한다**(추론). 폴백이 실제 동작으로 나타나면 T426 에서 점검.

## 11. 콜드 스타트 · 시작 프로브 · `PORT` (S9, S21, S3)
- **`PORT` 환경변수**가 주입되고(기본 8080, S9), 컨테이너는 **`0.0.0.0` 에서 그 포트**로 요청을 받아야 한다(S9). 127.0.0.1 만 열면 실패한다. TLS 는 Cloud Run 이 종단, 컨테이너가 직접 구현하지 않는다(S9).
- 시작 제한: 인스턴스는 시작 후 **4분 안에** 포트를 열고 건강해야 한다(S9, S10 "Startup timeout 4 minutes"). 시작 중에는 CPU 가 할당된다(S9).
- 요청 대기: 인스턴스가 없을 때 요청은 평균 시작 시간의 3.5배 또는 10초 중 큰 값까지 대기(S9).
- 시작 CPU 부스트: `--cpu-boost` / `--no-cpu-boost` (S3). 시작 시 CPU 를 일시 증가시켜 콜드 스타트를 줄인다. 이득/비용 [확인 필요: 부스트 값 표는 S3 에 있으나 본 문서에서 읽지 않음].
- 시작 프로브: 기본 initialDelay 0초, period 10초, failureThreshold 3, timeout 1초(S21). `--startup-probe tcpSocket.port=…,initialDelaySeconds=…,failureThreshold=…,timeoutSeconds=…,periodSeconds=…` (S21). 우리는 색인이 큰 이미지에서 읽기가 늦으면 HTTP 프로브(`/health` 등 [확인 필요: 우리 헬스 엔드포인트 이름은 T425 가 코드로 확인])를 쓴다.
- 종료: 인스턴스를 닫기 전 SIGTERM 을 보낸다(S9). 처리 중 일정 흐름이 잘릴 수 있다.
- 컨테이너 파일시스템은 인스턴스가 멈추면 사라진다(S9) → D27 ⑦(휘발) 과 일치.
- 콜드 스타트 실제 시간은 문서 값이 없다 `[확인 필요: T426 실측]`.

## 12. D27 ③ 권장 값 표
| 항목 | 권장 값 | 근거 절 |
|---|---|---|
| `--max-instances` | 1 (잠깐 초과 가능 — 한계로 명시) | §9 (S5) |
| `--min-instances` | 0 (1 이상은 유료·D27 ⑧ 위배) | §9 (S6, S4) |
| `--timeout` | 120 (일정 흐름 최대 100초 + 여유; 한도는 3600) | §2 (S1) |
| 청구 | 요청 기반(기본) — `--cpu-throttling` 기본 유지 | §4 (S11) |
| `--cpu` | 1 (1 미만이면 concurrency 1·1세대 강제) | §3 (S3) |
| `--memory` | T408 2차 실측 최대 RSS × 1.5 + `/tmp` 사용량(메모리에 합산). 상한 1 vCPU 에서 4 GiB | §3 (S2, S3, S9) |
| 무료 범위 환산 | 1 vCPU·2 GiB 면 월 약 50 시간 처리 시간 (us-central1 초 수 기준) | §4 산술 (S4) |
| 리전 | Tier 1 리전 우선(예: us-central1, asia-northeast1). 서울은 무료량 해석 확인 후 | §4 (S4) |
| `--concurrency` | T409 한도와 맞춰 결정(기본 80, 최대 1000) | §9 (S7, S10) |
| 시작 | `PORT`, `0.0.0.0`, 4분 제한; 필요하면 `--cpu-boost`·시작 프로브 | §11 (S9, S3, S21) |
| 비밀 | `--update-secrets=NVIDIA_API_KEY=<이름>:latest`, 서비스 계정에 `roles/secretmanager.secretAccessor` | §8 (S8) |
| 이미지 저장소 | Artifact Registry, 서비스와 같은 리전, 월 0.5 GiB 이하 목표 | §6 (S13) |
| 빌드 | 로컬 `docker build`+push 기본(linux/amd64), Cloud Build 는 선택 | §7 (S15, S9) |
| IP 헤더 | `KC_TRUSTED_PROXY_HOPS` 는 T426 실측으로만 정함 | §10 |

## 13. 유료가 되는 조건 (D27 ⑧ 점검용)
1. 요청 기반 청구 무료량(요청 200만 건·180,000 vCPU-초·360,000 GiB-초/월) 초과 (S4, S17). 서울 등 Tier 2 리전은 무료량이 실질 줄 수 있음(§4).
2. `min-instances` ≥ 1 (유휴 단가 청구, S4·S6), 또는 인스턴스 기반 청구(`--no-cpu-throttling`, S11).
3. `max-instances` 를 올림(S5 기본 100) — 트래픽 급증 시 비용 증가.
4. Artifact Registry 저장 0.5 GiB 초과, 취약점 스캔 켬(S13). 같은 리전 밖으로의 전송(S13).
5. Cloud Build 월 2,500 분 초과 또는 큰 머신 타입(S15).
6. Secret Manager 활성 버전 6개 초과·접근 10,000회 초과(S14). **옛 버전을 비활성 상태로 둬도 "활성"으로 센다**(Enabled·Disabled 모두 활성, S14) — 키를 돌릴 때 이전 버전은 **삭제(destroy)**.
7. 아웃바운드 데이터: 무료는 북미발 월 1 GiB 뿐(S4, S17). 그 밖 리전발 인터넷 송출은 Google Cloud 네트워킹 요금으로 청구된다(S4). 리전별 단가 [확인 필요: 네트워킹 가격 페이지 미확인]. Netlify↔Cloud Run 직접 CORS 면 응답 바이트가 전부 여기에 든다.
8. 결제 계정 없이는 서비스가 동작하지 않는다(§5). 예산 알림은 막지 않는다(S16).
9. 서비스 외에 로그(Cloud Logging) 보존·수집 요금 [확인 필요: 이 문서 범위 밖 — 로그 무료 할당량 미확인].

## 14. `[확인 필요]` 목록
1. 서울(asia-northeast3, Tier 2)에서 무료량이 몇 초에 해당하는지, 서울 단가 (§4).
2. 카드 없는 계정으로 Cloud Run 배포 가능 여부 — H4 에서 사람이 확인 (§5).
3. 무료 체험 $300 의 기간·조건 세부 (§5).
4. 예산 알림 메뉴의 정확한 이름, Budget spend caps(Preview) 사용 여부 (§5).
5. 6. 프로세스 페이지 캐시·mmap 이 컨테이너 메모리 한도에 합산되는지 — T426 실측 (§3).
7. `X-Forwarded-For` 를 Cloud Run 이 어떻게 붙이는지 (Cloud Run 문서에 없음) — T426 에서 직접 호출/프록시 경유 실측 (§10).
8. `latest` 비밀 버전의 갱신 시점 (§8), `describe` 출력에 값이 노출되는지 (§8).
9. 콜드 스타트 실측 시간 (§11), 헬스 엔드포인트 이름 (§11).
10. 이미지 아키텍처(arm64 호스트 시 amd64 빌드), 로컬 docker push 인증 명령 (§6, §7).
11. 로그 비용·무료 할당, 아시아 리전 인터넷 송출 요금 (§13).
12. uvicorn 자체 요청 타임아웃 (§2).
