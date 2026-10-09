# Sprint 3 — 해커톤 이후 완성: 포트폴리오 데모 (확정)

> 상태: **확정**(pm, 2026-10-09). 초안 `sprint-3.draft.md` 에 dev 현실성 평가를 반영했다(끝의 "dev 평가 반영 내역"). 초안은 그대로 둔다.
> 범위 근거: `docs/SCOPE.md` "Sprint 3 범위" — 반드시 만들 것 ① 안정성 + 평가셋 ② MOCK 제거 ③ 행사 실데이터 ④ README·상태 문서·GIF 갱신(우선순위 순).
> "지금 안 만들 것"(NemoClaw/OpenClaw·MCP 로 샌드박스 안 에이전트화, 공개 배포·Brev·도메인, 여행 기록·사진 정리, 4개 구 밖 자료)은 어떤 태스크에도 넣지 않았다.
> 시간 상자: 기한 없음. 소요 시간은 추정하지 않는다. **스테이지가 끝날 때마다 데모(README 실행 절차 + `?api=mock`)가 동작해야 한다** — 게이트마다 "데모 확인" 칸이 있다.
> 태스크 ID: `T3{순번 2자리}`. 초안과 같은 번호를 유지했다(T326 만 새로 생김).

## Sprint 3 최종 실행 계획

| 스테이지 | 태스크 | 병렬 | 예상 결과물 |
|---|---|---|---|
| Stage 1 — 기준선 측정 | 1a: T301 일정·게이트 평가셋 · T302 실록 언급 평가셋(색인 실측) · T303 판정 평가셋 · T304 평가 패키지·결정적 실행기 · T306 LLM 파라미터 확인 → 1b: T305 안정성 측정기 → **T307 기준선 실행** | 1a 5개 병렬 → 1b 순차 2개 | `eval/kc_eval/*`, `eval/kc.py`, `eval/drafts/*.json`, `docs/spikes/llm_params.md`, `eval/BASELINE.md` + `eval/results/baseline-*.json` |
| Stage 2 — 안정화 | 2a: T308 core/llm 파라미터·설정 값 · T309 재시도(예산 안)·결과 캐시 · T310 시간 예산·실패 시 고정 문구 → 2b: **T311 재측정** → 2c: *[조건부]* T326 규칙 대체 추출 | 2a 3개 병렬 → 2b → 2c | 결정적 파라미터, 예산 안 재시도, 캐시, 프론트 100초 기준 시간 사슬, `eval/results/stage2-*.json` |
| Stage 3 — MOCK 제거 ① 데이터 생산·수용 | T313 backend v2 수용 · T314 프론트 v2 수용·표시 · T317 계약 문서 → (머지 마지막) T312 파이프라인 v2 · *[조건부 H7]* T315 · *[조건부 H8]* T316 | 개발은 병렬, **머지는 수용(T313·T314) 먼저 → 생산(T312) 마지막** | `kc-chat-bundle/v2`(routes·rationale·events_rationale·schedule), 화면이 묶음으로 경로·근거를 그림 |
| Stage 4 — MOCK 제거 ② · 행사 지역 | T318 실제 모드 예시 끄기·보안 로그 실연결 · T319 카탈로그 4개 구 대상 | 2개 병렬 | 실제 모드 MOCK 딱지 0개, 카탈로그가 4개 구 |
| Stage 5 — 행사 실데이터 · 재측정 | T320 강남 검색 수집 출처 → T321 수집 실행·보고 ∥ *[조건부 D19]* T322 스냅샷 → **T323 재측정** | T320 → (T321 ∥ T322) → T323 | 4개 구 실제 행사, `docs/status/events_data_*.md`, 최종 수치 |
| Stage 6 — 문서·재현 | T324 데모 스크립트 + E2E · T325 README·상태 문서·다이어그램 HTML (PNG·GIF 는 사람 H12) | 2개 병렬 | `scripts/kc_demo.sh`, `tests/test_kc3_e2e_chat.py`, 새 상태 문서, README |

- **필수 경로**: T301~T304 → T305 → T307 →(D15 승인)→ T308~T310 → T311 → T313·T314·T317 → T312 → T318·T319 → T320 → T321 → T323 → T324·T325.
- **조건부**: T306(키 없으면 "미확인"으로 완료), T326(T311 미달 시), T315(H7 데이터가 올 때), T316(H8 데이터가 올 때), T322(D19 승인 시), T323 의 사전 효과 측정(H7·H8 이 없으면 T311 측정의 재실행으로 대체).
- **키가 필요한 일**: T306·T307·T311·T323 의 측정, T321 의 수집뿐이다. 모두 스테이지 끝에 두었다.
- **얇은 수직 경로는 이미 있다**: 일정 문장 → 별도 프로세스 파이프라인 → 묶음 → 화면, 보안 로그·사람 승인 API 는 Sprint 2 에서 이어졌다(§0.3). Stage 1 은 경로를 새로 세우지 않고 그 흔들림을 숫자로 잡는다.

---

## 0. 기준선 · 공통 규칙

### 0.1 착수 직전 dev 가 실측해 적는다
- `uv run python -m pytest -q` 건수: ____ (README 기록 1,644 — 실측값을 쓴다)
- `uv run ruff check .`: 통과 여부
- `(cd frontend/k-context && node --test)` 건수: ____ (README 기록 302)
- `uv run python -m domains.kcontext.index stats --db var/index/kcontext.db` 의 `total`·`fts_enabled`·지역별 건수. 색인 파일은 있다(약 45MB, 2026-10-07 생성).
- `.env` 에 `NVIDIA_API_KEY` 항목이 있다(확인됨). **크레딧 잔량은 미확인**(H4).

### 0.2 공통 규칙 (Sprint 2 §0.2 를 이어받음)
- 파이썬 3.11+, 줄 길이 100, ruff 통과. 공개 함수에 타입 힌트, 새 패키지 `__init__.py` 는 `__all__` 명시.
- **PostToolUse 훅이 `ruff --fix` 로 미사용 import 를 지운다. import 와 그 사용은 한 번의 편집에 같이 쓴다.**
- **새 런타임 의존성 금지.** 있는 것만: `fastapi`·`httpx`·`mcp`·`openai`·`python-dotenv`·`uvicorn` + 표준 라이브러리. 프론트는 의존성 없음.
- 테스트 파일 이름은 레포 전체에서 고유하게. 이번 스프린트 새 테스트는 **`test_kc3_*`** 접두사.
- `tests/test_layout.py`·`tests/test_smoke.py`·`tests/test_boundaries.py` 는 수정하지 않는다.
- 도메인 코드는 `domains/kcontext/` 에만. `core/` 에 도메인 용어 금지(D3). 예외: T308(도메인 무관한 호출 파라미터).
- **backend 는 `domains`·`mcp_server` 를 import 하지 않는다**(D3·D10). 별도 프로세스와 JSON 으로만 받는다.
- **지역은 코드에 박지 않는다**(`data/regions/*.json` 에서만. 테스트 fixture·`data/` 예외).
- **사실을 지어내지 않는다.** 평가셋·테스트의 행사·연도·인물·좌표는 `○○`·`예시`·`합성` 표시 값만. 일정 문장은 우리가 만든 입력이라 실제 장소 이름을 쓰되 `"synthetic": true`. **실록 근거는 실제 색인 조회 값만**(조회 날짜 기록). 장소 좌표·한자 별칭은 **사람이 출처를 확인한 값만**(H7·H8) — dev 가 채우지 않는다.
- 키는 env **변수 이름**으로만(규칙 1, D1, D5). 키 값·Authorization 헤더·LLM 원문 응답 전체를 코드·로그·결과 파일·커밋에 남기지 않는다.
- `deploy/openshell/policy*.yaml`·`.env`·`eval/testset.json`·`CLAUDE.md`·`docs/DECISIONS.md` 는 dev·pm 이 고치지 않는다.
- 프론트 태스크는 **표에 적힌 파일만** 고친다.
- **결과를 맞추려고 기대 정답을 고치지 않는다.** 다르게 나오면 "실패 — 발견"으로 기록한다. 기대 정답 확정은 사람(H10).
- `?api=mock` 데모 모드는 지우지 않는다. `frontend/k-context/src/data/*`·`src/api/mock.js` 는 mock 전용으로 남긴다.

### 0.3 코드로 확인한 현황 (2026-10-09, dev 대조 확인 완료)
| 영역 | 코드 위치 | 확인한 사실 | 관계 태스크 |
|---|---|---|---|
| 채팅 → 일정 흐름 | `backend/chat.py` → `schedule_gate.looks_like_schedule` → `story_runner.run_story`(`TIMEOUT_S = 90`) → `chat_story.clean_bundle`·`attach_events` | 실패·앵커 0개면 **일반 챗봇(LLM 한 번 더)** 으로 폴백 | T305, T310 |
| 일정 이해 | `domains/kcontext/schedule/understand.py` | LLM 1회, 재시도 없음. 실패는 `LLM_*` 문제 코드로 앵커 0개 | T309 |
| LLM 호출 | `core/llm/http_transport.py`·`client.py`·`deploy/llm.chat.yaml` | body 는 `model·messages·max_tokens·stream` 뿐(**temperature·seed·response_format 없음**). 키 1개면 시도 1번. `timeout_s: 60`. 일정 이해는 `chat` feature 재사용, `MAX_TOKENS=4096` | T308 |
| 시간 사슬 | transport 60s · runner 90s · 프론트 `REQUEST_TIMEOUT_MS = 80_000` · 폴백 챗봇 60s 추가 | 프론트가 backend 보다 먼저 끊을 수 있다 | T310 |
| 실록 언급 | `story/finder.py`·`mention.py` | LLM 없음(결정적). 별칭 표에 한자→한자 줄만, 한글→한자 없음. 검색어당 후보 200 상한 | T302, T316 |
| 좌표 | `data/places/demo_places.json` 5곳 + 사본 `backend/fixtures/chat_places.json`(수동 동기화) | | T315 |
| 경로 | `domains/kcontext/geo/`, `catalog/routes.py` | 경로 A·B·C 생성 코드 없음. 직선 추정은 `KC_ROUTE_ESTIMATE_APPROVED=1` 일 때만 | D16·D18, T312 |
| 화면 API | `backend/routers/screen.py` | `cards`·`sources`·`rationale` 은 mock 과 같은 fixture. itinerary·routes 없음 | D17 |
| 프론트 데이터 출처 | `src/api/index.js`·`http.js` | `chat` 모드: itinerary·routes·audit 는 mock, cards·sources·rationale 은 fixture. `http.js` 의 getItinerary·getRoutes·getAuditLog·decideAudit 미구현 | T314, T318 |
| 묶음 검증(프론트) | `src/api/bundle.js` | 알려진 필드만 새 객체로 — 서버가 필드를 더해도 화면에 안 간다. v1 외 schema 는 버림 | Stage 3 머지 순서 |
| 행사 카탈로그 | `domains/kcontext/catalog/` | 대상 지역 하나(`KC_TARGET_REGION`, 기본 `jung`). `Region.gu` 는 튜플. 검색 수집 출처는 `junggu_site` 하나. 서울 API 는 `GUNAME` 으로 판정 → 키만 있으면 4개 구를 덮는다 | T319·T320·T321 |
| 평가 | `eval/` | README 만. 훅이 `eval/testset.json` 쓰기를 막는다 | Stage 1 |

---

## 1. 의존성 그래프

```
[사람 선행 — §3]

Stage 1a (병렬)                                     Stage 1b (순차)
T301 일정·게이트 케이스 ─┐
T302 언급 케이스 ────────┤
T303 판정 케이스 ────────┼─► T305 측정기 (kc_eval.match import) ─► T307 기준선 (H4)
T304 패키지·실행기 ──────┤                                            │
T306 파라미터 스파이크 ──┘                                            │ + D15 승인 (Stage 1 게이트)
                                                                      ▼
Stage 2a (병렬): T308 파라미터·yaml · T309 재시도·캐시 · T310 시간 예산·고정 문구
Stage 2b: T311 재측정 (H4) ──► 미달 시 2c: T326 규칙 대체 (조건부)
                                                                      │
Stage 3 (개발 병렬, 머지 순서 고정)                                    ▼
  머지 1: T313 backend v2 수용 (T310 머지 후) · T314 프론트 v2 수용 · T317 문서
  머지 2: T312 파이프라인 v2 (생산 — 마지막)
  조건부: T315 (H7 데이터) · T316 (H8 데이터)
                                                                      │
Stage 4 (병렬): T318 실제 모드 예시 끄기 · T319 카탈로그 4개 구          │
                                                                      ▼
Stage 5: T320 강남 출처 → T321 수집 (H5 | H6) ∥ T322 스냅샷 (D19) → T323 재측정 (H4)
                                                                      │
Stage 6 (병렬): T324 데모 스크립트·E2E ∥ T325 문서         (그 뒤 H12: GIF·PNG)
```

---

## 2. 결정 후보 (먼저 결정을 추가해야 함)

pm·dev 는 `docs/DECISIONS.md` 를 고치지 않는다. 사람이 승인하면 D15 부터 추가한다.

| 후보 | 요지 | 승인 시점(착수 조건) | 승인 전 진행 |
|---|---|---|---|
| D15 | 일정 이해 안정화·시간 예산 정책 | **Stage 1 게이트**(Stage 2 착수 조건) | Stage 2 착수하지 않음 |
| D16 | 직선 추정 도보 시간은 표시(예상)에만, 판정에는 안 씀 | Stage 3 착수 전 | T312 는 `walk_min: null`("이동시간 확인 필요") |
| D17 | 화면 데이터 단일 출처 = 채팅 묶음 v2, 실제 모드에 예시 데이터 없음 | Stage 3 착수 전 | 없음 |
| D18 | 경로 A·B·C 는 근거 좌표 있는 이야기가 생길 때만 | Stage 3 착수 전 | 없음 |
| D19 | 데모 행사 스냅샷은 공공누리 출처 항목만 저장소에 | T322 착수 전 | 스냅샷 없이 진행 |

