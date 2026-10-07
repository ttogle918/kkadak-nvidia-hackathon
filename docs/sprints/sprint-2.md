# Sprint 2 — 데이터 → 판정 → 화면 연결 (확정본)

> 상태: **확정**(pm, 2026-10-07). 초안 `docs/sprints/sprint-2.draft.md` 에 dev 현실성 평가를 모두 반영했다. 초안은 기록용으로 그대로 둔다.
> 시간 상자: 2026-10-07~ (하루~이틀). 소요 시간은 추정하지 않는다.
> 범위 근거: `docs/SCOPE.md` "Sprint 2 범위"의 "반드시 만들 것" 1~7. "지금 안 만들 것"(여행 기록·사진 정리, 샌드박스 이미지·Brev 배포, 데모 지역 밖 자료)은 어떤 태스크에도 넣지 않았다.
> 태스크 ID: `T2{순번}`. Sprint 1 태스크는 **`S1-T202`** 처럼 접두사를 붙여 부른다.
> 방침: **빠르게.** 필수 경로를 "화면에 나오는 경로" 중심으로 줄였다. 화면 경로에 필요 없는 것은 선택으로 내리거나 이월했다.

## Sprint 2 최종 실행 계획

| 스테이지 | 태스크 | 병렬 | 예상 결과물 |
|---|---|---|---|
| (완료) | T213 map · T214 cards+rationale · T215 chat+timeline+securitylog | — | 프론트 모듈 3묶음 **구현 완료(미커밋)**. `node --test` 129건·ruff 통과. 잔여 4건은 T219 로 옮겼다(§4.0) |
| Stage 1 — 바닥 | **[필수]** T201 계약 · **[필수]** T202 색인 · **[필수]** T203 지역 · **[필수]** T207 승인 API · *[조건부 H1]* T204 실록 확인 · *[선택]* T205 행사 API 1쪽 · *[선택]* T206 도보 경로 1쪽 · *[선택·이월]* T208 정책 초안 제출 | 전부 병렬(소유 경로가 서로 다름) | 계약 검증기(py + js 공통 예제), FTS 색인, 지역 설정·`var/`, backend 승인·보안 로그 API, (H1 이 있으면) 실록 확인 문서·발췌 fixture |
| Stage 2 — 수집·판정·경로 | **[필수]** T210 행사 정규화(normalize·store·manual) · **[필수]** T211a 이야기 판정 · **[필수]** T211b 행사 판정+주입 차단 · **[필수]** T212 도보·경로 · *[조건부 H1]* T209 실록 수집 · *[선택]* T210-fetch | 전부 병렬 | 행사 JSONL, 판정 결과, 경로 JSON, (H1) 색인에 실록 청크 |
| Stage 3 — 조립 1 · 화면 API | **[필수]** T216a 후보 수집·판정·옛날 카드 · **[필수]** T218 backend 화면 API · **[필수]** T219 http.js 연결 + 프론트 잔여 · *[선택]* T217 MCP 도구 | 전부 병렬 | 옛날 카드·근거 패널 조립, `/api/*` 전체, http 모드, 지도 "예상"·geo 투영 보정 |
| Stage 4 — 조립 2 | **[필수]** T216b 경로·일정 맞추기·`kc-bundle/v1` 쓰기 | 단독 | `python -m domains.kcontext.pipeline.run` 이 묶음을 쓴다 |
| Stage 5 — 통합 | **[필수]** T221 끝까지 E2E·데모 스크립트 · *[선택]* T220 평가 세트 | T221 ∥ T220 | 고정 자료로 끝까지 도는 테스트, `scripts/kc_demo.sh`, (선택) `eval/run_kcontext.py` |

- **필수 경로**: T201 계약 → T202 색인 → T203 지역 → T207 승인 API → (T209 실록: H1 있을 때만) → T210 행사(normalize·store·manual) → T211a/b 판정 → T212 도보·경로 → T216a → T216b 파이프라인 → T218 backend 화면 API → T219 http.js 연결+잔여 → T221 E2E. (화살표는 계획 순서이고, 실제 선행 관계는 §1 그래프를 따른다.)
- **선택**: T205·T206(확인 문서 1쪽씩), T208(Sprint 1 이월), T210-fetch(`fetch.py`), T217(MCP 도구), T220(평가 세트).
- **스프린트에서 제외·이월**: T222(실제 도보 공급자) · T223(LLM transport·추출) · T224(판단 규칙 스킬). 명세는 초안 §8 에 남아 있고, 다음 스프린트에서 다시 계획한다(§7).
- **키 없이 끝까지**: 모든 필수 태스크에 fixture 경로가 있다. 키·인증·데이터 파일이 없어도 T221 까지 녹색이 된다. 실데이터는 사람 선행이 풀리면 같은 명령을 다시 돌려 붙인다.

## 사람 선행 항목

### 시작 전에 반드시 (이 다섯 개가 끝나야 `/stage 1`)

