# Sprint 4 — 서울 25개 구 확장 + 공개 배포 (확정)

> 상태: **확정**(pm, 2026-10-10). 초안 `sprint-4.draft.md` 에 dev 현실성 평가(실제 코드 대조)를 반영했다 — 끝의 "dev 평가 반영 내역". 초안은 그대로 둔다.
> 범위 근거: `docs/SCOPE.md` "Sprint 4 범위". "반드시"는 우선순위대로 ① 공개 배포 전 안전장치 ② 서울 25개 구 확장 ③ TourAPI 연결 ④ 배포(Netlify + Cloud Run + Secret Manager) ⑤ 문서다.
> "선택"(무료 DB, 자동 갱신, 구청 검색 수집 확대)은 이번 계획 본문에 태스크로 두지 않고 **이월(Sprint 5 후보)** 로만 적는다(§9). "지금 안 함"(NemoClaw/OpenClaw·MCP 에이전트화, 서울 밖, 유료 인프라)은 어떤 태스크에도 넣지 않았다.
> 시간 상자는 없고 소요 시간도 추정하지 않는다. **키·계정이 없어도 되는 코드 작업을 앞에 두고, 실호출·실배포는 뒤에 둔다.** 모든 스테이지 게이트에 "로컬 데모 동작 유지" 칸이 있다(§7).
> 태스크 ID: `T4{순번 2자리}`. 초안 번호를 유지했고 T433 이 새로 생겼다(T430~T432 는 이월로 빠짐). 새 테스트 접두사: `test_kc4_*`(파이썬), `*.kc4.test.js`(프론트).

## Sprint 4 최종 실행 계획

| 스테이지 | 태스크 | 병렬 | 결과물 |
|---|---|---|---|
| Stage 1 — 스파이크·이월·측정 (키·계정·결정 없이) | 1a: T401 TourAPI 문서(이용 조건 유형별 범위 포함) · T402 Cloud Run 문서 · T403 Netlify 문서 · T404 카카오 도메인 문서 · T405 캐시 키 today 일관성 · T406 보안 로그 날짜·최신 우선 · **T407 행사 검색 프로파일(동작 변경 없음)** → 1b: **T408 서울 API·자원(RSS) 측정** | 1a 7개 병렬 → 1b | `docs/spikes/{tourapi,cloud_run,netlify,kakao_domain}.md`, `docs/status/catalog_search_profile_*.md`, `docs/status/measure_*.md` |
| **게이트 G1** | 사람: D24~D28 승인(+ T407 결과에 따라 조건부 D29) | — | `docs/DECISIONS.md` |
| Stage 2 — 공개 안전장치 (D24) | 2a: T409 세션·제한·설정·카탈로그 동시성·미들웨어 순서 ∥ T410 프론트 세션·오류·배포 주소(+`events.html` 설정 로드) → 2b: T411 채팅 세션 분리·동시 처리·일일 상한 ∥ T412 공개 모드 보안 로그·승인·관리자·제보 → 2c: T413 공개 모드 통합 테스트·`kc_demo --public` | 2a 2개 → 2b 2개 → 2c 1개 | 방문자별 대화, 동시 2건, IP·세션별 제한, 일일 소프트 상한, 관리자·승인 닫힘, 429·413 에도 CORS 헤더 |
| Stage 3 — 서울 25개 구 (D28) | 3a: T414 지역 파일 21개(+기존 테스트 fixture 전환) ∥ T415 실록 키워드 측정·**자동 후보** 도구 ∥ T416 카탈로그 25개 구(전체 별칭·쪽 상한·**월 버킷 병합 블로킹**) ∥ T433 행사 검색 사전 제외 색인(`excluded` 보존) → 3b: **T418 실행**(25개 구 수집·색인(키워드 선택 시)·스냅샷·T408 재측정) | 3a 4개 병렬 → 3b 단독 | 25개 구 지역 설정, 25개 구 카탈로그(`var/catalog.all`), 검색 1.5초 이하 목표, (선택) 서울 키워드 색인 |
| Stage 4 — TourAPI·좌표 (D25·D26) | 4a: T419 TourAPI 수집기 ∥ T421 병합 규칙(D26) ∥ T417 좌표 자동 부착(서울 API 장소, 데이터 기반 이상치 제거) → 4b: T420 TourAPI 관광지 → 좌표 사전 → 4c: **T422 실수집·자동 좌표 생성**(TourAPI 부분은 키 필요) | 4a 3개 → 4b → 4c | `catalog/tourapi.py`, `kto:` 병합, 자동 좌표 사전, 수집 보고서 |
| Stage 5 — 배포 패키징 (D27, 계정 없이) | T423 Dockerfile·이미지 데이터(서울 API 유래만)·`.gitignore` ∥ T424 Netlify 설정·빌드 스크립트(T403 결론 모드만) ∥ T425 Cloud Run 배포 스크립트·가이드 | 3개 병렬 | `Dockerfile`, `netlify.toml`, `scripts/{build_image_data,netlify_build,deploy_cloudrun}.sh`, `docs/guides/DEPLOY.md` |
| Stage 6 — 실제 배포 (계정 필요) | T426 Cloud Run 배포·남용 점검 → T427 Netlify 배포·카카오 도메인·화면 확인 | 순차 | 공개 URL 2개, `docs/status/deploy_*.md` |
| Stage 7 — 문서 | T428 README·상태·가이드 ∥ T429 배포 URL 스크린샷 | 2개 병렬 | 배포 URL 기준 문서, `docs/demo/s4-*.png` |

- **필수 경로**: T401~T407 → T408 → G1(D24~D28) → T409·T410 → T411·T412 → T413 → T414·T415·T416·T433 → T418 → T419·T421·T417 → T420 → T422 → T423~T425 → (H4·H5·H11) T426 → (H6) T427 → T428·T429.
- **측정 순서**: T407(프로파일) → T408(1차, RSS 포함) → T433(개선) → T418 안에서 T408 재실행(2차). 2차 값이 D27 메모리 설정의 근거다.
- **키·계정이 필요한 일**: T408·T418(서울 키 — 이미 있음), T422 의 TourAPI 부분(H2), T426(GCP H4·H11), T427(Netlify H5·카카오 H6). 모두 해당 스테이지 끝에 있다.
- **사람 데이터가 없어도 끝까지 간다**: 21개 구 실록 키워드(H3)는 **선택**이다. 고르지 않으면 그 구는 "실록 색인 대상 아님"으로 문서에 밝힌다(D28 ③). 서울 범위 bbox 같은 사람 값은 이번 계획에서 쓰지 않는다(T417 은 데이터 기반).
- **얇은 수직 경로는 이미 있다**: 일정 문장 → 게이트 → 별도 프로세스 파이프라인 → 행사 검색 → 묶음 v2 → 화면, 보안 로그·사람 승인 API(Sprint 3). Stage 2 는 이 경로를 "여러 방문자가 동시에 써도 안전한" 형태로 바꾸고, Stage 5·6 은 같은 경로를 컨테이너에 그대로 싣는다.
- **TourAPI 키가 늦어져도** T419~T421·T417·T420 코드는 문서 스파이크(T401)와 합성 fixture 로 끝내고, T422 는 서울 API 자동 좌표만 만든 뒤 TourAPI 부분을 "실행 대기 — H2"로 남기고 Stage 5 로 간다. **TourAPI 데이터는 T401 이 이용 조건(공공누리 1·3유형)별 허용 범위를 확정하기 전에는 이미지에 넣지 않는다**(D26 ⑦·D27 ④).

---

## 0. 기준선 · 공통 규칙

### 0.1 착수 직전 dev 가 실측해 적는다
- `uv run python -m pytest -q` 건수: ____ (Sprint 3 마감 1,937 — 실측값을 쓴다)
- `uv run ruff check .`: 통과 여부
- `(cd frontend/k-context && node --test)` 건수: ____ (Sprint 3 마감 360)
- `uv run python eval/kc.py validate` · `uv run python eval/kc.py run --check --known-failures eval/BASELINE.md`: 0 여부(둘 다 LLM 을 부르지 않는다)
- `bash scripts/kc_demo.sh --check` · `--smoke`: 0 여부
- `du -sh var/index/kcontext.db var/catalog domains/kcontext/data/snapshots/catalog` (코디네이터 확인값: 43M · 46M · 836K)

### 0.2 공통 규칙 (Sprint 3 §0.2 를 이어받음)
- 파이썬 3.11+, 줄 길이 100, ruff 통과. 공개 함수에 타입 힌트, 새 패키지 `__init__.py` 는 `__all__` 명시.
- **PostToolUse 훅이 `ruff --fix` 로 미사용 import 를 지운다. import 와 그 사용은 한 번의 편집에 같이 쓴다.**
- **새 런타임 의존성 금지.** 있는 것만: `fastapi`·`httpx`·`mcp`·`openai`·`python-dotenv`·`uvicorn` + 표준 라이브러리. 프론트는 의존성 없음. GCP·Netlify 는 **CLI(`gcloud`·`netlify`)를 셸 스크립트에서** 부르고 SDK 를 쓰지 않는다. Secret Manager 는 Cloud Run 의 env 주입으로만 쓴다.
- 테스트 파일 이름은 레포 전체에서 고유하게. `tests/test_layout.py`·`test_smoke.py`·`test_boundaries.py` 는 수정하지 않는다.
- 도메인 코드는 `domains/kcontext/` 에만. `core/` 에 도메인 용어 금지(D3).
- **backend 는 `domains`·`mcp_server` 를 import 하지 않는다**(D3·D10).
- **지역은 코드에 박지 않는다**(`data/regions/*.json` 에서만. 테스트 fixture 예외).
- **사실을 지어내지 않는다.** 테스트·fixture 의 행사·좌표·한자 지명은 `○○`·`예시`·`합성` 값만. **실록 키워드(한자 지명)는 사람이 고른 값만**(자동 후보 도구는 후보를 낼 뿐 넣지 않는다). **좌표는 사람 사전(`demo_places.json`) 또는 D25 가 허용한 공공 API 값만.** TourAPI 의 오퍼레이션·파라미터·응답 필드 이름은 **T401 이 출처 URL 로 확인한 것만** 코드에 쓴다.
- **재배포 범위**: 저장소·이미지·공개 응답에 들어가는 행사·좌표 데이터는 이용 조건이 확인된 출처만 — 지금은 서울 열린데이터광장(공공누리 1유형) 유래만이다. Tavily 유래(`junggu_site`·`gangnam_site`)는 D12 ⑦·D19 대로 넣지 않는다. TourAPI 유래는 T401 확정 전까지 넣지 않는다.
- 키는 env **변수 이름**으로만(규칙 1, D1, D5). 키 값·Authorization 헤더·서비스키가 든 URL·세션 토큰·LLM 원문 응답 전체를 코드·로그·결과 파일·커밋에 남기지 않는다. TourAPI 서비스키는 쿼리 문자열로 들어갈 수 있으므로 **오류 메시지에 요청 URL 을 싣지 않는다**.
- `deploy/openshell/policy*.yaml`·`.env`·`eval/testset.json`·`CLAUDE.md`·`docs/DECISIONS.md` 는 dev·pm 이 고치지 않는다.
- 프론트 태스크는 **표에 적힌 파일만** 고친다. `?api=mock` 데모 모드는 지우지 않는다.
- **결과를 맞추려고 기존 테스트의 기대값을 바꾸지 않는다.** 실제 데이터 폴더에 의존하는 테스트가 깨지면 fixture 폴더로 전환한다(기대값 유지).
- **공개 모드는 env `KC_PUBLIC_MODE=1` 일 때만 켜진다.** 꺼져 있으면(로컬 기본) 지금 동작과 같아야 한다 — 기존 테스트·`eval/kc_eval/stability.py`(세션 헤더 없이 `/api/messages` 호출)·`kc_demo.sh` 가 그대로 통과해야 한다. 로컬 모드에서 세션 헤더가 없으면 공용 세션 `local` 이다.
- 실호출(NVIDIA·서울 API·TourAPI)은 §6 상한 안에서만. 상한은 코드 인자로도 둔다.

### 0.3 코드로 확인한 현황 (2026-10-10, pm 조사 + dev 대조)
| 영역 | 코드 위치 | 확인한 사실 | 관계 태스크 |
|---|---|---|---|
| 대화 기록 | `backend/chat.py` `ChatService._history`(deque 200), `_seq` | 프로세스에 하나 — 모든 방문자 공용. `GET /api/messages` 가 전부 돌려줌 | T411 |
| 동시 처리 | `chat.py` `_story_lock`(비차단 Lock) → `ChatBusy` → 429 `busy` | 일정 흐름 1건만 | T411 |
| 요청별 로그 | `chat.py` `_TeeSink.mark()/since()` | 누적 개수 기준 — 동시 요청이면 다른 요청의 audit 이벤트가 섞인다 | T411 |
| 행사 검색 한도 | `chat.py` `self._search_timeout_s` | 인스턴스 필드 — 동시 흐름이면 경쟁 | T411 |
| 카탈로그 자식 프로세스 | `backend/catalog_runner.py::run_catalog` | 동시성 상한 없음 — 검색 요청마다 자식 프로세스 | T409 |
| 미들웨어 순서 | `backend/app.py:35` CORS 추가 → 그 뒤 `@app.middleware("http") _limit_body` | 나중에 붙은 `_limit_body` 가 바깥 — **413 응답에 CORS 헤더가 없다**. 같은 방식으로 429 를 붙이면 똑같이 빠진다 | T409 |
| API 문서 | `FastAPI(title="backend")` | `/docs`·`/openapi.json` 기본 공개 | T409 |
| CORS | `backend/settings.py` 기본 localhost:8766, `KC_CORS_ORIGINS` | `allow_headers=["Content-Type","X-Admin-Token"]` | T409 |
| 보안 로그 | `routers/review.py` `GET /api/audit` | `audit_dir/*.jsonl` 전부 — 다른 방문자의 차단 기록(경로 문자열 포함)도 보임. `POST /api/audit/{id}/decision` **인증 없음** | T412 |
| 관리자 | `routers/events.py` `require_admin` | 토큰 hmac 비교, 미설정이면 닫힘. 실패 횟수 제한 없음 | T409·T412 |
| 제보 | `POST /api/reports` | 인증 없이 `reports.json` 에 씀 | T412 |
| 행사 검색 | `catalog/api.py::_search` → `store.load_entries()` 전체 → `query.search_events` | 8,719건을 매번 읽고 `excluded` 8,600건을 돌려줌 → 약 6초. 어느 단계가 큰지 미측정 | T407·T433 |
| `excluded` 소비자 | `backend/chat_story.py::_shrink_excluded`(묶음 표본 20 + 합계), `frontend/.../src/events/view.js:135`("제외된 항목 n건 보기" 목록) | `/api/events/search` 의 `excluded` 목록 모양이 화면 계약이다 | T433 |
| 병합 | `catalog/merge.py::_group`·`same_event` | 새 관찰값마다 기존 모든 그룹과 비교. 날짜 집합 교집합(상한 없음)으로 판정. 날짜 없는 항목은 외부 id 공유 때만 합쳐짐. **계측(dev): 2,000건 4.9초, 쌍당 약 2.5µs → 8.7k건 약 95초, 3만 건 약 18분** | T416 |
| 서울 API | `catalog/seoul.py::fetch_rows(max_pages=30)` | 1000행 × 30쪽 넘으면 조용히 잘림 | T408·T416 |
| 대상 지역 | `catalog/target.py` | `KC_TARGET_REGION` 쉼표 목록, 여럿이면 `"+"` 로 합친 Region | T416 |
| 지역 파일 | `data/regions/{jung,jongno,mapo,gangnam}.json`, `tests/domains/kcontext/test_kc_regions.py:31` 이 실제 폴더 4개를 단언 | `sillok_keywords` 가 하나라도 있으면 모든 지역이 그 필드로만 매칭(`ingest/sillok.py::_region_field`) — 빈 목록 지역은 색인에 없음 | T414·T418 |
| 실록 XML | `ingest/sillok.py` | 기사마다 `<index type="지명">` 태그 | T415 |
| 장소 사전 | `domains/kcontext/places.py` | `demo_places.json` 하나(5곳) | T417 |
| 캐시 키 | `schedule/cache.py::key_for(today=)`, `pipeline/__main__.py` | `__main__` 이 today 를 넘기지 않음 | T405 |
| 보안 로그 표시 | `frontend/.../api/http.js::sanitizeAuditEntry` | 서버 `at` 을 버림. 서버는 오래된 순 | T406 |
| 프론트 설정 | `index.html:13` 만 `config.local.js` 를 로드. **`events.html` 은 로드하지 않음**. `events.html`·`admin.html` meta CSP `connect-src 'self' http://localhost:* http://127.0.0.1:*` | 배포 주소를 행사 화면에 줄 수단이 없음 | T410·T424 |
| 스냅샷 | `scripts/snapshot_catalog.py::make_snapshot` | `seoul_openapi` 관찰값만 남기고 다시 묶음(D19) — 이미지 데이터도 이 규칙을 재사용할 수 있다 | T423 |
| 컨테이너 | `Dockerfile` 없음, `.dockerignore`(.env·.git·.claude 등) | `var/` 를 제외하지 않음 | T423 |
| TourAPI | `catalog_sources.json:23` "공공누리 1·3유형" | 3유형은 변경금지 — 정규화·병합·재배포 허용 범위 미확인. 호출 코드 없음 | T401·T419 |

---

## 1. 의존성 그래프