### D15~D19 문안 (승인용)

```markdown
## D15 — 일정 이해는 결정적 파라미터·예산 안 재시도·결과 캐시로 안정화하고, 시간 예산은 프론트 상한에서 거꾸로 정하며, 실패를 일반 답으로 덮지 않는다 (2026-10-09)
- **결정**:
  ① `core/llm` 의 feature 설정에 호출 파라미터 `params`(허용 목록: temperature·top_p·seed·max_tokens·response_format·reasoning_effort)를 둔다. 값은 공급자가 받아들인다고 실측(docs/spikes/llm_params.md)한 것만 넣는다. 일정 이해는 `schedule` feature 를 쓴다(없으면 `chat`).
  ② **시간 예산은 프론트 요청 상한 100초에서 거꾸로 정한다**: backend 파이프라인 한도 = 90초, 파이프라인 안 LLM 예산 = 75초, LLM 1회 한도(`timeout_s`) = 기준선 p95 × 1.5(20~75초 사이로 자름). 숫자는 sprint-3 §6.4 표를 따른다.
  ③ LLM 응답이 실패·빈 응답·JSON 아님·형식 틀림이면 **같은 백엔드로 1회** 다시 부르되, **남은 LLM 예산이 LLM 1회 한도 이상일 때만**(첫 시도가 일찍 실패했을 때만) 부른다. 다른 백엔드로 넘어가지 않는다(D6).
  ④ quote 검증을 통과한 LLM 결과는 `var/cache/schedule/` 에 캐시한다. 키는 정규화한 입력 글·여행 기간·프롬프트 해시·LLM 설정 파일 해시·모델 덮어쓰기 env 다. 캐시 결과를 쓰면 묶음에 `schedule.source: "cache"` 와 원래 생성 시각을 남기고 화면은 "이전 결과 재사용"으로 표시한다. 평가는 캐시를 끈다.
  ⑤ 일정 문장으로 판별됐는데 LLM 이 (재시도 뒤에도) 실패해 앵커를 얻지 못했거나 파이프라인이 한도를 넘기면, 일반 챗봇으로 넘기지 않고 고정 문구("일정을 지금 정리하지 못했어요. 잠시 뒤 다시 보내 주세요.")로 답한다. LLM 이 정상으로 답했는데 앵커가 0개(일정이 아님)일 때만, 남은 예산이 LLM 1회 한도 이상이면 일반 챗봇으로 간다. 입력·결과 조합별 동작은 sprint-3 §6.5 표다.
- **계기**: 같은 문장이 일정 3개/2개/일반 답 폴백으로 갈렸고(README), 시간 사슬이 어긋나 프론트(80초)가 backend(90초)보다 먼저 끊을 수 있었다.
- **대안**: 캐시 없이 파라미터만 — 공급자가 결정성을 보장하지 않으면 같은 결과를 약속할 수 없어 기각. 실패 시 일반 챗봇 폴백 유지 — 일정 실패가 엉뚱한 답으로 가려지고 지연이 두 배가 되어 기각. 예산과 무관한 고정 재시도 — 프론트 한도를 넘어 기각. 규칙 대체 추출 — 재측정(T311)이 목표에 못 미칠 때 별도 결정으로 다시 검토(보류).

## D16 — 직선 추정 도보 시간은 표시에만 쓰고 판정에는 쓰지 않는다 (2026-10-09)
- **결정**: D9 의 ③(직선거리 × 우회 계수 ÷ 보행 속도)은 화면에 "예상 시간"으로 보일 수 있지만, 일정 맞추기·추가 이동시간·"넣을 수 있음" 판정에는 쓰지 않는다. D13 ⑥ 은 "판정은 경로 서비스 결과만, 직선 추정은 '예상'으로 표시만"으로 읽는다. 켜는 것은 운영자 env(`KC_ROUTE_PROVIDER=estimate|chain` + `KC_ROUTE_ESTIMATE_APPROVED=1`)로만 한다.
- **계기**: docs/geo-walk.proposal.md 1번 — D9 와 D13 ⑥ 충돌. 구현은 이미 추정이 섞이면 fit 을 check_needed 로 둔다.
- **대안**: 추정 전면 금지 — 화면에 숫자가 하나도 없어 기각. 추정을 판정에도 — D13 ⑥ 의 위험 때문에 기각.

## D17 — 화면 데이터의 단일 출처는 채팅 묶음이고, 실제 모드에는 예시 데이터를 쓰지 않는다 (2026-10-09)
- **결정**: 실제 모드(backend 연결)의 타임라인·지도·카드·경로·판단 근거는 `POST /api/messages` 가 돌려준 `kc-chat-bundle/v2` 에서만 그린다. 묶음이 없으면 빈 상태, backend 에 닿지 못하면 오류 상태다. 보안 로그는 `GET /api/audit`·`POST /api/audit/{id}/decision`(D2) 만 쓴다. `backend/fixtures/screen` 과 `/api/cards`·`sources`·`rationale` 은 데모 전용으로 남기되 실제 모드는 부르지 않는다. 묶음은 서버에 보관하지 않는다.
- **계기**: SCOPE Sprint 3 ② "MOCK 제거".
- **대안**: 묶음을 서버에 저장하고 `/api/itinerary`·`routes` 로 읽기 — 일정 서버 보관을 하지 않기로 한 결정(screen-api.proposal §4-1)과 어긋나 기각. fixture 를 실제 모드에 계속 노출 — 가짜를 실제처럼 보여 기각.

## D18 — 경로 A·B·C 는 근거 좌표가 있는 이야기가 생길 때만 만든다 (2026-10-09)
- **결정**: 이야기 길 대안(A·B·C)은 좌표와 좌표 근거가 있는 이야기 레코드(`data/stories/`)가 있을 때만 만든다. 지금은 0건이므로 실제 모드는 같은 날 방문지 사이 "일정 순서 이동 구간"만 보이고 "이야기 길 없음 — 근거 좌표 없음"을 밝힌다. 실록 언급의 좌표는 일정 앵커 좌표이므로 이야기 구간으로 쓰지 않는다.
- **계기**: 실록 언급은 사건 장소를 알려 주지 않는다(제목 요약 글자 일치 검색).
- **대안**: 언급 앵커를 이은 선을 "이야기 길"로 — 근거 없는 경로라 기각. 경로 영역 숨김 — 이동 구간 정보까지 사라져 기각.

## D19 — 데모 재현용 행사 스냅샷은 공공누리 출처 항목만 저장소에 둔다 (2026-10-09)
- **결정**: `domains/kcontext/data/snapshots/catalog/` 에 서울 열린데이터광장(공공누리 1유형, 출처표시) 유래 정규화 항목과 수집 기록만 커밋하고 출처·수집일을 표시한다. Tavily 유래 레코드는 약관 확인 전 커밋하지 않는다(D12 ⑦). 데모 스크립트가 `var/catalog` 로 복사해 쓴다.
- **계기**: "누구나 README 대로 같은 결과"인데 행사 수집에는 각자의 키가 필요하다.
- **대안**: 스냅샷 없음 — 키 없는 사람은 0건만 봄(선택으로 남김). 원응답 커밋 — D7·D12 ⑦ 위반이라 기각.
```

---

## 3. 사람 선행 · 블로커

### 3.1 사람 선행 작업
| ID | 할 일 | 막는 태스크 | 막혀 있을 때 |
|---|---|---|---|
| H1 | `docs/SCOPE.md` 미커밋 변경 커밋 — **사용자 확인 후 코디네이터가 처리** | 전체 | 착수하지 않음 |
| H2 | D15~D19 승인 → DECISIONS.md. **D15 는 Stage 1 게이트에서** | §2 표 | §2 "승인 전 진행" |
| H3 | D14 확인(초안 → 확정 또는 수정) | 직접 막는 태스크 없음. T325 가 상태를 적는다 | "D14 확인 대기" 표기 |
| H4 | NVIDIA 크레딧 잔량 확인(키 항목은 `.env` 에 있음). 호출 수 상한: T306 ≤ 30, T307·T311·T323 각 ≤ 210(§8 T307) | T306·T307·T311·T323 | 코드는 진행, 측정만 대기 |
| H5 | **지금 바로 요청**: 서울 열린데이터광장 인증키 발급(발급 대기가 있다) → `SEOUL_OPENAPI_KEY`. 일일 호출 한도를 데이터셋 페이지에서 확인 | T321 경로 A | 경로 B(강남·중구 검색 수집)만 |
| H6 | Tavily 키·크레딧 확인, 이용약관(결과 저장·재사용) 원문 확인 | T321 경로 B | 경로 A 만 |
| H7 | 장소 좌표 확인·추가(`data/places/demo_places.json`, T315 README 형식) | T315 실행 | 5곳 그대로 |
| H8 | 한글→한자 별칭 사전 작성(`data/places/aliases.json`, 출처 필수, 한자 3자 이상) | T316 실행 | 별칭 없음 |
| H9 | 실록 언급 관련성 라벨링(`eval/drafts/mentions.json` 의 `relevant`) | precision@3 | 스냅샷 일치만 |
| H10 | 평가셋 검수 → `eval/testset.json` 생성(훅이 dev 쓰기를 막음) | "검수된 기준선" | `reviewed: false` 로 측정 |
| H11 | `CLAUDE.md` 회귀 절에 `(cd frontend/k-context && node --test)` 와 `uv run python eval/kc.py run --check --known-failures eval/BASELINE.md` 추가 | 공식 회귀 범위 | §7 게이트 표가 대신 |
| H12 | Stage 6 뒤 데모 GIF 재촬영(T325 장면 목록) **+ `docs/diagram/system-state.png` 를 T325 가 고친 HTML 에서 캡처** | README 완성 | 옛 GIF·PNG 에 "MOCK 표시 시기" 설명 |
| H13 | *(선택)* OSM 도보 엔진(OSRM foot) 구동 → `KC_OSM_ROUTER_URL` | T312 의 엔진 값 | D16 시 직선 추정 또는 "확인 필요" |
| H14 | *(선택, D18)* 좌표 근거 있는 이야기 레코드 큐레이션 | A·B·C(이번 태스크 없음) | A·B·C 는 mock 에만 |

### 3.2 블로커 요약
| 블로커 | 막히는 것 | 대응 |
|---|---|---|
| D15 승인 | Stage 2 | Stage 1 게이트 항목 |
| 크레딧(H4)·서울 키(H5)·Tavily(H6) | 측정·수집 | 스테이지 끝에 배치. 키 없을 때 기본 예산 표(§6.4) |
| 라이선스(서울 일일 한도, Tavily 약관) | T321 호출량, T322 범위 | 서울 1회 수집만, Tavily 레코드는 `var/` 에만 |
| 사람 데이터(H7·H8·H9) | 좌표·한자 재현율·정밀도 | T315·T316 조건부, T323 대체 경로 |
| 게이트웨이·샌드박스 | 없음 | 이번 스프린트는 샌드박스 밖 |

---

## 4. 스테이지 상세

### Stage 1 — 기준선 측정
| TASK | 제목 | 범위(소유 경로) | 선행 | 병렬 충돌 |
|------|------|------|------|------|
| T301 | 일정 이해·게이트 평가셋 | `eval/drafts/schedule.json`, `eval/drafts/gate.json` | — | 없음 |
| T302 | 실록 언급 평가셋(색인 실측) | `eval/kc_eval/snapshot_mentions.py`, `eval/drafts/mentions.json` | 로컬 색인 | 없음(`__init__.py` 는 만들지 않는다) |
| T303 | 판정 평가셋(Sprint 2 T220 재사용) | `eval/kc_eval/gen_judge.py`, `eval/drafts/judge.json` | — | 없음(같음) |
| T304 | 평가 패키지·결정적 실행기 | `eval/kc.py`, `eval/kc_eval/__init__.py`, `eval/kc_eval/match.py`, `eval/kc_eval/schema.py`, `eval/kc_eval/offline.py`, `eval/results/.gitkeep`, `eval/README.md`, `tests/eval/conftest.py`, `tests/eval/test_kc3_eval_offline.py` | §5.1 | 없음 |
| T306 | [확인] LLM 호출 파라미터 | `docs/spikes/llm_params.md` | H4(없으면 "미확인") | 없음 |
| T305 | 안정성 측정기 (1b) | `eval/kc_eval/stability.py`, `tests/eval/test_kc3_eval_stability.py` (`eval/kc.py` 의 `stability` 하위 명령은 T304 가 미리 자리를 만든다) | T304 | 1b 순차 |
| T307 | 기준선 실행·기록 (1b) | `eval/BASELINE.md`, `eval/results/baseline-*.json` | T301~T306, H4, 선행 게이트(§8 T307) | 1b 순차 |

### Stage 2 — 안정화
| TASK | 제목 | 범위 | 선행 | 병렬 충돌 |
|------|------|------|------|------|
| T308 | core/llm 기능별 파라미터 + 설정 값 | `core/llm/config.py`, `core/llm/client.py`, `core/llm/http_transport.py`, `deploy/llm.chat.yaml`, `deploy/llm.example.yaml`, `tests/core/llm/test_kc3_llm_params.py` | T306·T307, D15 | 없음 |
| T309 | 예산 안 재시도 + 결과 캐시 | `domains/kcontext/schedule/{understand.py, cache.py(신규), __main__.py, __init__.py}`, `domains/kcontext/pipeline/{run.py, __main__.py}`, `tests/domains/kcontext/schedule/test_kc3_schedule_{retry,cache}.py`, `tests/domains/kcontext/pipeline/test_kc3_pipeline_cache.py` | T307, D15 | 없음 |
| T310 | 시간 예산 정렬 + 실패 시 고정 문구 | `backend/story_runner.py`, `backend/chat.py`, `frontend/k-context/src/api/http.js`, `tests/backend/test_kc3_chat_failure.py`, `frontend/k-context/tests/api.timeout.test.js` | T307, D15 | 없음 |
| T311 | 재측정·분기 결정 (2b) | `eval/results/stage2-*.json`, `eval/BASELINE.md` "Stage 2 뒤", 필요 시 `deploy/llm.chat.yaml` 값만 | T308~T310, H4 | 단독 |
| T326 | *[조건부]* 규칙 대체 추출 (2c) | `domains/kcontext/schedule/{rules.py(신규), understand.py}`, `domains/kcontext/pipeline/run.py`, `tests/domains/kcontext/schedule/test_kc3_schedule_rules.py` | T311 미달 + 사람 승인(D15 보충) | 단독 |

