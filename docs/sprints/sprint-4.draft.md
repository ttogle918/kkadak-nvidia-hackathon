# Sprint 4 — 서울 25개 구 확장 + 공개 배포 (초안)

> 상태: **초안**(pm, 2026-10-10). dev 현실성 평가와 사람 승인(결정 D24~D28) 뒤 `sprint-4.md` 로 확정한다.
> 범위 근거: `docs/SCOPE.md` "Sprint 4 범위". "반드시"는 우선순위대로 ① 공개 배포 전 안전장치 ② 서울 25개 구 확장 ③ TourAPI 연결 ④ 배포(Netlify + Cloud Run + Secret Manager) ⑤ 문서다.
> "선택"(무료 DB, 자동 갱신, 구청 검색 수집 확대)은 조건부 태스크(T430~T432)로만 둔다. "지금 안 함"(NemoClaw/OpenClaw·MCP 에이전트화, 서울 밖, 유료 인프라)은 어떤 태스크에도 넣지 않았다.
> 시간 상자는 없고 소요 시간도 추정하지 않는다. **키·계정이 없어도 되는 코드 작업을 앞에 두고, 실호출·실배포는 뒤에 둔다.** 모든 스테이지 게이트에 "로컬 데모 동작 유지" 칸을 둔다(§7).
> 태스크 ID: `T4{순번 2자리}`. 새 테스트 파일 접두사: `test_kc4_*`(파이썬), `*.kc4.test.js`(프론트).

## Sprint 4 실행 계획 요약

| 스테이지 | 태스크 | 병렬 | 결과물 |
|---|---|---|---|
| Stage 1 — 스파이크·이월·측정 (키·계정·결정 없이) | T401 TourAPI 문서 · T402 Cloud Run 문서 · T403 Netlify 문서 · T404 카카오 도메인 문서 · T405 캐시 키 today 일관성 · T406 보안 로그 날짜·최신 우선 · T407 행사 검색 사전 제외 색인 · T408 서울 API·실행 자원 측정 | 8개 모두 병렬(파일 겹침 없음) | `docs/spikes/{tourapi,cloud_run,netlify,kakao_domain}.md`, 검색 1회 6초 → 목표 1.5초 이하, `docs/status/measure_2026-10-xx.md` |
| **게이트 G1** | 사람: D24~D28 승인(스파이크 결과 반영 문안) | — | `docs/DECISIONS.md` D24~D28 |
| Stage 2 — 공개 안전장치 (D24) | 2a: T409 세션·제한·설정 기반 ∥ T410 프론트 세션·오류·배포 주소 → 2b: T411 채팅 세션 분리·동시 처리·일일 상한 ∥ T412 공개 모드 보안 로그·승인·관리자·제보 → 2c: T413 공개 모드 통합 테스트·`kc_demo --public` | 2a 2개 → 2b 2개 → 2c 1개 | 방문자별 대화, 동시 2건, IP·세션별 제한, LLM 일일 상한, 관리자·승인 닫힘 |
| Stage 3 — 서울 25개 구 (D25·D28) | 3a: T414 지역 파일 21개 ∥ T415 실록 키워드 측정 도구 ∥ T416 카탈로그 25개 구(전체 별칭·쪽 상한·병합 블로킹) ∥ T417 좌표 자동 부착(서울 API 장소) → 3b: **T418 실행**(서울 25개 구 수집·색인 재구축·자동 좌표·스냅샷·측정) | 3a 4개 병렬 → 3b 단독 | 25개 구 지역 설정, 서울 전체 키워드 색인, 25개 구 행사, 자동 좌표 사전 |
| Stage 4 — TourAPI (D26) | 4a: T419 TourAPI 수집기 ∥ T421 병합 규칙(D26) → 4b: T420 TourAPI 관광지 → 좌표 사전 → 4c: **T422 실수집**(키 필요) | 4a 2개 → 4b → 4c | `catalog/tourapi.py`, `kto:` 병합, 관광지 좌표, 수집 보고서 |
| Stage 5 — 배포 패키징 (D27, 계정 없이) | T423 Dockerfile·컨테이너 설정 ∥ T424 Netlify 설정·빌드 스크립트 ∥ T425 Cloud Run 배포 스크립트·가이드 | 3개 병렬 | `Dockerfile`, `netlify.toml`, `scripts/{netlify_build,deploy_cloudrun}.sh`, `docs/guides/DEPLOY.md` |
| Stage 6 — 실제 배포 (계정 필요) | T426 Cloud Run 배포·남용 점검 → T427 Netlify 배포·카카오 도메인·화면 확인 | 순차 | 공개 URL 2개, `docs/status/deploy_2026-10-xx.md` |
| Stage 7 — 문서 | T428 README·상태·가이드 ∥ T429 배포 URL 스크린샷 | 2개 병렬 | 배포 URL 기준 문서, `docs/demo/s4-*.png` |
| 조건부 | T430 무료 DB 보존 · T431 일일 자동 갱신 · T432 구청 검색 수집 25개 구 | 조건 충족 시 | §5 |

- **필수 경로**: T401~T408 → G1(D24~D28) → T409·T410 → T411·T412 → T413 → T414~T417 → (H3) T418 → T419·T421 → T420 → (H2) T422 → T423~T425 → (H4·H5·H11) T426 → (H6) T427 → T428·T429.
- **키·계정이 필요한 일**: T408(서울 키 — 이미 있음), T418(서울 키 — 있음, 실록 키워드 H3), T422(TourAPI 키 H2), T426(GCP H4·H11), T427(Netlify H5·카카오 H6). 모두 해당 스테이지 끝에 있다.
- **얇은 수직 경로는 이미 있다**: 일정 문장 → 게이트 → 별도 프로세스 파이프라인 → 행사 검색 → 묶음 v2 → 화면, 보안 로그·사람 승인 API(Sprint 3). 이번 Stage 2 는 이 경로를 "여러 방문자가 동시에 써도 안전한" 형태로 바꾸는 것이고, 배포(Stage 5·6)는 같은 경로를 컨테이너에 그대로 싣는다.
- **TourAPI 키가 늦어져도** Stage 4 의 코드(T419~T421)는 문서 스파이크(T401)만으로 끝내고, T422 만 "실행 대기 — H2"로 남긴 채 Stage 5 로 넘어간다. 배포는 TourAPI 없이도 가능하다(서울 API 데이터로).

---

## 0. 기준선 · 공통 규칙

### 0.1 착수 직전 dev 가 실측해 적는다
- `uv run python -m pytest -q` 건수: ____ (Sprint 3 마감 1,937 — 실측값을 쓴다)
- `uv run ruff check .`: 통과 여부
- `(cd frontend/k-context && node --test)` 건수: ____ (Sprint 3 마감 360)
- `uv run python eval/kc.py validate` · `uv run python eval/kc.py run --check --known-failures eval/BASELINE.md`: 0 여부
- `bash scripts/kc_demo.sh --check` · `--smoke`: 0 여부
- `du -sh var/index/kcontext.db var/catalog domains/kcontext/data/snapshots/catalog` (코디네이터 확인값: 43M · 46M · 836K)
- 행사 검색 1회 시간(T408 이 정식으로 잰다. 코디네이터 확인값: 약 6초)

### 0.2 공통 규칙 (Sprint 3 §0.2 를 이어받음)
- 파이썬 3.11+, 줄 길이 100, ruff 통과. 공개 함수에 타입 힌트, 새 패키지 `__init__.py` 는 `__all__` 명시.
- **PostToolUse 훅이 `ruff --fix` 로 미사용 import 를 지운다. import 와 그 사용은 한 번의 편집에 같이 쓴다.**
- **새 런타임 의존성 금지.** 있는 것만: `fastapi`·`httpx`·`mcp`·`openai`·`python-dotenv`·`uvicorn` + 표준 라이브러리. 프론트는 의존성 없음. GCP·Netlify 는 **CLI(`gcloud`·`netlify`)를 셸 스크립트에서** 부르고 파이썬 SDK 를 쓰지 않는다. Secret Manager 는 Cloud Run 의 env 주입으로만 쓴다(코드가 Secret Manager API 를 부르지 않는다).
- 테스트 파일 이름은 레포 전체에서 고유하게(`test_kc4_*`). `tests/test_layout.py`·`test_smoke.py`·`test_boundaries.py` 는 수정하지 않는다.
- 도메인 코드는 `domains/kcontext/` 에만. `core/` 에 도메인 용어 금지(D3).
- **backend 는 `domains`·`mcp_server` 를 import 하지 않는다**(D3·D10). 별도 프로세스와 JSON 으로만 받는다.
- **지역은 코드에 박지 않는다**(`data/regions/*.json` 에서만. 테스트 fixture 예외).
- **사실을 지어내지 않는다.** 테스트·fixture 의 행사·좌표·한자 지명은 `○○`·`예시`·`합성` 값만. **실록 키워드(한자 지명)와 구 경계 매핑은 사람이 출처와 함께 준 값(H3)만** — dev 가 기억으로 채우지 않는다. **좌표는 사람 사전(`demo_places.json`) 또는 D25 가 허용한 공공 API 값만.** TourAPI 의 오퍼레이션·파라미터·응답 필드 이름은 **T401 이 출처 URL 로 확인한 것만** 코드에 쓴다.
- 키는 env **변수 이름**으로만(규칙 1, D1, D5). 키 값·Authorization 헤더·서비스키가 들어간 URL·LLM 원문 응답 전체를 코드·로그·결과 파일·커밋에 남기지 않는다. TourAPI 서비스키는 쿼리 문자열로 들어갈 수 있으므로 **오류 메시지에 요청 URL 을 싣지 않는다**(서울 API 와 같은 방식).
- `deploy/openshell/policy*.yaml`·`.env`·`eval/testset.json`·`CLAUDE.md`·`docs/DECISIONS.md` 는 dev·pm 이 고치지 않는다.
- 프론트 태스크는 **표에 적힌 파일만** 고친다.
- `?api=mock` 데모 모드는 지우지 않는다.
- **공개 모드는 env `KC_PUBLIC_MODE=1` 일 때만 켜진다.** 꺼져 있으면(로컬 기본) 지금 동작과 같아야 한다 — 기존 테스트·`eval/kc_eval/stability.py`(세션 헤더 없이 `/api/messages` 호출)·`kc_demo.sh` 가 그대로 통과해야 한다.
- 실호출(NVIDIA·서울 API·TourAPI)은 §6 상한 안에서만. 상한은 코드 인자로도 둔다.

### 0.3 코드로 확인한 현황 (2026-10-10, pm 대조)
| 영역 | 코드 위치 | 확인한 사실 | 관계 태스크 |
|---|---|---|---|
| 대화 기록 | `backend/chat.py` `ChatService._history`(deque 200), `_seq` | 프로세스에 하나 — 모든 방문자 공용. `GET /api/messages` 가 전부 돌려줌 | T411 |
| 동시 처리 | `chat.py` `_story_lock`(비차단 Lock) → `ChatBusy` → 429 `busy` | 일정 흐름 1건만. 일반 챗봇은 `client.busy("chat")` 로 provider 세마포어 판단 | T411 |
| 요청별 로그 | `chat.py` `_TeeSink.mark()/since()` | 누적 개수 기준 — **동시 요청이 생기면 다른 요청의 audit 이벤트가 섞인다** | T411(ContextVar 수집) |
| 행사 검색 한도 | `chat.py` `self._search_timeout_s` | 인스턴스 필드에 쓰고 읽음 — 동시 흐름이면 경쟁 | T411(인자로) |
| CORS | `backend/settings.py` 기본 localhost:8766 만, `KC_CORS_ORIGINS` 로 변경 | `allow_headers=["Content-Type","X-Admin-Token"]` | T409 |
| 보안 로그 | `routers/review.py` `GET /api/audit` | `audit_dir/*.jsonl` 전부 읽음 — 다른 방문자의 차단 기록(경로 문자열 포함)도 보임. `POST /api/audit/{id}/decision` 은 **인증 없음**("공개 배포 전에는 인증 계층이 필요" 주석) | T412 |
| 관리자 | `routers/events.py` `require_admin` | `X-Admin-Token` hmac 비교, 미설정이면 닫힘. 실패 횟수 제한 없음 | T409·T412 |
| 제보 | `POST /api/reports` | 인증 없이 `reports.json` 에 씀 | T412 |
| 행사 검색 | `catalog/api.py` `_search` → `store.load_entries()` 전체 → `query.search_events` | 8,719건을 매번 읽고 `excluded` 에 8,600건을 담아 돌려줌 → 약 6초 | T407 |
| 병합 | `catalog/merge.py` `_group` | 새 관찰값마다 기존 모든 그룹과 비교(이중 반복). 25개 구로 늘면 느려질 수 있음 | T416 |
| 서울 API | `catalog/seoul.py` `fetch_rows(max_pages=30)` | 1000행 × 최대 30쪽. 전체 행 수가 3만을 넘으면 조용히 잘린다 | T408·T416 |
| 대상 지역 | `catalog/target.py` | `KC_TARGET_REGION` 쉼표 목록, 여럿이면 `"+"` 로 합친 Region(bbox None) | T416 |
| 지역 파일 | `data/regions/{jung,jongno,mapo,gangnam}.json` | `sillok_keywords` 가 하나라도 있으면 **모든 지역이 sillok_keywords 로만** 매칭(`ingest/sillok.py::_region_field`) — 빈 목록 지역은 색인에 아무것도 안 들어감 | T414·T418 |
| 실록 XML | `ingest/sillok.py` | 기사마다 `<index type="지명">` 태그(`places`)가 있음 — 후보 측정에 쓸 수 있음 | T415 |
| 장소 사전 | `domains/kcontext/places.py` `default_path()` = `demo_places.json` 하나(5곳) | 파일 하나만 읽음. 모든 필드 필수 | T417 |
| 게이트 장소 | `backend/fixtures/chat_places.json`(사본) | 자동 좌표는 게이트에 넣지 않는다(오탐 증가 방지) | T417 |
| 캐시 키 | `schedule/cache.py::key_for(today=)`, `pipeline/__main__.py` | `__main__` 이 today 를 넘기지 않음 → 키와 해석이 각자 `kst_today()` | T405 |
| 보안 로그 표시 | `frontend/.../api/http.js::sanitizeAuditEntry` | 서버의 `at`(ISO) 을 버리고 `time`(HH:MM:SS)만 남김. 서버는 오래된 순 정렬 | T406 |
| 프론트 주소 | `src/api/index.js` `DEFAULT_CHAT_BASE='http://localhost:8000/api'`, `events/api.js::safeBase`(같은 출처 경로·루프백 8000 만) | 배포 주소를 줄 수단이 없음 | T410 |
| CSP | `events.html`·`admin.html` meta CSP `connect-src 'self' http://localhost:* …`, `index.html` 은 CSP 없음 | 다른 출처 API 로 직접 부르면 행사 화면이 막힘 | T424(D27) |
| 컨테이너 | `Dockerfile` 없음, `.dockerignore` 있음(.env·.git·.claude 제외) | `var/` 는 제외하지 않음 | T423 |
| TourAPI | `catalog_sources.json` `tourapi_kto`(`configurable_unverified`), `catalog_runner._SOURCE_KEYS` 에 `DATA_GO_KR_SERVICE_KEY` | 호출 코드 없음 | T401·T419 |

---

## 1. 의존성 그래프

```
Stage 1 (모두 병렬, 키·결정 불필요 — T408 만 이미 있는 서울 키 사용)
  T401 TourAPI 문서 ─┐
  T402 Cloud Run 문서 ┼──► G1: D24~D28 승인 (스파이크 값 반영)
  T403 Netlify 문서 ──┤
  T404 카카오 문서 ───┤
  T408 측정 ──────────┘
  T405 캐시 today · T406 보안 로그 날짜 · T407 검색 사전 제외 (이월 흡수, 결정 불필요)
                │
Stage 2 (D24)   ▼
  2a: T409 backend 세션·제한 기반(session.py·limits.py·settings·app·meta)  ∥  T410 프론트 세션·오류·주소
  2b: T411 chat.py·messages.py (T409 인터페이스 사용)  ∥  T412 review.py·events.py (T409 인터페이스 사용)
  2c: T413 공개 모드 통합 테스트 + kc_demo --public
                │
Stage 3 (D25·D28)
  3a: T414 지역 21개 ∥ T415 키워드 측정 도구 ∥ T416 카탈로그 25개 구 ∥ T417 자동 좌표(서울 API 장소)
  3b: T418 실행 ◄── H3(실록 키워드) — 없으면 색인은 기존 4개 구 키워드 그대로, 나머지는 진행
                │
Stage 4 (D26)
  4a: T419 TourAPI 수집기 (T401) ∥ T421 병합 D26 (T416 뒤 merge.py)
  4b: T420 관광지 → 좌표 사전 (T417·T419)
  4c: T422 실수집 ◄── H2(TourAPI 키)
                │
Stage 5 (D27, 계정 불필요)
  T423 Dockerfile ∥ T424 Netlify 설정 ∥ T425 배포 스크립트·가이드
                │
Stage 6 ◄── H4(GCP)·H11(시크릿 등록)·H5(Netlify)·H6(카카오)
  T426 Cloud Run 배포·남용 점검 → T427 Netlify 배포·도메인·화면
                │
Stage 7: T428 문서 ∥ T429 스크린샷
```

