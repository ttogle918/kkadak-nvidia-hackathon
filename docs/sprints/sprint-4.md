# Sprint 4 — 서울 25개 구 확장 + 공개 배포 (확정)

> 상태: **확정 · G1 반영**(pm, 2026-10-10). 초안 `sprint-4.draft.md` 에 dev 현실성 평가를 반영했고(끝의 "dev 평가 반영 내역"), Stage 1 결과와 **G1 사람 결정(2026-10-10)** 을 반영해 다시 썼다(끝의 "G1 반영 내역"). 초안은 그대로 둔다.
> 범위 근거: `docs/SCOPE.md` "Sprint 4 범위". "반드시"는 우선순위대로 ① 공개 배포 전 안전장치 ② 서울 25개 구 확장 ③ TourAPI 연결 ④ 배포(Netlify + Cloud Run + Secret Manager) ⑤ 문서다.
> "선택"(무료 DB, 자동 갱신, 구청 검색 수집 확대)은 태스크로 두지 않고 **이월(Sprint 5 후보)** 로만 적는다(§9). "지금 안 함"(NemoClaw/OpenClaw·MCP 에이전트화, 서울 밖, 유료 인프라)은 어떤 태스크에도 넣지 않았다.
> 시간 상자는 없고 소요 시간도 추정하지 않는다. **키·계정이 없어도 되는 코드 작업을 앞에 두고, 실호출·실배포는 뒤에 둔다.** 모든 스테이지 게이트에 "로컬 데모 동작 유지" 칸이 있다(§7).
> 태스크 ID: `T4{순번 2자리}`. G1 로 T420(이월)·T421(삭제)이 빠지고 T434·T435·T436 이 생겼다. 새 테스트 접두사: `test_kc4_*`(파이썬), `*.kc4.test.js`(프론트).
> **TourAPI 방향(D29, 사람 결정)**: 수집·저장·병합하지 않는다. 배포 backend 가 요청 시점에 호출해 **원문 그대로** 별도 절 "한국관광공사 관광정보(원문)"으로만 보인다.

## Sprint 4 최종 실행 계획

| 스테이지 | 태스크 | 병렬 | 결과물 |
|---|---|---|---|
| Stage 1 — 스파이크·이월·측정 | T401~T408 | — | **완료**(`d4f8a4f`, 완료 기록 참조) |
| **게이트 G1** | D24~D29 | — | **사람 승인 2026-10-10** → 코디네이터가 §2 문안을 `docs/DECISIONS.md` 로 옮김 |
| Stage 2 — 공개 안전장치 (D24) | 2a: T409 세션·제한·설정·미들웨어 순서·gzip·카탈로그 동시성 2 ∥ T410 프론트 세션·오류·배포 주소(+`events.html` 설정 로드) → 2b: T411 채팅 세션 분리·동시 처리·일일 상한 ∥ T412 공개 모드 보안 로그·승인·관리자·제보 → 2c: T413 공개 모드 통합 테스트·`kc_demo --public` | 2a 2개 → 2b 2개 → 2c 1개 | 방문자별 대화, 동시 2건, 세션·전역 상한(IP 제한은 실측 뒤에만), 관리자·승인 닫힘, 모든 오류 응답에 CORS 헤더 |
| Stage 3 — 서울 25개 구 (D28) | 3a: T414 지역 파일 21개(+기존 테스트 fixture 전환) ∥ T415 실록 키워드 측정·자동 후보 도구 ∥ T416 카탈로그 25개 구(전체 별칭·쪽 상한·월 버킷 병합 블로킹) ∥ T433 검색 색인(변환 건수 축소, `excluded` 보존) → 3b: **T418 실행**(25개 구 수집·색인(키워드 선택 시)·스냅샷·2차 측정) | 3a 4개 → 3b 단독 | 25개 구 카탈로그(`var/catalog.all`), 검색 1.5초 이하 목표, 2차 측정으로 메모리 확정 |
| Stage 4 — TourAPI 실시간 원문·좌표 (D25·D29) | 4a: T419 TourAPI 실시간 클라이언트(backend 전용, 저장 없음) ∥ T417 좌표 자동 부착(서울 API 장소만) → 4b: T434 묶음 연결·계약 ∥ T435 프론트 "한국관광공사 관광정보(원문)" 절 → 4c: **T422 자동 좌표 생성·실시간 원문 실확인** | 4a 2개 → 4b 2개 → 4c | `backend/tourapi_live.py`, 묶음 `kto_live` 필드, 화면 별도 절, 자동 좌표 사전(서울 API 유래) |
| Stage 5 — 배포 패키징 (D27) | T423 Dockerfile·이미지 데이터(서울 API 유래만)·`.gitignore` ∥ T424 Netlify 설정·빌드 스크립트(직접 CORS) ∥ T425 Cloud Run 배포 스크립트·가이드(us-central1·비밀 2개 숫자 버전) ∥ T436 쓰기 경로(`/tmp`) 크기 상한 | 4개 병렬 | `Dockerfile`, `netlify.toml`, `scripts/{build_image_data,netlify_build,deploy_cloudrun}.sh`, `docs/guides/DEPLOY.md`, 감사·캐시 상한 |
| Stage 6 — 실제 배포 (계정 필요) | T426 Cloud Run 배포·XFF 실측·남용 점검 → T427 Netlify 배포·카카오 도메인·화면 확인 | 순차 | 공개 URL 2개, `docs/status/deploy_*.md` |
| Stage 7 — 문서 | T428 README·상태·가이드 ∥ T429 배포 URL 스크린샷 | 2개 병렬 | 배포 URL 기준 문서, `docs/demo/s4-*.png` |

- **필수 경로**: (완료) T401~T408 → (승인) G1 → T409·T410 → T411·T412 → T413 → T414·T415·T416·T433 → T418 → T419·T417 → T434·T435 → T422 → T423·T424·T425·T436 → (H4·H5·H11) T426 → (H6) T427 → T428·T429.
- **측정 순서**: T407 프로파일(완료) → T408 1차(완료) → T433 → **T418 안에서 2차**(`measure_seoul_rows --full` + LLM 경로 RSS 추가). 2차 값으로 D27 메모리(2Gi)·카탈로그 동시성(2)을 다시 확인한다.
- **키·계정이 필요한 일**: T418(서울 키 — 있음, NVIDIA ≤ 2), T422(TourAPI 키 — 있음, H2 충족), T426(GCP H4·H11), T427(Netlify H5·카카오 H6). 모두 해당 스테이지 끝에 있다.
- **사람 데이터가 없어도 끝까지 간다**: 21개 구 실록 키워드(H3)는 선택이다. 고르지 않으면 그 구는 "실록 색인 대상 아님"(D28 ③).
- **얇은 수직 경로는 이미 있다**: 일정 문장 → 게이트 → 별도 프로세스 파이프라인 → 행사 검색 → 묶음 v2 → 화면(Sprint 3). Stage 2 는 이 경로를 여러 방문자용으로, Stage 4 는 같은 경로 끝에 TourAPI 원문 절을 붙이고, Stage 5·6 은 같은 경로를 컨테이너에 싣는다.

---

## 0. 기준선 · 공통 규칙

### 0.1 Stage 2 착수 직전 dev 가 실측해 적는다
- 기준(Stage 1 완료 기록): pytest 1,943 · node 365 · ruff 통과 · eval validate/check 0 · `kc_demo.sh --check` 0. 착수 시 다시 실측해 적는다: pytest ____ · node ____.

### 0.2 공통 규칙 (Sprint 3 §0.2 를 이어받음)
- 파이썬 3.11+, 줄 길이 100, ruff 통과. 공개 함수에 타입 힌트, 새 패키지 `__init__.py` 는 `__all__` 명시.
- **PostToolUse 훅이 `ruff --fix` 로 미사용 import 를 지운다. import 와 그 사용은 한 번의 편집에 같이 쓴다.**
- **새 런타임 의존성 금지.** 있는 것만: `fastapi`·`httpx`·`mcp`·`openai`·`python-dotenv`·`uvicorn` + 표준 라이브러리(그리고 이들이 이미 끌고 오는 `starlette` — gzip 미들웨어는 여기서). 프론트는 의존성 없음. GCP·Netlify 는 CLI(`gcloud`·`netlify`)를 셸 스크립트에서 부르고 SDK 를 쓰지 않는다. Secret Manager 는 Cloud Run env 주입으로만.
- 테스트 파일 이름은 레포 전체에서 고유하게. `tests/test_layout.py`·`test_smoke.py`·`test_boundaries.py` 는 수정하지 않는다.
- 도메인 코드는 `domains/kcontext/` 에만. `core/` 에 도메인 용어 금지(D3).
- **backend 는 `domains`·`mcp_server` 를 import 하지 않는다**(D3·D10). TourAPI 실시간 클라이언트는 backend 전용 모듈로 두고(D29, T419) `domains` 를 import 하지 않는다.
- **지역은 코드에 박지 않는다**(데이터 파일에서만). backend 가 쓰는 TourAPI 구 코드표는 `backend/fixtures/tourapi_codes.json`(데이터 파일, T401 ⑦ 실측값).
- **사실을 지어내지 않는다.** 테스트·fixture 의 행사·좌표·한자 지명은 `○○`·`예시`·`합성` 값만. 실록 키워드는 사람이 고른 값만. 좌표는 사람 사전 또는 D25(서울 API 장소만). TourAPI 이름·파라미터·필드는 `docs/spikes/tourapi.md` ⑩ "확정 필드 목록"만.
- **TourAPI 원문(D29)**: 저장(파일·DB·캐시·메모리 재사용)·정규화(날짜 포맷 변환 포함)·병합·요약·번역·좌표 사전 반영·지도 핀·이미지 표시를 하지 않는다. 받은 값은 그 요청의 응답에만 싣고 버린다. 로그·audit 에는 건수·상태만.
- **재배포 범위**: 저장소·이미지·정적 데이터에는 서울 열린데이터광장(공공누리 1유형) 유래만. Tavily 유래(D12 ⑦·D19)·TourAPI 유래(D29)는 넣지 않는다.
- 키는 env **변수 이름**으로만(규칙 1, D1, D5). 키 값·Authorization 헤더·서비스키가 든 URL·세션 토큰·LLM 원문 응답 전체를 코드·로그·결과 파일·커밋에 남기지 않는다. TourAPI 서비스키는 쿼리 문자열에 들어가므로 **오류 메시지·로그에 요청 URL 을 싣지 않는다**.
- `deploy/openshell/policy*.yaml`·`.env`·`eval/testset.json`·`CLAUDE.md`·`docs/DECISIONS.md` 는 dev·pm 이 고치지 않는다.
- 프론트 태스크는 **표에 적힌 파일만** 고친다. `?api=mock` 데모 모드는 지우지 않는다.
- **결과를 맞추려고 기존 테스트의 기대값을 바꾸지 않는다.** 실제 데이터 폴더에 의존하는 테스트가 깨지면 fixture 폴더로 전환한다.
- **공개 모드는 `KC_PUBLIC_MODE=1` 일 때만.** 꺼져 있으면(로컬 기본) 지금 동작과 같아야 한다(기존 테스트·`eval/kc_eval/stability.py`·`kc_demo.sh`). 로컬 모드에서 세션 헤더가 없으면 공용 세션 `local`.
- 실호출은 §6 상한 안에서만. 상한은 코드 인자로도 둔다.

### 0.3 코드·실측으로 확인한 현황 (pm 조사 + dev 대조 + Stage 1 결과)
| 영역 | 위치 | 확인한 사실 | 관계 태스크 |
|---|---|---|---|
| 대화 기록 | `backend/chat.py` `_history`·`_seq` | 프로세스에 하나 — 방문자 공용 | T411 |
| 동시 처리 | `chat.py` `_story_lock` | 일정 흐름 1건만 | T411 |
| 요청별 로그 | `chat.py` `_TeeSink.mark()/since()` | 동시 요청이면 로그가 섞인다 | T411 |
| 검색 한도 | `chat.py` `self._search_timeout_s` | 인스턴스 필드 — 경쟁 | T411 |
| 카탈로그 자식 | `backend/catalog_runner.py` | 동시성 상한 없음. **검색 자식 최대 RSS 199MiB(4개 구), 25개 구 추정 413MiB**(`measure_2026-10-10.md`) | T409·T433 |
| 미들웨어 순서 | `backend/app.py:35` | 나중에 붙은 http 미들웨어가 바깥 — 413 에 CORS 헤더 없음 | T409 |
| 응답 크기 | 행사 검색 응답 1.38MB(그중 `excluded` 1.1MB), 묶음 events 약 233KB | us-central1 무료 송출은 북미발 월 1GiB(`cloud_run.md` §4·§13 7) — 압축 없으면 금방 닿는다 | T409(gzip) |
| API 문서 | `FastAPI(title="backend")` | `/docs`·`/openapi.json` 공개 | T409 |
| 보안 로그 | `routers/review.py` | 전체 노출, 승인 API 무인증 | T412 |
| 관리자·제보 | `routers/events.py` | 실패 횟수 제한 없음, 제보 무인증 쓰기 | T409·T412 |
| 행사 검색 | `catalog/api.py::_search` | **병목은 `entry_from_dict` ×8,719 = 약 87%**, `excluded` 직렬화는 0.1%(`catalog_search_profile_2026-10-10.md`). `entries_built_at()` 이 entries.json 을 한 번 더 파싱(3%) | T433 |
| 검색 판정 순서 | `query.py::search_events` | demo 건너뜀 → `in_target != yes` → 취소 → 종료 → 여행 날짜… 앞의 셋은 요청과 무관 | T433 |
| `excluded` 소비자 | `backend/chat_story.py::_shrink_excluded`, `frontend/.../src/events/view.js:135` | 계약 — 보존 | T433 |
| 병합 | `catalog/merge.py::_group` | 2,000건 4.9초 → 3만 건 약 18분(dev 계측) | T416 |
| 서울 API | `catalog/seoul.py` | 총 **19,586행**(서울 전체, 구 필터 없음) — 쪽 상한 3만 안. 4개 구 관찰값 8,712 = 44.5% | T416·T418 |
| 지역 파일·테스트 | `data/regions/`, `tests/domains/kcontext/test_kc_regions.py:31` | 4개 단언 | T414 |
| TourAPI | `docs/spikes/tourapi.md` | 표본 **전부 공공누리 3유형**. 오류도 HTTP 200(`OpenAPI_ServiceResponse.cmmMsgHeader`). `item` 이 객체/리스트 둘 다 가능, 0건이면 `items` 빈 값. 서울 `lDongRegnCd=11`, 25개 구 `lDongSignguCd` 표(⑦). 개발계정 1,000건(단위 미확인). 서울 행사 10~12월 58건 | T419·T434 |
| Netlify | `docs/spikes/netlify.md` | 프록시 한도 **26초** → 직접 CORS. 미리보기 출처는 운영과 다름 | T424 |
| Cloud Run | `docs/spikes/cloud_run.md` | 무료량은 Tier 1 기준(서울은 Tier 2). 이미지 크기 직접 한도 없음, AR 무료 0.5GiB. `/tmp` 는 메모리. `max-instances` 잠깐 초과 가능(S5). 비활성 비밀 버전도 활성으로 셈 — destroy. XFF 처리 문서 없음 | D27·T425·T426·T436 |
| 프론트 설정 | `index.html:13` 만 `config.local.js` 로드 | 행사 화면에 배포 주소를 줄 수단 없음 | T410 |