### Stage 3 — MOCK 제거 ① (개발 병렬, 머지 순서 고정)
| TASK | 제목 | 범위 | 선행 | 머지 순서 |
|------|------|------|------|------|
| T313 | backend v2 수용 + 행사 근거 + env 전달 | `backend/chat_story.py`, `backend/story_runner.py`, `backend/chat.py`, `tests/backend/test_kc3_chat_bundle_v2.py` | **T310 머지 후**, §5.2, D17 | 1 |
| T314 | 프론트 v2 수용·경로·근거 표시 | `frontend/k-context/src/api/bundle.js`, `src/lib/chat-bundle.js`, `src/lib/chat-bundle-view.js`, `src/components/map/route-list.js`, `src/components/map/chat-layer.js`, `src/components/rationale/index.js`, `src/components/cards/bundle-view.js`, `src/components/timeline/bundle-view.js`, `src/i18n/ko.js`, `src/i18n/en.js`, `tests/chatbundle.v2.test.js` | §5.2, D17·D18 | 1 |
| T317 | 묶음 계약 문서 v2 | `docs/chat-bundle.contract.md` | §5.2 | 1 |
| T312 | 파이프라인 v2(생산) | `domains/kcontext/pipeline/{run.py, rationale.py(신규), legs.py(신규)}`, `tests/domains/kcontext/pipeline/test_kc3_pipeline_{rationale,legs,v2}.py` | T309, §5.2, D16·D18 | **2(마지막)** — T313·T314 가 머지된 뒤 |
| T315 | *[조건부 H7]* 장소 사전 동기화 | `scripts/sync_chat_places.py`, `backend/fixtures/chat_places.json`(생성물), `domains/kcontext/data/places/README.md`, `tests/test_kc3_places_sync.py` | H7 데이터 | 독립 |
| T316 | *[조건부 H8]* 한자 별칭 적재 | `domains/kcontext/index/aliases.py`, `domains/kcontext/index/__main__.py`, `domains/kcontext/data/places/aliases.json`, `tests/domains/kcontext/index/test_kc3_index_aliases.py` | H8 데이터 | 독립 |

### Stage 4 — MOCK 제거 ② · 행사 지역
| TASK | 제목 | 범위 | 선행 | 병렬 충돌 |
|------|------|------|------|------|
| T318 | 실제 모드에서 예시 데이터 끄기 + 보안 로그 실연결 | `frontend/k-context/src/api/index.js`, `src/api/http.js`, `src/state/selectors.js`, `src/state/actions.js`, `src/components/layout/topbar.js`, `src/components/timeline/index.js`, `src/components/cards/index.js`, `src/components/map/index.js`, `src/components/map/kakao-view.js`, `src/components/securitylog/index.js`, `src/i18n/ko.js`, `src/i18n/en.js`, `tests/realmode.test.js`, 기존 `tests/mock.status.test.js`·`tests/api.chat.test.js` 단언 수정 | T314, D17·D18 | 없음 |
| T319 | 카탈로그 대상 지역을 여러 구로 | `domains/kcontext/catalog/target.py`(신규), `catalog/api.py`, `catalog/__main__.py`, `catalog/web_events.py`(75행 지역 거르기만), `.env.example`, `tests/domains/kcontext/catalog/test_kc3_catalog_target.py` | — | 없음 |

### Stage 5 — 행사 실데이터 · 재측정
| TASK | 제목 | 범위 | 선행 | 순서 |
|------|------|------|------|------|
| T320 | 강남 검색 수집 출처 | `catalog/web_events.py`, `catalog/sources.py`, `data/catalog_sources.json`, `tests/domains/kcontext/catalog/test_kc3_catalog_web_sources.py` | T319 | 5a |
| T321 | 행사 수집 실행·검증 보고 | `docs/status/events_data_<YYYY-MM-DD>.md`, `data/catalog_sources.json` 의 `verified_at`·`notes` | T320, H5 또는 H6 | 5b |
| T322 | *[조건부 D19]* 데모 스냅샷 | `scripts/snapshot_catalog.py`, `domains/kcontext/data/snapshots/catalog/`, `tests/test_kc3_snapshot.py` | T321, D19 | 5b(∥ T321 의 보고서 작성) |
| T323 | 재측정·회귀 기준 확정 | `eval/results/final-*.json`, `eval/BASELINE.md` "최종" | T321, H4 | 5c |

### Stage 6 — 문서·재현
| TASK | 제목 | 범위 | 선행 |
|------|------|------|------|
| T324 | 데모 스크립트 + 끝까지 E2E (Sprint 2 T221 재사용) | `scripts/kc_demo.sh`, `tests/test_kc3_e2e_chat.py` | Stage 5 |
| T325 | README·상태 문서·다이어그램 HTML | `README.md`, `docs/status/<YYYY-MM-DD>_구현상태.md`(신규), `docs/diagram/system-state.html`, `docs/guides/EVENTS_CATALOG.md` | Stage 5 |

### 4.1 스테이지 구성 근거
- **Stage 1**: 제품 코드를 고치지 않으므로 데모는 그대로다. 평가 코드는 `eval/kc_eval/` 패키지 하나로 모으고(§5.0) 패키지 뼈대·앵커 비교 규칙(`match.py`)은 T304 만 만든다. 측정기(T305)는 그 규칙을 import 하므로 T304 뒤(1b)에 둔다. T302·T303 은 같은 패키지 안의 자기 모듈 한 개씩만 만든다. 키가 필요한 T307 은 맨 끝이고, Stage 1 게이트에 D15 승인을 넣어 Stage 2 가 결정 없이 시작하지 않게 했다.
- **Stage 2**: 파라미터(`core/llm`)·일정 이해(`domains`)·시간 사슬(`backend`·`http.js`) 세 층은 파일과 import 경계가 달라 병렬이 된다. `deploy/llm.chat.yaml` 은 T308 만 고친다. T309 는 `schedule` feature 가 없으면 `chat` 으로 내려가고 캐시 키는 yaml 바이트 해시로 만들어 T308 의 새 API 를 기다리지 않는다. 규칙 대체는 범위를 줄이려고 T311 결과에 달린 조건부(T326)로 뺐다.
- **Stage 3**: 프론트 검증기가 모르는 필드를 버리므로, v2 를 **받는 쪽(T313·T314)을 먼저 머지**하면 v1 묶음이 오는 동안에도 화면이 그대로고, 마지막에 **만드는 쪽(T312)** 을 머지하면 그 순간 v2 가 흐른다. T313 은 T310 이 고친 `chat.py`·`story_runner.py` 위에서 작업한다. T315·T316 은 사람 데이터가 올 때만 돌리는 독립 작업이다.
- **Stage 4**: T318 은 공용 프론트 파일을 고치므로 같은 스테이지에 다른 프론트 태스크가 없다. T319 는 `catalog/` 안에서 지역 id 를 쓰는 곳을 모두 맡고 `"+"` 분해 규칙을 `target.py` 한 곳에 둔다. 그래서 `web_events.py` 를 고치는 T320 은 Stage 5 로 넘겼다(같은 파일 충돌 방지).
- **Stage 5**: 출처 추가(T320) → 수집(T321) → 재측정(T323) 순. 키가 필요한 일을 뒤에 모았다.
- **Stage 6**: 결과가 다 나온 뒤 문서. PNG·GIF 캡처는 사람(H12).

---

## 5. 스테이지 사이 계약

### 5.0 평가 패키지 import 규칙 (하나로 못 박음)
- 평가 코드는 전부 `eval/kc_eval/` 패키지(`__init__.py` 는 T304 만 만들고 `__all__` 만 둔다). **`eval/__init__.py` 는 만들지 않는다**(`eval` 은 패키지가 아니다).
- 실행 입구는 하나: `uv run python eval/kc.py <하위 명령>`. `eval/kc.py` 맨 위에서 `sys.path.insert(0, str(Path(__file__).resolve().parent))` 와 레포 루트(`backend`·`domains` import 용) 삽입 후 `from kc_eval import ...`(그 import 줄에 `# noqa: E402`). 하위 명령: `run`(offline), `stability`(T305), `snapshot-mentions`(T302), `gen-judge`(T303). `kc.py` 는 하위 명령을 실행할 때 해당 모듈을 **지연 import** 하고 `main(argv: list[str]) -> int` 를 부른다 — 그래서 T302·T303·T305 모듈이 아직 없어도 T304 는 끝난다(없는 모듈이면 "아직 없음" 종료 코드 2).
- 테스트: `tests/eval/conftest.py`(T304) 가 같은 방식으로 `<repo>/eval` 을 `sys.path` 앞에 넣고, 테스트는 `from kc_eval import match` 처럼 import 한다. 다른 곳에서 `kc_eval` 을 import 하지 않는다.
- 앵커 비교 규칙은 `kc_eval/match.py` 에만 있다. T304(offline)·T305(stability)·T323 모두 이것을 import 한다.

### 5.1 평가셋 형식 `kc-eval/v1` (T301~T303 작성, T304·T305 읽기)
모든 파일 머리: `{"schema": "kc-eval/v1", "suite": "schedule|gate|mentions|judge", "created_at": "YYYY-MM-DD", "reviewed": false, "synthetic": true|false, "provenance": "한 줄", "cases": [...]}`. 케이스 `id` 는 `^[a-z0-9_]{1,48}$` 파일 안 고유, 모든 케이스에 `tags: [str]`.

**schedule** (T301):
```json
{"id": "sch_ko_basic_01", "lang": "ko", "synthetic": true,
 "text": "10/15에 창덕궁 10시, 익선동 2시, 숙소는 종로3가야",
 "trip": {"from": "2026-10-15", "to": "2026-10-18"},
 "expect": {"status": "ok",
   "anchors": [{"type": "visit", "name": "창덕궁", "date": "2026-10-15", "from": "10:00", "to": null},
               {"type": "visit", "name": "익선동", "date": "2026-10-15", "from": "14:00", "to": null},
               {"type": "hotel", "name": "종로3가", "date": null, "from": null, "to": null}],
   "problems_include": ["AMPM_ASSUMED"]},
 "tags": ["ampm", "hotel"]}
```
`trip` 은 null 가능. `expect.status`: `ok` | `no_anchors`.
**비교 규칙(`kc_eval/match.py`)**: `norm_name` = NFKC → 공백 제거 → casefold. 기대·실제 이름이 서로 포함 관계면 같은 장소. 날짜는 실제 `from`(없으면 `to`)의 앞 10자, 시각은 `from`/`to` 의 11~16자. 기대 `"*"` 는 무엇이든 통과, `null` 은 실제도 null. 숙소 `date` 는 체크인 날짜. "정답 일치" = 이름 1:1 대응 + 모든 필드 통과 + 개수 같음.
```python
# match.py
def norm_name(s: str) -> str
def same_place(expected: str, actual: str) -> bool
def match_anchors(expected: list[dict], actual: list[dict]) -> dict
    # {"pairs": [(ei, ai)], "missing": [ei], "extra": [ai], "field_fail": [{"i": ei, "field": str}], "exact": bool}
```

**gate** (T301): `{"id", "text", "expect": {"schedule": bool}, "tags"}`.

**mentions** (T302): 파일 `"synthetic": false` + `"index": {"db", "measured_at", "total_chunks", "fts_enabled", "alias_rows"}`.
```json
{"id": "men_changdeokgung", "anchor": "창덕궁", "limit": 3,
 "expect": {"reason": null, "terms": ["..."], "found_articles": 0, "found_truncated": false,
            "top": [{"article_id": "...", "title_summary": "...", "matched_in": "title",
                     "king": "...", "date_label": "...", "relevant": null}]},
 "tags": ["verified_coord"]}
```
(숫자·문자열은 형식 예시일 뿐 — 전부 T302 가 색인을 조회해 채운다.)

**judge** (T303):
```json
{"id": "trap_ended_01", "trap": "끝난 행사", "synthetic": true, "now": "2026-10-07T12:00:00+09:00",
 "observations": [<observation_from_dict 입력>], "request": {"trip": {...}, "interests": []},
 "expect": {"listed": ["○○ 가을 음악회"], "excluded": {"○○ 지난 축제": "종료됨"},
            "unresolved_conflict_fields": {}, "entry_count": 2},
 "tags": ["d13"]}
```
제목으로 비교, `excluded` 값은 `search_events` 사유 문자열 앞부분 일치. 주입 함정은 `{"kind": "guard", "text", "expect": {"verdict": "injection|suspicious|clean", "understand_blocked": bool}}`.