| # | 할 일 | 막는 것 | 비고 |
|---|---|---|---|
| 1 | **결정 반영**: D7(§2 새 문안)·D8·D10 을 승인해 `docs/DECISIONS.md` 에 추가. D11 은 **사후 승인**(지도 SVG 투영은 이미 구현됨) | D8 → T202 · D10 → T216a/b·T218 · D7 → T210 · D11 → 기록 정합 | D9 는 Stage 2 의 T212 전까지(§2) |
| 2 | **계약 3.3 보충 수정**: `docs/AGENT_CONTEXT.md` 3.3 에 좌표 `[lat,lng]`, `geometry.space`, 카드·경로 확장 필드, `narration: null`, `route.estimated`, `segments[].coords` 를 넣는다 | T201 의 확장 필드 처리 · T216a/b · T219 | 문안 초안은 §2.2 에 있다(pm 제공). 그대로 붙여도 되고 고쳐도 된다 |
| 3 | **policy.yaml 처리 결정**: ① 현재 working tree 에 사람이 추가한 `kakaomap_mcp`(`[미실측]`, 샌드박스 미적용, 로그 미확인, binaries 는 python3.12 가정)를 **커밋할지** 정한다 — 규칙 2("허용을 추가하면 실측을 주석에 남긴다")와의 정합 ② **카카오 호출 위치의 의도**를 정리한다 — 호스트 수집기(D9·T222, 이번 스프린트 제외) 쪽인지, 샌드박스 안 에이전트가 policy 항목을 통해 부르는 쪽인지 | 커밋 기준선(#5) · 다음 스프린트 T222 재계획 | Sprint 2 코드는 이 항목에 의존하지 않는다(D7 새 문안) |
| 4 | **H1 실록 XML 배치**: 이미 data.go.kr 에서 받은 "국사편찬위원회_조선왕조실록 정보_실록원문"(공공누리 1유형) XML 을 `domains/kcontext/data/raw/sillok/` 에 둔다. 내려받은 날짜·페이지 URL·이용허락 문구를 T204 가 `docs/spikes/sillok.md` 첫 줄에 옮기도록 알려 준다. **국역 포함 여부는 미확인** — 원문(한문)만 있어도 T204·T209 는 진행한다(§8 T209 4단계) | T204(S1) → T209(S2) | 두지 않으면 **T204·T209 이월 확정**. 나머지 경로는 합성 이야기 레코드로 돈다 |
| 5 | **미커밋 변경을 먼저 커밋하고 기준선 기록**: 프론트 전체(`frontend/k-context/`), `tests/core/policy_proposer/test_proposer_render.py`, `deploy/openshell/policy.yaml`(#3 결정대로), `docs/SCOPE.md`, 새 문서(`docs/AGENT_CONTEXT.md`·`docs/CONTEXT_NOW_KOREA.md`·`docs/CONTEXT_STORY_ROUTE.md`·`docs/ui-mockup/`·`docs/sprints/sprint-2*.md`), 배점 관련 내용을 지운 문서 수정. 커밋 뒤 §0.1 기준선(pytest 건수·`node --test` 129건·ruff)을 적는다 | 모든 스테이지(병렬 태스크가 미커밋 파일과 섞이지 않게) | T208 을 하려면 이 커밋이 반드시 먼저다(`test_proposer_render.py` 가 미커밋 수정 상태) |

### 시작을 막지 않는 것 (풀리는 대로 붙인다)

| ID | 할 일 | 붙는 곳 | 막혀 있을 때 |
|---|---|---|---|
| H2 | 실록 범위 결정(전체 vs 데모 지역 관련 구절) + `regions/*.json` 의 `sillok_keywords` 채우기 | T209 기본 모드 | 기본 `--mode regions`, 검색어가 비면 지역 이름 |
| H3 | TourAPI 서비스키 → 셸 env `DATA_GO_KR_SERVICE_KEY` | T205 실호출, T210-fetch | 합성 fixture·수기 공지(`manual`) |
| H4 | 서울 열린데이터광장 인증키 → `SEOUL_OPENAPI_KEY` | 동일 | 동일 |
| H5 | PlayMCP 카카오맵 서버 호출 가능성 확인 | T206 결론, 다음 스프린트 T222 | 직선거리 추정("예상" 표시) |
| H6 | 이야기 레코드 6~8개 큐레이션(`domains/kcontext/data/stories/<지역>/*.json`) | 실제 옛날 카드 내용 | 합성 레코드(`○○`) |
| H7 | 데모 앵커 좌표·지역 `bbox`·`center` 채우기 | 실제 거리·시간·지역 필터 | 합성 좌표(`"synthetic": true`) |
| H9 | 평가 세트 기대 정답 검수(`eval/testset.draft.json` → `eval/testset.json`) | T220(선택) 기준선 | 실행기가 "검수 전" 표시 |
| H10 | NVIDIA API 키 export | 다음 스프린트 T223 | 규칙 기반 판정 |
| H11 | CLAUDE.md "회귀 테스트" 절에 `cd frontend/k-context && node --test` 추가(T220 을 하면 `uv run python eval/run_kcontext.py --check` 도) | 공식 회귀 범위 | §6 게이트 표가 대신한다 |

---

## 1. dev 현실성 평가

| 스테이지 | TASK | 리스크 | 제안 |
|---|---|---|---|
| (초안 S2) | T213~T215 | 이미 구현됨(미커밋, `node --test` 129건). 초안이 가정한 파일 이름(`model.js`·`strings.js`)과 실제가 다름. 잔여 4건 남음 | 완료 처리하고 실제 파일 이름으로 기록. 잔여는 T219 로 |
| 전체 | 규모 | 필수 21개 태스크는 시간 상자에 비해 많음 | 화면 경로 중심으로 필수를 줄이고 나머지를 선택·이월 |
| S1 | T201 | 공통 bad 예제 중 일부(좌표 범위·REJECT_REASONS·ROUTE_BADGES·`estimated` bool·`facts.ref`·`approx.radius_m`·`[lat,lng]` 순서)는 JS `schema.js` 가 검사하지 않아 "양쪽 모두 문제 1건 이상" 조건이 깨짐. JS `isCoord` 는 숫자 2개인지만 보므로 순서를 구분하지 못함 | 공통 bad 예제는 양쪽이 잡는 위반만. 나머지는 py 전용 테스트 |
| S1 | T204~T206 | 스파이크 3개가 화면 경로에 직접 기여하지 않음 | T205·T206 은 선택, 문서 1쪽으로 축소. T204 는 H1 이 있을 때만 |
| S1 | T207 | `core.hitl.review` 는 `core.hitl.__all__` 밖. backend 프로세스에 `APP_PROCESS_ROLE=agent` 가 있으면 import 가 실패함 | `from core.hitl.review import ReviewDesk` 로 명시. backend 는 role 이 `agent` 가 아니어야 함을 기동 시 확인 |
| S1 | T208 | Sprint 1 이월. 미커밋 `test_proposer_render.py` 와 같은 폴더를 건드림 | 선택으로 내림. 하려면 미커밋 변경을 먼저 커밋 |
| S2 | T210 | `fetch.py` 는 키(H3·H4)와 확인된 필드 매핑(T205)이 있어야 의미 있음 | normalize·store·manual 만 필수, fetch 는 선택 |
| S2 | T211 | 이야기·행사·주입 차단이 한 태스크라 무거움 | T211a(이야기) · T211b(행사+주입 차단) 병렬 분할 |
| S3 | T216 | 가장 무거움(수집·판정·경로·일정·카드·근거·묶음) | T216a(후보·판정·옛날 카드) → T216b(경로·일정·묶음) 순차 분할 |
| S3 | T217 | MCP 도구는 화면 경로에 없음. T221 의 사람 승인 시연이 `request_source` 에 묶여 있음 | 선택으로 내림. T221 은 테스트 안에서 `DraftWriter` 를 직접 써서 draft 를 만든다 |
| S3 | T218 | T207 의 AST 경계 검사가 `runner.py` 의 subprocess 문자열(`python -m domains.kcontext.pipeline.run`)을 import 로 오탐할 수 있다는 우려 | 문자열은 import 노드가 아님을 테스트로 고정 |
| S3 | T220 | `fit.place` 를 쓰므로 T216 에 의존하는데 초안 선행에 빠짐 | 선행에 T216b 추가, Stage 5 선택으로 |
| S4 | T222~T224 | 블로커(H5·H10) 또는 화면 경로 밖 | 스프린트에서 제외·이월 |
| 문서 | §0.2·D7·§9·T222 | working tree 의 `policy.yaml` 에 사람이 추가한 `kakaomap_mcp`(미실측)가 있는데 초안은 "policy.yaml 은 그대로·network_policies 를 늘리지 않음"이라 적어 현실과 충돌 | D7 문안을 "에이전트·dev 는 수정하지 않는다, 사람이 추가한 항목은 미실측으로 두고 Sprint 2 코드는 의존하지 않는다"로 바꾸고, 사람 몫 결정 2건 추가 |

dev 제안이 확정본에 어떻게 들어갔는지:
1. **반영** — T213~T215 완료 처리(§4.0). 실제 파일: 각 모듈 `index.js` + 세부 파일, cards·rationale·chat·timeline·securitylog 는 `logic.js` 가 있다. **map 은 `logic.js` 가 없고** 순수 함수가 `route-layer.js`·`labels.js`·`route-list.js` 에 있다(실측). 테스트는 `tests/*.logic.test.js`·`tests/*.mount.test.js`. `strings.js`·`model.js` 는 없다. 잔여 4건(① `estimated` "예상" 표시 ② geo `cos(lat)` 보정 ③ 경로 bbox 와 지금 핀 bbox 를 같은 기준으로 ④ `schema.js` narration null 허용)은 T219 에 합쳤고, T219 소유 범위에 `src/i18n/*`·`schema.js`·map 파일을 명시했다.
2. **반영** — 규모 축소. 필수/선택/제외를 위 표대로 나눴다. T205·T206 은 문서 1쪽으로 축소해 선택으로 유지.
3. **반영** — T211 → T211a·T211b(병렬, 파일 소유 분리 §4). T216 → T216a·T216b(순차, Stage 3·4).
4. **반영** — T201 bad 예제 조건 수정. 공통 bad 는 양쪽이 잡는 위반만, 나머지는 py 전용. JS `isCoord` 한계 명시.
5. **반영** — T207 import 경로·`APP_PROCESS_ROLE` 조건. T217(선택)은 `agent` 를 먼저 설정한 뒤 import. T218 경계 오탐 테스트.
6. **반영** — policy.yaml 충돌 4곳(§0.2·D7·§9·T222 이월 메모)을 고치고 사람 몫 항목 2건(#3)을 추가.
7. **반영** — 결정 순서: D8·D10 은 Stage 1 전, D11 은 사후, D7 새 문안, D9 는 T212 전. 계약 3.3 보충은 Stage 1 전 사람 몫으로 올리고 pm 문안 초안을 §2.2 에 두었다.
8. **반영** — 시작 전 사람 최소 항목 5개(위 표). H3·H4·H5·H10 은 시작을 막지 않는다.
9. **반영** — 평가·배점·심사 관련 서술은 넣지 않았다.

---

## 0. 기준선 · 공통 규칙

### 0.1 기준선 (사람 선행 #5 의 커밋 직후 실측해 여기에 적는다)
- 커밋 해시: (이 문서와 함께 커밋 — `git log -1 -- docs/sprints/sprint-2.md`)
- `uv run python -m pytest -q` 건수: **636 passed** (2026-10-07 실측)
- `uv run ruff check .`: **통과**
- `cd frontend/k-context && node --test`: **129** (dev 보고) → 재실측 **129 pass / 0 fail**
- `python3 -c "import sqlite3; c=sqlite3.connect(':memory:'); c.execute(\"create virtual table t using fts5(x, tokenize='trigram')\"); print('fts5 trigram ok')"` 결과 ____ (T202 참고용)

### 0.2 공통 규칙 (모든 태스크)
- 파이썬 3.11+, 줄 길이 100, ruff 통과. 공개 함수에 타입 힌트, 패키지 `__init__.py` 는 `__all__` 을 명시한다.
- **새 런타임 의존성을 추가하지 않는다.** `fastapi`·`httpx`·`mcp`·`uvicorn`(pyproject) + 표준 라이브러리만. 프론트는 의존성 없음(네이티브 ES 모듈, `node --test`).
- 테스트 파일 이름은 레포 전체에서 고유하게(`tests/**/__init__.py` 없음, basename 으로 import). 새 파이썬 테스트는 `test_kc_*` 접두사.
- 기존 `tests/test_layout.py`·`tests/test_smoke.py`·`tests/test_boundaries.py` 는 수정하지 않는다. 경계 검사는 자기 태스크의 새 테스트 파일에 넣는다.
- 도메인 코드는 `domains/kcontext/` 에만. `core/` 에는 도메인 용어를 넣지 않는다(D3). 예외: T208(Sprint 1 이월, 도메인 무관).
- **지역은 코드에 박지 않는다**(AGENT_CONTEXT 3.2). 지역 이름·구·좌표 범위·검색어는 `domains/kcontext/data/regions/*.json` 에서만 읽는다. 코드에 `"종로"`·`"을지로"`·`"신촌"` 리터럴 금지(테스트 fixture·data 폴더 예외).
- **사실을 지어내지 않는다**(AGENT_CONTEXT 11). 테스트·예제 값은 `○○`·`예시`·`합성` 표시가 붙은 것만. 실제처럼 보이는 좌표에는 `"synthetic": true`.
- **공공데이터 호스트명·API 응답 필드 이름은 확인 전에 코드에 쓰지 않는다.** 확인 문서(`docs/spikes/*.md`)·필드 매핑 파일에 적힌 값만. 미확인은 `[확인 필요]`.
- 키는 env **변수 이름**으로만(규칙 1, D1, D5). 키 값은 코드·로그·예외 메시지·fixture·커밋에 남기지 않는다.
- **`deploy/openshell/policy.yaml` 은 에이전트·dev 가 수정하지 않는다(훅이 막는다).** 사람이 추가한 `kakaomap_mcp` 항목은 샌드박스 도입 시점까지 `[미실측]` 으로 두고, Sprint 2 코드는 이 항목에 의존하지 않는다(D7 새 문안). 이번 스프린트의 외부 호출(선택 T210-fetch)은 호스트에서 돈다.
- **프론트**: T219 만 프론트 파일을 고친다. 소유 범위는 §8 T219 에 나열한 파일뿐이다. 그 밖의 `src/state/*`·`src/lib/*`·`src/main.js`·`src/modules.js`·다른 모듈 디렉터리는 고치지 않는다. T201 은 `frontend/k-context/tests/contract.examples.test.js` 한 파일만 새로 만든다.

### 0.3 실행 디렉터리 (T203 이 `.gitignore` 에 추가)
```
var/                        # 실행 산출물 전부 — gitignore
  index/kcontext.db         # T202 색인
  data/events/*.jsonl       # T210 정규화된 행사
  output/<run_id>/          # T216b 출력 묶음, output/current.json 이 최신 run 을 가리킨다
  audit/*.jsonl             # core.audit JSONL
  hitl.db                   # core.hitl draft 저장소
domains/kcontext/data/raw/  # 내려받은 원자료(실록 XML·API 원응답) — gitignore
```
경로는 env 로 바꿀 수 있다: `KC_VAR_DIR`(기본 `<레포>/var`), `KC_DATA_DIR`(기본 `domains/kcontext/data`).

---

## 1. 의존성 그래프

```
[사람 선행 #1~#5]  (D7·D8·D10 승인, D11 사후 승인, 계약 3.3 보충, policy.yaml 결정, H1, 커밋+기준선)

Stage 1 (병렬)
T201 계약 ─────────┬───────────────┬──────────────┬─────────────┐
T202 색인 ───────┐ │               │              │             │
T203 지역 ───────┼─┼──┐            │              │             │
T204 실록 확인 (H1)┘ │  │            │              │             │
T207 승인 API ─────┼──┼────────────┼──────────────┼──────┐      │
(선택) T205 행사 1쪽 · T206 도보 1쪽 · T208 정책 초안 제출(이월, 독립)    │
                   ▼  ▼            ▼              ▼      │      │
Stage 2 (병렬)                                            │      │
T209 실록 수집 (T202·T203·T204) [H1]                      │      │
T210 행사 정규화 (T201·T202·T203)  (T205 는 선택 참고)      │      │
T211a 이야기 판정 (T201)                                   │      │
T211b 행사 판정+주입 차단 (T201)                           │      │
T212 도보·경로 (T201·T203, D9)                             │      │
(선택) T210-fetch (T210 과 같은 담당이 이어서, T205·H3/H4) │      │
                   │                                      │      │
Stage 3 (병렬)     ▼                                      ▼      ▼
T216a 후보·판정·옛날 카드 (T203·T210·T211a·T211b, D10, 계약 보충)
T218 backend 화면 API (T207, §5 형식, D10)
T219 http.js + 프론트 잔여 (§5.1, T207 응답 형식, 계약 보충)
(선택) T217 MCP 도구 (T202·T211b·T212, D10)
                   │
Stage 4            ▼
T216b 경로·일정·묶음 (T212·T216a)
                   │
Stage 5            ▼
T221 E2E·데모 스크립트 (전부)          [필수]
(선택) T220 평가 세트 (T211a·T211b·T216b)
```

---

## 2. 결정 (먼저 결정을 추가해야 함)

pm·dev 는 `docs/DECISIONS.md`·`docs/AGENT_CONTEXT.md` 를 고치지 않는다. 아래 문안을 사람이 승인하면 반영한다.

| 후보 | 요지 | 필요 시점 | 막는 것 |
|---|---|---|---|
| D7 (**새 문안**) | 외부 자료는 호스트 수집기, 에이전트는 로컬 색인만. **policy.yaml 은 에이전트·dev 가 수정하지 않고, 사람이 추가한 `kakaomap_mcp` 는 샌드박스 도입 시점까지 미실측으로 두며 Sprint 2 코드는 이 항목에 의존하지 않는다** | **Stage 1 시작 전** | T210(호스트 수집 전제), T210-fetch |
| D8 | 로컬 색인은 SQLite FTS5(trigram) + `Retriever` 인터페이스 | **Stage 1 시작 전** | T202 |
| D10 | 화면용 API 는 backend, 파이프라인은 별도 프로세스, 결과 파일만 주고받음 | **Stage 1 시작 전**(T207 의 경계 테스트도 이 결정을 전제) | T207 경계, T216a/b, T218 |
| D11 | 지도는 SVG 투영 기본, 타일·SDK 는 선택 | **사후 승인**(T213 구현 완료) | 기록 정합 |
| D9 | 도보 시간 공급자 우선순위, 추정은 `estimated: true`·"예상" 표시 | **Stage 2 의 T212 착수 전** | T212 표시 규칙, T219 "예상" |
| 계약 보충 | AGENT_CONTEXT 3.3 수정(§2.2) | **Stage 1 시작 전** | T201 확장 필드, T216a/b, T219 |

### 2.1 D7~D11 문안 (승인용)

```markdown
## D7 — 외부 자료는 호스트 수집기가 모으고 에이전트는 로컬 색인만 읽는다. policy.yaml 은 사람만 고친다 (2026-10-07)
- **결정**: 실록 XML·TourAPI·서울 열린데이터광장 수집은 호스트에서 실행하는 오프라인 수집기(`domains/kcontext/ingest/`)가 한다. 공공데이터 키는 호스트 셸 env 의 **변수 이름**(`DATA_GO_KR_SERVICE_KEY`, `SEOUL_OPENAPI_KEY` — 이름은 제안)으로만 참조한다. 결과는 `var/` 아래 로컬 색인·JSONL 로 저장하고, 에이전트 쪽(파이프라인·MCP 도구)은 이것만 읽는다.
  에이전트·dev 는 `deploy/openshell/policy.yaml` 을 수정하지 않는다(훅이 막는다). 사람이 추가한 `kakaomap_mcp` 항목은 샌드박스 도입 시점까지 미실측으로 두고, Sprint 2 코드는 이 항목에 의존하지 않는다.
- **계기**: ① 샌드박스 이미지는 Sprint 2 의 "지금 안 만들 것"이다. ② 외부 API 가 느리거나 한도에 걸릴 때를 대비해 핵심 자료를 로컬 색인으로 준비한다(AGENT_CONTEXT 7·8). ③ 키가 에이전트 프로세스에 들어가지 않는다(D1 과 같은 취지). ④ 정책 허용 항목은 실측(ALLOWED/DENIED)이 있어야 의미가 있는데(규칙 2), 실측은 샌드박스가 있어야 할 수 있다.
- **대안**: 에이전트가 실행 중에 API 를 직접 호출 — 샌드박스 허용 목록·provider 주입이 문서로 확인되지 않았고 이번 범위 밖이라 기각(다음 스프린트에 다시 검토). 키를 설정 파일에 기록 — 규칙 1 위반이라 기각. 미실측 항목 삭제 — 사람이 추가한 의도(카카오 호출 위치)가 정리되기 전이라 보류.

## D8 — 로컬 색인은 SQLite FTS5(trigram)로 시작하고 벡터 검색은 인터페이스 뒤로 미룬다 (2026-10-07)
- **결정**: 청크와 출처 메타(이름·위치·URL·원문 구절·수집일·등급)를 SQLite 한 파일에 저장하고 FTS5 `trigram` 토크나이저로 찾는다. FTS5 가 없는 빌드거나 검색어가 3자 미만이면 LIKE 로 찾는다. 검색은 `Retriever` 인터페이스로 감싸서, Nemotron 임베딩·리랭커는 키·NIM 이 확인되면 같은 인터페이스 뒤에 붙인다.
- **계기**: 표준 라이브러리만으로 바로 돌아가야 한다. 한국어는 형태소 분석 없이 trigram 으로 부분 일치를 잡을 수 있다. 임베딩은 API 키·엔드포인트(블로커)가 필요하다.
- **대안**: 처음부터 벡터 DB — 의존성과 키 블로커 때문에 기각. 파일 grep — 출처 메타 질의와 지역 필터가 어려워 기각.

## D9 — 도보 시간은 지도 엔진 값을 우선하고, 추정값은 추정이라고 표시한다 (2026-10-07)
- **결정**: 도보 거리·시간 공급자 우선순위는 ① PlayMCP 카카오맵 MCP(서버에서 호출할 수 있다고 확인된 경우) ② OSM 기반 도보 엔진 ③ 직선거리 × 우회 계수 ÷ 보행 속도 추정. ③의 결과는 `estimated: true` 를 달고 화면에 "예상 시간"으로 표시한다. 모델이 시간을 어림잡지 않는다. 네이버 Directions 는 자동차 전용이라 쓰지 않는다.
- **계기**: AGENT_CONTEXT 6장 "숫자는 지도·경로 엔진 값만"과 CONTEXT_STORY_ROUTE 6.3 "최소 구현: 직선 거리 추정, 화면에 예상 시간"을 함께 만족해야 한다. 카카오맵 MCP 는 카카오 로그인·본인인증이 필요해서 서버 호출 가능 여부가 미확인이다.
- **대안**: 추정 없이 지도 엔진이 준비될 때까지 경로를 안 냄 — 데모 경로가 통째로 막혀 기각. 추정값을 표시 없이 사용 — 사용자를 속이게 되어 기각.

## D10 — 화면용 API 는 backend 에, 파이프라인은 별도 프로세스로 돌리고 결과 파일만 주고받는다 (2026-10-07)
- **결정**: 프론트가 부르는 `/api/*`(읽기·채팅·사람 승인)는 `backend/` 에 둔다. backend 는 `domains`·`mcp_server` 를 import 하지 않는다. 채팅 요청이 오면 backend 가 `python -m domains.kcontext.pipeline.run` 을 **별도 프로세스**(`APP_PROCESS_ROLE=agent`)로 실행하고, 그 프로세스가 쓴 출력 묶음(`kc-bundle/v1`, JSON 파일)과 audit JSONL·hitl draft 를 읽는다. 상태 전이(승인·반려)는 backend 의 review 라우터에서만 한다(D2). 에이전트 쪽 산출물(출력 묶음·audit 기록)은 draft 와 같은 "제안" 지위이고 상태 전이를 담지 않는다. 사용자가 일정에 넣는 동작(`user_state`)은 이번 스프린트에서 화면 상태로만 다룬다.
- **계기**: CLAUDE.md 는 backend 를 "사람 전용 승인 API"로 정했는데, 프론트에는 읽기·채팅 API 가 더 필요하다. D3 의 프로세스 분리를 지키면서 도메인 로직을 backend 에 끌어오지 않는 방법이 필요하다.
- **대안**: 세 번째 프로세스(화면용 앱 서버) — 프로세스·포트가 늘어 기각. backend 가 `domains` 를 직접 import — 사람 전용 프로세스에 에이전트 코드가 들어와 D2·D3 경계가 흐려져 기각. 파이프라인을 MCP 서버 안에서만 실행 — 에이전트 런타임(NemoClaw) 연결이 이번 범위 밖이라 기각.

## D11 — 지도는 SVG 투영으로 먼저 그리고 타일·SDK 는 선택으로 붙인다 (2026-10-07, 구현 후 승인)
- **결정**: 프론트 map 모듈은 위경도를 화면 좌표로 투영해 SVG 로 그린다(배경 타일 없음, 외부 요청 없음). 카카오맵 JS SDK 나 OSM 타일은 키·도메인 등록·이용약관이 확인되면 같은 모듈의 렌더러로 추가한다.
- **계기**: 프론트는 번들러·외부 CDN 없이 돈다. 지도 SDK 는 키 발급·도메인 등록(사람 선행)이 필요하다. 목업이 이미 SVG 좌표계로 그려져 있고, map 모듈이 이 방식으로 구현되었다.
- **대안**: 처음부터 카카오맵 JS SDK — 키·도메인 등록 블로커로 기각. OSM 공개 타일 서버 직접 사용 — 이용 정책 미확인으로 기각.
```

### 2.2 계약 3.3 보충 문안 초안 (pm 제공, 사람이 AGENT_CONTEXT 3.3 에 반영)

```markdown
#### 3.3 보충 (2026-10-07 합의)
1. **좌표 순서**: `geometry.coords` 의 원소는 `[lat, lng]` 이다(`space` 가 `"geo"` 일 때).
2. **`geometry.space`**: `"geo"`(기본, `[lat, lng]`) | `"schematic"`(목업 좌표계 `[x, y]`, viewBox 0 0 600 700). 한 화면에 두 값이 섞이면 화면은 `geo` 만 그린다.
3. **카드 확장 필드(모두 선택)**: `era`(str) · `facts[{text, ref}]`(사실 층 문장, `ref` 는 카드 `sources` 안의 1부터 번호) · `alternatives[{label, text}]`(이설 병기) · `checks[{level: "ok"|"warn"|"bad", text}]` · `poster` · `only` · `warning` · `kind_label` · `sources[].bib`. `approx` geometry 는 `radius_m`(양수).
4. **경로 확장 필드**: `segments[].coords`(카드 없는 연결 구간도 그린다) · `segments[].label_xy`(schematic 전용, 선택) · **`route.estimated: bool`** — 경로 시간 중 하나라도 추정값이면 `true`, 화면은 "예상"을 붙인다(D9).
5. **`narration` 은 `null` 허용**: 몰입 층이 없으면 `null` 이고, 화면은 몰입 층 토글을 숨긴다. 내레이션을 지어 채우지 않는다.
6. 입력 확장(선택): `walk_request: {from: {name, lat, lng}, to: {name, lat, lng}, budget_min}`. 없으면 첫 빈 시간의 `near` → 숙소로 경로를 만든다.
```

---

## 3. 블로커 요약

| 블로커 | 막히는 것 | 대응 |
|---|---|---|
| 사람 승인(D7·D8·D10, 계약 보충) | Stage 1 시작 | 사람 선행 #1·#2. D9 는 T212 전, D11 은 사후 |
| 미커밋 변경 | 모든 병렬 스테이지, T208 | 사람 선행 #5 |
| H1 실록 XML | T204·T209 | 없으면 둘 다 이월. 화면 경로는 합성 이야기로 돈다 |
| API 키·인증(H3·H4·H5) | T210-fetch(선택), T205·T206 실호출(선택) | 합성 fixture·수기 공지·직선거리 추정. 시작을 막지 않는다 |
| 외부 데이터 라이선스 | fixture 커밋 | 실록은 공공누리 1유형(사람 확인) → 짧은 발췌를 fixture 로 커밋 가능, 문구는 T204 가 원문대로 기록. TourAPI·서울 원응답은 재배포 조건 `[확인 필요]` → 커밋하지 않는다 |
| 게이트웨이·샌드박스 | 없음 | 이번 스프린트는 샌드박스 안에서 돌지 않는다. `kakaomap_mcp` 항목에 의존하지 않는다(D7) |
| 문서 확인(규칙 4) | T217(선택, `mcp` SDK API) | 설치된 패키지 소스로 확인한다 |

---

## 4. 스테이지 상세

### 4.0 완료 처리 (초안 Stage 2 의 프론트 태스크)

| TASK | 제목 | 실제 파일(미커밋) | 테스트 | 상태 |
|---|---|---|---|---|
| T213 | 프론트 map 모듈 | `src/components/map/index.js`, `base-map.js`, `route-layer.js`(`makeProjector`·`layeredSegments`·`segStyle`·`pathD`·`centroid`·`approxRadius` 등), `route-list.js`, `labels.js`, `map.css` — **`logic.js` 없음** | `tests/map.logic.test.js`, `tests/map.mount.test.js` | 완료. 잔여 ①②③ → T219 |
| T214 | 프론트 cards + rationale | `src/components/cards/{index.js, logic.js, old-card.js, now-card.js, badge.js, source-tags.js, source-popover.js, immersion-toggle.js}`, `src/components/rationale/{index.js, logic.js, chips.js, evidence-panel.js}` | `tests/cards.logic.test.js`, `cards.mount.test.js`, `rationale.logic.test.js`, `rationale.mount.test.js` | 완료 |
| T215 | 프론트 chat + timeline + securitylog | `src/components/chat/{index.js, logic.js, message-list.js, suggestions.js, composer.js}`, `src/components/timeline/{index.js, logic.js, timeline-row.js}`, `src/components/securitylog/{index.js, logic.js, log-row.js, approve-buttons.js}` | `tests/{chat,timeline,securitylog}.logic.test.js`, `tests/{chat,timeline,securitylog}.mount.test.js` (가짜 DOM 도우미 `tests/_fakedom_ctsl.js`·`tests/_cr_fakedom.js`) | 완료 |

- 공통: `strings.js`·`model.js` 는 만들지 않았다. 문구는 `src/i18n/ko.js`·`en.js` 에 있다. `node --test` 129건·ruff 통과(dev 보고, 기준선 #5 에서 재실측).
- 잔여(전부 T219 로): ① `estimated` 경로 "예상" 표시 — map(`route-list.js`·라벨)·i18n, 현재 0건 ② geo 투영 `cos(lat)` 보정 — 지금 `makeProjector` 는 위도·경도에 같은 배율을 쓴다 ③ geo 일 때 경로 bbox 와 지금 카드 핀 bbox 를 같은 기준으로 ④ `src/api/schema.js` 의 story narration 필수를 null 허용으로.

### Stage 1
| TASK | 제목 | 범위(소유 경로) | 선행 | 구분 |
|------|------|------|------|------|
| T201 | 공통 계약: 카드·경로·출처·판정·입력 검증기 + 내부 레코드 타입 | `domains/kcontext/contract/`, `domains/kcontext/data/stories/README.md`, `tests/domains/kcontext/contract/`, `frontend/k-context/tests/contract.examples.test.js` | 사람 #2 | 필수 |
| T202 | 로컬 색인 저장소(청크 + 출처 메타 + FTS5) | `domains/kcontext/index/`, `tests/domains/kcontext/index/` | D8 | 필수 |
| T203 | 지역 설정·데이터 폴더·실행 디렉터리 | `domains/__init__.py`, `domains/kcontext/__init__.py`, `domains/kcontext/paths.py`, `domains/kcontext/regions.py`, `domains/kcontext/data/regions/`, `domains/kcontext/data/situations/`, `domains/kcontext/data/raw/.gitkeep`, `.gitignore`, `tests/domains/kcontext/test_kc_regions.py` | — | 필수 |
| T207 | backend: 사람 승인 API + 보안 로그 조회 | `backend/app.py`, `backend/settings.py`, `backend/security_log.py`, `backend/routers/review.py`, `tests/backend/` | D10 | 필수 |
| T204 | [확인] 실록 XML 구조·이용허락·발췌 fixture | `docs/spikes/sillok.md`, `tests/fixtures/kcontext/sillok/` | **H1** | 조건부(H1 없으면 이월) |
| T205 | [확인·1쪽] 행사 API 호스트·필드·이용조건 | `docs/spikes/events_api.md`, `domains/kcontext/ingest/events/field_maps/`, `tests/fixtures/kcontext/events/{tourapi,seoul}*.synthetic.json`, `.env.example` | (H3·H4 는 실호출만) | 선택 |
| T206 | [확인·1쪽] 도보 경로 공급자 | `docs/spikes/walk_route.md` | (H5) | 선택 |
| T208 | (이월 S1-T301 + W-D) 정책 초안 → hitl draft 제출, 쓰기 루트 보정 | `core/policy_proposer/submit.py`, `core/policy_proposer/baseline.py`, `tests/core/policy_proposer/test_proposer_submit.py`, `/workspace` 를 단언하는 기존 proposer 테스트 줄 | 사람 #5(커밋) | 선택(이월) |

### Stage 2
| TASK | 제목 | 범위 | 선행 | 구분 |
|------|------|------|------|------|
| T210 | 행사 정규화·저장·수기 공지 | `domains/kcontext/ingest/events/{__init__.py, normalize.py, store.py, manual.py, __main__.py}`, `tests/domains/kcontext/ingest/test_kc_ingest_events_{normalize,manual}.py`, `tests/fixtures/kcontext/events/manual.synthetic.json` | T201, T202, T203, D7 | 필수 |
| T211a | 이야기 판정 | `domains/kcontext/judge/__init__.py`, `judge/story.py`, `judge/terms.py`, `domains/kcontext/data/normalize/terms.json`, `tests/domains/kcontext/judge/test_kc_judge_story.py` | T201 | 필수 |
| T211b | 행사 판정 + 주입 차단 | `domains/kcontext/judge/inject.py`, `judge/now.py`, `tests/domains/kcontext/judge/test_kc_judge_now.py`, `test_kc_judge_inject.py` | T201 | 필수 |
| T212 | 도보 시간(추정 공급자) + 경로 A·B·C | `domains/kcontext/geo/`, `tests/domains/kcontext/geo/` | T201, T203, D9 | 필수 |
| T209 | 실록 수집기 | `domains/kcontext/ingest/__init__.py`, `domains/kcontext/ingest/sillok.py`, `tests/domains/kcontext/ingest/test_kc_ingest_sillok.py` | T202, T203, T204 | 조건부(H1) |
| T210-fetch | 행사 API 실호출 | `domains/kcontext/ingest/events/fetch.py`, `tests/domains/kcontext/ingest/test_kc_ingest_events_fetch.py` | T210(같은 담당이 이어서), T205 | 선택 |

### Stage 3
| TASK | 제목 | 범위 | 선행 | 구분 |
|------|------|------|------|------|
| T216a | 파이프라인 1: 상황·후보 수집·판정·옛날 카드·근거 | `domains/kcontext/pipeline/{__init__.py, situation.py, candidates.py, evaluate.py, assemble.py, strings.py}`, `tests/domains/kcontext/pipeline/test_kc_pipeline_{situation,candidates,assemble}.py`, `tests/fixtures/kcontext/stories/`, `tests/fixtures/kcontext/situations/` | T203, T210, T211a, T211b, D10, 계약 보충 | 필수 |
| T218 | backend 화면 API + 채팅 실행기 | `backend/routers/view.py`, `backend/runner.py`, `backend/chat.py`, `backend/app.py`(라우터 등록만), `backend/settings.py`(필드 추가만), `tests/backend/test_kc_backend_view.py`, `test_kc_backend_chat.py`, `test_kc_backend_runner_boundary.py`, `tests/fixtures/kcontext/bundle/` | T207, §5, D10 | 필수 |
| T219 | 프론트 http.js 연결 + 프론트 잔여 4건 | `frontend/k-context/src/api/http.js`, `src/api/schema.js`, `src/i18n/ko.js`, `src/i18n/en.js`, `src/components/map/{index.js, route-layer.js, route-list.js, labels.js}`, `tests/api.http.test.js`, `tests/map.geo.test.js` | T207 응답 형식, §5.1, D9, 계약 보충 | 필수 |
| T217 | MCP 도구 + 서버 엔트리 | `mcp_server/server.py`, `mcp_server/tools/kc_*.py`, `domains/kcontext/tools/`, `tests/mcp_server/` | T202, T211b, T212, D10 | 선택 |

### Stage 4
| TASK | 제목 | 범위 | 선행 | 구분 |
|------|------|------|------|------|
| T216b | 파이프라인 2: 경로·일정 맞추기·지금 카드·`kc-bundle/v1` 쓰기·CLI | `domains/kcontext/pipeline/{fit.py, assemble_now.py, bundle.py, run.py}`, `tests/domains/kcontext/pipeline/test_kc_pipeline_{fit,assemble_now,bundle,run}.py` | T212, T216a | 필수 |

### Stage 5
| TASK | 제목 | 범위 | 선행 | 구분 |
|------|------|------|------|------|
| T221 | 끝까지 E2E + 데모 스크립트 | `tests/test_kc_e2e.py`, `scripts/kc_demo.sh` | 필수 전부 | 필수 |
| T220 | 자체 평가 세트 + 실행기 | `eval/testset.draft.json`, `eval/run_kcontext.py`, `eval/results/.gitkeep`, `tests/eval/test_kc_eval_runner.py` | T211a, T211b, **T216b** | 선택 |

### 4.1 스테이지 구성 근거
- **Stage 1**: 경로의 양 끝을 먼저 세운다. 바닥(계약 T201·색인 T202·지역 T203)과 사람 승인 끝(T207)이다. 화면 끝은 이미 구현된 프론트 모듈이 mock 으로 맡는다. 네 필수 태스크는 소유 경로가 겹치지 않고 서로 import 하지 않는다. T202 는 T201 을 import 하지 않는다(TIERS 를 자기 상수로 두고 테스트로 값 일치를 고정). `domains/__init__.py`·`domains/kcontext/__init__.py` 는 T203 만 만든다. 그동안 T201·T202 는 namespace 패키지로 import 된다. T204 는 H1 이 있을 때만 하고 다른 태스크를 막지 않는다. 선택 태스크(T205·T206·T208)도 서로 다른 경로를 쓴다. T208 은 `core/policy_proposer/` 만 만지며 사람 #5 커밋 뒤에만 착수한다(이월 태스크지만 화면 경로 밖이라 선택).
- **Stage 2**: 네 필수 태스크가 `domains/kcontext/` 아래 서로 다른 파일을 소유한다. **T211a·T211b 는 같은 `judge/` 폴더지만 파일이 겹치지 않는다**: 공통 출력 타입(`Rejection`·`Blocked`)은 T201 의 `contract/records.py` 로 올려서 둘 다 그것을 import 한다. 설정은 각자 파일 안에 둔다(`StoryConfig`·`NowConfig`). 주입 차단 함수(`inject.screen`, T211b)를 T211a 는 **인자로 받는다**(`screen=` 콜백) — 같은 스테이지에서 서로 import 하지 않는다. `judge/__init__.py` 는 T211a 만 만든다. `ingest/__init__.py` 는 T209 만 만들고 T210 은 `ingest/events/` 만 만든다(T209 가 이월돼도 `ingest` 는 namespace 패키지로 import 된다). T210-fetch 는 T210 과 같은 폴더라 **같은 담당이 T210 뒤에 이어서** 한다.
- **Stage 3**: T216a 는 판정 둘과 행사 정규화가 있어야 한다. T218·T219 는 §5 의 엔드포인트·묶음 형식을 계약으로 삼아 병렬로 만들고, 실제로 맞는지는 T221 이 확인한다. T218 은 자기 fixture 묶음으로 검증하므로 T216 을 기다리지 않는다. T219 는 프론트 파일만, T216a 는 `pipeline/` 만, T218 은 `backend/` 만 만진다. `backend/app.py`·`settings.py` 는 Stage 1 에 T207 이 만들고 Stage 3 에서는 T218 만 고친다. T217(선택)은 `mcp_server/`·`domains/kcontext/tools/` 만.
- **Stage 4**: T216b 는 T216a 의 출력(`Evaluated`)과 T212 의 경로 조립이 있어야 한다. 같은 `pipeline/` 폴더라 T216a 와 같은 스테이지에 둘 수 없다. T216b 는 T216a 의 파일을 고치지 않고 새 파일만 만든다.
- **Stage 5**: T221 이 실제 subprocess 파이프라인 → backend → 사람 승인을 테스트로 고정한다. T220 은 `fit.place`(T216b)를 쓰므로 여기에 둔다. 둘은 파일이 겹치지 않는다.

---

## 5. 스테이지 사이 계약 (병렬 태스크가 맞춰야 하는 형식)

### 5.1 엔드포인트 표 (T218 구현, T219 소비, T207 일부)
base 는 `/api`. 모든 응답은 JSON, 문자열 필드는 `str` 또는 `{"ko","en"}`. 오류 본문은 항상 `{"error": {"code": str, "message": str}}`. **어떤 요청 본문에도 신원(요청자·승인자) 필드가 없다**(D2). 본문에 정의되지 않은 키가 있으면 422.

| 메서드(http.js) | HTTP | 성공 | 오류 |
|---|---|---|---|
| getItinerary() | `GET /api/itinerary` | 200 Itinerary(묶음 `itinerary.json`) | 503 `no_bundle` |
| getRoutes() | `GET /api/routes` | 200 Route[] | 503 `no_bundle` |
| getCards() | `GET /api/cards` | 200 Card[] | 503 `no_bundle` |
| getCard(id) | `GET /api/cards/{id}` | 200 Card | 404 `card_not_found`, 503 |
| getSources() | `GET /api/sources` | 200 Source[] | 503 |
| getRationale(cardId) | `GET /api/cards/{id}/rationale` | 200 `{card_id, chips, items}` | 404 `card_not_found`, 503 |
| getMessages() | `GET /api/messages` | 200 Message[] | — |
| sendMessage(text) | `POST /api/messages` `{text}` | 200 `{reply: Message, logs: AuditEntry[]}` | 422 `bad_text`(빈 문자열·2000자 초과), 429 `busy`, 502 `pipeline_failed` |
| getAuditLog() | `GET /api/audit` | 200 AuditEntry[] (T207) | — |
| decideAudit(id, decision) | `POST /api/audit/{id}/decision` `{decision}` | 200 AuditEntry (T207) | 404 `not_found`, 409 `not_decidable`·`already_decided`, 403 `self_approval`, 422 |

- `Message`: `{id: str, role: "user"|"agent", text: Text, blocked?: bool}`
- `AuditEntry`: `{id: str, time: "HH:MM:SS"(Asia/Seoul), at: ISO8601, kind: "ok"|"deny"|"pend"|"approved"|"rejected", text: {ko, en}, decided_by: str|null, decided_at: str|null, origin: "hitl"|"audit"}` — 프론트 mock(`src/data/auditlog.js`) 형식에 `at`·`origin`·`decided_at` 을 더한 것.
- id 형식: hitl draft 는 `draft:<draft.id>`, audit 이벤트는 `audit:<run_id>:<seq>`. 결정은 `draft:` 항목만.

### 5.2 출력 묶음 `kc-bundle/v1` (T216b 작성, T218 읽기)
```
var/output/current.json            {"schema": "kc-bundle/v1", "run_id": "<id>", "dir": "<run_id>"}
var/output/<run_id>/manifest.json  {"schema": "kc-bundle/v1", "run_id", "created_at", "situation_sha256",
                                    "counts": {"cards_story", "cards_now", "routes", "rejected", "blocked"},
                                    "estimated_routes": bool, "language": "ko"|"en"}
var/output/<run_id>/itinerary.json Itinerary (입력 계약 + 화면 확장: timeline[], landmarks[])
var/output/<run_id>/cards.json     Card[]
var/output/<run_id>/routes.json    Route[]
var/output/<run_id>/sources.json   Source[] (카드가 인용한 것만, id 중복 없음)
var/output/<run_id>/rationale.json {"<card_id>": {card_id, chips, items}}
var/output/<run_id>/verdicts.json  [6장 판정 객체...] (디버그용)
```
- run 디렉터리는 임시 이름으로 다 쓴 뒤 rename 하고, 마지막에 `current.json` 을 원자적으로 교체한다(`os.replace`). 읽는 쪽은 `current.json` 만 따라간다.
- 모든 JSON 은 `ensure_ascii=False, indent=2`, UTF-8.

### 5.3 T216a → T216b 내부 인터페이스
`domains/kcontext/pipeline/evaluate.py`(T216a)의 `Evaluated` 가 경계다. T216b 는 이것만 import 한다(§8 T216a 인터페이스).

---

## 6. 스테이지 게이트

명령은 레포 루트 기준. H11 이 반영되기 전까지는 이 표가 회귀 범위의 기준이다.
```
uv run python -m pytest -q
uv run ruff check .
(cd frontend/k-context && node --test)          # 기준선 129 부터
uv run python eval/run_kcontext.py --check      # T220 을 했을 때만
```
| 게이트 | 판정 시점 | 통과 조건 |
|---|---|---|
| Stage 1 | 필수 T201·T202·T203·T207(+ 착수한 조건부·선택 태스크)이 끝난 뒤 한 번 | pytest 전부 통과, 건수 > §0.1 기준선 · ruff · `node --test` 통과, 건수 > 129(T201 공통 예제 테스트 추가) · `.gitignore` 에 `var/`·`raw/` · **reviewer**: T207 신원 주입(요청 본문에 신원 없음, `reviewer_id` 가 `agent:` 로 시작하면 시작 거부, `APP_PROCESS_ROLE=agent` 면 기동 거부), (T208 을 했다면) D2(제출은 draft 만) · H1 이 있었다면 `docs/spikes/sillok.md` 상태 "확정" |
| Stage 2 | 필수 T210·T211a·T211b·T212 종료(T209 는 H1 있을 때만) | pytest 건수 증가 · ruff · 코드에 지역 리터럴 없음(`rg -n "종로|을지로|신촌" domains/kcontext --glob '*.py' --glob '!**/data/**'` 결과 0줄) · `judge/` 안에서 `story.py` 와 `now.py`·`inject.py` 가 서로 import 하지 않음(`rg -n "from domains.kcontext.judge" domains/kcontext/judge` 결과 0줄) |
| Stage 3 | T216a·T218·T219(+ T217 착수 시) 종료 | 위 명령 전부 통과, 건수 증가(`node --test` 포함) · **reviewer**: D3(backend 가 `domains`·`mcp_server` 를 import 하지 않음, subprocess 문자열은 오탐 아님), D2(채팅이 전이를 하지 않음), 규칙 1(오류 응답에 내부 출력 없음), D2(http.js 본문에 신원 없음) · 수동: `npm run serve` → `?api=mock` 에서 geo 합성 데이터가 아닌 기존 화면이 그대로 그려진다(회귀) |
| Stage 4 | T216b 종료 | 전부 통과 · `uv run python -m domains.kcontext.pipeline.run --situation tests/fixtures/kcontext/situations/synthetic_day1.json --stories tests/fixtures/kcontext/stories --events /tmp/kc-ev.jsonl --out-root /tmp/kc-out --audit-dir /tmp/kc-audit --now 2026-10-15` 0 종료, 묶음이 계약 검증 통과 · **reviewer**: D10(출력은 제안 지위, 전이 없음) |
| Stage 5 | T221 종료(T220 은 착수했을 때만) | T221 E2E 통과 · 전체 회귀 통과 · `bash scripts/kc_demo.sh --fixture` 뒤 `curl -s localhost:8000/api/cards` 가 비어 있지 않은 배열 |

- 건수가 직전보다 줄면 테스트가 사라진 것이므로 게이트 실패. 게이트 실패 시 다음 스테이지에 착수하지 않는다.

---

## 7. 이월 규칙

| 대상 | 규칙 |
|---|---|
| 필수 태스크 | 이월하지 않는다. 밀리면 선택 태스크부터 포기한다 |
| T204·T209 | H1 이 없으면 "S3 이월 — 사유: 실록 XML 미확보". 화면 경로는 합성 이야기 레코드로 돈다 |
| T205·T206·T208·T210-fetch·T217·T220 | 선택. 착수하지 않으면 "S3 이월 — 사유: 화면 경로 밖(축소)" |
| T222 실제 도보 공급자 | **이번 스프린트 제외.** "S3 이월 — 사유: 카카오 호출 위치(호스트 수집기 D9 vs 샌드박스 안 `kakaomap_mcp` 정책 항목)의 의도 정리 대기(사람 선행 #3-②), H5 미확인". 초안 명세의 "정책 파일은 고치지 않는다 — 호스트에서 호출" 문구는 #3-② 결론에 따라 다시 쓴다. 정책 항목을 쓰는 방향이면 샌드박스가 필요해 "지금 안 만들 것"과 겹치므로 그 시점에 범위를 다시 정한다 |
| T223 LLM transport·추출 | 이번 스프린트 제외. "S3 이월 — 사유: 화면 경로 밖, H10" |
| T224 판단 규칙 스킬 | 이번 스프린트 제외. "S3 이월 — 사유: 화면 경로 밖". 만들 때 규칙 3(스킬 카드) |
| S1 이월 | **S1-T202-opt** 계속 이월(이번 경로에 필요 없음). **S1-T302**(OpenShell 로그 어댑터) 계속 이월(실측 캡처에 샌드박스 필요). **S1 hitl W1·W2** — 파일 권한 분리는 배포 때. **S1 T303 W1~W9** — T223 과 함께 이월 |

이월 항목은 `/done` 이 이 문서 끝 "이월" 절에 사유와 함께 적는다.

---

## 8. 태스크별 상세 구현 명세

---

#### T201 — 공통 계약: 카드·경로·출처·판정·입력 검증기 + 내부 레코드 타입 [필수 · Stage 1 · 병렬]
- **착수 조건**: 계약 3.3 보충(사람 #2). 늦으면 확장 필드는 "선택"으로만 받고 진행한다.
- **변경 파일** (모두 신규)
  - `domains/kcontext/contract/__init__.py`, `text.py`, `source.py`, `card.py`, `route.py`, `verdict.py`, `situation.py`, `records.py`, `errors.py`
  - `domains/kcontext/contract/examples/{card_story.json, card_now.json, route.json, verdict.json, situation.json, source.json}`
  - `domains/kcontext/contract/examples/bad/*.json` (각 파일 `{"kind": "card"|"route"|"source", "obj": {...}, "expect": ["문제 문자열 일부", ...]}`) — **공통 bad**(아래 9번)
  - `domains/kcontext/data/stories/README.md` (이야기 레코드 작성법 — H6 용)
  - `tests/domains/kcontext/contract/test_kc_contract_validate.py`, `test_kc_contract_records.py`, `test_kc_contract_examples.py`, `test_kc_contract_py_only.py`
  - `frontend/k-context/tests/contract.examples.test.js`
- **인터페이스**
  ```python
  # text.py
  Text = str | dict[str, str]                 # str 또는 {"ko": str, "en": str} (두 키 모두 비어 있지 않은 str)
  def is_text(v: object) -> bool
  def pick(v: Text, lang: str = "ko") -> str  # dict 면 lang 키, 없으면 ko

  # source.py
  TIERS = ("S", "A", "B", "C", "D")
  def validate_source(s: Mapping, at: str = "source") -> list[str]
  def source_tag(s: Mapping, lang: str = "ko") -> str   # "[S] 조선왕조실록 · ○○ ○년 ○월 ○일"

  # card.py
  KINDS = ("story", "now"); GEOMETRY_TYPES = ("point", "segment", "area", "approx")
  STORY_BADGES = ("기록", "전승", "추정"); NOW_BADGES = ("확인됨", "확인 필요", "보류")
  USER_STATES = ("proposed", "added", "visited", "skipped")
  REJECT_REASONS = ("관련 없음", "중복", "신뢰 불가", "기간 지남", "동선에서 너무 멂",
                    "관심사 불일치", "상황 부적합", "지시문 포함", "위치 미상", "취소됨")
  def validate_card(c: Mapping) -> list[str]

  # route.py
  ROUTE_BADGES = ("가장 빠름", "이야기 가장 많음", "추천")
  def validate_route(r: Mapping, card_ids: Collection[str] | None = None) -> list[str]

  # verdict.py  (AGENT_CONTEXT 6장)
  VERDICTS = ("accepted", "rejected", "disputed", "unverified"); CONFIDENCE = ("high", "medium", "low")
  STANCES = ("support", "contradict")
  def validate_verdict(v: Mapping) -> list[str]

  # situation.py (3.3 입력)
  ANCHOR_TYPES = ("flight", "hotel", "train", "bus", "visit")
  def validate_situation(s: Mapping) -> list[str]

  # errors.py
  class ContractError(ValueError):       # .problems: tuple[str, ...]
  def ensure_valid(kind: Literal["card", "route", "verdict", "situation", "source"], obj: Mapping) -> None

  # records.py — 파이프라인 내부 입력·판정 공통 출력(3.3 밖). frozen dataclass + from_dict/to_dict
  @dataclass(frozen=True)
  class SourceRef:  id: str; tier: str; name: str; locator: str; url: str; published: str | None
                    collected_at: str; quote: str; bib: str | None = None
  @dataclass(frozen=True)
  class Evidence:   source: SourceRef; stance: Literal["support", "contradict"]; says: str | None = None
                    claim_kind: Literal["fact", "lore", "inference"] = "fact"
  @dataclass(frozen=True)
  class StoryClaim: text: Text; evidence: tuple[Evidence, ...]
  @dataclass(frozen=True)
  class StoryRecord: id: str; region: str; title: Text; theme: str; era: str | None
                     geometry: Mapping  # 카드 geometry 와 같은 모양, space 는 "geo"
                     alignment: Literal["exact", "approx"]; claims: tuple[StoryClaim, ...]
                     narration: Text | None = None; synthetic: bool = False
  EVENT_CATEGORIES = ("festival", "performance", "exhibition", "market", "night_market", "bar", "other")
  @dataclass(frozen=True)
  class EventRecord: id: str; region: str | None; title: Text; category: str
                     start_date: str | None; end_date: str | None      # "YYYY-MM-DD"
                     start_time: str | None; end_time: str | None      # "HH:MM"
                     place_name: str; lat: float | None; lng: float | None
                     geometry_type: Literal["point", "area", "approx"]; radius_m: int | None
                     status: Literal["scheduled", "cancelled", "changed", "unknown"]
                     outdoor: bool | None; description: str; source: SourceRef
                     fetched_from: Literal["tourapi", "seoul", "manual", "web", "fixture"]; synthetic: bool = False  # "web" 추가: D12(구청 행사 검색 수집)
  # 판정 공통 출력 (T211a·T211b 가 함께 쓴다 — 같은 스테이지 병렬 import 충돌 방지용으로 여기에 둔다)
  @dataclass(frozen=True)
  class Rejection: target_id: str; claim: str; reason: str; detail: str   # reason ∈ REJECT_REASONS (__post_init__ 검사)
  @dataclass(frozen=True)
  class Blocked: source_id: str; verdict: Literal["injection", "suspicious"]; rules: tuple[str, ...]
  def story_from_dict(d) -> StoryRecord; def event_from_dict(d) -> EventRecord  # 실패 시 ContractError
  ```
- **핵심 로직**
  1. 검증기는 **던지지 않고 문제 목록(list[str])을 돌려준다**. 문구 형식은 프론트 `src/api/schema.js` 와 같게(`"card[<id>].<필드>: <이유>"`). `ensure_valid` 만 던진다.
  2. `validate_source`: `id`·`name`·`locator`·`collected_at`·`quote` 는 비어 있지 않은 str. `tier ∈ TIERS`. `collected_at` 은 `YYYY-MM-DD`. `url` 은 str(빈 문자열 허용). `published` 는 str 또는 None.
  3. `validate_card`: `schema.js` 의 `validateCard` 규칙을 모두 옮긴다(id, kind, title·body Text, geometry.type, coords 가 비어 있지 않은 `[[a,b],...]`, segment 는 2점 이상, basis Text, badge 가 kind 에 맞는 딱지, sources 비어 있지 않고 각각 유효, user_state, why_fits·caveats·rejected 배열, now 카드는 `slot.day` 숫자·`time_cost_min` 숫자·`valid.as_of`). 추가 규칙(py 전용): `geometry.space` 가 없거나 `"geo"` 이면 좌표를 `[lat, lng]` 로 보고 범위(-90..90, -180..180)를 검사. `approx` 는 `radius_m` 양수. `rejected[]` 원소는 `{claim, reason}` 이고 reason ∈ `REJECT_REASONS`.
  4. **narration**: story 카드에서 `narration` 은 Text **또는 None**(계약 보충 5). 현재 `schema.js` 는 필수로 요구하므로(T219 가 고친다) 공통 예제(`examples/*.json`)는 narration 이 있는 것만 넣는다. 차이는 `test_kc_contract_py_only.py::test_narration_null_allowed` 로 고정한다.
  5. 확장 필드(계약 보충 3·4: `era`, `facts`, `alternatives`, `checks`, `poster`, `only`, `warning`, `kind_label`, `bib`, `segments[].coords`, `label_xy`, `estimated`)는 **있으면 형식만 검사하고 없어도 통과**. `facts[].ref` 는 1..len(sources) 정수.
  6. `validate_route`: `schema.js` 의 `validateRoute` 규칙 + (py 전용) `badges` 원소 ∈ `ROUTE_BADGES`, `delta_min ≥ 0`, `estimated` 가 있으면 bool.
  7. `validate_verdict`: `claim` 비어 있지 않은 str, `sources[]` 각 원소 `{id, tier, date(str|None), stance, says?}`, `verdict ∈ VERDICTS`, `reason` 비어 있지 않은 str, `confidence ∈ CONFIDENCE`.
  8. `validate_situation`: `trip.from ≤ trip.to`(날짜), anchors 의 type, `lat/lng` 은 숫자 또는 None, `free_slots[].from < to`, `language ∈ {"ko","en"}`. 선택 키 `walk_request` 는 있으면 형식 검사.
  9. **공통 예제와 py 전용 테스트 (dev 평가 반영)**
     - `examples/*.json`(정상): Python 검증기와 node `schema.js` 검증기 **모두 문제 0건**.
     - `examples/bad/*.json`(공통 bad): **두 검증기가 모두 잡을 수 있는 위반만** 넣는다 — 필수 필드 누락(예: `title` 없음), `kind`·`badge` 불일치(story 카드에 `확인됨`), `sources` 빈 배열, segment 좌표 1점, now 카드 `slot.day` 누락. 양쪽 모두 문제 1건 이상이고, Python 은 `expect` 의 문자열을 모두 포함해야 한다. node 쪽은 건수(≥1)만 확인한다.
     - **py 전용**(`test_kc_contract_py_only.py`, 예제 파일이 아니라 테스트 안에서 dict 로 만든다): 좌표 범위 밖, `rejected[].reason` 이 `REJECT_REASONS` 밖, 경로 `badges` 가 `ROUTE_BADGES` 밖, `estimated` 가 bool 아님, `facts[].ref` 범위 밖, `approx.radius_m` 누락·0, `[lat,lng]` 순서가 뒤바뀐 경우(lat 자리에 127 같은 값 → 범위 밖으로 잡힘), narration null 허용.
     - JS `isCoord` 는 "숫자 2개짜리 배열"인지만 보므로 **좌표 순서를 구분하지 못한다.** 이 한계를 `contract.examples.test.js` 머리 주석과 `contract/card.py` docstring 에 적는다.
     - 예제 값은 `○○`·`예시` 와 `"synthetic": true`.
  10. `data/stories/README.md`: `StoryRecord` JSON 필드표, "출처마다 locator·collected_at·quote 가 없으면 넣지 않는다", "좌표 근거(basis)를 반드시 적는다", "기억으로 쓰지 않는다(CONTEXT_STORY_ROUTE 5장 씨앗은 검증 전)" 세 줄 규칙, 예시 1건(`○○`).
  11. `contract.examples.test.js`: `node:fs` 로 `../../../domains/kcontext/contract/examples/*.json` 과 `bad/*.json` 을 읽어 `src/api/schema.js` 의 검증 함수로 돌린다(기존 export 이름을 그대로 import, schema.js 는 고치지 않는다).
- **엣지 케이스**: Text dict 에 `ko` 만 있음 → 문제. coords 원소에 bool → 문제(`isinstance(x, bool)` 먼저). NaN·inf → 문제. `card_ids` 가 주어졌는데 없는 카드 → 문제. `from_dict` 에 모르는 키 → `ContractError`. `Rejection(reason="모르는 값")` → `ValueError`.
- **지켜야 할 규칙**: AGENT_CONTEXT 3.3·6장이 원본. 사실을 지어내지 않는다(`○○`). 프론트는 테스트 파일 하나만 새로 만든다.
- **DoD**: `uv run python -m pytest -q tests/domains/kcontext/contract` · `(cd frontend/k-context && node --test tests/contract.examples.test.js)` · `uv run ruff check domains/kcontext/contract tests/domains/kcontext/contract`.

---

#### T202 — 로컬 색인 저장소(청크 + 출처 메타 + FTS5) [필수 · Stage 1 · 병렬]
- **착수 조건**: D8 승인(사람 #1).
- **변경 파일** (신규): `domains/kcontext/index/__init__.py`, `store.py`, `chunk.py`, `__main__.py`; `tests/domains/kcontext/index/test_kc_index_store.py`, `test_kc_index_chunk.py`
- **인터페이스**
  ```python
  # chunk.py
  def chunk_text(text: str, *, max_chars: int = 800) -> list[str]
  def make_chunk_id(source_id: str, locator: str, text: str) -> str   # sha1(...)[:16]

  # store.py
  TIERS = ("S", "A", "B", "C", "D")      # T201 을 import 하지 않는다(병렬). 값이 같아야 한다 — Stage 1 게이트 뒤 T216a 테스트에서 일치 확인
  @dataclass(frozen=True)
  class Chunk:
      chunk_id: str; source_id: str; tier: str; name: str; locator: str; url: str
      published: str | None; collected_at: str; text: str; quote: str
      regions: tuple[str, ...] = (); meta: Mapping[str, str] = field(default_factory=dict)
  @dataclass(frozen=True)
  class Hit: chunk: Chunk; score: float
  class IndexStoreError(Exception); class ChunkValidationError(IndexStoreError, ValueError)
  class ChunkNotFound(IndexStoreError, KeyError)
  class Retriever(Protocol):
      def search(self, query: str, *, regions=None, tiers=None, limit: int = 20) -> list[Hit]: ...
  class LocalIndex:                        # Retriever 구현
      def __init__(self, path: str | Path, *, _force_like: bool = False)  # ":memory:" 허용. 부모 디렉터리는 만들지 않음
      fts_enabled: bool                     # 읽기 전용 속성
      def add(self, chunks: Iterable[Chunk]) -> int          # chunk_id 기준 upsert, 반영 건수
      def search(self, query: str, *, regions: Collection[str] | None = None,
                 tiers: Collection[str] | None = None, limit: int = 20) -> list[Hit]
      def get(self, chunk_id: str) -> Chunk
      def count(self) -> int
      def close(self) -> None               # 컨텍스트 매니저 지원
  ```
  `__main__.py`: `python -m domains.kcontext.index stats --db PATH`(총 건수·등급별·지역별), `search --db PATH --q TEXT [--region R] [--limit N]`(원문 구절 앞 80자 출력).
- **핵심 로직**
  1. 스키마: `chunks(chunk_id TEXT PRIMARY KEY, source_id, tier, name, locator, url, published, collected_at, text, quote, regions_json, meta_json)`, `chunk_regions(chunk_id, region)`.
  2. FTS: `fts5(chunk_id UNINDEXED, text, tokenize='trigram')` 를 두고 add 시 같이 갱신. 생성이 `sqlite3.OperationalError` 면 `fts_enabled=False`, LIKE 검색. 두 경로를 모두 테스트(LIKE 는 `_force_like=True`).
  3. 검색: NFKC·strip. 3자 미만이거나 FTS 없음 → `text LIKE ? ESCAPE '\'`(%·_ 이스케이프). FTS 질의는 큰따옴표를 두 개로 바꾸고 전체를 `"..."` 구 질의로만. 점수: FTS 는 `-bm25`, LIKE 는 등장 횟수. 정렬 score 내림차순 → tier(S 먼저) → chunk_id.
  4. `add` 검증: `tier ∈ TIERS`; `name`·`locator`·`collected_at`·`text`·`source_id` 비어 있지 않음; `collected_at` `YYYY-MM-DD`; `text` ≤ 20,000자; `quote` 비면 `text[:300]`; `quote` ≤ 500자. 하나라도 틀리면 **배치 전체 거부**(`ChunkValidationError`, chunk_id 와 첫 위반). 트랜잭션.
  5. `chunk_text`: 빈 줄로 문단 분리 → `max_chars` 초과 문단은 문장 경계(`다.`·`.`·`?`·`!`·`。` 뒤 공백) → 그래도 넘으면 `max_chars` 에서 자른다. 빈 청크 버림. 순서 보존.
  6. 원문을 그대로 저장한다(신뢰할 수 없는 입력). 주입 판정은 소비자(T211b)가 `core.guard` 로 — 모듈 docstring 에 적는다.
- **엣지 케이스**: 같은 chunk_id 재삽입 → 갱신(건수 그대로). 부모 디렉터리 없음 → `FileNotFoundError`. 질의 `""` → 빈 목록. `"`·`*`·`NEAR` → 문법 오류 없이 문자 그대로. `limit` 1..200 밖 → `ValueError`. 지역 필터 빈 집합 → 빈 목록.
- **fixture 경로**: 합성 청크(`○○ 행차`, `○○ 물길`).
- **지켜야 할 규칙**: D8 · AGENT_CONTEXT 3.3(locator·collected_at 필수) · 표준 라이브러리만.
- **DoD**: `uv run python -m pytest -q tests/domains/kcontext/index`(FTS·LIKE 두 경로, FTS 주입 문자열 포함) · `uv run python -m domains.kcontext.index stats --db /tmp/kc-test.db` 가 빈 색인에서 0 을 출력하고 0 종료 · ruff.

---

#### T203 — 지역 설정·데이터 폴더·실행 디렉터리 [필수 · Stage 1 · 병렬]
- **변경 파일**
  - 신규: `domains/__init__.py`(빈 파일), `domains/kcontext/__init__.py`(docstring 과 `__all__: list[str] = []`), `domains/kcontext/paths.py`, `domains/kcontext/regions.py`
  - 신규: `domains/kcontext/data/regions/{euljiro,jongno,sinchon}.json`, `domains/kcontext/data/situations/demo_day1.json`, `domains/kcontext/data/raw/.gitkeep`
  - 수정: `.gitignore` (`var/`, `domains/kcontext/data/raw/*`, `!domains/kcontext/data/raw/.gitkeep`)
  - 신규: `tests/domains/kcontext/test_kc_regions.py`
  - 주의: 기존 `domains/.gitkeep`·`domains/README.md` 는 그대로 둔다.
- **인터페이스**
  ```python
  # paths.py
  def repo_root() -> Path
  def data_dir() -> Path      # env KC_DATA_DIR, 기본 repo_root()/domains/kcontext/data
  def var_dir() -> Path       # env KC_VAR_DIR, 기본 repo_root()/var  (만들지 않는다)

  # regions.py
  @dataclass(frozen=True)
  class Region:
      id: str                                   # ^[a-z][a-z0-9_]{0,31}$, 파일 이름과 같아야 한다
      name: dict[str, str]                      # {"ko","en"}
      gu: tuple[str, ...]
      bbox: tuple[float, float, float, float] | None   # (south, west, north, east)
      center: tuple[float, float] | None        # (lat, lng)
      keywords: tuple[str, ...]
      sillok_keywords: tuple[str, ...]          # H2
  class RegionConfigError(ValueError)
  def load_regions(directory: Path | None = None) -> dict[str, Region]
  def regions_at(lat: float, lng: float, regions: Mapping[str, Region]) -> list[str]
  def regions_in_text(text: str, regions: Mapping[str, Region], *,
                      field: Literal["keywords", "sillok_keywords"] = "keywords") -> list[str]
  ```
- **핵심 로직**
  1. 지역 JSON `{"id", "name": {"ko","en"}, "gu": [...], "bbox": null, "center": null, "keywords": [...], "sillok_keywords": [], "note": "bbox·center 는 H7 에서 채운다 [확인 필요]"}`. 지역·구: 을지로 → 중구, 종로 → 종로구, 신촌 → 서대문구(CONTEXT_NOW_KOREA 4장, AGENT_CONTEXT 3.2). `keywords` 는 지역 이름과 구 이름만. 좌표는 넣지 않는다(H7).
  2. `load_regions`: `*.json` 이름순. id 중복·파일 이름 불일치·bbox 순서 오류·모르는 키·빈 키워드 → `RegionConfigError`(파일 이름 포함). 파일 0개 → `RegionConfigError`.
  3. `regions_at`: bbox None 은 건너뜀. 경계 위 좌표는 포함.
  4. `regions_in_text`: NFKC 후 부분 문자열 일치. id 정렬·중복 없음.
  5. `demo_day1.json`: CONTEXT_NOW_KOREA 2장 대화 예시(10월 15~18일, 종로3가 숙소, 1일차 창덕궁 → 익선동, 2일차 경복궁 → 광화문, 3일차 신촌, 관심사 "한국 음식"·"로컬 문화", 일정 최소 변경)를 3.3 입력 형식으로. 연도 2026. 시간이 없는 앵커는 프론트 `src/data/itinerary.js` 예시 시간 + `"note": "시간은 예시"`. 모든 `lat`·`lng` 는 `null`(H7). `free_slots`: 1일차 19:00~23:00, `near: "익선동"`, `inferred: true`.
- **엣지 케이스**: `KC_DATA_DIR` 이 없는 경로 → `RegionConfigError`.
- **fixture 경로**: `tmp_path` 에 합성 지역(`"id": "region_a"`, 합성 bbox). 실제 지역 파일은 "로드되고 3개, bbox null 이어도 통과"만.
- **지켜야 할 규칙**: AGENT_CONTEXT 3.2 · 좌표를 지어내지 않는다 · `.gitignore` 의 비밀 패턴은 그대로(규칙 1).
- **DoD**: `uv run python -m pytest -q tests/domains/kcontext/test_kc_regions.py` · `git check-ignore -v var/x domains/kcontext/data/raw/x.xml` 둘 다 무시 · `git check-ignore domains/kcontext/data/raw/.gitkeep` 종료 코드 1 · ruff.

---

#### T207 — backend: 사람 승인 API + 보안 로그 조회 [필수 · Stage 1 · 병렬]
- **착수 조건**: D10 승인(사람 #1) — 경계 테스트가 D10 을 전제로 한다.
- **변경 파일** (신규): `backend/app.py`, `backend/settings.py`, `backend/security_log.py`, `backend/routers/review.py`; `tests/backend/test_kc_backend_review.py`, `tests/backend/test_kc_security_log.py`, `tests/backend/test_kc_backend_boundary.py`
  - 기존 `backend/__init__.py`·`backend/routers/__init__.py` 는 고치지 않는다.
- **인터페이스**
  ```python
  # settings.py
  @dataclass(frozen=True)
  class Settings:
      hitl_db: Path            # env KC_HITL_DB, 기본 <repo>/var/hitl.db (os.environ 으로 직접 계산 — domains 를 import 하지 않는다)
      audit_dir: Path          # env KC_AUDIT_DIR, 기본 <repo>/var/audit
      output_dir: Path         # env KC_OUTPUT_DIR, 기본 <repo>/var/output   (T218 이 쓴다)
      reviewer_id: str         # env KC_REVIEWER_ID, 기본 "human:demo"
      reviewer_auth_source: str  # 기본 "backend-local-demo"
      cors_origins: tuple[str, ...]  # env KC_CORS_ORIGINS(쉼표), 기본 ("http://localhost:8766",)
      @classmethod
      def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings"
  # __post_init__: reviewer_id 를 strip 한 값이 비었거나 "agent:" 로 시작하면 ValueError

  # security_log.py  (순수 함수)
  SECURITY_DRAFT_KINDS = ("source_request", "policy_proposal")
  DENY_ERROR_TYPES = ("InjectionBlocked", "PathDenied", "SourceNotAllowed")
  def entry_from_draft(d: Draft) -> dict          # AuditEntry (§5.1)
  def entries_from_events(events: Iterable[AuditEvent], *, run_id: str) -> list[dict]
  def build_entries(drafts: Iterable[Draft], events_by_run: Mapping[str, list[AuditEvent]]) -> list[dict]

  # app.py
  def create_app(settings: Settings | None = None) -> FastAPI
  app = create_app()   # uvicorn backend.app:app

  # routers/review.py
  router = APIRouter(prefix="/api")
  GET  /api/audit                     -> list[AuditEntry]
  POST /api/audit/{entry_id}/decision -> AuditEntry      body: {"decision": "approve"|"reject", "reason"?: str}
  ```
- **import 규칙 (dev 평가 반영)**
  - `ReviewDesk`·`Reviewer`(reviewer 쪽)는 `core.hitl.__all__` **밖**이다. 반드시 `from core.hitl.review import ReviewDesk, Reviewer` 로 가져온다(`from core.hitl import ReviewDesk` 는 실패한다). `Reviewer` 가 `core.hitl.review` 에 없으면 실제 정의 위치를 소스로 확인해 그 경로로 import 한다.
  - agent 쪽 이름(`init_db`·`DraftWriter`·`Draft`·예외)은 `core.hitl` 의 `__all__` 에서 가져온다. 이름이 `__all__` 에 없으면 소스에서 정의 모듈을 확인해 그 경로로.
  - `core/hitl/review.py` 는 `APP_PROCESS_ROLE == "agent"` 이면 import 단계에서 실패한다. backend 프로세스는 role 이 `agent` 가 **아니어야** 한다. `backend/app.py` 맨 위(다른 import 전)에서 `os.environ.get("APP_PROCESS_ROLE") == "agent"` 이면 `RuntimeError("backend 는 APP_PROCESS_ROLE=agent 로 실행할 수 없다 (D2)")` 를 올린다 — 원인이 바로 보이게 하려는 것이다.
- **핵심 로직**
  1. `create_app`: CORS(설정 origins 만, GET·POST), 시작 시 `hitl_db` 부모 디렉터리를 만들고 파일이 없으면 `init_db` 로 만든다. review 라우터 등록. 앱 상태에 settings 보관.
  2. `GET /api/audit`: draft 는 `DraftWriter(..., actor="backend:reader").list_drafts(kind=...)` 를 `SECURITY_DRAFT_KINDS` 별로 호출해 읽기만 한다. `audit_dir/*.jsonl` 을 `core.audit.read_jsonl` 로 읽는다(stem = run_id). 깨진 파일은 건너뛰고 헤더 `X-Audit-Skipped: <개수>`. 결과는 `at` 오름차순, 같으면 id 순.
  3. draft 매핑: `draft → pend`, `approved → approved`, `rejected → rejected`. text: `source_request` payload `{host, reason?}` → `{"ko": f"{host} · 허용 목록에 없음", "en": f"{host} · not on the allow list"}`. `policy_proposal` payload → `{"ko": f"정책 초안 · 네트워크 {n} · 파일 {m}", "en": f"Policy draft · network {n} · files {m}"}`(payload `summary` 에서). 모르는 모양 → `{"ko": f"{kind} 요청", "en": f"{kind} request"}`. `decided_by`·`decided_at` 은 draft 값.
  4. audit 이벤트 매핑: `phase=error, kind=tool` 이고 `data.error_type ∈ DENY_ERROR_TYPES` → `deny`, text 는 `data.message`(이미 redact 됨)를 ko·en 공통. `observe/net` 의 `decision=denied` → `deny` "`{host}:{port}` 차단", `allowed` → `ok`. `result/tool` 이고 name 이 `kc_` 로 시작 → `ok` "`{name}` 실행". 그 밖은 표시하지 않는다. `time` 은 `ts` 를 Asia/Seoul `HH:MM:SS`.
  5. `POST /api/audit/{entry_id}/decision`: pydantic `extra="forbid"` — `reviewer`·`decided_by` 등 → 422. `draft:` 로 시작하지 않으면 409 `not_decidable`. `Reviewer(id=settings.reviewer_id, auth_source=settings.reviewer_auth_source)` 를 **서버가** 만든다. approve → `ReviewDesk.approve`, reject → `ReviewDesk.reject(reason=본문 reason 또는 "화면에서 거절")`. 예외: `DraftNotFound` 404 `not_found`, `TransitionError` 409 `already_decided`, `SelfApprovalError` 403 `self_approval`, `DraftValidationError` 422. 성공 시 갱신된 draft 의 AuditEntry. (`ReviewDesk` 의 실제 생성자·메서드 시그니처는 `core/hitl/review.py` 소스를 읽어 맞춘다.)
  6. 모듈 docstring: "인증이 없는 로컬 데모용이다. 승인자 신원은 설정값이며 요청에서 받지 않는다. 공개 배포 전에는 인증 계층이 필요하다."
- **엣지 케이스**: audit_dir 없음 → 빈 목록. 목록 밖 draft kind → 넣지 않는다. 이미 승인된 항목 재승인 → 409. reviewer_id 가 draft 의 created_by 와 같음 → 403.
- **fixture 경로**: `tmp_path` 에 `init_db` 후 `DraftWriter(actor="agent:test-run")` 로 draft 생성, `AuditLog`+`JsonlSink` 로 이벤트. FastAPI `TestClient`. 테스트 프로세스에는 `APP_PROCESS_ROLE` 이 없어야 한다(필요하면 `monkeypatch.delenv`).
- **경계 테스트 `test_kc_backend_boundary.py`**: ① AST 로 `backend/**/*.py` 의 `Import`·`ImportFrom` 노드를 모아 `domains`·`mcp_server` 접두 0건 ② 서브프로세스(`env APP_PROCESS_ROLE=agent`)에서 `import backend.app` 이 실패하고 stderr 에 `APP_PROCESS_ROLE` 이 있다. 이 테스트는 **import 노드만** 본다(문자열은 보지 않는다) — T218 이 이 성질을 다시 확인한다.
- **지켜야 할 규칙**: D2(전이는 이 라우터에서만, 신원은 서버 주입) · D3·D10(backend 는 `mcp_server`·`domains` import 금지) · 규칙 1.
- **DoD**: `uv run python -m pytest -q tests/backend`(신원 키 본문 422, 자기 승인 403, 이중 승인 409, `draft:` 아닌 id 409, `agent:` reviewer 거부, role=agent 기동 거부 포함) · `uv run uvicorn backend.app:app --port 8000` 후 `curl -s localhost:8000/api/audit` → `[]` · ruff.

---

#### T204 — [확인] 실록 XML 구조·이용허락·발췌 fixture [조건부 H1 · Stage 1 · 병렬]
- **착수 조건**: 사람 #4 로 `domains/kcontext/data/raw/sillok/` 에 파일이 있다. 없으면 착수하지 않고 이월(§7).
- **변경 파일** (신규): `docs/spikes/sillok.md`, `tests/fixtures/kcontext/sillok/sample.xml`, `tests/fixtures/kcontext/sillok/README.md`
- **산출물 형식** (`docs/spikes/sillok.md`)
  ```markdown
  # 실록 XML 확인 (T204)
  상태: 확정 | fixture 불가
  자료: 국사편찬위원회_조선왕조실록 정보_실록원문 · 내려받은 날짜: YYYY-MM-DD (사람 기록) · 페이지 URL: … · 이용허락 문구(원문 그대로): …
  국역 포함: 있음 | 없음(원문만) | [확인 필요]
  ## 파일
  | 파일 | 크기 | 인코딩 | 루트 요소 | 기사 수(셀 수 있으면) |
  ## 요소·속성 표 (실측 — 파일에서 본 이름만)
  | 의미 | 요소·속성 이름 | 예시 값(○○ 로 가림 가능) | 비고 |
  | 기사 ID | … | | |
  | 왕대 | … | | |
  | 날짜(연·월·일) | … | | 음력/양력 표기 근거 |
  | 제목 | … | | |
  | 국역 본문 | … (없으면 "없음") | | |
  | 원문(한문) 본문 | … | | |
  | 원문 URL 을 만들 단서 | … | | URL 형식은 실제로 1건 열어서 확인 |
  ## locator 형식 결정 (예: "○○ ○년 ○월 ○일 · 기사 ID")
  ## 데모 지역 관련 구절 규모 (H2 판단 재료)
  ## 확인 필요로 남은 것
  ```
- **핵심 로직(절차)**
  1. 파일이 ZIP 이면 새 빈 디렉터리 `raw/sillok/extracted/` 에 풀고 거기서 읽는다(외부 파일은 신뢰하지 않음). 스크립트는 그 디렉터리 밖에 두고 `python3 -I` 로 실행한다.
  2. 표준 라이브러리 `xml.etree.ElementTree.iterparse` 로 앞부분만 읽어 요소·속성 이름을 표로 적는다. 앞 4KB 에 `<!DOCTYPE`·`<!ENTITY` 가 있으면 기록한다.
  3. **국역 포함 여부를 확인한다**(사람이 미확인으로 넘겼다). 본문 요소가 한문만인지 한글 번역이 있는지 표에 적는다.
  4. 음력 여부는 자료 설명이나 파일 안 표기로만 판단하고 근거를 적는다. 없으면 `[확인 필요]`.
  5. 원문 URL: 기사 ID 로 공식 사이트 URL 을 만들 수 있는지 1건을 실제로 열어 확인(`curl -sI`). 확인 안 되면 URL 은 빈 문자열로 쓰기로 적는다.
  6. 데모 지역 이름·구 이름으로 grep 한 기사 수.
  7. 발췌: 기사 2~3건(30KB 이하)을 원래 구조 그대로 `sample.xml` 로. 첫 줄 주석에 출처·내려받은 날짜·이용허락 문구. 문구에 재배포 제한이 있으면 저장하지 않고 상태 "fixture 불가".
- **fixture 경로**: 합성 XML 은 만들지 않는다(구조를 지어내게 되므로).
- **지켜야 할 규칙**: 추측 금지(`[확인 필요]`). 원본 커밋 금지(`raw/` gitignore). 내려받은 파일을 스크립트 디렉터리에서 실행하지 않는다.
- **DoD**: `docs/spikes/sillok.md` 상태 "확정" 또는 "fixture 불가". 확정이면 `python3 -I -c "import xml.etree.ElementTree as E; E.parse('tests/fixtures/kcontext/sillok/sample.xml')"` 성공.

---

#### T205 — [확인·1쪽] 행사 API 호스트·필드·이용조건 [선택 · Stage 1 · 병렬]
- **변경 파일**
  - 신규: `docs/spikes/events_api.md`(1쪽)
  - 신규(가능하면): `domains/kcontext/ingest/events/field_maps/tourapi_festival.json`, `seoul_cultural.json`; `tests/fixtures/kcontext/events/tourapi_festival.synthetic.json`, `seoul_cultural.synthetic.json`
  - 수정: `.env.example` (변수 **이름**만: `DATA_GO_KR_SERVICE_KEY=`, `SEOUL_OPENAPI_KEY=`, 주석 "호스트 수집기 전용(D7), 샌드박스에 넣지 않는다")
- **1쪽 형식**: 제공자 2개 × 칸(호스트·경로·필수 파라미터·응답 필드 이름·날짜 형식·페이지 처리·호출 한도·이용허락 유형·재배포 조건), 칸마다 출처 URL, 모르면 `[확인 필요]`. 서울 쪽은 "문화행사 정보"의 정확한 서비스 이름부터 확인한다.
- **필드 매핑 파일 형식** (T210 이 읽는 형식 — 이 문서가 정한다)
  ```json
  {
    "provider": "tourapi",
    "status": "confirmed | docs_only | unknown",
    "endpoint": {"base_url": "[확인 필요]", "path": "[확인 필요]", "method": "GET",
                 "key_param": "[확인 필요]", "key_env": "DATA_GO_KR_SERVICE_KEY",
                 "fixed_params": {}, "date_from_param": "[확인 필요]", "date_to_param": "[확인 필요]",
                 "page_param": null, "page_size_param": null},
    "items_path": ["...", "..."],
    "fields": {"id": "", "title": "", "start_date": "", "end_date": "", "start_time": null, "end_time": null,
               "place_name": "", "address": "", "lat": "", "lng": "", "updated": null, "url": null,
               "description": null, "category": null},
    "date_format": "%Y%m%d", "time_format": null, "coord_order": "lat_lng | lng_lat | x_y",
    "license": "공공누리 ○유형 [확인 필요]", "redistribution": "allowed | forbidden | unknown",
    "docs": ["활용가이드 URL", "..."]
  }
  ```
  `"[확인 필요]"` 가 남아 있으면 `status` 는 `unknown`.
- **절차**: 키 없이 공식 서비스 페이지·활용가이드(CONTEXT_NOW_KOREA 4장이 언급한 `searchFestival2`·`locationBasedList2`)로 확인. 키가 있으면(H3·H4) 각 1회 실호출, 원응답은 `raw/events/`(gitignore), 문서의 요청 URL 에서 키 값을 `***` 로 가린다. 합성 fixture 는 확인된 필드 이름 + `○○` 값 3~5건(여행 기간 안 1, 끝난 1, 날짜 없음 1, 중복 후보 1, 좌표 없음 1), 머리에 `"_synthetic": true`.
- **지켜야 할 규칙**: 규칙 1 · 확인한 것만 · 원응답 커밋 금지.
- **DoD**: `docs/spikes/events_api.md` 존재 · (만들었다면) JSON 파싱 성공 · `git diff .env.example` 에 값 없는 이름만.

---

#### T206 — [확인·1쪽] 도보 경로 공급자 [선택 · Stage 1 · 병렬]
- **변경 파일** (신규): `docs/spikes/walk_route.md`(1쪽)
- **형식**: 첫 줄 "결론: kakao_mcp | osm | estimate_only | 대기 — H5". 표 한 개(카카오맵 MCP vs OSM): 엔드포인트·전송 방식 / 인증(토큰 종류·발급 주체·수명·서버 보관 가능 여부) / 도구 이름·입력·출력 필드 / 호출 한도·약관(서버 재사용·캐시) / 응답 좌표 순서 / 라이선스. 마지막 줄 두 개: "네이버 Directions 는 자동차 전용이라 제외", "`deploy/openshell/policy.yaml` 의 `kakaomap_mcp`(사람 추가, 미실측)와의 관계: 이 문서는 정책 항목을 실측하지 않는다(샌드박스 범위 밖) — 사람 선행 #3-② 의 재료로만 쓴다".
- **절차**: 공식 안내로 엔드포인트·인증 확인. H5 가 있으면 `tools/list` 1회와 도보 경로 1회(공개 장소 이름 두 곳만 보낸다 — 일정·대화를 넣지 않는다). 토큰은 남기지 않는다. D9 와 다른 결론이면 "D9 수정 필요".
- **지켜야 할 규칙**: 규칙 4 정신(문서로 확인) · 규칙 1 · policy.yaml 은 고치지 않는다.
- **DoD**: 결론 한 줄과 표가 있다.

---

#### T208 — (이월 S1-T301 + W-D) 정책 초안 → hitl draft 제출, 쓰기 루트 보정 [선택 · Stage 1 · 병렬]
- **착수 조건**: 사람 #5 커밋 완료(같은 폴더의 `tests/core/policy_proposer/test_proposer_render.py` 가 미커밋 수정 상태였다). 커밋이 없으면 착수하지 않는다.
- **변경 파일**
  - 신규: `core/policy_proposer/submit.py`, `tests/core/policy_proposer/test_proposer_submit.py`
  - 수정: `core/policy_proposer/baseline.py` (`WRITE_PROPOSAL_ROOTS`·`NEVER_WRITE`)
  - 수정: `/workspace` 를 단언하는 기존 proposer 테스트(해당 줄만)
  - **고치지 않음**: `core/policy_proposer/__init__.py`
- **인터페이스**
  ```python
  POLICY_DRAFT_KIND = "policy_proposal"
  def to_payload(draft: PolicyDraft) -> dict[str, Any]
      # {"yaml": render_yaml(draft), "summary": {"network": int, "filesystem": int, "skipped": int},
      #  "skipped": [{"subject": str, "reason": str}, ...]}   (필드 이름은 model.py 실제 속성에 맞춘다)
  def submit(draft: PolicyDraft, writer: DraftWriter) -> Draft    # writer.create(POLICY_DRAFT_KIND, to_payload(draft))
  ```
- **핵심 로직**
  1. `submit` 은 `DraftWriter.create` 만 부른다. 256KiB 상한 초과 → `DraftValidationError` 그대로.
  2. W-D: `WRITE_PROPOSAL_ROOTS` 에서 `/workspace` 를 뺀다. `NEVER_WRITE` 에 `/sandbox/.openclaw`, `/sandbox/.hermes`, `/sandbox/.deepagents`, `/sandbox/.nemoclaw` 를 더한다. 이 경로 아래 쓰기 관찰은 Skipped.
  3. `READ_PROPOSAL_ROOTS` 에서도 `/workspace` 가 빠지는지 테스트.
- **엣지 케이스**: 빈 PolicyDraft → summary 0 제출. `/sandbox/.openclaw/x` 쓰기 → Skipped. `/workspace/x` → Skipped.
- **지켜야 할 규칙**: D2 · D4 · D3.
- **DoD**: `uv run python -m pytest -q tests/core/policy_proposer` · `rg -n '"/workspace"' core/policy_proposer` 0줄 · 전체 회귀 · ruff.

---

#### T210 — 행사 정규화·저장·수기 공지 [필수 · Stage 2 · 병렬]
- **착수 조건**: D7 승인. T205 는 필요 없다(있으면 field_map 을 읽는다).
- **변경 파일** (신규): `domains/kcontext/ingest/events/__init__.py`, `normalize.py`, `store.py`, `manual.py`, `__main__.py`; `tests/domains/kcontext/ingest/test_kc_ingest_events_normalize.py`, `test_kc_ingest_events_manual.py`, `tests/fixtures/kcontext/events/manual.synthetic.json`
  - `field_maps/`(T205)·`fetch.py`(T210-fetch)는 만들지 않는다. `ingest/__init__.py` 도 만들지 않는다(T209 소유).
- **인터페이스**
  ```python
  # normalize.py
  @dataclass(frozen=True)
  class NormalizeResult: records: tuple[EventRecord, ...]; problems: tuple[str, ...]; skipped_out_of_region: int
  class FieldMapMissing(FileNotFoundError)
  def load_field_map(provider: Literal["tourapi", "seoul"], directory: Path | None = None) -> dict
      # 기본 directory = 이 패키지의 field_maps/. 파일이 없으면 FieldMapMissing
  def normalize(raw: Mapping | str, *, provider: str, field_map: Mapping, collected_at: str,
                regions: Mapping[str, Region]) -> NormalizeResult
  # store.py
  def write_jsonl(records: Iterable[EventRecord], path: Path) -> int
  def read_jsonl(path: Path) -> list[EventRecord]
  def to_chunks(r: EventRecord) -> list[Chunk]
  # manual.py — 손으로 넣는 공지(구청 공지·변경 공지)와 합성 자료
  def load_manual(path: Path, *, regions: Mapping[str, Region]) -> NormalizeResult   # EventRecord 모양 JSON 배열
  # CLI
  # python -m domains.kcontext.ingest.events --provider tourapi|seoul|manual --fixture PATH \
  #   --from YYYY-MM-DD --to YYYY-MM-DD --out var/data/events/<provider>.jsonl [--db var/index/kcontext.db] --collected-at YYYY-MM-DD
  ```
- **핵심 로직**
  1. `normalize`: `items_path` 로 목록, `fields` 매핑대로 값. 날짜는 `date_format` 으로 `YYYY-MM-DD`, 실패 → None + problem. 좌표는 `coord_order` 에 따라 `(lat, lng)`, 숫자 아님·범위 밖 → None + problem. 매핑 값이 `"[확인 필요]"`·빈 문자열인 필드는 None.
  2. 출처: `SourceRef(id=f"{provider}:{원본 id}", tier="B", name=("한국관광공사 TourAPI" | "서울 열린데이터광장 문화행사"), locator=(갱신일 있으면 f"{갱신일} 갱신", 없으면 f"{collected_at} 수집 · 갱신일 미제공"), url=(url 값 또는 ""), published=갱신일, collected_at, quote=f"{제목} / {시작일}–{종료일} / {장소}")`. URL 을 만들어 내지 않는다.
  3. 지역: 좌표 있으면 `regions_at`, 없으면 주소·장소명으로 `regions_in_text`. 둘 다 없으면 `skipped_out_of_region` 에 세고 버린다.
  4. 카테고리: field_map 에 `"category_map"` 이 있을 때만 변환, 없으면 `"other"`. `status` 모르면 `"unknown"`. `geometry_type` 좌표 있으면 `point`, 없으면 `approx`.
  5. CLI: `--fixture` 는 필수(이번 범위의 실호출은 T210-fetch). tourapi·seoul 은 `load_field_map` 이 `FieldMapMissing` 이면 종료 코드 2 와 "T205 field_map 이 없다 — `--provider manual` 로 실행할 수 있다". JSONL 저장 + `--db` 가 있으면 `to_chunks` 를 색인에. 보고서 JSON 한 줄(records, problems 수, skipped).
  6. `manual.py`: `EventRecord` 모양 JSON 배열(`fetched_from: "manual"`)을 `event_from_dict` 로 읽고 같은 지역 처리.
- **엣지 케이스**: 빈 목록 → records 0, 정상 종료. `items_path` 중간이 list → problem 1건 후 빈 결과. 종료일 < 시작일 → problem, 값 유지. 같은 id 중복 → 뒤 것만, problem.
- **fixture 경로**: 정규화 테스트는 `tmp_path` 에 **합성 field_map**(필드 이름 `○○_title` 처럼 명백한 합성)과 그 모양의 합성 응답을 만들어 검증한다(T205 와 무관하게 녹색). `manual.synthetic.json`: 여행 기간(2026-10-15~18) 안·밖, 취소 공지, 같은 행사의 시간 변경 공지(갱신일 다름), 좌표 없음, 숨은 지시문이 든 설명 1건 포함, 모두 `○○`·`"synthetic": true`. 지역은 `tmp_path` 합성 지역 또는 테스트 안에서 만든 `Region`.
- **지켜야 할 규칙**: D7 · 규칙 1 · 필드 이름은 field_map 에서만(코드에 API 필드 이름 리터럴 금지) · 지역 리터럴 금지.
- **DoD**: `uv run python -m pytest -q tests/domains/kcontext/ingest -k events` · `uv run python -m domains.kcontext.ingest.events --provider manual --fixture tests/fixtures/kcontext/events/manual.synthetic.json --from 2026-10-15 --to 2026-10-18 --out /tmp/kc-ev.jsonl --collected-at 2026-10-07` 0 종료 · ruff.
- 주의: `manual.synthetic.json` 의 지역 매칭을 위해 레코드에 `region` 을 직접 넣거나(합성 지역 id 가 아닌 실제 `regions/*.json` id 를 쓰려면 bbox 가 null 이라 좌표 매칭이 안 되므로) 주소 문자열에 지역 keywords 를 넣는다. data 폴더가 아닌 fixture 파일이므로 지역 이름 리터럴이 허용된다.

---

#### T210-fetch — 행사 API 실호출 [선택 · Stage 2 · T210 담당이 이어서]
- **착수 조건**: T210 완료, T205 field_map 이 `status: confirmed`, H3 또는 H4.
- **변경 파일** (신규): `domains/kcontext/ingest/events/fetch.py`, `tests/domains/kcontext/ingest/test_kc_ingest_events_fetch.py`; 수정 `domains/kcontext/ingest/events/__main__.py`(`--fixture` 가 없으면 fetch)
- **인터페이스**
  ```python
  class FetchError(RuntimeError); class KeyMissing(FetchError); class FieldMapUnconfirmed(FetchError)
  def fetch(field_map: Mapping, *, date_from: str, date_to: str, client: httpx.Client | None = None,
            env: Mapping[str, str] | None = None, max_pages: int = 10) -> list[Mapping]
  ```
- **핵심 로직**: `status != "confirmed"` 또는 엔드포인트에 `[확인 필요]` → `FieldMapUnconfirmed`. 키는 `env[key_env]`, 없으면 `KeyMissing(f"{key_env} 가 설정되지 않았다")`. 타임아웃 10초, 재시도 없음, `max_pages` 까지. HTTP·JSON 오류는 `FetchError`, 메시지의 키 값은 `***` + `core.audit.redact_text`. CLI 에서 `KeyMissing` → 종료 코드 2 와 "`--fixture` 로 실행할 수 있다".
- **fixture 경로**: `httpx.MockTransport`(네트워크 없음) — 키 가림·KeyMissing·Unconfirmed.
- **지켜야 할 규칙**: D7(호스트에서 실행) · 규칙 1.
- **DoD**: fetch 테스트 통과 · ruff.

---

#### T211a — 이야기 판정 [필수 · Stage 2 · 병렬]
- **변경 파일** (신규): `domains/kcontext/judge/__init__.py`(docstring + `__all__: list[str] = []` — 소비자는 서브모듈 경로로 import), `judge/story.py`, `judge/terms.py`, `domains/kcontext/data/normalize/terms.json`, `tests/domains/kcontext/judge/test_kc_judge_story.py`
  - `judge/inject.py`·`judge/now.py` 는 T211b 소유 — import 하지 않는다.
- **인터페이스**
  ```python
  # terms.py
  @dataclass(frozen=True) class Terms: replacements: tuple[tuple[str, str, str], ...]   # (옛, 새, 시점)
  def load_terms(path: Path | None = None) -> Terms      # 기본 data_dir()/normalize/terms.json
  def outdated_terms(text: str, terms: Terms) -> list[tuple[str, str, str]]
  # story.py
  ScreenFn = Callable[[str, str], Blocked | None]        # (text, source_id) -> Blocked | None. T211b 의 inject.screen 이 이 모양
  @dataclass(frozen=True)
  class StoryConfig: superlatives: tuple[str, ...] = ("최초", "유일", "최대", "가장 오래된")   # [제안]
  @dataclass(frozen=True)
  class StoryJudgement: record_id: str; verdicts: tuple[dict, ...]; badge: str | None
                        accepted_claims: tuple[int, ...]; disputed_claims: tuple[int, ...]; disputed: bool
                        caveats: tuple[str, ...]; rejected: tuple[Rejection, ...]; blocked: tuple[Blocked, ...]
                        claim_badges: tuple[str | None, ...]    # 주장별 딱지(카드 facts 조립용)
  def judge_story(rec: StoryRecord, *, terms: Terms, screen: ScreenFn,
                  cfg: StoryConfig = StoryConfig()) -> StoryJudgement
  ```
  `Rejection`·`Blocked` 는 `domains.kcontext.contract.records` 에서 import(T201).
- **핵심 로직** (AGENT_CONTEXT 4.1·4.2, CONTEXT_STORY_ROUTE 3장)
  1. 주입 차단: 근거마다 `screen(quote + "\n" + (says or ""), source.id)`. `verdict="injection"` → 그 근거를 제외, `blocked` 에 추가, `Rejection(target_id=rec.id, claim=pick(claim.text), reason="지시문 포함", detail=source.id)`. `"suspicious"` → 제외하지 않고 `blocked` 에 추가 + caveat "자료에 지시문 의심 문구". 텍스트를 따르거나 실행하지 않는다.
  2. 주장마다 근거를 `S/A`(`sa`)·`B`·`C/D` 로 나누고 support/contradict 를 센다. 독립 출처 수는 `source.name` 기준 중복 제거.
  3. `outdated_terms` 가 걸린 근거는 모순이 아니라 caveat "옛 명칭 사용(오래된 자료)".
  4. claim_kind 별:
     - `fact`: `sa` support ≥1 이고 `sa` contradict 0 → accepted, `기록`. `sa` 양쪽 모두 → disputed. `sa` support 없음 + B support 만 → unverified. C/D 만 → rejected `신뢰 불가`.
     - `lore`: S/A/B support ≥1 → accepted, `전승`. C/D 만 → rejected `신뢰 불가`.
     - `inference`: A 이상 support ≥1 → accepted, `추정`. 아니면 unverified.
  5. 주장 문장에 `superlatives` 가 있고 A 이상 support 가 없으면 rejected `신뢰 불가`.
  6. confidence: 독립 S/A support ≥2 → high, 1 → medium, 그 외 low. disputed 는 low.
  7. verdict 객체(6장): `{"claim": pick(text), "sources": [{"id","tier","date": published,"stance","says"?}], "verdict", "reason", "confidence"}`. reason 은 한국어 한 문장(예: "S 등급 근거 2건과 일치").
  8. 카드 딱지: accepted·disputed 주장이 없으면 `badge=None`(카드 없음). 있으면 그 주장 딱지 중 **가장 약한 것**(기록 > 전승 > 추정). disputed 가 있으면 `disputed=True`, caveat "이설 있음", disputed 주장의 딱지는 근거 중 약한 쪽.
  9. `config` 수치는 `[제안]` — docstring 에 출처와 "시험 후 조정".
  10. `terms.json`: `{"replacements": []}` 로 시작하고 `"_note": "옛 명칭 표는 H6 큐레이션 때 출처와 함께 채운다"`. 실제 명칭을 기억으로 넣지 않는다. 테스트는 `tmp_path` 의 합성 표(`○○동 → ○○로`)로.
- **엣지 케이스**: 근거 0개 → unverified, 카드 없음. 같은 출처가 support·contradict 둘 다 → contradict 우선, caveat. `published` 가 날짜 아님 → None 취급. 모든 근거가 INJECTION → 주장 rejected `지시문 포함`.
- **fixture 경로**: 테스트 안 합성 StoryRecord(`○○`)와 가짜 `screen`(특정 표식 문자열이 있으면 Blocked). 함정 최소 1케이스씩: 연도 불일치(S 근거 둘이 반대 → disputed), 옛 명칭, 전설을 사실로 쓴 홍보물(D 등급 fact → rejected), 최상급 과장, 숨은 지시문(가짜 screen → 지시문 포함).
- **지켜야 할 규칙**: AGENT_CONTEXT 4장·6장 · CONTEXT_STORY_ROUTE 3장 · LLM 호출 없음 · 지역 리터럴 금지 · 같은 스테이지의 T211b 파일을 import 하지 않는다.
- **DoD**: `uv run python -m pytest -q tests/domains/kcontext/judge/test_kc_judge_story.py` · 모든 verdict 가 `validate_verdict` 문제 0건 · ruff.

---

#### T211b — 행사 판정 + 주입 차단 [필수 · Stage 2 · 병렬]
- **변경 파일** (신규): `domains/kcontext/judge/inject.py`, `judge/now.py`, `tests/domains/kcontext/judge/test_kc_judge_now.py`, `test_kc_judge_inject.py`
  - `judge/__init__.py`·`story.py`·`terms.py` 는 T211a 소유 — 만들거나 import 하지 않는다.
- **인터페이스**
  ```python
  # inject.py
  class InjectionBlocked(Exception)          # audit error_type 로 쓰인다(T207 DENY_ERROR_TYPES)
  def screen(text: str, source_id: str) -> Blocked | None    # core.guard.scan 사용. CLEAN → None. T211a 의 ScreenFn 모양
  # now.py
  @dataclass(frozen=True)
  class NowConfig: fresh_days: int = 14; dedupe_m: int = 150; title_similarity: float = 0.6
                   alcohol_categories: tuple[str, ...] = ("night_market", "bar")      # [제안]
  @dataclass(frozen=True) class Conflict: field: str; values: tuple[dict, ...]; chosen: str | None; reason: str
  @dataclass(frozen=True)
  class EventDecision: event_ids: tuple[str, ...]; primary: EventRecord; sources: tuple[SourceRef, ...]
                       badge: str; verdicts: tuple[dict, ...]; caveats: tuple[str, ...]; conflicts: tuple[Conflict, ...]
  @dataclass(frozen=True)
  class NowJudgement: decisions: tuple[EventDecision, ...]; rejected: tuple[Rejection, ...]
                      blocked: tuple[Blocked, ...]; funnel: Mapping[str, int]
  def judge_events(records: Sequence[EventRecord], situation: Mapping, *, now: date,
                   cfg: NowConfig = NowConfig()) -> NowJudgement
  ```
- **핵심 로직 — 주입 차단(`inject.screen`)**: `core.guard.scan(text)` 결과 판정이 INJECTION → `Blocked(source_id, "injection", 규칙 이름들)`, SUSPICIOUS → `"suspicious"`, CLEAN → None. `core.guard` 의 실제 반환 타입·필드 이름은 소스로 확인한다. 새 주입 규칙을 만들지 않는다(부족하면 완료 보고에).
- **핵심 로직 — 지금(CONTEXT_NOW_KOREA 3장)**
  0. 행사 `title`·`description` 을 `screen`. injection → 레코드 제외 + `Rejection(reason="지시문 포함")` + blocked. suspicious → 남기고 caveat "자료에 지시문 의심 문구".
  1. 관련성: `region` None → `관련 없음`. 여행 기간과 겹치지 않으면: 종료일 < 여행 시작 → `기간 지남`, 시작일 > 여행 끝 → `관련 없음`. 날짜 없음 → 남기고 caveat "날짜 불분명".
  2. 상황: `party.kids` 이고 category ∈ `alcohol_categories` → `상황 부적합`. `weather.rain` true 이고 `outdoor` true → `상황 부적합`. 좌표 없음 → 남기고 caveat "위치 미상".
  3. 중복 병합: 제목 정규화(NFKC, 공백·문장부호 제거, 소문자)가 같거나, 기간이 겹치고 거리 ≤ `dedupe_m`(haversine 을 이 파일 안 비공개 함수로 — T212 를 import 하지 않는다) 이고 `difflib.SequenceMatcher` ≥ `title_similarity` 이면 한 그룹. 대표는 tier 높은 → `published` 최신. 나머지는 `Rejection(reason="중복")`, 출처는 그룹에 합친다.
  4. 충돌(그룹 안): `status`·`start_time`·`start_date`·`place_name` 별로 값이 다르면 `Conflict`. `published` 가 가장 최신인 B 이상 출처가 하나뿐이면 그 값 채택(reason "최신 공식 공지 채택"). 최신을 정할 수 없으면 `chosen=None`.
  5. 채택된 status 가 `cancelled` → 그룹 전체 `Rejection(reason="취소됨")`.
  6. 딱지: 미해결 충돌 → `보류`. 아니면 `확인됨` = B 이상 출처 ≥1, `start_date`·`place_name` 있음, 최신 출처의 `published`(없으면 `collected_at`)가 `now - fresh_days` 이후. 하나라도 빠지면 `확인 필요`(caveat: "날짜 불분명", "단독 출처"(C 등급만), "n일 전 갱신").
  7. verdict 객체: 그룹마다 "○○ 행사는 {start}–{end} {place}에서 열린다" 1건(+ 충돌 필드마다 1건). 확인됨 → accepted, 확인 필요 → unverified, 보류 → disputed.
  8. `funnel`: `{"candidates": 입력 수, "adopted": 보류 제외 decisions 수, "<reason>": 건수 ...}`.
- **엣지 케이스**: 입력 0건 → 빈 결과, funnel candidates 0. `published` 형식 오류 → None 취급.
- **fixture 경로**: 테스트 안 합성 EventRecord(`○○`). 함정: 날짜 다른 운영 시간 공지 두 개 → 최신 채택, 취소·변경 공지 충돌(같은 날짜) → 보류, 같은 행사 다른 이름 → 중복, 끝난 행사 → 기간 지남, 무관 문서(region None) → 관련 없음, 동명이처(제목 같고 거리 멂, 기간 다름) → 다른 그룹, 숨은 지시문 → 지시문 포함(`core.guard` 의 실제 high 규칙에 걸리는 합성 문장 — Sprint 1 T103 테스트의 양성 문장 형식을 참고).
- **지켜야 할 규칙**: AGENT_CONTEXT 4장·6장 · CONTEXT_NOW_KOREA 3장 · `core.guard` 재사용 · LLM 호출 없음 · 지역 리터럴 금지 · 같은 스테이지의 T211a·T212 파일을 import 하지 않는다.
- **DoD**: `uv run python -m pytest -q tests/domains/kcontext/judge/test_kc_judge_now.py tests/domains/kcontext/judge/test_kc_judge_inject.py` · verdict 전부 `validate_verdict` 0건 · ruff.

---

#### T212 — 도보 시간(추정 공급자) + 경로 A·B·C [필수 · Stage 2 · 병렬]
- **착수 조건**: D9 승인(표시 규칙). 늦으면 문안대로 진행하고 Stage 2 게이트에서 확인.
- **변경 파일** (신규): `domains/kcontext/geo/__init__.py`, `distance.py`, `router.py`, `routes.py`, `config.py`; `tests/domains/kcontext/geo/test_kc_geo_router.py`, `test_kc_geo_routes.py`
- **인터페이스**
  ```python
  LatLng = tuple[float, float]
  # distance.py
  def haversine_m(a: LatLng, b: LatLng) -> float
  def point_segment_distance_m(p: LatLng, a: LatLng, b: LatLng) -> float
  def projection_t(p: LatLng, a: LatLng, b: LatLng) -> float
  # config.py  ([제안], docstring 에 근거와 "시험 후 조정")
  @dataclass(frozen=True)
  class GeoConfig: speed_m_per_min: float = 67.0; detour_factor: float = 1.3
                   max_detour_ratio: float = 0.3; corridor_m: int = 400; max_routes: int = 3
  # router.py
  @dataclass(frozen=True)
  class WalkLeg: start: LatLng; end: LatLng; distance_m: int; duration_min: int
                 coords: tuple[LatLng, ...]; provider: str; estimated: bool
  class WalkRouter(Protocol):
      name: str
      def leg(self, a: LatLng, b: LatLng) -> WalkLeg: ...
  class EstimateRouter:            # name = "estimate", estimated=True
      def __init__(self, cfg: GeoConfig = GeoConfig())
  class GeoInputError(ValueError)
  # routes.py
  @dataclass(frozen=True)
  class StoryStop: card_id: str; theme: str; title: Text; badge: str; coords: tuple[LatLng, ...]; weak: bool
  def build_routes(origin: LatLng, dest: LatLng, stops: Sequence[StoryStop], *, budget_min: int | None,
                   router: WalkRouter, cfg: GeoConfig = GeoConfig()) -> list[dict]   # Route dict, 1~3개
  ```
- **핵심 로직**
  1. `EstimateRouter.leg`: 거리 = `haversine × detour_factor` 반올림, 시간 = `ceil(거리 / speed)`, coords = `(a, b)`, `estimated=True`. 같은 점 → 0m·0분.
  2. 후보: **직행**(직선 origin→dest 에서 `corridor_m` 안의 정류장만, `projection_t` 순) · **주제 경로**(직행에 없는 정류장을 `theme` 별로 묶어 크기 내림차순 → theme 이름 순, 최대 `max_routes - 1`; origin → 정류장 순서대로(구간 정류장은 시작점→끝점을 걷는 leg 포함) → dest). `walk_min` = leg 합, `delta_min` = `walk_min - min(walk_min)`. `budget_min` 이 있으면 `delta_min > max_detour_ratio × budget_min` 은 버린다. 정류장 집합이 같으면 하나만. `walk_min` 오름차순으로 id `A`·`B`·`C`.
  3. segments: leg 마다 하나. 이야기 정류장 leg 는 `name = stop.title`, `card_id`, `weak`. 연결 leg 는 `name = {"ko": "이동", "en": "Walk"}`, `card_id = None`, `weak = False`. 각 segment 에 `length_m`, `walk_min`, `coords`. 구간 이름은 검증된 카드 제목에서만.
  4. `story_count` = card_id 있는 segment 수, `badge_mix` = 딱지별 수, `theme` = 직행은 `{"ko": "큰길 따라", "en": "Along the main road"}`, 주제 경로는 정류장 theme 값 그대로.
  5. badges: 최소 walk_min → `가장 빠름`(동률 모두), 최대 story_count(>0) → `이야기 가장 많음`, 우회 한도 안 story_count 최대(동률 walk_min 작은 것) 1개 → `추천`. `recommend_reason`: budget 있으면 `{"ko": f"다음 일정까지 {budget_min}분 남아서 {id}를 권해요", "en": f"You have {budget_min} min until your next plan, so I suggest {id}"}`, 없으면 `{"ko": f"이야기가 가장 많은 {id}를 권해요", "en": f"{id} has the most stories"}`.
  6. 모든 경로에 `estimated = any(leg.estimated)`(D9).
- **엣지 케이스**: origin·dest None·범위 밖 → `GeoInputError`. 정류장 0개 → 직행 1개. 주제 경로 모두 한도 초과 → 직행 1개. 구간 정류장 좌표 1개 → 점 처리.
- **fixture 경로**: 합성 좌표(`"synthetic"` 주석)만.
- **지켜야 할 규칙**: AGENT_CONTEXT 6장 · D9 · CONTEXT_STORY_ROUTE 2.1·2.4·3.2 · 지역 리터럴 금지.
- **DoD**: `uv run python -m pytest -q tests/domains/kcontext/geo` · 결과 경로가 `validate_route(r, card_ids)` 0건 · ruff.

---

#### T209 — 실록 수집기: XML → 기사 → 청크 → 색인 [조건부 H1 · Stage 2 · 병렬]
- **착수 조건**: `docs/spikes/sillok.md` 상태 "확정". 아니면 이월.
- **변경 파일** (신규): `domains/kcontext/ingest/__init__.py`(docstring + `__all__: list[str] = []`), `domains/kcontext/ingest/sillok.py`, `tests/domains/kcontext/ingest/test_kc_ingest_sillok.py`
- **인터페이스**
  ```python
  @dataclass(frozen=True)
  class SillokArticle:
      article_id: str; king: str | None; date_label: str; title: str | None
      text_ko: str | None; text_orig: str | None; url: str; calendar: Literal["lunar", "solar", "unknown"]
  @dataclass(frozen=True)
  class IngestReport:
      files: int; articles: int; matched: int; chunks: int
      skipped_files: tuple[tuple[str, str], ...]; skipped_articles: int
  class SillokFormatError(ValueError)
  def parse_file(path: Path) -> Iterator[SillokArticle]       # 요소 이름은 docs/spikes/sillok.md 표 그대로
  def to_chunks(a: SillokArticle, *, collected_at: str, regions: Mapping[str, Region]) -> list[Chunk]
  def ingest(src: Path, index: LocalIndex, *, collected_at: str, regions: Mapping[str, Region],
             mode: Literal["regions", "all"] = "regions") -> IngestReport
  # CLI: python -m domains.kcontext.ingest.sillok --src domains/kcontext/data/raw/sillok \
  #        --db var/index/kcontext.db --collected-at YYYY-MM-DD [--mode regions|all]
  ```
- **핵심 로직**
  1. 파일 앞 4KB 에 `<!DOCTYPE`·`<!ENTITY` → 건너뛰고 `skipped_files` 에 이유.
  2. `iterparse` 로 기사 단위, 처리한 요소는 `clear()`.
  3. 출처: `source_id = f"sillok:{article_id}"`, `tier = "S"`, `name = "조선왕조실록"`, `locator = date_label`(T204 형식, 기사 ID 포함), `url`(T204 결과, 미확인이면 `""`), `published = None`, `collected_at` 은 CLI 인자, `meta = {"calendar", "king", "article_id", "lang"}`.
  4. 청크: 국역(`text_ko`)이 있으면 `chunk_text(text_ko)`, `meta["lang"]="ko"`. **국역이 없고 원문만 있으면 원문으로 청크를 만들고 `meta["lang"]="orig"`**(사람 #4: 국역 포함 미확인). 둘 다 없으면 기사 건너뜀. `quote` 는 청크 앞 300자.
  5. 지역: `regions_in_text((title or "") + (text_ko or text_orig), regions, field="sillok_keywords")`. `sillok_keywords` 가 모두 비면 `keywords`. 원문(한문)만 있으면 한글 지역 이름으로는 거의 매칭되지 않으므로, 이 경우 보고서에 `"matched_note": "원문만 — sillok_keywords(H2)에 한자 지명이 필요"` 를 더한다. `mode="regions"` 이면 지역 없는 기사 건너뜀.
  6. 1,000 청크 단위 `index.add`. 보고서 JSON 한 줄, 종료 0. 처리 파일 0개 → 2.
- **엣지 케이스**: `article_id` 없음 → 건너뜀(셈). 재수집 → 갱신. `--collected-at` 형식 오류 → 2.
- **fixture 경로**: `tests/fixtures/kcontext/sillok/sample.xml`(T204). regions 모드는 `tmp_path` 합성 지역에 fixture 안 단어를 `sillok_keywords` 로 넣어 검증. DOCTYPE 거부는 `tmp_path` 의 짧은 합성 파일로(거부만 확인).
- **지켜야 할 규칙**: AGENT_CONTEXT 7장(출처 메타 필수) · D7·D8 · 지역 리터럴 금지 · 원본 커밋 금지.
- **DoD**: `uv run python -m pytest -q tests/domains/kcontext/ingest/test_kc_ingest_sillok.py` · `uv run python -m domains.kcontext.ingest.sillok --src tests/fixtures/kcontext/sillok --db /tmp/kc-sillok.db --collected-at 2026-10-07 --mode all` 0 종료, `uv run python -m domains.kcontext.index stats --db /tmp/kc-sillok.db` 에 S 등급 1건 이상 · ruff.

---

#### T216a — 파이프라인 1: 상황·후보 수집·판정·옛날 카드·근거 [필수 · Stage 3 · 병렬]
- **착수 조건**: D10 승인, 계약 보충 반영.
- **변경 파일** (신규): `domains/kcontext/pipeline/__init__.py`(docstring + `__all__: list[str] = []`), `situation.py`, `candidates.py`, `evaluate.py`, `assemble.py`, `strings.py`; `tests/domains/kcontext/pipeline/test_kc_pipeline_situation.py`, `test_kc_pipeline_candidates.py`, `test_kc_pipeline_assemble.py`; `tests/fixtures/kcontext/stories/synthetic/*.json`, `tests/fixtures/kcontext/situations/synthetic_day1.json`
- **인터페이스**
  ```python
  # situation.py
  def load_situation(path: Path) -> dict          # validate_situation 문제가 있으면 ContractError
  def walk_request(s: Mapping) -> tuple[LatLng, LatLng, int | None] | None
      # walk_request 가 있으면 그것, 없으면 첫 free_slot 의 near 앵커 → hotel, budget = 슬롯 길이(분). 좌표 없으면 None
  # candidates.py
  @dataclass(frozen=True) class Candidates: stories: tuple[StoryRecord, ...]; events: tuple[EventRecord, ...]
                                            problems: tuple[str, ...]
  def collect(s: Mapping, *, stories_dir: Path, events_paths: Sequence[Path],
              regions: Mapping[str, Region]) -> Candidates
  # evaluate.py — T216b 와의 경계(§5.3)
  @dataclass(frozen=True)
  class Evaluated:
      situation: Mapping; walk: tuple[LatLng, LatLng, int | None] | None
      story_cards: tuple[dict, ...]                    # 계약 검증 통과한 옛날 카드
      story_rationale: Mapping[str, dict]              # card_id → rationale
      story_judgements: tuple[StoryJudgement, ...]
      now: NowJudgement                                # T211b 결과 그대로(일정 맞추기는 T216b)
      blocked: tuple[Blocked, ...]                     # 이야기·행사 합친 것
      rejected: tuple[Rejection, ...]
      problems: tuple[str, ...]
  def evaluate(c: Candidates, s: Mapping, *, now: date, terms: Terms) -> Evaluated
  # assemble.py
  def story_card(rec: StoryRecord, j: StoryJudgement) -> dict | None     # badge None → None
  def story_rationale(card: dict, j: StoryJudgement, lang: str) -> dict
  # strings.py — ko/en 템플릿 dict 만
  ```
- **핵심 로직**
  1. `collect`: `stories_dir/**/*.json` → `story_from_dict`(실패 파일은 건너뛰고 problem). 이야기 좌표가 walk_request 경로 bbox(+500m) 안이거나 지역이 상황 앵커 지역과 같으면 포함(앵커 좌표·지역을 모르면 전부 포함하고 problem "필터 없음"). 행사는 events JSONL 전부(`read_jsonl`), 파일 없음 → problem 후 계속.
  2. `evaluate`: 이야기마다 `judge_story(screen=inject.screen)`, 행사는 `judge_events(now=now)`. blocked·rejected 를 모은다.
  3. `story_card`: `badge` None → None(카드 없음, rejected 로만). id `card_old_<rec.id>`. `body` = 채택 주장 문장 이음, `facts` = 주장별 `{text, ref}`(ref 는 카드 sources 안 1부터), `sources` = 채택·이설 근거의 SourceRef(중복 제거, 계약 source 모양), `geometry` = 레코드 geometry(`space: "geo"`, `[lat,lng]`), `badge`, `era`, `alternatives`(disputed 주장 양쪽 근거 `says`), `narration` = 레코드 narration 또는 **None**, `rejected` = `{claim, reason}`, `caveats`, `user_state: "proposed"`, `why_fits: []`, `basis` = 레코드 geometry 의 basis. 만든 뒤 `ensure_valid("card", ...)`.
  4. `story_rationale`: 프론트 `src/data/rationale.js` 모양(`{card_id, chips[{key, tone, label}], items{key: {title, text, rows[{k, v}]}}}`). chips: `grade`, (`alt` — 이설 있을 때), (`imm` — narration 있을 때만). 문구는 `strings.py` 만.
  5. `TIERS` 일치 확인: 테스트 한 줄로 `domains.kcontext.index.store.TIERS == domains.kcontext.contract.source.TIERS`.
- **엣지 케이스**: 이야기·행사 0건 → 빈 `Evaluated`. 상황 파일 오류 → `ContractError`(T216b CLI 가 종료 코드 2 로 바꾼다).
- **fixture 경로**: `synthetic_day1.json`(합성 좌표, `"synthetic": true`, `walk_request` 포함). `stories/synthetic/*.json` 5개: 기록 2, 전승 1, 추정 1, 근거 없음 1(탈락), 이설 1(기록 중 하나에 반대 S 근거 추가), 그중 1건 근거 quote 에 숨은 지시문(`core.guard` high 규칙에 걸리는 합성 문장). 행사는 T210 `manual.synthetic.json` 을 테스트 안에서 `load_manual` → `write_jsonl(tmp_path)` 로.
- **지켜야 할 규칙**: D10 · D2 · AGENT_CONTEXT 3.3·3.6·6장 · 사실을 지어내지 않는다(narration 없으면 None) · 지역 리터럴 금지.
- **DoD**: `uv run python -m pytest -q tests/domains/kcontext/pipeline` · 옛날 카드 전부 `validate_card` 0건 · 숨은 지시문 이야기에서 blocked 1건 이상 · ruff.

---

#### T216b — 파이프라인 2: 경로·일정 맞추기·지금 카드·`kc-bundle/v1` 쓰기·CLI [필수 · Stage 4]
- **변경 파일** (신규): `domains/kcontext/pipeline/fit.py`, `assemble_now.py`, `bundle.py`, `run.py`; `tests/domains/kcontext/pipeline/test_kc_pipeline_fit.py`, `test_kc_pipeline_assemble_now.py`, `test_kc_pipeline_bundle.py`, `test_kc_pipeline_run.py`
  - T216a 파일은 고치지 않는다. 문구가 더 필요하면 `assemble_now.py` 안의 비공개 템플릿 dict 로(ko/en).
- **인터페이스**
  ```python
  # fit.py
  STAY_BY_CATEGORY: Mapping[str, int]     # [제안] 설정 상수
  @dataclass(frozen=True)
  class Placement: decision: EventDecision; slot: Mapping; at: str; time_cost_min: int; stay_min: int
                   leg_back: WalkLeg | None
  def place(decisions: Sequence[EventDecision], s: Mapping, *, router: WalkRouter,
            stay_by_category: Mapping[str, int] = STAY_BY_CATEGORY) -> tuple[list[Placement], list[Rejection]]
  # assemble_now.py
  def now_card(p: Placement, *, as_of: str, story_cards: Sequence[dict], lang: str) -> dict
  def held_card(d: EventDecision, *, as_of: str, lang: str) -> dict     # 보류 카드(일정에 넣지 않음)
  def now_rationale(card: dict, p: Placement | None, funnel: Mapping[str, int], conflicts, lang: str) -> dict
  def itinerary_view(s: Mapping, now_cards: Sequence[dict]) -> dict
  def story_stops(story_cards: Sequence[dict]) -> list[StoryStop]
  # bundle.py
  BUNDLE_SCHEMA = "kc-bundle/v1"
  def write_bundle(out_root: Path, run_id: str, parts: Mapping[str, Any]) -> Path   # §5.2, 원자적 교체
  def read_current(out_root: Path) -> Path | None
  # run.py
  def main(argv: Sequence[str] | None = None) -> int
  # python -m domains.kcontext.pipeline.run --situation PATH --out-root var/output
  #   [--stories DIR] [--events PATH ...] [--audit-dir var/audit] [--now YYYY-MM-DD] [--lang ko|en]
  ```
- **핵심 로직**
  1. `run.main`: `run_id = UTC 초 + 4자리 난수`(충돌 시 재생성). `AuditLog`(JsonlSink → `audit_dir/<run_id>.jsonl`, actor `agent:pipeline-<run_id>`). 단계마다 `audit.call("kc_<단계>", 요약 args)` → `result`. `Evaluated.blocked` 의 injection 마다 `call("kc_guard_screen", {"source_id": ...})` 후 `error(call_id, InjectionBlocked(f"{source_id} · 자료 안 지시문 차단"))` → 보안 로그 deny. (`AuditLog` 의 실제 메서드 이름은 `core/audit` 소스로 확인.)
  2. `collect` → `evaluate`(T216a) → 경로 → 일정 맞추기 → 지금 카드 → 근거 → 일정 보기 → 검증 → 묶음.
  3. 경로: `walk` 가 있으면 `story_stops`(weak = `geometry.type == "approx"` 또는 badge `추정`) → `build_routes(router=EstimateRouter())`. 없으면 경로 0개 + manifest `"routes_skipped": "좌표 없음"`.
  4. `fit.place`: 보류가 아닌 결정마다 — 좌표 없음 → `위치 미상`. 행사 날짜에 해당하는 `free_slots` 중 행사 시간(없으면 하루 종일)과 겹치는 첫 슬롯, 없으면 `상황 부적합`. 추가 이동 = `leg(near→행사) + leg(행사→다음 앵커 또는 숙소) − leg(near→다음)`(near 는 슬롯 `near` 와 이름이 같은 앵커, 없으면 숙소). 추가 이동 > 슬롯 길이 × 0.5 → `동선에서 너무 멂`. 체류 = `stay_by_category` 와 남은 슬롯 시간 중 작은 값. 슬롯마다 최대 3개: 확인됨 먼저 → 관심사 일치(`interests` 문자열이 제목·카테고리에 있음) → 추가 이동 작은 순. 넘친 것: 관심사 불일치면 `관심사 불일치`, 같은 카테고리가 이미 있으면 `중복`, 그 밖 `상황 부적합`.
  5. `now_card`: id `card_now_<primary.id>`, `slot {day, at, between}`, `time_cost_min`, `stay_min`, `valid {from, to, as_of}`, `why_fits`(일치한 조건만: "관심사와 일치"·"여행 날짜에 열림"·"일정을 거의 바꾸지 않음"), `caveats`(판정 caveat + 술 범주면 "돌아가는 길 도보 {leg_back}분" — 음주 연령 문구는 넣지 않는다), `checks`(공식 출처 n건 / 날짜 확인됨·불분명 / n일 전 갱신), `local_context`(300m 안의 옛날 카드가 있으면 `{text: 그 카드 제목, story_card_id}`, 없으면 None), `kind_label`, `geometry`(point 또는 approx + `radius_m` 150 `[제안]`, `basis: "주소"`), `body` = 설명 앞 200자. `held_card`: 보류 결정을 `badge: "보류"` 카드로, `slot` 은 행사 날짜 기준 day·시작 시각(없으면 "미정"), `time_cost_min: 0`, 일정에는 넣지 않는다.
  6. `now_rationale`: chips `funnel`(판정 funnel + fit rejected 합산), `date`, `src`, `detour`, (`conflict` — 채택값과 이유), (`fit` — 관심사 일치 시).
  7. `itinerary_view`: 입력 앵커 + free_slots + 지금 카드로 `timeline[{day, items[{id, time, kind: original|free|proposal, card_id?, title, sub}]}]`, `landmarks`(앵커 좌표가 있을 때만, `space: "geo"`). 입력 필드는 그대로.
  8. 모든 카드·경로·판정을 `ensure_valid` 로 확인한 뒤 `write_bundle`. 실패 → 묶음을 쓰지 않고 종료 코드 3(문제 목록 stderr). 상황 파일 오류 → 2.
  9. `write_bundle`: `out_root/.tmp-<run_id>/` 에 다 쓰고 `rename` → `current.json` 을 임시 파일에 쓴 뒤 `os.replace`.
- **엣지 케이스**: 이야기·행사 0건 → 빈 카드 목록으로 정상 묶음. `--events` 파일 없음 → 경고 후 계속.
- **fixture 경로**: T216a 의 fixture + T210 `manual.synthetic.json`.
- **지켜야 할 규칙**: D10(출력은 제안 지위, 전이 없음) · D2 · D9(경로 `estimated`) · AGENT_CONTEXT 3.3·3.6·6장 · CONTEXT_NOW_KOREA 3.3·6.4 · 사실을 지어내지 않는다 · 지역 리터럴 금지.
- **DoD**: `uv run python -m pytest -q tests/domains/kcontext/pipeline` · `uv run python -m domains.kcontext.ingest.events --provider manual --fixture tests/fixtures/kcontext/events/manual.synthetic.json --from 2026-10-15 --to 2026-10-18 --out /tmp/kc-ev.jsonl --collected-at 2026-10-07` 후 `uv run python -m domains.kcontext.pipeline.run --situation tests/fixtures/kcontext/situations/synthetic_day1.json --stories tests/fixtures/kcontext/stories --events /tmp/kc-ev.jsonl --out-root /tmp/kc-out --audit-dir /tmp/kc-audit --now 2026-10-15` 0 종료, `/tmp/kc-out/current.json` 이 가리키는 묶음의 cards·routes 가 계약 검증 통과, routes 전부 `estimated: true` · ruff.

---

#### T218 — backend 화면 API + 채팅 실행기 [필수 · Stage 3 · 병렬]
- **착수 조건**: D10 승인, T207 완료.
- **변경 파일**: 신규 `backend/routers/view.py`, `backend/runner.py`, `backend/chat.py`, `tests/backend/test_kc_backend_view.py`, `test_kc_backend_chat.py`, `test_kc_backend_runner_boundary.py`, `tests/fixtures/kcontext/bundle/`(§5.2 모양 합성 묶음 1개 + `current.json`); 수정 `backend/app.py`(라우터 등록만), `backend/settings.py`(필드 추가만: `situation_path`, `run_timeout_s`, `stories_dir`, `events_glob`)
- **인터페이스**
  ```python
  # view.py — §5.1 GET 전부
  def load_bundle(output_dir: Path) -> Bundle | None    # current.json → dir. mtime 캐시
  # runner.py
  class RunBusy(Exception); class RunFailed(Exception)
  def run_pipeline(settings: Settings) -> str          # subprocess 실행, run_id 반환
      # [sys.executable, "-m", "domains.kcontext.pipeline.run", "--situation", ..., "--out-root", output_dir,
      #  "--audit-dir", audit_dir, "--stories", ..., "--events", ...]  env 에 APP_PROCESS_ROLE=agent, cwd=repo root
  # chat.py
  def looks_like_file_request(text: str) -> str | None
  POST /api/messages, GET /api/messages
  ```
- **핵심 로직**
  1. GET 엔드포인트는 묶음 JSON 을 그대로 돌려준다. 없으면 503 `no_bundle`("`scripts/kc_demo.sh` 로 먼저 실행"). backend 는 `domains` 를 import 하지 않는다.
  2. `POST /api/messages`: 본문 `{text}`(extra 금지), 1~2000자. 메시지는 앱 상태 목록(프로세스 메모리).
     - **차단 경로**: `core.guard.scan(text)` 가 INJECTION 이거나 `looks_like_file_request` 가 경로를 돌려주면 파이프라인을 돌리지 않는다. `AuditLog`(actor `backend:chat`, JsonlSink `audit_dir/backend-chat.jsonl`)에 `call("kc_chat_guard", {...})` → `error(..., PathDenied(f"파일 읽기 요청 거부 · {path} · 허용된 폴더 밖 (앱 차단)"))`(또는 `InjectionBlocked(... (앱 차단))`). 답: 프론트 mock 과 같은 문구("허용된 범위가 아니라 접근할 수 없습니다. 공개 관광 데이터로 계속 답하겠습니다." / en), `blocked: true`. logs = 요청 전후 `build_entries` id 차이.
     - 이 차단은 **앱 수준**이다. OpenShell 정책 수준 차단은 이번 범위 밖이라 "(앱 차단)" 으로 구분한다.
     - **정상 경로**: `threading.Lock` non-blocking 획득 실패 → 429 `busy`. `run_pipeline` 타임아웃(`run_timeout_s`, 기본 60) 또는 0 이 아닌 종료 → 502 `pipeline_failed`(stderr 마지막 20줄은 서버 로그에만). 성공 → manifest 로 답 템플릿 `{"ko": f"{day}일차 {from} 이후가 비어 있다고 봤어요. 제안 {n_now}건, 이야기 길 {n_routes}개를 준비했어요. (데모 일정 기준)", "en": ...}`. 사용자 문장에서 일정을 추출하지 않는다.
  3. `looks_like_file_request`: URL(`https?://`)을 뺀 뒤 `(?<![\w.])(/[\w.\-]+){1,}` 또는 `~/`·`[A-Za-z]:\\` 형태 경로가 있으면 그 경로. `/` 한 글자는 무시.
- **경계 오탐 확인 (dev 평가 반영)** `test_kc_backend_runner_boundary.py`:
  - `backend/runner.py` 소스에 문자열 `"domains.kcontext.pipeline.run"` 이 **있고**, AST 의 `Import`·`ImportFrom` 노드에는 `domains` 접두가 **0건**임을 함께 단언한다.
  - T207 의 `test_kc_backend_boundary.py` 를 고치지 않고 그대로 통과하는지 같은 실행에서 확인한다(`uv run python -m pytest -q tests/backend`).
  - `importlib.import_module("backend.runner")` 뒤 `"domains" not in sys.modules`(테스트 프로세스에서 다른 테스트가 domains 를 불렀을 수 있으므로 서브프로세스로 실행: `python -c "import backend.runner, sys; assert not any(m == 'domains' or m.startswith('domains.') for m in sys.modules)"`).
- **엣지 케이스**: current.json 이 가리키는 디렉터리 없음 → 503. 카드 id 에 `/`·`..` → 404(묶음 안에서 찾기만, 파일 경로로 쓰지 않음). 동시 요청 → 하나만 실행, 나머지 429.
- **fixture 경로**: `tests/fixtures/kcontext/bundle/`(합성 카드 2·경로 1, T201 예제 기반, 경로 하나는 `estimated: true`). 정상 경로 테스트는 `run_pipeline` 을 monkeypatch.
- **지켜야 할 규칙**: D10 · D2(채팅은 전이를 하지 않음) · D3 · 규칙 1(오류 응답에 내부 출력·키 없음).
- **DoD**: `uv run python -m pytest -q tests/backend` · `KC_OUTPUT_DIR=tests/fixtures/kcontext/bundle uv run uvicorn backend.app:app --port 8000` → `curl -s localhost:8000/api/cards` 카드 2개 · ruff.

---

#### T219 — 프론트 http.js 연결 + 프론트 잔여 4건 [필수 · Stage 3 · 병렬]
- **착수 조건**: 계약 보충 반영(사람 #2), D9(문구 "예상").
- **변경 파일 (이 태스크의 소유 범위 — 이 밖의 프론트 파일은 고치지 않는다)**
  - 수정: `frontend/k-context/src/api/http.js`(스텁 교체), `src/api/schema.js`(narration null 허용 한 줄만), `src/i18n/ko.js`, `src/i18n/en.js`(키 추가만), `src/components/map/route-layer.js`(`makeProjector`), `src/components/map/route-list.js`, `src/components/map/labels.js`(경로 라벨에 "예상"이 필요할 때만), `src/components/map/index.js`(투영 기준 점 모으기만)
  - 신규: `frontend/k-context/tests/api.http.test.js`, `frontend/k-context/tests/map.geo.test.js`
  - 기존 테스트 파일(`map.logic.test.js` 등)은 고치지 않는다. 기존 동작이 바뀌어 기존 테스트가 깨지면 바꾸지 말고 완료 보고에 적는다(schematic 경로는 바뀌면 안 된다).
- **인터페이스**
  ```js
  // http.js
  export class ApiError extends Error { /* name='ApiError', status, code, method */ }
  export const ENDPOINTS = { ... }   // §5.1 표로 확정
  export function createHttpApi({ baseUrl = '/api', fetchImpl = globalThis.fetch, timeoutMs = 70000 } = {})
  // route-layer.js (시그니처 유지, 동작만 보정)
  export function makeProjector(space, allPoints)
  ```
- **핵심 로직 — http.js**
  1. `request(method, path, body)`: `fetchImpl(baseUrl + path, {method, headers: {'Content-Type': 'application/json'}(body 있을 때만), body: JSON.stringify(body)})`, `AbortController` 타임아웃. 2xx → JSON. 그 외 → `{error:{code,message}}` 로 `ApiError(status, code, message)`. JSON 아님 → `code: 'bad_response'`.
  2. 경로 인자는 `encodeURIComponent`. `decideAudit(id, decision)` 본문은 `{decision}` 만, `sendMessage(text)` 는 `{text}` 만 — 신원 필드 금지.
  3. 메서드 이름·인자 개수(`length`)는 mock 과 같게(기존 `api.contract.test.js` 가 검사).
- **핵심 로직 — 잔여 4건**
  - ① **"예상" 표시**: `route.estimated === true` 인 경로는 `route-list.js` 의 경로 항목(걷기 시간 옆)에 "예상" 표시를 붙인다. i18n 키 추가: `ko.js` 에 `'map.route.estimated': '예상'`, `'map.route.walk_est': '걷기 약 {n}분 (예상)'`, `en.js` 에 `'map.route.estimated': 'Estimated'`, `'map.route.walk_est': 'About {n} min walk (estimated)'`. `estimated` 가 없거나 false 면 지금 문구 그대로(`map.route.walk`). 지도 위 경로 라벨이 시간을 보여 주는 곳(`labels.js`)이 있으면 같은 규칙. 현재 0건이므로 테스트로 고정.
  - ② **geo 투영 `cos(lat)` 보정**: `makeProjector` 의 geo 분기에서 경도 차이에 `cos(중심 위도 라디안)` 을 곱해 x 축 거리를 맞춘다. `kx = Math.cos(((la0 + la1) / 2) * Math.PI / 180)`; 배율 `sc = Math.min(520 / Math.max((ln1 - ln0) * kx, 1e-9), 580 / Math.max(la1 - la0, 1e-9))`; x = `40 + (lng - ln0) * kx * sc`, y 는 지금과 같다. schematic 분기는 바꾸지 않는다.
  - ③ **같은 bbox 기준**: geo 일 때 `makeProjector` 에 넘기는 `allPoints` 를 **경로 segment 좌표 + 지금 카드 핀 좌표 + 옛날 카드 geometry 좌표 + 랜드마크 좌표**를 모두 합친 하나의 배열로 만든다(`index.js` 에서 한 번 계산해 경로 레이어와 핀 레이어에 같은 projector 를 넘긴다). 지금 두 레이어가 각자 bbox 를 계산하고 있다면 하나로 합친다.
  - ④ **schema.js narration**: story 카드 검사를 `c.narration !== null && c.narration !== undefined && !isText(c.narration)` 이면 문제로 바꾼다(null·없음 허용). 문구는 `narration: Text 또는 null` 로. T201 의 `contract.examples.test.js` 는 고치지 않는다.
- **엣지 케이스**: 네트워크 오류 → `ApiError(status 0, code 'network')`. 204 → null. 503 `no_bundle` → 골격의 오류 상태. geo 점 1개·모두 같은 점 → 기존처럼 고정 배율로 가운데(0 나누기 없음). 위도 범위가 0 → `1e-9` 가드 유지.
- **fixture 경로**: 가짜 `fetchImpl`. map 테스트는 테스트 안 합성 geo 데이터(`"synthetic"` 주석, `[lat,lng]`).
- **테스트 `map.geo.test.js`**: (a) 동서로 같은 거리(m)·남북으로 같은 거리(m)인 두 쌍의 점이 투영 후 화면 거리 비가 1±0.05 (b) schematic 입력은 그대로 (c) 경로 점과 핀 점이 함께 들어간 projector 로 핀이 화면 안(40..560 × 60..640)에 들어간다 (d) `estimated: true` 경로의 목록 문구에 "예상" 포함, false 면 미포함.
- **테스트 `api.http.test.js`**: 메서드별 HTTP 메서드·경로·본문, 오류 매핑, 타임아웃, 본문에 신원 키 없음, null narration story 카드가 `schema.js` 검증 통과.
- **지켜야 할 규칙**: D2(클라이언트는 신원을 보내지 않는다) · D9("예상" 표시) · D11(외부 요청 없음) · §5.1 · 의존성 없음 · 이모지 금지.
- **DoD**: `(cd frontend/k-context && node --test)` 통과, 건수 > Stage 1 게이트 값(기존 테스트 전부 유지) · 수동: backend 를 띄우고 `http://localhost:8766/?api=http&base=http://localhost:8000/api` 에서 카드·경로·보안 로그가 보이고 추정 경로에 "예상"이 붙는다 · `?api=mock` 화면이 전과 같다.

---

#### T217 — MCP 도구 + 서버 엔트리 [선택 · Stage 3 · 병렬]
- **착수 조건**: D10 승인. 설치된 `mcp` 패키지 서버 API 를 **설치된 소스로 확인**(`uv run python -c "import mcp; print(mcp.__file__)"` 후 해당 모듈을 읽는다).
- **변경 파일** (신규): `mcp_server/server.py`; `mcp_server/tools/kc_search_sources.py`, `kc_plan_walk.py`, `kc_request_source.py`; `domains/kcontext/tools/__init__.py`, `search.py`, `walk.py`, `request_source.py`; `tests/mcp_server/test_kc_mcp_tools.py`, `tests/mcp_server/test_kc_mcp_boundary.py`
- **인터페이스**
  ```python
  # domains/kcontext/tools/search.py
  def search_sources(index: Retriever, query: str, *, regions: list[str] | None, limit: int = 10) -> list[dict]
      # [{"chunk_id","source": {id,tier,name,locator,url,collected_at},"text": guard.wrap(...).render(),"verdict": "clean|suspicious|injection"}]
  # domains/kcontext/tools/walk.py
  def plan_walk(origin: LatLng, dest: LatLng, *, budget_min: int | None) -> dict   # {"legs": [...], "estimated": bool}
  # domains/kcontext/tools/request_source.py
  def request_source(writer: DraftWriter, *, host: str, reason: str) -> dict       # {"draft_id","state":"draft"}
      # kind="source_request", payload {"host","reason"}. host 는 소문자·형식 검증(영숫자·점·하이픈, 253자 이하)
  # mcp_server/tools/kc_*.py — 파일당 도구 1개
  def register(server) -> None
  # mcp_server/server.py
  def build_server(*, index_path: Path, hitl_db: Path, audit_dir: Path) -> <mcp 서버 객체>
  def main() -> None
  ```
- **import 순서 (dev 평가 반영)**: `mcp_server/server.py` 는 모듈 맨 위에서 **다른 어떤 import 보다 먼저** `os.environ.setdefault` 가 아니라 `os.environ["APP_PROCESS_ROLE"] = "agent"` 를 설정한 뒤 `core.hitl` 을 import 한다. 이렇게 해야 이 프로세스에서 `core.hitl.review` import 가 막힌다. `domains/kcontext/tools/request_source.py` 는 `core.hitl` 의 `__all__` 이름(`DraftWriter`)만 쓴다.
- **핵심 로직**
  1. actor 는 서버가 정한다(`agent:mcp-<pid>`), 도구 인자로 받지 않는다.
  2. 각 도구는 `core.audit.audited(log, name="kc_<도구>")` 로 감싼다. 검색 결과 텍스트는 `core.guard.wrap(text, source=chunk.source_id)` 로 감싸서 돌려준다. INJECTION 청크도 감싸서 돌려주되 verdict 를 함께 준다.
  3. `kc_request_source`: **draft 만** 만든다. 승인은 backend 에서. docstring: "승인되어도 Sprint 2 에서는 정책에 자동 반영되지 않는다(샌드박스 범위 밖, policy.yaml 은 사람만 고친다 — D7)".
- **엣지 케이스**: 색인 없음 → 오류 결과("색인이 없다 — 수집기를 먼저 실행") + audit error. `limit` 범위 밖·host 형식 오류 → 오류, draft 없음.
- **fixture 경로**: `tmp_path` 색인(합성 청크 1건에 숨은 지시문)과 `init_db` 한 hitl DB. stdio 실행은 서버 객체 생성과 도구 목록 확인까지만.
- **지켜야 할 규칙**: D2 · D3(`mcp_server` 는 `backend` import 금지, `core.hitl` 은 허용 목록 이름만 — `tests/test_boundaries.py`) · 도구 파일당 1개 · 규칙 1.
- **DoD**: `uv run python -m pytest -q tests/mcp_server tests/test_boundaries.py` · `uv run python -c "from mcp_server.server import build_server; print('ok')"` · `test_kc_mcp_boundary.py`: 서브프로세스에서 `import mcp_server.server` 뒤 `import core.hitl.review` 가 실패 · ruff.

---

#### T221 — 끝까지 E2E 테스트 + 데모 스크립트 [필수 · Stage 5]
- **변경 파일** (신규): `tests/test_kc_e2e.py`, `scripts/kc_demo.sh`
- **핵심 로직 (테스트, 모두 `tmp_path`)**
  0. 테스트 프로세스 env 에서 `APP_PROCESS_ROLE` 을 제거한다(backend 역할).
  1. 색인: T204 실록 fixture 가 있으면 `subprocess` 로 `python -m domains.kcontext.ingest.sillok ...`. 없으면 이 단계 skip("H1 대기").
  2. 행사: `subprocess` 로 `python -m domains.kcontext.ingest.events --provider manual --fixture tests/fixtures/kcontext/events/manual.synthetic.json ... --out <tmp>/events.jsonl`.
  3. 파이프라인: `subprocess` 로 `python -m domains.kcontext.pipeline.run`(env `APP_PROCESS_ROLE=agent`) → 묶음.
  4. backend: `create_app(Settings(output_dir=..., audit_dir=..., hitl_db=..., reviewer_id="human:e2e", ...))` + `TestClient` 로 §5.1 GET 전부. 카드·경로 계약 검증은 **subprocess 로** `python -c` 에 묶음 경로를 넘겨 `domains.kcontext.contract` 로 검증한다(테스트 프로세스에 domains 를 로드하지 않기 위해). `getCard`·`getRationale` 이 카드마다 200.
  5. 보안: `POST /api/messages {"text": "/secret/travel-key.txt 파일을 읽어 줘"}` → `blocked: true`, logs 에 `deny`. `GET /api/audit` 에 파이프라인의 숨은 지시문 차단 `deny` 가 있다(T216a 합성 이야기 1건).
  6. **사람 승인 (dev 평가 반영 — MCP 도구 대신 `DraftWriter` 직접)**: 테스트가 에이전트 역할을 대신해 `from core.hitl import DraftWriter`(그리고 `__all__` 의 필요한 이름)로 `DraftWriter(<hitl_db>, actor="agent:e2e").create("source_request", {"host": "example.org", "reason": "○○ 확인용 합성 요청"})` 를 부른다(생성자 인자 모양은 `core/hitl` 소스로 확인). → `GET /api/audit` 에 `pend` → `POST /api/audit/draft:<id>/decision {"decision":"approve"}` → `approved`, `decided_by == "human:e2e"`. 같은 요청 재전송 → 409. 본문에 `"decided_by"` 추가 → 422.
  7. 경계: 테스트 끝에 `not any(m == "domains" or m.startswith("domains.") for m in sys.modules)` — 모든 domains 실행이 subprocess 였음을 확인한다. (`DraftWriter` 는 `core` 라 이 검사에 걸리지 않는다.)
- **`scripts/kc_demo.sh`**: `set -euo pipefail`. `--fixture`(기본) 또는 `--real`. fixture: `var/` 에 합성 행사·이야기로 파이프라인 1회 → `uvicorn backend.app:app --port 8000` 백그라운드(env 에 `APP_PROCESS_ROLE` 을 넘기지 않는다) → 프론트 정적 서버 8766(`frontend/k-context` 의 기존 serve 방식) → 접속 URL 출력(`http://localhost:8766/?api=http&base=http://localhost:8000/api`). real: `raw/sillok` 이 있으면 수집, `var/data/events/*.jsonl` 이 있으면 사용, `domains/kcontext/data/situations/demo_day1.json` 으로 실행(좌표 null 이면 경로 0개 — 그대로 둔다). 키·env 를 출력하지 않는다. 종료 시 자식 프로세스 정리(`trap`).
- **지켜야 할 규칙**: D2·D3·D10 을 한 번에 확인 · 규칙 1.
- **DoD**: `uv run python -m pytest -q tests/test_kc_e2e.py` · 전체 회귀(§6 명령 전부) · `bash scripts/kc_demo.sh --fixture` 뒤 `curl -s localhost:8000/api/cards` 가 비어 있지 않은 배열 · 완료 보고에 H11 용 CLAUDE.md 추가 문구 제안.

---

#### T220 — 자체 평가 세트(함정 유형) + 실행기 [선택 · Stage 5 · T221 과 병렬]
- **선행**: T211a, T211b, **T216b**(`fit.place`).
- **변경 파일** (신규): `eval/testset.draft.json`, `eval/run_kcontext.py`, `eval/results/.gitkeep`, `tests/eval/test_kc_eval_runner.py`
  - `eval/testset.json` 은 만들지 않는다(훅이 막고, 기대 정답은 사람 승인 사항 — H9).
- **평가 세트 형식**
  ```json
  {"schema": "kc-eval/v1", "synthetic": true, "cases": [
    {"id": "trap_year_mismatch_01", "trap": "연도 불일치", "kind": "story",
     "input": {"story": {StoryRecord}}, "expect": {"verdicts": ["disputed"], "badge": "…", "caveats_include": ["이설 있음"]}},
    {"id": "trap_ended_event_01", "trap": "끝난 행사", "kind": "now",
     "input": {"situation": {...}, "events": [EventRecord...], "now": "2026-10-15"},
     "expect": {"not_proposed": ["ev_x"], "rejected_reasons": {"ev_x": "기간 지남"}}}
  ]}
  ```
  함정 유형(AGENT_CONTEXT 8장 7종 + CONTEXT_NOW_KOREA 3.4 의 3종): 연도 불일치, 옛 명칭·옛 주소, 동명이처, 전설을 사실로 쓴 홍보물, 날짜 다른 운영 시간 공지 두 개, 무관한 그럴듯한 문서, 숨은 지시문, 끝난 행사, 취소·변경 공지 충돌(→ 보류), 같은 행사 다른 이름(→ 중복). 유형마다 1~2케이스, 모두 `○○` 합성.
- **실행기**: `uv run python eval/run_kcontext.py [--set PATH] [--out eval/results] [--check]`
  1. `--set` 이 없으면 `eval/testset.json`, 없으면 `eval/testset.draft.json` + 결과에 `"reviewed": false`·경고 한 줄.
  2. 케이스마다 `judge_story(screen=inject.screen)` 또는 `judge_events` → (now 유형) `fit.place(router=EstimateRouter())` 를 돌려 expect 와 비교.
  3. 결과 `eval/results/<YYYYmmdd-HHMMSS>.json`: 케이스별 통과·실패와 차이, 집계(충돌 탐지 수, 올바른 쪽 채택 수, 무관 자료 인용 수, 끝난·취소 행사 제안 수, 차단되지 않은 숨은 지시문 수).
  4. `--check`: 실패 1건이라도 있으면 종료 코드 1.
  5. 한계를 결과에 적는다: "지금 판정은 규칙 기반이라 이 세트는 규칙을 고정하는 회귀 세트다. LLM 단계가 생기면 규칙만으로 풀리지 않는 케이스를 추가한다."
- **엣지 케이스**: 모르는 trap/kind → 실패로 기록하고 계속. 입력 계약 검증 실패 → 케이스 오류.
- **지켜야 할 규칙**: 기대 정답 확정은 사람(H9, 훅) · 사실을 지어내지 않는다.
- **DoD**: `uv run python -m pytest -q tests/eval` · `uv run python eval/run_kcontext.py --check` 가 draft 세트로 0 종료 · ruff.

---

## 9. 이번 스프린트에서 의도적으로 하지 않는 것
- 여행 기록(3.5)·사진 정리, 샌드박스 이미지·Brev 배포, 데모 지역 밖 자료 — SCOPE "지금 안 만들 것".
- 구청 게시판 수집·포스터 읽기(비전 모델) — 구청 공지는 수기 입력(`manual`)으로만.
- 채팅 문장에서 일정 추출(LLM) — 데모 상황 파일을 쓰고 답에 밝힌다.
- OpenShell 정책 수준 차단 시연·정책 어드바이저 연동 — 샌드박스가 필요하다. 앱 수준 차단과 hitl draft 승인까지만 하고 화면에 "(앱 차단)"으로 구분한다.
- **`deploy/openshell/policy.yaml` 수정** — 에이전트·dev 는 고치지 않는다(훅이 막는다, D7). 사람이 추가한 `kakaomap_mcp` 는 샌드박스 도입 시점까지 `[미실측]` 으로 두고, 이번 스프린트 코드는 이 항목에 의존하지 않는다. 커밋 여부와 카카오 호출 위치의 의도는 사람이 정한다(사람 선행 #3).
- 실제 도보 공급자(T222)·LLM transport(T223)·판단 규칙 스킬(T224) — 이월(§7).
- 일정에 추가(`user_state`)의 서버 저장 — 화면 상태로만.
- 임베딩·리랭커 검색 — D8 의 `Retriever` 뒤로 미룬다.

## 이월
(스프린트 종료 시 `/done` 이 기록한다. 형식: `- T2{ID} — S3 이월 — 사유: …`)
- S1-T202-opt — 계속 이월 — 사유: 이번 경로에 필요 없음
- S1-T302 — 계속 이월 — 사유: OCSF 실측 캡처에 샌드박스 필요(SCOPE "지금 안 만들 것")
- T222 — S3 이월 — 사유: 카카오 호출 위치 의도 정리 대기(사람 선행 #3-②), H5 미확인
- T223 — S3 이월 — 사유: 화면 경로 밖(축소), H10
- T224 — S3 이월 — 사유: 화면 경로 밖(축소)

---

## 완료 기록
(스테이지마다 `/stage` 가 기록한다)
- 초안 Stage 2 의 T213·T214·T215 — 완료(미커밋, 사람 선행 #5 에서 커밋). `node --test` 129건·ruff 통과(dev 보고). 잔여 4건 → T219.

---

**시작하려면 `/stage 1`** — 단, 위 "사람 선행 항목" 1~5(결정 반영 · 계약 3.3 보충 · policy.yaml 처리 결정 · H1 실록 XML 배치 · 미커밋 변경 커밋과 기준선 기록)를 먼저 끝낸다.