```
Stage 1
  1a (병렬): T401 TourAPI 문서(+이용 조건) · T402 Cloud Run 문서 · T403 Netlify 문서 · T404 카카오 문서
             T405 캐시 today · T406 보안 로그 날짜 · T407 검색 프로파일(동작 변경 없음)
  1b: T408 측정(서울 API 행 수 · RSS) ──► G1: D24~D28 (+ 조건부 D29: T407 이 excluded 직렬화가 병목이라고 보이면)
                │
Stage 2 (D24)   ▼
  2a: T409 backend 기반(session.py·limits.py·settings·app 미들웨어 순서·meta·catalog_runner 동시성)  ∥  T410 프론트
  2b: T411 chat.py·messages.py  ∥  T412 review.py·events.py          (둘 다 T409 인터페이스만 사용)
  2c: T413 공개 모드 통합 + kc_demo --public
                │
Stage 3 (D28)
  3a: T414 지역 21개 ∥ T415 키워드 측정·자동 후보 ∥ T416 카탈로그 25개 구 ∥ T433 검색 색인(excluded 보존 / D29 면 요약)
  3b: T418 실행 (H3 선택: 고른 키워드가 있으면 색인 재구축, 없으면 4개 구 색인 유지) + T408 재측정
                │
Stage 4 (D25·D26)
  4a: T419 TourAPI 수집기 (T401) ∥ T421 병합 D26 (merge.py — T416 뒤) ∥ T417 자동 좌표(서울 API)
  4b: T420 관광지 → 좌표 사전 (T417·T419)
  4c: T422 실수집 — 서울 API 자동 좌표는 키 없이, TourAPI 부분은 H2
                │
Stage 5 (D27)
  T423 Dockerfile·이미지 데이터 ∥ T424 Netlify ∥ T425 배포 스크립트·가이드
                │
Stage 6 ◄── H4·H11·H7 / H5·H6
  T426 Cloud Run 배포·남용 점검 → T427 Netlify 배포·도메인·화면
                │
Stage 7: T428 문서 ∥ T429 스크린샷
```

---

## 2. 결정 후보 (먼저 결정을 추가해야 함)

pm·dev 는 `docs/DECISIONS.md` 를 고치지 않는다. 사람이 승인하면 D24 부터 추가한다. **G1 에서 한꺼번에 승인받되**, 스파이크(T401~T404)·프로파일(T407)·측정(T408) 결과로 `[확인 필요]` 값을 채운 문안을 올린다.

| 후보 | 요지 | 착수 조건이 되는 스테이지 | 승인 전 진행 |
|---|---|---|---|
| D24 | 공개 배포 보안 모델 + D20 재검토 결론 | Stage 2 | Stage 2 착수하지 않음 |
| D25 | 좌표 자동 부착은 공공 API 좌표만, 데이터 기반 이상치 제거 | T417·T420 | T417·T420 착수하지 않음 |
| D26 | TourAPI × 서울 API 병합 + 이용 조건 확정 전 재배포 금지 | T419·T421 | 둘 다 착수하지 않음 |
| D27 | 배포 구성(Netlify + Cloud Run 1 인스턴스 + Secret Manager, 휘발 상태, 이미지 = 25개 구·서울 API 유래만) | Stage 5 | Stage 5 착수하지 않음 |
| D28 | 실록 색인 서울 확장(사람이 고른 키워드만, 기본 빈 목록, 크기 상한, 전체 색인 안 함) | T418 의 색인 부분 | 색인은 4개 구 그대로 |
| D29 *(조건부)* | `/api/events/search` 의 `excluded` 를 요약(표본+사유별 수)으로 바꾼다 | T433 의 B안 | T433 은 A안(`excluded` 보존)만 |

D29 는 T407 프로파일이 "`excluded` 직렬화·전송이 검색 시간의 대부분"이라고 보일 때만 올린다. 그렇지 않으면 올리지 않는다.

### D24~D29 문안 (승인용)