### 5.2 채팅 묶음 `kc-chat-bundle/v2` (T312 생산, T313 정리·추가, T314·T318 소비, T317 문서화)
v1 필드를 모두 두고 아래를 더한다. backend·프론트는 v1·v2 를 모두 받는다.
```
schema: "kc-chat-bundle/v2"
schedule: {"source": "llm" | "cache" | "rules"(T326 시에만), "attempts": int, "model": str | null,
           "prompt_sha": str, "cache_created_at": "YYYY-MM-DDTHH:MM:SSZ" | null}
           # T309 가 v1 에 가산 필드로 먼저 넣는다(프론트 v1 검증기는 무시). T312 가 schema 를 v2 로 올린다
routes: [{"id": "day1", "day": int | null, "date": "YYYY-MM-DD",
          "legs": [{"from": str, "to": str, "from_ll": [lat, lng], "to_ll": [lat, lng],
                    "straight_m": int, "walk_min": int | null, "provider": str, "estimated": bool}],
          "skipped": [{"from": str, "to": str, "reason": "좌표 없음" | "시각 없음"}]}]
rationale: {"mention:<story card id>": Rationale}       # T312
events_rationale: {"event:<event id>": Rationale}       # T313
story_routes_note: {"ko": "이야기 길 없음 — 근거 좌표가 있는 이야기가 없어요", "en": "No story route — no stories with grounded coordinates"}
```
- **id 공간**: 근거 맵의 키는 접두어 + 원래 id 다. 실록 언급 카드는 `mention:` + `cards[].card.id`(예 `mention:story_<article_id>`), 행사는 `event:` + `events.events[].id`. 각 값의 `card_id` 필드에도 접두어가 붙은 같은 키를 넣는다. 프론트는 선택한 항목 종류에 따라 접두어를 붙여 찾는다. 두 맵에 같은 키가 생길 수 없다.
- `Rationale` = 프론트 기존 형식 `{"card_id", "chips": [{"key", "tone": "old"|"now", "label": {ko,en}}], "items": {"<key>": {"title": {ko,en}, "text": {ko,en}, "rows": [{"k": {ko,en}, "v": {ko,en}}]}}}`.
- 상한(backend `clean_bundle`): routes 7 × legs 20, 근거 100개, chips 8, rows 12, 문자열은 v1 상한. 넘으면 자르고 `TRUNCATED`. 모양이 틀린 v2 필드는 그 필드만 버리고 `FIELD_DROPPED`.
- 모든 문자열은 신뢰하지 않는 입력(textContent 로만).

---

## 6. 안정화 목표·예산·분기

### 6.1 지표 정의 (T305 계산, T307·T311·T323 기록)
| 지표 | 정의 | 층 |
|---|---|---|
| 폴백 건수·률 | 기대 `ok` 케이스 실행 중 결과가 `fallback_llm`·`fallback_unverified`·`timeout`·`error`(파이프라인) 또는 `fallback_chat`·`schedule_unavailable`·`error`·`timeout`(API)인 건수와 비율 | 두 층 |
| 변동 케이스 수 | 기대 `ok` 케이스 중 반복 실행에서 앵커 개수가 한 번이라도 다른 케이스 수 | 파이프라인 |
| 일정 개수 변동률 | 케이스마다 (최빈값과 다른 실행 수 ÷ 실행 수)의 평균 | 파이프라인 |
| 정답 일치 건수·률 | §5.1 "정답 일치" 실행 수와 비율 | 파이프라인 |
| 앵커 재현율·정밀도 | 이름 대응 기준 | 파이프라인 |
| 지연 p50/p95 | 벽시계, nearest-rank. 성공 실행만의 p95 도 따로(§6.4 의 L) | 두 층 |
| 문제 코드 분포·좌표 부착률 | | 파이프라인 |
| 게이트 정밀도·재현율, 판정 통과율(함정별), 언급 스냅샷 일치·no_match·잘림·precision@3 | | 결정적 |

### 6.2 목표 — 건수 기준 (반복 수·케이스 고정)
측정 구성은 T307·T311·T323 에서 **같게** 고정한다: 파이프라인 층 = schedule 기대 `ok` 케이스 전부 × 3회, API 층 = 고정 10케이스 × 3회, 캐시 끔. 기준선 건수를 `F0`(폴백 건수), `C0`(변동 케이스 수), `E0`(정답 일치 건수), 실행 총수를 `N` 이라 할 때 T311 목표:
- 폴백 건수 ≤ min(⌊F0 / 2⌋, ⌊N × 0.05⌋). F0 = 0 이면 0.
- 변동 케이스 수 ≤ ⌊C0 / 2⌋. 캐시 켬 재요청은 변동 0(구조상 — T309 테스트).
- 정답 일치 건수 ≥ E0 − 2 (노이즈 허용 2건, 이 이상 떨어지면 회귀).
- 파이프라인 층 성공 실행 중 `TIMEOUT_S`(§6.4)에 걸린 건 0.
- 결정적 세트: Stage 1 에서 통과한 케이스는 계속 통과.
T307 이 실제 숫자를 `eval/BASELINE.md` "목표" 표에 계산해 적는다.

### 6.3 안정화 수단 분기 (Stage 2 범위 축소 반영)
| 수단 | 언제 | 담당 |
|---|---|---|
| S1 예산 안 재시도 1회 | 항상(D15 ③) | T309 |
| S3 결과 캐시 | 항상(D15 ④), 평가는 끔 | T309 |
| S4 실패 시 고정 문구 | 항상(D15 ⑤) | T310 |
| S5 temperature 0 | T306 "받아들임" + 기준선 C0 > 0 | T308 |
| S6 seed 고정(상수 7) | T306 "받아들임" + temperature 0·seed 5회 동일 | T308 |
| S7 JSON 모드 `{type: json_object}` | T306 "받아들임" + 기준선 폴백 중 `LLM_BAD_JSON`·`LLM_UNEXPECTED_SHAPE` ≥ 30% | T308 |
| S8 reasoning_effort · S9 max_tokens · S10 재시도 대상에 NO_ANCHOR_VERIFIED | **T311 재측정 결과로 정한다** | T311 |
| S2 규칙 대체 추출 | T311 미달 시 조건부 T326 | T326 |
| S11 스트리밍 | 이번 스프린트 안 함. T311 뒤 API 층 p95 가 프론트 상한을 넘으면 이월 기록 | — |

### 6.4 시간 예산 — 프론트 상한에서 거꾸로 (D15 ②)
| 이름 | 값 | 정하는 법 | 위치 |
|---|---|---|---|
| `F` 프론트 요청 상한 | **100초** (고정, 바꾸려면 D15 수정) | — | `http.js REQUEST_TIMEOUT_MS = 100_000` |
| `R` backend 파이프라인 한도 | **90초** = F − 10 | backend 가 프론트보다 먼저 끝나 고정 문구를 돌려줄 여유 | `story_runner.TIMEOUT_S` |
| `B` 파이프라인 안 LLM 예산 | **75초** = R − 15 | 프로세스 시작·색인 검색·쓰기 여유 | pipeline `--llm-budget-s` |
| `T_llm` LLM 1회 한도 | min(B, max(20, ⌈L × 1.5⌉)), L = 기준선 파이프라인 성공 실행 p95(초) | T307 계산 | yaml provider `timeout_s` |
| 재시도 허용 | 첫 시도 경과 `e` 에 대해 `e + T_llm ≤ B` 일 때만 | 첫 시도가 일찍 실패했을 때만 | `understand_with_meta` |
| 일반 챗봇 진입 | 파이프라인 경과 `s` 에 대해 `s + T_llm ≤ F − 5` 일 때만 | 아니면 고정 문구(§6.5) | `chat.py` |

**키가 없어 T307 이 비었을 때 쓰는 기본 예산**: F 100 · R 90 · B 75 · **T_llm 45** → 재시도는 첫 시도가 30초 안에 실패했을 때만, 일반 챗봇은 파이프라인이 50초 안에 끝났을 때만. 기준선 L × 1.5 > 75 면 T_llm = 75 (재시도가 사실상 없음) — `eval/BASELINE.md` 에 "지연 과다 — S8·S11 검토"로 기록.

### 6.5 T309·T310 동작 표 (입력 조합 → 출력)
Stage 2 범위(규칙 대체 없음). 파이프라인 종료 코드 2 는 실행 조건 미충족(파일·색인 없음, `--require-llm` + 키 없음)뿐이다.

| # | 캐시 | LLM 결과(재시도 포함) | `schedule.source` | 앵커 | 파이프라인 종료 | backend 동작 → 사용자 응답 | 캐시 쓰기 |
|---|---|---|---|---|---|---|---|
| 1 | 적중 | (부르지 않음) | `cache` | ≥1 | 0 | 묶음 + 정리 문구 + "이전 결과 재사용" | 없음 |
| 2 | 미적중 | 정상, 앵커 ≥1 | `llm` | ≥1 | 0 | 묶음 + 정리 문구 | 씀 |
| 3 | 미적중 | 정상, 앵커 0(일정 아님, `LLM_*` 문제 없음) | `llm` | 0 | 0 | 예산이 있으면(§6.4) 일반 챗봇 답, 없으면 고정 문구 "일정으로 정리할 항목을 찾지 못했어요" | 안 씀 |
| 4 | 미적중 | 실패(`LLM_FAILED·LLM_EMPTY·LLM_BAD_JSON·LLM_UNEXPECTED_SHAPE`, 재시도 후 또는 예산 부족으로 재시도 없음) | `llm` | 0 | 0 | **고정 문구 "일정을 지금 정리하지 못했어요"**(일반 챗봇으로 덮지 않음, D15 ⑤) | 안 씀 |
| 5 | 미적중 | 키 없음(클라이언트 생성 실패 → `LLM_UNAVAILABLE`) | `llm`(attempts 0) | 0 | 0 | #4 와 같음 | 안 씀 |
| 6 | — | 파이프라인이 `R` 을 넘김·비정상 종료·묶음 없음 | (묶음 없음) | — | timeout/≠0 | #4 와 같은 고정 문구, audit 에 종류 | 안 씀 |
| 7 | — | 입력 주입 차단(`INJECTION_BLOCKED`) — backend 가드가 먼저 막지 못한 경우 | `llm`(attempts 0) | 0 | 0 | #3 과 같음(LLM 실패가 아님) | 안 씀 |
| 8 | — | 색인 없음 | (실행 안 함) | — | — | 지금처럼 일반 챗봇(설치 문제 — README 안내) | — |
| (T326 시) | 미적중 | #4·#5 + 규칙 추출 앵커 ≥1 | `rules` | ≥1 | 0 | 묶음 + "규칙으로 정리(장소 사전 이름만)" | 안 씀 |

---

## 7. 스테이지 게이트