---

## 1. 의존성 그래프

```
Stage 1 (완료 d4f8a4f)  ──►  G1: D24~D29 사람 승인(2026-10-10)
                                   │
Stage 2 (D24)                      ▼
  2a: T409 backend 기반(session·limits·settings·app 순서·gzip·meta·catalog 동시성 2) ∥ T410 프론트
  2b: T411 chat.py·messages.py ∥ T412 review.py·events.py
  2c: T413 공개 모드 통합 + kc_demo --public
                                   │
Stage 3 (D28)
  3a: T414 지역 21개 ∥ T415 키워드 도구 ∥ T416 카탈로그 25개 구 ∥ T433 검색 색인
  3b: T418 실행 + 2차 측정 (H3 선택)
                                   │
Stage 4 (D25·D29)
  4a: T419 TourAPI 실시간 클라이언트(backend/tourapi_live.py) ∥ T417 자동 좌표(서울 API만)
  4b: T434 묶음 연결·계약(chat.py·chat_story.py·계약 문서) ∥ T435 프론트 원문 절
  4c: T422 자동 좌표 생성 + 실시간 원문 실확인
                                   │
Stage 5 (D27): T423 이미지 ∥ T424 Netlify ∥ T425 배포 스크립트 ∥ T436 /tmp 상한
                                   │
Stage 6 ◄── H4·H11·H7 / H5·H6:  T426 Cloud Run·XFF 실측 → T427 Netlify·카카오·화면
                                   │
Stage 7: T428 문서 ∥ T429 스크린샷
```

---

## 2. 결정 (G1 — 2026-10-10 사람 승인)

pm·dev 는 `docs/DECISIONS.md` 를 고치지 않는다. **아래 §2.1 문안을 코디네이터가 DECISIONS.md 로 옮긴다.**

| 결정 | 요지 | 착수 조건이 되는 스테이지 |
|---|---|---|
| D24 | 공개 배포 보안 모델 + D20 재검토 결론. IP 를 믿을 수 없으면 IP 제한을 끈다 | Stage 2 |
| D25 | 좌표 자동 부착은 서울 API 장소만, 데이터 기반 이상치 제거 | T417 |
| D26 | **철회(승인 전) — D29 로 대체**. 기록만 남긴다 | — |
| D27 | 배포: Netlify(직접 CORS) + Cloud Run us-central1(1 인스턴스, 2Gi·1 CPU) + Secret Manager(비밀 2개, 숫자 버전) | Stage 5 |
| D28 | 실록 색인은 사람이 고른 키워드로만, 기본 빈 목록, 이미지 상한은 AR 0.5GiB·빌드 시간 | T418 |
| D29 | TourAPI 는 실시간 원문 표시만(D7 예외). 저장·정규화·병합·좌표·핀 없음 | Stage 4 |

> **메모 — D29 번호 재사용**: 초안·확정 1판의 D29 는 "`excluded` 를 요약으로 바꾸는 조건부 후보"였다. T407 프로파일(`excluded` 직렬화 0.1%)로 필요 없어져 DECISIONS.md 에 올라간 적이 없으므로, 그 번호를 TourAPI 실시간 원문 결정에 다시 쓴다. "번호는 지우지 않는다"는 규칙은 DECISIONS.md 에 추가된 번호에 적용되며, D29(조건부)는 추가된 적이 없다.

### 2.1 D24~D29 최종 문안 (DECISIONS.md 이관용)