---

## 2. 결정 후보 (먼저 결정을 추가해야 함)

pm·dev 는 `docs/DECISIONS.md` 를 고치지 않는다. 사람이 승인하면 D24 부터 추가한다. **G1 에서 한꺼번에 승인받되**, 스파이크(T401~T404)·측정(T408) 결과로 `[확인 필요]` 값을 채운 문안을 올린다.

| 후보 | 요지 | 착수 조건이 되는 스테이지 | 승인 전 진행 |
|---|---|---|---|
| D24 | 공개 배포 보안 모델 + D20 재검토 결론 | Stage 2 | Stage 2 착수하지 않음 |
| D25 | 좌표 자동 부착은 공공 API 좌표만(외부 장소 검색은 쓰지 않음) | T417·T420 | T417·T420 착수하지 않음(T414~T416 은 진행) |
| D26 | TourAPI × 서울 API 병합 규칙(D13 보충) | T419·T421 | 둘 다 착수하지 않음 |
| D27 | 배포 구성(Netlify + Cloud Run 1 인스턴스 + Secret Manager, 상태는 휘발) | Stage 5 | Stage 5 착수하지 않음 |
| D28 | 실록 색인 서울 확장(키워드 출처·크기 상한, 전체 색인 안 함) | T418 의 색인 부분 | 색인은 4개 구 그대로 |

### D24~D28 문안 (승인용)