```
uv run python -m pytest -q
uv run ruff check .
(cd frontend/k-context && node --test)
uv run python eval/kc.py run --check --known-failures eval/BASELINE.md     # Stage 1 부터
```
| 게이트 | 판정 시점 | 통과 조건 | 데모 확인 |
|---|---|---|---|
| Stage 1 | T307 종료 | pytest 건수가 §0.1 보다 많다 · node 건수는 §0.1 과 같다(프론트 변경 없음) · ruff · 위 eval 명령 0 종료 · `eval/BASELINE.md` 에 §6.1 지표·§6.2 목표·§6.4 예산 표 · **D15 승인됨(Stage 2 착수 조건)** · reviewer: 결과 파일에 키·원문 응답 없음, 지어낸 실록 근거 없음 | 제품 변경 없음 — README 절차 그대로 |
| Stage 2 | T311(·T326) 종료 | 위 명령 전부, pytest·node 건수 증가 · §6.2 목표 표에 줄마다 "충족 / 미충족 — 원인 — 조치" · reviewer: D1·D5·D6, D15 ⑤(§6.5 #4~#6 에서 일반 챗봇이 불리지 않음), 캐시에 키·원문 없음 | 같은 문장 두 번 → 두 번째가 "이전 결과 재사용" + 같은 앵커 |
| Stage 3 | 머지 2(T312) 뒤 | 위 명령 전부, 건수 증가 · **머지 1 직후에도** 같은 명령이 통과하고 화면이 v1 묶음으로 그대로 돈다(dev 1회 확인) · 파이프라인 CLI 가 v2 묶음을 쓰고 `rationale` 키 = `mention:`+카드 id · reviewer: D3·D10, 근거 문구가 템플릿 + 데이터 값뿐, D18 | 일정 문장 → 이동 구간 목록, 카드 → 실제 근거 패널. `?api=mock` 그대로 |
| Stage 4 | T318·T319 종료 | 위 명령 전부, 건수 ≥ 직전(T318 은 단언 수정이라 같은 수 유지) · 실제 모드 `.mock-badge` 0개(T318 테스트) · `uv run python -m domains.kcontext.catalog --region jung,jongno,mapo,gangnam status` 0 종료 · **의도된 변화 명시**: 실제 모드에서 backend 가 꺼져 있으면(명시 `?api=chat`·`http`) 예전처럼 mock 으로 채우지 않고 빈 상태·오류 상태가 나온다. `auto` 에서 backend 가 꺼져 있으면 지금처럼 mock 모드(전체 MOCK 딱지)다 · reviewer: D2(결정 본문에 신원 없음) | 백엔드 연결 시 첫 화면 MOCK 딱지 0, 보안 로그가 서버 기록만 |
| Stage 5 | T323 종료 | 위 명령 전부 · `docs/status/events_data_*.md` · BASELINE "최종" · (D19 시) 스냅샷 테스트 | 4개 구 날짜 일정 → 실제 행사 카드 또는 "0건 + 수집 범위" |
| Stage 6 | T324·T325 종료 | 위 명령 전부 · `bash scripts/kc_demo.sh --check` 0 종료 · README 명령을 새 셸에서 따라 해 화면이 뜬다(dev 1회 기록) | README 절차만으로 데모 |

- 건수가 줄면 게이트 실패. 게이트 실패 시 다음 스테이지에 착수하지 않는다.

---

## 8. 태스크별 상세 구현 명세

---

#### T301 — 일정 이해·게이트 평가셋 [Stage 1a]
- **변경 파일**: 신규 `eval/drafts/schedule.json`, `eval/drafts/gate.json`
- **장소 이름 제한**: **T302 와 같은 목록만** 쓴다 — `domains/kcontext/data/regions/*.json` 의 `keywords` 와 장소 사전 5곳(창덕궁·익선동·경복궁·광화문·종로3가와 그 aliases). 목록 밖 이름은 쓰지 않는다. `out_of_dict` 유형은 이 목록 중 장소 사전에 **없는** 이름(regions keywords 쪽)으로 만든다.
- **핵심 로직**
  1. schedule 케이스 20개: 한국어 14 · 영어 4 · 주입 2. trip 은 16개 `{"from": "2026-10-15", "to": "2026-10-18"}`, 4개 null.
  2. 유형(태그, 각 1개 이상): `basic`(데모 문장 그대로 포함), `ampm`, `explicit_pm`, `range`, `multi_day`, `date_header`, `hotel_checkin`, `out_of_dict`, `no_year_no_trip`(기대 `date: null`, `problems_include: ["YEAR_UNKNOWN"]`), `en`(4개), `korean_month_day`, `injection`(기대 `no_anchors`, `INJECTION_BLOCKED`), `long_list`(앵커 5개 이상).
  3. 기대 앵커는 문장이 말한 것만. 없는 끝 시각 `null`, 오전·오후 없는 "2시"는 `14:00` + `AMPM_ASSUMED`, 확신 없는 필드 `"*"`.
  4. gate 케이스 24개(참 12 · 거짓 12). 거짓에 "경복궁은 어떤 곳이야?", 시각만, 장소만, "10/15 경복궁은 어때?"(기대 거짓 — 현재 오탐으로 실패 기록), 참에 "경복궁 갔다가 익선동 갈 거야"(기대 참 — 현재 미탐으로 실패 기록).
- **엣지 케이스**: 문장·id 중복 금지, 300자 이하, 실제 인물·연도·행사명 금지.
- **지켜야 할 규칙**: §0.2 합성 표시 · 4개 구 밖 금지.
- **DoD**: 두 파일이 JSON 으로 로드되고 케이스 수가 20·24 다(`python -c` 한 줄로 확인). 형식 검증(`validate_suite`)은 T307 의 선행 게이트에서 돌린다.

---

#### T302 — 실록 언급 평가셋(색인 실측) [Stage 1a]
- **변경 파일**: 신규 `eval/kc_eval/snapshot_mentions.py`(`main(argv) -> int`), `eval/drafts/mentions.json`
- **실행**: `uv run python eval/kc.py snapshot-mentions --db var/index/kcontext.db --out eval/drafts/mentions.json --measured-at YYYY-MM-DD [--limit 3] [--extra-aliases-label NAME]`
- **핵심 로직**
  1. 앵커 목록은 **고정**: `load_regions()` 의 모든 `keywords` + `load_places()` 의 이름 5개(별칭 제외), 정렬·중복 제거. 코드에 이름을 쓰지 않는다.
  2. `LocalIndex(db)`(먼저 `is_file()` 확인) → `build_mentions(idx, [{"name": n}...], limit)` → §5.1 `mentions` 케이스. 파일 머리 `index` 블록(`idx.count()`, `fts_enabled`, `SELECT COUNT(*) FROM place_alias`, `measured_at`).
  3. 결과를 고치지 않는다(no_match 도 케이스). 원문 구절(`quote`)은 넣지 않는다.
- **엣지 케이스**: db 없음 → 종료 2.
- **지켜야 할 규칙**: 실제 색인 값만, 읽기 전용 · `eval/kc_eval/__init__.py` 를 만들지 않는다.
- **DoD**: 두 번 실행 결과의 `cases` 가 같다(결정적) · 파일 커밋 · ruff. (T304 의 `kc.py` 가 아직 없으면 `uv run python -c "import sys; sys.path.insert(0,'eval'); from kc_eval import snapshot_mentions as m; raise SystemExit(m.main([...]))"` 로 실행해도 된다.)

---

#### T303 — 판정 평가셋(Sprint 2 T220 재사용) [Stage 1a]
- **출처**: Sprint 2 초안 T220. 대상을 화면이 실제로 쓰는 카탈로그 경로(`build_entries` → `search_events`)와 주입 차단(`screen`, `understand`)으로 바꿨다. 이야기 함정은 대상 코드가 없어 뺐다.
- **변경 파일**: 신규 `eval/kc_eval/gen_judge.py`(`main(argv) -> int`), `eval/drafts/judge.json`
- **실행**: `uv run python eval/kc.py gen-judge --out eval/drafts/judge.json`
- **핵심 로직**: `catalog.model` 의 dataclass 로 합성 관찰값을 이 파일 안에서 만들고(tests 를 import 하지 않음) `dataclasses.asdict` 로 직렬화, `observation_from_dict` 로 되읽어 확인. 케이스(각 1개 이상, `○○`): 끝난 행사 → "종료됨" / 공식 취소 → "취소됨" / AI·제보만 취소 → 목록에 남음 / 지역 밖 → "대상 지역 밖에서 열림" / 지역 미확인 → "대상 지역에서 열리는지 확인되지 않음" / 날짜 안 열림 → "여행 날짜에 열리지 않음" / 휴무일 → "여행 날짜가 휴무일" / 공식끼리 가격 충돌 → `unresolved_conflict_fields` 에 `price` / 같은 외부 id → `entry_count` 1 / 같은 체계 다른 id → 2 / 행사명만 같음 → 2 / 관심사 필수 불일치 → "관심사와 맞지 않음" / 숨은 지시문(guard) ×3 / 정상 대조군 ×2. 기대값은 D13·코드 주석 규칙에서 정하고 현재 코드와 다르면 "불일치 — 발견"으로 보고.
- **DoD**: 생성기 0 종료 · 모든 관찰값이 `observation_from_dict` 통과 · 케이스 ≥ 16 · ruff.

---

#### T304 — 평가 패키지·결정적 실행기 [Stage 1a]
- **변경 파일**: §4 표.
- **인터페이스**
  ```python
  # kc_eval/schema.py
  SCHEMA = "kc-eval/v1"; SUITES = ("schedule", "gate", "mentions", "judge")
  def load_suite(path: Path) -> dict
  def validate_suite(doc: Mapping) -> list[str]
  # kc_eval/match.py — §5.1 (유일한 비교 규칙)
  # kc_eval/offline.py
  def run_gate(doc) -> dict; def run_mentions(doc, db: Path | None) -> dict
  def run_judge(doc) -> dict; def run_guard(schedule_doc, judge_doc) -> dict
  def main(argv) -> int        # "run" 하위 명령
  ```
  ```
  uv run python eval/kc.py run [--set eval/testset.json] [--drafts eval/drafts] [--suites gate,mentions,judge,guard]
      [--db var/index/kcontext.db] [--out eval/results] [--label NAME] [--check] [--known-failures FILE]
  uv run python eval/kc.py validate [--drafts eval/drafts]     # 모든 drafts 에 validate_suite, 문제 있으면 1
  ```
- **핵심 로직**
  1. `eval/kc.py`: §5.0 의 sys.path 처리, 하위 명령 `run`·`validate`(T304), `stability`(→ `kc_eval.stability`), `snapshot-mentions`, `gen-judge` 는 지연 import.
  2. 세트 선택: `--set` 있으면 그것(`{"schema", "suites": {...}}`, `reviewed: true`), 없으면 drafts(`reviewed: false` + stderr 경고).
  3. gate: `backend.schedule_gate.looks_like_schedule`. mentions: db 없으면 `skipped`, 있으면 `reason` + `top[].article_id` 순서 비교, precision@3(라벨 있을 때). judge: `observation_from_dict` → `build_entries` → `search_events`, §5.1 비교. guard: `understand(text, complete=_boom)`(불리면 AssertionError) + `screen`.
  4. 결과 `eval/results/<label|offline>-<YYYYmmdd-HHMMSS>.json` `{"schema": "kc-eval-result/v1", "reviewed", "git_head", "suites": [...]}`. `git_head` 는 `.git/HEAD` 를 읽어서(실패 시 null).
  5. `--check`: 실패가 있으면 1. `--known-failures FILE` 안의 `` `known-failure: <suite>/<id>` `` 줄은 제외. skip 은 실패 아님.
  6. `tests/eval/conftest.py`: `<repo>/eval` 을 sys.path 앞에. `eval/README.md`: 실행 명령·세트 선택·§6.1 지표·"규칙만으로 통과하는 세트는 회귀 기준" 문구.
- **엣지 케이스**: 모르는 suite → 2. 케이스 예외는 그 케이스 실패(`detail.error` 에 타입 이름만).
- **DoD**: `uv run python -m pytest -q tests/eval/test_kc3_eval_offline.py`(tmp 세트: gate 2·judge 1·guard 1·mentions 는 tmp 색인 합성 청크 2) · `uv run python eval/kc.py run --suites gate,judge,guard` 결과 파일 생성 · ruff.

---

#### T305 — 안정성 측정기 [Stage 1b · T304 뒤]
- **변경 파일**: 신규 `eval/kc_eval/stability.py`, `tests/eval/test_kc3_eval_stability.py`
- **인터페이스**
  ```
  uv run python eval/kc.py stability --suite eval/drafts/schedule.json --layer pipeline|api
      [--runs 3] [--cases id1,id2] [--db var/index/kcontext.db] [--timeout-s 90]
      [--base http://localhost:8000/api] [--out eval/results] [--label baseline] [--cache off|on]
      [--max-calls 210] [--yes]
  ```
  ```python
  OUTCOMES = ("ok", "no_anchors_expected", "fallback_llm", "fallback_unverified", "fallback_chat",
              "schedule_unavailable", "timeout", "error")
  LLM_FAIL_CODES = ("LLM_FAILED", "LLM_EMPTY", "LLM_BAD_JSON", "LLM_UNEXPECTED_SHAPE", "LLM_UNAVAILABLE")
  def classify_pipeline(exit_code, bundle, expect_status) -> str
  def classify_api(status, body, expect_status) -> str
  def summarize(case_runs, cases) -> dict
  def percentile(values, p) -> float | None
  ```
  앵커 비교는 `from kc_eval.match import match_anchors`.
- **핵심 로직**
  1. pipeline 층: backend 와 같은 명령 `[sys.executable, "-m", "domains.kcontext.pipeline", "--text-file", f, "--db", db, "--out", tmp/"out", "--force"]` (+trip), env = **backend 와 같은 허용 목록**(`backend.story_runner._ENV_ALLOW` 와 같은 사본 + `LLM_BACKEND*` — Stage 1 은 제품 코드를 고치지 않으므로 사본을 두고 테스트가 두 목록이 같음을 단언한다. T310 이 목록을 늘리면 그 테스트가 잡는다. D7 ③) + `APP_PROCESS_ROLE=agent` + `KC_SCHEDULE_CACHE=<--cache>`. 현재 env 를 통째로 넘기지 않는다(Stage 1 reviewer 블로커), timeout `--timeout-s`. `out/bundle.json` 에서 앵커·problems.
  2. 분류: timeout → `timeout`; 종료 ≠ 0 → `error`; 앵커 ≥1 → `ok`; 앵커 0 + `LLM_FAIL_CODES` → `fallback_llm`; 앵커 0 + 기대 `no_anchors` → `no_anchors_expected`; 그 밖 앵커 0 → `fallback_unverified`.
  3. api 층: 순차 `POST {base}/messages` `{"text", "context": {"schema": "chat-context/v1", "lang", "trip"}}`(trip null 이면 뺌), 클라이언트 timeout 110초. 200 + `bundle.status == "ok"` → `ok`; 200 + 묶음 없음 + reply 가 고정 문구(T310 의 `SCHEDULE_UNAVAILABLE_REPLY.ko` 와 같음 — 문자열을 이 모듈 상수로 두고 T310 머지 뒤 일치를 테스트) → `schedule_unavailable`; 200 + 묶음 없음 → 기대 `no_anchors` 면 `no_anchors_expected`, 아니면 `fallback_chat`; 429·502·503 → `error`; 클라이언트 timeout → `timeout`.
  4. 실행 기록에 LLM 원문·묶음 전체·reply 를 저장하지 않는다(앵커 요약·문제 코드·ms·좌표 수만).
  5. 결과 `eval/results/<label>-<layer>-<시각>.json` `{"schema": "kc-eval-stability/v1", "label", "layer", "runs", "cache", "git_head", "llm_config_sha256", "model_env", "started_at", "finished_at", "case_runs", "summary"}`.
  6. **호출 상한**: 예상 최대 LLM 호출 = 실행 수 × 2(재시도) (+ api 층은 × 3, 일반 챗봇 포함)이 `--max-calls`(기본 210)를 넘으면 `--yes` 없이 시작하지 않는다.
- **엣지 케이스**: api 층 첫 연결 실패 → 종료 2 "backend 를 먼저 띄운다". db 없음 → 2.
- **DoD**: 테스트(분류·요약·백분위, `subprocess.run` monkeypatch 1회) · `uv run python eval/kc.py stability --help` · ruff.

---

#### T306 — [확인] LLM 호출 파라미터 [Stage 1a · H4]
- **변경 파일**: 신규 `docs/spikes/llm_params.md`(확인 스크립트는 레포 밖 임시 파일)
- **대상**: provider `https://integrate.api.nvidia.com/v1`, 모델 `openai/gpt-oss-20b`. 파라미터 `temperature`(0) · `top_p`(1) · `seed`(7) · `response_format`(`{"type": "json_object"}`) · `reasoning_effort`(`"low"`) · `max_tokens`(1024·4096).
- **방법**: ① build.nvidia.com 의 해당 모델 API 레퍼런스에서 파라미터 목록(URL·확인 날짜). ② 실호출 — system = `domains/kcontext/schedule/understand.py` 의 `SYSTEM_PROMPT`, user = `core.guard.wrap("10/15에 창덕궁 10시, 익선동 2시, 숙소는 종로3가야", source="schedule_text").render()`. 파라미터 하나씩 더해 1회씩: HTTP 상태·`finish_reason`·content 길이·JSON 해석 여부·`usage`. ③ 결정성: temperature 0 단독 / + seed 7 각 5회 → content sha256 앞 12자, "동일 n/5". ④ 지연 ms. ⑤ 결론 표(받아들임·효과 확인 / 받아들임·효과 불명 / 거부(코드) / 미확인).
- **규칙**: 본문·키·응답 원문을 문서에 넣지 않는다 · 호출 ≤ 30.
- **DoD**: 결론 표로 §6.3 S5~S7 조건을 판정할 수 있다("미확인" 허용).

---

#### T307 — 기준선 실행·기록 [Stage 1b · H4 선행]
- **선행 게이트**: H4(크레딧 확인) · `uv run python eval/kc.py validate` 0 종료(T301~T303 형식) · T305 테스트 통과.
- **변경 파일**: `eval/BASELINE.md`, `eval/results/baseline-*.json`
- **실행 (기본 `--runs 3`)**
  1. `uv run python eval/kc.py run --db var/index/kcontext.db --label baseline-offline`
  2. `uv run python eval/kc.py stability --suite eval/drafts/schedule.json --layer pipeline --runs 3 --cache off --label baseline` (기대 ok 케이스 18 × 3 = 54 실행, LLM 호출 ≤ 108)
  3. backend 를 README 대로 띄우고 `--layer api --runs 3 --cases <고정 10개> --label baseline` (30 실행, 호출 ≤ 90)
  - **호출 상한 합계 ≤ 210**(T306 제외). 크레딧이 모자라면 `--runs 2` 로 줄이고 BASELINE 에 사유. 이후 T311·T323 은 같은 구성.
- **BASELINE.md 내용**: 날짜·git head·모델·설정 해시·색인 통계 / §6.1 지표(층별) / 문제 코드 상위 10 / 알려진 실패(`` `known-failure: <suite>/<id>` `` + 이유) / §6.2 목표 표(F0·C0·E0·N 대입 결과) / §6.4 예산 표(L 와 T_llm 계산, 키가 없어 비었으면 기본 예산 표) / S5~S7 켬·끔과 근거 / API 층 고정 10케이스 목록.
- **DoD**: 세 결과 파일과 BASELINE 커밋, 표에 빈칸 없음("미확인" 허용).

---

#### T308 — core/llm 기능별 파라미터 + 설정 값 [Stage 2a]
- **인터페이스**
  ```python
  # config.py
  PARAM_KEYS = ("temperature", "top_p", "seed", "max_tokens", "response_format", "reasoning_effort")
  @dataclass(frozen=True)
  class FeatureConfig: name: str; provider: str; model: str
                       params: Mapping[str, Any] = field(default_factory=dict)   # MappingProxyType 사본
  # feature 키: provider·model 필수 + params 선택. 값 검증: temperature 0..2 · top_p 0<x<=1 · seed 0 이상 int(bool 거부)
  #   · max_tokens 1..32768 · response_format == {"type": "json_object"} · reasoning_effort ∈ {low, medium, high}
  #   모르는 키 → LlmConfigError(키 이름만)
  def load_config(path, env=None, *, check_keys: bool = True) -> LlmConfig   # check_keys=False 면 키 존재 확인 생략
  # client.py — params 가 비어 있지 않을 때만 transport.send(..., params=fc.params). audit call 인자에 "params": 키 이름 목록
  # http_transport.py — send(..., params: Mapping | None = None): body 에 합침. params 의 max_tokens 가 생성자 기본값보다 우선
  ```
- **설정 값**(`deploy/llm.chat.yaml`): `features.schedule: {provider: nvidia, model: "openai/gpt-oss-20b", params: {...}}` — params 는 BASELINE 에서 "켬"인 S5~S7 만(없으면 `params` 키를 쓰지 않음). provider `timeout_s` = BASELINE 예산 표의 `T_llm`. 주석에 근거 문서 경로.
- **엣지 케이스**: `params: {}` 는 빈 것. 기존 fake transport 는 params 인자를 몰라도 된다(빈 params 면 넘기지 않음).
- **규칙**: D3·D5·D6·규칙 1.
- **DoD**: `uv run python -m pytest -q tests/core/llm` · `uv run python -c "from core.llm import load_config; print(sorted(load_config('deploy/llm.chat.yaml', check_keys=False).features))"` → `['chat', 'schedule']` · ruff.

---

#### T309 — 예산 안 재시도 + 결과 캐시 [Stage 2a]
- **인터페이스**
  ```python
  # understand.py
  RETRY_CODES = ("LLM_FAILED", "LLM_EMPTY", "LLM_BAD_JSON", "LLM_UNEXPECTED_SHAPE")
  PROMPT_SHA = sha256(SYSTEM_PROMPT)[:12]
  def understand_with_meta(text, *, complete, trip_from=None, trip_to=None, max_attempts: int = 1,
                           budget_s: float | None = None, attempt_timeout_s: float | None = None,
                           retry_unverified: bool = False, clock=time.monotonic, **기존 키워드) -> tuple[dict, dict]
      # meta {"source": "llm", "attempts": int}
  def understand(...)   # 기존 시그니처·반환 그대로
  # cache.py
  CACHE_ENV = "KC_SCHEDULE_CACHE"   # on(기본) | off
  def key_for(text: str, trip, *, root: Path | None = None) -> str
      # sha256(정규화 JSON{NFKC text, trip, prompt_sha, sha256(deploy/llm.chat.yaml 바이트), SCHEDULE_MODEL or CHAT_MODEL or ""})
  class ScheduleCache:
      def __init__(self, root: Path)                    # 기본 var_dir()/"cache"/"schedule"
      def get(self, key) -> dict | None                 # {"result", "meta", "created_at"}, 손상이면 None
      def put(self, key, result: dict, meta: dict) -> None   # 임시 파일 + os.replace
  # schedule/__main__.py: FEATURE = "schedule"(yaml 에 없으면 "chat"), 모델 덮어쓰기는 dataclasses.replace(fc, model=...)
  # pipeline/run.py: run_story_pipeline(..., max_attempts=2, budget_s=None, attempt_timeout_s=None,
  #                                     cache: ScheduleCache | None = None, cache_key: str | None = None)
  # pipeline/__main__.py: --llm-budget-s (기본 75), --require-llm
  ```
- **핵심 로직**
  1. **재시도(D15 ③)**: 첫 시도 경과 `e` 를 `clock` 으로 재고, 실패 종류가 `RETRY_CODES`(+`retry_unverified` 면 `NO_ANCHOR_VERIFIED`)이고 `budget_s is None or e + attempt_timeout_s <= budget_s` 일 때만 다시 부른다. 재시도마다 `{"code": "LLM_RETRY", "message": "<n>회차 <코드> 후 재시도"}`. 예산 부족으로 재시도하지 않으면 `{"code": "RETRY_SKIPPED_BUDGET"}`. 입력 검증(빈 글·길이·주입)은 재시도하지 않는다.
  2. `attempt_timeout_s` 는 pipeline `__main__` 이 LLM 설정의 provider `timeout_s` 에서 읽는다(`load_config(..., check_keys=False)` 를 T308 이 아직 머지 전이면 `None` — 재시도 조건에서 예산 비교를 생략하지 않고 `budget_s` 만 남은 시간 > 0 으로 본다. T311 전에 두 태스크가 모두 머지되므로 측정은 정식 경로로 한다).
  3. **캐시(D15 ④)**: `KC_SCHEDULE_CACHE != "off"` 이면 이해 단계 전에 `get` → 적중 시 결과 사용, `schedule = {"source": "cache", "attempts": 0, "model": meta.model, "prompt_sha", "cache_created_at"}`. 미적중 → 이해 → `source == "llm"` · 앵커 ≥1 · `RETRY_CODES` 문제 없음일 때만 `put`. 저장 내용은 이해 결과 dict 와 meta 뿐.
  4. **지연 클라이언트**: pipeline `__main__` 의 `complete` 는 첫 호출 때 `_make_complete()` 를 만든다. 만들기 실패(키·설정) → 그 호출이 예외 → `LLM_FAILED`, 문제 `{"code": "LLM_UNAVAILABLE"}` 추가, 종료 0(§6.5 #5). `--require-llm` 이면 지금처럼 시작 시 확인하고 종료 2.
  5. 묶음에 `schedule` 필드(v1 가산). 동작은 §6.5 #1~#5·#7 과 같아야 한다.
- **엣지 케이스**: 캐시 손상 → 없는 것으로 보고 덮어씀. 폴더 생성 실패 → `CACHE_UNAVAILABLE` 후 계속. `max_attempts < 1` → ValueError.
- **fixture 경로**: 회차별 응답 목록 가짜 `complete` + 가짜 `clock`(예산 판정), tmp 캐시, `tests/fixtures/kcontext/sillok/` 로 만든 tmp 색인.
- **규칙**: D15 · D6 · D10 · 지역·장소 리터럴 금지 · 규칙 1.
- **DoD**: `uv run python -m pytest -q tests/domains/kcontext/schedule tests/domains/kcontext/pipeline`(§6.5 #1~#5·#7 각 1 테스트) · 키 있는 환경에서 같은 글로 CLI 두 번 → 두 번째 `schedule.source == "cache"`, 앵커 같음(완료 보고에 기록) · ruff.

---

#### T310 — 시간 예산 정렬 + 실패 시 고정 문구 [Stage 2a]
- **인터페이스**
  ```python
  # story_runner.py
  TIMEOUT_S = 90                                    # §6.4 R
  LLM_BUDGET_S = 75                                 # §6.4 B, 자식에 --llm-budget-s 로 넘김
  _ENV_ALLOW += ("KC_VAR_DIR", "KC_SCHEDULE_CACHE", "KC_SCHEDULE_RETRY_UNVERIFIED")
  # chat.py
  FRONT_LIMIT_S = 100                               # §6.4 F
  SCHEDULE_UNAVAILABLE_REPLY = {"ko": "일정을 지금 정리하지 못했어요. 잠시 뒤 다시 보내 주세요.",
                                "en": "I couldn't organize your schedule right now. Please try again shortly."}
  NO_SCHEDULE_REPLY = {"ko": "일정으로 정리할 항목을 찾지 못했어요.", "en": "I couldn't find schedule items to organize."}
  ```
  ```js
  export const REQUEST_TIMEOUT_MS = 100_000;   // http.js
  ```
- **핵심 로직**: `_story` 의 결과를 §6.5 대로 나눈다. #4·#5·#6 → `SCHEDULE_UNAVAILABLE_REPLY`(LLM 안 부름, audit 에 종류 — 기존 `StoryRunnerError(kind)` 방식, kind 에 `llm_failed` 추가). #3·#7 → 파이프라인 경과 `s` 를 재서 `s + T_llm ≤ FRONT_LIMIT_S − 5` 면 일반 챗봇, 아니면 `NO_SCHEDULE_REPLY`. `T_llm` 은 chat 클라이언트의 provider `timeout_s`(설정에서 읽음). #8 은 지금 그대로. 고정 문구 응답과 그 사용자 문장은 LLM 맥락에 넣지 않는다. 기존 테스트가 80_000·90 을 단언하면 같은 테스트에서 새 값으로.
- **fixture 경로**: `run_story` monkeypatch(각 실패 종류, LLM 실패 코드가 든 묶음, 정상 no_anchors 묶음), 호출되면 실패하는 가짜 transport, 가짜 시계.
- **규칙**: D15 ⑤ · D3·D10 · 규칙 1 · D2.
- **DoD**: `uv run python -m pytest -q tests/backend` · `(cd frontend/k-context && node --test)` · ruff.

---

#### T311 — 재측정·분기 결정 [Stage 2b · H4]
- **핵심 로직**: T307 과 같은 구성(케이스·반복·고정 10케이스)으로 `--label stage2`, `--cache off`. 추가로 기대 ok 3케이스 × 3회 `--cache on` → 변동 0 확인. §6.2 건수 목표와 비교. 미달이면 §6.3 S8~S10 중 원인(문제 코드 분포)에 맞는 것 **하나**를 켜고 같은 측정 1회 더. 그래도 미달이면: (a) 폴백 대부분이 `fallback_llm` 이면 T326 착수를 사람에게 제안(D15 보충 문안 함께), (b) 그 밖이면 원인·케이스 id 와 "다음 스프린트 이월". 목표를 낮춰 적지 않는다. API 층 p95 가 100초를 넘는 실행이 있으면 S11 이월 기록.
- **DoD**: 결과 파일·BASELINE "Stage 2 뒤" 절, 목표 표 줄마다 결론.

---

#### T326 — *[조건부]* 규칙 대체 추출 [Stage 2c]
- **착수 조건**: T311 미달 + 폴백 대부분 `fallback_llm` + 사람이 D15 보충(규칙 대체 허용) 승인.
- **변경 파일**: §4 표.
- **핵심 로직**: `rules.rule_candidates(text, names) -> list[dict]` — 글을 NFKC 후 `[,\n;]`·`" 그리고 "`·`" 다음에 "`·`", then "` 로 조각냄. 조각마다 `names` 중 포함된 가장 긴 이름 1개(없으면 버림), `find_dates` 첫 날짜(없으면 앞 조각의 마지막 날짜), `find_times` 첫·둘째 시각(모호하면 08:00~20:59 후보, 없으면 첫 값), `_HOTEL_WORDS` 있으면 hotel, quote = 조각(200자 초과면 버림). 결과는 기존 `_clean_candidate`·`_build_anchor`·`_free_slots` 를 그대로 통과. §6.5 "(T326 시)" 행: LLM 실패(#4·#5) 뒤에만, 앵커 ≥1 이면 `source: "rules"`, 문제 `RULE_FALLBACK`, 캐시 안 씀, backend 는 정상 묶음으로 응답. `names` 는 pipeline 이 `PlaceBook` 의 이름·별칭. `KC_SCHEDULE_RULES=off` 로 끔.
- **DoD**: 새 테스트 + 재측정 1회(T311 과 같은 구성) 결과를 BASELINE 에.

---

#### T313 — backend v2 수용 + 행사 근거 + env 전달 [Stage 3 · 머지 1 · T310 머지 후]
- **인터페이스**
  ```python
  # story_runner.py
  BUNDLE_SCHEMAS = ("kc-chat-bundle/v1", "kc-chat-bundle/v2")
  _ENV_ALLOW += ("KC_ROUTE_PROVIDER", "KC_OSM_ROUTER_URL", "KC_ROUTE_ESTIMATE_APPROVED")
  # chat_story.py
  MAX_ROUTES = 7; MAX_LEGS = 20; MAX_RATIONALE = 100; MAX_CHIPS = 8; MAX_ROWS = 12
  def clean_bundle(raw) -> dict             # v1 그대로 + v2 필드 모양 확인·상한, 틀린 v2 필드만 버리고 FIELD_DROPPED
  def event_rationale(search: Mapping) -> dict[str, dict]   # 키 "event:<id>"
  def attach_events(bundle, trip, search) -> None             # 성공 시 bundle["events_rationale"] 도 채움
  ```
- **핵심 로직**: `clean_bundle` 은 `routes`·`rationale`(키가 `mention:` 로 시작하는 것만)·`schedule`(허용 키만)·`story_routes_note` 확인. `event_rationale` 은 검색 결과 JSON 값만으로: `avail`(availability 별 고정 라벨 + matching_dates 행), `src`(links 등급, C 면 "검색 수집 · 미확인"), `funnel`("수집 {events+excluded}건 중 {events}건 남김" + excluded 사유별 개수), `interest`(일치 있을 때), `coverage`(coverage.note). 값의 `card_id` 도 `event:<id>`. 영어는 고정 번역. 묶음이 v1 이어도 `events_rationale` 은 붙인다(프론트 v1 검증기는 무시 — 머지 1 시점에 안전).
- **엣지 케이스**: events None → `events_rationale` 없음. 문자열 아닌 id → 건너뜀.
- **규칙**: D3·D10 · D17 · D12.
- **DoD**: `uv run python -m pytest -q tests/backend` · ruff.

---

#### T314 — 프론트 v2 수용·경로·근거 표시 [Stage 3 · 머지 1]
- **인터페이스**: `api/bundle.js` — `BUNDLE_SCHEMAS = ['kc-chat-bundle/v1', 'kc-chat-bundle/v2']`, `MAX` 에 routes 7·legs 20·rationale 100·chips 8·rows 12. `validateChatBundle` 결과에 `schedule|null`, `routes[]`, `rationale{}`, `events_rationale{}`, `story_routes_note|null`. v2 필드 하나가 틀리면 그 필드만 비움(v1 필드가 틀릴 때만 `ok:false`). 근거 맵은 키 접두어(`mention:`·`event:`)가 맞는 것만 남긴다.
- **핵심 로직**
  1. `map/route-list.js`: 묶음이 있으면 A·B·C 탭 대신 날짜별 "이동 구간": `{from} → {to}` · "직선거리 {straight_m}m" · `walk_min` 있으면 "도보 {n}분"(+`estimated` 면 "예상"), 없으면 "이동시간 확인 필요" · skipped · 아래 `story_routes_note`.
  2. `map/chat-layer.js`: 같은 날 이웃 핀 사이 점선 + 라벨 "직선 연결(실제 길 아님)" 데이터(SVG 렌더러). 카카오 렌더러 쪽은 T318.
  3. `rationale/index.js`: 묶음이 있으면 숨기지 않고 선택 항목이 언급 카드면 `rationale["mention:"+id]`, 행사면 `events_rationale["event:"+id]`. 없으면 "이 카드의 판단 근거 없음". 서버 호출 없음. 묶음이 v1 이면 지금처럼 숨김.
  4. `cards/bundle-view.js`·`timeline/bundle-view.js`: `schedule.source` 가 `cache` → "이전 결과 재사용 ({cache_created_at})", `rules` → "규칙으로 정리(장소 사전 이름만)".
- **엣지 케이스**: v1 묶음 → 경로 영역 "이동 구간 정보 없음", 근거 숨김(머지 1 직후 상태). textContent 만.
- **규칙**: D17·D18 · 프론트 소유 규칙 · 색만으로 구분하지 않음.
- **DoD**: `(cd frontend/k-context && node --test)` 건수 증가(v1·v2·틀린 v2 필드·접두어 테스트) · 머지 1 직후 수동: 실제 서버 일정 문장이 지금과 같이 그려진다.

---

#### T317 — 묶음 계약 문서 v2 [Stage 3 · 머지 1]
- §5.2(id 접두어 포함)·§6.4 예산·§6.5 동작 표를 `docs/chat-bundle.contract.md` 로 옮기고 "구현 메모"의 90초·폴백 서술을 고친다. 결정 번호는 승인된 것만.
- **DoD**: 필드 목록이 §5.2 와 같다(reviewer).

---

#### T312 — 파이프라인 v2(생산) [Stage 3 · 머지 2 — 마지막]
- **인터페이스**
  ```python
  # rationale.py
  def mention_rationale(card_id: str, row: Mapping, mention: Mapping, excluded: int) -> dict   # card_id 는 "mention:<id>"
  # legs.py
  def build_routes(anchors: Sequence[Mapping], *, provider: RouteProvider) -> list[dict]
  # run.py
  BUNDLE_SCHEMA = "kc-chat-bundle/v2"
  run_story_pipeline(..., route_provider: RouteProvider | None = None)   # None → geo.chain.make_route_provider(os.environ)
  ```
- **핵심 로직**
  1. 근거(카드마다, 키 `mention:` + 최종 카드 id): 고정 템플릿 + 데이터 값. `match`("검색어 일치: {matched_term}", rows: terms·일치 위치(title→"한국사DB 한글 요약 제목", body→"원문 본문")·별칭 여부), `pick`("후보 {found_articles}건{ 이상} 중 선택", rows: 후보 수·200 상한 여부·주입 검사 제외 수), `src`("출처 등급 {tier} · 국역 없음", rows: 출처 이름·locator·date_label 그대로·링크 유무·collected_at), `scope`(text = `COVERAGE_NOTE`). LLM 없음, 새 문장 없음.
  2. `excluded` = `mention_out["problems"]` 중 `excluded_by_screen` 이고 같은 anchor 인 수.
  3. 이동 구간: 방문 앵커 중 `from` 있는 것을 날짜별·시각순, 이웃 쌍마다 둘 다 좌표 → `straight_m`(`geo/distance.py` 의 haversine), `ChainRouteProvider` 면 `begin()` 후 `minutes`·`.name`·`.estimated`, `NullRouteProvider` 면 `walk_min: null`·`provider: "none"`. 좌표 없음 → skipped "좌표 없음", `from` 없는 방문 → skipped "시각 없음"(`to` 빈 문자열). 같은 장소 연속 → 0m·0분·`provider: "same_place"`. 숙소 제외. id `day{n}`.
  4. `routes`·`rationale`·`story_routes_note` 추가, schema v2.
- **규칙**: D16(승인 전 기본 공급자 none) · D18 · D10 · 지어내기 금지 · 지역 리터럴 금지.
- **DoD**: `uv run python -m pytest -q tests/domains/kcontext/pipeline` · CLI 가 v2 묶음, rationale 키 = `mention:`+카드 id · ruff · **머지는 T313·T314 머지 뒤**.

---

#### T315 — *[조건부 H7]* 장소 사전 동기화 [Stage 3 이후 언제든]
- **착수 조건**: H7 이 `demo_places.json` 에 항목을 더했거나 더할 예정.
- **핵심 로직**: `scripts/sync_chat_places.py [--check]` — `load_places()` 의 이름+별칭을 정렬·중복 제거해 `backend/fixtures/chat_places.json` 에 `{"names", "generated_from", "note": "생성물 — 손으로 고치지 않는다"}`. `--check` 는 다르면 1. 테스트가 같은 비교. `data/places/README.md` 에 항목 형식·"사람이 확인한 좌표만"·4개 구 안·추가 뒤 스크립트 실행.
- **DoD**: `--check` 0 · 테스트 · ruff.

---

#### T316 — *[조건부 H8]* 한글→한자 별칭 적재 [Stage 3 이후 언제든]
- **착수 조건**: H8 데이터가 오거나 오기로 확정.
- **인터페이스**: `aliases.py` — `AliasEntry(ko, hanja, source, verified_at, note="")`, `load_alias_file(path)`(필수 키, 한자는 CJK 통합 한자 3자 이상, 중복 거부), `to_place_aliases(entries)` → `PlaceAlias(alias=ko, place=hanja, lang="ko", region=None, source=f"manual:{source}")`. CLI `uv run python -m domains.kcontext.index aliases --db ... --file domains/kcontext/data/places/aliases.json [--dry-run]` → `{"entries", "upserted"}`.
- **규칙**: 값은 사람 확인분만(dev 는 `[]` 만 커밋) · 색인 쓰기는 호스트 CLI(D7).
- **DoD**: 테스트(upsert 후 `expand_place(ko)` 에 한자) · `--dry-run` 0 · ruff.

---

#### T318 — 실제 모드에서 예시 데이터 끄기 + 보안 로그 실연결 [Stage 4]
- **인터페이스**
  ```js
  export const HTTP_METHODS = ['getMessages', 'sendMessage', 'getAuditLog', 'decideAudit'];
  DATA_KINDS.chat = DATA_KINDS.http = { itinerary: 'empty', routes: 'empty', cards: 'empty', sources: 'empty',
                                        rationale: 'bundle', messages: 'server', audit: 'server' };
  // chat·http 모드: getItinerary → {anchors: [], free_slots: [], timeline: [], landmarks: []},
  //   getRoutes/getCards/getSources → [], getCard·getRationale → reject(code 'not_found')
  // http.js: getAuditLog() GET /audit, decideAudit(id, decision) POST /audit/{id}/decision {decision} (신원 없음)
  ```
- **핵심 로직**: `selectors.mockRegions` 에서 `empty`·`bundle`·`server` 는 MOCK 아님. 실제 모드 + 묶음 없음 → 빈 상태 문구(i18n). backend 에 닿지 못하면(명시 chat·http 모드) 오류 상태 문구 — **의도된 변화**(Stage 4 게이트). `myLocation` 은 실제 모드에서 그리지 않음(`map/index.js`·`kakao-view.js`), 카카오 렌더러에 T314 의 이동 구간 점선. `topbar.js` `screenStatus` 에 `'empty'`("실제 서버 · 일정 대기"). 보안 로그는 `loadAll`·메시지 전송 뒤 `getAuditLog`, 결정 버튼은 서버 `pend` 만. `actions.loadAll` 은 실제 모드에서 `getCard`·`getRationale` 를 부르지 않음. 기존 단언은 같은 테스트에서 고친다. 새 `tests/realmode.test.js`: MOCK 딱지 0, 빈 상태, `GET /audit`, decide 본문 `{decision}` 뿐, backend 연결 실패 시 오류 상태.
- **엣지 케이스**: `?api=mock` 과 `auto`+backend 꺼짐은 지금과 완전히 같다(회귀 테스트).
- **규칙**: D17·D18 · D2 · `?api=mock` 유지.
- **DoD**: `node --test` 건수 ≥ 직전 · 수동: backend 연결 시 첫 화면 MOCK 0, 보안 로그 `audit:` 만.

---

#### T319 — 카탈로그 대상 지역을 여러 구로 [Stage 4]
- **지역 id 를 쓰는 곳 전부(코드 확인)**: `catalog/api.py:103-104`(`region_id = os.environ.get("KC_TARGET_REGION", "jung")`, `load_regions()[region_id]` → `admin_report_decide`·`admin_refresh`(`make_fetcher(region=)`)에 전달) · `catalog/__main__.py:32`(`TARGET_REGION`), `:41-44`(`_setup` 의 `regions.get(args.region)`), `:74`(`--region` 기본값) · `catalog/web_events.py:75`(`if r.region != region.id`). 그 밖은 Region 객체를 받아 `region.gu`·`bbox` 만 쓴다(`rules.classify_venue` ← `seoul.py`·`web_events.py`·`reports.py:120`) — 고칠 필요 없음. backend 는 `catalog_runner._BASE_ENV` 로 env 이름만 넘긴다(변경 없음).
- **인터페이스**
  ```python
  # target.py — "+" 분해 규칙은 여기 한 곳에만
  ENV = "KC_TARGET_REGION"          # 쉼표 목록: "jung,jongno,mapo,gangnam". 없으면 "jung"
  def target_region(spec: str | None = None, regions: Mapping[str, Region] | None = None) -> Region
      # 하나 → 그 Region. 여럿 → id "+".join(정렬 id), name 각 이름을 "·" 로, gu 합집합(순서 유지),
      # bbox·center None, keywords 합집합, sillok_keywords (). 모르는 id·빈 문자열 → ValueError
  def region_ids(region: Region) -> tuple[str, ...]
  ```
- **핵심 로직**: 위 세 파일의 해당 줄을 `target_region(...)`·`region_ids(...)` 로 바꾼다(`web_events.py:75` → `r.region not in region_ids(region)`). `.env.example` 에 `KC_TARGET_REGION=jung,jongno,mapo,gangnam` 예시. 합친 Region 은 `load_regions()` 결과에 넣지 않는다.
- **규칙**: 지역 리터럴 금지 · D13 ② · D7.
- **DoD**: 새 테스트(하나·여럿·모르는 id·서울 합성 행 4개 구 판정·웹 레코드 거르기) · 기존 카탈로그 테스트 · ruff.

---

#### T320 — 강남 검색 수집 출처 [Stage 5a · T319 뒤]
- **범위 축소 근거**: 마포는 실측(`docs/spikes/web_search.md` §5)에서 후보 0건이라 뺀다. 서울 열린데이터광장 API 는 `GUNAME` 으로 4개 구를 이미 덮으므로(키 H5 필요) 검색 수집은 보조다.
- **인터페이스**: `catalog_sources.json` 의 선택 키 `"web_source"` — `junggu_site` 에 `"junggu"`, 새 `gangnam_site`(`method: "search"`, `status: "partial"`, `env_keys: ["TAVILY_SEARCH_KEY", "TAVILY_API_KEY"]`, `"web_source": "gangnam"`, url = `data/web_sources/gangnam.json` 의 `allow_url_prefixes[0]`, notes 는 junggu_site 형식). `sources.py` 허용 키에 `web_source`, `make_fetcher` 가 `web_source` 가 있으면 그 id 로 web fetcher. `web_events.default_events_file(web_source_id)` → `var/data/events/web.<id>.jsonl`(junggu 는 기존 `web.jsonl` 도 읽음).
- **엣지 케이스**: `web_source` 파일 없음·`status != confirmed` → `SourceError`(D12 ①).
- **규칙**: D12 전부 · 구 이름 리터럴 금지.
- **DoD**: 새 테스트(합성 강남 web 레코드 → 관찰값, 합친 Region 거르기) · 기존 테스트 · ruff.

---

#### T321 — 행사 수집 실행·검증 보고 [Stage 5b]
| 조건 | 실행 |
|---|---|
| A. `SEOUL_OPENAPI_KEY` 있음(H5) | `KC_TARGET_REGION=jung,jongno,mapo,gangnam uv run python -m domains.kcontext.catalog --region jung,jongno,mapo,gangnam update --source seoul_openapi` 1회 |
| B. Tavily 확인(H6) | `junggu`·`gangnam` 각각 `uv run python -m domains.kcontext.ingest.events.web_run --source <id> --month <달> --out var/data/events/web.<id>.jsonl --collected-at <오늘> --max-calls 10 --max-candidates 10` → `catalog --region <4개> update --source <id>_site` |
| A ∧ B | A 다음 B |
| 둘 다 없음 | 실행 안 함. 보고서에 "0건 — 키 없음"과 화면이 0건을 사실대로 보이는지 |
- **보고서**: 날짜·명령(키 값 없이)·호출 수 / `catalog status` 요약 / 구별 × 출처별 항목 수, 검증 상태 수, `in_target` unknown 수 / 사람 확인용 무작위 5건 표 / 문제 상위 사유 / "모든 행사가 아니다".
- **규칙**: D7·D12·D13 · 규칙 1 · 서울 한도 확인 전 1회만.
- **DoD**: 보고서 + 실제 서버 확인 1회 기록.

---

#### T322 — *[조건부 D19]* 데모 스냅샷 [Stage 5b]
- `scripts/snapshot_catalog.py --from var/catalog --to domains/kcontext/data/snapshots/catalog`: 관찰값 중 `evidence.source_id == "seoul_openapi"` 만 남기고 `build_entries` 로 다시 묶어 저장, `SNAPSHOT.md`(출처·공공누리 1유형·수집일·건수). `--restore`(기존 폴더 있으면 거부, `--force` 교체).
- **DoD**: 테스트(검색 수집 관찰값 제외, 되돌리기) · ruff.

---

#### T323 — 재측정·회귀 기준 확정 [Stage 5c · H4]
- T307 과 같은 구성, `--label final`. H7·H8 데이터가 들어왔으면 별칭 적재 후 `snapshot-mentions --out eval/drafts/mentions.aliases.json` 로 전·후 비교(no_match·found_articles 합·잘림·precision@3), 좌표 부착률 비교. **H7·H8 이 없으면 T311 측정의 재실행으로 대체**(같은 구성, 라벨 final). `eval/testset.json`(H10)이 있으면 그것으로도 돌려 "검수된 기준선" 표시.
- **DoD**: BASELINE "최종" 절에 Stage 1·2·최종 비교 표, 남은 미충족·이월.

---

#### T324 — 데모 스크립트 + E2E (Sprint 2 T221 재사용) [Stage 6]
- **`scripts/kc_demo.sh`**: `set -euo pipefail`. `--check` 는 점검만: `uv` 있음, `var/index/kcontext.db` 있음(없으면 ingest 명령 안내 후 1), `NVIDIA_API_KEY` 가 셸 env 또는 `.env` 에 **있음/없음만**, `var/catalog` 없음 + 스냅샷 있음 → 복원 안내(`--restore-snapshot` 일 때만 실행). 기본: `KC_TARGET_REGION=jung,jongno,mapo,gangnam` 으로 backend(8000)·정적 서버(8766) 백그라운드, URL 두 개(실제·`?api=mock`), `trap` 정리. env 를 echo 하지 않는다.
- **E2E (`tmp_path`, LLM 없음)**: ① 픽스처 XML 을 `ingest.sillok` 으로 tmp 색인 ② 데모 문장·trip 의 `key_for` 로 손으로 쓴 합성 이해 결과(앵커 3)를 tmp 캐시에 `put` ③ `KC_VAR_DIR` 설정, `CHAT_MODEL`·`SCHEDULE_MODEL`·`NVIDIA_API_KEY` 제거, `create_app(Settings(... reviewer_id="human:e2e", index_db=tmp, catalog_dir=빈 tmp))` + TestClient → `POST /api/messages` → v2 묶음, `schedule.source == "cache"`, 앵커 3, `set(rationale) == {"mention:"+c.card.id}`, `routes[0].legs[0].from == "창덕궁"`, `events.events == []` ④ 파일 읽기 요청 → `blocked`, logs 에 deny ⑤ 사람 승인(T221 6단계: hitl draft → `GET /api/audit` pend → approve → `decided_by == "human:e2e"`, 재전송 409, 본문 `decided_by` 422 — draft 쓰기 함수는 `core/hitl` 공개 API 에서 확인) ⑥ `domains.kcontext.pipeline` 이 테스트 프로세스에 로드되지 않음.
- **DoD**: E2E 통과 · `bash scripts/kc_demo.sh --check` 0 · 전체 회귀.

---

#### T325 — README·상태 문서·다이어그램 HTML [Stage 6]
- README "지금 상태"를 측정값으로(BASELINE 최종 링크, 행사 보고서 링크, 실제 모드 MOCK 0), 남은 한계(좌표 수·별칭 수·이야기 길 없음 D18·이동시간 공급자). "평가 절차"에 `eval/kc.py run`·`stability` 명령. "실행"에 `scripts/kc_demo.sh`·환경변수 이름 추가·스냅샷 복원(D19 시). "기능별 데모"에 H12 촬영 장면 목록: ① 일정 문장 → 타임라인·핀·이동 구간·근거 ② 같은 문장 재요청 → 이전 결과 재사용 ③ 공격 프롬프트 → 서버 보안 로그·사람 승인 ④ 4개 구 행사 카드 ⑤ `?api=mock`. 새 상태 문서(옛 문서와 같은 표 구조, D14·D15~D19 상태). `system-state.html` 을 실제 흐름으로 고친다(**PNG 캡처는 H12**).
- **DoD**: README 명령이 실제 파일·옵션과 맞다(reviewer 대조).

---

## 9. 이번 스프린트에서 의도적으로 하지 않는 것
- SCOPE "지금 안 만들 것" 전부.
- 경로 A·B·C(D18), 이야기 판정 평가, 이야기 문장(narration), 스트리밍(S11), 벡터 검색, TourAPI, 일정 서버 보관(D17), Nemotron 으로 모델 교체(안정성 기준선이 gpt-oss-20b 기준).
- 마포 검색 수집(실측 후보 0건 — 서울 API 로 덮음).
- 규칙 대체 추출은 T311 결과에 달린 조건부(T326).

## 10. 이월 규칙
| 대상 | 규칙 |
|---|---|
| 필수 태스크 | 이월하지 않는다. 키가 없어 실행 못 한 측정·수집은 "실행 대기 — H번호"로 기록하고 코드·문서는 끝낸다 |
| 조건부(T306·T315·T316·T322·T326) | 조건이 안 되면 "S4 이월 — 사유: <조건>" |
| Sprint 2 이월 | T222 계속 이월(엔진 미구동, H13) · T223 transport 해소, 추출 보조는 계속 이월 · T224 계속 이월(에이전트화와 함께) · T212 D18 로 이월 · T220 → T303·T304 로 완료 처리 · T221 → T324 로 완료 처리 |
| Sprint 1 이월 | S1-T202-opt·S1-T302·S1 hitl W1·W2·S1 T303 W1~W9 계속 이월 |

---

## dev 평가 반영 내역
| # | 지적 | 반영 |
|---|---|---|
| 1 | 시간 예산 공식이 runner 140초·프론트 155초를 내고 `T_llm` 상한이 고정 | §6.4 를 프론트 100초에서 거꾸로 계산(R 90 · B 75 · T_llm 은 B 안에서 기준선으로), 재시도는 남은 예산 안에서만. D15 ②③ 에 넣음. 키 없을 때 기본 예산 표(T_llm 45) |
| 2 | T309↔T310 상호작용이 불명확, D15 ③⑤ 모순 | §6.5 동작 표(캐시 × LLM 결과 → source·앵커·종료 코드·응답). D15 에서 규칙 대체를 빼고 ⑤ 를 "LLM 실패 → 고정 문구 / 일정 아님 → 예산 안에서 일반 챗봇"으로 정리 |
| 3 | eval import 경로가 갈림 | §5.0: `eval/kc_eval/` 하나, 입구 `eval/kc.py`, 테스트는 `tests/eval/conftest.py` 의 sys.path, `eval/__init__.py` 없음. 비교 규칙은 `match.py` 하나. T305 를 1b(T304 뒤)로 |
| 4 | rationale·events_rationale id 공간 | `mention:`·`event:` 접두어 규칙(§5.2) |
| 5 | Stage 3 머지 순서 | 수용(T313·T314·T317) 먼저, 생산(T312) 마지막. 게이트에 "머지 1 직후에도 v1 으로 정상" 확인 |
| 6 | D15 승인 시점 | Stage 1 게이트 항목(Stage 2 착수 조건) |
| 숨은 의존 | T302 앵커 입력 | regions keywords + 장소 사전 5곳으로 고정, T301 은 그 이름만 |
| | T306 의 케이스 id 참조 | 문장을 직접 적음 |
| | T301 DoD | 로드·개수까지, `validate` 는 T307 선행 게이트 |
| | T307 | 기본 `--runs 3`, 호출 상한 210, H4 선행 |
| | T311 목표 | 반복·케이스 고정, 건수 기준(§6.2, 정답 일치 노이즈 허용 2건) |
| | T319 | catalog 안 지역 id 사용처 전부 목록, `"+"` 분해는 `target.py` 한 곳. 같은 파일을 쓰는 T320 은 Stage 5 로 |
| | T318 | backend 꺼짐 시 빈 상태·오류 상태를 Stage 4 게이트에 의도된 변화로 |
| | T313 | 선행에 "T310 머지 후" |
| | 훅 | §0.2 에 `ruff --fix` 안내 |
| 범위 축소 | 규칙 대체 | Stage 2 에서 빼고 조건부 T326. S8~S10 은 T311 결과로 |
| | T320 | 강남 하나로. 서울 API 가 4개 구를 덮음을 명시 |
| | T315·T316 | H7·H8 데이터가 올 때 실행하는 조건부 |
| | T323 | H7·H8 없으면 T311 측정 재실행으로 대체 |
| | T325 PNG | H12(GIF)와 합쳐 사람 작업 |
| 사실 갱신 | 색인 있음(45MB, 10/7)·`.env` 에 키 항목·크레딧 미확인 | §0.1·H4 |
| | H1 | 코디네이터가 사용자 확인 후 처리 |
| | H5 | "지금 바로 요청" |

## 이월
(스프린트 종료 시 `/done` 이 기록한다)

---


### Stage 2 에서 이월 (2026-10-09)
- **변동 목표 미달**(파이프라인 7 > 4, API 4 > 2, S5+S8): 원인은 low 추론에서 회차마다 앵커 일부를 놓치는 재현율 흔들림(ampm_01·pm_01·header_01·outdict_01·long_01·en_basic_01·en_list_01). 조치: H10 검수 뒤 같은 구성으로 재판정, 그래도 미달이면 다음 스프린트. 목표는 낮추지 않는다. D15 보충.
- **W5** 성공 경로의 행사 검색 시간(`attach_events`)이 §6.4 예산 밖 → T313 에서 남은 시간으로 한도.
- **W9** `schedule` 필드가 backend 를 모양 검증 없이 통과 → T313 v2 수용 때 검증.
- **W7** 캐시 키에 `LLM_BACKEND*`·주입 규칙 버전 없음 → 다음 결정 보충 때 검토.
- **key_wait 명시 인자화**: `understand_with_meta` 가 `complete.key_wait_s` 를 duck typing 으로 읽음(래퍼가 끼면 조용히 0 — fail-open). T312 에서 `run.py` 를 고칠 때 `key_wait: Callable[[], float] | None` 명시 인자로 바꾸고 예외 시 보수값.
- T326(규칙 대체): 착수 조건(폴백 대부분 `fallback_llm`) 불성립 — 폴백 0. 착수하지 않음.

## 완료 기록
(스테이지마다 `/stage` 가 기록한다)

### Stage 1 — 기준선 측정 (2026-10-09, 커밋 `9ea6e5e`)
- 착수 전 기준선(§0.1 실측): pytest 1,644 · node 312 · ruff 통과 · 색인 7,713 청크(fts) · `.env` 키 항목 있음. 계획 커밋 `fb46d92`(브랜치 `sprint-3`).
- 태스크별 파일
  - T301 `eval/drafts/schedule.json`(20) · `gate.json`(24)
  - T302 `eval/kc_eval/snapshot_mentions.py` · `eval/drafts/mentions.json`(13, 언급 있는 앵커 4 · no_match 9)
  - T303 `eval/kc_eval/gen_judge.py` · `eval/drafts/judge.json`(23)
  - T304 `eval/kc.py` · `eval/kc_eval/{__init__,match,schema,offline}.py` · `eval/README.md` · `tests/eval/{conftest,test_kc3_eval_offline}.py`
  - T305 `eval/kc_eval/stability.py` · `tests/eval/test_kc3_eval_stability.py`
  - T306 `docs/spikes/llm_params.md`(호출 25)
  - T307 `eval/BASELINE.md` · `eval/results/baseline-{offline,pipeline,api}-*.json`(실호출 약 85, 429 없음)
  - reviewer 수정: `eval/kc_eval/meta.py` 신규, stability 자식 env 허용 목록화(D7), run_mentions 임시 사본
- 회귀: pytest 1,668 passed · node 312 · ruff 통과 · `kc.py validate` 0 · `kc.py run --check --known-failures eval/BASELINE.md` 0 (gate 22/24 known-failure 2 · mentions 13/13 · judge 18/18 · guard 7/7)
- reviewer: 1차 FAIL(블로커 1 — 측정기가 셸 env 전체를 자식에 전달, D7 ③) → 수정 후 PASS
- 기준선 요약: 파이프라인 폴백 2/54 · 변동 케이스 8/18 · 일치 35/54 · p95 27.1s / API 폴백 1/30 · 변동 4/10 · 일치 17/30 · p95 46.6s → T_llm 40s
- **Stage 2 착수 조건 미충족: D15 사람 승인 대기**