```markdown
## D24 — 공개 배포는 서버 발급 세션 토큰·요청 제한·일일 소프트 상한으로 지키고, 공개 모드에서는 관리자·승인·제보 쓰기를 닫는다. OpenShell 은 계속 선택이다 (2026-10-10, 사람 승인)
- **결정**:
  ① **세션**: `POST /api/session` 이 임의 토큰(`secrets.token_urlsafe(32)`, 43자)을 발급하고, 브라우저는 탭 단위 `sessionStorage` 에 두어 `X-KC-Session` 헤더로 보낸다(쿠키 없음). 서버는 세션별 대화 기록(최대 100개)·보안 로그 항목(최대 200개)을 **프로세스 메모리에만** 두고, 마지막 사용 후 2시간 뒤 지운다(세션 수 상한 1,000, 넘으면 가장 오래 안 쓴 세션부터). **채팅 묶음은 서버에 보관하지 않는다(D17 유지)**. **로컬 모드(공개 모드 꺼짐)에서 세션 헤더가 없으면 공용 세션 `local`** — 지금 동작과 같다.
  ② **동시 처리**: 일정 흐름은 인스턴스당 동시 2건(`KC_STORY_CONCURRENCY`), 세션당 1건, 행사 카탈로그 자식 프로세스는 인스턴스당 **2개**(`KC_CATALOG_CONCURRENCY`, 메모리 2Gi 기준 — 2차 측정으로 재확인). 넘으면 기다리지 않고 429 `busy`.
  ③ **요청 제한·상한**: 세션별·전역 고정 창 제한(sprint-4 §6.2). 넘으면 429 `rate_limited` + `Retry-After`. **LLM 일일 상한**: 하루(KST) LLM 호출 단위 `KC_LLM_DAILY_UNITS`(기본 300)를 넘으면 503 `daily_limit`. 일정 흐름은 2단위를 예약하고 실제 시도 수(캐시면 0)만큼 남기고 돌려받는다. 일반 챗봇은 1단위. **이 상한은 인스턴스 메모리 기반 소프트 상한이라 재시작하면 0 으로 돌아간다. 실제 비용 상한은 NVIDIA 크레딧이다.**
  ④ **IP**: `X-Forwarded-For` 를 오른쪽에서 `KC_TRUSTED_PROXY_HOPS` 번째 값으로 읽는다. **값에 기본값을 두지 않는다** — 배포 후 실측(T426)으로 정해 설정한다. **설정되지 않았거나(실측 전) 그 값으로 IP 를 읽지 못해 연결 주소로 폴백하는 요청에는 IP 별 제한을 적용하지 않고**, 세션 제한과 전역 상한(일일 LLM·TourAPI, 전역 요청률)만 적용한다 — 폴백 주소는 앞단 프록시라 모든 방문자가 같은 IP 로 보이기 때문이다.
  ⑤ **공개 모드**(`KC_PUBLIC_MODE=1`): `/api/admin/*`·`POST /api/audit/{id}/decision`·`POST /api/reports` 는 403 `disabled_in_public`. `GET /api/audit` 은 그 세션의 항목만. `/docs`·`/redoc`·`/openapi.json` 은 끈다. `admin.html` 은 공개 배포물에 넣지 않는다. 모든 오류 응답(413·429·403·503 포함)에 CORS 헤더가 붙는다(CORS 를 가장 바깥 미들웨어로). 응답은 gzip 으로 압축한다(송출량 — D27).
  ⑥ **일정 캐시 공유(알려진 작은 노출)**: 일정 이해 캐시(D15 ④)는 방문자 사이에 공유되어, 같은 문장을 누군가 먼저 보냈다면 "이전 결과 재사용" 표시로 그 사실이 드러날 수 있다. 내용은 드러나지 않아 영향이 작다고 보고 그대로 둔다(README 한계에 적는다).
  ⑦ **D20 재검토 결론**: 공개 서비스로 띄워도 OpenShell 은 필수로 돌리지 않는다. LLM 에 도구가 없고 출력이 실행되지 않으며, 에이전트 역할 프로세스에는 허용 목록 env 만 가고(D7 ③), 외부 자료는 호스트 수집기만 받는다(D7, 예외는 D29 — backend 의 TourAPI 실시간 호출이며 LLM·에이전트 프로세스와 무관). 공개로 새로 생기는 위협은 ①~⑤ 로 막는다. LLM 에 도구를 주거나 NemoClaw 로 옮기면 D20 대로 다시 본다.
- **계기**: SCOPE Sprint 4 ① 과 D20 "다시 볼 때 — 공개 서비스로 띄울 때". 코드 확인: 대화 기록 공용, 일정 흐름 1건, 승인 API 무인증, 보안 로그 전체 노출, 동시 요청 시 로그 섞임, 413 에 CORS 헤더 없음. Cloud Run 문서에 XFF 처리 설명 없음(sprint-4 T402).
- **대안**: (a) 쿠키 세션 — 다른 출처라 서드파티 쿠키 문제로 기각. (b) 대화 기록을 브라우저가 들고 보냄 — 위조 턴 주입 경로라 기각. (c) 클라이언트 생성 토큰 — 발급 수를 제한할 수 없어 기각. (d) 승인 API 를 관리자 토큰으로 열어 둠 — 공개 흐름에 승인할 초안이 없고 대입 표면만 생겨 기각. (e) XFF 맨 왼쪽 값을 그대로 신뢰 — 방문자가 값을 위조할 수 있어 기각. (f) 실측 전 hops 기본값(예: 1) — 근거 없이 정하면 전원이 같은 IP 로 묶이거나 위조 값을 믿게 되어 기각. (g) 외부 저장소로 상한 공유 — 새 의존성·유료 가능성으로 기각. (h) OpenShell 필수화 — 위협 모델과 맞지 않아 기각.

## D25 — 장소 좌표 자동 부착은 서울 열린데이터광장 행사 장소 좌표만 쓰고, 데이터로 이상치를 거르며, 사람 사전이 우선하고, 화면에 "공공 데이터 좌표"로 밝힌다 (2026-10-10, 사람 승인)
- **결정**: ① 출처는 **서울 열린데이터광장 문화행사의 장소명·위경도(LAT·LOT)·자치구(GUNAME)** 뿐이다. **TourAPI 좌표는 쓰지 않는다(D29).** ② 같은 이름(정규화 후)의 좌표들이 중앙값에서 모두 150m 안이면 중앙값을 쓰고, 벗어나면 그 이름은 버린다(모호). ③ 이상치: 같은 GUNAME 의 모든 좌표 중앙값에서 `max_gu_dist_km`(제안 8km, 분포를 보고 조정해 근거를 남김) 넘게 떨어진 좌표는 버린다. 구가 없는 좌표, 표본이 3개 미만인 구의 좌표는 쓰지 않는다. 사람이 정하는 범위 값은 쓰지 않는다. ④ 사람 사전(`demo_places.json`)에 같은 이름·별칭이 있으면 사람 값이 이긴다. ⑤ 자동 사전은 `var/places/auto_places.json` 에 생성하고(커밋하지 않음) 항목마다 `source`·`verified_at`·`auto: true`·`origin` 을 둔다. ⑥ 앵커가 자동 좌표를 쓰면 문제 코드 `COORD_AUTO` 를 남기고 화면은 고정 문구("공공 데이터 좌표(사람 확인 전)")로 보인다. ⑦ 자동 좌표는 지도 핀·이동 구간 거리 표시에 쓰고, 판정 규칙(D16·D13 ⑥)은 그대로다. ⑧ 자동 사전 이름은 일정 게이트(`backend/fixtures/chat_places.json`)에 넣지 않는다.
- **계기**: 좌표가 있는 장소가 5곳뿐이라 25개 구 확장의 병목. Sprint 3 규칙("좌표는 사람이 출처를 확인한 값만")을 서울 API 값에 한해 넓힌다.
- **대안**: (a) 카카오 로컬 등 외부 장소 검색 — 새 키·외부 호출·약관 확인 필요로 기각. (b) TourAPI 관광지 좌표 — 공공누리 3유형(변경금지)이고 좌표의 핀 사용 허용 여부가 미확인이라 기각(D29). (c) 사람이 정한 서울 bbox — 사람 값이 필요하고 구 단위 오류는 못 거르므로 기각. (d) 좌표 하나라도 있으면 채택 — 동명 장소가 섞여 기각.

## D26 — (승인 전 철회) TourAPI × 서울 API 병합 — D29 로 대체 (2026-10-10, 사람 결정)
- **결정**: TourAPI 행사를 서울 열린데이터광장 행사와 병합하지 않는다. TourAPI 는 D29(실시간 원문 표시)로만 다룬다. 이 번호는 검토 기록으로 남긴다.
- **계기**: 원안("D13 묶기 규칙으로 병합, 관광지는 좌표 사전 입력")은 TourAPI 표본 전부가 공공누리 3유형(변경금지)으로 확인되어(sprint-4 T401) 병합·정규화가 "변경"에 해당할 수 있다.
- **대안**: 원안대로 병합 — 3유형 위반 가능성으로 기각. 1유형 항목만 병합 — 표본에 1유형이 없고 `cpyrhtDivCd` 의 적용 대상(텍스트·좌표·사진)이 미확인이라 기각.

## D27 — 배포는 Netlify(정적, 직접 CORS) + Cloud Run(us-central1, 인스턴스 1개, 2Gi·1 CPU) + Secret Manager(비밀 2개, 숫자 버전 고정)로 하고, 이미지는 서울 25개 구·서울 API 유래만 담으며, 상태는 휘발이다 (2026-10-10, 사람 승인)
- **결정**:
  ① **화면**: Netlify 정적 배포. `frontend/k-context` 를 빌드에서 `dist/` 로 복사하고 `config.local.js` 를 Netlify 환경변수로 생성(키는 저장소에 없음). `admin.html` 은 싣지 않는다.
  ② **API 연결은 직접 CORS** — Netlify 프록시 요청 시간 한도 26초가 일정 흐름 최대 100초보다 짧다(T403). `KC_CORS_ORIGINS` 는 **운영 도메인 하나만**(미리보기·브랜치 배포 출처는 넣지 않는다 — 미리보기는 화면 확인용). 빌드가 `dist/events.html` 의 `connect-src` 에 Cloud Run 원점을 넣는다. `index.html` CSP 는 강제하지 않는다(카카오 SDK 위험, 넣으면 Report-Only).
  ③ **Cloud Run**: 리전 **us-central1**(Tier 1 무료량과 북미발 송출 월 1GiB 를 쓰기 위해. 서울 대비 지연 약 0.15~0.2초 증가를 감수 — 사람 결정). 컨테이너 하나(uvicorn 1 프로세스 + 요청마다 자식 프로세스), `max-instances=1`·`min-instances=0`, `--timeout=120`, **`--memory=2Gi`·`--cpu=1`**, 요청 기반 청구. 카탈로그 자식 동시성 2(D24 ②). 메모리는 T418 2차 측정(25개 구 + T433 적용)의 최대 RSS × 1.5 + `/tmp` 사용량이 2Gi 안인지로 다시 확인하고, 넘으면 카탈로그 동시성을 1로 낮춘다. 응답은 gzip(송출 1GiB 보호).
  ④ **이미지 데이터**: 실록 색인 + **서울 25개 구 카탈로그**(사용자 결정 "서울 전체") + 자동 좌표 사전. 카탈로그는 스냅샷(D19)과 같은 규칙으로 **`seoul_openapi` 유래만** 남겨 다시 묶은 것이고, Tavily 유래(D12 ⑦)·TourAPI 유래(D29)는 넣지 않는다. 모두 빌드 전에 호스트에서 만든다. 런타임에는 서울 API·Tavily 를 부르지 않는다(D7). **TourAPI 만 D29 예외로 요청 시점에 부른다.**
  ⑤ 로컬 데모(`kc_demo.sh`) 기본 지역은 4개 구, `all` 은 옵션. 배포 이미지만 25개 구다.
  ⑥ **비밀**: Secret Manager → Cloud Run env 로 **`NVIDIA_API_KEY`·`DATA_GO_KR_SERVICE_KEY` 두 개**. 참조는 `latest` 가 아니라 **숫자 버전으로 고정**하고, 키를 교체하면 새 버전으로 재배포한 뒤 **옛 버전을 destroy** 한다(비활성 버전도 무료 6개 한도에 들어감, T402 §8). 서비스 계정에 `roles/secretmanager.secretAccessor`. 이미지·빌드 컨텍스트에는 비밀이 없다(규칙 1).
  ⑦ **상태는 휘발**: hitl·audit·일정 캐시는 `/tmp`(인메모리 파일시스템 — 인스턴스 메모리에 합산된다), 세션은 프로세스 메모리. 재시작하면 비워진다. `/tmp` 상한: 감사 JSONL 은 파일당 8MiB 에서 회전하고 최근 2개만 남긴다(최대 16MiB), 일정 캐시는 최대 500개 파일·32MiB 를 넘으면 오래된 것부터 지운다, 파이프라인 임시 폴더는 요청마다 지운다(기존).
  ⑧ **알려진 한계**: `max-instances=1` 은 트래픽 급증 때 **잠깐 초과될 수 있다**(Cloud Run 문서). 그동안 인스턴스가 둘이 되어 메모리 세션·요청 제한·일일 상한이 인스턴스마다 따로 세어지고(상한이 최대 2배), 새 탭이 다른 인스턴스로 가면 대화가 안 보일 수 있다. 데모 범위에서 감수한다.
  ⑨ 무료 사용량 밖 설정(최소 인스턴스 ≥1, 인스턴스 기반 청구, 취약점 스캔 등)은 쓰지 않고, 사람이 결제 계정에 예산 알림을 건다(알림은 사용을 막지 않는다 — 1차 방어는 ③·D24). 이미지 저장소는 같은 리전 Artifact Registry, 빌드는 로컬 `docker build`(linux/amd64) + push 기본.
- **계기**: SCOPE Sprint 4 ④. T402(Cloud Run)·T403(Netlify)·T408(측정) 결과와 사람 결정(리전·직접 CORS·비밀 2개).
- **대안**: (a) Netlify 프록시 — 26초 한도로 기각. (b) 서울 리전 — Tier 2 라 무료량이 실질 줄 수 있어 기각(지연은 낮음). (c) Netlify Functions 백엔드 — 별도 프로세스·SQLite·90초 파이프라인과 맞지 않아 기각. (d) 색인을 GCS 에서 내려받기 — 이미지가 AR 0.5GiB 를 크게 넘을 때의 예비안. (e) 런타임 수집 — D7 과 충돌해 기각. (f) 인스턴스 여러 개 — 제한이 무력해져 기각. (g) `var/catalog` 를 그대로 이미지에 — Tavily 유래가 공개돼 기각. (h) 비밀 `latest` 참조 — 교체 시점이 인스턴스 시작에 따라 달라지고 옛 버전이 남아 기각.

## D28 — 실록 색인은 사람이 고른 키워드로만 서울 확장하고, 고르지 않은 구는 "색인 대상 아님"으로 둔다. 전체 색인은 하지 않는다 (2026-10-10, 사람 승인)
- **결정**: ① `--mode regions` 그대로, 25개 구 `sillok_keywords` 의 합집합으로 다시 만든다. ② 새 구의 키워드는 자동 후보 도구(실록 지명 태그 독음 ↔ 구별 동 이름, 건수 포함)가 낸 후보 중 **사람이 고른 것**만 넣고, 고른 사람·날짜·근거를 지역 파일 `note` 에 남긴다. ③ **기본은 빈 목록**이고, 빈 목록인 구는 "실록 색인 대상 아님"으로 README·상태 문서에 밝힌다. ④ **크기 상한은 Cloud Run 한도가 아니라 Artifact Registry 무료 저장 0.5GiB 와 빌드·푸시 시간이다**(Cloud Run 은 이미지 크기에 직접 한도가 없다, T402 §6). 25개 구 전부에 키워드가 있을 때 색인은 거친 상한 약 270MiB(T408 추정)이므로, 이미지 전체(기반 이미지·의존성·카탈로그·색인)가 0.5GiB 를 넘으면 키워드를 줄이거나 D27 (d) 예비안으로 간다. ⑤ `--mode all`(38만 기사)은 하지 않는다.
- **계기**: SCOPE Sprint 4 ② "실록 색인을 서울 전체 키워드로 재구축". 키워드는 사실이라 기억으로 채울 수 없다.
- **대안**: 전체 색인 — 수 GB 로 기각. 한글 구 이름만 — 본문이 한문이라 재현율이 낮고 동명이 섞여 기각. 사람이 처음부터 출처를 찾아 작성 — 병목이라 자동 후보 + 고르기로 바꿈.

## D29 — 한국관광공사 TourAPI 는 요청 시점에 호출해 원문 그대로 별도 절로만 보이고, 저장·정규화·병합·좌표 반영·지도 핀은 하지 않는다 (2026-10-10, 사람 결정)
- **결정**:
  ① **D7 의 예외**: 배포 backend 가 사용자 요청 시점에 TourAPI(`https://apis.data.go.kr/B551011/KorService2`, `searchFestival2` 등 sprint-4 T401 확정 오퍼레이션)를 직접 호출할 수 있다. 호출은 backend 프로세스(`backend/tourapi_live.py`)만 하고, 키는 에이전트 역할 자식 프로세스에 넘기지 않는다. LLM 은 TourAPI 값을 보지 않는다.
  ② **하지 않는 것**: 저장(파일·DB·로그·캐시), **메모리 안 짧은 재사용(예: 같은 조건 10분)도 "저장"에 해당하는지 미확인이므로 하지 않는다**, 정규화(필드 값 형식 변환 — 날짜 포맷 포함), 서울 API 행사와의 병합(D13·D26 대상 아님), 요약·번역·재서술, 좌표 사전 반영(D25), **지도 핀(허용 여부 미확인 → 불허로 취급)**, 이미지(`firstimage` 등) 표시·hotlink.
  ③ **화면**: 서울 API 행사 목록과 섞지 않고 별도 절 **"한국관광공사 관광정보(원문)"** 으로 둔다. 값은 응답 필드 그대로(고른 필드만 보이는 것은 허용, 값은 바꾸지 않는다), 출처 표기 **"출처: 한국관광공사 TourAPI · 공공누리 제3유형(변경금지)"**(항목의 `cpyrhtDivCd` 가 `Type1` 이면 "제1유형(출처표시)")와 원문 링크를 붙인다. 원문 링크는 한국관광공사 상세 페이지 주소 형식이 확인되면 그 주소, 확인 전에는 공공데이터포털 데이터셋 페이지(`https://www.data.go.kr/data/15101578/openapi.do`).
  ④ **실패·상한**: 호출 실패(네트워크·시간 초과·`cmmMsgHeader` 오류·`resultCode` ≠ `0000`)나 상한 초과 시 그 절을 **"지금 확인할 수 없음"** 으로 보이고 나머지 화면은 그대로다. **키 오류도 HTTP 200 으로 오므로** 최상위가 `response` 가 아니면(`OpenAPI_ServiceResponse.cmmMsgHeader`) 오류로 판정한다.
  ⑤ **호출 한도**: 개발계정 1,000건(단위는 일일로 추정 [확인 필요])에 맞춰 **전역 일일 소프트 상한 300회**(`KC_TOURAPI_DAILY_CALLS`, 개발·확인용 여유를 남김), **세션당 하루 10회**, 요청 1건당 최대 1회 호출(첫 쪽 `numOfRows` 20)·시간 한도 5초. 메모리 기반이라 재시작 시 초기화된다(D24 ③ 과 같은 성격).
  ⑥ **키**: `DATA_GO_KR_SERVICE_KEY` 는 Secret Manager 로 주입한다(D27 ⑥). 오류 메시지·로그에 요청 URL·키를 싣지 않는다. 키가 없으면 절은 "지금 확인할 수 없음"(로컬 데모에서 키가 없을 때도 같음).
  ⑦ 공개 모드 남용 방지는 ⑤ 의 세션·전역 상한과 D24 의 세션·전역 제한으로 한다.
  ⑧ `cpyrhtDivCd` 의 적용 대상(텍스트·좌표·사진)과 3유형 데이터의 저장·재배포·핀 사용 허용 여부가 활용매뉴얼 또는 한국관광공사 회신으로 확인되면 이 결정을 다시 본다.
- **계기**: sprint-4 T401 — 서울 행사 58건·관광지·이미지 표본 전부 공공누리 3유형(변경금지). 공식 문구로 허용이 분명한 것은 "바꾸지 않은 값을 출처와 함께 이용"뿐이다. SCOPE Sprint 4 ③ "TourAPI 연결"을 이 범위 안에서 채운다.
- **대안**: (a) 수집·병합(원 D26) — 3유형 변경금지와 충돌 가능성으로 기각. (b) 원문 저장 후 표시 — 저장 허용 여부 미확인으로 기각. (c) 짧은 메모리 재사용 — 같은 이유로 기각(호출 수는 ⑤ 상한으로 묶음). (d) TourAPI 를 쓰지 않음 — SCOPE ③ 을 못 채워 기각. (e) 에이전트 자식 프로세스에서 호출 — 키가 에이전트 역할 프로세스로 가서 D7 ③ 과 어긋나 기각.
- **메모**: 이 번호는 계획 단계의 조건부 후보("excluded 요약")에 붙었다가 T407 결과로 필요 없어져 DECISIONS.md 에 추가되지 않았던 번호를 다시 쓴 것이다.
```

---

## 3. 사람 선행 · 블로커

### 3.1 사람 선행 작업
| ID | 할 일 | 상태 | 막는 태스크 | 막혀 있을 때 |
|---|---|---|---|---|
| H1 | G1: D24~D29 승인 → DECISIONS.md 이관(코디네이터) | **승인됨**(2026-10-10), 이관 대기 | Stage 2 착수 | — |
| H2 | TourAPI 서비스키(`DATA_GO_KR_SERVICE_KEY`) | **충족** — `.env` 에 있고 T401 이 실호출로 확인 | T419 실확인·T422 | — |
| H4 | **GCP**: 프로젝트, 결제 계정 연결(카드 등록에 시간이 걸릴 수 있음), 예산 알림(예: 1 USD), `gcloud auth login`, API 사용 설정(Run·Artifact Registry·Secret Manager) | **지금 착수 가능** | T426 | Stage 5 까지 진행, 배포 대기 |
| H5 | **Netlify** 계정·`netlify login`, 사이트 이름 | 지금 착수 가능 | T427 | 배포 대기 |
| H6 | **카카오 개발자 콘솔**에 운영 도메인 등록(`docs/spikes/kakao_domain.md` 절차), JS 키를 Netlify 환경변수 `KC_KAKAO_JS_KEY` 로 | T427 직전 | T427 의 카카오 지도 | SVG 지도로 배포(D11) |
| H7 | **NVIDIA 크레딧 잔량·호출 한도 확인** → `KC_LLM_DAILY_UNITS` 확정(기본 300) — 실제 비용 상한 | T426 전 | T426 공개 | 기본 300 |
| H11 | **Secret Manager 에 `NVIDIA_API_KEY`·`DATA_GO_KR_SERVICE_KEY` 값 등록**(사람이 직접, 숫자 버전 기록 — 명령은 T425 가이드) | T426 전 | T426 | 배포 대기 |
| H3 | *(선택)* T415 자동 후보 중 21개 구 실록 키워드 고르기 | Stage 3 | T418 의 색인 재구축 | 그 구는 "실록 색인 대상 아님" |
| H13 | *(선택)* TourAPI 활용매뉴얼 내려받기·한국관광공사 문의(`cpyrhtDivCd` 적용 대상, 3유형 저장·핀 허용) | 언제든 | 없음(D29 ⑧ 재검토 근거) | D29 그대로 |
| H12 | *(선택)* T429 스크린샷 확인 | Stage 7 | T428 이미지 | 텍스트만 |

### 3.2 블로커 요약
| 블로커 | 막히는 것 | 대응 |
|---|---|---|
| GCP·Netlify·카카오(H4·H5·H6·H11) | Stage 6 | Stage 5 까지 계정 없이. H4 는 지금 착수 |
| NVIDIA 크레딧(H7) | 공개 상한 확정 | 기본 300(소프트) |
| XFF 처리(문서 없음) | IP 별 제한 | 실측 전에는 IP 제한 끔(D24 ④), T426 실측 후 설정 |
| TourAPI 이용 조건(3유형) | 저장·병합·핀 | D29 범위(원문 실시간 표시)만 |
| 송출량(북미발 월 1GiB) | 공개 서비스 지속 | gzip(T409), 묶음 크기 주시(T426) |
| 사람 데이터(H3) | 새 구 실록 | 빈 키워드 기본 |

---

## 4. 스테이지 상세

### Stage 1 — 스파이크·이월·측정 (완료)
| TASK | 제목 | 결과 |
|------|------|------|
| T401 | TourAPI 문서·이용 조건 | `docs/spikes/tourapi.md` — 표본 전부 3유형, 확정 필드 목록, 서울 구 코드표 |
| T402 | Cloud Run 문서 | `docs/spikes/cloud_run.md` — Tier 1 리전, AR 0.5GiB, `/tmp` 메모리, S5, 비밀 destroy |
| T403 | Netlify 문서 | `docs/spikes/netlify.md` — 프록시 26초 → 직접 CORS |
| T404 | 카카오 도메인 문서 | `docs/spikes/kakao_domain.md` |
| T405 | 캐시 키 today·LLM_BACKEND | 완료 |
| T406 | 보안 로그 날짜·최신 우선 | 완료 |
| T407 | 검색 프로파일 | `docs/status/catalog_search_profile_2026-10-10.md` — 병목 `entry_from_dict` 87%, D29(excluded) 불필요 |
| T408 | 측정 1차 | `docs/status/measure_2026-10-10.md` — 서울 19,586행, 검색 자식 199MiB, 권고 2Gi. `--full`·LLM RSS 는 T418 로 |

### Stage 2 — 공개 안전장치 (D24)
| TASK | 제목 | 범위 | 선행 | 병렬 충돌 |
|------|------|------|------|------|
| T409 | backend 세션·제한 기반 + 설정 + 미들웨어 순서 + gzip + 메타 + 카탈로그 동시성 (2a) | `backend/session.py`(신규), `backend/limits.py`(신규), `backend/routers/meta.py`(신규), `backend/settings.py`, `backend/app.py`, `backend/catalog_runner.py`, `.env.example`, `tests/backend/test_kc4_session.py`, `test_kc4_limits.py`, `test_kc4_app_middleware.py` | D24 | 없음 |
| T410 | 프론트 세션·제한 오류·배포 주소 설정 (2a) | `frontend/k-context/src/api/{http,index}.js`, `src/lib/api-base.js`(신규), `src/events/api.js`, `src/components/securitylog/approve-buttons.js`, `src/i18n/{ko,en}.js`, `events.html`, `admin.html`, `config.local.example.js`, `tests/session.kc4.test.js` | D24 | 없음 |
| T411 | 채팅 세션 분리·동시 처리·일일 상한 (2b) | `backend/chat.py`, `backend/routers/messages.py`, `tests/backend/test_kc4_chat_sessions.py` | T409 | 없음 |
| T412 | 공개 모드 보안 로그·승인·관리자·제보 (2b) | `backend/routers/review.py`, `backend/routers/events.py`, `tests/backend/test_kc4_public_mode.py` | T409 | 없음 |
| T413 | 공개 모드 통합 테스트·로컬 공개 모드 (2c) | `tests/test_kc4_public_e2e.py`, `scripts/kc_demo.sh`(`--public`) | T409~T412 | 단독 |

### Stage 3 — 서울 25개 구 (D28)
| TASK | 제목 | 범위 | 선행 | 병렬 충돌 |
|------|------|------|------|------|
| T414 | 지역 파일 21개 + 기존 지역 테스트 fixture 전환 | `domains/kcontext/data/regions/*.json`(신규 21), `tests/domains/kcontext/test_kc_regions.py`(`test_real_regions_load` 만), `tests/fixtures/regions4/*.json`(신규), `tests/domains/kcontext/test_kc4_regions25.py` | — | 없음 |
| T415 | 실록 키워드 측정·자동 후보 도구 | `domains/kcontext/ingest/sillok_keywords.py`(신규), `tests/domains/kcontext/ingest/test_kc4_sillok_keywords.py`, `docs/spikes/sillok_candidates.md`(신규) | — | 없음 |
| T416 | 카탈로그 25개 구: 전체 별칭·쪽 상한·월 버킷 병합 블로킹 | `domains/kcontext/catalog/{target,seoul,merge}.py`, `.env.example`(설명 줄), `scripts/kc_demo.sh`(`KC_DEMO_REGIONS`), `tests/.../catalog/test_kc4_target_all.py`, `test_kc4_merge_blocking.py` | — | `.env.example`·`kc_demo.sh` 는 Stage 2 도 고침 — 다른 스테이지 |
| T433 | 행사 검색 색인 — 변환 건수 축소, `excluded` 보존 | `domains/kcontext/catalog/{store,query,api,__main__}.py`, `scripts/snapshot_catalog.py`(복원 끝 색인 생성 1줄), `tests/.../catalog/test_kc4_search_index.py` | T407 | 없음 |
| T418 | 실행: 25개 구 수집·색인(선택)·스냅샷·2차 측정 (3b) | `data/regions/*.json` 의 `sillok_keywords`(H3), `data/snapshots/catalog/*`, `data/catalog_sources.json`, `docs/status/seoul25_2026-10-xx.md`(신규), `docs/status/measure_2026-10-10.md`(2차 칸), `docs/spikes/sillok.md`(25개 구 절) | T414~T416·T433 | 단독 |

### Stage 4 — TourAPI 실시간 원문·좌표 (D25·D29)
| TASK | 제목 | 범위 | 선행 | 병렬 충돌 |
|------|------|------|------|------|
| T419 | TourAPI 실시간 클라이언트(backend 전용, 저장 없음) (4a) | `backend/tourapi_live.py`(신규), `backend/fixtures/tourapi_codes.json`(신규), `backend/settings.py`(TourAPI 설정 필드), `.env.example`(TourAPI 줄 갱신), `tests/backend/test_kc4_tourapi_live.py`, `tests/fixtures/tourapi/*.json`(합성) | D29 | 없음(settings·.env.example 은 Stage 2·3 과 다른 스테이지) |
| T417 | 좌표 자동 부착 — 서울 API 장소만 (4a) | `domains/kcontext/places.py`, `domains/kcontext/places_build.py`(신규), `domains/kcontext/data/places/auto_rules.json`(신규), `domains/kcontext/pipeline/run.py`(`_attach_coords` 만), `frontend/k-context/src/lib/chat-bundle.js`, `src/i18n/{ko,en}.js`, `tests/domains/kcontext/test_kc4_places_auto.py`, `frontend/k-context/tests/coordauto.kc4.test.js` | D25 | 없음 |
| T434 | 묶음 연결·계약 `kto_live` (4b) | `backend/chat.py`(일정 흐름 끝 1곳), `backend/chat_story.py`(`kto_live` 모양 검사), `docs/chat-bundle.contract.md`, `tests/backend/test_kc4_kto_bundle.py` | T419, T411 | 없음 |
| T435 | 프론트 "한국관광공사 관광정보(원문)" 절 (4b) | `frontend/k-context/src/api/bundle.js`(`kto_live` 수용), `src/components/ktolive/{index,logic}.js`(신규), `src/components/ktolive/ktolive.css`(신규), `src/modules.js`, `src/components/layout/app-shell.js`(슬롯 1개), `src/i18n/{ko,en}.js`, `tests/ktolive.kc4.test.js` | §5.2 계약, T417(i18n 머지 뒤) | 4b 에서 T434 와 파일 겹침 없음 |
| T422 | 자동 좌표 생성·실시간 원문 실확인 (4c) | `docs/status/events_data_2026-10-xx.md`(신규), `domains/kcontext/data/places/auto_rules.json`(값 조정 시), `domains/kcontext/data/catalog_sources.json`(`tourapi_kto` status·notes) | T417·T434·T435 | 단독 |

### Stage 5 — 배포 패키징 (D27)
| TASK | 제목 | 범위 | 선행 | 병렬 충돌 |
|------|------|------|------|------|
| T423 | Dockerfile·이미지 데이터·컨테이너 설정 | `Dockerfile`(신규), `.dockerignore`, **`.gitignore`**(`image-data/`·`dist/`), `deploy/cloudrun/entrypoint.sh`(신규), `deploy/cloudrun/README.md`(신규), `scripts/build_image_data.sh`(신규), `scripts/snapshot_catalog.py`(`--keep-ended`), `tests/test_kc4_container_files.py`, `tests/test_kc4_image_data_filter.py` | D27, T418·T422 | 없음(`.gitignore` 는 이 태스크만) |
| T424 | Netlify 설정·빌드 스크립트(직접 CORS) | `netlify.toml`(신규), `scripts/netlify_build.sh`(신규), `tests/test_kc4_netlify_build.py` | D27 | 없음 |
| T425 | Cloud Run 배포 스크립트·가이드 | `scripts/deploy_cloudrun.sh`(신규), `docs/guides/DEPLOY.md`(신규), `deploy/README.md` | D27 | 없음 |
| T436 | 쓰기 경로(`/tmp`) 크기 상한 | `backend/chat.py`(`_TeeSink` 회전만), `backend/story_runner.py`(캐시 상한 env 전달만), `domains/kcontext/schedule/cache.py`(정리만), `tests/backend/test_kc4_audit_rotate.py`, `tests/domains/kcontext/schedule/test_kc4_cache_prune.py` | D27 ⑦ | 없음(Stage 5 에서 chat.py 는 이 태스크만) |

### Stage 6 — 실제 배포
| TASK | 제목 | 범위 | 선행 | 병렬 충돌 |
|------|------|------|------|------|
| T426 | Cloud Run 배포·XFF 실측·남용 점검 | `docs/status/deploy_2026-10-xx.md`(신규) — 코드 변경 없음 | T423·T425·T436, H4·H7·H11 | 단독 |
| T427 | Netlify 배포·카카오 도메인·화면 확인 | 같은 문서에 절 추가 | T424·T426, H5·H6 | 단독 |

### Stage 7 — 문서
| TASK | 제목 | 범위 | 선행 | 병렬 충돌 |
|------|------|------|------|------|
| T428 | README·상태·가이드 갱신 | `README.md`, `docs/status/2026-10-xx_구현상태.md`(신규), `docs/guides/{SETUP,EVENTS_CATALOG}.md`, `docs/diagram/system-state.html` | T427 | 없음 |
| T429 | 배포 URL 스크린샷 | `docs/demo/s4-0{1..6}-*.png` | T427 | 없음 |

### 스테이지 구성 근거
- **Stage 2**: 공유 인터페이스(`session.py`·`limits.py`·설정·`app.state`·미들웨어 순서·`session_from_request`·카탈로그 동시성)를 T409 가 먼저 만들어 2b 의 두 태스크가 서로의 파일에 기대지 않는다. 프론트는 §5.1 계약만 알면 되므로 2a 병렬.
- **Stage 3**: 25개 구 수집은 병합 블로킹(T416)과 검색 색인(T433) 없이는 시간(병합 수십 분)·메모리(검색 자식 약 413MiB)가 감당되지 않으므로 그 뒤 T418.
- **Stage 4**: TourAPI 는 수집이 없어져 "클라이언트(T419) → 묶음 연결(T434) → 화면(T435)" 의 얇은 경로가 됐다. T417 과 T435 가 `i18n` 을 같이 고치므로 T435 는 4b. T434 는 Stage 2 의 `chat.py` 변경(T411) 뒤에 같은 파일을 고친다(다른 스테이지). 실확인(T422)은 4c.
- **Stage 5**: 이미지 데이터가 T418·T422 산출물에 걸려 Stage 4 뒤. 네 태스크의 파일이 겹치지 않는다(`chat.py` 는 T436 만).
- **Stage 6·7**: 계정이 필요한 일, 그 뒤 문서.

---

## 5. 태스크별 상세 구현 명세

### 5.1 Stage 2 공통 계약 (T409~T413)

| 항목 | 값 |
|---|---|
| 세션 발급 | `POST /api/session` → 201 `{"session": "<43자>", "ttl_s": 7200}` |
| 세션 헤더 | `X-KC-Session` — `^[A-Za-z0-9_-]{43}$`, 틀린 형식은 "없음" |
| 세션 해석 | `backend/session.py::session_from_request(request) -> Session | None`(T409). 공개 모드: 헤더 → `store.get`. 로컬 모드: 유효하고 찾으면 그 세션, 아니면 `store.local()` |
| 세션 없음/만료 | 공개 모드: `POST /api/messages` → 401 `no_session`, `GET /api/messages`·`GET /api/audit` → `[]` |
| 제한 초과 | 429 `rate_limited` + `Retry-After` |
| 동시 처리 초과 | 429 `busy` |
| 일일 상한 | 503 `daily_limit` |
| 닫힌 API | 403 `disabled_in_public` |
| 메타 | `GET /api/meta` → `{"schema":"kc-meta/v1","public":bool,"decisions":"open"|"closed","reports":"open"|"closed"}` |
| 미들웨어 | 순서: `_limit_body` → `_rate_limit` → GZip(`starlette.middleware.gzip.GZipMiddleware`, `minimum_size=1024`) → **CORS(마지막 = 가장 바깥)** |
| CORS | `allow_headers=["Content-Type","X-Admin-Token","X-KC-Session"]`, `expose_headers=["X-Audit-Skipped","Retry-After"]` |
| API 문서 | 공개 모드: `docs_url=None`, `redoc_url=None`, `openapi_url=None` |
| 설정(env) | `KC_PUBLIC_MODE` · `KC_TRUSTED_PROXY_HOPS`(**기본 없음** — 비어 있으면 IP 제한 끔, 값은 1~3) · `KC_LLM_DAILY_UNITS`(기본 300) · `KC_STORY_CONCURRENCY`(1~8, 기본 2) · `KC_CATALOG_CONCURRENCY`(1~8, **기본 2**) · `KC_SESSION_TTL_S`(7200) · `KC_SESSION_MAX`(1000). 범위 밖이면 서버 시작 실패 |

#### T409 — backend 세션·제한 기반 + 설정 + 미들웨어 순서 + gzip + 메타 + 카탈로그 동시성
- **변경 파일**: §4 표.
- **인터페이스**:
  ```python
  # backend/session.py — core 만 import (D3·D10)
  TOKEN_RE; SESSION_HEADER = "X-KC-Session"; LOCAL_SESSION_ID = "local"
  @dataclass
  class Session:
      id: str; created: float; last_seen: float
      history: deque  # maxlen=100, (message dict, in_llm_context: bool)
      logs: deque     # maxlen=200
      seq: int = 0
      busy: threading.Lock; lock: threading.Lock
      tourapi_calls: int = 0; tourapi_day: date | None = None   # D29 ⑤ 세션당 하루 10회(T434 가 사용)
  class SessionStore:
      def __init__(self, *, ttl_s: float, max_sessions: int, clock=time.monotonic): ...
      def create(self) -> Session | None; def get(self, token) -> Session | None
      def local(self) -> Session; def __len__(self) -> int
  def session_from_request(request) -> Session | None
  # backend/limits.py
  @dataclass(frozen=True)
  class Rule: name: str; limit: int; window_s: int; scope: Literal["ip", "session", "global"]
  RULES: dict[str, tuple[Rule, ...]]   # §6.2 표
  class RateLimiter:
      def hit(self, bucket: str, keys: Mapping[str, str | None], rules) -> int | None
      # keys = {"ip": <ip 또는 None>, "session": <id 또는 None>, "global": "all"}; 키가 None 인 scope 의 규칙은 건너뛴다
  class DailyBudget:
      def __init__(self, units: int, *, today: Callable[[], date]): ...
      def reserve(self, n: int) -> bool; def refund(self, n: int) -> None; used: int
  class AdminGuard: blocked(ip) / fail(ip) / ok(ip)
  def client_ip(request, trusted_hops: int | None) -> str | None
      # hops None → None(IP 제한 끔). XFF 길이 < hops 이거나 IP 형식 아님 → None(폴백도 IP 제한 끔, D24 ④)
  def classify(path: str, method: str) -> str | None
  # backend/catalog_runner.py
  class CatalogBusy(CatalogRunnerError): ...
  def configure_concurrency(n: int) -> None
  ```
  - `Settings`: §5.1 env 필드 전부(`trusted_proxy_hops: int | None = None`).
  - `app.py` 순서: ① `FastAPI(..., docs_url/redoc_url/openapi_url = None if public)` ② `app.state.sessions/limiter/budget/admin_guard`, `configure_concurrency(s.catalog_concurrency)` ③ `_limit_body` ④ `_rate_limit`(공개 모드에서만) ⑤ `GZipMiddleware` ⑥ **마지막에 CORS**. `_forbidden` 처리기는 `getattr(exc, "code", "forbidden")`. `ROUTERS` 에 `meta.router`(`GET /api/meta`, `POST /api/session` — `create()` None 이면 429 `busy`).
- **핵심 로직**: 고정 창 `{(bucket, rule.name, key)}` + Lock, 1,000번에 한 번 만료 정리. 토큰은 로그에 sha256 앞 8자만. `DailyBudget` 날짜는 KST.
- **엣지 케이스**: hops 미설정 → IP 규칙 전부 건너뜀(세션·전역만). units 0 → LLM 전부 503. 로컬 모드 `_rate_limit` 통과. gzip 은 이미 압축된 응답·작은 응답 건너뜀(starlette 기본).
- **지켜야 할 규칙**: D24 ①~⑤ · D27 ③ · D3·D10 · 규칙 1.
- **DoD**: `test_kc4_session.py`, `test_kc4_limits.py`(창 경계·Retry-After·KST 리셋·refund 하한·`client_ip` hops None/1/2/짧은 XFF/위조 형식→None·IP 규칙 건너뜀·전역 규칙 적용·설정 범위), `test_kc4_app_middleware.py`(공개 모드 **429 응답에 `Access-Control-Allow-Origin`**, **413 응답에도**, preflight `X-KC-Session`, `/docs`·`/openapi.json` 공개 모드 404·로컬 200, `Accept-Encoding: gzip` 이고 1KB 넘는 응답이 `Content-Encoding: gzip`, `CatalogBusy` 가 동시 2 초과에서 발생). 전체 회귀.
- **병렬 충돌**: 없음.

#### T410 — 프론트 세션·제한 오류·배포 주소 설정
- 확정 1판과 같다. 요점: `src/lib/api-base.js::configuredBase`(같은 출처 경로 또는 `https:` 절대 URL만), `http.js` 세션(`sessionStorage` `kc.session`, 401 한 번 재시도, 오류 문구 `rate_limited`·`daily_limit`·`disabled_in_public`·`no_session`, `getMeta()`), `index.js`·`events/api.js` 기본 주소가 `configuredBase()` 우선, **`events.html`·`admin.html` 에 `<script src="config.local.js"></script>` 를 모듈 앞에 추가**(원본 CSP 문자열 불변 — 배포 원점은 T424 가 `dist/` 에만), `approve-buttons.js` 승인 닫힘 문구, `config.local.example.js` 에 `KC_API_BASE`.
- **DoD**: `node --test` 통과 — 토큰 저장·재사용, 401 재시도 1회, 429 문구, `configuredBase` 허용·거부표, 승인 닫힘, mock 무변화, 두 HTML 의 스크립트 순서, 기존 `events.security.test.js` 통과.
- **병렬 충돌**: 없음.

#### T411 — 채팅 세션 분리·동시 처리·일일 상한
- 확정 1판과 같다. 요점: `send(text, context, *, session)`, 세션 history 로만 LLM 맥락, `BoundedSemaphore(story_concurrency)`, 세션 `busy`, `DailyBudget` 예약 2·환불(`2 - min(attempts,2)`)·일반 챗봇 1, `ContextVar` 로 요청별 audit 수집(`mark/since` 제거), `_search_events(args, timeout_s)`, `CatalogBusy` 는 행사 검색 실패 경로(`EVENTS_UNAVAILABLE`), 라우터는 `session_from_request` 만 사용.
- **DoD**: 세션 간 비노출·LLM 맥락 분리·동시 요청 로그 비섞임·슬롯·예산 테스트, 기존 `test_kc3_chat_*`·`test_kc3_e2e_chat.py` 통과(기대값 변경 금지), `eval/kc.py run --check` 0.

#### T412 — 공개 모드 보안 로그·승인·관리자·제보
- 확정 1판과 같다. 요점: 공개 모드 `GET /api/audit` 은 세션 logs 만, decision·admin·reports 403 `disabled_in_public`(`Forbidden.code`), 로컬 모드 관리자 실패 5회 → 15분 차단(**IP 를 읽지 못하면(None) 차단 키는 `"unknown"` 하나** — 로컬 모드 전용이라 영향 작음), `_call` 에서 `CatalogBusy` → 429 `busy`.
- **DoD**: `test_kc4_public_mode.py` + 기존 `tests/backend/*`.

#### T413 — 공개 모드 통합 테스트·로컬 공개 모드
- 확정 1판과 같다. 테스트에 추가: ⑧ `KC_TRUSTED_PROXY_HOPS` 미설정이면 IP 규칙이 걸리지 않고 세션 규칙(30회/일)과 전역 규칙이 걸린다 ⑨ 응답 gzip.
- **DoD**: 테스트 통과, `kc_demo.sh --check`·`--smoke`·`--public --smoke` 0, 전체 회귀.

#### T414 — 지역 파일 21개 + 기존 지역 테스트 fixture 전환
- 확정 1판과 같다(서울시 공식 자치구 목록에서 이름·영문 표기, `keywords` 는 구 이름 하나, `sillok_keywords` 빈 목록, `test_kc_regions.py:31` 은 기대값 유지·`tests/fixtures/regions4/` 로 전환).
- **DoD**: `load_regions()` 25개, 기존 4개 파일 git diff 0, `test_kc_regions.py` 통과(단언 동일), 전체 회귀.

#### T415 — 실록 키워드 측정·자동 후보 도구
- 확정 1판과 같다(`count`·`places`·`candidates` 하위 명령, 독음 표는 Unicode Unihan `kHangul`, 구별 행정동 목록은 서울 열린데이터광장 데이터셋 — 출처·이용 조건을 `docs/spikes/sillok_candidates.md` 에, 받은 파일은 `var/data/`). 도구는 지역 파일을 고치지 않는다. 입력 데이터를 못 구하면 `candidates` 는 문서만, `count`·`places` 는 완료.

#### T416 — 카탈로그 25개 구: 전체 별칭·쪽 상한·월 버킷 병합 블로킹
- 확정 1판과 같다. 근거 계측(2,000건 4.9초 → 3만 건 약 18분)과 T408 실측(서울 총 19,586행 → 25개 구 관찰값 약 19,600)을 함께 적는다. `fetch_rows(max_pages=60)` + 상한 초과 시 수집 실패. `_group` 은 상한 없는 월 버킷(`m:YYYY-MM`) + 외부 id 키(`id:…`), 후보는 그룹 생성 순, 동등성 근거·300개 테스트(긴×짧은 기간·기간 밖·날짜 없음±외부 id·같은 체계 다른 id·달 경계·세션 날짜만·demo 섞임). `kc_demo.sh` 는 `KC_DEMO_REGIONS`(기본 4개 구).

#### T433 — 행사 검색 색인: 변환 건수 축소, `excluded` 보존
- **출처**: Sprint 3 이월(검색 6초), T407 결론(병목 `entry_from_dict` 87%, `excluded` 직렬화 0.1% — 계약을 바꿀 이유 없음).
- **변경 파일**: §4 표.
- **설계 — 변환을 후보에만**: 검색 판정의 앞 세 조건(`demo` 는 제외)은 요청과 무관하다 — `in_target != yes`(사유 2종), 취소, 종료(`query.py:162~171`). 색인을 만들 때 이 조건으로 빠지는 항목은 **`entry_from_dict` 없이** `{pos, id, title, reason}` 만 남기고, 나머지(후보 — 25개 구 추정 약 360건 + demo + 연기·미상)만 전체 dict 로 저장한다. 검색 경로는 색인 파일 하나를 `json.loads` 하고 **후보만** `entry_from_dict` 한다(8,719 → 수백 회). 사전 제외 항목은 저장된 사유를 그대로 쓴다.
- **A안(`excluded` 순서까지 보존)과 양립**: 사전 제외 항목과 루프에서 생긴 제외 항목에 원래 순번(`pos`)이 있어, `search_events` 가 끝에서 순번으로 병합하면 전체 경로와 같은 순서·같은 사유 문자열이 나온다. 사유 문자열은 `query.py` 상수(`REASON_NOT_IN_TARGET`·`REASON_TARGET_UNKNOWN`·`REASON_CANCELLED`·`REASON_ENDED` — 값 변경 금지)를 색인 생성과 검색이 공유한다. "종료"는 시간이 지나도 종료이므로 `now_search >= indexed_at` 이면 같다. 따라서 **계약 변경 없음**(`docs/chat-bundle.contract.md`·행사 화면 무변경).
- **인터페이스**: `search_events(entries, request, *, now, coverage=None, positions=None, pre_excluded=None)` — `positions` 는 후보의 원래 순번, `pre_excluded` 는 `[(pos, {"id","title","reason"})]`. `store.py`: `SEARCH_INDEX="search_index.json"` `{"schema":"kc-search-index/v1","built_at","indexed_at","total","candidates":[{"pos","entry"}],"pre_excluded":[{"pos","id","title","reason"}]}`, `save_search_index`, `load_search_index`, `save_entries` 끝에서 자동 생성. `api._search`: 색인이 유효하면(schema·`built_at` 일치·`now >= indexed_at`) 색인 경로, 아니면 전체 경로. **커버리지용 `entries_built_at()` 재파싱을 없앤다** — 색인 경로는 색인의 `built_at` 을 쓴다(전체 경로도 이미 읽은 dict 에서 꺼내도록 고친다). `__main__.py reindex`.
- **엣지 케이스**: 색인 없음·schema 다름·`built_at` 불일치·`now < indexed_at`·파일 깨짐 → 전체 경로(조용한 폴백, 경고 로그). demo 항목은 항상 후보(`include_demo` 가 요청 값이라).
- **지켜야 할 규칙**: D13 ⑤ · D23 · D10 · 계약 불변.
- **DoD**: ① `test_kc4_search_index.py`: 합성 항목(대상 밖·미확인·취소·종료·진행·종료일 없음 1년 초과/이내·연기·demo)으로 **전체 경로와 색인 경로의 결과 dict 가 같음 — `events`·`counts`·`excluded`(순서까지)·`coverage`**, `include_demo` 참/거짓 둘 다, 폴백 5종, 후보만 변환됨(`entry_from_dict` 호출 수 monkeypatch 로 셈). ② 실제 `var/catalog` 에서 `reindex` 뒤 데모 문장 검색 결과를 변경 전과 diff(커밋 안 함) — 같아야 함, 시간 3회 중앙값(목표 ≤ 1.5초). ③ 행사 화면 "제외된 항목 n건 보기" n 이 변경 전과 같음(헤드리스 또는 수동 기록). ④ 전체 회귀.
- **병렬 충돌**: 없음.

#### T418 — 실행: 25개 구 수집·색인(선택)·스냅샷·2차 측정
- **수행자**: 코디네이터. dev 는 명령·문서 틀 준비.
- **순서**:
  1) (선택, H3) 자동 후보 → 사람이 고른 키워드 → 색인 재구축(`kcontext.new.db`) → 크기·이미지 0.5GiB 관점 확인 후 교체. 없으면 4개 구 색인 유지.
  2) 25개 구 서울 API: `KC_CATALOG_DIR=var/catalog.all KC_TARGET_REGION=all … update --source seoul_openapi` → `reindex`. 병합 시간 기록. **로컬 `var/catalog`(4개 구)는 별도 유지.**
  3) 로컬 4개 구 갱신 → 스냅샷 재생성(D19).
  4) **2차 측정**(같은 문서 "2차" 칸): `measure_seoul_rows.py --full`(**구별 수·끝나지 않은 행·좌표 있는 행**, `truncated`) · `measure_runtime.py --catalog var/catalog.all`(검색 자식 최대 RSS·시간, backend + 검색 2건 동시 합계, 파이프라인 캐시 적중) · **`--with-llm` 으로 LLM 경로 파이프라인 RSS 1회** · 확정 `--memory`(D27 ③ 공식) 와 카탈로그 동시성 2 유지/1 로 낮춤 판정. 실제 서버(`var/catalog.all`)에서 데모 문장 + 새 구 문장 2개.
- **호출 상한**: 서울 API — 수집 2회 실행(25개 구·4개 구) 각 20쪽 + 재시도 여유 = **≤ 50**, 2차 측정 `--full` **≤ 30**. NVIDIA — `--with-llm` 1회 + 실서버 확인을 캐시 적중 문장 위주로 해서 **≤ 2**.
- **DoD**: `docs/status/seoul25_*.md`(구별 행사 수·병합 시간·검색 시간·색인 크기·실서버 3문장), 측정 문서 2차 칸 전부, 스냅샷 크기(5MB 넘으면 사람 확인), 회귀 + `kc_demo.sh --check` 0.

#### T419 — TourAPI 실시간 클라이언트 (backend 전용, 저장 없음)
- **위치 결정 — (a) backend 전용 모듈 `backend/tourapi_live.py`**:
  - 이유 1: 키(`DATA_GO_KR_SERVICE_KEY`)가 backend 프로세스에만 있고, 에이전트 역할 자식 프로세스(`APP_PROCESS_ROLE=agent`)로 가지 않는다(D7 ③·D29 ①). (b) 자식 프로세스 방식이면 매 요청마다 키를 자식 env 로 넘겨야 한다.
  - 이유 2: 정규화·병합을 하지 않는 얇은 HTTP 클라이언트라 도메인 로직이 없다 — `domains` 를 import 할 필요가 없다(D3·D10 그대로).
  - 이유 3: 요청당 1회·5초 한도라 자식 프로세스 기동 비용(약 0.14초)·메모리를 아낄 수 있다.
  - 구 코드표는 데이터 파일 `backend/fixtures/tourapi_codes.json`(T401 ⑦ 25개 구, 출처·확인일 포함) — `schedule_gate` 가 `backend/fixtures/chat_places.json` 을 읽는 것과 같은 방식.
- **변경 파일**: §4 표.
- **인터페이스**:
  ```python
  # backend/tourapi_live.py — httpx·표준 라이브러리·core 만
  BASE = "https://apis.data.go.kr/B551011/KorService2"
  KEY_ENV = "DATA_GO_KR_SERVICE_KEY"
  SHOW_FIELDS = ("contentid", "title", "addr1", "addr2", "eventstartdate", "eventenddate",
                 "tel", "progresstype", "lDongSignguCd", "cpyrhtDivCd")   # T401 ⑩ 확정 필드 중 화면용(이미지·좌표 제외)
  ATTRIBUTION = {"Type3": "출처: 한국관광공사 TourAPI · 공공누리 제3유형(변경금지)",
                 "Type1": "출처: 한국관광공사 TourAPI · 공공누리 제1유형(출처표시)"}
  SOURCE_PAGE = "https://www.data.go.kr/data/15101578/openapi.do"
  @dataclass(frozen=True)
  class LiveResult:
      status: Literal["ok", "unavailable"]
      reason: str | None          # "no_key" | "limit" | "timeout" | "http" | "gateway:<returnReasonCode>" | "result:<resultCode>" | "bad_shape"
      items: tuple[dict[str, str], ...]   # SHOW_FIELDS 만, 값은 응답 문자열 그대로
      total: int | None
  class TourApiLive:
      def __init__(self, *, key_lookup: Callable[[], str | None], client: httpx.Client | None = None,
                   timeout_s: float = 5.0, daily_calls: int = 300, today: Callable[[], date] = kst_today): ...
      def festivals(self, *, date_from: str, date_to: str, signgu: str | None = None,
                    rows: int = 20) -> LiveResult     # date_* 는 YYYY-MM-DD 입력 → 요청 파라미터 YYYYMMDD
  ```
  요청 파라미터(T401 ⑩ 만): `serviceKey`, `MobileOS=ETC`, `MobileApp=KContext`, `_type=json`, `numOfRows`, `pageNo=1`, `eventStartDate`, `eventEndDate`, `lDongRegnCd=11`, (선택) `lDongSignguCd`, `arrange=A`.
- **핵심 로직**:
  1) 전역 일일 상한(`DailyBudget` 재사용 아님 — 이 모듈 안 카운터, KST 날짜 리셋, 스레드 Lock)을 먼저 확인 → 초과면 `unavailable/limit`(호출 안 함).
  2) 키: `key_lookup()`(셸 env → `.env` 허용 목록, `core.llm.envfile`) 없음 → `unavailable/no_key`. 키에 `%` 가 있으면 그대로, 없으면 `urllib.parse.quote(safe="")` 한 번(T401 ④) — 쿼리 문자열을 직접 조립해 httpx 가 다시 인코딩하지 않게 한다.
  3) `httpx` GET, 시간 한도 5초. 예외 → `timeout`/`http`. 상태 ≠ 200 → `http`.
  4) JSON 파싱 실패 → `bad_shape`. **최상위에 `OpenAPI_ServiceResponse` 가 있으면 `cmmMsgHeader.returnReasonCode` 로 `gateway:<코드>`**(키 오류가 HTTP 200 으로 옴). 최상위가 `response` 가 아니면 `bad_shape`. `response.header.resultCode != "0000"` → `result:<코드>`.
  5) `body.items` 가 빈 문자열·None·`{}` → 0건. `items.item` 이 **dict 이면 1건 리스트로**, 리스트면 그대로, 그 밖 → `bad_shape`.
  6) 각 item 에서 `SHOW_FIELDS` 만 골라 **값을 문자열 그대로**(`str` 이 아니면 그 필드 생략). `lDongRegnCd != "11"` 인 항목은 버린다(서울 질의 응답 확인 — 값은 안 바꿈). 정렬·날짜 변환 없음.
  7) 로그·audit 에는 `status·reason·건수·소요 시간`만(요청 URL·키·원문 없음).
  8) 결과를 어디에도 저장하지 않는다(모듈 상태는 호출 수 카운터뿐).
- **엣지 케이스**: `totalCount` 가 숫자 문자열이 아니면 `total=None`. 응답이 32MiB 등 비정상으로 크면 httpx 읽기 상한(1MB) 초과 → `bad_shape`. 서울 구 코드가 표에 없으면 `signgu=None`(서울 전체).
- **지켜야 할 규칙**: D29 ①②④⑤⑥ · D3·D10 · 규칙 1 · `tourapi.md` ⑩ "쓰지 말 것 목록".
- **DoD**: `test_kc4_tourapi_live.py`(`httpx.MockTransport`): 정상 리스트 · **item 이 객체 1건** · 0건(`items` 빈 값) · `cmmMsgHeader`(코드 20·30) HTTP 200 · `resultCode` ≠ 0000 · 비 JSON · 시간 초과 · 키 없음(호출 안 함) · 일일 상한(호출 안 함, KST 리셋) · 키 인코딩(`%` 있음/없음 — 이중 인코딩 없음) · **오류 메시지·로그에 키·URL 문자열 없음**(caplog 검사) · 값 불변(입력 문자열과 출력 문자열 동일) · 서울 밖 항목 제외. 합성 fixture 는 T401 이 기록한 구조대로, 값은 `○○`. 전체 회귀.
- **병렬 충돌**: 없음.

#### T417 — 좌표 자동 부착 (서울 API 장소만)
- 확정 1판의 T417 에서 **입력을 서울 API 하나로 고정**한다: `places_build --catalog <dir> --rules … --out var/places/auto_places.json --collected-at …` (`--sources`·`--tourapi-attractions` 인자 없음). 이상치는 같은 GUNAME 좌표 중앙값에서 `max_gu_dist_km`(8) 초과, 구 없음·구 표본 3개 미만 제외, 같은 이름 150m 모호 제외, 사람 사전 우선, `COORD_AUTO` 문제 코드·프론트 문구. 항목 `origin: ["seoul_openapi"]`.
- **DoD**: `test_kc4_places_auto.py`(구 중앙값 이상치·모호·사람 우선·구 없음·표본 부족·자동 파일 깨짐 경고·`COORD_AUTO`), `coordauto.kc4.test.js`, 자동 파일 없을 때 기존 결과 불변, 전체 회귀.

#### T434 — 묶음 연결·계약 `kto_live`
- **변경 파일**: §4 표.
- **계약(§5.2)** 을 `docs/chat-bundle.contract.md` 에 추가한다(D29 로 승인된 계약 변경).
- **핵심 로직**: `chat.py::_story` 에서 `attach_events` 뒤, 묶음 상태가 정상이고 행사 검색 범위(`trip`)가 정해졌을 때만:
  1) 남은 프론트 예산이 8초 미만이면 호출하지 않고 `{"status":"unavailable","reason":"budget"}`.
  2) 세션 하루 10회(`session.tourapi_calls`, KST 날짜 바뀌면 0) 초과 → `reason: "limit"`.
  3) `TourApiLive.festivals(date_from=trip[0], date_to=trip[1])` 를 `asyncio.to_thread` 로(전역 상한·키·오류 판정은 T419). 앵커가 한 구에만 있고 코드표에 있으면 `signgu` 지정, 아니면 서울 전체.
  4) 결과를 `bundle["kto_live"]` 로. **LLM 맥락·세션 history·audit 본문에 넣지 않는다.**
  5) 공개·로컬 모드 모두 같은 동작(로컬에서 키가 없으면 `no_key` → 화면 "지금 확인할 수 없음").
  - `chat_story.py`: `kto_live` 모양 검사(`status` 두 값, `items` 최대 20, 각 값 문자열·200자 이하 — 넘으면 그 항목을 버린다. **값을 자르거나 고치지 않는다**).
  - `TourApiLive` 인스턴스는 `ChatService` 가 하나 들고(전역 상한 공유), `Settings` 의 `KC_TOURAPI_DAILY_CALLS`(기본 300)·`KC_TOURAPI_TIMEOUT_S`(기본 5) 로 만든다 — 설정 필드는 T419 가 추가.
- **엣지 케이스**: 일정 실패·고정 문구 응답에는 `kto_live` 를 붙이지 않는다(필드 없음 = 화면 절 없음). 캐시 적중 일정도 매번 실시간 호출(D29 ② — 재사용 없음).
- **지켜야 할 규칙**: D29 · D17(묶음은 서버에 보관하지 않음) · D24 ③(TourAPI 는 LLM 단위가 아니라 별도 상한) · D3·D10.
- **DoD**: `test_kc4_kto_bundle.py`(가짜 `TourApiLive`): 정상 → 필드 있음, 실패 → `unavailable`, 예산 부족 → 호출 안 함, 세션 10회 초과, 고정 문구 응답엔 필드 없음, LLM 맥락·history 에 TourAPI 값 없음, 200자 초과 항목은 버려지고 나머지 값은 바이트 동일. 기존 `tests/backend/*`·`test_kc3_e2e_chat.py` 통과. 계약 문서 diff 를 reviewer 가 확인.
- **병렬 충돌**: 없음.

### 5.2 `kto_live` 묶음 계약 (T434·T435 공통, D29)
```json
"kto_live": {
  "status": "ok" | "unavailable",
  "reason": null | "no_key" | "limit" | "budget" | "timeout" | "http" | "gateway:<코드>" | "result:<코드>" | "bad_shape",
  "fetched_at": "<서버 시각 ISO, KST>",
  "total": <정수 | null>,
  "items": [ { "contentid": "…", "title": "…", "addr1": "…", "addr2": "…", "eventstartdate": "YYYYMMDD", "eventenddate": "YYYYMMDD", "tel": "…", "progresstype": "…", "lDongSignguCd": "…", "cpyrhtDivCd": "Type3" } ],
  "attribution": { "Type3": "출처: 한국관광공사 TourAPI · 공공누리 제3유형(변경금지)", "Type1": "출처: 한국관광공사 TourAPI · 공공누리 제1유형(출처표시)" },
  "source_url": "https://www.data.go.kr/data/15101578/openapi.do"
}
```
- 필드는 선택이다(없으면 화면 절도 없음). 항목의 값은 응답 문자열 그대로이며 화면도 바꾸지 않는다(날짜 `YYYYMMDD` 를 그대로 보인다 — 라벨은 화면이 붙임).
- `reason` 은 화면에 보이지 않는다(내부 코드). 화면은 `status` 만 본다.
- 좌표(`mapx`·`mapy`)·이미지 필드는 계약에 없다.

#### T435 — 프론트 "한국관광공사 관광정보(원문)" 절
- **변경 파일**: §4 표.
- **인터페이스**: `bundle.js` 의 검증기에 `kto_live` 수용(§5.2 키만 새 객체로 복사, 모르는 키·문자열 아닌 값 버림, `items` 최대 20). `components/ktolive/logic.js` export `ktoView(bundle) -> {state:'none'|'ok'|'unavailable', items:[{fields:[{label, value}], attribution, link}], sourceUrl}` — **값은 그대로**(가공 없음), `label` 은 i18n. `index.js` 는 모듈(`mount(slotEl, ctx)`)로 상태를 구독해 그린다.
- **화면 규칙**: 제목 "한국관광공사 관광정보(원문)" / 영어 "Korea Tourism Organization data (original text)". 항목마다 제목·주소(`addr1`+공백+`addr2`, 각 값 그대로)·기간(`eventstartdate`–`eventenddate` 문자열 그대로)·전화, 항목 아래 출처 문구(`cpyrhtDivCd` 에 맞는 `attribution`, 모르는 값이면 Type3 문구), 절 끝에 "원문 출처 보기" 링크(`source_url`, `rel="noopener noreferrer" target="_blank"`). `unavailable` 이면 "지금 확인할 수 없음" 한 줄. **지도 핀·지도 레이어에 넣지 않고, 서울 API 행사 카드 목록과 섞지 않으며, 이미지를 그리지 않는다.** 텍스트는 `textContent` 로만(HTML 해석 없음).
- **엣지 케이스**: mock 모드 — `src/data/chat-bundle.js` 에 예시를 넣지 않는다(절 없음). 항목 0건이면 "이 기간의 관광공사 행사 정보가 없습니다".
- **지켜야 할 규칙**: D29 ②③ · D17 · 프론트는 표 파일만.
- **DoD**: `ktolive.kc4.test.js`: 값 불변(입력 문자열 = 출력 문자열), 출처 문구 유형별, 링크 속성, `unavailable` 문구, 필드 없음이면 절 없음, 지도 모듈이 `kto_live` 를 읽지 않음(지도 레이어 입력에 없음), `textContent` 사용(스크립트 문자열이 그대로 글자로 보임). 기존 `node --test` 통과.
- **병렬 충돌**: 없음(4b, T417 머지 뒤 i18n).

#### T422 — 자동 좌표 생성·실시간 원문 실확인
- **수행자**: 코디네이터.
- **순서**: ① `places_build --catalog var/catalog.all` → 자동 좌표, 구별 거리 분포를 보고 `max_gu_dist_km` 조정(근거를 `auto_rules.json` note·보고서에). ② 로컬 서버(`var/catalog.all`, 키 있음)에서 데모 문장 + 새 구 문장으로 `kto_live` 확인 — 출처 문구·링크·핀 없음·서울 API 행사와 분리. ③ 키를 일부러 비운 서버로 "지금 확인할 수 없음" 확인. ④ `catalog_sources.json` 의 `tourapi_kto` 를 `status: "live_display_only"`·notes(D29: 수집 없음, 실시간 원문 표시) 로 갱신.
- **호출 상한**: TourAPI ≤ 10, NVIDIA 는 캐시 적중 문장 위주로 ≤ 2.
- **DoD**: `docs/status/events_data_2026-10-xx.md`(자동 좌표 수·버린 사유별 수·실시간 절 확인 결과), 회귀 + `kc_demo.sh --check` 0.

#### T423 — Dockerfile·이미지 데이터·컨테이너 설정
- 확정 1판과 같고 아래만 바뀐다.
  - 이미지 데이터: 카탈로그 = `snapshot_catalog.py --from var/catalog.all --to image-data/catalog --keep-ended`(서울 API 유래만) + `reindex`. 자동 좌표 = `origin == ["seoul_openapi"]` 항목만. **TourAPI 데이터는 없다(수집 자체가 없음)**. 전체 이미지 크기를 출력하고 **0.5GiB 를 넘으면 경고**(D28 ④).
  - `entrypoint.sh`: `KC_PUBLIC_MODE=${KC_PUBLIC_MODE:-1}`, `KC_TARGET_REGION=${KC_TARGET_REGION:-all}`, 쓰기 경로는 `/tmp/kc`, `KC_TRUSTED_PROXY_HOPS` 는 **기본값을 넣지 않는다**(배포 env 로만). `exec uvicorn backend.app:app --host 0.0.0.0 --port "${PORT:-8080}" --workers 1`.
  - 빌드 플랫폼 `linux/amd64`(T402 §6).
- **DoD**: `test_kc4_container_files.py`(`.dockerignore`·Dockerfile 에 키 없음·entrypoint·`.gitignore` 에 `image-data/`·`dist/`·entrypoint 에 hops 기본값 없음), `test_kc4_image_data_filter.py`(서울 API 유래만·`web` 0·키 파라미터 없음·끝난 행사 보존·좌표 `origin` 필터). docker 있으면 빌드·키 없이 `/api/meta` 200·이미지 크기 기록.

#### T424 — Netlify 설정·빌드 스크립트 (직접 CORS)
- **직접 CORS 만 구현한다**(T403 결론). 프록시 리라이트·`_redirects` 코드는 만들지 않는다.
- `scripts/netlify_build.sh`: ① `frontend/k-context` → `dist/`(`tests/`·`admin.html`·`config.local.js`·`README.md` 제외) ② `dist/config.local.js` = `window.KC_KAKAO_JS_KEY` + `window.KC_API_BASE = KC_BACKEND_ORIGIN + '/api'`(`KC_BACKEND_ORIGIN` 은 `^https://[A-Za-z0-9.-]+$`, 카카오 키 형식은 `kakao_domain.md` 확인값, 틀리면 빌드 실패) ③ `dist/events.html` meta CSP `connect-src` 에 `KC_BACKEND_ORIGIN` 추가(원본 불변) ④ `index.html` CSP 는 강제하지 않음(넣으면 `_headers` 의 Report-Only) ⑤ 값은 로그에 길이만. 운영 컨텍스트에서만 `KC_BACKEND_ORIGIN` 이 의미 있다 — 미리보기에서는 같은 값이어도 CORS 에서 거부된다(D27 ②, 의도).
- **DoD**: `test_kc4_netlify_build.py` — `dist/` 구조, `admin.html` 없음, `config.local.js`, `events.html` CSP 원점, `index.html` 강제 CSP 없음, 잘못된 값 실패, 출력에 값 없음, 원본 불변.

#### T425 — Cloud Run 배포 스크립트·가이드
- 확정 1판과 같고 아래가 정해졌다.
  - `--region us-central1`(기본값으로 스크립트에 둠, 인자로 바꿀 수 있음), `--memory 2Gi --cpu 1 --timeout 120 --max-instances 1 --min-instances 0`, `--concurrency` 는 20(앱 동시성 상한이 일정 2·카탈로그 2라 그 이상은 대기만 늘림 — 근거를 가이드에 적고 T426 에서 확인).
  - env: `KC_PUBLIC_MODE=1`, `KC_TARGET_REGION=all`, `KC_CATALOG_CONCURRENCY=2`, `KC_CORS_ORIGINS=<운영 도메인>`, `KC_LLM_DAILY_UNITS`(H7), `KC_TOURAPI_DAILY_CALLS=300`. `KC_TRUSTED_PROXY_HOPS` 는 **첫 배포에서 넣지 않는다**(IP 제한 꺼진 상태) — T426 실측 뒤 `--update-env-vars` 로.
  - 비밀: `--update-secrets=NVIDIA_API_KEY=<이름>:<숫자 버전>,DATA_GO_KR_SERVICE_KEY=<이름>:<숫자 버전>`. 스크립트는 버전 인자 두 개(`--nvidia-secret-version`·`--tourapi-secret-version`)를 **필수**로 받고 `latest` 를 거부한다.
  - `DEPLOY.md`: 비밀 등록(표준입력)·버전 번호 기록, **교체 절차**(새 버전 추가 → 새 버전으로 재배포 → 확인 → 옛 버전 `destroy`), 무료 한도(활성 버전 6개 — 비활성도 셈), 송출량 점검(콘솔에서 월 송출 확인 — 1GiB), `max-instances` 잠깐 초과 한계(D27 ⑧), 이미지 데이터 갱신 절차.
- **DoD**: `--dry-run` 이 계정 없이 0, `latest` 거부 테스트(스크립트 인자 검사), `shellcheck` 있으면 경고 0.

#### T436 — 쓰기 경로(`/tmp`) 크기 상한
- **변경 파일**: §4 표.
- **인터페이스**: `backend/chat.py::_TeeSink` — 공개 모드에서 현재 JSONL 파일이 `KC_AUDIT_MAX_BYTES`(기본 8MiB)를 넘으면 `<run_id>.1.jsonl` 로 이름을 바꾸고(이전 `.1` 은 지움) 새 파일로 이어 쓴다(최대 2개 = 16MiB). 로컬 모드는 지금 그대로. `domains/kcontext/schedule/cache.py::ScheduleCache.put` — 쓰기 뒤 `KC_SCHEDULE_CACHE_MAX_FILES`(기본 500)·`KC_SCHEDULE_CACHE_MAX_BYTES`(기본 32MiB) 를 넘으면 수정 시각 오래된 것부터 지운다. 이 env 둘은 `backend/story_runner.py::_ENV_ALLOW` 에 추가해야 자식에 전달된다 — **`story_runner.py` 도 변경 파일에 포함**.
- **엣지 케이스**: 회전 중 다른 요청의 쓰기 — `_TeeSink` 의 Lock 안에서 회전. 캐시 정리 중 다른 프로세스가 같은 파일을 읽음 — 읽기 실패는 캐시 미적중으로 이미 처리됨(확인 후 테스트).
- **지켜야 할 규칙**: D27 ⑦ · D15 ④(캐시 의미 불변).
- **DoD**: `test_kc4_audit_rotate.py`(경계·2개 유지·로컬 모드 무변화), `test_kc4_cache_prune.py`(개수·바이트 상한·최신 유지), 전체 회귀. (`story_runner.py` 는 §4 표에도 추가로 본다.)

#### T426 — Cloud Run 배포·XFF 실측·남용 점검
- **순서**: ① H4·H7·H11 확인 ② `deploy_cloudrun.sh`(hops 미설정) ③ **XFF 실측**: 진단용 임시 리비전(트래픽 0%, 태그 URL)에 `KC_DEBUG_XFF=1` 같은 코드를 넣지 않는다 — 대신 Cloud Run 요청 로그(`httpRequest.remoteIp`)와 앱이 받은 `X-Forwarded-For` 의 **항목 수와 오른쪽에서 몇 번째가 `remoteIp` 와 같은지**만 비교한다(앱 로그에 XFF 의 항목 수와 일치 위치만 남기는 1회성 확인은 T409 의 `client_ip` 단위 테스트 범위 밖이므로, 로그 비교로 안 되면 사람에게 보고하고 IP 제한은 끈 채 둔다). 브라우저(직접 CORS) 경로로 측정. 일치 위치가 일관되면 `KC_TRUSTED_PROXY_HOPS` 를 그 값으로 `--update-env-vars`. ④ 점검 표: `/api/meta`·`/docs` 404·세션 분리·세션 제한 31번째 429·CORS 헤더·gzip·admin/decision/reports 403·데모 문장 응답 시간·`kto_live` 절(출처·링크)·콜드 스타트·최대 메모리·로그에 키·토큰 없음·`describe` 출력에 비밀 값 없음·하루 송출량 추정(응답 바이트 × 예상 요청).
- **호출 상한**: NVIDIA ≤ 10, TourAPI ≤ 10.
- **DoD**: 모든 행 결과, hops 결정(또는 "IP 제한 끔 유지" 와 이유), 실패 행 원인·조치.

#### T427 — Netlify 배포·카카오 도메인·화면 확인
- 확정 1판과 같고(프록시 분기 삭제) 확인 항목에 **"한국관광공사 관광정보(원문)" 절**(출처 문구·링크·핀 없음)과 미리보기 도메인에서 API 가 거부되는 것(의도)을 더한다.

#### T428 — README·상태·가이드 갱신
- 확정 1판과 같고 아래를 더한다: TourAPI 는 "실시간 원문 표시(D29) — 저장·병합·핀 없음, 공공누리 제3유형", 리전 us-central1(지연), IP 제한은 실측 결과에 따름, 알려진 한계(D24 ⑥ 캐시 공유, D27 ⑧ 인스턴스 잠깐 초과, 소프트 상한 재시작 초기화, 송출 1GiB).

#### T429 — 배포 URL 스크린샷
- 장면: ① 첫 화면 ② 데모 문장 결과 ③ 새 구 문장(자동 좌표 문구) ④ **한국관광공사 관광정보(원문) 절** ⑤ 보안 로그(날짜·승인 닫힘) ⑥ 제한 초과 안내.

---

## 6. 비용·남용 방지 기준

### 6.1 외부 호출 상한
| 대상 | 런타임(공개 서비스) | 이번 스프린트 개발·확인 | 근거·비고 |
|---|---|---|---|
| NVIDIA 추론 | **하루 300 단위**(`KC_LLM_DAILY_UNITS`). 메모리 기반 소프트 상한 — 재시작 시 0. 실제 상한은 크레딧(H7) | T418 ≤ 2 · T422 ≤ 2 · T426 ≤ 10 · T427 ≤ 6 · **합계 ≤ 20** | D15 일정 흐름 최대 2회 |
| NVIDIA — 평가 | — | `eval/kc.py validate`·`run --check` 는 **LLM 을 부르지 않는다**(매 게이트). `eval/kc.py stability` 는 이번 계획에 없고, 요청 시에만 1회 ≤ 210 | |
| **TourAPI(D29)** | **전역 하루 300회**(`KC_TOURAPI_DAILY_CALLS`, 메모리 기반 소프트) · **세션 하루 10회** · 요청당 ≤ 1회 · 5초 | T419 테스트는 모의 전송(0회) · T422 ≤ 10 · T426 ≤ 10 · T427 ≤ 5 · **합계 ≤ 25** | 개발계정 1,000건(단위 일일 추정). 개발·확인용 여유와 재시작 초기화를 감안해 3할 |
| 서울 열린데이터광장 | **0회**(키 주입 안 함) | T415 행정동 목록 ≤ 5 · T418 수집 ≤ 50 + 2차 측정 `--full` ≤ 30 | 총 19,586행 = 20쪽 |
| Tavily | 0회 | 0회 | 이월 |
| Cloud Run | `max-instances 1`(잠깐 초과 가능)·`min-instances 0`·us-central1 | — | 무료: 요청 200만·vCPU 180,000초·360,000 GiB-초·**북미발 송출 1GiB/월** |
| 송출량 | gzip 압축. 묶음 events 약 233KB·검색 응답 1.38MB(압축 전) | T426 에서 압축 후 바이트 실측 → 월 1GiB 대비 요청 수 환산 | 넘을 기미면 사람에게 보고(묶음 필드 다듬기는 이월 항목) |
| Secret Manager | 활성 버전 ≤ 6(비밀 2개 × 교체 시 일시 2버전 = 최대 4) | — | 옛 버전 destroy |
| Artifact Registry | 이미지 ≤ 0.5GiB 목표 | — | D28 ④ |

### 6.2 요청 제한 (공개 모드, `backend/limits.py::RULES`)
| 규칙 키 | 대상 | scope | 한도 |
|---|---|---|---|
| `session_create` | `POST /api/session` | ip(hops 설정 시) | 10회/시간 |
| `session_create` | 〃 | global | 600회/시간 |
| `messages` | `POST /api/messages` | ip(hops 설정 시) | 5회/분 · 40회/일 |
| `messages` | 〃 | session | 3회/분 · 30회/일 |
| `messages` | 〃 | global | 30회/분 |
| `events` | `/api/events/*` | ip(hops 설정 시) / session / global | 20회/분 / 20회/분 / 120회/분 |
| `read` | 그 밖의 `GET /api/*` | ip(hops 설정 시) / global | 60회/분 / 600회/분 |
| `reports`·`admin` | — | — | 공개 모드에서 닫힘(403) |
| 동시 처리 | 일정 흐름 / 카탈로그 자식 | 인스턴스·세션 | 2·1 / **2** |
| 일일 | LLM 단위 / TourAPI | global (+ TourAPI session 10) | 300 / 300 |

- **IP 를 믿을 수 없을 때(hops 미설정·폴백)** ip 행은 적용하지 않는다(D24 ④). 세션은 새로 만들 수 있으므로 비용은 **전역 행과 일일 상한**이 막는다.
- 숫자는 보수적 시작값이다. T426 실측으로 사람이 조정하고, 조정은 `limits.py` 표 한 곳만 바꾼다.

---

## 7. 스테이지 게이트

### 7.1 공통 — "로컬 데모 동작 유지"
| 확인 | 명령(레포 루트) | 기준 |
|---|---|---|
| pytest | `uv run python -m pytest -q` | 통과, 건수 직전 이상 |
| 린트 | `uv run ruff check .` | 통과 |
| 프론트 | `(cd frontend/k-context && node --test)` | 통과, 건수 직전 이상 |
| 평가(LLM 없음) | `uv run python eval/kc.py validate` · `uv run python eval/kc.py run --check --known-failures eval/BASELINE.md` | 0 · 0 |
| 데모 | `bash scripts/kc_demo.sh --check` · `--smoke` | 0 |
| 데모 확인 | 로컬(기본 4개 구)에서 데모 문장 "10/15에 창덕궁 10시, 익선동 2시, 숙소는 종로3가야" → 일정 3개·실록 언급·행사, `?api=mock` 그대로 | 사람 또는 헤드리스 기록 |
| reviewer | 스테이지 diff 검토 | PASS |

### 7.2 스테이지별 추가 확인
| 게이트 | 추가 확인 | 의도된 변화(실패로 보지 않음) |
|---|---|---|
| Stage 2 | `--public --smoke` 0, 공개 모드 E2E, 429·413 CORS 헤더, gzip, hops 미설정 시 IP 규칙 미적용 | 로컬에서도 새 탭 = 새 대화 |
| Stage 3 | 검색 결과 동등(`excluded` 순서 포함)·행사 화면 n 동일, 병합 블로킹 동등, T418 2차 측정 | — |
| Stage 4 | TourAPI 클라이언트·묶음·화면 테스트, T422 보고서 | 일정 결과에 "한국관광공사 관광정보(원문)" 절(키 없으면 "지금 확인할 수 없음"), `COORD_AUTO` 문구 |
| Stage 5 | 컨테이너·이미지 필터·빌드 스크립트·`/tmp` 상한 테스트, dry-run, 이미지 크기 | — |
| Stage 6 | T426·T427 점검 표 전 항목 | — |
| Stage 7 | 문서 링크 | — |

---

## 8. 이월 흡수 표 (Sprint 3 → Sprint 4)
| 출처(sprint-3) | 항목 | 이번 처리 |
|---|---|---|
| Stage 5 이월 | 행사 검색 1회 약 6초 | T407(완료) → **T433** |
| Stage 6 이월 | 보안 로그 날짜·순서 | **T406**(완료) |
| Stage 4 이월 | 캐시 키 today 불일치 | **T405**(완료) |
| Stage 2 이월 W7 | 캐시 키 `LLM_BACKEND*` | **T405**(완료) |
| Stage 5 이월 | 스냅샷 시점 자료 | **T418** |

## 9. 이월 (Sprint 5 후보 · 유지)
| 항목 | 사유 |
|---|---|
| 무료 DB(Postgres) 보존 (SCOPE 선택) | DB 드라이버가 새 런타임 의존성 — 결정·예외 먼저 |
| 서울 행사 하루 1회 자동 갱신 (SCOPE 선택) | 영속 저장소와 D7 범위 재결정 필요 |
| 구청·주민센터 검색 수집 25개 구 (SCOPE 선택) | D12 ① 사람 승인 도메인, 수확 낮음, 재배포 불가 |
| **T420 TourAPI 관광지 → 좌표 사전** | D29·D25 로 TourAPI 좌표 사용 안 함. D29 ⑧ 재검토(활용매뉴얼·관광공사 회신, H13) 뒤 다시 본다 |
| ~~T421 TourAPI 병합 규칙~~ | **삭제**(D26 철회) |
| TourAPI 행사 화면(`events.html`) 에도 원문 절 | 이번에는 채팅 묶음 경로만 |
| 묶음 events 233KB(필드 다듬기) | 송출량 실측(T426) 결과에 따라 우선순위 |
| 지역 bbox 도우미 · 프론트 여행 기간 상한 안내 · Tavily LlmCallError 원인 · 변동 목표 재판정 · 새로고침 시 일정 비움(D17) · 캐시 키 주입 규칙 버전 | 유지 |
| Sprint 2·1 이월, Sprint 3 사람 작업(좌표 H7·별칭 H8·라벨 H9·평가셋 H10·D14) | 유지 |

## 10. 가장 큰 리스크
1. **25개 구 데이터 규모와 2Gi 메모리**: 검색 자식 25개 구 추정 413MiB × 동시 2 + backend + `/tmp`. T433(변환을 후보 수백 건으로)이 기대만큼 줄이지 못하면 카탈로그 동시성을 1로 내려야 하고 응답이 느려진다. 2차 측정(T418)까지 확정 못 한다.
2. **IP 를 믿을 수 없는 동안의 남용 방지와 송출 1GiB**: XFF 실측 전에는 IP 제한이 꺼져 세션을 새로 만들면 세션 제한을 피할 수 있다 — 전역 제한·일일 상한이 막지만 그 사이 정상 방문자도 같이 막힐 수 있다. us-central1 북미발 송출 무료 1GiB 는 묶음·검색 응답 크기로 금방 닿을 수 있다(gzip 효과는 T426 실측).
3. **TourAPI 실시간 경로의 외부 의존**: 요청마다 호출이라 개발계정 한도(단위 미확인)·응답 지연·키 오류(HTTP 200)가 화면 품질에 바로 드러난다. 재사용(캐시)을 못 하므로 상한에 걸리면 그날 절이 "지금 확인할 수 없음"으로 남는다. 이용 조건 해석(3유형)이 바뀌면 다시 설계해야 한다.
- 그 밖: 소프트 상한의 재시작 초기화(크레딧이 최종 상한), `max-instances` 잠깐 초과(D27 ⑧), 새 구 대부분이 "실록 색인 대상 아님"일 수 있음, 자동 후보 도구 입력 데이터 확보.

## 이월
(스프린트 종료 시 `/done` 이 기록한다)

---

## G1 반영 내역 (2026-10-10, 사람 결정 → 계획 변경)
| # | 사람 결정 | 계획 변경 |
|---|---|---|
| 1 | TourAPI 는 실시간 원문 표시 | 새 D29(§2.1). Stage 4 재설계: T419 = backend 전용 실시간 클라이언트(위치 (a) 와 이유), T434 묶음 연결·계약(§5.2), T435 프론트 별도 절. 수집·저장·정규화·병합·핀·이미지 없음 |
| 2 | D26 철회 | D26 을 "승인 전 철회 — D29 로 대체" 기록으로. T421 삭제 |
| 3 | D25 서울 API 장소만 | D25 ① 수정, T417 입력 고정, T420 이월 |
| 4 | D27: us-central1, 직접 CORS(미리보기 제외), 비밀 2개 숫자 버전·destroy, 2Gi·1 CPU, 카탈로그 동시성 2, S5 한계, `/tmp` 상한 | D27 전면 수정, D24 ② 동시성 2, T424 직접 CORS 만, T425 리전·버전 고정·교체 절차, 새 T436(감사 회전·캐시 정리), gzip(송출 1GiB 보호, T409) |
| 5 | D24: IP 를 믿을 수 없으면 IP 제한 끔, hops 기본값 없음 | D24 ④ 수정, `client_ip` 가 None 을 돌려주고 ip 규칙 건너뜀, §6.2 에 session·global 규칙 추가, T426 XFF 실측 절차 |
| 6 | D28 ④ 상한 = AR 0.5GiB·빌드 시간, 색인 약 270MiB | D28 ④ 수정, T423 이미지 크기 경고 |
| 7 | D24~D29 승인 | §2.1 문안 머리에 "(2026-10-10, 사람 승인/결정)" |
| — | T433 설계 | 앞 세 조건(요청 무관)으로 빠지는 항목은 변환 없이 `{pos,id,title,reason}` 만, 후보만 `entry_from_dict` — A안과 양립 근거 명시, `entries_built_at` 재파싱 제거 |
| — | T418 2차 측정 | `measure_seoul_rows --full` · LLM 경로 RSS 추가, 상한 서울 API ≤ 30(측정)·NVIDIA ≤ 2 |
| — | H 표 | H2 충족, H11 에 TourAPI 키, H13(선택, 활용매뉴얼·관광공사 문의) 추가 |
| — | §6.1 | TourAPI 런타임 상한(전역 300·세션 10·요청당 1·5초) 추가 |

## dev 평가 반영 내역

| # | 지적 | 수준 | 반영 |
|---|---|---|---|
| 1 | `events.html` 이 `config.local.js` 를 로드하지 않음(`index.html:13` 에만) | 차단 | T410 범위에 `events.html`·`admin.html` 의 script 추가, `connect-src` 정리(원본은 로컬용 유지, 배포 원점은 T424 가 `dist/` 에만) + 파싱 테스트 |
| 2 | CORS 미들웨어 순서 — `app.py:35` 뒤에 붙은 http 미들웨어가 바깥이라 429·413 에 CORS 헤더 없음 | 차단 | T409 에서 http 미들웨어(`_limit_body`·`_rate_limit`)를 먼저, CORS 를 **마지막에** 추가. 429·413 응답 `Access-Control-Allow-Origin` 테스트(`test_kc4_app_middleware.py`), §5.1 계약·D24 ⑤ 에 명시 |
| 3 | T416 블로킹 동등성 주장 오류(400일 상한·nodays 버킷) | 차단 | 상한 없는 **월 버킷** + 외부 id 키, 후보를 그룹 생성 순으로 순회하는 설계와 동등성 근거를 명세에 적음. 300개 테스트에 긴×짧은 기간·달 경계·날짜 없음 등 8종 포함. 계측값(2,000건 4.9초, 쌍당 약 2.5µs, 8.7k 약 95초, 3만 약 18분)을 근거로 §0.3·T416 에 기록 |
| 4 | 라이선스·재배포 — `var/catalog` 통째로 넣으면 Tavily 유래 공개, TourAPI 3유형 | 차단 | 이미지 카탈로그는 `snapshot_catalog.py --keep-ended`(서울 API 유래만, D19 규칙) + 필터 테스트(`test_kc4_image_data_filter.py`). 자동 좌표도 `origin` 필터. T401 에 공공누리 유형별 허용 범위 절 추가, D26 ⑦·D27 ④ 에 "확정 전 TourAPI 이미지 포함 금지" 명시, T420 TourAPI 입력 기본 꺼짐, T422 는 시험 파일만 *(G1 뒤: TourAPI 는 D29 실시간 원문 표시로 바뀌어 수집 자체가 없다)* |
| 5 | `test_kc_regions.py:31` 이 지역 4개 단언 | 차단 | T414 범위에 명시. 기대값 유지, `tests/fixtures/regions4/` 로 전환 |
| 6 | T407 이 `excluded` 계약을 바꿈(행사 화면이 사용) | 차단 | T407 은 Stage 1 프로파일만(동작 변경 없음). 개선은 T433(Stage 3)로 옮기고 기본 A안은 `excluded` 를 순서까지 보존. 계약을 바꾸는 B안은 조건부 결정 D29 승인 뒤에만. DoD 에 `excluded` 비교·행사 화면 n 확인 *(G1 뒤: T407 결과로 B안·조건부 D29 불필요, 번호는 TourAPI 결정에 재사용)* |
| 7 | `session_from_request` 위치 — 2b 숨은 의존 | 권장 | T409 의 `session.py` 로 옮김, T411·T412 는 이것만 사용 |
| 8 | `run_catalog` 전역 동시성 상한 | 권장 | T409: `CatalogBusy`·`configure_concurrency`(`KC_CATALOG_CONCURRENCY` 기본 3), T412 `_call` 에서 429, T411 은 행사 검색 실패 경로 *(G1 뒤: 기본 2)* |
| 9 | 공개 모드 `docs_url`·`openapi_url` | 권장 | T409·D24 ⑤·T413·T426 점검 |
| 10 | D24 문안 보강 | 권장 | ③ 소프트 상한·재시작 초기화·크레딧이 실제 상한, ① 로컬 `local` 공용 세션, ⑥ 일정 캐시 공유로 같은 문장 질의 여부 노출(영향 작음) |
| 11 | T417 사람 `seoul_bbox` → 데이터 기반 | 권장 | 같은 구 좌표 중앙값에서 `max_gu_dist_km` 넘으면 제외(D25 ③), 사람 값 없음. Stage 4 로 내려 T420 과 묶음. H 표에서 bbox 삭제 *(G1 뒤: T420 이월)* |
| 12 | H3 필수 → 선택, 자동 후보 도구 | 권장 | H3 선택(기본 빈 키워드, D28 ③). T415 에 `candidates`(실록 지명 태그 독음 ↔ 구별 동 이름) 추가, 사람은 고르기만 |
| 13 | `kc_demo.sh` 기본 4개 구, 배포는 25개 구 | 권장 | T416 `KC_DEMO_REGIONS`(기본 4개 구), T418 은 `var/catalog.all` 따로, D27 ④⑤ 에 명시 |
| 14 | T424 모드·`index.html` CSP | 권장 | T403 결론 하나만 구현(직접 CORS 면 프록시 코드 없음). `index.html` CSP 는 강제하지 않음(넣으면 Report-Only) |
| 15 | 프로파일 → T408 RSS → 재측정 순서 | 권장 | 최종 표·"측정 순서" 줄: T407 → T408(1차, RSS·동시 2건) → T433 → T418 안 2차 |
| 16 | §6.1 "회귀 측정 ≤ 210" 의미 | 권장 | `validate`·`run --check` 는 LLM 없음, `stability` 는 이번 계획에 없고 요청 시에만 ≤ 210 으로 구분 |
| 17 | T430~T432 | 권장 | 본문에서 빼고 §9 이월(Sprint 5 후보)로만 |
| 18 | H4·H2 상태 | 권장 | H4 "지금 착수 가능"(결제 계정 카드 등록 시간), H2 "신청 중" *(G1 뒤: H2 충족)* |
| 19 | 초안 T423 표에 `.gitignore` 누락 | 정리 | T423 범위에 `.gitignore`(`image-data/`·`dist/`) 명시, T424 는 고치지 않음 |

## 완료 기록
(스테이지마다 `/stage` 가 기록한다)

### Stage 1 — 스파이크·이월·측정 (2026-10-10, 커밋 `d4f8a4f`)
- 파일: `docs/spikes/{tourapi,cloud_run,netlify,kakao_domain}.md` · `domains/kcontext/{pipeline/__main__,pipeline/run,schedule/cache}.py` · `tests/.../test_kc4_cache_today.py` · `frontend/k-context/src/api/http.js` · `src/components/securitylog/{index,log-row,logic}.js` · `tests/securitylog.kc4.test.js` · `scripts/{profile_catalog_search,measure_seoul_rows,measure_runtime}.py` · `docs/status/{catalog_search_profile,measure}_2026-10-10.md`
- 회귀: pytest 1,943 · node 365 · ruff · eval validate/check 0 · kc_demo --check 0
- 실호출: TourAPI 10(키 `.env` — H2 이미 충족) · 서울 API 1 · NVIDIA 0
- reviewer: PASS(블로커 0, 권장 9 — 문서·주입 경로 정정 반영)
- **범위 이탈(정당, 기록)**: T406 이 `securitylog/index.js`(목록 렌더·스크롤이 여기 있음)와 `tests/realmode.test.js:172`(최신 우선 — 의도된 변화) 를 고쳤다.
- **명세와 다른 점(코디네이터 상한)**: T408 은 서울 API 3회·NVIDIA 0회 상한 때문에 `--full`(구별·끝나지 않은 행·좌표 행)과 LLM 경로 RSS 를 재지 않았다 → **T418 2차 측정 항목에 추가**.
- 결론: Netlify 는 직접 CORS(프록시 26초). TourAPI 표본 전부 공공누리 3유형. 검색 병목은 `entry_from_dict`(D29 불필요, T433 은 변환 건수 축소). 서울 총 19,586행. 메모리 2Gi 권고(추정, 카탈로그 동시 2 기준).
- G1 에 올릴 충돌 목록(reviewer): D26·D25 의 TourAPI 병합·좌표는 3유형과 충돌 / 실시간 원문 표시는 D7(런타임 외부 호출 금지)과 충돌 / XFF 미확인 시 IP 제한 폴백 / 리전·송출비 / 카탈로그 동시성 3 과 메모리 2Gi 불일치 / max-instances 잠깐 초과 / 비밀 버전 고정.