```markdown
## D24 — 공개 배포는 서버 발급 세션 토큰·요청 제한·일일 상한으로 지키고, 공개 모드에서는 관리자·승인·제보 쓰기를 닫는다. OpenShell 은 계속 선택이다 (2026-10-xx)
- **결정**:
  ① **세션**: `POST /api/session` 이 임의 토큰(`secrets.token_urlsafe(32)`, 43자)을 발급하고, 브라우저는 탭 단위 `sessionStorage` 에 두어 `X-KC-Session` 헤더로 보낸다(쿠키를 쓰지 않는다 — 다른 출처 API 에서 서드파티 쿠키가 막히는 문제와 CSRF 를 함께 피한다). 서버는 세션별 대화 기록(최대 100개)·보안 로그 항목(최대 200개)을 **프로세스 메모리에만** 두고, 마지막 사용 후 2시간이 지나면 지운다(세션 수 상한 1,000, 넘으면 가장 오래 안 쓴 세션부터). 디스크·DB 에 쓰지 않는다. **채팅 묶음은 지금처럼 서버에 보관하지 않는다(D17 유지)** — 세션이 들고 있는 것은 화면 대화 문장뿐이다.
  ② **동시 처리**: 일정 흐름은 인스턴스당 동시 2건(`KC_STORY_CONCURRENCY`), 세션당 동시 1건. 넘으면 기다리지 않고 429 `busy`.
  ③ **요청 제한**(IP·세션별, 고정 창): §6.2 표의 숫자. 넘으면 429 `rate_limited` + `Retry-After`. **LLM 일일 상한**: 하루(KST) LLM 호출 단위 `KC_LLM_DAILY_UNITS`(기본 300)를 넘으면 503 `daily_limit` 고정 문구. 일정 흐름은 2단위를 예약하고 실제 시도 수(`schedule.attempts`, 캐시면 0)만큼 남기고 돌려받는다. 일반 챗봇은 1단위.
  ④ **IP**: Cloud Run 앞단이 붙이는 `X-Forwarded-For` 를 오른쪽에서 `KC_TRUSTED_PROXY_HOPS` 번째 값으로 읽는다(값은 T402·T403 실측으로 정함). 읽지 못하면 연결 주소.
  ⑤ **공개 모드**(`KC_PUBLIC_MODE=1`): `/api/admin/*`·`POST /api/audit/{id}/decision`·`POST /api/reports` 는 403 `disabled_in_public` 이다. `GET /api/audit` 은 **그 세션의 항목만** 돌려준다(다른 방문자의 차단 기록·경로 문자열을 보이지 않는다). 관리자 화면(`admin.html`)은 공개 배포물에 넣지 않는다. 로컬 모드(기본)는 지금 동작 그대로다.
  ⑥ **D20 재검토 결론**: 공개 서비스로 띄워도 OpenShell 은 필수로 돌리지 않는다. 근거 — LLM 에 도구(파일·네트워크)가 없고 출력이 실행되지 않으며, 에이전트 역할 프로세스에는 허용 목록 env 만 가고(D7 ③), 외부 자료는 호스트 수집기만 받는다(D7). 공개로 새로 생기는 위협(방문자 간 대화 노출·비용 남용·관리자 API·승인 위조)은 샌드박스가 아니라 위 ①~⑤ 로 막는다. 컨테이너는 Cloud Run 의 격리 위에서 돈다. **LLM 에 도구를 주거나 NemoClaw 로 옮기면 D20 대로 다시 본다.**
- **계기**: SCOPE Sprint 4 ① 과 D20 "다시 볼 때 — 공개 서비스로 띄울 때". 코드 확인: 대화 기록 공용, 일정 흐름 1건, 승인 API 무인증, 보안 로그 전체 노출, 동시 요청 시 로그 섞임.
- **대안**: (a) 쿠키 세션 — Netlify 와 Cloud Run 이 다른 출처면 서드파티 쿠키 차단·SameSite 처리가 필요해 기각(프록시 방식이 확정되면 다시 볼 수 있음). (b) 대화 기록을 브라우저가 들고 매 요청에 실어 보냄 — 위조한 assistant 턴이 LLM 맥락에 들어가 주입 경로가 되어 기각. (c) 클라이언트가 토큰을 만듦 — 서버가 발급 수를 IP 별로 제한할 수 없어 기각. (d) 승인 API 를 관리자 토큰으로 열어 둠 — 공개 데모에서 승인할 초안(product 흐름은 초안을 만들지 않음)이 없고 토큰 무차별 대입 표면만 생겨 기각(필요하면 `KC_PUBLIC_ADMIN=1` 로 다시 연다 — 이번 범위 밖). (e) OpenShell 필수화 — 위협 모델과 맞지 않고 Cloud Run 에서 돌릴 수 없어 기각.

## D25 — 장소 좌표 자동 부착은 공공 API 가 준 좌표만 쓰고, 사람 사전이 우선하며, 화면에 "공공 데이터 좌표"로 밝힌다 (2026-10-xx)
- **결정**: ① 자동 좌표의 출처는 **서울 열린데이터광장 문화행사의 장소명(PLACE)·위경도(LAT·LOT)** 와 **TourAPI 관광지의 이름·좌표**(필드 이름은 T401 확인값) 둘뿐이다. ② 같은 이름(정규화 후)의 좌표들이 중앙값에서 모두 150m 안이면 중앙값을 쓰고, 하나라도 벗어나면 그 이름은 버린다(모호). 좌표가 `data/places/auto_rules.json` 의 서울 범위(사람이 출처와 함께 적은 값) 밖이면 버린다. ③ 사람 사전(`demo_places.json`)에 같은 이름·별칭이 있으면 사람 값이 이긴다. ④ 자동 사전 항목은 `source`(출처 이름·행 수)와 `verified_at`(수집일)을 갖고 `var/places/auto_places.json` 에 생성한다(공공누리 1유형 유래라도 저장소에는 커밋하지 않는다 — 생성 결과는 재현 가능). ⑤ 앵커가 자동 좌표를 쓰면 문제 코드 `COORD_AUTO`("이름: 공공 데이터 좌표(사람 확인 전)")를 남기고 화면은 고정 문구로 보인다. ⑥ 자동 좌표는 지도 핀·이동 구간 거리 표시에 쓴다. 판정 규칙(D16·D13 ⑥)은 그대로다. ⑦ 자동 사전 이름은 일정 게이트(`backend/fixtures/chat_places.json`)에 넣지 않는다.
- **계기**: 좌표가 있는 장소가 5곳뿐이라 25개 구 확장의 가장 큰 병목. Sprint 3 규칙은 "좌표는 사람이 출처를 확인한 값만"이었다 — 이 결정은 공공 API 값에 한해 그 규칙을 넓힌다.
- **대안**: (a) 카카오 로컬 등 외부 장소 검색 — 새 키·외부 호출·결과 저장 약관 확인이 필요하고 런타임 호출이면 D7 과 충돌해 이번에는 기각(H8 로 후보 유지). (b) 좌표 하나라도 있으면 채택 — 같은 이름의 다른 장소(체인점 등)가 섞여 기각. (c) 사람이 전부 확인 — 25개 구 규모에서 병목이 그대로라 기각.

## D26 — TourAPI 행사는 D13 묶기 규칙 그대로 서울 API 와 합치고, 관광지는 카탈로그가 아니라 좌표 사전 입력으로만 쓴다 (2026-10-xx)
- **결정**: ① TourAPI 콘텐츠 id 는 외부 id 체계 `kto:`(값은 T401 이 확인한 콘텐츠 id 필드)로 둔다. 서울 API 는 지금처럼 `seoul_cult:` 다. ② 두 체계가 다르므로 묶기는 D13 ③ 의 장소+기간+행사명 유사도 규칙만 쓴다(주최 같으면 0.5, 아니면 0.8). 같은 체계 다른 값은 다른 행사(D13 ③ 그대로). ③ 두 출처 모두 `official_api` 등급이고, **원천 관계가 확인되기 전에는 독립 출처로 세지 않는다**(D13 ③ "재배포 자료"를 보수적으로 적용). ④ 같은 필드 값이 다르면 D13 ④ 대로 더 최근 수정 → 해결 안 되면 `conflict`(값 비우고 "확인 필요"). 출처 간 우선순위를 새로 만들지 않는다. ⑤ TourAPI 관광지(행사가 아닌 콘텐츠)는 `EventEntry` 로 만들지 않고 D25 좌표 사전 입력으로만 쓴다. ⑥ 대상 지역은 D13 ② 대로 개최 장소로 정한다 — TourAPI 의 지역 코드(이름은 T401 확인값)는 "출처가 준 자치구"로 쓰되, 코드→구 이름 대응표는 T401 이 공식 코드 조회 결과로 만든 것만 쓴다.
- **계기**: SCOPE Sprint 4 ③ "서울 API 와 중복을 합친다". D13 은 출처 간 묶기를 이미 정했지만 TourAPI 고유의 id 체계·관광지 처리·독립 출처 여부는 정하지 않았다.
- **대안**: TourAPI 우선(또는 서울 API 우선) 고정 — 근거 없이 한쪽 값을 사실로 올리게 되어 기각. 관광지도 카탈로그 항목으로 — 행사 검색 결과에 상설 관광지가 행사처럼 섞여 기각.

## D27 — 배포는 Netlify(정적) + Cloud Run(backend·파이프라인, 인스턴스 1개) + Secret Manager 로 하고, 상태는 기본 휘발이며, 수집은 호스트에서 한 뒤 결과를 이미지에 싣는다 (2026-10-xx)
- **결정**: ① 화면은 Netlify 정적 배포(`frontend/k-context` 를 빌드 단계에서 `dist/` 로 복사하고 `config.local.js` 를 Netlify 환경변수로 생성 — 키는 저장소에 없다). `admin.html` 은 싣지 않는다. ② API 연결은 **T403 결과로 고른다**: Netlify 프록시(`/api/*` → Cloud Run, 같은 출처)의 요청 시간 한도가 100초 이상이고 방문자 IP 가 전달되면 프록시, 아니면 **직접 CORS**(`KC_CORS_ORIGINS`=Netlify 도메인, 빌드가 `dist/` 의 CSP `connect-src` 에 Cloud Run 주소를 넣음). [확인 필요: T403] ③ Cloud Run 은 컨테이너 하나(uvicorn 1 프로세스 + 요청마다 파이프라인·카탈로그 자식 프로세스), `max-instances=1`·`min-instances=0`, 요청 한도 ≥ 120초, 메모리는 T408 실측 × 1.5 를 무료 사용량 안에서. [확인 필요: T402] ④ 이미지에는 실록 색인·카탈로그(검색 색인 포함)·자동 좌표 사전을 **빌드 전에 호스트에서 만들어** 넣는다. 런타임에는 서울 API·TourAPI·Tavily 를 부르지 않는다(키를 주입하지 않는다, D7). ⑤ 비밀은 Secret Manager → Cloud Run env(`NVIDIA_API_KEY` 하나. 관리자 토큰은 공개 모드에서 쓰지 않으므로 넣지 않는다). 이미지·빌드 컨텍스트에는 비밀이 없다(규칙 1, `.dockerignore`). ⑥ hitl·audit·일정 캐시·세션·제보는 인스턴스 안(`/tmp`)에만 두고 재시작하면 비워진다(데모). 보존은 선택 T430(별도 결정). ⑦ 무료 사용량 밖으로 나가는 설정(최소 인스턴스 ≥1, 유료 리전 등)은 쓰지 않고, 사람이 결제 계정에 예산 알림을 건다(H4).
- **계기**: SCOPE Sprint 4 ④. 인스턴스가 하나여야 메모리 세션·제한·일일 상한이 정확하다(D24).
- **대안**: (a) 백엔드도 정적 호스팅 함수(Netlify Functions) — 파이프라인이 별도 프로세스·SQLite 색인·최대 90초라 맞지 않아 기각. (b) 색인을 GCS 에 두고 시작할 때 내려받기 — 이미지가 한도를 넘을 때의 예비안으로 남김(T402·T408 결과). (c) 런타임 수집 — D7 과 충돌, 키 주입이 늘어 기각. (d) 인스턴스 여러 개 — 메모리 상태가 갈려 제한이 무력해져 기각.

## D28 — 실록 색인은 25개 구 키워드(사람이 출처와 함께 준 값)로만 다시 만들고, 전체 색인은 하지 않는다 (2026-10-xx)
- **결정**: ① `--mode regions` 그대로, 25개 구 `sillok_keywords` 의 합집합으로 다시 만든다. ② 새 구의 `sillok_keywords` 는 **사람이 출처(서울지명사전 등 문헌·URL)와 함께 준 한자 지명**만 넣고, 넣기 전에 T415 로 전수 건수(제목·본문)를 재서 노이즈(일반명사·다른 지역 동명)를 사람이 뺀다(Sprint 2 `docs/spikes/sillok.md` 방식). ③ 키워드가 없는 구는 빈 목록으로 두고 "실록 색인 대상 아님"으로 문서에 밝힌다(빈 목록이면 그 구의 기사는 색인에 없다). ④ 색인 파일 상한은 **[확인 필요: T402 이미지 한도·T408 실측]** — 넘으면 키워드를 줄이거나 D27 (b) 예비안으로 간다. ⑤ `--mode all`(38만 기사)은 하지 않는다.
- **계기**: SCOPE Sprint 4 ② "실록 색인을 서울 전체 키워드로 재구축". 지금 색인은 4개 구 키워드 기사 4,822건·43MB. 키워드는 사실이므로 기억으로 채울 수 없다(§0.2).
- **대안**: 전체 색인 — 수 GB 로 이미지·무료 사용량을 넘을 가능성이 커 기각(T408 이 4개 구 대비 비율을 잰다). 한글 구 이름만 키워드로 — 본문이 한문이라 제목 요약에만 걸려 재현율이 낮고 동명 지명이 섞여 기각(측정 도구로 확인 가능).
```

---

## 3. 사람 선행 · 블로커

### 3.1 사람 선행 작업
| ID | 할 일 | 막는 태스크 | 막혀 있을 때 |
|---|---|---|---|
| H1 | **G1: D24~D28 승인** → DECISIONS.md (스파이크 값이 채워진 문안으로) | Stage 2~5 의 결정 의존 태스크(§2 표) | §2 "승인 전 진행" |
| H2 | **TourAPI 서비스키**(`DATA_GO_KR_SERVICE_KEY`) 발급 완료 알림 → `.env` 입력. 공공데이터포털 활용가이드 문서(키 없이 못 받으면 사람이 내려받아 `docs/private/` 에 둠) | T401 의 "실측 확인" 칸, T422 | T401 은 공개 문서 기준 + `[확인 필요]`, T422 "실행 대기 — H2" |
| H3 | **21개 구 실록 키워드 후보와 출처**(구별 한자 지명 목록, 문헌·URL). T415 출력(건수)을 보고 노이즈 제외 확정 | T418 의 색인 재구축 | 색인은 4개 구 키워드 그대로, 새 구는 "실록 색인 대상 아님" |
| H4 | **GCP**: 프로젝트 생성, 결제 계정 연결(T402 가 필요 여부 확인), **예산 알림(예: 1 USD)**, `gcloud auth login`·`gcloud config set project`, API 사용 설정(Run·Artifact Registry·Secret Manager·Cloud Build — 이름은 T402 확인값) | T426 | Stage 5 까지 진행, 배포 대기 |
| H5 | **Netlify** 계정·`netlify login`(또는 Git 연동), 사이트 이름 | T427 | 배포 대기 |
| H6 | **카카오 개발자 콘솔**에 배포 도메인 등록(T404 절차), JS 키를 Netlify 환경변수 `KC_KAKAO_JS_KEY` 로 입력 | T427 의 카카오 지도 | SVG 지도로 배포(D11 — 기능 유지) |
| H7 | **NVIDIA 크레딧 잔량·호출 한도 확인** → 공개 일일 상한 `KC_LLM_DAILY_UNITS` 확정(기본 300) | T426 공개 전 | 기본 300 으로 공개 |
| H11 | **Secret Manager 에 `NVIDIA_API_KEY` 값 등록**(사람이 직접 — 에이전트는 값을 보지 않는다. 명령은 T425 가이드) | T426 | 배포 대기 |
| H8 | *(선택, D25 대안)* 외부 장소 검색 키(카카오 로컬 등) — 쓰려면 별도 결정 | 없음(이번 태스크 없음) | D25 대로 공공 API 좌표만 |
| H9 | *(선택)* 무료 DB 계정(Neon·Supabase 등) | T430 | 휘발(D27 ⑥) |
| H10 | *(선택)* 25개 구 구청 공식 도메인 승인(`data/web_sources/*.json`, D12 ①) + Tavily 크레딧 | T432 | 하지 않음 |
| H12 | *(선택)* 배포 뒤 스크린샷 확인(T429 가 찍은 것) | T428 의 이미지 | 텍스트만 |

Sprint 3 의 사람 작업(평가셋 검수 H10·좌표 H7·별칭 H8·라벨 H9·D14 확인)은 이번 범위가 아니며 그대로 남는다(이월 표 §8).

### 3.2 블로커 요약
| 블로커 | 막히는 것 | 대응 |
|---|---|---|
| 결정 승인(G1) | Stage 2~5 | Stage 1 은 결정 없이 진행, 스파이크 값으로 문안 완성 |
| TourAPI 키(H2) | T422 실수집, T401 실측 칸 | 코드(T419~T421)는 문서·합성 fixture 로 끝냄. 배포는 TourAPI 없이도 가능 |
| GCP·Netlify·카카오 계정(H4·H5·H6·H11) | Stage 6 | Stage 5 까지 계정 없이. 컨테이너는 로컬 `docker` 가 있으면 로컬로 시험 |
| 실록 키워드(H3, 사실 데이터) | T418 색인 | 4개 구 색인 유지, 새 구는 행사·좌표만 |
| NVIDIA 크레딧(H7) | 공개 일일 상한 확정 | 보수 기본값 300 |
| 무료 사용량·이미지 한도(문서 미확인) | D27·D28 숫자 | T402·T408 로 확인 후 문안 채움 |
| 게이트웨이·샌드박스 | 없음 | D20·D24 ⑥ — 이번 경로는 샌드박스 밖 |

---

## 4. 스테이지 상세

### Stage 1 — 스파이크 · 이월 · 측정
| TASK | 제목 | 범위(소유 경로) | 선행 | 병렬 충돌 |
|------|------|------|------|------|
| T401 | [스파이크] TourAPI KorService2 | `docs/spikes/tourapi.md` | — (H2 있으면 실측 칸) | 없음 |
| T402 | [스파이크] Cloud Run·Artifact Registry·Secret Manager·Cloud Build | `docs/spikes/cloud_run.md` | — | 없음 |
| T403 | [스파이크] Netlify 정적 배포·API 연결 | `docs/spikes/netlify.md` | — | 없음 |
| T404 | [스파이크] 카카오 지도 JS 키 도메인 등록 | `docs/spikes/kakao_domain.md` | — | 없음 |
| T405 | 이월: 캐시 키·해석의 today 일관성 + 캐시 키 LLM_BACKEND | `domains/kcontext/pipeline/{__main__,run}.py`, `domains/kcontext/schedule/{cache,understand}.py`, `tests/domains/kcontext/pipeline/test_kc4_cache_today.py` | — | 없음 |
| T406 | 이월: 보안 로그 날짜 표시·최신 우선 | `frontend/k-context/src/api/http.js`(sanitize 만), `src/components/securitylog/{logic,log-row}.js`, `src/i18n/{ko,en}.js`, `tests/securitylog.kc4.test.js` | — | 없음 |
| T407 | 이월: 행사 검색 사전 제외 색인 | `domains/kcontext/catalog/{store,query,api,__main__}.py`, `backend/chat_story.py`(`_shrink_excluded`·근거 요약 부분만), `scripts/snapshot_catalog.py`(복원 뒤 색인 생성 1줄), `docs/chat-bundle.contract.md`(excluded 절), `tests/domains/kcontext/catalog/test_kc4_search_index.py`, `tests/backend/test_kc4_excluded_merge.py` | — | 없음 |
| T408 | [측정] 서울 API 전체 행·자원 기준선 | `scripts/measure_seoul_rows.py`(신규), `scripts/measure_runtime.py`(신규), `docs/status/measure_2026-10-xx.md` | 서울 키(있음) | 없음(T407 전후 둘 다 재려면 T407 머지 뒤 1회 더 — 같은 문서에 칸 추가) |

### Stage 2 — 공개 안전장치 (D24)
| TASK | 제목 | 범위 | 선행 | 병렬 충돌 |
|------|------|------|------|------|
| T409 | backend 세션·제한 기반 + 설정 + 메타 API (2a) | `backend/session.py`(신규), `backend/limits.py`(신규), `backend/routers/meta.py`(신규), `backend/settings.py`, `backend/app.py`, `.env.example`, `tests/backend/test_kc4_session.py`, `tests/backend/test_kc4_limits.py` | D24 | 없음 |
| T410 | 프론트 세션·제한 오류·배포 주소 설정 (2a) | `frontend/k-context/src/api/{http,index}.js`, `src/events/api.js`, `src/components/securitylog/approve-buttons.js`, `src/i18n/{ko,en}.js`, `config.local.example.js`, `tests/session.kc4.test.js` | D24 | 없음(T406 과 다른 스테이지) |
| T411 | 채팅 세션 분리·동시 처리·일일 상한 (2b) | `backend/chat.py`, `backend/routers/messages.py`, `tests/backend/test_kc4_chat_sessions.py` | T409 | 없음 |
| T412 | 공개 모드 보안 로그·승인·관리자·제보 (2b) | `backend/routers/review.py`, `backend/routers/events.py`, `tests/backend/test_kc4_public_mode.py` | T409 | 없음 |
| T413 | 공개 모드 통합 테스트·로컬 공개 모드 실행 (2c) | `tests/test_kc4_public_e2e.py`, `scripts/kc_demo.sh`(`--public` 옵션) | T409~T412 | 단독 |

### Stage 3 — 서울 25개 구 (D25·D28)
| TASK | 제목 | 범위 | 선행 | 병렬 충돌 |
|------|------|------|------|------|
| T414 | 지역 파일 21개 + 25개 구 검사 | `domains/kcontext/data/regions/*.json`(신규 21), `tests/domains/kcontext/test_kc4_regions25.py` | — (D28 은 키워드 칸만) | 없음 |
| T415 | 실록 키워드 측정 도구 | `domains/kcontext/ingest/sillok_keywords.py`(신규), `tests/domains/kcontext/ingest/test_kc4_sillok_keywords.py` | — | 없음(`ingest/sillok.py` 는 import 만) |
| T416 | 카탈로그 25개 구: 전체 별칭·서울 API 쪽 상한·병합 블로킹 | `domains/kcontext/catalog/{target,seoul,merge}.py`, `.env.example`(`KC_TARGET_REGION=all`), `scripts/kc_demo.sh`(`REGIONS`), `tests/domains/kcontext/catalog/test_kc4_target_all.py`, `test_kc4_merge_blocking.py` | — | `.env.example` 은 T409(Stage 2)도 고침 — 다른 스테이지. `kc_demo.sh` 는 T413(Stage 2) — 다른 스테이지 |
| T417 | 좌표 자동 부착(서울 API 장소) | `domains/kcontext/places.py`, `domains/kcontext/places_build.py`(신규), `domains/kcontext/data/places/auto_rules.json`(신규 — 서울 범위 값은 H 확인 전 `null`), `domains/kcontext/pipeline/run.py`(`_attach_coords` 만), `frontend/k-context/src/lib/chat-bundle.js`(`COORD_AUTO` 매핑), `src/i18n/{ko,en}.js`, `tests/domains/kcontext/test_kc4_places_auto.py`, `frontend/k-context/tests/coordauto.kc4.test.js` | D25 | 없음 |
| T418 | 실행: 25개 구 수집·색인·자동 좌표·스냅샷·측정 (3b) | `domains/kcontext/data/regions/*.json` 의 `sillok_keywords`(H3 값만), `domains/kcontext/data/snapshots/catalog/*`, `domains/kcontext/data/catalog_sources.json`(verified_at·notes), `docs/status/seoul25_2026-10-xx.md`, `docs/spikes/sillok.md`(25개 구 절 추가) | T414~T417, H3(색인 부분), D28 | 단독 |

### Stage 4 — TourAPI (D26)
| TASK | 제목 | 범위 | 선행 | 병렬 충돌 |
|------|------|------|------|------|
| T419 | TourAPI 수집기·정규화 (4a) | `domains/kcontext/catalog/tourapi.py`(신규), `domains/kcontext/catalog/sources.py`, `domains/kcontext/data/catalog_sources.json`(`tourapi_kto` 항목만), `domains/kcontext/data/tourapi_codes.json`(신규, T401 확인값), `tests/domains/kcontext/catalog/test_kc4_tourapi.py`, `tests/fixtures/tourapi/*.json`(합성) | T401, D26 | 없음 |
| T421 | 병합 규칙 D26 반영 (4a) | `domains/kcontext/catalog/merge.py`, `tests/domains/kcontext/catalog/test_kc4_merge_kto.py` | T416(merge.py), D26 | 없음 |
| T420 | TourAPI 관광지 → 좌표 사전 (4b) | `domains/kcontext/places_build.py`(입력 어댑터 추가), `domains/kcontext/catalog/tourapi.py`(관광지 내보내기 함수만), `tests/domains/kcontext/test_kc4_places_tourapi.py` | T417·T419 | 단독 |
| T422 | 실수집·보고 (4c) | `docs/status/events_data_2026-10-xx.md`(신규), `catalog_sources.json`(`tourapi_kto` 의 status·verified_at·notes) | T419~T421, H2 | 단독 |

### Stage 5 — 배포 패키징 (D27)
| TASK | 제목 | 범위 | 선행 | 병렬 충돌 |
|------|------|------|------|------|
| T423 | Dockerfile·컨테이너 설정 | `Dockerfile`(신규), `.dockerignore`, `deploy/cloudrun/entrypoint.sh`(신규), `deploy/cloudrun/README.md`(신규), `scripts/build_image_data.sh`(신규), `tests/test_kc4_container_files.py` | D27, T418(데이터 경로) | 없음 |
| T424 | Netlify 설정·빌드 스크립트 | `netlify.toml`(신규), `scripts/netlify_build.sh`(신규), `tests/test_kc4_netlify_build.py` | D27, T403·T404 | 없음 |
| T425 | Cloud Run 배포 스크립트·가이드 | `scripts/deploy_cloudrun.sh`(신규), `docs/guides/DEPLOY.md`(신규), `deploy/README.md`(표에 cloudrun·netlify 줄) | D27, T402 | 없음 |

### Stage 6 — 실제 배포
| TASK | 제목 | 범위 | 선행 | 병렬 충돌 |
|------|------|------|------|------|
| T426 | Cloud Run 배포·공개 URL 남용 점검 | `docs/status/deploy_2026-10-xx.md`(신규) — 코드 변경 없음(발견은 이월로) | T423·T425, H4·H7·H11 | 단독 |
| T427 | Netlify 배포·카카오 도메인·화면 확인 | 같은 문서에 절 추가 | T424·T426, H5·H6 | 단독(T426 뒤) |

### Stage 7 — 문서
| TASK | 제목 | 범위 | 선행 | 병렬 충돌 |
|------|------|------|------|------|
| T428 | README·상태·가이드 갱신 | `README.md`, `docs/status/2026-10-xx_구현상태.md`(신규), `docs/guides/{SETUP,EVENTS_CATALOG}.md`, `docs/diagram/system-state.html` | T427 | 없음 |
| T429 | 배포 URL 스크린샷 | `docs/demo/s4-0{1..5}-*.png` | T427 | 없음 |

### 스테이지 구성 근거
- **Stage 1**: 결정 문안의 `[확인 필요]` 를 채울 스파이크 4개와 측정 1개를 결정 승인 앞에 둔다(D27·D28 숫자는 측정 없이는 정할 수 없다). 이월 3개(T405~T407)는 결정이 필요 없고 서로 다른 파일만 건드리며, 특히 **T407(검색 사전 제외)은 25개 구 확장과 Cloud Run 메모리의 전제**라 가장 먼저 한다. 8개 태스크의 파일 집합이 겹치지 않아 모두 병렬이다.
- **Stage 2**: 우선순위 ①. `chat.py`·`messages.py`·`review.py`·`events.py`·`app.py`·`settings.py` 가 얽혀 있어, 공유 인터페이스(`session.py`·`limits.py`·설정 필드·`app.state` 이름)를 T409 가 먼저 만들고(2a), 그 인터페이스를 쓰는 라우터 쪽을 2b 에서 파일별로 나눴다. 프론트(T410)는 §5.1 계약(헤더 이름·오류 코드)만 알면 되므로 2a 에서 병렬. 2c 에서 공개 모드 전체를 한 번에 검증한다.
- **Stage 3**: 우선순위 ②. 지역 파일·측정 도구·카탈로그·좌표가 서로 다른 파일이라 3a 병렬. 실데이터 실행(T418)은 사람 데이터(H3)와 3a 전부에 걸리므로 단독 3b. H3 이 없으면 색인 부분만 건너뛴다.
- **Stage 4**: 우선순위 ③. `merge.py` 를 T416 이 Stage 3 에서 먼저 고치므로 T421 은 Stage 4 로. `places_build.py` 를 T417 과 T420 이 같이 고치므로 T420 은 Stage 4 안에서도 뒤(4b). 키가 필요한 T422 를 맨 끝(4c)에 두어 키가 없어도 Stage 5 로 간다.
- **Stage 5**: 우선순위 ④ 중 계정이 필요 없는 부분. 세 태스크가 각자 새 파일만 만든다.
- **Stage 6**: 계정·도메인 등록이 필요한 일만. Netlify 쪽은 Cloud Run URL(또는 프록시 대상)이 있어야 하므로 T426 → T427 순차.
- **Stage 7**: 우선순위 ⑤. 배포 URL 이 있어야 쓸 수 있다.

---

## 5. 태스크별 상세 구현 명세

### 5.1 Stage 2 공통 계약 (T409~T413 이 함께 지킨다)

| 항목 | 값 |
|---|---|
| 세션 발급 | `POST /api/session` 본문 없음(또는 `{}`) → 201 `{"session": "<43자>", "ttl_s": 7200}`. 공개·로컬 모드 모두 있음 |
| 세션 헤더 | `X-KC-Session: <토큰>` — 정규식 `^[A-Za-z0-9_-]{43}$`. 틀린 형식은 "없음"으로 본다 |
| 세션 없음/만료 | 공개 모드: `POST /api/messages` → 401 `no_session`. `GET /api/messages`·`GET /api/audit` → 200 `[]`. 로컬 모드: 헤더가 없으면 공용 세션 `"local"`(지금 동작) |
| 제한 초과 | 429 `{"error":{"code":"rate_limited","message":"요청이 너무 많다"}}` + `Retry-After: <초>` |
| 동시 처리 초과 | 429 `busy`(지금 코드 그대로) |
| 일일 상한 | 503 `daily_limit` |
| 공개 모드에서 닫힌 API | 403 `disabled_in_public` |
| 메타 | `GET /api/meta` → `{"schema":"kc-meta/v1","public":bool,"decisions":"open"|"closed","reports":"open"|"closed"}` (숫자 상한은 싣지 않는다 — 우회 단서 최소화) |
| CORS | `allow_headers=["Content-Type","X-Admin-Token","X-KC-Session"]`, `expose_headers=["X-Audit-Skipped","Retry-After"]` |
| 설정(env) | `KC_PUBLIC_MODE`(`1`이면 켬, 그 밖은 끔) · `KC_TRUSTED_PROXY_HOPS`(정수 0~3, 기본 0) · `KC_LLM_DAILY_UNITS`(정수 ≥0, 기본 300) · `KC_STORY_CONCURRENCY`(1~8, 기본 2) · `KC_SESSION_TTL_S`(기본 7200) · `KC_SESSION_MAX`(기본 1000) |

---

#### T401 — [스파이크] TourAPI KorService2 확인
- **변경 파일**: `docs/spikes/tourapi.md` (신규). 코드 변경 없음.
- **인터페이스**: 문서 절 고정 — ① 출처 목록(URL·확인 날짜) ② 엔드포인트(사용자 제공 `https://apis.data.go.kr/B551011/KorService2` 의 공식 확인 여부) ③ 오퍼레이션 표(이름 · 용도 · 필수 파라미터 · 선택 파라미터 · 응답 필드 · 페이지 방식) ④ 인증(서비스키 파라미터 이름, 인코딩/디코딩 키 차이) ⑤ 호출 한도(개발 계정·운영 계정 일일 트래픽) ⑥ 응답 형식(JSON 지정 방법, 오류 응답 형태·코드) ⑦ 서울 지역 코드·시군구 코드 조회 방법과 **그 조회로 얻은 서울 25개 구 코드 표**(키가 있으면 실호출, 없으면 `[확인 필요]`) ⑧ 행사(축제) 기간 필드·좌표 필드·수정일 필드·콘텐츠 id 필드 이름 ⑨ 이용 조건(공공누리 유형, 사진 제한 — `catalog_sources.json` 의 기존 메모와 대조) ⑩ T419 가 쓸 "확정 필드 목록"과 "쓰지 말 것 목록".
- **핵심 로직**: 1) 공공데이터포털 데이터셋 페이지(`https://www.data.go.kr/data/15101578/openapi.do`)와 첨부 활용가이드, 한국관광공사 TourAPI 공식 안내 페이지를 읽는다. 2) 각 값 옆에 출처 URL·문서 이름(버전)·확인 날짜를 적는다. 3) H2 키가 있으면 서울 지역 행사 목록 1쪽·관광지 목록 1쪽·코드 조회 1회만 호출해 실제 응답의 필드 이름과 대조한다(최대 20회, §6). 응답 원문은 커밋하지 않고 필드 이름·타입·예시 값의 형식(값 자체가 아니라 `YYYYMMDD` 같은 형태)만 적는다. 4) 기억으로 쓴 값은 하나도 없어야 한다 — 확인 못 한 칸은 `[확인 필요]`.
- **엣지 케이스**: 활용가이드가 로그인 뒤에만 받아지면 H2 로 사람에게 요청하고 그 칸은 `[확인 필요]`. KorService2 와 이전 버전(KorService1) 문서가 섞여 있으면 버전별로 나눠 적고 KorService2 만 "확정"으로 표시. 실호출 결과가 문서와 다르면 둘 다 적고 실호출을 우선 표시.
- **지켜야 할 규칙**: Sprint 2 규칙(오퍼레이션 이름·필드는 확인 전에 코드에 쓰지 않는다) · 규칙 1(키 값·키가 든 URL 기록 금지) · 규칙 4 취지(기억이 아니라 문서).
- **DoD**: 문서에 ①~⑩ 절이 있고 모든 표 행에 출처 URL 또는 `[확인 필요]` 가 있다. `grep -c "확인 필요" docs/spikes/tourapi.md` 결과를 문서 끝 "남은 확인" 수와 맞춘다. 키 값 문자열이 없음을 `grep -nE "serviceKey=[^<{\[]" docs/spikes/tourapi.md` 0건으로 확인.
- **병렬 충돌**: 없음.

#### T402 — [스파이크] Cloud Run·Artifact Registry·Secret Manager·Cloud Build
- **변경 파일**: `docs/spikes/cloud_run.md` (신규).
- **인터페이스**: 절 고정 — ① 출처(URL·날짜) ② 요청 시간 한도(기본·최대, 설정 플래그) ③ 메모리·CPU 선택지와 "인스턴스 파일시스템 쓰기가 메모리에 잡히는지" ④ 무료 사용량(요청 수·vCPU-초·GiB-초·네트워크, **해당 리전 조건**) ⑤ 결제 계정이 무료 사용량에도 필요한지, 예산 알림 설정 방법 ⑥ 이미지 크기 한도와 Artifact Registry 무료 저장 용량 ⑦ Cloud Build 무료 사용량(또는 로컬 `docker build` + push 로 대신하는 방법) ⑧ Secret Manager 무료 사용량과 Cloud Run 에 env 로 주입하는 플래그·서비스 계정 권한 이름 ⑨ `max-instances`·`min-instances`·동시 요청 수(concurrency) 플래그 ⑩ 요청 헤더 `X-Forwarded-For` 를 Cloud Run 앞단이 어떻게 붙이는지(문서 근거) ⑪ 콜드 스타트·시작 프로브·`PORT` env ⑫ D27 ③ 에 넣을 권장 값 표(시간 한도·메모리·CPU·max-instances·concurrency·리전) — 근거 칸 포함.
- **핵심 로직**: Google Cloud 공식 문서(cloud.google.com/run/docs, /run/pricing, /artifact-registry/pricing, /secret-manager/pricing, /build/pricing)만 읽는다. 값마다 URL·확인 날짜. 실제 계정 조작은 하지 않는다.
- **엣지 케이스**: 무료 사용량이 리전에 따라 다르면 서울(asia-northeast3) 포함 여부를 따로 적고, 포함되지 않으면 "무료 리전 + 지연 증가"를 D27 문안에 반영하도록 권고. 문서끼리 숫자가 다르면 둘 다 적고 `[확인 필요]`.
- **지켜야 할 규칙**: 기억이 아닌 문서(규칙 4 취지) · SCOPE "유료 인프라 금지" — 무료 사용량을 넘는 권장값을 쓰지 않는다.
- **DoD**: ①~⑫ 절 존재, ⑫ 표의 모든 값에 근거 절 번호. "유료가 되는 조건" 목록이 있다.
- **병렬 충돌**: 없음.

#### T403 — [스파이크] Netlify 정적 배포·API 연결
- **변경 파일**: `docs/spikes/netlify.md` (신규).
- **인터페이스**: 절 고정 — ① 출처 ② 정적 배포 방법(CLI `netlify deploy` 와 Git 연동, publish 디렉터리·build command) ③ 빌드 때 환경변수 읽기(빌드 스크립트에서 파일 생성 가능 여부, 값이 로그에 찍히는지) ④ **프록시 리라이트**(`/api/*` → 외부 URL, status 200)의 **요청 시간 한도** ⑤ 프록시가 방문자 IP 를 어떤 헤더로 넘기는지(`X-Forwarded-For` 등) ⑥ `_headers`/`netlify.toml` 의 헤더(CSP) 설정과 HTML meta CSP 의 관계(둘 다 적용되는지) ⑦ 무료 플랜 한도(대역폭·빌드 시간·사이트 수) ⑧ 배포 미리보기 도메인 형식(카카오 도메인 등록과 관련) ⑨ 결론 표: **프록시 vs 직접 CORS** — 우리 조건(일정 요청 최대 100초, IP 기반 제한, CSP)별 가능/불가와 권고.
- **핵심 로직**: docs.netlify.com 의 redirects·rewrites/proxies·headers·build environment variables·limits 문서를 읽는다. 프록시 한도가 100초 미만이면 권고는 "직접 CORS".
- **엣지 케이스**: 프록시 시간 한도가 문서에 없으면 `[확인 필요]` 로 두고 T427 에서 실측(100초 걸리는 요청 대신 `/api/meta` 와 실제 일정 문장 1회)하도록 적는다 — 이 경우 권고는 직접 CORS(안전한 쪽).
- **지켜야 할 규칙**: 기억이 아닌 문서.
- **DoD**: ①~⑨ 존재, ⑨ 표에 근거 절 번호. D27 ② 를 채울 문장 1개를 문서 끝에 제안.
- **병렬 충돌**: 없음.

#### T404 — [스파이크] 카카오 지도 JS 키 도메인 등록
- **변경 파일**: `docs/spikes/kakao_domain.md` (신규).
- **인터페이스**: 절 — ① 출처(developers.kakao.com 문서 URL·날짜) ② 웹 플랫폼 도메인 등록 위치·형식(스킴 포함 여부, 포트, 와일드카드 지원) ③ 등록 가능 도메인 수 ④ 지도 JS SDK 무료 사용량·초과 시 동작 ⑤ JS 키가 브라우저에 노출되는 것이 설계상 정상인지와 보호 수단(도메인 제한) ⑥ Netlify 미리보기 도메인을 등록해야 하는지 ⑦ H6 절차 체크리스트(사람이 그대로 따라 할 순서).
- **핵심 로직**: 공식 문서만. 키 값은 다루지 않는다.
- **엣지 케이스**: 와일드카드 미지원이면 운영 도메인 1개만 등록하고 미리보기에서는 SVG 지도(D11)로 보인다는 사실을 적는다.
- **지켜야 할 규칙**: 규칙 1(키 값 없음).
- **DoD**: ①~⑦ 존재. ⑦ 은 번호 매긴 단계.
- **병렬 충돌**: 없음.

#### T405 — 이월: 캐시 키·해석의 today 일관성 (+ W7 LLM_BACKEND)
- **출처**: Sprint 3 "Stage 4 에서 이월" 첫 줄(캐시 키와 해석 기준 불일치), "Stage 2 에서 이월" W7(캐시 키에 `LLM_BACKEND*` 없음).
- **변경 파일**: `domains/kcontext/pipeline/__main__.py`, `domains/kcontext/pipeline/run.py`, `domains/kcontext/schedule/cache.py`, `domains/kcontext/schedule/understand.py`(인자 전달만), `tests/domains/kcontext/pipeline/test_kc4_cache_today.py`(신규).
- **인터페이스**:
  - `run_story_pipeline(..., today: date | None = None)` — None 이면 지금처럼 `kst_today()`.
  - `understand_with_meta(..., today: date | None = None)` — 없으면 추가하고 하위 `understand`(이미 `today` 를 받음)로 넘긴다.
  - `key_for(text, trip, *, root=None, today=None, env=None) -> str` — `today` 를 키에 넣는 조건을 "trip 이 None" 에서 **"trip 이 None 이거나 형식이 틀림(YYYY-MM-DD 두 개, from ≤ to 가 아님)"** 으로 바꾼다. `env`(None 이면 `os.environ`)에서 `LLM_BACKEND` 와 `LLM_BACKEND_` 로 시작하는 이름=값을 정렬해 키에 넣는다. 캐시 형식 버전을 한 단계 올린다(지금 v4 → v5; 읽기 쪽 검사가 옛 버전을 버린다).
- **핵심 로직**: 1) `__main__` 에서 `today = kst_today()` 를 **한 번** 구한다. 2) `key_for(text, trip, today=today)` 와 `run_story_pipeline(..., today=today)` 에 같은 값을 넘긴다. 3) `run_story_pipeline` 은 `understand_with_meta(..., today=today)` 로 넘긴다. 4) trip 형식 검사는 `schedule` 쪽에 이미 있는 검사 함수를 재사용한다(없으면 `cache.py` 안에 `_trip_ok(trip) -> bool` 사설 함수로 둔다 — 정규식 `^\d{4}-\d{2}-\d{2}$` 두 개 + `date.fromisoformat` 성공 + from ≤ to).
- **엣지 케이스**: 자정 경계 — 테스트에서 `today` 를 2026-12-31 로 고정하고 `kst_today` 를 2027-01-01 을 내도록 monkeypatch 해도 키와 해석이 같은 날을 쓰는지. 형식 틀린 trip 은 trip 없는 요청과 **다른 키**(TRIP_INVALID 문제가 재사용되지 않게). `LLM_BACKEND` 값이 다르면 다른 키.
- **지켜야 할 규칙**: D15 ④(키 구성 요소 — 이번에 today·백엔드가 늘어날 뿐 의미는 같음) · D22 ② · D6(백엔드는 생성 시점 고정).
- **DoD**: `uv run python -m pytest -q tests/domains/kcontext/pipeline/test_kc4_cache_today.py` 통과(케이스: 같은 today 전달, 자정 경계, 잘못된 trip 키 분리, LLM_BACKEND 키 분리, v4 캐시 무시). 전체 회귀(§7) 통과, 건수 감소 없음.
- **병렬 충돌**: 없음.

#### T406 — 이월: 보안 로그 날짜 표시·최신 우선
- **출처**: Sprint 3 "Stage 6 에서 이월" — "보안 로그가 날짜 없이 시각만, 오래된 기록이 위".
- **변경 파일**: `frontend/k-context/src/api/http.js`(`sanitizeAuditEntry` 만), `src/components/securitylog/logic.js`, `src/components/securitylog/log-row.js`, `src/i18n/ko.js`·`en.js`(필요한 키만), `frontend/k-context/tests/securitylog.kc4.test.js`(신규).
- **인터페이스**: `sanitizeAuditEntry(e)` 가 `at` 을 보존 — 문자열이고 40자 이하이며 `Date.parse` 가 유한하면 `at` 필드로 남긴다, 아니면 뺀다. `logic.js` 에 `sortNewestFirst(entries) -> entries` (새 배열, `at` 내림차순, `at` 없는 항목은 원래 순서를 유지한 채 맨 뒤) 와 `formatWhen(at, lang) -> string`(Asia/Seoul 기준 `MM-DD HH:MM:SS`; `at` 이 없거나 잘못이면 `null`) 을 export.
- **핵심 로직**: 1) 목록을 그릴 때 `sortNewestFirst` 적용. 2) 행 표시는 `formatWhen(at)` 이 있으면 그것, 없으면 기존 `time`. 3) 포맷은 `Intl.DateTimeFormat` 에 `timeZone: 'Asia/Seoul'` 을 주고 부분을 조립(로캘 차이 없이 숫자 고정).
- **엣지 케이스**: mock 데이터(`at` 없음) — 지금과 같은 표시·순서. 같은 `at` 두 개 — `id` 오름차순으로 안정 정렬. 미래 시각·잘못된 문자열 — `at` 제거.
- **지켜야 할 규칙**: 프론트는 표의 파일만 · 서버 문자열을 그대로 쓰지 않는 기존 방침(검증된 필드만).
- **DoD**: `(cd frontend/k-context && node --test)` 통과, 새 테스트(보존·정렬·포맷·mock 무변화) 포함. 실제 서버에서 보안 로그 1건 이상이 `10-1x HH:MM:SS` 로 위에 최신이 오는지 헤드리스 확인 또는 수동 확인 기록.
- **병렬 충돌**: 없음(Stage 2 의 T410 도 `http.js` 를 고치지만 다른 스테이지).

#### T407 — 이월: 행사 검색 사전 제외 색인
- **출처**: Sprint 3 "Stage 5 에서 이월" — "행사 검색 1회 약 6초(8.7k 항목 매번 로드) — 끝난 행사 사전 제외·색인화 검토", 상태 문서 🔶 "행사 검색 속도".
- **변경 파일**: `domains/kcontext/catalog/store.py`, `query.py`, `api.py`, `__main__.py`, `backend/chat_story.py`(`_shrink_excluded` 와 근거 요약에서 excluded 수를 세는 곳만), `scripts/snapshot_catalog.py`(복원 끝에 색인 생성 호출 1줄), `docs/chat-bundle.contract.md`(excluded 절), 테스트 2개(신규).
- **인터페이스**:
  - `query.py`: 종료·취소 제외 사유 문자열을 모듈 상수로 꺼낸다 — `REASON_ENDED`, `REASON_CANCELLED`(지금 `search_events` 안의 문자열 그대로; 값 변경 금지). `search_events(entries, a, *, now, coverage, pre_excluded: Mapping[str, int] | None = None) -> dict` — `pre_excluded` 가 있으면 결과에 `"excluded_precomputed": dict(pre_excluded)` 를 싣고 `counts.excluded` 에 합을 더한다.
  - `store.py`: `SEARCH_INDEX = "search_index.json"`, `save_search_index(entries, built_at, now) -> dict`(요약 반환), `load_search_index() -> tuple[list[EventEntry], dict] | None`. 파일 형식 `{"schema":"kc-search-index/v1","built_at":<entries.json 의 built_at>,"indexed_at":<ISO>,"total":int,"pre_excluded":{사유:수},"entries":[...]}`. `save_entries` 끝에서 `save_search_index` 를 자동 호출(같은 잠금 안).
  - `api.py::_search`: 색인이 있고 `schema` 가 맞고 `built_at == store.entries_built_at()` 이고 `now >= indexed_at` 이면 색인 항목 + `pre_excluded` 로 검색, 아니면 지금처럼 전체.
  - `__main__.py`: 하위 명령 `reindex`(entries.json 에서 색인만 다시 만듦, 출력 `{"total","indexed","pre_excluded"}`).
  - `backend/chat_story.py::_shrink_excluded`: `excluded_total = len(excl) + sum(excluded_precomputed.values())`, `excluded_by_reason` 에 사전 제외 사유 수를 더한 뒤 상위 20 정렬. 근거 요약("수집 N건 중 M건 남김")의 N 도 같은 합을 쓴다. `excluded_precomputed` 키는 묶음으로 내보내지 않는다(기존 필드만).
- **핵심 로직**: 1) 색인 생성 시점 `indexed_at=now` 에서 `event_lifecycle(e, now)` 가 `ended`·`cancelled` 인 항목은 색인에서 빼고 사유별로 센다(사유 문자열은 `search_events` 가 같은 항목에 붙였을 것과 같아야 한다 — 상수 공유). 2) 시간은 앞으로만 가므로 `now_search >= indexed_at` 이면 "끝남"은 그대로 끝남이다(취소는 데이터 기반이라 재생성 전까지 고정). 3) 나머지 규칙(D23 등)은 검색 시점에 지금처럼 적용.
- **엣지 케이스**: 색인 없음(스냅샷 복원 직후 등)·schema 다름·`built_at` 불일치·`now < indexed_at`(시계 역행) → 전체 경로(결과 동일). 색인 파일 깨짐 → 전체 경로 + 결과 `problems` 에 넣지 않음(조용한 폴백, 로그만). `lifecycle` 이 `postponed`·`unknown` 이면 색인에 남긴다.
- **지켜야 할 규칙**: D13 ⑤(데이터를 지우지 않는다 — entries.json 은 그대로, 색인은 파생물) · D23 · D10(backend 는 JSON 만).
- **DoD**: ① `test_kc4_search_index.py`: 합성 항목(끝남·취소·진행·종료일 없음 1년 초과·이내 섞음)으로 **전체 경로와 색인 경로의 `events`·`counts`·사유별 합이 같음**, 폴백 4종. ② `test_kc4_excluded_merge.py`: `_shrink_excluded` 합산. ③ 실측: `var/catalog` 로 `reindex` 후 데모 문장 검색 시간 3회 중앙값 기록(목표 ≤ 1.5초, 못 미치면 값과 원인을 기록하고 이월). 묶음의 `excluded_total` 이 변경 전과 같은지(8,620 근처의 같은 값) 확인. ④ 전체 회귀.
- **병렬 충돌**: 없음.

#### T408 — [측정] 서울 API 전체 행·자원 기준선
- **변경 파일**: `scripts/measure_seoul_rows.py`(신규), `scripts/measure_runtime.py`(신규), `docs/status/measure_2026-10-xx.md`(신규).
- **인터페이스**:
  - `uv run python scripts/measure_seoul_rows.py --today YYYY-MM-DD [--max-pages 40]` → stdout JSON `{"list_total_count", "fetched", "pages", "by_guname":{구:수}, "no_guname", "not_ended_by_end_date", "with_latlng", "distinct_place_with_latlng"}`. 키는 `core.llm.envfile` 의 허용 목록 로더로 `SEOUL_OPENAPI_KEY` 하나만 읽는다(셸 env 우선). 행 원문은 저장하지 않는다.
  - `uv run python scripts/measure_runtime.py --catalog var/catalog --index var/index/kcontext.db [--with-llm]` → 카탈로그 검색 자식 프로세스 3회의 시간·`resource.getrusage(RUSAGE_CHILDREN).ru_maxrss`, 파이프라인 자식 1회(기본 `--with-llm` 없음: 캐시 적중 문장으로; 있으면 LLM 최대 2회) 시간·최대 RSS, 파일 크기.
- **핵심 로직**: `seoul.fetch_rows` 를 재사용(새 HTTP 코드 없음). 끝남 판정은 `END_DATE < today` 만 센다(표시용 측정). 측정 문서에 4개 구 대비 25개 구의 예상 배수(행 수·끝나지 않은 행 수)와 색인 크기 추정 근거(4개 구 키워드 기사 4,822건 → 43MB 비율)를 적는다.
- **엣지 케이스**: `list_total_count > max_pages*1000` 이면 `"truncated": true` 로 표시하고 멈춘다(T416 에서 상한을 올리는 근거). 키 없음 → 종료 코드 2, 메시지에 키 이름만.
- **지켜야 할 규칙**: 규칙 1 · §6 호출 상한(서울 API ≤ 40회) · D7(호스트 수집).
- **DoD**: 두 스크립트 실행 결과가 문서에 표로 있고, 원응답·키가 없음. T407 머지 뒤 `measure_runtime.py` 를 한 번 더 돌려 같은 문서에 "T407 뒤" 칸을 채운다. ruff 통과.
- **병렬 충돌**: 없음.

#### T409 — backend 세션·제한 기반 + 설정 + 메타 API
- **변경 파일**: `backend/session.py`(신규), `backend/limits.py`(신규), `backend/routers/meta.py`(신규), `backend/settings.py`, `backend/app.py`, `.env.example`, `tests/backend/test_kc4_session.py`, `tests/backend/test_kc4_limits.py`.
- **인터페이스**:
  ```python
  # backend/session.py — core 만 import (D3·D10)
  TOKEN_RE: re.Pattern  # ^[A-Za-z0-9_-]{43}$
  LOCAL_SESSION_ID = "local"
  @dataclass
  class Session:
      id: str; created: float; last_seen: float
      history: deque  # maxlen=100, (message dict, in_llm_context: bool)
      logs: deque     # maxlen=200, 보안 로그 항목 dict
      seq: int = 0
      busy: threading.Lock  # 세션당 동시 1건
      lock: threading.Lock  # history·logs·seq 보호
  class SessionStore:
      def __init__(self, *, ttl_s: float, max_sessions: int, clock: Callable[[], float] = time.monotonic): ...
      def create(self) -> Session            # 새 토큰, 상한 넘으면 LRU 하나 제거
      def get(self, token: str | None) -> Session | None   # 형식 틀림·없음·만료 → None, 찾으면 last_seen 갱신
      def local(self) -> Session             # 로컬 모드 공용 세션(만료 없음)
      def __len__(self) -> int
  # backend/limits.py
  @dataclass(frozen=True)
  class Rule: name: str; limit: int; window_s: int
  RULES: dict[str, tuple[Rule, ...]]  # §6.2 표 그대로(키: "session_create","messages","events","reports","admin","read")
  class RateLimiter:
      def __init__(self, clock=time.monotonic): ...
      def hit(self, bucket: str, key: str, rules: tuple[Rule, ...]) -> int | None  # 허용이면 None, 거절이면 Retry-After 초
  class DailyBudget:
      def __init__(self, units: int, *, today: Callable[[], date]): ...
      def reserve(self, n: int) -> bool          # KST 날짜가 바뀌면 0 으로
      def refund(self, n: int) -> None           # 음수·초과 방지
      @property
      def used(self) -> int
  class AdminGuard:  # 관리자 토큰 실패 5회 → 15분 차단(IP 별)
      def blocked(self, ip: str) -> bool; def fail(self, ip: str) -> None; def ok(self, ip: str) -> None
  def client_ip(request, trusted_hops: int) -> str
  def classify(path: str, method: str) -> str | None  # 경로 → RULES 키
  ```
  - `Settings` 에 필드 추가: `public_mode: bool=False`, `trusted_proxy_hops: int=0`, `llm_daily_units: int=300`, `story_concurrency: int=2`, `session_ttl_s: int=7200`, `session_max: int=1000`. `from_env` 는 §5.1 env 를 읽고 범위 밖이면 `ValueError`(서버 시작 실패 — 조용히 기본값으로 가지 않는다).
  - `app.py`: `app.state.sessions = SessionStore(...)`, `app.state.limiter`, `app.state.budget`, `app.state.admin_guard`. CORS 헤더 §5.1. HTTP 미들웨어 `_rate_limit`(본문 크기 검사 뒤): `bucket = classify(path, method)`; 공개 모드에서만 적용(로컬 모드는 통과); 키는 `ip`(세션 헤더가 유효하면 `messages` 는 세션 키로도 한 번 더); 거절이면 429 `rate_limited` + `Retry-After`. `ROUTERS` 에 `meta.router` 와 세션 라우트를 추가(세션 발급은 `meta.py` 안의 `POST /api/session` — 발급 자체도 `session_create` 규칙을 거친다).
- **핵심 로직**: 고정 창 카운터 `{(bucket, rule.name, key): (window_start, count)}` 를 `threading.Lock` 으로 보호, 만료 항목은 `hit` 때 1,000번에 한 번 정리. `client_ip`: `trusted_hops==0` → `request.client.host`; 아니면 `X-Forwarded-For` 를 쉼표로 나눠 공백 제거, `len >= hops` 이면 `parts[-hops]`, 아니면 `request.client.host`; 결과가 IP 형식(`ipaddress.ip_address`)이 아니면 `"unknown"`. `DailyBudget` 의 날짜는 KST.
- **엣지 케이스**: `request.client` 가 None(테스트 클라이언트) → `"unknown"`. 세션 상한 도달 시 생성 → 가장 오래 안 쓴 세션 제거(진행 중 `busy` 가 잡힌 세션은 건너뛰고, 전부 바쁘면 503 `busy` 대신 429 `busy`). TTL 만료 판정은 `get` 시점. 토큰 비교는 dict 조회(타이밍 공격 실익 없음 — 토큰 길이 43자 임의값). 설정 범위: hops 0~3, units 0~100000(0 이면 LLM 호출 전부 503), concurrency 1~8.
- **지켜야 할 규칙**: D24 ①③④ · D3·D10(backend 는 core 만) · 규칙 1(토큰을 로그에 남기지 않음 — 로그에는 토큰 sha256 앞 8자만).
- **DoD**: `test_kc4_session.py`(발급 형식, 만료, LRU, 로컬 세션, 바쁜 세션 보호), `test_kc4_limits.py`(창 경계, Retry-After 값, 일일 리셋 KST, refund 하한, client_ip 의 hops 0·1·2·잘못된 헤더, classify 표, 설정 범위 오류, 공개 모드 끔이면 미들웨어 통과). `uv run python -m pytest -q tests/backend` 통과 + 전체 회귀.
- **병렬 충돌**: 없음(T410 은 프론트).

#### T410 — 프론트 세션·제한 오류·배포 주소 설정
- **변경 파일**: `frontend/k-context/src/api/http.js`, `src/api/index.js`, `src/events/api.js`, `src/components/securitylog/approve-buttons.js`, `src/i18n/ko.js`·`en.js`, `config.local.example.js`, `frontend/k-context/tests/session.kc4.test.js`(신규).
- **인터페이스**:
  - `http.js`: `SESSION_KEY = 'kc.session'`. `createHttpApi({ baseUrl, storage = globalThis.sessionStorage })` 내부 `ensureSession()` — 저장값이 `^[A-Za-z0-9_-]{43}$` 이면 그대로, 아니면 `POST /session` 으로 받아 저장. 모든 요청에 `X-KC-Session` 헤더. 401 `no_session` 이면 저장값 지우고 **한 번만** 새로 받아 재시도. `ERROR_MESSAGES` 에 `rate_limited: '요청이 많아요. 잠시 뒤 다시 시도해 주세요'`, `daily_limit: '오늘 사용량이 다 찼어요. 내일 다시 시도해 주세요'`, `disabled_in_public: '공개 데모에서는 쓸 수 없는 기능입니다'`, `no_session: '연결을 다시 시도하고 있어요'`. `getMeta()` 추가(`GET /meta`, 실패하면 `{public:false, decisions:'open', reports:'open'}`).
  - `probeBackend` 는 그대로(`GET /messages` 가 배열이면 true — 공개 모드에서 세션 없이도 `[]`).
  - `index.js`: `DEFAULT_CHAT_BASE` 결정을 `configuredBase(win = globalThis) ?? 'http://localhost:8000/api'` 로. `configuredBase` 는 `win.KC_API_BASE` 가 문자열이고 ① 같은 출처 경로(`/api` 형태) 또는 ② `https:` 절대 URL(사용자 이름·비밀번호 없음, 경로 끝 `/` 제거)일 때만 값, 아니면 null. `?base=` 검증(`safeBase`)은 그대로 — URL 로는 외부 주소를 받지 않는다.
  - `events/api.js::defaultBase`: 같은 `configuredBase` 를 먼저 본다(import 해서 공유 — 순환 import 가 생기면 `src/lib/api-base.js` 신규로 빼고 표에 추가).
  - `approve-buttons.js`: `ctx.api.meta?.decisions === 'closed'` 이면 버튼 대신 "공개 데모에서는 승인 기능이 닫혀 있어요" 문구.
  - `config.local.example.js`: `window.KC_API_BASE = '';` 줄과 주석(배포 때 Netlify 빌드가 채움) 추가.
- **핵심 로직**: 세션 토큰은 `sessionStorage`(탭 단위). 저장소 접근 실패(사파리 비공개 모드 등)면 메모리 변수로.
- **엣지 케이스**: `/session` 자체가 429 → `rate_limited` 오류로 끝(무한 재시도 금지). mock 모드는 세션·메타를 부르지 않는다. 로컬 backend(공개 모드 꺼짐)도 세션 헤더를 받아 세션별 기록을 쓴다 — 로컬 데모에서 새 탭은 새 대화가 된다(의도된 변화, 게이트에 적음).
- **지켜야 할 규칙**: D24 ① · D13 ⑨(`?base=` 는 같은 출처·루프백만 — 유지) · 프론트는 표 파일만.
- **DoD**: `node --test` 통과. 새 테스트: 토큰 저장·재사용, 401 한 번 재시도, 429 메시지, `configuredBase` 허용·거부 표(http 절대 URL 거부, `javascript:` 거부, 같은 출처 경로 허용), 승인 버튼 닫힘, mock 모드 무변화.
- **병렬 충돌**: 없음.

#### T411 — 채팅 세션 분리·동시 처리·일일 상한
- **변경 파일**: `backend/chat.py`, `backend/routers/messages.py`, `tests/backend/test_kc4_chat_sessions.py`(신규).
- **인터페이스**:
  - `ChatService.__init__(settings, *, ..., budget: DailyBudget | None = None, story_concurrency: int = 2)`. `_story_lock` → `self._story_slots = threading.BoundedSemaphore(story_concurrency)`.
  - `ChatService.messages(session: Session) -> list[dict]`, `ChatService.send(text, context, *, session: Session) -> ChatResult`. 기존 인스턴스 `_history`·`_seq` 제거(세션으로 이동). 메시지 id 는 세션의 `seq` 로 `msg_001…`.
  - 새 예외 `DailyLimit(Exception)`. 라우터가 503 `daily_limit` 으로.
  - 요청별 audit 수집: 모듈 `ContextVar[list[AuditEvent] | None]` `_REQ_EVENTS`; `_TeeSink.write` 가 공유 JSONL 에 쓰고 현재 컨텍스트 목록이 있으면 거기에도 append. `send` 시작에서 `token = _REQ_EVENTS.set([])`, 끝에서 `reset`. `logs = entries_from_events(collected, run_id=...)`. `mark()/since()` 는 지운다(요청 간 섞임 제거). `asyncio.to_thread` 는 컨텍스트를 복사하므로 스레드 안 audit 도 잡힌다.
  - `_search_events(args, timeout_s)` — 한도를 인자로 받는다(`self._search_timeout_s` 제거).
  - `messages.py`: `_session(request) -> Session | None` — 헤더 → `store.get`; 로컬 모드이고 None 이면 `store.local()`. `GET /api/messages`: 세션 없으면 `[]`. `POST /api/messages`: 공개 모드에서 세션 없으면 401 `no_session`. 세션 `busy.acquire(blocking=False)` 실패 → 429 `busy`. 응답 끝나면 세션의 `logs` 에 이번 `logs` 를 넣는다(최대 200).
- **핵심 로직**:
  1) `send` 순서: 주입·경로 검사(LLM 없음, 예산 소모 없음) → 일정 게이트면 `_story`: 예산 `reserve(2)` 실패 → `DailyLimit`; 슬롯 `acquire(blocking=False)` 실패 → `refund(2)` 후 `ChatBusy`. 파이프라인 끝나면 묶음 `schedule.attempts`(정수, 없으면 2)로 `refund(2 - min(attempts, 2))`. `StoryRunnerError` 면 환불 없음(시도했을 수 있음). 일반 챗봇으로 넘어가면 그때 `reserve(1)`.
  2) 일반 챗봇: `reserve(1)` 실패 → `DailyLimit`. `client.busy` 이면 `refund(1)` 후 `ChatBusy`.
  3) LLM 맥락(`_context`)은 **그 세션의 history** 에서만.
  4) `budget is None`(로컬 모드 기본) 이면 예산 검사 생략.
- **엣지 케이스**: 같은 세션 동시 2요청 → 두 번째 429 `busy`(첫 요청 영향 없음). 다른 세션 3개 동시 일정 → 2개 처리, 1개 429. 예산이 정확히 1 남았을 때 일정 문장 → 503(부분 예약 금지). 세션이 처리 중 TTL 만료 → 처리 중엔 `busy` 로 LRU 제거 대상에서 빠지므로 끝까지 진행, 기록은 그 세션 객체에 남음. 캐시 적중(`attempts` 0) → 2 환불.
- **지켜야 할 규칙**: D24 ①②③ · D15 ⑤(실패 문구·폴백 조건 그대로) · D17(묶음 서버 보관 안 함 — 세션에 묶음을 넣지 않는다) · D3·D10.
- **DoD**: `test_kc4_chat_sessions.py`: 세션 A 의 메시지가 세션 B 의 `GET` 에 안 보임, A 의 LLM 맥락에 B 문장 없음, 동시 요청 로그 비섞임(가짜 transport 2개를 `asyncio.gather`), 슬롯 2개·세션당 1개, 예산 예약·환불(캐시 적중·실패·폴백), 로컬 모드 헤더 없이 기존 동작. 기존 `tests/backend/test_kc3_chat_*`·E2E(`tests/test_kc3_e2e_chat.py`) 통과(시그니처 변경에 맞춘 호출부 수정은 허용하되 기대값 변경 금지). `uv run python eval/kc.py run --check --known-failures eval/BASELINE.md` 0.
- **병렬 충돌**: 없음(T412 와 파일 다름).

#### T412 — 공개 모드 보안 로그·승인·관리자·제보
- **변경 파일**: `backend/routers/review.py`, `backend/routers/events.py`, `tests/backend/test_kc4_public_mode.py`(신규).
- **인터페이스**:
  - `review.py::get_audit`: 공개 모드면 `session = store.get(header)`; 없으면 `[]`; 있으면 `list(session.logs)` 를 `at` 오름차순(지금 정렬 규칙과 같음)으로. 로컬 모드는 지금 그대로(파일 전체).
  - `review.py::decide`: 공개 모드면 403 `disabled_in_public`.
  - `events.py::require_admin`: 공개 모드면 `Forbidden("disabled_in_public")` → 403 코드 `disabled_in_public`(앱 예외 처리기의 코드를 메시지에 따라 고르도록 `Forbidden` 에 `code` 속성 추가 — `app.py` 는 T409 소유이므로 **`Forbidden.code` 를 읽는 처리기 수정은 T409 에 포함**한다: T409 명세에 "`_forbidden` 처리기가 `getattr(exc, 'code', 'forbidden')` 을 쓴다" 를 넣는다). 로컬 모드: 토큰 비교 전에 `admin_guard.blocked(ip)` 이면 403, 실패면 `fail(ip)`, 성공이면 `ok(ip)`.
  - `events.py::submit_report`: 공개 모드면 403 `disabled_in_public`.
- **핵심 로직**: 공개 여부는 `request.app.state.settings.public_mode` 한 곳에서만 읽는다.
- **엣지 케이스**: 공개 모드인데 관리자 토큰을 맞게 보내도 403(D24 ⑤). 로컬 모드 관리자 실패 5회 → 15분 403, 성공하면 카운터 초기화. 공개 모드 `GET /api/audit` 에 `X-Audit-Skipped` 헤더 없음.
- **지켜야 할 규칙**: D24 ⑤ · D2(신원은 서버 주입 — 그대로) · D13 ⑧.
- **DoD**: `test_kc4_public_mode.py`: 공개 모드 audit 세션 분리(세션 A 의 차단 기록이 B 에 안 보임), decision·admin·reports 403, 로컬 모드 기존 동작, 관리자 차단 15분(가짜 시계). 기존 `tests/backend/*` 통과.
- **병렬 충돌**: 없음.

> T409 명세 보충: `app.py` 의 `_forbidden` 처리기는 `_error(403, getattr(exc, "code", "forbidden"), str(exc))` 로 바꾼다(T412 가 쓰는 `Forbidden.code`). `Forbidden` 클래스 정의는 `events.py` 에 그대로 두고 `code` 속성 추가는 T412 가 한다 — T409 는 `getattr` 이라 T412 머지 전후 모두 동작.

#### T413 — 공개 모드 통합 테스트·로컬 공개 모드 실행
- **변경 파일**: `tests/test_kc4_public_e2e.py`(신규), `scripts/kc_demo.sh`(`--public` 옵션).
- **인터페이스**: `bash scripts/kc_demo.sh --public` = `KC_PUBLIC_MODE=1 KC_LLM_DAILY_UNITS=${KC_LLM_DAILY_UNITS:-20}` 로 backend 기동(나머지 동일). `--smoke` 와 조합 가능(`--public --smoke`).
- **핵심 로직(테스트)**: 실제 앱(`create_app(Settings(..., public_mode=True))`)·가짜 LLM transport·가짜 파이프라인 러너(`run_story` monkeypatch)로 ① 세션 발급 → 메시지 → 다른 세션에서 안 보임 ② `messages` 제한 6번째 429 + `Retry-After` ③ 일일 상한 0 이면 503 ④ 관리자·승인·제보 403 ⑤ CORS preflight 에 `X-KC-Session` 허용 ⑥ `GET /api/meta` 값.
- **엣지 케이스**: `kc_demo.sh` 의 기존 옵션 파싱이 단일 인자라 `--public --smoke` 를 받도록 고친다(순서 무관). 기존 옵션 동작 변화 없음.
- **지켜야 할 규칙**: D24 · 규칙 1(스크립트가 키를 출력하지 않음 — 기존 `key_state` 그대로).
- **DoD**: `uv run python -m pytest -q tests/test_kc4_public_e2e.py` 통과, `bash scripts/kc_demo.sh --check`·`--smoke`·`--public --smoke` 종료 코드 0, 전체 회귀.
- **병렬 충돌**: 단독.

#### T414 — 지역 파일 21개 + 25개 구 검사
- **변경 파일**: `domains/kcontext/data/regions/*.json` 신규 21개, `tests/domains/kcontext/test_kc4_regions25.py`(신규).
- **인터페이스**: 파일 이름 = id(소문자 영문, `_ID_RE` 통과). 각 파일 `{"id","name":{"ko","en"},"gu":["<구 이름>"],"bbox":null,"center":null,"keywords":["<구 이름>"],"sillok_keywords":[],"note":"..."}`.
- **핵심 로직**: 1) **서울시 공식 자치구 목록 페이지**(서울시 누리집 — URL 은 dev 가 찾아 `note` 에 적음)에서 25개 구의 한글 이름과 영문 표기를 옮긴다. 기존 4개(`jung`·`jongno`·`mapo`·`gangnam`)는 건드리지 않는다. 2) id 는 영문 표기에서 `-gu` 를 뗀 소문자(예: 영문 표기가 "Seocho-gu" 면 `seocho`) — 하이픈·공백은 `_`. 3) `keywords` 는 구 이름 하나만(사실 추가 없음). `sillok_keywords` 는 빈 목록(H3 → T418). 4) `note` 에 "출처: <URL> (확인일). bbox·center·sillok_keywords 는 [확인 필요]".
- **엣지 케이스**: 공식 페이지에 영문 표기가 없으면 `name.en` 에 한글 이름의 로마자 표기를 쓰지 말고 **같은 출처에서 확인한 값만** — 없으면 사람에게 묻고(H3 에 합침) 그 사이 `"name.en": "<한글 이름> [확인 필요]"`(로더는 비어 있지 않은 문자열만 요구). `_region_field` 규칙상 새 구는 색인 매칭이 없다 — 테스트로 이 사실을 고정하고 문서화(T418·T428).
- **지켜야 할 규칙**: 지역은 데이터 파일에만 · 사실 지어내지 않기(§0.2).
- **DoD**: `load_regions()` 가 25개를 읽고 id 중복 없음, 25개의 `gu` 합집합이 25개 서로 다른 이름, 기존 4개 파일 바이트 변경 없음(git diff 0). `uv run python -m pytest -q tests/domains/kcontext/test_kc4_regions25.py` + 전체 회귀(지역 개수를 4로 가정한 기존 테스트가 깨지면 **그 테스트가 실제 데이터 폴더에 의존하는지** 확인하고, 의존한다면 fixture 폴더로 바꾸는 수정만 허용 — 기대 개수만 바꾸지 않는다).
- **병렬 충돌**: 없음.

#### T415 — 실록 키워드 측정 도구
- **변경 파일**: `domains/kcontext/ingest/sillok_keywords.py`(신규), `tests/domains/kcontext/ingest/test_kc4_sillok_keywords.py`(신규).
- **인터페이스**:
  - `python -m domains.kcontext.ingest.sillok_keywords count --src <XML 폴더> --candidates <json> [--out <json>]` — candidates 형식 `{"<region_id>": ["<한자 지명>", ...]}`. 출력 `{"<region_id>": {"<kw>": {"title": n, "body": n, "articles": n}}, "_meta": {"files","articles","skipped_files"}}`.
  - `... places --src <XML 폴더> [--top 500]` — 기사 `<index type="지명">` 태그 빈도 상위 N(태그 문자열과 기사 수만. 지역 매핑 없음).
  - 함수: `count_keywords(src: Path, candidates: Mapping[str, Sequence[str]]) -> dict`, `top_place_tags(src: Path, top: int) -> list[tuple[str, int]]`.
- **핵심 로직**: `ingest.sillok.parse_file`(D14 검사 포함)을 재사용해 기사 단위로 NFKC 정규화 후 부분 문자열 포함 여부를 센다(같은 기사 안 중복은 1). 색인에 쓰지 않는다(읽기만).
- **엣지 케이스**: D14 검사에서 거른 파일은 `_meta.skipped_files` 에 이유와 함께. 빈 후보 목록 지역은 `{}`. 후보에 한자가 아닌 문자열이 있어도 그대로 센다(판단은 사람).
- **지켜야 할 규칙**: D14(파서 재사용) · D28 ②(측정만, 키워드 선택은 사람) · D7(호스트 실행).
- **DoD**: 합성 XML 3개(fixture, `○○` 지명)로 건수·중복·skipped 검증. `ruff` 통과. 실제 원본으로 `places --top 50` 을 1회 돌려 실행 시간을 테스트 밖 메모(T418 문서)로 넘긴다.
- **병렬 충돌**: 없음.

#### T416 — 카탈로그 25개 구: 전체 별칭·서울 API 쪽 상한·병합 블로킹
- **변경 파일**: `domains/kcontext/catalog/target.py`, `catalog/seoul.py`, `catalog/merge.py`, `.env.example`, `scripts/kc_demo.sh`, 테스트 2개(신규).
- **인터페이스**:
  - `target.py`: spec 이 정확히 `"all"` 이면 `load_regions()` 의 모든 id 로 해석(합친 Region id 는 지금 규칙대로 정렬한 id 를 `+` 로 이음). `ALL = "all"` export.
  - `seoul.py::fetch_rows(..., max_pages: int = 60)` — 첫 쪽 `list_total_count` 를 보고 `ceil(total/page_size) > max_pages` 이면 `SeoulApiError("행 수가 쪽 상한을 넘는다 (total=…, max_pages=…)")` 로 **수집 실패**(D13 ⑤: 기존 데이터 유지). 지금처럼 조용히 잘리지 않는다.
  - `merge.py::_group`: 결과가 같은 블로킹 — 관찰값마다 블록 키 집합 = {외부 id 들} ∪ {"day:"+각 날짜(최대 400일, 넘으면 "nodays")}. 비교 후보는 키를 하나라도 공유하는 기존 그룹만. `same_event` 는 날짜 교집합이 없으면 외부 id 공유 외에는 False 이므로 결과가 같다(외부 id 키로 그 경우를 덮음). 그룹 순회 순서는 원래처럼 생성 순.
- **핵심 로직**: 블로킹 전후 결과가 같아야 한다 — 테스트로 무작위 합성 관찰값 300개(시드 고정)를 두 구현(옛 `_group` 을 테스트 안에 복사해 기준으로)에 넣어 그룹 구성이 같은지 비교.
- **엣지 케이스**: 날짜 없는 관찰값(검색 수집 7건처럼) → `nodays` 키끼리만 비교(외부 id 공유는 별도 키로 잡힘). 기간이 400일 넘는 상설 행사 → `nodays` 와 같은 버킷 + 외부 id 키. `"all"` 과 다른 id 를 섞은 spec(`"all,jung"`) → ValueError.
- **지켜야 할 규칙**: D13 ③(묶기 규칙 불변) · D13 ⑤(실패는 기존 유지) · 지역은 데이터에서.
- **DoD**: `test_kc4_target_all.py`, `test_kc4_merge_blocking.py`(동등성 + 300개 처리 시간이 옛 구현보다 짧음을 기록만, 단언은 동등성). `.env.example` 의 `KC_TARGET_REGION=all` 과 설명, `kc_demo.sh` 의 `REGIONS="all"`. `kc_demo.sh --check`·`--smoke` 0. 전체 회귀.
- **병렬 충돌**: 없음.

#### T417 — 좌표 자동 부착(서울 API 장소)
- **변경 파일**: `domains/kcontext/places.py`, `domains/kcontext/places_build.py`(신규), `domains/kcontext/data/places/auto_rules.json`(신규), `domains/kcontext/pipeline/run.py`(`_attach_coords` 만), `frontend/k-context/src/lib/chat-bundle.js`(`PROBLEM_KEYS`·`NAMED`·`problemName`), `src/i18n/ko.js`·`en.js`, 테스트 2개(신규).
- **인터페이스**:
  - `places.py`: `Place` 에 `auto: bool = False` 추가. `auto_path() -> Path` = env `KC_AUTO_PLACES`(있으면) 또는 `<var>/places/auto_places.json`(`domains.kcontext.paths` 의 var 경로 규칙). `load_places(path=None, *, auto: Path | None | Literal["default"] = "default") -> PlaceBook` — 사람 사전을 먼저 읽고, 자동 파일이 있으면 읽어 **사람 사전의 이름·별칭과 겹치는 자동 항목은 버린다**. 자동 파일 형식은 사람 사전과 같은 필드 + `"auto": true`. 자동 파일이 없거나 깨지면 사람 사전만(자동 파일 오류는 예외가 아니라 경고 1줄 — 데모를 막지 않는다).
  - `places_build.py`: `python -m domains.kcontext.places_build --catalog var/catalog --rules domains/kcontext/data/places/auto_rules.json --out var/places/auto_places.json --collected-at YYYY-MM-DD` → 출력 요약 `{"names_seen","accepted","ambiguous","out_of_range","shadowed_by_manual"}`. 함수 `build_from_observations(observations, rules, manual: PlaceBook, collected_at) -> tuple[list[dict], dict]`.
  - `auto_rules.json`: `{"seoul_bbox": null, "max_spread_m": 150, "min_rows": 1, "note": "seoul_bbox 는 [south, west, north, east] — 사람이 출처와 함께 채운다 [확인 필요]"}`. `seoul_bbox` 가 null 이면 범위 검사를 건너뛰지 않고 **빌더가 실패**(종료 코드 2) — 범위 확인 없이 자동 좌표를 만들지 않는다. (H: T418 착수 전에 사람이 채움 — §3.1 H3 와 함께 요청)
  - `run.py::_attach_coords`: `place.auto` 이면 `problems.append(_problem("COORD_AUTO", f"{name}: 공공 데이터 좌표(사람 확인 전)"))`.
  - 프론트: `PROBLEM_KEYS.COORD_AUTO = 'bundle.problem.coord_auto'`, `NAMED` 에 추가, `problemName` 은 `COORD_AUTO` 를 `COORD_UNKNOWN` 과 같은 "이름: …" 규칙으로. i18n `bundle.problem.coord_auto`(+`.named`) 문구 "공공 데이터 좌표를 썼어요(사람 확인 전)" / "Used public-data coordinates (not yet human-checked)".
- **핵심 로직(빌더)**: 1) `CatalogStore(dir).load_observations()` 에서 `source_id == "seoul_openapi"` 이고 장소명·위경도가 있는 관찰값만. 2) 장소명 `norm()`(places.py 의 것)으로 묶는다. 3) 좌표 중앙값(위도·경도 각각) → 모든 점이 중앙값에서 `max_spread_m` 안이면 채택, 아니면 `ambiguous`. 4) `seoul_bbox` 밖이면 `out_of_range`. 5) 사람 사전에 있으면 `shadowed_by_manual`. 6) 항목 `{"name": <원래 장소명 중 가장 많이 나온 표기>, "aliases": [], "lat","lng", "source": "서울 열린데이터광장 문화행사 장소 좌표 (행 n건)", "verified_at": collected_at, "note": "자동 생성(D25)", "auto": true}`. 7) 출력은 이름순 정렬(재현성).
- **엣지 케이스**: 정규화 후 같은 이름이 서로 다른 표기로 나오면 가장 흔한 표기(동률이면 사전순). 이름이 200자 초과 → 제외. 자동 항목끼리 별칭 충돌 없음(별칭 없음). 사람 사전과 이름은 다른데 좌표가 같은 경우는 그대로 둔다.
- **지켜야 할 규칙**: D25 ①~⑦ · D19 취지(공공누리 출처 표시 — `source` 에) · 자동 파일은 `var/`(커밋 안 함) · 게이트 사본(`backend/fixtures/chat_places.json`)은 건드리지 않는다.
- **DoD**: `test_kc4_places_auto.py`(중앙값·모호·범위·사람 우선·bbox null 이면 실패·자동 파일 깨짐 경고·`COORD_AUTO` 코드), `coordauto.kc4.test.js`(문구·이름 붙이기·모르는 이름은 안 붙임). 전체 회귀(자동 파일이 없는 기본 상태에서 기존 결과 불변).
- **병렬 충돌**: 없음.

#### T418 — 실행: 서울 25개 구 수집·색인·자동 좌표·스냅샷·측정
- **수행자**: 코디네이터(실호출·대용량 실행). dev 는 명령·문서 틀을 준비.
- **변경 파일**: `data/regions/*.json` 의 `sillok_keywords`(H3 가 준 값만, 출처를 `note` 에), `data/places/auto_rules.json` 의 `seoul_bbox`(사람 값), `data/snapshots/catalog/*`(재생성), `data/catalog_sources.json`(`seoul_openapi` 의 verified_at·notes), `docs/status/seoul25_2026-10-xx.md`(신규), `docs/spikes/sillok.md`(25개 구 절 추가).
- **순서**:
  1) H3 후보로 `sillok_keywords count` 실행 → 건수표를 사람에게 → 노이즈 제외 확정 → 지역 파일에 반영(사람 확인 기록).
  2) 색인 재구축: `uv run python -m domains.kcontext.ingest.sillok --src <실록 XML> --db var/index/kcontext.new.db --collected-at <오늘> --mode regions` → `index stats` → 크기가 D28 ④ 상한 안이면 기존 파일을 `kcontext.4gu.db` 로 옮기고 교체. 넘으면 교체하지 않고 사람에게 보고.
  3) 서울 API: `KC_TARGET_REGION=all uv run python -m domains.kcontext.catalog --region all update --source seoul_openapi` (임시 폴더 `var/catalog.new` → 검증 후 교체). 이어서 `catalog reindex`(T407).
  4) 자동 좌표: `places_build` 실행.
  5) 스냅샷: `scripts/snapshot_catalog.py`(D19 — 서울 API 유래만).
  6) 측정: `measure_runtime.py`(T408) 재실행, 데모 문장 + 새 구 문장 2개(합성 일정, 실제 장소 이름) 로 실제 서버 1회씩.
- **엣지 케이스**: H3 가 없으면 1)·2) 를 건너뛰고 문서에 "색인 = 4개 구 키워드, 새 21개 구는 실록 색인 대상 아님"을 쓴다. 서울 API 쪽 상한 초과(T416) → `--max-pages` 를 T408 측정값 기준으로 올려 재실행(상한 §6). 병합 시간이 길면 시간을 기록.
- **지켜야 할 규칙**: D28 · D19 · D7 · §6 호출 상한 · 규칙 1.
- **DoD**: 문서에 구별 행사 수·검색 시간·색인 크기·자동 좌표 수·스냅샷 수·실서버 3문장 결과(앵커·좌표 출처·언급 수·행사 수)가 있다. 회귀(§7) + `kc_demo.sh --check` 0. 스냅샷 크기가 기존 836KB 대비 기록되고 5MB 를 넘으면 사람에게 확인(저장소 크기).
- **병렬 충돌**: 단독.

#### T419 — TourAPI 수집기·정규화
- **선행 조건**: T401 문서에 "확정 필드 목록"이 있어야 한다. 그 목록 밖의 필드·오퍼레이션 이름은 쓰지 않는다.
- **변경 파일**: `domains/kcontext/catalog/tourapi.py`(신규), `catalog/sources.py`(fetcher 등록), `data/catalog_sources.json`(`tourapi_kto` 의 `status: "implemented_unverified"`·notes), `data/tourapi_codes.json`(신규 — T401 ⑦ 의 서울 코드 표, 출처·확인일), `tests/domains/kcontext/catalog/test_kc4_tourapi.py`, `tests/fixtures/tourapi/*.json`(합성 — T401 이 기록한 응답 **구조**대로, 값은 `○○`·`예시`).
- **인터페이스**:
  ```python
  KEY_ENV = "DATA_GO_KR_SERVICE_KEY"
  BASE = "https://apis.data.go.kr/B551011/KorService2"  # T401 확인값으로 확정
  SOURCE_ID = "tourapi_kto"
  class TourApiError(RuntimeError): ...
  def fetch_festivals(key: str, *, start_date: str, client: httpx.Client | None = None,
                      max_calls: int = 200, page_size: int = <T401 최대값>) -> tuple[list[dict], dict]
  def fetch_attractions(key: str, *, client=None, max_calls: int = 200) -> tuple[list[dict], dict]
  def observation_from_item(item: Mapping, region: Region, *, collected_at: str) -> Observation | None
  def observations_from_items(items, region, *, collected_at) -> tuple[list[Observation], list[str]]
  ```
  두 번째 반환값은 `{"calls": n, "total": n, "truncated": bool}`.
- **핵심 로직**: 1) 쿼리 파라미터 이름·값은 T401 표대로(서울 지역 코드는 `tourapi_codes.json` 에서). 2) 쪽 단위 호출, `max_calls` 를 넘으면 멈추고 `truncated=True`(**수집 실패로 처리**하지 않고 runs 에 남김 — 다만 일부만 받은 결과로 기존 관찰값을 지우지 않는다, D13 ⑤ 는 updater 가 이미 지킴). 3) 관찰값: `external_ids=("kto:<콘텐츠 id>",)`, evidence kind `official_api`, 이름 `한국관광공사 TourAPI`, 등급은 서울 API 와 같은 규칙. 시군구 코드 → 구 이름은 `tourapi_codes.json` 으로만, 표에 없으면 구 미확인. 좌표 필드는 T401 이 확인한 이름·축 순서대로 `Venue.lat/lng`. 예약·언어·참여조건은 출처가 명시한 필드가 T401 에 확인된 경우만, 아니면 unknown(D13 ①). 4) 오류 메시지에 URL·키 금지(`TourApiError(f"TourAPI HTTP {status}")` 형식). 5) `catalog_runner._SOURCE_KEYS` 는 이미 이 키 이름을 가짐 — 변경 없음.
- **엣지 케이스**: 응답이 JSON 이 아니면(XML 오류 응답) 오류 코드만 추출해 `TourApiError`. 결과 0건 → 정상(빈 목록). 같은 콘텐츠 id 중복 → 하나로. 날짜 형식이 T401 기록과 다르면 그 항목 버리고 problem.
- **지켜야 할 규칙**: D26 ①⑥ · D13 ①②⑤ · D7(호스트 수집기, 런타임 호출 없음) · 규칙 1 · §6.1 TourAPI 상한.
- **DoD**: `test_kc4_tourapi.py`(httpx `MockTransport` 로 쪽 넘김·`max_calls`·오류 응답·URL 미노출·관찰값 변환·코드표 밖 구). `catalog update --source tourapi_kto` 가 키 없으면 runs 에 "키 없음"으로 남고 종료 코드 0(지금 서울 API 와 같은 방식인지 확인). 전체 회귀.
- **병렬 충돌**: 없음(T421 은 merge.py).

#### T421 — 병합 규칙 D26 반영
- **변경 파일**: `domains/kcontext/catalog/merge.py`, `tests/domains/kcontext/catalog/test_kc4_merge_kto.py`(신규).
- **인터페이스**: 독립 출처 계산이 있다면(entries 의 `independent_sources` 류 필드 — dev 가 위치 확인) `kto:` 와 `seoul_cult:` 를 함께 가진 그룹은 독립 출처 1로 센다(D26 ③). `same_event` 로직 자체는 바꾸지 않는다(D26 ②).
- **핵심 로직**: 합성 관찰값으로 ① `kto:A` + `seoul_cult:B`, 같은 장소·기간·제목 유사 → 한 항목 ② 같은 `kto:` 체계 다른 값 → 두 항목 ③ 기간 불일치 → 두 항목 ④ 같은 필드 값 충돌 → `conflict`·값 비움.
- **엣지 케이스**: 독립 출처 수 필드가 없으면 코드 변경 없이 테스트만 추가하고 문서에 "독립 출처 계산 없음 — D26 ③ 은 현재 코드에서 자동 충족"으로 기록.
- **지켜야 할 규칙**: D26 · D13 ③④.
- **DoD**: 테스트 4케이스 + 전체 회귀.
- **병렬 충돌**: 없음.

#### T420 — TourAPI 관광지 → 좌표 사전
- **변경 파일**: `domains/kcontext/places_build.py`(입력 어댑터), `domains/kcontext/catalog/tourapi.py`(`export_attractions(items) -> list[dict]` 만 추가), `tests/domains/kcontext/test_kc4_places_tourapi.py`(신규).
- **인터페이스**: `places_build ... --tourapi-attractions var/data/tourapi/attractions.jsonl`(선택 인자). JSONL 한 줄 = `{"name","lat","lng","content_id","collected_at"}`(원응답 아님 — `export_attractions` 가 만든 정규화 줄). `tourapi.py` CLI 하위 명령 `attractions --out <jsonl>`(호출은 `fetch_attractions`, 상한 §6).
- **핵심 로직**: 서울 API 장소와 같은 규칙(중앙값·150m·bbox·사람 우선). 같은 이름이 두 출처에 있고 150m 안이면 하나로(`source` 에 두 출처 모두), 150m 밖이면 모호로 버림. `source` 문자열 "한국관광공사 TourAPI 관광지 좌표".
- **엣지 케이스**: 관광지 이름이 행사 장소명보다 길게 붙는 경우(예 "○○궁 (○○)")는 별칭을 만들지 않는다 — 이름 그대로만(추측 금지).
- **지켜야 할 규칙**: D25 ①② · D26 ⑤.
- **DoD**: 테스트(두 출처 병합·충돌·사람 우선) + 전체 회귀.
- **병렬 충돌**: 단독(4b).

#### T422 — TourAPI 실수집·보고
- **수행자**: 코디네이터. **조건**: H2(키) 있음. 없으면 "실행 대기 — H2" 로 기록하고 Stage 5 로 간다.
- **변경 파일**: `docs/status/events_data_2026-10-xx.md`(신규), `catalog_sources.json`(`tourapi_kto` status·verified_at·notes).
- **순서**: ① 행사 수집(`catalog --region all update --source tourapi_kto`) ② 관광지 내보내기(`tourapi attractions`) ③ `places_build` 재실행 ④ `catalog reindex` ⑤ 보고서: 출처별·구별 수, 병합으로 합쳐진 수(`kto:`+`seoul_cult:` 동시 보유 항목 수), conflict 수와 표본 5건, 무작위 5건 링크 확인(사람), 자동 좌표 증가 수, 실서버 데모 문장 1회.
- **엣지 케이스**: 개발 계정 일일 한도에 닿으면 멈추고 다음 날 재개(§6). `truncated` 면 보고서에 명시.
- **지켜야 할 규칙**: §6 · D26 · D19(스냅샷에 TourAPI 유래를 넣을지는 이용 조건 확인 뒤 — 이번에는 넣지 않는다).
- **DoD**: 보고서 + 회귀 + `kc_demo.sh --check` 0.
- **병렬 충돌**: 단독.

#### T423 — Dockerfile·컨테이너 설정
- **변경 파일**: `Dockerfile`(신규), `.dockerignore`, `deploy/cloudrun/entrypoint.sh`(신규), `deploy/cloudrun/README.md`(신규), `scripts/build_image_data.sh`(신규), `tests/test_kc4_container_files.py`(신규).
- **인터페이스**:
  - 이미지: 파이썬 3.12 slim 계열 공식 이미지(태그는 고정), `uv` 로 `uv sync --frozen --no-dev`, 비루트 사용자, 작업 폴더 `/app`. 복사 대상은 `core/ backend/ domains/ deploy/llm.chat.yaml pyproject.toml uv.lock` + **이미지 데이터 폴더** `image-data/`(아래) → `/app/var/`.
  - `scripts/build_image_data.sh` — 호스트에서 실행. `var/index/kcontext.db`·`var/catalog/{entries,observations,runs,search_index}.json`·`var/places/auto_places.json` 을 `image-data/` 로 복사(존재·크기 검사, 합계 출력). `image-data/` 는 `.gitignore` 에 추가(→ `.gitignore` 도 변경 파일에 넣는다).
  - `entrypoint.sh`: `KC_PUBLIC_MODE=${KC_PUBLIC_MODE:-1}`, `KC_HITL_DB=/tmp/kc/hitl.db`, `KC_AUDIT_DIR=/tmp/kc/audit`, `KC_SCHEDULE_CACHE` 경로·`KC_VAR_DIR` 를 `/tmp/kc` 아래로(읽기 전용 데이터는 `/app/var`, 쓰기는 `/tmp/kc`) — 필요한 env 이름은 dev 가 코드에서 확인해 목록화. `exec uvicorn backend.app:app --host 0.0.0.0 --port "${PORT:-8080}" --workers 1`.
  - `.dockerignore`: 지금 항목 + `var/` 전체(이미지 데이터는 `image-data/` 로만 들어감) + `docs/` + `frontend/` + `eval/` + `tests/` + `test_condition/` + `domains/kcontext/data/raw/` + `*.db` (단 `image-data/**` 예외).
- **핵심 로직**: 비밀 0 — 빌드 인자·ENV 에 키 없음. 색인·카탈로그는 읽기 전용, 쓰기 경로는 `/tmp/kc`.
- **엣지 케이스**: 카탈로그 쓰기(제보 등)는 공개 모드에서 닫힘(D24 ⑤)이지만 `CatalogStore.lock()` 이 잠금 파일을 데이터 폴더에 만든다면 읽기 전용 폴더에서 실패 — dev 가 확인하고, 그렇다면 `KC_CATALOG_DIR` 를 `/tmp/kc/catalog` 로 두고 entrypoint 가 시작할 때 `/app/var/catalog` 를 복사(용량을 README 에 기록). 일정 캐시가 `/tmp` 메모리를 먹는 문제 — 일일 상한(D24)이 상한 역할, README 에 적음.
- **지켜야 할 규칙**: 규칙 1(이미지·빌드 컨텍스트에 비밀 없음) · D27 ③④⑤⑥ · 새 런타임 의존성 없음.
- **DoD**: `test_kc4_container_files.py` — `.dockerignore` 에 `.env`·`var/`·`.git` 이 있고 `image-data` 예외가 있음, Dockerfile 에 `ENV .*KEY`·`ARG .*KEY` 없음, entrypoint 가 `--workers 1`·`KC_PUBLIC_MODE`. docker 가 있으면 `docker build` + `docker run -e NVIDIA_API_KEY` 없이 `/api/meta` 200, `/api/messages` 일정 문장 → 503 `llm_unavailable` 또는 고정 문구(키 없음) 확인 기록, 이미지 크기 기록. docker 가 없으면 "실행 대기 — docker" 로 기록하고 T426 에서 Cloud Build 로 확인.
- **병렬 충돌**: 없음.

#### T424 — Netlify 설정·빌드 스크립트
- **변경 파일**: `netlify.toml`(신규), `scripts/netlify_build.sh`(신규), `tests/test_kc4_netlify_build.py`(신규).
- **인터페이스**:
  - `netlify.toml`: `[build] command = "bash scripts/netlify_build.sh"`, `publish = "dist"`. T403 결론이 **프록시**면 `[[redirects]] from="/api/*" to="<Cloud Run URL>/api/:splat" status=200 force=true` — URL 은 빌드 env `KC_BACKEND_ORIGIN` 으로 스크립트가 `dist/_redirects` 에 쓴다(저장소에 URL 을 박지 않는다). 직접 CORS 면 리다이렉트 없음.
  - `scripts/netlify_build.sh`: ① `frontend/k-context` → `dist/` 복사(`tests/`·`admin.html`·`config.local.js`·`README.md` 제외) ② `dist/config.local.js` 생성: `window.KC_KAKAO_JS_KEY = '<KC_KAKAO_JS_KEY 또는 빈 값>'; window.KC_API_BASE = '<프록시면 /api, CORS 면 KC_BACKEND_ORIGIN + /api>';` — 값 검증(`KC_BACKEND_ORIGIN` 은 `^https://[A-Za-z0-9.-]+$`, 카카오 키는 `^[0-9a-f]{32}$` 형태만 허용 — 형식은 T404 확인값으로 확정, 아니면 빌드 실패) ③ 직접 CORS 면 `dist/events.html` 의 meta CSP `connect-src` 에 `KC_BACKEND_ORIGIN` 을 덧붙임(원본 파일은 안 고침) ④ `dist/_headers` 에 `index.html` 용 CSP(카카오 SDK 출처는 T404 확인값, `connect-src` 는 'self' + 직접 CORS 면 backend 원점) ⑤ 값을 로그에 출력하지 않음(길이만).
  - 모드 선택 env: `KC_API_MODE=proxy|cors`(필수, 없으면 빌드 실패).
- **엣지 케이스**: 키 없음 → 빈 값(SVG 폴백, D11). `KC_BACKEND_ORIGIN` 에 경로가 붙어 오면 실패. 로컬에서 같은 스크립트를 돌려 `dist/` 를 만들고 `python3 -m http.server --directory dist` 로 확인 가능해야 함.
- **지켜야 할 규칙**: 규칙 1(키를 저장소에 두지 않음 — 생성 파일은 `dist/`, `.gitignore` 에 `dist/` 추가 → `.gitignore` 변경은 T423 과 겹치므로 **T423 이 `image-data/`·`dist/` 둘 다 추가**한다) · D27 ① · D11.
- **DoD**: `test_kc4_netlify_build.py` — 임시 폴더에서 스크립트 실행(proxy·cors 두 모드, 가짜 값)해 `dist/` 구조, `admin.html` 없음, `config.local.js` 내용, CSP 에 origin 포함(cors), `_redirects`(proxy), 잘못된 값이면 종료 코드 ≠ 0, 출력에 값 문자열 없음. 원본 `frontend/k-context/*.html` 바이트 불변.
- **병렬 충돌**: 없음(`.gitignore` 는 T423 담당으로 정리).

#### T425 — Cloud Run 배포 스크립트·가이드
- **변경 파일**: `scripts/deploy_cloudrun.sh`(신규), `docs/guides/DEPLOY.md`(신규), `deploy/README.md`(표에 `cloudrun/`·`netlify.toml` 줄, 필수·선택 구분).
- **인터페이스**: `bash scripts/deploy_cloudrun.sh --project <id> --region <region> --service kcontext [--dry-run]` — ① `scripts/build_image_data.sh` ② 이미지 빌드·푸시(T402 결론: Cloud Build 또는 로컬 docker) ③ `gcloud run deploy` 에 T402 ⑫ 값(시간 한도·메모리·CPU·`--max-instances 1`·`--min-instances 0`·concurrency·`--allow-unauthenticated`), env(`KC_PUBLIC_MODE=1`, `KC_TRUSTED_PROXY_HOPS`(T402·T403 값), `KC_CORS_ORIGINS`(cors 모드), `KC_LLM_DAILY_UNITS`(H7), `KC_TARGET_REGION=all`), 시크릿 주입(`NVIDIA_API_KEY` ← Secret Manager, 플래그는 T402 확인값). `--dry-run` 은 실행할 명령만 출력(값 중 비밀 없음).
  - `DEPLOY.md`: 사람 선행(H4·H5·H6·H11) 체크리스트, 시크릿 등록 명령(값은 사람이 표준입력으로 — 셸 기록에 안 남게), 배포 순서(Cloud Run → URL 확인 → Netlify env `KC_BACKEND_ORIGIN`·`KC_API_MODE`·`KC_KAKAO_JS_KEY` → Netlify 배포 → 카카오 도메인), 비용 안전장치(예산 알림, max-instances 1, 일일 상한), 되돌리기(서비스 삭제·트래픽 0), 이미지 데이터 갱신 절차.
- **엣지 케이스**: `gcloud` 없음·로그인 안 됨 → 안내 후 종료 코드 2. 다른 프로젝트·서비스 이름과 충돌 방지 — 서비스 이름 인자 필수, 기존 서비스가 있으면 `--yes` 없이는 덮어쓰지 않음.
- **지켜야 할 규칙**: 규칙 1 · D27 · SCOPE "유료 인프라 금지"(최소 인스턴스 0 고정).
- **DoD**: `bash scripts/deploy_cloudrun.sh --project example --region example --service kcontext --dry-run` 이 계정 없이 명령 목록을 내고 0 으로 끝남(gcloud 미설치여도 dry-run 은 동작). `shellcheck` 이 있으면 경고 0(없으면 생략 기록). 문서 링크 확인.
- **병렬 충돌**: 없음.

#### T426 — Cloud Run 배포·공개 URL 남용 점검
- **수행자**: 코디네이터 + 사람(로그인·시크릿 값).
- **변경 파일**: `docs/status/deploy_2026-10-xx.md`(신규). 코드 변경 없음 — 발견한 문제는 "이월" 절.
- **순서**: ① H4·H11 확인 ② `deploy_cloudrun.sh` 실행 ③ 점검 표(모두 실제 URL 로): `/api/meta` 200·public true / 세션 2개로 대화 분리 / `messages` 6번째 429·`Retry-After` / `/api/admin/review` 403 / `POST /api/audit/x/decision` 403 / `POST /api/reports` 403 / 일정 데모 문장 1회 응답 시간·앵커·행사 수 / 콜드 스타트 시간 / 메모리 최대치(콘솔 지표) / 로그에 키·토큰 문자열 없음(검색) / `X-Forwarded-For` 로 읽힌 IP 가 실제 방문자 IP 인지(본인 IP 와 비교, 값은 문서에 적지 않음 — 일치 여부만).
- **엣지 케이스**: 일정 요청이 시간 한도에 걸리면 Cloud Run 시간 한도·프론트 100초 사슬을 문서에 적고 이월. 무료 사용량 지표가 예상보다 크면 즉시 `max-instances` 유지·트래픽 확인 후 사람에게 보고.
- **지켜야 할 규칙**: §6 · D24 · D27 · `maintq*` 등 다른 자원은 건드리지 않음(CLAUDE.md 로컬 환경 주의 취지).
- **DoD**: 점검 표 모든 행에 결과. 실패 행이 있으면 원인·조치(또는 이월). LLM 호출 총수 기록(≤ 10).
- **병렬 충돌**: 단독.

#### T427 — Netlify 배포·카카오 도메인·화면 확인
- **수행자**: 코디네이터 + 사람(H5·H6).
- **변경 파일**: T426 문서에 절 추가.
- **순서**: ① Netlify env 설정(`KC_API_MODE`·`KC_BACKEND_ORIGIN`·`KC_KAKAO_JS_KEY`) ② 배포 ③ 카카오 도메인 등록 확인 ④ 헤드리스 브라우저로 첫 화면(MOCK 0·"실제 서버")·데모 문장·지도(카카오 또는 SVG)·보안 로그(날짜·최신 우선, 승인 버튼 닫힘 문구)·행사 화면(`events.html`) 확인 ⑤ 프록시 모드면 일정 요청이 프록시 시간 한도 안에 끝나는지 실측 ⑥ CORS 모드면 다른 출처(임의 페이지)에서의 `fetch` 가 막히는지(`KC_CORS_ORIGINS`).
- **엣지 케이스**: 프록시 시간 한도에 걸리면 즉시 CORS 모드로 다시 빌드(T424 스크립트가 두 모드를 지원) — D27 ② 문안의 분기대로.
- **지켜야 할 규칙**: D27 · D11 · D17.
- **DoD**: 문서에 확인 항목별 결과와 공개 URL 2개(프론트·API). 사람 확인(H6) 기록.
- **병렬 충돌**: 단독(T426 뒤).

#### T428 — README·상태·가이드 갱신
- **변경 파일**: `README.md`, `docs/status/2026-10-xx_구현상태.md`(신규, 옛 문서 유지), `docs/guides/SETUP.md`·`EVENTS_CATALOG.md`, `docs/diagram/system-state.html`.
- **핵심 로직**: README 맨 위에 공개 URL·"공개 데모 제한(일일 상한·제한·승인 닫힘)" 안내, 지역 25개 구·실록 색인 대상 구 목록(H3 결과대로 — 대상 아님 구를 밝힘), 좌표 출처 두 종류(사람 확인·공공 데이터), TourAPI 상태(실행했으면 수치, 아니면 "실행 대기"), 외부 서비스 표에 Netlify·Cloud Run·Secret Manager·TourAPI 행, 보안 설계 절에 D24·D20 재검토 결론. 상태 문서는 Sprint 3 형식(✅·🔶·❌·⚠) 그대로, 측정 숫자는 T418·T422·T426 문서에서만 옮긴다(새로 지어내지 않음).
- **엣지 케이스**: 실행 대기 항목(H2 등)은 "실행 대기 — H번호"로.
- **지켜야 할 규칙**: 사실은 측정 문서 인용만 · D20/D24 표현 일치.
- **DoD**: 문서 내 상대 링크가 모두 존재하는 파일을 가리킴(간단 스크립트 또는 수동 목록). `kc_demo.sh --check` 0.
- **병렬 충돌**: 없음(T429 는 png 만).

#### T429 — 배포 URL 스크린샷
- **변경 파일**: `docs/demo/s4-0{1..5}-*.png`.
- **장면**: ① 첫 화면(실제 서버·여행 기간) ② 데모 문장 결과(타임라인·지도·행사) ③ 새 구 문장 결과(자동 좌표 문구 포함) ④ 보안 로그(날짜·승인 닫힘) ⑤ 제한 초과 안내(429 문구).
- **DoD**: 5장, 헤드리스 Chromium(Sprint 3 방식). 화면에 키·토큰 없음.
- **병렬 충돌**: 없음.

### 5.2 조건부 태스크 (SCOPE "선택")
| TASK | 제목 | 조건 | 착수 전 필요한 것 |
|---|---|---|---|
| T430 | 무료 DB(Postgres)로 승인·감사·캐시 보존 | Stage 7 이후 여유 + H9 | **새 결정(D29 후보)** + **런타임 의존성 예외 결정**(Postgres 드라이버가 필요 — §0.2 금지 규칙과 충돌. HTTP SQL API 가 있는 서비스면 `httpx` 로 가능한지 스파이크 먼저) |
| T431 | 서울 행사 하루 1회 자동 갱신(Cloud Scheduler + Cloud Run job) | T430 완료(갱신 결과를 둘 영속 저장소) | **새 결정** — D7 "호스트 수집기"의 범위를 Cloud Run job 으로 넓힐지, 서울 키를 job 에만 주입하는 방식, 무료 사용량 확인(T402 보충) |
| T432 | 구청 검색 수집 25개 구 확대 | 여유 + H10(도메인 승인) | D12 ①(사람이 승인한 도메인만) — `web_sources/<구>.json` 을 사람이 `status: confirmed` 로 채운 구만. Tavily 호출 §6 상한. 실측 수확이 낮아(7건, 날짜 없음) 우선순위 최하 |

조건이 안 되면 "S5 이월 — 사유: <조건>".

---

## 6. 비용·남용 방지 기준

### 6.1 외부 호출 상한 (개발·운영 공통)
| 대상 | 런타임(공개 서비스) | 이번 스프린트 개발·수집 | 근거·비고 |
|---|---|---|---|
| NVIDIA 추론 | **하루 300 단위**(`KC_LLM_DAILY_UNITS`, 1 단위 = LLM 호출 1회. 일정 흐름 최대 2, 일반 챗봇 1). 인스턴스 1개라 전역 상한 = 이 값. H7 확인 뒤 사람이 조정 | T408 ≤ 2 · T418 실서버 확인 ≤ 6 · T422 ≤ 2 · T426 ≤ 10 · T427 ≤ 6 · 회귀 측정(필요 시 `eval` 1회) ≤ 210. **합계 ≤ 240** | D15 의 일정 흐름 최대 2회. 크레딧 잔량 미확인(H7)이라 보수값 |
| 서울 열린데이터광장 | **0회**(키를 주입하지 않음, D27 ④) | T408 ≤ 60 · T418 ≤ 60(재시도 1회 포함 ≤ 120) · **하루 1회 수집 실행** | 1회 1000행. 전체 행 수는 T408 측정. 일일 한도는 문서 미기재 [확인 필요] |
| TourAPI | **0회** | T401 ≤ 20 · T422 행사 ≤ 200 · 관광지 ≤ 200 · **하루 합계 ≤ 500** | 개발 계정 하루 1,000건(`catalog_sources.json` 2026-10-07 메모, T401 재확인) — 절반 이하 |
| Tavily | 0회 | T432 를 할 때만, 구당 ≤ 3, 합계 ≤ 75 | D12 ⑥, 월 1,000 크레딧 |
| Cloud Run | `max-instances 1`·`min-instances 0`, 요청 시간 한도 T402 값 | 배포 횟수 제한 없음(무료 빌드 시간 안) | 무료 사용량 [T402] · 예산 알림(H4) |
| 카카오 지도 JS | 브라우저 호출(우리 서버 아님) | — | 무료 사용량 [T404] |

### 6.2 요청 제한 (공개 모드, `backend/limits.py::RULES`)
| 규칙 키 | 대상 | 키 | 한도 |
|---|---|---|---|
| `session_create` | `POST /api/session` | IP | 10회/시간 |
| `messages` | `POST /api/messages` | IP | 5회/분 · 40회/일 |
| `messages` | 〃 | 세션 | 30회/일 |
| `events` | `/api/events/*`(검색·카드·일정 추가·취소·변경) | IP | 20회/분 |
| `reports` | `POST /api/reports` | — | 공개 모드에서 닫힘(403) |
| `admin` | `/api/admin/*` | — | 공개 모드에서 닫힘(403). 로컬 모드: 토큰 실패 5회 → 15분 차단 |
| `read` | 그 밖의 `GET /api/*` | IP | 60회/분 |
| 동시 처리 | 일정 흐름 | 인스턴스 / 세션 | 2건 / 1건 |
| 본문 | 모든 요청 | — | 256KB(기존), 채팅 2,000자(기존) |

숫자는 근거 있는 추정이 아니라 **보수적 시작값**이다. T426 실측(응답 시간·메모리)으로 사람이 조정하고, 조정은 `limits.py` 의 표 한 곳만 바꾼다.

---

## 7. 스테이지 게이트 (모든 스테이지 공통 + 개별)

### 7.1 공통 — "로컬 데모 동작 유지"
| 확인 | 명령(레포 루트) | 기준 |
|---|---|---|
| pytest | `uv run python -m pytest -q` | 통과, 건수 직전 이상 |
| 린트 | `uv run ruff check .` | 통과 |
| 프론트 | `(cd frontend/k-context && node --test)` | 통과, 건수 직전 이상 |
| 평가 | `uv run python eval/kc.py validate` · `uv run python eval/kc.py run --check --known-failures eval/BASELINE.md` | 0 · 0 |
| 데모 | `bash scripts/kc_demo.sh --check` · `--smoke` | 0 |
| 데모 확인 | 로컬 서버에서 데모 문장 "10/15에 창덕궁 10시, 익선동 2시, 숙소는 종로3가야" → 일정 3개·실록 언급·행사, `?api=mock` 그대로 | 사람 또는 헤드리스 확인 기록 |
| reviewer | 스테이지 diff 검토 | PASS |

### 7.2 스테이지별 추가 확인
| 게이트 | 추가 확인 | 의도된 변화(실패로 보지 않음) |
|---|---|---|
| Stage 1 | 스파이크 4개 `[확인 필요]` 목록, 검색 시간 전후, 측정 문서 | 보안 로그가 최신 우선·날짜 표시 |
| G1 | D24~D28 승인 | — |
| Stage 2 | `--public --smoke` 0, 공개 모드 E2E | 로컬에서도 새 탭 = 새 대화(세션별 기록) |
| Stage 3 | 25개 구 행사 수·색인 크기·자동 좌표 수(T418 문서) | 행사 수 증가, `COORD_AUTO` 문구 등장 |
| Stage 4 | TourAPI 테스트, (키 있으면) 보고서 | 행사 항목 수 변화 |
| Stage 5 | 컨테이너 파일 테스트, 빌드 스크립트 테스트, dry-run | — |
| Stage 6 | T426 점검 표 전 항목 | — |
| Stage 7 | 문서 링크 | — |

---

## 8. 이월 흡수·유지 표

| 출처(sprint-3) | 항목 | 이번 처리 |
|---|---|---|
| Stage 5 이월 | 행사 검색 1회 약 6초 | **T407** |
| Stage 5 이월 | 묶음 events 233KB(항목 필드 다듬기) | 유지 — T407 로 excluded 쪽만 영향 없음. 필드 다듬기는 S5 이월 |
| Stage 6 이월 | 보안 로그 날짜 없음·오래된 순 | **T406** |
| Stage 4 이월 | 캐시 키와 해석의 today 불일치(TRIP_INVALID·자정) | **T405** |
| Stage 2 이월 W7 | 캐시 키에 `LLM_BACKEND*` 없음 | **T405**(주입 규칙 버전은 유지 이월 — 버전 상수가 없어 별도 결정 필요) |
| Stage 4 이월 | 지역 bbox 도우미(합친 지역의 좌표만 있는 장소) | 유지 — bbox 가 모두 null(H7 데이터 없음). 25개 구는 출처가 준 구(GUNAME·T401 코드표)로 판정 |
| Stage 4 이월 | 프론트 여행 기간 상한 미리 안내 | 유지(S5) |
| Stage 5 이월 | Tavily LlmCallError 3건 원인 | T432 를 할 때만 |
| Stage 5 이월 | 스냅샷 시점 자료 | **T418** 재생성 |
| Stage 2·5 이월 | 변동 목표 미달(H10 검수 뒤 재판정) | 유지 — 범위 밖 |
| Stage 6 이월 | 새로고침 시 일정·지도 비워짐(D17) | 유지 — 세션은 대화만 복원(D24 ①) |
| Sprint 2·1 이월 | T222·T223 추출 보조·T224·S1 항목 | 유지 |

## 9. 가장 큰 리스크
1. **Netlify ↔ Cloud Run 연결 방식**: 프록시 시간 한도가 일정 흐름(최대 100초)보다 짧거나 방문자 IP 가 안 넘어오면 프록시를 못 쓴다 → 직접 CORS + 빌드 시 CSP 주입으로 가야 하고(T424 가 두 모드를 모두 준비), IP 기반 제한(D24 ④)의 hops 값이 달라진다. T403 에서 문서로 못 정하면 T427 실측까지 불확실.
2. **25개 구 데이터 규모 → 무료 사용량·메모리·이미지 크기**: 행사 행 수 증가로 병합(이중 반복)·검색·자식 프로세스 메모리가 커지고, 실록 색인도 커진다. T407(사전 제외)·T416(블로킹)·T408(측정)으로 대응하지만, 측정 전에는 Cloud Run 메모리와 이미지 한도 안에 드는지 알 수 없다(D27·D28 의 `[확인 필요]`).
3. **사실 데이터의 사람 의존**: 21개 구 실록 키워드(H3)와 서울 범위 bbox 는 지어낼 수 없어, 없으면 새 구는 "행사·자동 좌표만, 실록 없음"이 된다. 자동 좌표도 행사 장소명이라 사용자가 쓰는 명소 이름과 어긋날 수 있고, 명소 좌표는 TourAPI 키(H2)가 와야 채워진다.
- 그 밖: 공개 LLM 비용(크레딧 미확인 — 일일 상한 300으로 막음), TourAPI 필드 확인 지연(T401 `[확인 필요]` 가 많으면 T419 범위 축소), 메모리 세션은 재시작 시 대화가 사라짐(데모로 허용, D27 ⑥).

## 이월
(스프린트 종료 시 `/done` 이 기록한다)

## 완료 기록
(스테이지마다 `/stage` 가 기록한다)