```markdown
## D24 — 공개 배포는 서버 발급 세션 토큰·요청 제한·일일 소프트 상한으로 지키고, 공개 모드에서는 관리자·승인·제보 쓰기를 닫는다. OpenShell 은 계속 선택이다 (2026-10-xx)
- **결정**:
  ① **세션**: `POST /api/session` 이 임의 토큰(`secrets.token_urlsafe(32)`, 43자)을 발급하고, 브라우저는 탭 단위 `sessionStorage` 에 두어 `X-KC-Session` 헤더로 보낸다(쿠키 없음 — 다른 출처의 서드파티 쿠키 차단과 CSRF 를 함께 피한다). 서버는 세션별 대화 기록(최대 100개)·보안 로그 항목(최대 200개)을 **프로세스 메모리에만** 두고, 마지막 사용 후 2시간 뒤 지운다(세션 수 상한 1,000, 넘으면 가장 오래 안 쓴 세션부터). **채팅 묶음은 지금처럼 서버에 보관하지 않는다(D17 유지)**. **로컬 모드(공개 모드 꺼짐)에서 세션 헤더가 없으면 공용 세션 `local` 을 쓴다** — 지금 동작과 같다.
  ② **동시 처리**: 일정 흐름은 인스턴스당 동시 2건(`KC_STORY_CONCURRENCY`), 세션당 1건, 행사 카탈로그 자식 프로세스는 인스턴스당 3개(`KC_CATALOG_CONCURRENCY`). 넘으면 기다리지 않고 429 `busy`.
  ③ **요청 제한**(IP·세션별 고정 창, sprint-4 §6.2 표). 넘으면 429 `rate_limited` + `Retry-After`. **LLM 일일 상한**: 하루(KST) LLM 호출 단위 `KC_LLM_DAILY_UNITS`(기본 300)를 넘으면 503 `daily_limit`. 일정 흐름은 2단위를 예약하고 실제 시도 수(`schedule.attempts`, 캐시면 0)만큼 남기고 돌려받는다. 일반 챗봇은 1단위. **이 상한은 인스턴스 메모리 기반 소프트 상한이라 인스턴스가 재시작되면 0 으로 돌아간다. 실제 비용 상한은 NVIDIA 크레딧(사람 확인 H7)이다.**
  ④ **IP**: `X-Forwarded-For` 를 오른쪽에서 `KC_TRUSTED_PROXY_HOPS` 번째 값으로 읽는다(값은 T402·T403 근거, T426 실측). 읽지 못하면 연결 주소.
  ⑤ **공개 모드**(`KC_PUBLIC_MODE=1`): `/api/admin/*`·`POST /api/audit/{id}/decision`·`POST /api/reports` 는 403 `disabled_in_public`. `GET /api/audit` 은 **그 세션의 항목만**. `/docs`·`/openapi.json` 은 끈다. 관리자 화면(`admin.html`)은 공개 배포물에 넣지 않는다. 모든 오류 응답(413·429·403·503 포함)에 CORS 헤더가 붙는다(미들웨어 순서).
  ⑥ **일정 캐시 공유(알려진 작은 노출)**: 일정 이해 캐시(D15 ④)는 방문자 사이에 공유된다. 같은 문장을 누군가 먼저 보냈다면 "이전 결과 재사용" 표시로 그 사실이 드러날 수 있다. 내용(다른 방문자의 문장·결과)은 드러나지 않고, 드러나는 것은 "똑같은 문장을 누가 보낸 적 있음" 뿐이라 영향이 작다고 보고 그대로 둔다(README 한계에 적는다).
  ⑦ **D20 재검토 결론**: 공개 서비스로 띄워도 OpenShell 은 필수로 돌리지 않는다. 근거 — LLM 에 도구(파일·네트워크)가 없고 출력이 실행되지 않으며, 에이전트 역할 프로세스에는 허용 목록 env 만 가고(D7 ③), 외부 자료는 호스트 수집기만 받는다(D7). 공개로 새로 생기는 위협(방문자 간 대화 노출·비용 남용·관리자 API·승인 위조)은 샌드박스가 아니라 ①~⑤ 로 막는다. **LLM 에 도구를 주거나 NemoClaw 로 옮기면 D20 대로 다시 본다.**
- **계기**: SCOPE Sprint 4 ① 과 D20 "다시 볼 때 — 공개 서비스로 띄울 때". 코드 확인: 대화 기록 공용, 일정 흐름 1건, 승인 API 무인증, 보안 로그 전체 노출, 동시 요청 시 로그 섞임, 413 에 CORS 헤더 없음.
- **대안**: (a) 쿠키 세션 — 다른 출처면 서드파티 쿠키·SameSite 처리가 필요해 기각. (b) 대화 기록을 브라우저가 들고 매 요청에 실음 — 위조한 assistant 턴이 LLM 맥락에 들어가는 주입 경로라 기각. (c) 클라이언트가 토큰 생성 — 발급 수를 IP 별로 제한할 수 없어 기각. (d) 승인 API 를 관리자 토큰으로 열어 둠 — 공개 흐름에는 승인할 초안이 없고 토큰 대입 표면만 생겨 기각. (e) 일일 상한을 외부 저장소로 — 새 의존성·유료 가능성으로 기각(크레딧이 최종 상한). (f) OpenShell 필수화 — 위협 모델과 맞지 않고 Cloud Run 에서 돌릴 수 없어 기각.

## D25 — 장소 좌표 자동 부착은 공공 API 가 준 좌표만 쓰고, 데이터 자체로 이상치를 거르며, 사람 사전이 우선하고, 화면에 "공공 데이터 좌표"로 밝힌다 (2026-10-xx)
- **결정**: ① 출처는 **서울 열린데이터광장 문화행사의 장소명·위경도(LAT·LOT)** 와 **TourAPI 관광지의 이름·좌표**(필드 이름은 T401 확인값) 둘뿐이다. ② 같은 이름(정규화 후)의 좌표들이 중앙값에서 모두 150m 안이면 중앙값을 쓰고, 하나라도 벗어나면 그 이름은 버린다(모호). ③ 이상치: 같은 자치구(서울 API 는 GUNAME, TourAPI 는 T401 코드표의 구)로 분류된 모든 좌표의 중앙값에서 `max_gu_dist_km`(제안 8km, T422 에서 분포를 보고 조정) 넘게 떨어진 좌표는 버린다 — 사람이 정하는 범위 값을 쓰지 않는다. 구가 없는 좌표는 쓰지 않는다. ④ 사람 사전(`demo_places.json`)에 같은 이름·별칭이 있으면 사람 값이 이긴다. ⑤ 자동 사전 항목은 `source`(출처 이름·행 수)·`verified_at`(수집일)·`auto: true` 를 갖고 `var/places/auto_places.json` 에 생성한다(커밋하지 않음). ⑥ 앵커가 자동 좌표를 쓰면 문제 코드 `COORD_AUTO` 를 남기고 화면은 고정 문구로 보인다. ⑦ 자동 좌표는 지도 핀·이동 구간 거리 표시에 쓰고, 판정 규칙(D16·D13 ⑥)은 그대로다. ⑧ 자동 사전 이름은 일정 게이트(`backend/fixtures/chat_places.json`)에 넣지 않는다.
- **계기**: 좌표가 있는 장소가 5곳뿐이라 25개 구 확장의 병목. Sprint 3 규칙("좌표는 사람이 출처를 확인한 값만")을 공공 API 값에 한해 넓힌다.
- **대안**: (a) 카카오 로컬 등 외부 장소 검색 — 새 키·외부 호출·결과 저장 약관 확인이 필요해 기각(H8 후보 유지). (b) 사람이 정한 서울 bbox 로 거르기 — 사람 값이 필요하고 구 단위 오류는 못 거르므로 기각. (c) 좌표 하나라도 있으면 채택 — 동명 장소가 섞여 기각.

## D26 — TourAPI 행사는 D13 묶기 규칙 그대로 서울 API 와 합치고, 관광지는 좌표 사전 입력으로만 쓰며, 이용 조건이 확정되기 전에는 재배포하지 않는다 (2026-10-xx)
- **결정**: ① TourAPI 콘텐츠 id 는 외부 id 체계 `kto:`(값은 T401 이 확인한 콘텐츠 id 필드), 서울 API 는 `seoul_cult:` 그대로. ② 두 체계가 다르므로 묶기는 D13 ③ 의 장소+기간+행사명 유사도 규칙만(주최 같으면 0.5, 아니면 0.8). 같은 체계 다른 값은 다른 행사. ③ 두 출처 모두 `official_api` 등급이고 **원천 관계가 확인되기 전에는 독립 출처로 세지 않는다**. ④ 같은 필드 값이 다르면 D13 ④ 대로(최근 수정 → 미해결이면 `conflict`, 값 비움). 출처 간 우선순위를 새로 만들지 않는다. ⑤ TourAPI 관광지는 `EventEntry` 로 만들지 않고 D25 좌표 사전 입력으로만 쓴다. ⑥ 대상 지역은 D13 ② — TourAPI 지역 코드는 T401 이 공식 코드 조회로 만든 대응표로만 구 이름이 된다. ⑦ **이용 조건**: TourAPI 는 "공공누리 1·3유형"(데이터셋 페이지)이고 3유형은 변경금지다. T401 이 항목·필드별 유형과 정규화·병합·저장·이미지 포함의 허용 여부를 확정하기 전에는 TourAPI 유래 데이터(행사 관찰값·관광지 좌표)를 **저장소·이미지·공개 응답에 넣지 않는다** — 호스트 `var/` 에서 수집·병합 시험만 한다. 확정되면 허용된 유형만 넣고 출처를 표시한다.
- **계기**: SCOPE Sprint 4 ③. D13 은 출처 간 묶기를 정했지만 TourAPI 의 id 체계·관광지·독립 출처·이용 조건은 정하지 않았다.
- **대안**: 한쪽 출처 우선 고정 — 근거 없이 한쪽 값을 사실로 올려 기각. 관광지도 카탈로그 항목으로 — 상설 관광지가 행사처럼 섞여 기각. 1유형 항목만 골라 바로 재배포 — 항목별 유형 표시 여부부터 미확인이라 기각.

## D27 — 배포는 Netlify(정적) + Cloud Run(인스턴스 1개) + Secret Manager 로 하고, 이미지는 서울 25개 구·서울 API 유래만 담으며, 상태는 휘발이다 (2026-10-xx)
- **결정**: ① 화면은 Netlify 정적 배포(`frontend/k-context` 를 빌드에서 `dist/` 로 복사하고 `config.local.js` 를 Netlify 환경변수로 생성 — 키는 저장소에 없다). `admin.html` 은 싣지 않는다. ② API 연결은 **T403 결과로 하나만 둔다**: Netlify 프록시의 요청 시간 한도가 일정 흐름 최대 100초 이상이고 방문자 IP 가 전달되면 프록시, 아니면 **직접 CORS**(`KC_CORS_ORIGINS`=Netlify 도메인, 빌드가 `dist/events.html` 의 `connect-src` 에 Cloud Run 원점을 넣음). [확인 필요: T403] `index.html` 의 CSP 는 이번에 강제하지 않는다(카카오 SDK 를 깨뜨릴 위험 — 넣는다면 Report-Only). ③ Cloud Run: 컨테이너 하나(uvicorn 1 프로세스 + 요청마다 자식 프로세스), `max-instances=1`·`min-instances=0`, 요청 한도 ≥ 120초, 메모리는 T408 2차 실측 최대 RSS × 1.5 를 무료 사용량 안에서. [확인 필요: T402] ④ **이미지 데이터**: 실록 색인 + **서울 25개 구 카탈로그**(사용자 결정 "서울 전체") + 자동 좌표 사전. 카탈로그는 스냅샷(D19)과 같은 규칙으로 **`seoul_openapi` 유래만** 남겨 다시 묶은 것이고, Tavily 유래(D12 ⑦)와 TourAPI 유래(D26 ⑦ 확정 전)는 넣지 않는다. 좌표 사전도 출처가 같은 규칙을 통과한 항목만. 모두 **빌드 전에 호스트에서** 만든다. 런타임에는 서울 API·TourAPI·Tavily 를 부르지 않는다(키를 주입하지 않음, D7). ⑤ 로컬 데모(`kc_demo.sh`)의 기본 지역은 수집 시간 때문에 4개 구 그대로이고 `all` 은 옵션이다 — 배포 이미지만 25개 구다. ⑥ 비밀은 Secret Manager → Cloud Run env(`NVIDIA_API_KEY` 하나). 이미지·빌드 컨텍스트에는 비밀이 없다(규칙 1). ⑦ hitl·audit·일정 캐시·세션은 인스턴스 안(`/tmp`)에만 두고 재시작하면 비워진다. ⑧ 무료 사용량 밖 설정(최소 인스턴스 ≥1 등)은 쓰지 않고, 사람이 결제 계정에 예산 알림을 건다(H4).
- **계기**: SCOPE Sprint 4 ④. 인스턴스가 하나여야 메모리 세션·제한·일일 상한이 정확하다(D24).
- **대안**: (a) Netlify Functions 로 백엔드 — 별도 프로세스·SQLite·최대 90초 파이프라인과 맞지 않아 기각. (b) 색인을 GCS 에서 시작 시 내려받기 — 이미지 한도를 넘을 때의 예비안. (c) 런타임 수집 — D7 과 충돌해 기각. (d) 인스턴스 여러 개 — 제한이 무력해져 기각. (e) `var/catalog` 를 그대로 이미지에 — Tavily 유래가 공개돼 D12 ⑦·D19 위반이라 기각.

## D28 — 실록 색인은 사람이 고른 키워드로만 서울 확장하고, 고르지 않은 구는 "색인 대상 아님"으로 둔다. 전체 색인은 하지 않는다 (2026-10-xx)
- **결정**: ① `--mode regions` 그대로, 25개 구 `sillok_keywords` 의 합집합으로 다시 만든다. ② 새 구의 키워드는 **T415 자동 후보 도구가 낸 후보(실록 지명 태그 ↔ 구별 동 이름 대응, 건수 포함) 중에서 사람이 고른 것**만 넣는다. 고른 사람·날짜·후보 근거를 지역 파일 `note` 에 남긴다. ③ **기본은 빈 목록**이고, 빈 목록인 구는 "실록 색인 대상 아님"으로 README·상태 문서에 밝힌다. ④ 색인 파일 상한은 **[확인 필요: T402 이미지 한도·T408 실측]** — 넘으면 키워드를 줄이거나 D27 (b) 예비안. ⑤ `--mode all`(38만 기사)은 하지 않는다.
- **계기**: SCOPE Sprint 4 ② "실록 색인을 서울 전체 키워드로 재구축". 키워드는 사실이라 기억으로 채울 수 없다.
- **대안**: 전체 색인 — 수 GB 로 기각. 한글 구 이름만 — 본문이 한문이라 재현율이 낮고 동명이 섞여 기각. 사람이 처음부터 출처를 찾아 작성 — 병목이라 자동 후보 + 고르기로 바꿈.

## D29 (조건부) — 행사 검색 응답의 excluded 를 표본과 사유별 수로 줄인다 (2026-10-xx)
- **결정**: `/api/events/search`·`cards` 의 `excluded` 를 앞 N건 표본 + `excluded_total` + `excluded_by_reason` 으로 바꾸고(묶음과 같은 모양), 행사 화면은 "제외된 항목 n건(사유별)"과 표본만 보인다. 끝난 행사는 색인 단계에서 미리 세어 둔다.
- **계기**: T407 프로파일에서 excluded 직렬화·전송이 검색 시간의 대부분일 때만.
- **대안**: excluded 전체 보존(T433 A안) — 기본안. 이 결정은 A안으로 목표 시간에 못 미칠 때만.
```

---

## 3. 사람 선행 · 블로커

### 3.1 사람 선행 작업
| ID | 할 일 | 상태 | 막는 태스크 | 막혀 있을 때 |
|---|---|---|---|---|
| H1 | **G1: D24~D28(+조건부 D29) 승인** | Stage 1 뒤 | Stage 2~5 의 결정 의존 태스크 | §2 "승인 전 진행" |
| H2 | **TourAPI 서비스키**(`DATA_GO_KR_SERVICE_KEY`) 발급 → `.env`. 활용가이드가 로그인 뒤에만 받아지면 `docs/private/` 에 둠 | **신청 중** | T401 실측 칸, T422 의 TourAPI 부분 | T401 은 공개 문서 + `[확인 필요]`, T422 TourAPI "실행 대기 — H2" |
| H4 | **GCP**: 프로젝트, **결제 계정 연결(카드 등록에 시간이 걸릴 수 있음)**, 예산 알림(예: 1 USD), `gcloud auth login`, API 사용 설정(이름은 T402 확인값) | **지금 착수 가능** | T426 | Stage 5 까지 진행, 배포 대기 |
| H5 | **Netlify** 계정·`netlify login`(또는 Git 연동), 사이트 이름 | 지금 착수 가능 | T427 | 배포 대기 |
| H6 | **카카오 개발자 콘솔**에 배포 도메인 등록(T404 절차), JS 키를 Netlify 환경변수 `KC_KAKAO_JS_KEY` 로 | T427 직전 | T427 의 카카오 지도 | SVG 지도로 배포(D11) |
| H7 | **NVIDIA 크레딧 잔량·호출 한도 확인** → `KC_LLM_DAILY_UNITS` 확정(기본 300). 실제 비용 상한은 이것 | T426 전 | T426 공개 | 기본 300 으로 공개 |
| H11 | **Secret Manager 에 `NVIDIA_API_KEY` 값 등록**(사람이 직접, 명령은 T425 가이드) | T426 전 | T426 | 배포 대기 |
| H3 | *(선택)* T415 자동 후보 중 21개 구 실록 키워드 고르기 | Stage 3 | T418 의 색인 재구축 | 그 구는 "실록 색인 대상 아님", 색인은 4개 구 그대로 |
| H8 | *(선택, D25 대안)* 외부 장소 검색 키 | — | 없음 | D25 대로 |
| H12 | *(선택)* T429 스크린샷 확인 | Stage 7 | T428 이미지 | 텍스트만 |

Sprint 3 의 사람 작업(평가셋 검수·좌표 H7·별칭 H8·라벨 H9·D14 확인)은 이번 범위가 아니며 남는다(§9).

### 3.2 블로커 요약
| 블로커 | 막히는 것 | 대응 |
|---|---|---|
| 결정 승인(G1) | Stage 2~5 | Stage 1 은 결정 없이, 스파이크 값으로 문안 완성 |
| TourAPI 키(H2)·이용 조건 | T422 TourAPI 부분, 이미지 포함 | 코드는 문서·합성 fixture 로 끝냄. 배포는 서울 API 데이터로 |
| GCP·Netlify·카카오(H4·H5·H6·H11) | Stage 6 | Stage 5 까지 계정 없이. H4 는 지금 착수 |
| NVIDIA 크레딧(H7) | 공개 상한 확정 | 보수 기본값 300(소프트 상한) |
| 무료 사용량·이미지 한도 | D27·D28 숫자 | T402·T408 로 확인 |
| 게이트웨이·샌드박스 | 없음 | D20·D24 ⑦ |

---

## 4. 스테이지 상세

### Stage 1 — 스파이크 · 이월 · 측정
| TASK | 제목 | 범위(소유 경로) | 선행 | 병렬 충돌 |
|------|------|------|------|------|
| T401 | [스파이크] TourAPI KorService2 + 이용 조건 | `docs/spikes/tourapi.md` | — (H2 있으면 실측 칸) | 없음 |
| T402 | [스파이크] Cloud Run·Artifact Registry·Secret Manager·Cloud Build | `docs/spikes/cloud_run.md` | — | 없음 |
| T403 | [스파이크] Netlify 정적 배포·API 연결 | `docs/spikes/netlify.md` | — | 없음 |
| T404 | [스파이크] 카카오 지도 JS 키 도메인 등록 | `docs/spikes/kakao_domain.md` | — | 없음 |
| T405 | 이월: 캐시 키·해석의 today 일관성 + LLM_BACKEND | `domains/kcontext/pipeline/{__main__,run}.py`, `domains/kcontext/schedule/{cache,understand}.py`, `tests/domains/kcontext/pipeline/test_kc4_cache_today.py` | — | 없음 |
| T406 | 이월: 보안 로그 날짜·최신 우선 | `frontend/k-context/src/api/http.js`(sanitize 만), `src/components/securitylog/{logic,log-row}.js`, `src/i18n/{ko,en}.js`, `tests/securitylog.kc4.test.js` | — | 없음 |
| T407 | 이월: 행사 검색 프로파일(**동작 변경 없음**) | `scripts/profile_catalog_search.py`(신규), `docs/status/catalog_search_profile_2026-10-xx.md`(신규) | — | 없음 |
| T408 | [측정] 서울 API 전체 행·자원(RSS) 기준선 (1b) | `scripts/measure_seoul_rows.py`(신규), `scripts/measure_runtime.py`(신규), `docs/status/measure_2026-10-xx.md`(신규) | T407(같은 데이터로 잰 프로파일을 문서에서 참조), 서울 키(있음) | 1b 단독 |

### Stage 2 — 공개 안전장치 (D24)
| TASK | 제목 | 범위 | 선행 | 병렬 충돌 |
|------|------|------|------|------|
| T409 | backend 세션·제한 기반 + 설정 + 미들웨어 순서 + 메타 + 카탈로그 동시성 (2a) | `backend/session.py`(신규), `backend/limits.py`(신규), `backend/routers/meta.py`(신규), `backend/settings.py`, `backend/app.py`, `backend/catalog_runner.py`, `.env.example`, `tests/backend/test_kc4_session.py`, `tests/backend/test_kc4_limits.py`, `tests/backend/test_kc4_app_middleware.py` | D24 | 없음 |
| T410 | 프론트 세션·제한 오류·배포 주소 설정 (2a) | `frontend/k-context/src/api/{http,index}.js`, `src/lib/api-base.js`(신규), `src/events/api.js`, `src/components/securitylog/approve-buttons.js`, `src/i18n/{ko,en}.js`, `events.html`, `admin.html`, `config.local.example.js`, `tests/session.kc4.test.js` | D24 | 없음(T406 과 다른 스테이지) |
| T411 | 채팅 세션 분리·동시 처리·일일 상한 (2b) | `backend/chat.py`, `backend/routers/messages.py`, `tests/backend/test_kc4_chat_sessions.py` | T409 | 없음 |
| T412 | 공개 모드 보안 로그·승인·관리자·제보 (2b) | `backend/routers/review.py`, `backend/routers/events.py`, `tests/backend/test_kc4_public_mode.py` | T409 | 없음 |
| T413 | 공개 모드 통합 테스트·로컬 공개 모드 실행 (2c) | `tests/test_kc4_public_e2e.py`, `scripts/kc_demo.sh`(`--public`) | T409~T412 | 단독 |

### Stage 3 — 서울 25개 구 (D28)
| TASK | 제목 | 범위 | 선행 | 병렬 충돌 |
|------|------|------|------|------|
| T414 | 지역 파일 21개 + 기존 지역 테스트 fixture 전환 | `domains/kcontext/data/regions/*.json`(신규 21), `tests/domains/kcontext/test_kc_regions.py`(`test_real_regions_load` 만), `tests/fixtures/regions4/*.json`(신규, 기존 4개 파일 사본), `tests/domains/kcontext/test_kc4_regions25.py` | — | 없음 |
| T415 | 실록 키워드 측정·자동 후보 도구 | `domains/kcontext/ingest/sillok_keywords.py`(신규), `tests/domains/kcontext/ingest/test_kc4_sillok_keywords.py`, `docs/spikes/sillok_candidates.md`(신규 — 입력 데이터 출처 기록) | — | 없음 |
| T416 | 카탈로그 25개 구: 전체 별칭·서울 API 쪽 상한·월 버킷 병합 블로킹 | `domains/kcontext/catalog/{target,seoul,merge}.py`, `.env.example`(설명 줄만), `scripts/kc_demo.sh`(`KC_DEMO_REGIONS`), `tests/domains/kcontext/catalog/test_kc4_target_all.py`, `test_kc4_merge_blocking.py` | — | `.env.example`·`kc_demo.sh` 는 Stage 2 태스크도 고침 — 다른 스테이지 |
| T433 | 행사 검색 사전 제외 색인(A안 `excluded` 보존 / D29 면 B안) | `domains/kcontext/catalog/{store,query,api,__main__}.py`, `scripts/snapshot_catalog.py`(복원 끝 색인 생성 1줄), `tests/domains/kcontext/catalog/test_kc4_search_index.py` (B안이면 + `backend/chat_story.py`·`frontend/k-context/src/events/{view,logic,api}.js`·`docs/chat-bundle.contract.md`·`tests/events.excluded.kc4.test.js`) | T407, (B안) D29 | 없음 |
| T418 | 실행: 25개 구 수집·색인(선택)·스냅샷·재측정 (3b) | `data/regions/*.json` 의 `sillok_keywords`(H3 고른 값만), `data/snapshots/catalog/*`(4개 구 기준 재생성), `data/catalog_sources.json`(`seoul_openapi` verified_at·notes), `docs/status/seoul25_2026-10-xx.md`(신규), `docs/status/measure_2026-10-xx.md`(2차 칸), `docs/spikes/sillok.md`(25개 구 절) | T414~T416·T433, D28 | 단독 |

### Stage 4 — TourAPI·좌표 (D25·D26)
| TASK | 제목 | 범위 | 선행 | 병렬 충돌 |
|------|------|------|------|------|
| T419 | TourAPI 수집기·정규화 (4a) | `domains/kcontext/catalog/tourapi.py`(신규), `catalog/sources.py`, `data/catalog_sources.json`(`tourapi_kto` 항목만), `data/tourapi_codes.json`(신규, T401 확인값), `tests/domains/kcontext/catalog/test_kc4_tourapi.py`, `tests/fixtures/tourapi/*.json`(합성) | T401, D26 | 없음 |
| T421 | 병합 규칙 D26 반영 (4a) | `domains/kcontext/catalog/merge.py`, `tests/domains/kcontext/catalog/test_kc4_merge_kto.py` | T416(merge.py), D26 | 없음 |
| T417 | 좌표 자동 부착 — 서울 API 장소, 데이터 기반 이상치 제거 (4a) | `domains/kcontext/places.py`, `domains/kcontext/places_build.py`(신규), `domains/kcontext/data/places/auto_rules.json`(신규), `domains/kcontext/pipeline/run.py`(`_attach_coords` 만), `frontend/k-context/src/lib/chat-bundle.js`, `src/i18n/{ko,en}.js`, `tests/domains/kcontext/test_kc4_places_auto.py`, `frontend/k-context/tests/coordauto.kc4.test.js` | D25 | 없음 |
| T420 | TourAPI 관광지 → 좌표 사전 (4b) | `domains/kcontext/places_build.py`(입력 어댑터), `domains/kcontext/catalog/tourapi.py`(관광지 내보내기 함수·하위 명령만), `tests/domains/kcontext/test_kc4_places_tourapi.py` | T417·T419 | 단독 |
| T422 | 실수집·자동 좌표 생성·보고 (4c) | `docs/status/events_data_2026-10-xx.md`(신규), `catalog_sources.json`(`tourapi_kto` status·verified_at·notes) | T417~T421, (TourAPI 부분) H2 | 단독 |

### Stage 5 — 배포 패키징 (D27)
| TASK | 제목 | 범위 | 선행 | 병렬 충돌 |
|------|------|------|------|------|
| T423 | Dockerfile·이미지 데이터·컨테이너 설정 | `Dockerfile`(신규), `.dockerignore`, **`.gitignore`**(`image-data/`·`dist/` 추가), `deploy/cloudrun/entrypoint.sh`(신규), `deploy/cloudrun/README.md`(신규), `scripts/build_image_data.sh`(신규), `scripts/snapshot_catalog.py`(`--keep-ended` 옵션), `tests/test_kc4_container_files.py`, `tests/test_kc4_image_data_filter.py` | D27, T418·T422 | 없음(`.gitignore` 는 이 태스크만 고침) |
| T424 | Netlify 설정·빌드 스크립트 | `netlify.toml`(신규), `scripts/netlify_build.sh`(신규), `tests/test_kc4_netlify_build.py` | D27, T403·T404 | 없음 |
| T425 | Cloud Run 배포 스크립트·가이드 | `scripts/deploy_cloudrun.sh`(신규), `docs/guides/DEPLOY.md`(신규), `deploy/README.md` | D27, T402 | 없음 |

### Stage 6 — 실제 배포
| TASK | 제목 | 범위 | 선행 | 병렬 충돌 |
|------|------|------|------|------|
| T426 | Cloud Run 배포·공개 URL 남용 점검 | `docs/status/deploy_2026-10-xx.md`(신규) — 코드 변경 없음 | T423·T425, H4·H7·H11 | 단독 |
| T427 | Netlify 배포·카카오 도메인·화면 확인 | 같은 문서에 절 추가 | T424·T426, H5·H6 | 단독(T426 뒤) |

### Stage 7 — 문서
| TASK | 제목 | 범위 | 선행 | 병렬 충돌 |
|------|------|------|------|------|
| T428 | README·상태·가이드 갱신 | `README.md`, `docs/status/2026-10-xx_구현상태.md`(신규), `docs/guides/{SETUP,EVENTS_CATALOG}.md`, `docs/diagram/system-state.html` | T427 | 없음 |
| T429 | 배포 URL 스크린샷 | `docs/demo/s4-0{1..5}-*.png` | T427 | 없음 |

### 스테이지 구성 근거
- **Stage 1**: 결정 문안의 `[확인 필요]` 를 채울 스파이크 4개와, 동작을 바꾸지 않는 이월 3개(T405~T407)를 병렬로 둔다. 검색 개선은 계약(`excluded`)에 닿을 수 있어 **프로파일만** 먼저 하고(T407), 그 결과로 D29 를 올릴지 정한다. 측정(T408)은 프로파일과 같은 데이터 위에서 RSS 를 재야 해서 1b.
- **Stage 2**: 우선순위 ①. 공유 인터페이스(`session.py`·`limits.py`·설정·`app.state`·미들웨어 순서·`session_from_request`·카탈로그 동시성)를 T409 가 먼저 만들어, 2b 의 두 태스크가 서로의 파일에 기대지 않게 했다. 프론트는 §5.1 계약만 알면 되므로 2a 병렬. 2c 에서 공개 모드 전체를 검증한다.
- **Stage 3**: 우선순위 ②. 지역 파일·후보 도구·카탈로그·검색 색인이 서로 다른 파일이라 3a 병렬. 25개 구 수집은 병합 블로킹(T416)과 검색 색인(T433) 없이는 시간·메모리가 감당되지 않으므로 그 뒤 T418.
- **Stage 4**: 우선순위 ③. `merge.py` 는 T416 이 먼저 고치므로 T421 은 여기. 좌표 자동 부착(T417)은 우선순위를 낮춰 TourAPI 관광지 좌표(T420)와 같은 스테이지에 묶었다. `places_build.py` 를 둘이 고치므로 T420 은 4b. 실행(T422)은 4c — 서울 API 쪽 자동 좌표는 키 없이도 만들어진다.
- **Stage 5**: 우선순위 ④ 중 계정이 필요 없는 부분. 이미지 데이터가 T418·T422 산출물에 걸리므로 Stage 4 뒤.
- **Stage 6**: 계정·도메인 등록 필요. Netlify 쪽은 API 원점이 있어야 하므로 순차.
- **Stage 7**: 우선순위 ⑤.

---

## 5. 태스크별 상세 구현 명세

### 5.1 Stage 2 공통 계약 (T409~T413 이 함께 지킨다)

| 항목 | 값 |
|---|---|
| 세션 발급 | `POST /api/session` 본문 없음(또는 `{}`) → 201 `{"session": "<43자>", "ttl_s": 7200}`. 공개·로컬 모드 모두 있음 |
| 세션 헤더 | `X-KC-Session: <토큰>` — 정규식 `^[A-Za-z0-9_-]{43}$`. 틀린 형식은 "없음" |
| 세션 해석 | **`backend/session.py::session_from_request(request) -> Session | None`**(T409). 공개 모드: 헤더 → `store.get`. 로컬 모드: 헤더가 유효하고 찾으면 그 세션, 아니면 `store.local()` |
| 세션 없음/만료 | 공개 모드: `POST /api/messages` → 401 `no_session`, `GET /api/messages`·`GET /api/audit` → 200 `[]` |
| 제한 초과 | 429 `rate_limited` + `Retry-After: <초>` |
| 동시 처리 초과 | 429 `busy`(일정 흐름·세션·카탈로그 자식 프로세스) |
| 일일 상한 | 503 `daily_limit` |
| 공개 모드에서 닫힌 API | 403 `disabled_in_public` |
| 메타 | `GET /api/meta` → `{"schema":"kc-meta/v1","public":bool,"decisions":"open"|"closed","reports":"open"|"closed"}` |
| CORS | **가장 바깥 미들웨어**(모든 오류 응답에 헤더). `allow_headers=["Content-Type","X-Admin-Token","X-KC-Session"]`, `expose_headers=["X-Audit-Skipped","Retry-After"]` |
| API 문서 | 공개 모드: `docs_url=None`, `redoc_url=None`, `openapi_url=None` |
| 설정(env) | `KC_PUBLIC_MODE`(`1`이면 켬) · `KC_TRUSTED_PROXY_HOPS`(0~3, 기본 0) · `KC_LLM_DAILY_UNITS`(0~100000, 기본 300) · `KC_STORY_CONCURRENCY`(1~8, 기본 2) · `KC_CATALOG_CONCURRENCY`(1~8, 기본 3) · `KC_SESSION_TTL_S`(기본 7200) · `KC_SESSION_MAX`(기본 1000). 범위 밖이면 서버 시작 실패 |

---

#### T401 — [스파이크] TourAPI KorService2 + 이용 조건
- **변경 파일**: `docs/spikes/tourapi.md` (신규). 코드 변경 없음.
- **인터페이스**: 절 고정 — ① 출처 목록(URL·확인 날짜) ② 엔드포인트(`https://apis.data.go.kr/B551011/KorService2` 공식 확인 여부) ③ 오퍼레이션 표(이름·용도·필수/선택 파라미터·응답 필드·페이지 방식) ④ 인증(서비스키 파라미터 이름, 인코딩/디코딩 키) ⑤ 호출 한도(개발·운영 계정) ⑥ 응답 형식(JSON 지정, 오류 응답 형태·코드) ⑦ 서울 지역 코드·시군구 코드 조회 방법과 **서울 25개 구 코드 표**(키 있으면 실호출, 없으면 `[확인 필요]`) ⑧ 행사 기간·좌표(축 순서)·수정일·콘텐츠 id 필드 이름 ⑨ **이용 조건**: 공공누리 1·3유형이 어느 항목·필드(텍스트·좌표·사진)에 적용되는지, 항목별 유형 표시 필드가 있는지, 3유형(변경금지)일 때 정규화·병합·요약·저장·이미지 포함·화면 표시가 허용되는지 — 공공누리 공식 설명(kogl.or.kr)과 데이터셋 이용허락 문구를 근거로 **허용/불허/미확인 표** ⑩ T419 의 "확정 필드 목록"과 "쓰지 말 것 목록" ⑪ D26 ⑦ 결론 문장 제안(재배포 가능 범위).
- **핵심 로직**: 공공데이터포털 데이터셋 페이지(`https://www.data.go.kr/data/15101578/openapi.do`)·첨부 활용가이드·한국관광공사 TourAPI 안내·공공누리 유형 설명을 읽는다. 값마다 출처 URL·문서 이름·확인 날짜. H2 키가 있으면 서울 행사 1쪽·관광지 1쪽·코드 조회 1회만(최대 20회) 호출해 필드 이름을 대조 — 원문은 커밋하지 않고 필드 이름·형태만 적는다.
- **엣지 케이스**: 활용가이드가 로그인 뒤에만 받아지면 H2 로 요청하고 `[확인 필요]`. KorService1 문서가 섞이면 버전별로 나누고 KorService2 만 "확정". 이용 조건이 판단되지 않으면 ⑨ 표는 "미확인" — 이 경우 D26 ⑦ 에 따라 재배포하지 않는다.
- **지켜야 할 규칙**: Sprint 2 규칙(확인 전 코드에 이름을 쓰지 않음) · 규칙 1 · D26 ⑦.
- **DoD**: ①~⑪ 절 존재, 모든 표 행에 출처 URL 또는 `[확인 필요]`. `grep -nE "serviceKey=[^<{\[]" docs/spikes/tourapi.md` 0건.
- **병렬 충돌**: 없음.

#### T402 — [스파이크] Cloud Run·Artifact Registry·Secret Manager·Cloud Build
- **변경 파일**: `docs/spikes/cloud_run.md` (신규).
- **인터페이스**: 절 고정 — ① 출처 ② 요청 시간 한도(기본·최대, 플래그) ③ 메모리·CPU 선택지, 인스턴스 파일시스템 쓰기가 메모리에 잡히는지 ④ 무료 사용량(요청·vCPU-초·GiB-초·네트워크, **리전 조건**) ⑤ 결제 계정 필요 여부, 예산 알림 방법 ⑥ 이미지 크기 한도·Artifact Registry 무료 저장 용량 ⑦ Cloud Build 무료 사용량(또는 로컬 `docker build` + push) ⑧ Secret Manager 무료 사용량·env 주입 플래그·서비스 계정 권한 이름 ⑨ `max-instances`·`min-instances`·concurrency 플래그 ⑩ `X-Forwarded-For` 처리(문서 근거) ⑪ 콜드 스타트·시작 프로브·`PORT` ⑫ D27 ③ 권장 값 표(근거 절 번호).
- **핵심 로직**: cloud.google.com 공식 문서·가격 페이지만. 계정 조작 없음.
- **엣지 케이스**: 무료 사용량이 리전에 따라 다르면 서울 리전 포함 여부를 따로 적고, 아니면 "무료 리전 + 지연 증가"를 D27 문안에 반영하도록 권고. 문서끼리 숫자가 다르면 둘 다 + `[확인 필요]`.
- **지켜야 할 규칙**: 기억이 아닌 문서 · 유료 인프라 금지.
- **DoD**: ①~⑫ 존재, ⑫ 모든 값에 근거. "유료가 되는 조건" 목록.
- **병렬 충돌**: 없음.

#### T403 — [스파이크] Netlify 정적 배포·API 연결
- **변경 파일**: `docs/spikes/netlify.md` (신규).
- **인터페이스**: 절 — ① 출처 ② 정적 배포(CLI·Git 연동, publish·build command) ③ 빌드 때 환경변수로 파일 생성, 값이 로그에 찍히는지 ④ **프록시 리라이트의 요청 시간 한도** ⑤ 프록시가 방문자 IP 를 넘기는 헤더 ⑥ `_headers` CSP 와 HTML meta CSP 의 관계(둘 다 적용되는지), Report-Only 지원 ⑦ 무료 플랜 한도 ⑧ 미리보기 도메인 형식 ⑨ 결론: **프록시 vs 직접 CORS** 중 하나(일정 요청 최대 100초, IP 기반 제한, CSP 조건별).
- **핵심 로직**: docs.netlify.com 공식 문서만. 프록시 한도가 100초 미만이거나 문서에 없으면 결론은 **직접 CORS**.
- **엣지 케이스**: 한도가 문서에 없으면 `[확인 필요]` + 결론 직접 CORS(안전한 쪽).
- **지켜야 할 규칙**: 기억이 아닌 문서.
- **DoD**: ①~⑨, ⑨ 에 근거 절 번호. D27 ② 문장 제안.
- **병렬 충돌**: 없음.

#### T404 — [스파이크] 카카오 지도 JS 키 도메인 등록
- **변경 파일**: `docs/spikes/kakao_domain.md` (신규).
- **인터페이스**: 절 — ① 출처 ② 웹 플랫폼 도메인 등록 위치·형식(스킴·포트·와일드카드) ③ 등록 가능 수 ④ 지도 JS SDK 무료 사용량·초과 시 동작 ⑤ JS 키 노출이 설계상 정상인지와 보호 수단 ⑥ 미리보기 도메인 등록 필요 여부 ⑦ JS 키 형식(빌드 스크립트 검증용 — 문서에 형식이 없으면 "검증 안 함, 길이 상한만") ⑧ SDK 가 불러오는 출처(CSP 를 쓸 때 필요한 목록) ⑨ H6 절차 체크리스트.
- **핵심 로직**: 공식 문서만. 키 값은 다루지 않는다.
- **엣지 케이스**: 와일드카드 미지원이면 운영 도메인 1개만, 미리보기는 SVG(D11).
- **지켜야 할 규칙**: 규칙 1.
- **DoD**: ①~⑨, ⑨ 는 번호 매긴 단계.
- **병렬 충돌**: 없음.

#### T405 — 이월: 캐시 키·해석의 today 일관성 (+ W7 LLM_BACKEND)
- **출처**: Sprint 3 "Stage 4 에서 이월" 첫 줄, "Stage 2 에서 이월" W7.
- **변경 파일**: `domains/kcontext/pipeline/__main__.py`, `pipeline/run.py`, `schedule/cache.py`, `schedule/understand.py`(인자 전달만), `tests/domains/kcontext/pipeline/test_kc4_cache_today.py`(신규).
- **인터페이스**:
  - `run_story_pipeline(..., today: date | None = None)` — None 이면 지금처럼.
  - `understand_with_meta(..., today: date | None = None)` — 없으면 추가하고 하위로 넘긴다.
  - `key_for(text, trip, *, root=None, today=None, env=None) -> str` — `today` 를 넣는 조건을 "trip 이 None" 에서 **"trip 이 None 이거나 형식이 틀림"** 으로. `env`(None 이면 `os.environ`)의 `LLM_BACKEND`·`LLM_BACKEND_*` 이름=값을 정렬해 키에 넣는다. 캐시 형식 버전 한 단계 올림(v4 → v5).
- **핵심 로직**: `__main__` 에서 `today = kst_today()` 를 한 번 구해 `key_for(..., today=today)` 와 `run_story_pipeline(..., today=today)` 에 같이 넘긴다. trip 형식 검사는 schedule 의 기존 검사를 재사용하고, 없으면 `cache.py` 사설 `_trip_ok(trip)`(YYYY-MM-DD 두 개, `fromisoformat` 성공, from ≤ to).
- **엣지 케이스**: 자정 경계(`today` 고정 + `kst_today` 다른 날 monkeypatch), 잘못된 trip 은 trip 없는 요청과 다른 키, `LLM_BACKEND` 값이 다르면 다른 키, v4 캐시 무시.
- **지켜야 할 규칙**: D15 ④ · D22 ② · D6.
- **DoD**: `uv run python -m pytest -q tests/domains/kcontext/pipeline/test_kc4_cache_today.py` 통과 + 전체 회귀(§7).
- **병렬 충돌**: 없음.

#### T406 — 이월: 보안 로그 날짜 표시·최신 우선
- **출처**: Sprint 3 "Stage 6 에서 이월".
- **변경 파일**: `frontend/k-context/src/api/http.js`(`sanitizeAuditEntry` 만), `src/components/securitylog/{logic,log-row}.js`, `src/i18n/{ko,en}.js`(필요 키만), `tests/securitylog.kc4.test.js`(신규).
- **인터페이스**: `sanitizeAuditEntry` 가 `at` 보존(문자열·40자 이하·`Date.parse` 유한). `logic.js` export `sortNewestFirst(entries)`(`at` 내림차순, 같은 `at` 은 `id` 오름차순, `at` 없는 항목은 원래 순서로 맨 뒤), `formatWhen(at) -> string|null`(Asia/Seoul `MM-DD HH:MM:SS`).
- **핵심 로직**: 목록은 `sortNewestFirst`, 행은 `formatWhen(at) ?? time`. `Intl.DateTimeFormat` 에 `timeZone: 'Asia/Seoul'`, 부분 조립.
- **엣지 케이스**: mock 데이터(`at` 없음) 무변화. 잘못된 `at` 제거.
- **지켜야 할 규칙**: 프론트는 표 파일만 · 검증된 필드만.
- **DoD**: `(cd frontend/k-context && node --test)` 통과(보존·정렬·포맷·mock 무변화). 실제 서버 보안 로그 확인 기록.
- **병렬 충돌**: 없음.

#### T407 — 이월: 행사 검색 프로파일 (동작 변경 없음)
- **출처**: Sprint 3 "Stage 5 에서 이월" — 검색 1회 약 6초.
- **변경 파일**: `scripts/profile_catalog_search.py`(신규), `docs/status/catalog_search_profile_2026-10-xx.md`(신규). **카탈로그·backend·프론트 코드는 바꾸지 않는다.**
- **인터페이스**: `uv run python scripts/profile_catalog_search.py --catalog var/catalog --trip 2026-10-15..2026-10-18 [--runs 3]` → stdout JSON `{"runs": n, "entries": n, "stages_ms": {"read_file", "json_parse", "entry_from_dict", "search_events", "result_dumps", "subprocess_total"}, "result_bytes": n, "excluded_bytes": n, "events": n, "excluded": n, "max_rss_kb": n}`. 단계별 중앙값.
- **핵심 로직**: 1) 같은 프로세스 안에서 `CatalogStore` 의 파일 읽기 → `json.loads` → `EventEntry` 변환 → `search_events`(데모 문장과 같은 trip·itinerary) → `json.dumps(result)` 를 `time.perf_counter` 로 나눠 잰다(store 내부 함수를 그대로 부르되 코드는 바꾸지 않음 — 필요한 단계가 공개 함수로 없으면 스크립트 안에서 같은 순서로 재현하고 문서에 "재현 경로"라고 적는다). 2) 실제 경로(`python -m domains.kcontext.catalog.api` 자식 프로세스, JSON 한 건)를 3회 재서 `subprocess_total` 과 `ru_maxrss`(RUSAGE_CHILDREN). 3) 문서에 단계별 비율과 **결론: A안(`excluded` 보존, 사전 제외 색인)으로 목표(≤1.5초)에 닿는지 / B안(D29)이 필요한지**를 쓴다. 판단 규칙: `result_dumps` + 자식 → 부모 전송(= `subprocess_total` − 나머지 단계 합) 이 전체의 50% 이상이면 B안 필요 후보.
- **엣지 케이스**: `var/catalog` 없음 → 스냅샷 복원 경로 안내 후 종료 2. 측정 중 데이터 수정 없음(읽기만).
- **지켜야 할 규칙**: D13 ⑤(데이터 수정 없음) · 계약 변경 없음.
- **DoD**: 문서에 단계별 표·결론·D29 필요 여부. ruff 통과. 전체 회귀(코드 변경 없음 확인).
- **병렬 충돌**: 없음.

#### T408 — [측정] 서울 API 전체 행·자원 기준선 (1b, T418 에서 2차)
- **변경 파일**: `scripts/measure_seoul_rows.py`(신규), `scripts/measure_runtime.py`(신규), `docs/status/measure_2026-10-xx.md`(신규).
- **인터페이스**:
  - `uv run python scripts/measure_seoul_rows.py --today YYYY-MM-DD [--max-pages 60]` → `{"list_total_count","fetched","pages","truncated","by_guname":{구:수},"no_guname","not_ended_by_end_date","with_latlng","distinct_place_with_latlng"}`. 키는 `core.llm.envfile` 허용 목록 로더로 `SEOUL_OPENAPI_KEY` 하나만. 행 원문 저장 안 함.
  - `uv run python scripts/measure_runtime.py --catalog <dir> --index var/index/kcontext.db [--with-llm]` → 카탈로그 검색 자식 3회 시간·`ru_maxrss`, 파이프라인 자식 1회(기본은 캐시 적중 문장으로 LLM 0회, `--with-llm` 이면 최대 2회) 시간·`ru_maxrss`, 동시 2건 실행 시 합계 RSS(자식 2개 동시 기동 후 최대값), 파일 크기.
- **핵심 로직**: `seoul.fetch_rows` 재사용(새 HTTP 코드 없음). 문서에 4개 구 대비 25개 구 예상 배수(행 수·끝나지 않은 행 수)와 색인 크기 추정 근거(4개 구 키워드 기사 4,822건 → 43MB). 2차 측정(T418)은 같은 스크립트를 25개 구 카탈로그·새 색인으로 돌려 같은 문서의 "2차" 칸에 채운다.
- **엣지 케이스**: `list_total_count > max_pages*1000` → `truncated: true` 후 멈춤. 키 없음 → 종료 2(키 이름만).
- **지켜야 할 규칙**: 규칙 1 · §6 · D7.
- **DoD**: 1차 표가 문서에 있고 원응답·키 없음. ruff 통과.
- **병렬 충돌**: 1b 단독.

#### T409 — backend 세션·제한 기반 + 설정 + 미들웨어 순서 + 메타 + 카탈로그 동시성
- **변경 파일**: `backend/session.py`(신규), `backend/limits.py`(신규), `backend/routers/meta.py`(신규), `backend/settings.py`, `backend/app.py`, `backend/catalog_runner.py`, `.env.example`, 테스트 3개(신규).
- **인터페이스**:
  ```python
  # backend/session.py — core 만 import (D3·D10)
  TOKEN_RE: re.Pattern  # ^[A-Za-z0-9_-]{43}$
  SESSION_HEADER = "X-KC-Session"
  LOCAL_SESSION_ID = "local"
  @dataclass
  class Session:
      id: str; created: float; last_seen: float
      history: deque  # maxlen=100, (message dict, in_llm_context: bool)
      logs: deque     # maxlen=200, 보안 로그 항목 dict
      seq: int = 0
      busy: threading.Lock   # 세션당 동시 1건
      lock: threading.Lock   # history·logs·seq 보호
  class SessionStore:
      def __init__(self, *, ttl_s: float, max_sessions: int, clock: Callable[[], float] = time.monotonic): ...
      def create(self) -> Session | None   # 상한이면 busy 아닌 LRU 하나 제거, 전부 busy 면 None
      def get(self, token: str | None) -> Session | None
      def local(self) -> Session
      def __len__(self) -> int
  def session_from_request(request) -> Session | None   # §5.1 "세션 해석" 규칙
  # backend/limits.py
  @dataclass(frozen=True)
  class Rule: name: str; limit: int; window_s: int
  RULES: dict[str, tuple[Rule, ...]]   # §6.2 표 그대로
  class RateLimiter:
      def __init__(self, clock=time.monotonic): ...
      def hit(self, bucket: str, key: str, rules: tuple[Rule, ...]) -> int | None  # 허용 None, 거절이면 Retry-After 초
  class DailyBudget:
      def __init__(self, units: int, *, today: Callable[[], date]): ...
      def reserve(self, n: int) -> bool
      def refund(self, n: int) -> None
      @property
      def used(self) -> int
  class AdminGuard:
      def blocked(self, ip: str) -> bool; def fail(self, ip: str) -> None; def ok(self, ip: str) -> None
  def client_ip(request, trusted_hops: int) -> str
  def classify(path: str, method: str) -> str | None
  # backend/catalog_runner.py
  class CatalogBusy(CatalogRunnerError): ...
  def configure_concurrency(n: int) -> None   # 모듈 전역 BoundedSemaphore 교체(앱 시작 때 1회)
  # run_catalog: 시작에서 acquire(blocking=False) 실패 → CatalogBusy, finally release
  ```
  - `Settings` 필드 추가(§5.1 env 전부): `public_mode`, `trusted_proxy_hops`, `llm_daily_units`, `story_concurrency`, `catalog_concurrency`, `session_ttl_s`, `session_max`. 범위 밖이면 `ValueError`.
  - `app.py` 순서(중요): ① `FastAPI(title="backend", docs_url=None if public else "/docs", redoc_url=None if public else "/redoc", openapi_url=None if public else "/openapi.json")` ② `app.state.sessions/limiter/budget/admin_guard`, `configure_concurrency(s.catalog_concurrency)` ③ `@app.middleware("http") _limit_body`(지금 것) ④ `@app.middleware("http") _rate_limit`(공개 모드에서만 적용: `bucket = classify(...)`, 키 IP, `messages` 는 유효 세션이면 세션 키로도) ⑤ **마지막에 `app.add_middleware(CORSMiddleware, ...)`** — 나중에 추가한 미들웨어가 가장 바깥이므로 413·429·403·503 모두 CORS 헤더를 갖는다. ⑥ `_forbidden` 처리기: `_error(403, getattr(exc, "code", "forbidden"), str(exc))`. ⑦ `ROUTERS` 에 `meta.router`(`GET /api/meta`, `POST /api/session` — 발급도 `session_create` 규칙, `create()` 가 None 이면 429 `busy`).
- **핵심 로직**: 고정 창 카운터 `{(bucket, rule.name, key): (window_start, count)}` + `threading.Lock`, 만료 항목은 1,000번에 한 번 정리. `client_ip`: hops 0 → `request.client.host`; 아니면 `X-Forwarded-For` 를 쉼표로 나눠 `parts[-hops]`(길이 부족이면 연결 주소); `ipaddress.ip_address` 실패면 `"unknown"`. `DailyBudget` 날짜는 KST. 토큰은 로그에 sha256 앞 8자만.
- **엣지 케이스**: `request.client` None → `"unknown"`. 세션 TTL 은 `get` 시점 판정. units 0 → LLM 호출 전부 503. 로컬 모드는 `_rate_limit` 통과(기존 테스트 무변화).
- **지켜야 할 규칙**: D24 ①②③④⑤ · D3·D10 · 규칙 1.
- **DoD**: `test_kc4_session.py`(발급 형식·만료·LRU·busy 보호·`session_from_request` 공개/로컬), `test_kc4_limits.py`(창 경계·Retry-After·KST 리셋·refund 하한·client_ip hops 0/1/2/잘못된 헤더·classify·설정 범위), `test_kc4_app_middleware.py`(**공개 모드 429 응답에 `Access-Control-Allow-Origin`**, **413 응답에도 같은 헤더**(허용 origin 으로 요청), preflight 에 `X-KC-Session` 허용, 공개 모드 `/docs`·`/openapi.json` 404, 로컬 모드 `/docs` 200, `CatalogBusy` 가 동시성 상한에서 발생). `uv run python -m pytest -q tests/backend` + 전체 회귀.
- **병렬 충돌**: 없음.

#### T410 — 프론트 세션·제한 오류·배포 주소 설정
- **변경 파일**: `frontend/k-context/src/api/http.js`, `src/api/index.js`, `src/lib/api-base.js`(신규), `src/events/api.js`, `src/components/securitylog/approve-buttons.js`, `src/i18n/{ko,en}.js`, `events.html`, `admin.html`, `config.local.example.js`, `tests/session.kc4.test.js`(신규).
- **인터페이스**:
  - `src/lib/api-base.js`: `export function configuredBase(win = globalThis) -> string|null` — `win.KC_API_BASE` 가 ① 같은 출처 경로(`^/(?!/)[\w\-./]*$`) 또는 ② `https:` 절대 URL(사용자 이름·비밀번호 없음, 끝 `/` 제거)이면 값, 아니면 null.
  - `http.js`: `SESSION_KEY='kc.session'`. `createHttpApi({ baseUrl, storage = globalThis.sessionStorage })` 내부 `ensureSession()`(저장값이 43자 형식이면 그대로, 아니면 `POST /session`). 모든 요청에 `X-KC-Session`. 401 `no_session` 이면 저장값 지우고 **한 번만** 새로 받아 재시도. `ERROR_MESSAGES` 추가: `rate_limited`, `daily_limit`, `disabled_in_public`, `no_session`(초안 문구 그대로). `getMeta()`(실패 시 `{public:false, decisions:'open', reports:'open'}`). `probeBackend` 그대로.
  - `index.js`: 기본 주소 = `configuredBase() ?? 'http://localhost:8000/api'`. `?base=` 검증(`safeBase`)은 그대로.
  - `events/api.js::defaultBase`: `configuredBase()` 를 먼저 본다.
  - **`events.html`·`admin.html`**: `<script src="config.local.js"></script>` 를 모듈 스크립트 앞에 추가(`index.html:13` 과 같은 방식 — 파일이 없으면 404 한 번, 정상). meta CSP 는 `script-src 'self'` 로 이 파일을 허용하므로 그대로. **`connect-src` 정리**: 원본은 로컬 개발용(`'self' http://localhost:* http://127.0.0.1:*`) 그대로 두고, 배포 원점은 T424 가 `dist/` 사본에만 넣는다는 주석을 meta 위에 단다(원본 CSP 문자열은 바꾸지 않아 `tests/events.security.test.js` 가 그대로 통과).
  - `approve-buttons.js`: `ctx.api.meta?.decisions === 'closed'` 이면 버튼 대신 "공개 데모에서는 승인 기능이 닫혀 있어요".
  - `config.local.example.js`: `window.KC_API_BASE = '';` 줄과 주석.
- **핵심 로직**: 저장소 접근 실패면 메모리 변수. mock 모드는 세션·메타를 부르지 않는다.
- **엣지 케이스**: `/session` 이 429 → `rate_limited` 로 끝(무한 재시도 금지). 로컬 backend 도 세션 헤더로 세션별 기록 — 새 탭 = 새 대화(게이트의 의도된 변화).
- **지켜야 할 규칙**: D24 ① · D13 ⑨(`?base=` 제한 유지) · 프론트는 표 파일만.
- **DoD**: `node --test` 통과. 새 테스트: 토큰 저장·재사용, 401 한 번 재시도, 429 문구, `configuredBase` 허용·거부(http 절대 URL·`javascript:`·사용자 정보 거부), 승인 버튼 닫힘, mock 무변화, `events.html`·`admin.html` 에 `config.local.js` 스크립트가 모듈 앞에 있음(파일 파싱 테스트), 기존 `events.security.test.js` 통과.
- **병렬 충돌**: 없음.

#### T411 — 채팅 세션 분리·동시 처리·일일 상한
- **변경 파일**: `backend/chat.py`, `backend/routers/messages.py`, `tests/backend/test_kc4_chat_sessions.py`(신규).
- **인터페이스**:
  - `ChatService.__init__(settings, *, ..., budget: DailyBudget | None = None, story_concurrency: int = 2)`. `_story_lock` → `BoundedSemaphore(story_concurrency)`.
  - `messages(session) -> list[dict]`, `send(text, context, *, session) -> ChatResult`. 인스턴스 `_history`·`_seq` 제거. 메시지 id 는 세션 `seq`.
  - `DailyLimit(Exception)` → 라우터 503 `daily_limit`.
  - 요청별 audit 수집: 모듈 `ContextVar` `_REQ_EVENTS`; `_TeeSink.write` 가 공유 JSONL 에 쓰고 현재 컨텍스트 목록에도 append. `send` 시작 `set([])`, 끝 `reset`. `mark()/since()` 제거. `asyncio.to_thread` 는 컨텍스트를 복사하므로 스레드 안 audit 도 잡힌다.
  - `_search_events(args, timeout_s)` — 한도를 인자로(`self._search_timeout_s` 제거). `CatalogBusy` 는 `CatalogRunnerError` 하위라 기존 행사 검색 실패 처리(`EVENTS_UNAVAILABLE`)로 간다 — `attach_events` 의 예외 처리가 이를 잡는지 확인하고, 안 잡으면 `_search_events` 에서 잡아 같은 경로로.
  - `messages.py`: 세션은 **`session_from_request`(T409)** 로만. `GET /api/messages`: None 이면 `[]`. `POST`: 공개 모드에서 None → 401 `no_session`. `session.busy.acquire(blocking=False)` 실패 → 429 `busy`. 끝나면 세션 `logs` 에 이번 logs 추가.
- **핵심 로직**:
  1) 주입·경로 검사(예산 소모 없음) → 일정 게이트면: `reserve(2)` 실패 → `DailyLimit`; 슬롯 실패 → `refund(2)` 후 `ChatBusy`. 끝나면 `schedule.attempts`(없으면 2)로 `refund(2 - min(attempts, 2))`. `StoryRunnerError` 면 환불 없음. 일반 챗봇으로 넘어가면 그때 `reserve(1)`.
  2) 일반 챗봇: `reserve(1)` 실패 → `DailyLimit`; `client.busy` → `refund(1)` 후 `ChatBusy`.
  3) LLM 맥락은 그 세션 history 에서만. `budget is None`(로컬 기본) 이면 예산 생략.
- **엣지 케이스**: 같은 세션 동시 2요청 → 두 번째 429. 세션 3개 동시 일정 → 2 처리·1 429. 예산 1 남았을 때 일정 문장 → 503(부분 예약 금지). 처리 중 세션은 `busy` 라 LRU 제거 대상 아님. 캐시 적중 → 2 환불.
- **지켜야 할 규칙**: D24 ①②③ · D15 ⑤ · D17 · D3·D10.
- **DoD**: `test_kc4_chat_sessions.py`(세션 간 비노출, LLM 맥락 분리, 동시 요청 로그 비섞임 — 가짜 transport 2개 `asyncio.gather`, 슬롯·세션 상한, 예산 예약·환불, 로컬 모드 헤더 없이 기존 동작). 기존 `tests/backend/test_kc3_chat_*`·`tests/test_kc3_e2e_chat.py` 통과(시그니처 변경에 맞춘 호출부 수정만, 기대값 변경 금지). `eval/kc.py run --check` 0.
- **병렬 충돌**: 없음.

#### T412 — 공개 모드 보안 로그·승인·관리자·제보
- **변경 파일**: `backend/routers/review.py`, `backend/routers/events.py`, `tests/backend/test_kc4_public_mode.py`(신규).
- **인터페이스**:
  - `review.py::get_audit`: 공개 모드면 `session_from_request` → None 이면 `[]`, 있으면 `session.logs` 를 `at` 오름차순. 로컬 모드는 지금 그대로.
  - `review.py::decide`: 공개 모드면 403 `disabled_in_public`.
  - `events.py`: `Forbidden` 에 `code` 속성(기본 `"forbidden"`). `require_admin`: 공개 모드면 `Forbidden(code="disabled_in_public")`. 로컬 모드: `admin_guard.blocked(ip)` 면 403, 실패 `fail(ip)`, 성공 `ok(ip)`. `submit_report`: 공개 모드면 403 `disabled_in_public`. `_call`: `CatalogBusy` 를 `CatalogRunnerError` 보다 먼저 잡아 429 `busy`.
- **핵심 로직**: 공개 여부는 `request.app.state.settings.public_mode` 한 곳에서.
- **엣지 케이스**: 공개 모드에서 맞는 관리자 토큰도 403. 로컬 모드 관리자 실패 5회 → 15분 403, 성공 시 초기화.
- **지켜야 할 규칙**: D24 ⑤ · D2 · D13 ⑧.
- **DoD**: `test_kc4_public_mode.py`(audit 세션 분리, decision·admin·reports 403, 로컬 모드 기존 동작, 관리자 차단(가짜 시계), `CatalogBusy` → 429). 기존 `tests/backend/*` 통과.
- **병렬 충돌**: 없음.

#### T413 — 공개 모드 통합 테스트·로컬 공개 모드 실행
- **변경 파일**: `tests/test_kc4_public_e2e.py`(신규), `scripts/kc_demo.sh`.
- **인터페이스**: `bash scripts/kc_demo.sh --public` = `KC_PUBLIC_MODE=1 KC_LLM_DAILY_UNITS=${KC_LLM_DAILY_UNITS:-20}` 로 기동. 옵션 파싱을 여러 인자로(`--public --smoke`, 순서 무관).
- **핵심 로직(테스트)**: `create_app(Settings(..., public_mode=True))`·가짜 LLM transport·`run_story` monkeypatch 로 ① 세션 분리 ② `messages` 6번째 429 + `Retry-After` + CORS 헤더 ③ 일일 상한 0 → 503 ④ 관리자·승인·제보 403 ⑤ preflight `X-KC-Session` ⑥ `/api/meta` ⑦ `/docs` 404.
- **엣지 케이스**: 기존 옵션 동작 변화 없음.
- **지켜야 할 규칙**: D24 · 규칙 1.
- **DoD**: 테스트 통과, `kc_demo.sh --check`·`--smoke`·`--public --smoke` 0, 전체 회귀.
- **병렬 충돌**: 단독.

#### T414 — 지역 파일 21개 + 기존 지역 테스트 fixture 전환
- **변경 파일**: `domains/kcontext/data/regions/*.json` 신규 21개, `tests/domains/kcontext/test_kc_regions.py`(`test_real_regions_load` 만), `tests/fixtures/regions4/{gangnam,jongno,jung,mapo}.json`(신규, 현재 파일의 바이트 사본), `tests/domains/kcontext/test_kc4_regions25.py`(신규).
- **인터페이스**: 지역 파일 `{"id","name":{"ko","en"},"gu":["<구 이름>"],"bbox":null,"center":null,"keywords":["<구 이름>"],"sillok_keywords":[],"note":"..."}`. id 는 공식 영문 표기에서 `-gu` 를 뗀 소문자(하이픈·공백 → `_`).
- **핵심 로직**: 1) 서울시 공식 자치구 목록 페이지(URL·확인일을 `note` 에)에서 한글 이름·영문 표기를 옮긴다. 기존 4개 파일은 건드리지 않는다. 2) `keywords` 는 구 이름 하나, `sillok_keywords` 는 빈 목록(D28 ③). 3) **`test_kc_regions.py:31` 의 4개 단언은 기대값을 바꾸지 않는다** — `test_real_regions_load` 를 `load_regions(REPO / "tests/fixtures/regions4")` 로 바꿔 같은 단언(`{"gangnam","jongno","jung","mapo"}`, bbox·center None)을 유지한다. 4) 실제 폴더 25개 검사는 새 `test_kc4_regions25.py` 에.
- **엣지 케이스**: 공식 페이지에 영문 표기가 없으면 로마자 표기를 지어내지 않고 `"name.en": "<한글 이름> [확인 필요]"`. `_region_field` 규칙상 빈 키워드 구는 색인에 없음 — 테스트로 고정. 실제 폴더 개수에 의존하는 다른 기존 테스트가 있으면 같은 방식(fixture 전환, 기대값 유지)으로만 고치고 목록을 완료 기록에 남긴다.
- **지켜야 할 규칙**: 지역은 데이터 파일에만 · 사실 지어내지 않기 · 기대값 변경 금지.
- **DoD**: `load_regions()` 25개·id 중복 없음·`gu` 합집합 25개, 기존 4개 지역 파일 git diff 0, `test_kc_regions.py` 통과(단언 동일), 전체 회귀.
- **병렬 충돌**: 없음.

#### T415 — 실록 키워드 측정·자동 후보 도구
- **변경 파일**: `domains/kcontext/ingest/sillok_keywords.py`(신규), `tests/domains/kcontext/ingest/test_kc4_sillok_keywords.py`(신규), `docs/spikes/sillok_candidates.md`(신규).
- **인터페이스**:
  - `python -m domains.kcontext.ingest.sillok_keywords count --src <XML> --candidates <json> [--out <json>]` — candidates `{"<region_id>": ["<한자>", ...]}` → `{"<region_id>": {"<kw>": {"title","body","articles"}}, "_meta": {...}}`.
  - `... places --src <XML> [--top 500]` — `<index type="지명">` 태그 빈도 상위 N.
  - **`... candidates --src <XML> --dongs <json> --readings <txt> [--top 2000] [--out <json>]`** — 자동 후보. `--dongs` = `{"<구 이름>": ["<동 이름>", ...]}`(서울 열린데이터광장의 구별 행정동 목록에서 만든 파일, 아래), `--readings` = 한자 → 한글 독음 표(Unicode Unihan `kHangul` 필드 파일). 출력 `{"<region_id>": [{"tag": "<한자>", "reading": "<한글>", "dong": "<동 이름>", "articles": n}]}`(건수 내림차순).
  - 함수: `count_keywords(src, candidates) -> dict`, `top_place_tags(src, top) -> list[tuple[str, int]]`, `make_candidates(tags, dongs_by_gu, readings, regions) -> dict`.
- **핵심 로직(candidates)**: 1) 상위 지명 태그 각각을 독음 표로 한글로 읽는다(글자마다 첫 독음, 독음이 여럿인 글자는 모든 조합 — 최대 8조합). 2) 동 이름에서 끝의 "동"과 숫자·"제n" 접미를 뗀 어근과 **완전 일치**하는 조합이 있으면 그 동의 구로 후보. 3) 한 태그가 여러 구에 걸리면 모두 후보로 내고 `ambiguous: true`. 4) 각 후보에 `count_keywords` 건수를 붙인다. **도구는 지역 파일을 고치지 않는다** — 사람이 골라 T418 에서 넣는다(D28 ②).
- **입력 데이터 출처(문서 `sillok_candidates.md`)**: ① 구별 행정동 목록 — 서울 열린데이터광장의 해당 데이터셋 URL·이용 조건·확인일을 dev 가 찾아 적고, 받은 파일은 `var/data/dongs.json`(커밋 안 함)으로. 키가 필요한 API 면 기존 `SEOUL_OPENAPI_KEY` 로 1회(§6 서울 API 상한 안). ② Unihan — unicode.org 의 Unihan 데이터 파일 URL·버전·라이선스(Unicode License)를 적고 `var/data/Unihan_Readings.txt` 로(커밋 안 함). 둘 다 못 구하면 `candidates` 는 문서만 남기고 `count`·`places` 만 완료.
- **엣지 케이스**: D14 검사로 거른 파일은 `_meta.skipped_files`. 독음 없는 글자가 있으면 그 태그는 건너뜀. 일반명사 동명(예: 방위·관청 이름)은 도구가 거르지 않는다 — 건수와 함께 사람이 판단.
- **지켜야 할 규칙**: D14(파서 재사용) · D28 ② · D7 · 사실 지어내지 않기(도구는 후보만).
- **DoD**: 합성 XML 3개·합성 동 목록·합성 독음 표(`○` 대신 테스트 전용 가짜 문자 매핑)로 count·places·candidates(일치·모호·독음 없음) 검증. ruff 통과. 실제 원본으로 `places --top 50` 1회 실행 시간 메모(T418 문서로).
- **병렬 충돌**: 없음.

#### T416 — 카탈로그 25개 구: 전체 별칭·서울 API 쪽 상한·월 버킷 병합 블로킹
- **변경 파일**: `domains/kcontext/catalog/{target,seoul,merge}.py`, `.env.example`, `scripts/kc_demo.sh`, 테스트 2개(신규).
- **근거(계측, dev)**: 현 `_group` 은 2,000건 4.9초(쌍당 약 2.5µs) → 8.7k건 약 95초, 3만 건 약 18분. 25개 구 수집(T418) 전에 줄여야 한다.
- **인터페이스**:
  - `target.py`: spec 이 정확히 `"all"` 이면 `load_regions()` 의 모든 id. `ALL = "all"` export. `"all,jung"` 처럼 섞으면 ValueError.
  - `seoul.py::fetch_rows(..., max_pages: int = 60)` — 첫 쪽 `list_total_count` 로 `ceil(total/page_size) > max_pages` 이면 `SeoulApiError("행 수가 쪽 상한을 넘는다 (total=…, max_pages=…)")`(수집 실패 — D13 ⑤ 로 기존 데이터 유지). 조용히 잘리지 않는다.
  - `merge.py::_group` 블로킹(결과 동등):
    - 관찰값의 블록 키 = `{"id:"+외부 id 각각}` ∪ `{"m:"+YYYY-MM | _days(o.schedule) 의 각 날짜가 속한 달}` — **기간 상한 없음**(긴 행사는 걸친 모든 달을 키로 가진다. 10년짜리면 120개).
    - 그룹마다 구성원 키의 합집합을 색인 `key → {그룹 번호}` 에 등록.
    - 새 관찰값 `o` 의 후보 그룹 = 자기 키 중 하나라도 공유하는 그룹들. **후보를 그룹 생성 순(번호 오름차순)으로** 돌며 기존과 똑같이 `all(same_event(o, x) for x in g)` 인 첫 그룹에 넣는다.
    - **동등성 근거**: `same_event(o, x)` 가 참이려면 (a) 외부 id 공유 → `id:` 키 공유, 또는 (b) 날짜 교집합이 비어 있지 않음 → 그 날짜의 달 키 공유. `o` 가 그룹 `g` 에 들어가려면 `g` 의 모든 구성원과 참이어야 하므로 특히 첫 구성원과 키를 공유한다 → `g` 는 반드시 후보에 있다. 후보 순서가 원래 순서와 같으므로 "첫 그룹" 도 같다. 날짜가 없는 관찰값은 달 키가 없어 외부 id 공유 그룹만 후보 — 원래도 외부 id 공유 없이는 합쳐지지 않는다(`same_event` 의 날짜 조건). `demo` 불일치는 `same_event` 가 그대로 거른다.
  - `.env.example`: `KC_TARGET_REGION` 기본값 줄은 그대로(4개 구) 두고 "`all` = data/regions 의 모든 구(수집이 오래 걸림, 배포 이미지는 all)" 설명 줄 추가.
  - `kc_demo.sh`: `REGIONS="${KC_DEMO_REGIONS:-jung,jongno,mapo,gangnam}"` — 기본 4개 구 유지, `KC_DEMO_REGIONS=all` 로 25개 구.
- **엣지 케이스**: 키 하나에 그룹이 아주 많이 몰리는 달(행사 집중) — 정확성에는 영향 없고 속도만. 세션 날짜(`sessions`)도 `_days` 에 포함되므로 그대로 키가 된다.
- **지켜야 할 규칙**: D13 ③(묶기 규칙 불변) · D13 ⑤ · 지역은 데이터에서.
- **DoD**: `test_kc4_target_all.py`. `test_kc4_merge_blocking.py`: 옛 `_group` 을 테스트 안에 복사한 기준 구현과 **그룹 구성이 같음** — 시드 고정 합성 관찰값 300개에 반드시 포함: ① **긴 기간(2년) × 짧은 기간(1일, 그 사이 임의 날짜)** 같은 장소·제목 유사 ② 긴 기간 × 기간 밖 짧은 행사 ③ 날짜 없음 + 외부 id 공유 ④ 날짜 없음 + 공유 없음 ⑤ 같은 체계 다른 외부 id ⑥ 달 경계(1/31 ~ 2/1) ⑦ 세션 날짜만 있는 관찰값 ⑧ demo 섞임. 추가로 실제 `var/catalog` 관찰값으로 두 구현의 결과가 같은지 1회(시간 기록, 테스트 밖 메모). `kc_demo.sh --check`·`--smoke` 0. 전체 회귀.
- **병렬 충돌**: 없음.

#### T433 — 행사 검색 사전 제외 색인
- **출처**: Sprint 3 "Stage 5 에서 이월" 검색 6초. T407 프로파일 결론에 따라 A안(기본) 또는 B안(D29 승인 시).
- **변경 파일**: A안 — `domains/kcontext/catalog/{store,query,api,__main__}.py`, `scripts/snapshot_catalog.py`(복원 끝에 색인 생성 1줄), `tests/domains/kcontext/catalog/test_kc4_search_index.py`. B안 — 위 + `backend/chat_story.py`, `frontend/k-context/src/events/{view,logic,api}.js`, `docs/chat-bundle.contract.md`, `frontend/k-context/tests/events.excluded.kc4.test.js`.
- **A안 인터페이스(계약 불변)**:
  - `query.py`: 종료·취소 사유 문자열을 상수 `REASON_ENDED`·`REASON_CANCELLED` 로 꺼낸다(값 변경 금지). `search_events(entries, a, *, now, coverage, pre_excluded: Sequence[tuple[int, dict]] | None = None, positions: Sequence[int] | None = None)` — `positions` 는 `entries` 각 항목의 원래 순번, `pre_excluded` 는 `(원래 순번, {"id","title","reason"})`. 결과의 `excluded` 는 루프에서 생긴 항목과 `pre_excluded` 를 **원래 순번으로 병합**해 전체 경로와 같은 순서를 만든다. `counts.excluded` 도 합.
  - `store.py`: `SEARCH_INDEX="search_index.json"` 형식 `{"schema":"kc-search-index/v1","built_at","indexed_at","total","candidates":[{"pos":i,"entry":{...}}],"pre_excluded":[{"pos":i,"id","title","reason"}]}`. `save_search_index(entries, built_at, now)`, `load_search_index()`. `save_entries` 끝에서 자동 생성(같은 잠금 안).
  - `api.py::_search`: 색인이 있고 schema 맞고 `built_at == store.entries_built_at()` 이고 `now >= indexed_at` 이면 색인 경로, 아니면 전체 경로.
  - `__main__.py`: 하위 명령 `reindex`.
- **핵심 로직**: `indexed_at` 시점 `event_lifecycle(e, now)` 가 `ended`·`cancelled` 인 항목은 `EventEntry` 전체 대신 `{id,title,reason}` 만 저장(사유 문자열은 `search_events` 가 붙였을 것과 같은 상수). 시간은 앞으로만 가므로 `now_search >= indexed_at` 이면 결과가 같다. 그 밖 규칙(D23 등)은 검색 시점에 그대로.
- **B안(D29 승인 시에만)**: `search_events` 결과의 `excluded` 를 앞 20건 표본 + `excluded_total` + `excluded_by_reason` 으로(묶음 `_shrink_excluded` 와 같은 모양으로 맞추고 backend 는 이미 요약된 값을 그대로 쓴다). 행사 화면 `view.js:135` 는 "제외된 항목 n건 보기"의 n 을 `excluded_total` 로, 목록은 표본 + 사유별 수. 계약 문서 갱신.
- **엣지 케이스**: 색인 없음·schema 다름·`built_at` 불일치·`now < indexed_at`·파일 깨짐 → 전체 경로(조용한 폴백, 경고 로그만). `postponed`·`unknown` 은 후보에 남김.
- **지켜야 할 규칙**: D13 ⑤(entries.json 그대로, 색인은 파생물) · D23 · D10 · 계약 변경은 D29 승인 시에만.
- **DoD**: ① `test_kc4_search_index.py`: 합성 항목(끝남·취소·진행·종료일 없음 1년 초과·이내·연기)으로 **전체 경로와 색인 경로의 결과 dict 가 같음 — `events`·`counts`·`excluded`(순서까지)**, 폴백 5종. ② 실제 `var/catalog` 에서 `reindex` 뒤 데모 문장 검색 결과를 변경 전 결과와 비교(`excluded` 목록 동일 — 파일로 떠서 diff, 커밋 안 함), 시간 3회 중앙값(목표 ≤ 1.5초, 못 미치면 값·원인 기록 후 D29 제안). ③ **행사 화면 확인**: `events.html` 에서 같은 검색의 "제외된 항목 n건 보기" n 이 변경 전과 같음(헤드리스 또는 수동 기록). ④ B안이면 `events.excluded.kc4.test.js` 와 계약 문서 diff 를 reviewer 가 확인. ⑤ 전체 회귀.
- **병렬 충돌**: 없음.

#### T418 — 실행: 25개 구 수집·색인(선택)·스냅샷·재측정
- **수행자**: 코디네이터(실호출·대용량). dev 는 명령·문서 틀 준비.
- **변경 파일**: `data/regions/*.json` 의 `sillok_keywords`(H3 가 고른 값만, `note` 에 고른 사람·날짜·후보 근거), `data/snapshots/catalog/*`(4개 구 기준 재생성), `data/catalog_sources.json`, `docs/status/seoul25_2026-10-xx.md`(신규), `docs/status/measure_2026-10-xx.md`(2차), `docs/spikes/sillok.md`(25개 구 절).
- **순서**:
  1) (선택) T415 `candidates` 출력을 사람에게 → 고른 키워드를 지역 파일에 → 색인 재구축 `--db var/index/kcontext.new.db --mode regions` → `index stats` → D28 ④ 상한 안이면 교체(기존은 `kcontext.4gu.db` 로 보관). H3 가 없으면 건너뛰고 "색인 = 4개 구 키워드, 나머지 21개 구는 실록 색인 대상 아님".
  2) 서울 API 25개 구: `KC_CATALOG_DIR=var/catalog.all KC_TARGET_REGION=all uv run python -m domains.kcontext.catalog --region all update --source seoul_openapi` → `catalog reindex`. **로컬 데모용 `var/catalog`(4개 구)는 그대로 둔다** — 배포 이미지는 `var/catalog.all` 을 쓴다(D27 ④⑤). 병합 시간 기록.
  3) 로컬 4개 구도 같은 날 갱신(`var/catalog`, 4개 구) → 스냅샷 재생성(D19).
  4) 측정: T408 `measure_runtime.py` 를 `var/catalog.all`·새 색인으로 2차 실행. 실제 서버(`KC_CATALOG_DIR=var/catalog.all KC_TARGET_REGION=all`)에서 데모 문장 + 새 구 문장 2개(합성 일정, 실제 장소 이름) 1회씩.
- **엣지 케이스**: 쪽 상한 초과(T416) → T408 측정값 기준으로 `--max-pages` 를 올려 재실행(§6 상한 안). 병합이 예상보다 길면 시간 기록 후 계속.
- **지켜야 할 규칙**: D28 · D19 · D7 · §6 · 규칙 1.
- **DoD**: 문서에 구별 행사 수·병합 시간·검색 시간·색인 크기(교체 여부)·실서버 3문장 결과·2차 RSS. 스냅샷 크기 기록(5MB 넘으면 사람 확인). 회귀 + `kc_demo.sh --check` 0.
- **병렬 충돌**: 단독.

#### T419 — TourAPI 수집기·정규화
- **선행 조건**: T401 "확정 필드 목록". 그 밖의 이름은 쓰지 않는다.
- **변경 파일**: `domains/kcontext/catalog/tourapi.py`(신규), `catalog/sources.py`, `data/catalog_sources.json`(`tourapi_kto` 의 `status: "implemented_unverified"`·notes — 이용 조건 결론을 notes 에), `data/tourapi_codes.json`(신규, T401 ⑦), `tests/domains/kcontext/catalog/test_kc4_tourapi.py`, `tests/fixtures/tourapi/*.json`(합성).
- **인터페이스**:
  ```python
  KEY_ENV = "DATA_GO_KR_SERVICE_KEY"
  BASE = "https://apis.data.go.kr/B551011/KorService2"  # T401 확인값
  SOURCE_ID = "tourapi_kto"
  class TourApiError(RuntimeError): ...
  def fetch_festivals(key: str, *, start_date: str, client: httpx.Client | None = None,
                      max_calls: int = 200, page_size: int = <T401 최대값>) -> tuple[list[dict], dict]
  def fetch_attractions(key: str, *, client=None, max_calls: int = 200) -> tuple[list[dict], dict]
  def observation_from_item(item: Mapping, region: Region, *, collected_at: str) -> Observation | None
  def observations_from_items(items, region, *, collected_at) -> tuple[list[Observation], list[str]]
  ```
  두 번째 반환값 `{"calls","total","truncated"}`.
- **핵심 로직**: 파라미터는 T401 표대로(지역 코드는 `tourapi_codes.json`). `max_calls` 초과 시 멈추고 `truncated=True`. 관찰값 `external_ids=("kto:<id>",)`, evidence `official_api`, 시군구 코드 → 구 이름은 코드표로만, 좌표는 T401 축 순서대로. 예약·언어·참여조건은 T401 확인 필드만(D13 ①). 오류 메시지에 URL·키 금지.
- **엣지 케이스**: XML 오류 응답 → 코드만 추출. 0건 정상. 중복 id 하나로. 날짜 형식 불일치 → 항목 버리고 problem.
- **지켜야 할 규칙**: D26 ①⑥⑦ · D13 ①②⑤ · D7 · 규칙 1 · §6.1.
- **DoD**: `httpx.MockTransport` 로 쪽 넘김·`max_calls`·오류·URL 미노출·변환·코드표 밖 구. 키 없을 때 `catalog update --source tourapi_kto` 가 runs 에 "키 없음" + 종료 0(서울 API 방식과 같은지 확인). 전체 회귀.
- **병렬 충돌**: 없음.

#### T421 — 병합 규칙 D26 반영
- **변경 파일**: `domains/kcontext/catalog/merge.py`, `tests/domains/kcontext/catalog/test_kc4_merge_kto.py`(신규).
- **인터페이스**: 독립 출처 계산이 있으면(dev 가 위치 확인) `kto:`·`seoul_cult:` 공존 그룹은 독립 1. `same_event` 불변. T416 의 블로킹은 `id:` 키에 `kto:` 도 자연히 포함.
- **핵심 로직**: 합성 4케이스 — 교차 체계 같은 행사 → 한 항목 / 같은 `kto:` 체계 다른 값 → 둘 / 기간 불일치 → 둘 / 필드 충돌 → `conflict`·값 비움.
- **엣지 케이스**: 독립 출처 계산이 없으면 테스트만 추가하고 "D26 ③ 현재 코드에서 자동 충족" 기록.
- **지켜야 할 규칙**: D26 · D13 ③④.
- **DoD**: 4케이스 + T416 블로킹 동등성 테스트 재통과 + 전체 회귀.
- **병렬 충돌**: 없음.

#### T417 — 좌표 자동 부착 (서울 API 장소, 데이터 기반 이상치 제거)
- **변경 파일**: `domains/kcontext/places.py`, `domains/kcontext/places_build.py`(신규), `domains/kcontext/data/places/auto_rules.json`(신규), `domains/kcontext/pipeline/run.py`(`_attach_coords` 만), `frontend/k-context/src/lib/chat-bundle.js`, `src/i18n/{ko,en}.js`, `tests/domains/kcontext/test_kc4_places_auto.py`, `frontend/k-context/tests/coordauto.kc4.test.js`.
- **인터페이스**:
  - `places.py`: `Place.auto: bool = False`. `auto_path()` = env `KC_AUTO_PLACES` 또는 `<var>/places/auto_places.json`. `load_places(path=None, *, auto="default")` — 사람 사전 먼저, 자동 파일이 있으면 읽되 사람 이름·별칭과 겹치는 자동 항목은 버림. 자동 파일 없음·깨짐 → 사람 사전만 + 경고 1줄.
  - `places_build.py`: `python -m domains.kcontext.places_build --catalog <dir> --rules domains/kcontext/data/places/auto_rules.json --out var/places/auto_places.json --collected-at YYYY-MM-DD [--sources seoul_openapi]` → 요약 `{"names_seen","accepted","ambiguous","far_from_gu","no_gu","shadowed_by_manual"}`. 함수 `build_from_observations(observations, rules, manual, collected_at) -> tuple[list[dict], dict]`.
  - `auto_rules.json`: `{"max_spread_m": 150, "max_gu_dist_km": 8, "note": "max_gu_dist_km 는 제안값 — T422 에서 구별 거리 분포를 보고 조정(D25 ③)"}`. **사람이 정하는 범위 값 없음.**
  - `run.py::_attach_coords`: `place.auto` 면 `COORD_AUTO` 문제("이름: 공공 데이터 좌표(사람 확인 전)").
  - 프론트: `PROBLEM_KEYS.COORD_AUTO`, `NAMED` 추가, `problemName` 은 `COORD_UNKNOWN` 과 같은 "이름: …" 규칙. i18n `bundle.problem.coord_auto`(+`.named`).
- **핵심 로직(빌더)**: 1) `source_id` 가 `--sources` 에 있고(기본 `seoul_openapi`) 장소명·위경도·구(GUNAME)가 있는 관찰값만. 구 없음 → `no_gu`. 2) 구별로 모든 좌표의 중앙값을 구하고 `max_gu_dist_km` 넘게 떨어진 좌표는 버림(`far_from_gu`). 3) 남은 좌표를 장소명 `norm()` 으로 묶어 중앙값, 모든 점이 `max_spread_m` 안이면 채택, 아니면 `ambiguous`. 4) 사람 사전과 겹치면 `shadowed_by_manual`. 5) 항목 `{"name": 가장 흔한 표기, "aliases": [], "lat","lng", "source": "서울 열린데이터광장 문화행사 장소 좌표 (행 n건)", "verified_at", "note": "자동 생성(D25)", "auto": true, "origin": ["seoul_openapi"]}` — `origin` 은 이미지 필터(T423)용. 6) 이름순 정렬.
- **엣지 케이스**: 구 표본이 3개 미만이면 그 구의 이상치 판정을 건너뛰지 않고 그 구 좌표 전체를 `far_from_gu` 로 버림(근거 부족). 이름 200자 초과 제외.
- **지켜야 할 규칙**: D25 ①~⑧ · 공공누리 출처 표시(`source`) · 자동 파일은 `var/` · 게이트 사본 불변.
- **DoD**: `test_kc4_places_auto.py`(구 중앙값 이상치·모호·사람 우선·구 없음·표본 부족·자동 파일 깨짐 경고·`COORD_AUTO`), `coordauto.kc4.test.js`. 자동 파일 없는 기본 상태에서 기존 결과 불변. 전체 회귀.
- **병렬 충돌**: 없음.

#### T420 — TourAPI 관광지 → 좌표 사전
- **변경 파일**: `domains/kcontext/places_build.py`(입력 어댑터), `domains/kcontext/catalog/tourapi.py`(`export_attractions(items) -> list[dict]`·하위 명령 `attractions --out <jsonl>` 만), `tests/domains/kcontext/test_kc4_places_tourapi.py`.
- **인터페이스**: `places_build ... --tourapi-attractions var/data/tourapi/attractions.jsonl`. JSONL 줄 `{"name","lat","lng","gu","content_id","collected_at"}`(정규화 줄, 원응답 아님). `--sources` 에 `tourapi_kto` 가 있을 때만 이 입력을 쓴다(기본 꺼짐 — D26 ⑦).
- **핵심 로직**: T417 과 같은 규칙(구 중앙값 이상치·150m·사람 우선). 같은 이름이 두 출처에 있고 150m 안이면 하나(`origin` 에 둘 다), 밖이면 모호. `source` "한국관광공사 TourAPI 관광지 좌표".
- **엣지 케이스**: 이름에 괄호 설명이 붙어도 별칭을 만들지 않는다(추측 금지).
- **지켜야 할 규칙**: D25 · D26 ⑤⑦.
- **DoD**: 테스트(두 출처 병합·충돌·사람 우선·기본 꺼짐) + 전체 회귀.
- **병렬 충돌**: 단독(4b).

#### T422 — 실수집·자동 좌표 생성·보고
- **수행자**: 코디네이터.
- **변경 파일**: `docs/status/events_data_2026-10-xx.md`(신규), `catalog_sources.json`(`tourapi_kto`).
- **순서**: ① **(키 없이)** `places_build --catalog var/catalog.all --sources seoul_openapi` → 자동 좌표, `max_gu_dist_km` 분포 확인 후 필요하면 `auto_rules.json` 값 조정(근거를 note 에). ② (H2 있으면) TourAPI 행사 수집을 **`var/catalog.all` 의 사본(`var/catalog.kto`)** 에 → 병합 결과 확인(합쳐진 수·conflict 표본 5건) ③ 관광지 내보내기 → `places_build --sources seoul_openapi,tourapi_kto --out var/places/auto_places.kto.json`(시험용, 이미지에는 안 씀 — D26 ⑦ 확정 전) ④ 실서버 데모 문장 + 새 구 문장 1회씩(자동 좌표로 핀이 생기는지, `COORD_AUTO` 문구) ⑤ 보고서.
- **엣지 케이스**: TourAPI 키 없음 → ②③ "실행 대기 — H2". 일일 한도 도달 → 다음 날 재개. T401 이 TourAPI 재배포를 허용으로 확정했다면 ③ 을 정식 파일로 승격하는 결정을 사람에게 요청(자동 승격 안 함).
- **지켜야 할 규칙**: §6 · D25 · D26 ⑦ · D19.
- **DoD**: 보고서(자동 좌표 수·버린 사유별 수·TourAPI 결과 또는 실행 대기) + 회귀 + `kc_demo.sh --check` 0.
- **병렬 충돌**: 단독.

#### T423 — Dockerfile·이미지 데이터·컨테이너 설정
- **변경 파일**: `Dockerfile`(신규), `.dockerignore`, **`.gitignore`**(`image-data/`·`dist/` 추가 — 이 태스크만 고친다), `deploy/cloudrun/entrypoint.sh`(신규), `deploy/cloudrun/README.md`(신규), `scripts/build_image_data.sh`(신규), `scripts/snapshot_catalog.py`(`--keep-ended` 옵션), `tests/test_kc4_container_files.py`, `tests/test_kc4_image_data_filter.py`.
- **인터페이스**:
  - 이미지: 파이썬 3.12 slim 계열(태그 고정), `uv sync --frozen --no-dev`, 비루트, `/app`. 복사: `core/ backend/ domains/ deploy/llm.chat.yaml pyproject.toml uv.lock image-data/ → /app/var/`.
  - **`scripts/build_image_data.sh`** — 호스트에서: ① 실록 색인 복사 ② **카탈로그는 `scripts/snapshot_catalog.py --from var/catalog.all --to image-data/catalog --keep-ended` 로 만든다** — 스냅샷과 같은 규칙(`seoul_openapi` 관찰값만 남기고 `build_entries` 로 다시 묶음, 수집 기록의 키 파라미터 제거). `--keep-ended` 는 끝난 행사도 남겨 로컬과 같은 `excluded` 를 만든다(옵션 없으면 지금 스냅샷 동작). 이어서 `catalog reindex`. ③ 자동 좌표는 `auto_places.json` 에서 `origin` 이 `["seoul_openapi"]` 뿐인 항목만 `image-data/places/auto_places.json` 으로 ④ 크기 합계 출력.
  - `entrypoint.sh`: `KC_PUBLIC_MODE=${KC_PUBLIC_MODE:-1}`, `KC_TARGET_REGION=${KC_TARGET_REGION:-all}`, 쓰기 경로(`KC_HITL_DB`·`KC_AUDIT_DIR`·일정 캐시·var 쓰기 경로 env — dev 가 코드에서 이름을 모아 목록화)를 `/tmp/kc` 아래로, 읽기 데이터는 `/app/var`. 카탈로그 잠금 파일이 데이터 폴더에 생기면 시작 때 `/app/var/catalog` 를 `/tmp/kc/catalog` 로 복사하고 `KC_CATALOG_DIR` 를 그쪽으로. `exec uvicorn backend.app:app --host 0.0.0.0 --port "${PORT:-8080}" --workers 1`.
  - `.dockerignore`: 지금 항목 + `var/`·`docs/`·`frontend/`·`eval/`·`tests/`·`test_condition/`·`domains/kcontext/data/raw/`·`*.db`·`dist/`(단 `!image-data/**`).
- **핵심 로직**: 비밀 0. Tavily·TourAPI 유래 데이터 0.
- **엣지 케이스**: `var/catalog.all` 없음 → 실패(4개 구 이미지로 조용히 가지 않는다). 일정 캐시의 `/tmp` 메모리 사용은 일일 상한이 묶는다(README).
- **지켜야 할 규칙**: 규칙 1 · D27 ④⑤⑥⑦ · D12 ⑦ · D19 · D26 ⑦ · 새 런타임 의존성 없음.
- **DoD**: `test_kc4_container_files.py`(`.dockerignore` 에 `.env`·`var/`·`.git`·`!image-data` 예외, Dockerfile 에 `ENV .*KEY`·`ARG .*KEY` 없음, entrypoint `--workers 1`·`KC_PUBLIC_MODE`, `.gitignore` 에 `image-data/`·`dist/`). **`test_kc4_image_data_filter.py`**: 합성 카탈로그(`seoul_openapi`·`junggu_site`·`gangnam_site`·`tourapi_kto`·제보 관찰값 섞음)를 `--keep-ended` 로 만들면 결과 관찰값·항목 근거가 모두 `seoul_openapi` 뿐, `fetched_from="web"` 0, 수집 기록에 키 파라미터 없음, 끝난 행사 보존. 자동 좌표 필터(`origin`) 테스트. docker 가 있으면 빌드 + 키 없이 `/api/meta` 200 확인·이미지 크기 기록, 없으면 "실행 대기 — docker"(T426 에서 확인).
- **병렬 충돌**: 없음.

#### T424 — Netlify 설정·빌드 스크립트
- **변경 파일**: `netlify.toml`(신규), `scripts/netlify_build.sh`(신규), `tests/test_kc4_netlify_build.py`(신규).
- **모드**: **T403 결론 하나만 구현한다.** 결론이 직접 CORS(프록시 한도 < 100초 또는 미확인)면 프록시 코드를 만들지 않는다. 결론이 프록시면 리라이트만 만들고 CSP 원점 주입을 만들지 않는다.
- **인터페이스**:
  - `netlify.toml`: `[build] command = "bash scripts/netlify_build.sh"`, `publish = "dist"`.
  - `scripts/netlify_build.sh`: ① `frontend/k-context` → `dist/`(`tests/`·`admin.html`·`config.local.js`·`README.md` 제외) ② `dist/config.local.js` 생성: `window.KC_KAKAO_JS_KEY='<KC_KAKAO_JS_KEY 또는 빈 값>'; window.KC_API_BASE='<직접 CORS: KC_BACKEND_ORIGIN + /api | 프록시: /api>';` — `KC_BACKEND_ORIGIN` 은 `^https://[A-Za-z0-9.-]+$`(경로 없음), 카카오 키는 T404 ⑦ 형식(없으면 길이 ≤ 64·영숫자만) 아니면 빌드 실패 ③ 직접 CORS: `dist/events.html` 의 meta CSP `connect-src` 에 `KC_BACKEND_ORIGIN` 추가(원본 불변) / 프록시: `dist/_redirects` 에 `/api/* <KC_BACKEND_ORIGIN>/api/:splat 200!` ④ **`index.html` CSP 는 이번 범위에서 강제하지 않는다** — 넣는다면 `dist/_headers` 에 `Content-Security-Policy-Report-Only` 만(카카오 SDK 출처는 T404 ⑧) ⑤ 값을 로그에 출력하지 않음(길이만).
- **엣지 케이스**: 카카오 키 없음 → 빈 값(SVG, D11). 로컬에서 같은 스크립트로 `dist/` 를 만들어 `python3 -m http.server --directory dist` 로 확인 가능.
- **지켜야 할 규칙**: 규칙 1 · D27 ①② · D11.
- **DoD**: `test_kc4_netlify_build.py` — 임시 폴더에서 가짜 값으로 실행해 `dist/` 구조, `admin.html` 없음, `config.local.js` 내용, (CORS) `events.html` CSP 에 원점 포함 / (프록시) `_redirects`, `index.html` 에 강제 CSP 없음, 잘못된 값이면 종료 ≠ 0, 출력에 값 문자열 없음, 원본 HTML 바이트 불변.
- **병렬 충돌**: 없음.

#### T425 — Cloud Run 배포 스크립트·가이드
- **변경 파일**: `scripts/deploy_cloudrun.sh`(신규), `docs/guides/DEPLOY.md`(신규), `deploy/README.md`.
- **인터페이스**: `bash scripts/deploy_cloudrun.sh --project <id> --region <region> --service <name> [--dry-run] [--yes]` — ① `build_image_data.sh` ② 이미지 빌드·푸시(T402 결론) ③ `gcloud run deploy`: T402 ⑫ 값(시간 한도·메모리·CPU·`--max-instances 1`·`--min-instances 0`·concurrency·비인증 허용), env(`KC_PUBLIC_MODE=1`, `KC_TRUSTED_PROXY_HOPS`, `KC_CORS_ORIGINS`(CORS 모드), `KC_LLM_DAILY_UNITS`(H7), `KC_TARGET_REGION=all`), 시크릿(`NVIDIA_API_KEY` ← Secret Manager). `--dry-run` 은 명령만 출력(비밀 없음).
  - `DEPLOY.md`: 사람 선행 체크리스트(H4 지금 착수·H5·H6·H7·H11), 시크릿 등록(값은 표준입력 — 셸 기록에 안 남게), 순서(Cloud Run → URL → Netlify env `KC_BACKEND_ORIGIN`·`KC_KAKAO_JS_KEY` → Netlify → 카카오 도메인), 비용 안전장치(예산 알림·max-instances 1·일일 소프트 상한·크레딧이 실제 상한), 되돌리기, 이미지 데이터 갱신 절차(`var/catalog.all` 재수집 → `build_image_data.sh` → 재배포).
  - `deploy/README.md`: `cloudrun/`·`netlify.toml` 줄(필수·선택 구분).
- **엣지 케이스**: `gcloud` 없음·미로그인 → 안내 후 종료 2(dry-run 은 동작). 서비스 이름 필수, 기존 서비스는 `--yes` 없이 덮어쓰지 않음. 다른 프로젝트 자원은 건드리지 않음.
- **지켜야 할 규칙**: 규칙 1 · D27 · 유료 인프라 금지.
- **DoD**: `--dry-run` 이 계정 없이 0. `shellcheck` 있으면 경고 0(없으면 기록).
- **병렬 충돌**: 없음.

#### T426 — Cloud Run 배포·공개 URL 남용 점검
- **수행자**: 코디네이터 + 사람(로그인·시크릿).
- **변경 파일**: `docs/status/deploy_2026-10-xx.md`(신규). 코드 변경 없음(발견은 이월).
- **점검 표(실제 URL)**: `/api/meta` public true / `/docs` 404 / 세션 2개로 대화 분리 / `messages` 6번째 429·`Retry-After`·CORS 헤더 / `/api/admin/review`·decision·reports 403 / 데모 문장 응답 시간·앵커·행사 수 / 새 구 문장 1회 / 콜드 스타트 / 최대 메모리(콘솔 지표) / 로그에 키·토큰 문자열 없음 / `X-Forwarded-For` 로 읽힌 IP 가 실제 방문자 IP 와 일치하는지(일치 여부만 기록).
- **엣지 케이스**: 시간 한도에 걸리면 시간 사슬을 기록하고 이월. 지표가 무료 사용량에 가까우면 즉시 사람에게 보고.
- **지켜야 할 규칙**: §6 · D24 · D27.
- **DoD**: 모든 행 결과, 실패 행 원인·조치. LLM 호출 ≤ 10.
- **병렬 충돌**: 단독.

#### T427 — Netlify 배포·카카오 도메인·화면 확인
- **수행자**: 코디네이터 + 사람(H5·H6).
- **변경 파일**: T426 문서에 절 추가.
- **순서**: Netlify env 설정 → 배포 → 카카오 도메인 확인 → 헤드리스로 첫 화면(MOCK 0)·데모 문장·지도·보안 로그(날짜·승인 닫힘)·**행사 화면(`events.html` 이 배포 API 로 검색되는지)** → (프록시면) 일정 요청이 한도 안에 끝나는지 / (CORS 면) 다른 출처 `fetch` 가 막히는지.
- **엣지 케이스**: 프록시가 실측에서 끊기면 T403 결론과 다름 — 직접 CORS 로 T424 를 고치는 작업을 이월이 아니라 즉시 추가 태스크로 사람에게 요청.
- **지켜야 할 규칙**: D27 · D11 · D17.
- **DoD**: 항목별 결과, 공개 URL 2개, H6 확인 기록.
- **병렬 충돌**: 단독.

#### T428 — README·상태·가이드 갱신
- **변경 파일**: `README.md`, `docs/status/2026-10-xx_구현상태.md`(신규), `docs/guides/{SETUP,EVENTS_CATALOG}.md`, `docs/diagram/system-state.html`.
- **핵심 로직**: README 맨 위 공개 URL·공개 데모 제한(일일 소프트 상한·요청 제한·승인 닫힘), 지역 25개 구와 **실록 색인 대상 구 목록**(대상 아님 구 명시), 좌표 출처 두 종류, TourAPI 상태(수치 또는 실행 대기·이용 조건), 외부 서비스 표에 Netlify·Cloud Run·Secret Manager·TourAPI, 보안 설계에 D24·D20 재검토 결론, 한계에 "일정 캐시 공유로 같은 문장 질의 여부가 드러날 수 있음(D24 ⑥)"·"로컬 데모 기본 4개 구, 배포는 25개 구". 숫자는 T418·T422·T426 문서에서만 옮긴다.
- **엣지 케이스**: 실행 대기 항목은 "실행 대기 — H번호".
- **지켜야 할 규칙**: 사실은 측정 문서 인용만.
- **DoD**: 상대 링크가 모두 존재하는 파일. `kc_demo.sh --check` 0.
- **병렬 충돌**: 없음.

#### T429 — 배포 URL 스크린샷
- **변경 파일**: `docs/demo/s4-0{1..5}-*.png`.
- **장면**: ① 첫 화면 ② 데모 문장 결과 ③ 새 구 문장(자동 좌표 문구) ④ 보안 로그(날짜·승인 닫힘) ⑤ 제한 초과 안내.
- **DoD**: 5장, 헤드리스 Chromium. 키·토큰 없음.
- **병렬 충돌**: 없음.

---

## 6. 비용·남용 방지 기준

### 6.1 외부 호출 상한
| 대상 | 런타임(공개 서비스) | 이번 스프린트 개발·수집 | 근거·비고 |
|---|---|---|---|
| NVIDIA 추론 | **하루 300 단위**(`KC_LLM_DAILY_UNITS`, 1 단위 = LLM 호출 1회. 일정 흐름 최대 2, 일반 챗봇 1). 인스턴스 1개라 전역 값이지만 **메모리 기반 소프트 상한 — 재시작하면 0 으로 돌아간다. 실제 비용 상한은 NVIDIA 크레딧(H7)** | T408 ≤ 2 · T418 ≤ 6 · T422 ≤ 4 · T426 ≤ 10 · T427 ≤ 6 · **합계 ≤ 30** | D15 일정 흐름 최대 2회 |
| NVIDIA — 평가 | — | `eval/kc.py validate`·`run --check` 는 **LLM 을 부르지 않는다**(결정적, 매 게이트 실행). LLM 을 부르는 `eval/kc.py stability` 측정은 **이번 계획에 없다** — 일정 이해 동작을 바꾸는 변경이 생겨 사람이 재측정을 요청할 때만, 1회 ≤ 210 호출(Sprint 3 T307 상한) | 회귀 측정과 안정성 측정 구분 |
| 서울 열린데이터광장 | **0회**(키 주입 안 함, D27 ④) | T408 ≤ 60 · T415 행정동 목록 ≤ 5 · T418 ≤ 120(4개 구·25개 구 각 1회 + 재시도 1회) · **하루 1회 수집 실행 원칙** | 1회 1000행. 일일 한도 [확인 필요] |
| TourAPI | **0회** | T401 ≤ 20 · T422 행사 ≤ 200 · 관광지 ≤ 200 · **하루 합계 ≤ 500** | 개발 계정 하루 1,000건(데이터셋 페이지, T401 재확인) |
| Tavily | 0회 | 0회(구청 검색 수집 확대는 이월) | D12 |
| Cloud Run | `max-instances 1`·`min-instances 0` | 배포 횟수 제한 없음(무료 빌드 시간 안) | T402 · 예산 알림(H4) |
| 카카오 지도 JS | 브라우저 호출 | — | T404 |

### 6.2 요청 제한 (공개 모드, `backend/limits.py::RULES`)
| 규칙 키 | 대상 | 키 | 한도 |
|---|---|---|---|
| `session_create` | `POST /api/session` | IP | 10회/시간 |
| `messages` | `POST /api/messages` | IP | 5회/분 · 40회/일 |
| `messages` | 〃 | 세션 | 30회/일 |
| `events` | `/api/events/*` | IP | 20회/분 |
| `reports` | `POST /api/reports` | — | 공개 모드에서 닫힘(403) |
| `admin` | `/api/admin/*` | — | 공개 모드에서 닫힘. 로컬: 토큰 실패 5회 → 15분 차단 |
| `read` | 그 밖의 `GET /api/*` | IP | 60회/분 |
| 동시 처리 | 일정 흐름 / 카탈로그 자식 | 인스턴스 / 세션 | 2건·세션당 1건 / 3개 |
| 본문 | 모든 요청 | — | 256KB(기존), 채팅 2,000자(기존) |

숫자는 근거 있는 추정이 아니라 **보수적 시작값**이다. T426 실측으로 사람이 조정하고, 조정은 `limits.py` 표 한 곳만 바꾼다.

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
| 데모 확인 | 로컬 서버(기본 4개 구)에서 데모 문장 "10/15에 창덕궁 10시, 익선동 2시, 숙소는 종로3가야" → 일정 3개·실록 언급·행사, `?api=mock` 그대로 | 사람 또는 헤드리스 기록 |
| reviewer | 스테이지 diff 검토 | PASS |

### 7.2 스테이지별 추가 확인
| 게이트 | 추가 확인 | 의도된 변화(실패로 보지 않음) |
|---|---|---|
| Stage 1 | 스파이크 `[확인 필요]` 목록, 프로파일 결론(D29 필요 여부), 측정 1차 | 보안 로그 최신 우선·날짜 |
| G1 | D24~D28(+D29) 승인 | — |
| Stage 2 | `--public --smoke` 0, 공개 모드 E2E, 429·413 CORS 헤더 | 로컬에서도 새 탭 = 새 대화 |
| Stage 3 | 검색 결과 동등(`excluded` 포함)·행사 화면 n 동일, 병합 블로킹 동등, T418 문서 | (B안이면) 행사 화면 제외 목록이 요약 |
| Stage 4 | TourAPI·병합·자동 좌표 테스트, T422 보고서 | `COORD_AUTO` 문구, 핀 증가 |
| Stage 5 | 컨테이너·이미지 데이터 필터·빌드 스크립트 테스트, dry-run | — |
| Stage 6 | T426·T427 점검 표 전 항목 | — |
| Stage 7 | 문서 링크 | — |

---

## 8. 이월 흡수 표 (Sprint 3 → Sprint 4)

| 출처(sprint-3) | 항목 | 이번 처리 |
|---|---|---|
| Stage 5 이월 | 행사 검색 1회 약 6초 | **T407**(프로파일) → **T433**(개선) |
| Stage 6 이월 | 보안 로그 날짜 없음·오래된 순 | **T406** |
| Stage 4 이월 | 캐시 키와 해석의 today 불일치 | **T405** |
| Stage 2 이월 W7 | 캐시 키에 `LLM_BACKEND*` 없음 | **T405**(주입 규칙 버전은 유지 이월) |
| Stage 5 이월 | 스냅샷 시점 자료 | **T418** 재생성 |

## 9. 이월 (Sprint 5 후보 · 유지)
| 항목 | 사유 |
|---|---|
| 무료 DB(Postgres)로 승인·감사·캐시 보존 (SCOPE 선택) | DB 드라이버가 새 런타임 의존성 — 결정과 의존성 예외가 먼저 필요. HTTP SQL API 로 `httpx` 만으로 가능한지 스파이크부터 |
| 서울 행사 하루 1회 자동 갱신(Cloud Scheduler + Cloud Run job) (SCOPE 선택) | 영속 저장소(위 항목)와 D7 범위 재결정(호스트 수집기 → job) 필요 |
| 구청·주민센터 검색 수집 25개 구 확대 (SCOPE 선택) | D12 ① 사람 승인 도메인 필요, 실측 수확 낮음(7건, 날짜 없음), Tavily 유래는 재배포 불가 |
| 묶음 events 233KB(항목 필드 다듬기) | 유지 |
| 지역 bbox 도우미 | bbox 가 모두 null — 유지 |
| 프론트 여행 기간 상한 미리 안내 | 유지 |
| Tavily LlmCallError 3건 원인 | 구청 수집 확대 때 |
| 변동 목표 미달(H10 검수 뒤 재판정) | 범위 밖 |
| 새로고침 시 일정·지도 비워짐(D17) | 유지 — 세션은 대화만 복원 |
| 캐시 키 주입 규칙 버전 | 버전 상수 없음 — 별도 결정 |
| Sprint 2·1 이월(T222·T223 추출 보조·T224·S1 항목) | 유지 |
| Sprint 3 사람 작업(좌표 H7·별칭 H8·라벨 H9·평가셋 H10·D14) | 유지 |

## 10. 가장 큰 리스크
1. **Netlify ↔ Cloud Run 연결 방식**: 프록시 한도가 100초보다 짧거나 IP 가 안 넘어오면 직접 CORS 로 가야 하고, 그때 `events.html` CSP·`KC_TRUSTED_PROXY_HOPS` 가 달라진다. T403 이 문서로 못 정하면 T427 실측까지 불확실(T424 는 결론 하나만 구현하므로 뒤집히면 추가 작업).
2. **25개 구 데이터 규모**: 병합(현 구현 3만 건 약 18분)·검색·자식 프로세스 메모리·색인 크기. T416(월 버킷 블로킹)·T433(사전 제외)·T408(1·2차 측정)로 대응하지만, 2차 측정 전에는 Cloud Run 메모리·이미지 한도 안에 드는지 모른다.
3. **재배포 가능한 데이터 범위**: Tavily 유래는 넣을 수 없고, TourAPI 는 공공누리 3유형(변경금지) 포함이라 T401 확정 전까지 이미지에 못 넣는다. 확정이 늦으면 공개 서비스의 명소 좌표·TourAPI 행사가 빠진 채 배포된다(서울 API 데이터만).
- 그 밖: 공개 LLM 비용(소프트 상한 300, 재시작 시 초기화 — 크레딧이 최종 상한), 실록 키워드가 선택이 되어 새 구 대부분이 "실록 색인 대상 아님"일 수 있음, 자동 후보 도구의 입력 데이터(행정동 목록·Unihan) 확보·이용 조건.

## 이월
(스프린트 종료 시 `/done` 이 기록한다)

## 완료 기록
(스테이지마다 `/stage` 가 기록한다)

---

## dev 평가 반영 내역

| # | 지적 | 수준 | 반영 |
|---|---|---|---|
| 1 | `events.html` 이 `config.local.js` 를 로드하지 않음(`index.html:13` 에만) | 차단 | T410 범위에 `events.html`·`admin.html` 의 script 추가, `connect-src` 정리(원본은 로컬용 유지, 배포 원점은 T424 가 `dist/` 에만) + 파싱 테스트 |
| 2 | CORS 미들웨어 순서 — `app.py:35` 뒤에 붙은 http 미들웨어가 바깥이라 429·413 에 CORS 헤더 없음 | 차단 | T409 에서 http 미들웨어(`_limit_body`·`_rate_limit`)를 먼저, CORS 를 **마지막에** 추가. 429·413 응답 `Access-Control-Allow-Origin` 테스트(`test_kc4_app_middleware.py`), §5.1 계약·D24 ⑤ 에 명시 |
| 3 | T416 블로킹 동등성 주장 오류(400일 상한·nodays 버킷) | 차단 | 상한 없는 **월 버킷** + 외부 id 키, 후보를 그룹 생성 순으로 순회하는 설계와 동등성 근거를 명세에 적음. 300개 테스트에 긴×짧은 기간·달 경계·날짜 없음 등 8종 포함. 계측값(2,000건 4.9초, 쌍당 약 2.5µs, 8.7k 약 95초, 3만 약 18분)을 근거로 §0.3·T416 에 기록 |
| 4 | 라이선스·재배포 — `var/catalog` 통째로 넣으면 Tavily 유래 공개, TourAPI 3유형 | 차단 | 이미지 카탈로그는 `snapshot_catalog.py --keep-ended`(서울 API 유래만, D19 규칙) + 필터 테스트(`test_kc4_image_data_filter.py`). 자동 좌표도 `origin` 필터. T401 에 공공누리 유형별 허용 범위 절 추가, D26 ⑦·D27 ④ 에 "확정 전 TourAPI 이미지 포함 금지" 명시, T420 TourAPI 입력 기본 꺼짐, T422 는 시험 파일만 |
| 5 | `test_kc_regions.py:31` 이 지역 4개 단언 | 차단 | T414 범위에 명시. 기대값 유지, `tests/fixtures/regions4/` 로 전환 |
| 6 | T407 이 `excluded` 계약을 바꿈(행사 화면이 사용) | 차단 | T407 은 Stage 1 프로파일만(동작 변경 없음). 개선은 T433(Stage 3)로 옮기고 기본 A안은 `excluded` 를 순서까지 보존. 계약을 바꾸는 B안은 조건부 결정 D29 승인 뒤에만. DoD 에 `excluded` 비교·행사 화면 n 확인 |
| 7 | `session_from_request` 위치 — 2b 숨은 의존 | 권장 | T409 의 `session.py` 로 옮김, T411·T412 는 이것만 사용 |
| 8 | `run_catalog` 전역 동시성 상한 | 권장 | T409: `CatalogBusy`·`configure_concurrency`(`KC_CATALOG_CONCURRENCY` 기본 3), T412 `_call` 에서 429, T411 은 행사 검색 실패 경로 |
| 9 | 공개 모드 `docs_url`·`openapi_url` | 권장 | T409·D24 ⑤·T413·T426 점검 |
| 10 | D24 문안 보강 | 권장 | ③ 소프트 상한·재시작 초기화·크레딧이 실제 상한, ① 로컬 `local` 공용 세션, ⑥ 일정 캐시 공유로 같은 문장 질의 여부 노출(영향 작음) |
| 11 | T417 사람 `seoul_bbox` → 데이터 기반 | 권장 | 같은 구 좌표 중앙값에서 `max_gu_dist_km` 넘으면 제외(D25 ③), 사람 값 없음. Stage 4 로 내려 T420 과 묶음. H 표에서 bbox 삭제 |
| 12 | H3 필수 → 선택, 자동 후보 도구 | 권장 | H3 선택(기본 빈 키워드, D28 ③). T415 에 `candidates`(실록 지명 태그 독음 ↔ 구별 동 이름) 추가, 사람은 고르기만 |
| 13 | `kc_demo.sh` 기본 4개 구, 배포는 25개 구 | 권장 | T416 `KC_DEMO_REGIONS`(기본 4개 구), T418 은 `var/catalog.all` 따로, D27 ④⑤ 에 명시 |
| 14 | T424 모드·`index.html` CSP | 권장 | T403 결론 하나만 구현(직접 CORS 면 프록시 코드 없음). `index.html` CSP 는 강제하지 않음(넣으면 Report-Only) |
| 15 | 프로파일 → T408 RSS → 재측정 순서 | 권장 | 최종 표·"측정 순서" 줄: T407 → T408(1차, RSS·동시 2건) → T433 → T418 안 2차 |
| 16 | §6.1 "회귀 측정 ≤ 210" 의미 | 권장 | `validate`·`run --check` 는 LLM 없음, `stability` 는 이번 계획에 없고 요청 시에만 ≤ 210 으로 구분 |
| 17 | T430~T432 | 권장 | 본문에서 빼고 §9 이월(Sprint 5 후보)로만 |
| 18 | H4·H2 상태 | 권장 | H4 "지금 착수 가능"(결제 계정 카드 등록 시간), H2 "신청 중" |
| 19 | 초안 T423 표에 `.gitignore` 누락 | 정리 | T423 범위에 `.gitignore`(`image-data/`·`dist/`) 명시, T424 는 고치지 않음 |
