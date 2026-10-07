# Sprint 2 — 데이터 → 판정 → 화면 연결 (초안)

> 상태: **초안**(pm, 2026-10-07). dev 현실성 평가와 사람 승인(§2 결정 후보) 뒤에 `sprint-2.md` 로 확정한다.
> 시간 상자: 하루~이틀(2026-10-07~). 스테이지 4개. 소요 시간은 추정하지 않는다.
> 범위 근거: `docs/SCOPE.md` "Sprint 2 범위"의 "반드시 만들 것" 1~7. "지금 안 만들 것"(여행 기록·사진 정리, 샌드박스 이미지·Brev 배포, 데모 지역 밖 자료)은 어떤 태스크에도 넣지 않았다.
> 전제(태스크 아님): `frontend/k-context/` 기반 골격(모듈 슬롯 map/cards/chat/securitylog/rationale/timeline, `src/api/index.js` 의 mock|http 어댑터, `src/state/*`, `src/lib/*`)은 dev 가 지금 만들고 있다. Stage 2 의 프론트 태스크는 이 골격이 끝난 뒤에 시작한다.
> 태스크 ID: `T2{순번}`. Sprint 1 문서의 T201·T202 와 번호가 겹치므로 Sprint 1 태스크는 이 문서에서 **`S1-T202`** 처럼 접두사를 붙여 부른다.

## Sprint 2 실행 계획 요약

| 스테이지 | 태스크 | 병렬 | 결과물 |
|---|---|---|---|
| Stage 1 — 기반·확인 | T201 계약 · T202 로컬 색인 · T203 지역 설정 · T204 실록 스파이크 · T205 행사 API 스파이크 · T206 도보 경로 스파이크 · T207 승인·보안 로그 API · T208 (이월) 정책 초안 제출 | **8개 병렬**(디렉터리가 서로 다름) | 계약 검증기(py·js 공통 예제), FTS 색인, 지역 설정, 확인 문서 3개, `backend` 승인 API, `core/policy_proposer/submit.py` |
| Stage 2 — 수집·판정·화면 모듈 | T209 실록 수집 · T210 행사 수집·정규화 · T211 판정 엔진 · T212 도보 시간·경로 A·B·C · T213 프론트 map · T214 프론트 cards+rationale · T215 프론트 chat+timeline+securitylog | **7개 병렬** | 색인에 실록 청크, 행사 JSONL, 판정 결과, 경로 JSON, 프론트 모듈 3묶음 |
| Stage 3 — 조립·연결 | T216 파이프라인(카드·경로·근거 묶음) · T217 MCP 도구 · T218 backend 화면 API·채팅 실행기 · T219 프론트 http.js · T220 자체 평가 세트·실행기 | **5개 병렬**(T218·T219 는 §5.1 엔드포인트 표로 맞춘다) | `kc-bundle/v1` 출력, MCP 도구 3~4종, `/api/*` 전체, http 모드 동작, `eval/run_kcontext.py` |
| Stage 4 — 통합 | **[필수]** T221 끝까지 E2E·데모 스크립트 · *[선택·블로커]* T222 실제 도보 경로 공급자 · *[선택·블로커]* T223 LLM transport·추출 보조 · *[선택]* T224 판단 규칙 스킬 | T221 ∥ T222 ∥ T223 ∥ T224 | 고정 자료로 끝까지 도는 테스트, `scripts/kc_demo.sh` |

- **필수 경로**: Stage 1 전체 → T209~T215 → T216·T218·T219 → T221. 여기까지 끝나면 SCOPE "반드시 만들 것" 1~7 이 고정 자료(fixture) 기준으로 충족된다. 실데이터로 바꾸는 것은 사람 선행(§3) 결과에 따라 같은 명령을 다시 돌리는 일이다.
- **키 없이 끝까지 가는 길**: 모든 태스크에 "fixture 경로"를 적었다. 키·인증·데이터 파일이 없어도 Stage 4 E2E 까지 녹색이 된다. 대신 실데이터 표시는 각 사람 선행이 풀릴 때 붙는다.
- **얇은 수직 경로가 Stage 1 에 없는 이유**: 끝까지 잇는 경로(입력 → 판정 → 카드 → 화면 → 사람 승인)는 모든 단계가 계약(T201)을 import 한다. 계약과 소비자를 같은 스테이지에 두면 같은 타입 파일을 동시에 건드리게 된다. 그래서 Stage 1 에서는 경로의 **양 끝**(계약·색인 / 사람 승인 API)을 먼저 세우고, 화면 쪽 끝은 이미 mock 으로 돌아가는 골격이 맡는다. 경로 전체는 Stage 3 의 T216·T218·T219 에서 이어지고 T221 이 테스트로 고정한다.

---

## 0. 기준선 · 공통 규칙

### 0.1 기준선 (착수 직전 dev 가 실측해 여기에 적는다)
- `uv run python -m pytest -q` 건수: ____ (Sprint 1 마지막 기록은 607. 그 뒤 D6 커밋 `d5c6935` 에서 늘었을 수 있으므로 기록값이 아니라 실측값을 쓴다)
- `uv run ruff check .`: 통과 여부
- `cd frontend/k-context && node --test`: 건수 ____ (골격 완료 시점)
- `python3 -c "import sqlite3; c=sqlite3.connect(':memory:'); c.execute(\"create virtual table t using fts5(x, tokenize='trigram')\"); print('fts5 trigram ok')"` 결과 (T202 분기에 쓴다)

### 0.2 공통 규칙 (모든 태스크)
- 파이썬 3.11+, 줄 길이 100, ruff 통과. 공개 함수에 타입 힌트, 패키지 `__init__.py` 는 `__all__` 을 명시한다.
- **새 런타임 의존성을 추가하지 않는다.** 이미 있는 것만 쓴다: `fastapi`·`httpx`·`mcp`·`uvicorn`(pyproject) + 표준 라이브러리. 프론트는 의존성 없음(네이티브 ES 모듈, `node --test`).
- 테스트 파일 이름은 레포 전체에서 고유하게 짓는다(`tests/**/__init__.py` 가 없어 basename 으로 import 된다). 이번 스프린트 새 테스트는 `test_kc_*` 접두사를 쓴다.
- 기존 `tests/test_layout.py`·`tests/test_smoke.py`·`tests/test_boundaries.py` 는 수정하지 않는다. 경계 검사를 더하려면 자기 태스크의 새 테스트 파일에 넣는다.
- 도메인 코드는 `domains/kcontext/` 에만 둔다. `core/` 에는 도메인 용어를 넣지 않는다(D3, `tests/test_boundaries.py` 금지어 검사). 예외: T208(Sprint 1 이월, 도메인 무관)·T223(D5·D6 의 transport 후속).
- **지역은 코드에 박지 않는다**(AGENT_CONTEXT 3.2). 지역 이름·구·좌표 범위·검색어는 `domains/kcontext/data/regions/*.json` 에서만 읽는다. 코드에 `"종로"`·`"을지로"`·`"신촌"` 리터럴이 있으면 안 된다(테스트 fixture 는 예외).
- **사실을 지어내지 않는다**(AGENT_CONTEXT 11). 테스트·예제 데이터의 연도·인물·좌표·행사는 `○○`·`예시`·`합성` 표시가 붙은 값만 쓴다. 실제 좌표처럼 보이는 숫자를 넣을 때는 필드나 파일 머리에 `"synthetic": true` 를 둔다.
- **공공데이터 호스트명·API 응답 필드 이름은 확인 전에 코드에 쓰지 않는다.** T204·T205·T206 의 확인 문서(`docs/spikes/*.md`)와 필드 매핑 파일에 적힌 값만 쓴다. 확인되지 않은 값은 `[확인 필요]` 로 둔다.
- 키는 env **변수 이름**으로만 다룬다(규칙 1, D1, D5). 키 값은 코드·로그·예외 메시지·fixture·커밋에 남기지 않는다. 오류 메시지에는 변수 이름만 쓴다.
- `deploy/openshell/policy.yaml` 은 이번 스프린트에서 **고치지 않는다**. 수집은 호스트에서 하므로(D7 후보) 샌드박스 허용 목록을 늘릴 일이 없다(규칙 2).
- 프론트 모듈 태스크(T213~T215)는 **자기 `src/components/<모듈>/` 디렉터리와 자기 테스트 파일만** 고친다. `src/state/*`·`src/api/*`·`src/lib/*`·`src/i18n/*`·`src/main.js`·`src/modules.js` 는 고치지 않는다. 새 action·i18n 키가 필요하면 모듈 안의 `strings.js`·`model.js` 로 해결하고, 공용으로 올릴 것은 완료 보고에 적는다(Stage 3 에 pm 이 묶는다).

### 0.3 실행 디렉터리 (T203 이 `.gitignore` 에 추가)
```
var/                        # 실행 산출물 전부 — gitignore
  index/kcontext.db         # T202 색인
  data/events/*.jsonl       # T210 정규화된 행사
  output/<run_id>/          # T216 출력 묶음, output/current.json 이 최신 run 을 가리킨다
  audit/*.jsonl             # core.audit JSONL
  hitl.db                   # core.hitl draft 저장소
domains/kcontext/data/raw/  # 내려받은 원자료(실록 XML·API 원응답) — gitignore
```
경로는 env 로 바꿀 수 있다: `KC_VAR_DIR`(기본 `<레포>/var`), `KC_DATA_DIR`(기본 `domains/kcontext/data`).

---

## 1. 의존성 그래프

```
[사람 선행 H1~H11 — §3]

Stage 1 (병렬)
T201 계약 ──────────────┬──────────────┬───────────────┬──────────────┐
T202 색인 ──────┐        │              │               │              │
T203 지역 ──────┼──┐     │              │               │              │
T204 실록 확인 ─┘  │     │              │               │              │
T205 행사 확인 ────┼─────┤              │               │              │
T206 도보 확인 ────┼─────┼──────────────┼──────┐        │              │
T207 승인 API ─────┼─────┼──────────────┼──────┼────────┼──────┐       │
T208 정책 초안 제출 (이월, 독립 — T207 이 kind 로 읽는다)                │
                   │     │              │      │        │      │       │
Stage 2 (병렬)     ▼     ▼              ▼      ▼        │      │       │
T209 실록 수집 (T202·T203·T204)                         │      │       │
T210 행사 수집 (T201·T202·T203·T205)                    │      │       │
T211 판정 (T201)                                        │      │       │
T212 도보·경로 (T201·T203 · T206 은 표시 규칙만)         │      │       │
T213 map · T214 cards+rationale · T215 chat+timeline+securitylog (골격 전제, T201 예제)
                   │
Stage 3 (병렬)     ▼
T216 파이프라인 (T209·T210·T211·T212, D10)
T217 MCP 도구 (T202·T211·T212, D10)
T218 backend 화면 API (T207, §5 묶음 형식, D10)
T219 프론트 http.js (§5.1 엔드포인트 표, T207 응답 형식)
T220 평가 세트 (T211·T212)
                   │
Stage 4            ▼
T221 E2E·데모 스크립트 (전부)      [필수]
T222 실제 도보 공급자 (T212, H5, D9) [선택·블로커]
T223 LLM transport·추출 (H10)      [선택·블로커]
T224 판단 규칙 스킬 (T211)          [선택]
```

---

## 2. 결정이 필요한 것 (먼저 결정을 추가해야 함)

pm·dev 는 `docs/DECISIONS.md` 를 고치지 않는다. 아래 문안을 사람이 승인하면 DECISIONS.md 에 추가한다. "막는 것" 열의 태스크는 해당 결정이 들어간 뒤 착수한다.

| 후보 | 요지 | 막는 것 | 승인 전 진행 |
|---|---|---|---|
| D7 | 외부 자료 수집은 **호스트 오프라인 수집기**가 한다. 키는 호스트 env 이름으로만. 에이전트 쪽은 로컬 색인·JSONL 만 읽는다. Sprint 2 에서 `policy.yaml` 은 그대로 | T210 의 실호출(`fetch.py`) | T205 문서 조사·T210 정규화(fixture)는 진행 |
| D8 | 로컬 색인은 **SQLite FTS5(trigram)** + 구조화 JSONL. 임베딩·리랭커(Nemotron)는 `Retriever` 인터페이스 뒤에 나중에 붙인다 | T202 | Stage 1 시작 시 승인 권장. 늦으면 T202 는 문안대로 진행하고 Stage 1 게이트에서 확인 |
| D9 | 도보 시간 공급자 우선순위: 카카오맵 MCP → OSM 엔진 → **직선거리 추정**. 추정값은 `estimated: true` 이고 화면에 "예상"으로 표시한다 | T212 의 표시 규칙, T222 | T212 는 추정 공급자만 만든다(어느 결론이든 필요) |
| D10 | **화면용 API 는 backend 에 둔다.** backend 는 `domains` 를 import 하지 않고, 파이프라인은 별도 프로세스(`python -m domains.kcontext.pipeline.run`, `APP_PROCESS_ROLE=agent`)로 돌려 출력 묶음(JSON 파일)을 읽는다. 에이전트 쪽 산출물(출력 묶음·audit)은 "제안" 지위이고 상태 전이를 담지 않는다(D2 해석) | T216·T217·T218 | Stage 3 전에 필요. Stage 1·2 는 무관 |
| D11 | 지도 렌더러 기본값은 **SVG 투영(타일 없음, 외부 요청 없음)**. 타일·SDK(카카오맵 JS·OSM 타일)는 키·이용약관 확인 뒤에 선택 사항으로 붙인다 | T213 | Stage 2 전에 필요 |
| 계약 보충 | AGENT_CONTEXT 3.3 을 **먼저** 고친다(3.3: "필드를 추가·변경하려면 두 사람이 합의하고 이 문서를 먼저 고친다"). 항목은 아래 | T216·T219(최종 형식). T201 은 선택 필드로 받아 두고 진행 | Stage 3 전에 필요 |

**계약 보충 항목** (프론트 골격 `src/data/*.js` 주석에 이미 "정식 채택은 3.3 수정 후"로 적힌 확장과, 이번 계획이 새로 요구하는 것)
1. `geometry.coords` 의 좌표 순서는 **`[lat, lng]`**. 3.3 은 순서를 정하지 않았다.
2. `geometry.space`: `"geo"`(기본, `[lat,lng]`) | `"schematic"`(목업 좌표계 `[x,y]`).
3. 카드 확장: `era`, `facts[{text, ref}]`(사실 층 문장과 출처 번호, ref 는 1부터), `alternatives[{label, text}]`(이설 병기), `checks[{level: ok|warn|bad, text}]`, `poster`, `only`, `warning`, `kind_label`, `sources[].bib`.
4. 경로 확장: `segments[].coords`(카드 없는 연결 구간도 그리기 위해), `segments[].label_xy`(schematic 전용), **`route.estimated: bool`**(D9, 새 항목).
5. 카드 `narration` 은 **`null` 허용**(몰입 층이 없으면 화면이 층을 숨긴다). 지금 `src/api/schema.js` 는 story 카드에 narration 을 필수로 요구한다. LLM 내레이션(T223)이 없으면 옛날 카드를 하나도 낼 수 없게 되므로 필요하다.
6. 입력 확장(선택): `walk_request: {from: {name, lat, lng}, to: {name, lat, lng}, budget_min}`. 없으면 첫 빈 시간의 `near` → 숙소로 경로를 만든다.

### D7~D11 문안 (승인용)

```markdown
## D7 — 외부 자료는 호스트 수집기가 모으고, 에이전트는 로컬 색인만 읽는다 (2026-10-07)
- **결정**: 실록 XML·TourAPI·서울 열린데이터광장 수집은 호스트에서 실행하는 오프라인 수집기(`domains/kcontext/ingest/`)가 한다. 공공데이터 키는 호스트 셸 env 의 **변수 이름**(`DATA_GO_KR_SERVICE_KEY`, `SEOUL_OPENAPI_KEY` — 이름은 제안)으로만 참조한다. 결과는 `var/` 아래 로컬 색인·JSONL 로 저장하고, 에이전트 쪽(파이프라인·MCP 도구)은 이것만 읽는다. Sprint 2 에서는 `deploy/openshell/policy.yaml` 의 `network_policies` 를 늘리지 않는다.
- **계기**: ① 샌드박스 이미지는 Sprint 2 의 "지금 안 만들 것"이다. ② 외부 API 가 느리거나 한도에 걸릴 때를 대비해 핵심 자료를 로컬 색인으로 준비한다(AGENT_CONTEXT 7·8). ③ 키가 에이전트 프로세스에 들어가지 않는다(D1 과 같은 취지).
- **대안**: 에이전트가 실행 중에 API 를 직접 호출 — 샌드박스 허용 목록·provider 주입이 문서로 확인되지 않았고 이번 범위 밖이라 기각(다음 스프린트에 provider 경유로 다시 검토). 키를 설정 파일에 기록 — 규칙 1 위반이라 기각.

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
- **대안**: 세 번째 프로세스(화면용 앱 서버) — 프로세스·포트가 늘어 하루 일정에 맞지 않아 기각. backend 가 `domains` 를 직접 import — 사람 전용 프로세스에 에이전트 코드가 들어와 D2·D3 경계가 흐려져 기각. 파이프라인을 MCP 서버 안에서만 실행 — 에이전트 런타임(NemoClaw) 연결이 이번 범위 밖이라 기각.

## D11 — 지도는 SVG 투영으로 먼저 그리고 타일·SDK 는 선택으로 붙인다 (2026-10-07)
- **결정**: 프론트 map 모듈은 위경도를 화면 좌표로 투영해 SVG 로 그린다(배경 타일 없음, 외부 요청 없음). 카카오맵 JS SDK 나 OSM 타일은 키·도메인 등록·이용약관이 확인되면 같은 모듈의 렌더러로 추가한다.
- **계기**: 프론트는 번들러·외부 CDN 없이 돈다. 지도 SDK 는 키 발급·도메인 등록(사람 선행)이 필요하다. 목업이 이미 SVG 좌표계로 그려져 있다.
- **대안**: 처음부터 카카오맵 JS SDK — 키·도메인 등록 블로커로 기각. OSM 공개 타일 서버 직접 사용 — 이용 정책 미확인으로 기각.
```

---

## 3. 사람 선행 · 블로커

### 3.1 사람 선행 작업 (먼저 시작할수록 좋다 — H1 이 가장 급하다)

| ID | 할 일 | 막는 태스크(스테이지) | 막혀 있을 때의 fixture 경로 |
|---|---|---|---|
| H1 | 공공데이터포털에서 조선왕조실록 원문·국역 XML(과 인물 CSV)을 내려받아 `domains/kcontext/data/raw/sillok/` 에 둔다. **내려받은 날짜**와 내려받은 페이지 URL·이용허락 문구를 `docs/spikes/sillok.md` 첫 줄에 적는다 | T204 확정(S1) → **T209 착수(S2)** | 없음. XML 구조를 모르면 파서를 쓰지 않는다(추측 금지). T209 만 대기하고 나머지는 진행한다. 옛날 카드는 합성 이야기 레코드로 끝까지 돈다 |
| H2 | 실록 범위 결정: **전체** 색인 vs **데모 지역 관련 구절만**(`sillok_keywords` 일치). 데모 지역 옛 지명 검색어 목록(`regions/*.json` 의 `sillok_keywords`)을 채운다 | T209 기본 모드(S2) | 결정 전 기본값은 `--mode regions`. 검색어가 비어 있으면 지역 이름만 쓴다 |
| H3 | 공공데이터포털에서 한국관광공사 TourAPI 활용신청 → 서비스키를 셸 env `DATA_GO_KR_SERVICE_KEY` 로 export(.env 에도 가능, 커밋 금지) | T205 실호출 확인(S1), T210 실수집(S2) | T205 가 공식 활용 문서로 필드를 확인하고 **합성 fixture**(실제 필드 이름 + `○○` 값)를 만든다. T210 은 그것으로 정규화를 완성한다 |
| H4 | 서울 열린데이터광장 인증키 발급 → `SEOUL_OPENAPI_KEY` | 동일 | 동일 |
| H5 | PlayMCP 카카오맵 확인: 카카오 로그인·본인인증을 하고, **우리 서버 프로세스에서** MCP 엔드포인트를 부를 수 있는지(인증 방식·토큰 수명·이용약관) 확인한다. 결과를 `docs/spikes/walk_route.md` 에 붙인다 | T206 결론(S1), **T222(S4)** | `EstimateRouter`(직선거리 추정, "예상" 표시)로 끝까지 간다 |
| H6 | 이야기 레코드 6~8개 큐레이션: 실록 구절 등 근거(출처·위치·원문 구절·수집일), 좌표와 좌표 근거(발굴·고지도 비정·표석 위치), 주제. `domains/kcontext/data/stories/<지역>/*.json`(형식은 T201 의 `data/stories/README.md`) | 실제 옛날 카드(S3 T216 결과물의 내용) | `tests/fixtures/kcontext/stories/` 의 합성 레코드(`○○`)로 돈다 |
| H7 | 데모 앵커 좌표(숙소·창덕궁·익선동 등)와 지역 `bbox`·`center` 를 지도 검색 결과로 채운다(`data/situations/demo_day1.json`, `data/regions/*.json`) | 실제 거리·시간, 지역 필터(S3) | 합성 좌표 fixture(`"synthetic": true`) |
| H8 | §2 결정 후보 승인 → DECISIONS.md·AGENT_CONTEXT 3.3 반영 | D8: T202(S1) · D11: T213(S2) · D7: T210 실호출(S2) · D9: T212 표시 규칙(S2) · D10·계약 보충: T216~T219(S3) | 표 §2 의 "승인 전 진행" 열 |
| H9 | 평가 세트 기대 정답 검수 → `eval/testset.draft.json` 을 검토해 `eval/testset.json` 으로 옮긴다(훅이 dev 의 `eval/testset.json` 쓰기를 막는다) | T220 기준선 기록(S3) | 실행기가 draft 를 읽고 결과에 "검수 전"을 표시한다 |
| H10 | (선택) NVIDIA API 키를 셸에 export(`NVIDIA_API_KEY_A` 등, D5) | T223(S4) | 규칙 기반 판정만 쓴다 |
| H11 | CLAUDE.md "회귀 테스트" 절에 `cd frontend/k-context && node --test` 와 `uv run python eval/run_kcontext.py` 를 추가한다(에이전트는 CLAUDE.md 를 고치지 않는다) | 공식 회귀 범위 | 이 문서 §6 게이트 표에 명령을 적어 대신한다 |

### 3.2 블로커 요약

| 블로커 | 막히는 것 | 대응 |
|---|---|---|
| 사람 승인(D7~D11, 계약 보충) | §2 표 | 승인 전 진행 범위를 태스크마다 적었다 |
| API 키·인증(H3·H4·H5·H10) | 실수집·실경로·LLM 보조 | fixture·추정 공급자·규칙 기반으로 우회. 블로커가 있는 태스크(T222·T223)는 Stage 4 로 뺐다 |
| 외부 데이터 규모·라이선스(H1·H2, TourAPI·서울 재배포 조건) | T209 실데이터, 테스트 fixture 커밋 | 실록은 이용허락 제한 없음(사용자 확인) → 짧은 발췌를 fixture 로 커밋. TourAPI·서울 원응답은 재배포 조건 `[확인 필요]` → **커밋하지 않는다**(`raw/` gitignore), 테스트는 합성 fixture |
| 게이트웨이·샌드박스 | 없음 | 이번 스프린트는 샌드박스 안에서 돌지 않는다(SCOPE "지금 안 만들 것"). MCP 서버도 호스트에서 돈다 |
| 문서 확인(규칙 4) | T217(`mcp` SDK API), T222 | 설치된 패키지 소스·공식 문서로 확인한다. 기억으로 쓰지 않는다 |

---

## 4. 스테이지 상세

### Stage 1
| TASK | 제목 | 범위(소유 경로) | 선행 | 구분 |
|------|------|------|------|------|
| T201 | 공통 계약: 카드·경로·출처·판정·입력 검증기 + 내부 레코드 타입 | `domains/kcontext/contract/`, `domains/kcontext/data/stories/README.md`, `tests/domains/kcontext/contract/`, `frontend/k-context/tests/contract.examples.test.js` | — | 필수 |
| T202 | 로컬 색인 저장소(청크 + 출처 메타 + FTS5) | `domains/kcontext/index/`, `tests/domains/kcontext/index/` | D8(권장) | 필수 |
| T203 | 지역 설정·데이터 폴더 배치·실행 디렉터리 | `domains/__init__.py`, `domains/kcontext/__init__.py`, `domains/kcontext/paths.py`, `domains/kcontext/regions.py`, `domains/kcontext/data/regions/`, `domains/kcontext/data/situations/`, `.gitignore`, `tests/domains/kcontext/test_kc_regions.py` | — | 필수 |
| T204 | [확인] 실록 XML 구조·이용허락·발췌 fixture | `docs/spikes/sillok.md`, `tests/fixtures/kcontext/sillok/` | **H1** | 필수(H1 대기 가능) |
| T205 | [확인] TourAPI·서울 문화행사 API 호스트·필드·이용조건 | `docs/spikes/events_api.md`, `tests/fixtures/kcontext/events/`, `domains/kcontext/ingest/events/field_maps/`, `.env.example` | (H3·H4 는 실호출만) | 필수 |
| T206 | [확인] 도보 경로: PlayMCP 카카오맵 서버 호출 가능성 + OSM 대안 | `docs/spikes/walk_route.md` | (H5) | 필수(결론 "대기" 허용) |
| T207 | backend: 사람 승인 API + 보안 로그 조회 | `backend/app.py`, `backend/settings.py`, `backend/security_log.py`, `backend/routers/review.py`, `tests/backend/` | — | 필수 |
| T208 | (이월 S1-T301 + W-D) 정책 초안 → hitl draft 제출, 쓰기 루트 보정 | `core/policy_proposer/submit.py`, `core/policy_proposer/baseline.py`, `tests/core/policy_proposer/test_proposer_submit.py`, 기존 proposer 테스트 중 `/workspace` 단언 | — | 필수(이월 최우선) |

### Stage 2
| TASK | 제목 | 범위 | 선행 | 구분 |
|------|------|------|------|------|
| T209 | 실록 수집기: XML → 기사 → 청크 → 색인 | `domains/kcontext/ingest/__init__.py`, `domains/kcontext/ingest/sillok.py`, `tests/domains/kcontext/ingest/test_kc_ingest_sillok.py` | T202, T203, T204, H2(기본값 있음) | 필수(H1 대기 가능) |
| T210 | 행사 수집·정규화(TourAPI·서울·수기 JSON) | `domains/kcontext/ingest/events/`(field_maps 제외 — T205 소유), `tests/domains/kcontext/ingest/test_kc_ingest_events_*.py` | T201, T202, T203, T205, D7(실호출만) | 필수 |
| T211 | 판정 엔진(등급·충돌·무관 걸러내기·주입 차단 → 6장 형식) | `domains/kcontext/judge/`, `domains/kcontext/data/normalize/terms.json`, `tests/domains/kcontext/judge/` | T201 | 필수 |
| T212 | 도보 시간(추정 공급자) + 경로 A·B·C 조립 | `domains/kcontext/geo/`, `tests/domains/kcontext/geo/` | T201, T203, D9(표시 규칙) | 필수 |
| T213 | 프론트 map 모듈 | `frontend/k-context/src/components/map/`, `frontend/k-context/tests/map.model.test.js` | 골격, T201 예제, D11 | 필수 |
| T214 | 프론트 cards + rationale 모듈 | `src/components/cards/`, `src/components/rationale/`, `tests/cards.model.test.js`, `tests/rationale.model.test.js` | 골격, T201 예제 | 필수 |
| T215 | 프론트 chat + timeline + securitylog 모듈 | `src/components/chat/`, `src/components/timeline/`, `src/components/securitylog/`, `tests/{chat,timeline,securitylog}.model.test.js` | 골격, T207 응답 형식 | 필수 |

### Stage 3
| TASK | 제목 | 범위 | 선행 | 구분 |
|------|------|------|------|------|
| T216 | 파이프라인: 후보 수집 → 판정 → 일정 맞추기 → 카드·경로·근거 → 출력 묶음 | `domains/kcontext/pipeline/`, `tests/domains/kcontext/pipeline/`, `tests/fixtures/kcontext/stories/`, `tests/fixtures/kcontext/situations/` | T209~T212, D10, 계약 보충 | 필수 |
| T217 | MCP 도구(검색·도보·출처 요청) + 서버 엔트리 | `mcp_server/server.py`, `mcp_server/tools/kc_*.py`, `domains/kcontext/tools/`, `tests/mcp_server/` | T202, T211, T212, D10 | 필수 |
| T218 | backend 화면 API + 채팅 실행기 | `backend/routers/view.py`, `backend/runner.py`, `backend/chat.py`, `backend/app.py`(라우터 등록만), `tests/backend/test_kc_backend_view.py`, `tests/backend/test_kc_backend_chat.py`, `tests/fixtures/kcontext/bundle/` | T207, §5 묶음 형식, D10 | 필수 |
| T219 | 프론트 http.js 를 backend 에 연결 | `frontend/k-context/src/api/http.js`, `frontend/k-context/src/api/schema.js`(계약 보충 5번만), `frontend/k-context/tests/api.http.test.js` | §5.1 표, T207, 계약 보충 | 필수 |
| T220 | 자체 평가 세트(함정 유형) + 실행기 | `eval/testset.draft.json`, `eval/run_kcontext.py`, `eval/results/.gitkeep`, `tests/eval/test_kc_eval_runner.py` | T211, T212 | 필수(기준선은 H9 뒤) |

### Stage 4
| TASK | 제목 | 범위 | 선행 | 구분 |
|------|------|------|------|------|
| T221 | 끝까지 E2E 테스트 + 데모 실행 스크립트 | `tests/test_kc_e2e.py`, `scripts/kc_demo.sh` | 전부 | **필수** |
| T222 | 실제 도보 공급자(카카오 MCP 또는 OSM) | `domains/kcontext/geo/providers/`, `tests/domains/kcontext/geo/test_kc_geo_provider_*.py` | T212, T206 결론, H5, D9 | 선택·블로커 |
| T223 | `core/llm` HTTP transport + 판정용 주장 추출 보조 | `core/llm/transport.py`, `deploy/llm.example.yaml`, `domains/kcontext/judge/llm_extract.py`, `tests/core/llm/test_llm_transport.py`, `tests/domains/kcontext/judge/test_kc_judge_llm_extract.py` | H10 | 선택·블로커 |
| T224 | 제품 스킬: 판단 규칙 SKILL.md + 스킬 카드 | `skills/kcontext-judge/` | T211 | 선택 |

### 4.1 스테이지 구성 근거
- **Stage 1**: 여덟 태스크가 모두 서로 다른 경로를 소유하고 서로 import 하지 않는다. 계약(T201)·색인(T202)·지역(T203)은 Stage 2 의 모든 도메인 태스크가 쓰는 바닥이라 먼저 둔다. T202 는 T201 을 import 하지 않도록 출처 메타를 자기 컬럼으로 검증한다(Stage 2 에서 변환). 스파이크 3개(T204~T206)는 코드가 아니라 확인 문서·fixture 를 만들고, 사람 선행(H1·H3~H5)이 늦어도 **다른 태스크를 막지 않는 위치**에 있다. 사용자 우선순위(데이터 수집 먼저)에 따라 실록·행사 확인을 첫 스테이지에 넣었다. T207 은 이미 있는 `core.hitl`·`core.audit` 만 쓰므로 바로 만들 수 있고, 사람 승인이라는 경로의 끝을 먼저 세운다. T208 은 Sprint 1 이월이라 원칙 4 에 따라 여기에 두고, `core/policy_proposer/` 만 만진다(`__init__.py` 는 고치지 않는다 — S1 규칙 유지). 패키지 `__init__.py`(`domains/`, `domains/kcontext/`)는 T203 만 만든다. T201·T202 는 그동안 namespace 패키지로 import 된다.
- **Stage 2**: 수집 2개(T209·T210)는 색인·지역·확인 결과가 있어야 하고, 판정(T211)·경로(T212)는 계약이 있어야 한다. 네 개 모두 `domains/kcontext/` 아래 서로 다른 하위 폴더를 소유한다. `ingest/__init__.py` 는 T209 만 만들고 T210 은 `ingest/events/` 만 만든다. 프론트 3개는 골격의 모듈 슬롯 경계(`mount(root, ctx)`, 서로 import 금지)를 따라 나눴다. 공용 파일(`state`·`api`·`lib`·`i18n`)을 고치지 않는다는 규칙으로 병렬 충돌을 막는다. 프론트 모듈은 mock API 로 각자 검증할 수 있다.
- **Stage 3**: 조립(T216)은 수집·판정·경로가 모두 있어야 한다. backend(T218)와 http.js(T219)는 이 문서 §5 의 엔드포인트·묶음 형식을 계약으로 삼아 병렬로 만들고, 실제로 맞는지는 T221 이 확인한다. T218 은 자기 fixture 묶음(`tests/fixtures/kcontext/bundle/`)으로 검증하므로 T216 을 기다리지 않는다. T217 은 `mcp_server/` 와 `domains/kcontext/tools/` 만, T220 은 `eval/` 과 자기 테스트만 만진다. `backend/app.py` 는 Stage 1 에 T207 이 만들고 Stage 3 에서는 T218 만 고친다.
- **Stage 4**: T221 이 고정 자료로 끝까지 도는 경로를 테스트로 고정한다. 키·인증이 필요한 T222·T223 은 원칙 5 에 따라 맨 뒤에 두었다. 둘 다 이월해도 SCOPE 필수 항목은 충족된다(추정 공급자·규칙 기반 판정).

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
- `AuditEntry`: `{id: str, time: "HH:MM:SS"(Asia/Seoul), at: ISO8601, kind: "ok"|"deny"|"pend"|"approved"|"rejected", text: {ko, en}, decided_by: str|null, decided_at: str|null, origin: "hitl"|"audit"}` — 프론트 mock(`src/data/auditlog.js`)의 형식에 `at`·`origin`·`decided_at` 을 더한 것이다.
- id 형식: hitl draft 는 `draft:<draft.id>`, audit 이벤트는 `audit:<run_id>:<seq>`. 결정은 `draft:` 항목만 할 수 있다.

### 5.2 출력 묶음 `kc-bundle/v1` (T216 작성, T218 읽기)
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
var/output/<run_id>/verdicts.json  [6장 판정 객체...] (디버그·평가용)
```
- run 디렉터리는 임시 이름으로 다 쓴 뒤 rename 하고, 마지막에 `current.json` 을 원자적으로 교체한다(`os.replace`). 읽는 쪽은 `current.json` 만 따라간다.
- 모든 JSON 은 `ensure_ascii=False, indent=2`, UTF-8.

---

## 6. 스테이지 게이트

명령은 레포 루트 기준이다. H11 이 반영되기 전까지는 이 표가 회귀 범위의 기준이다.
```
uv run python -m pytest -q
uv run ruff check .
(cd frontend/k-context && node --test)          # Stage 2 부터
uv run python eval/run_kcontext.py --check      # Stage 3 부터 (T220)
```
| 게이트 | 판정 시점 | 통과 조건 |
|---|---|---|
| Stage 1 | T201~T208 이 모두 끝난 뒤 한 번 | pytest 전부 통과, 건수가 §0.1 기준선보다 많다 · ruff 통과 · `node --test` 통과(T201 의 공통 예제 테스트 포함) · `docs/spikes/{sillok,events_api,walk_route}.md` 가 있다(대기 상태라면 "대기 — H번호" 가 적혀 있다) · **reviewer**: T207 의 신원 주입(요청 본문에 신원 없음, 설정의 `reviewer_id` 가 `agent:` 로 시작하면 시작 거부), T208 의 D2(제출은 draft 만), `.gitignore` 에 `var/`·`raw/` |
| Stage 2 | T209~T215 종료(T209 가 H1 대기면 그것만 빼고) | pytest 건수 증가 · ruff · `node --test` 건수 증가 · 코드에 지역 이름 리터럴이 없다(`rg -n "종로|을지로|신촌" domains/kcontext --glob '*.py'` 결과가 0줄. fixture·data 폴더 제외) · 브라우저 수동 확인: `cd frontend/k-context && npm run serve` → `http://localhost:8766/?api=mock` 에서 세 모듈 묶음이 자리표시 없이 그려진다 |
| Stage 3 | T216~T220 종료 | 위 명령 전부 통과, 건수 증가 · `uv run python -m domains.kcontext.pipeline.run --situation tests/fixtures/kcontext/situations/synthetic_day1.json --out-root /tmp/kc-out ...`(T216 DoD 명령)가 0 으로 끝나고 묶음이 계약 검증을 통과한다 · **reviewer**: D2(MCP 도구의 쓰기는 draft 와 산출물뿐, 전이 없음)·D3(backend 가 `domains`·`mcp_server` 를 import 하지 않음, `mcp_server` 가 `backend` 를 import 하지 않음)·규칙 1(fetch 오류에 키 값 없음) |
| Stage 4 | T221 종료(선택 태스크는 착수했을 때만) | T221 E2E 통과 · 전체 회귀 통과 · `scripts/kc_demo.sh --fixture` 가 backend 를 띄우고 `curl -s localhost:8000/api/cards` 가 카드를 돌려준다 |

- 건수가 직전보다 줄면 테스트가 사라진 것이므로 게이트 실패다. 게이트 실패 시 다음 스테이지에 착수하지 않는다.

---

## 7. 이월 규칙

| 대상 | 규칙 |
|---|---|
| 필수 T201~T221 | 이월하지 않는다. 밀리면 선택 태스크(T222~T224)를 포기한다 |
| T209 | **H1 이 풀리지 않으면 "S3 이월 — 사유: 실록 XML 미확보"**. 이월해도 나머지 경로는 합성 이야기 레코드로 돈다 |
| T222 | T206 결론이 "서버 호출 가능" 이거나 OSM 엔진 구성이 확인됐을 때만 착수. 아니면 "S3 이월 — 사유: 지도 인증 미확인" |
| T223 | H10 이 없으면 착수하지 않는다. "S3 이월 — 사유: 키 없음" |
| T224 | 시간이 남을 때만 |
| S1 이월 중 이번에 다루지 않는 것 | **S1-T202-opt**(정보성 항목) — 이번 경로에 필요 없음, 계속 이월. **S1-T302**(OpenShell 로그 어댑터) — OCSF 내보내기는 문서로 확인됐지만 실측 캡처에 샌드박스가 필요하고 샌드박스는 "지금 안 만들 것"이라 계속 이월. **S1 hitl W1·W2**(raw 연결 우회) — 근본 해결은 DB 파일 권한 분리. T217·T218 로 프로세스는 분리되지만 파일 권한 분리는 배포(샌드박스) 때 다룬다. **S1 T303 W1~W9** — transport 를 만드는 T223 에서 W6·W9 를 함께 처리하고, 나머지는 계속 이월 |

이월 항목은 `/done` 이 이 문서 끝 "이월" 절에 사유와 함께 적는다.

---

## 8. 태스크별 상세 구현 명세

---

#### T201 — 공통 계약: 카드·경로·출처·판정·입력 검증기 + 내부 레코드 타입 [필수 · Stage 1 · 병렬]
- **변경 파일** (모두 신규)
  - `domains/kcontext/contract/__init__.py`, `text.py`, `source.py`, `card.py`, `route.py`, `verdict.py`, `situation.py`, `records.py`, `errors.py`
  - `domains/kcontext/contract/examples/{card_story.json, card_now.json, route.json, verdict.json, situation.json, source.json}`
  - `domains/kcontext/contract/examples/bad/*.json` (각 파일에 `{"kind": "card"|..., "obj": {...}, "expect": ["문제 문자열 일부", ...]}`)
  - `domains/kcontext/data/stories/README.md` (이야기 레코드 작성법 — H6 용)
  - `tests/domains/kcontext/contract/test_kc_contract_validate.py`, `test_kc_contract_records.py`, `test_kc_contract_examples.py`
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

  # records.py — 파이프라인 내부 입력(3.3 밖). frozen dataclass + from_dict/to_dict
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
                     fetched_from: Literal["tourapi", "seoul", "manual", "fixture"]; synthetic: bool = False
  def story_from_dict(d) -> StoryRecord; def event_from_dict(d) -> EventRecord  # 실패 시 ContractError
  ```
- **핵심 로직**
  1. 검증기는 **던지지 않고 문제 목록(list[str])을 돌려준다**. 문구 형식은 프론트 `src/api/schema.js` 와 같게(`"card[<id>].<필드>: <이유>"`) 맞춘다. `ensure_valid` 만 던진다.
  2. `validate_source`: `id`·`name`·`locator`·`collected_at`·`quote` 는 비어 있지 않은 str. `tier ∈ TIERS`. `collected_at` 은 `YYYY-MM-DD`. `url` 은 str(빈 문자열 허용). `published` 는 str 또는 None.
  3. `validate_card`: `schema.js` 의 `validateCard` 규칙을 모두 옮긴다(id, kind, title·body Text, geometry.type, coords 가 비어 있지 않은 `[[a,b],...]`, segment 는 2점 이상, basis Text, badge 가 kind 에 맞는 딱지, sources 비어 있지 않고 각각 유효, user_state, why_fits·caveats·rejected 배열, now 카드는 `slot.day` 숫자·`time_cost_min` 숫자·`valid.as_of`). 추가 규칙: `geometry.space` 가 없거나 `"geo"` 이면 좌표는 `[lat, lng]` 로 보고 범위(-90..90, -180..180)를 검사한다. `approx` 는 `radius_m` 양수. `rejected[]` 원소는 `{claim, reason}` 이고 reason 은 `REJECT_REASONS` 중 하나.
  4. **narration**: story 카드에서 `narration` 은 Text **또는 None** 을 허용한다(계약 보충 5번). 이 한 가지만 현재 `schema.js` 와 다르다. 공통 예제(`examples/*.json`)는 narration 이 있는 것만 넣어 양쪽이 같은 결과를 내게 하고, 차이는 테스트 이름 `test_narration_null_allowed_python_only` 로 고정한다(T219 가 schema.js 를 맞추면 node 쪽에도 같은 케이스를 추가한다).
  5. 확장 필드(계약 보충 3·4번: `era`, `facts`, `alternatives`, `checks`, `poster`, `only`, `warning`, `kind_label`, `bib`, `segments[].coords`, `label_xy`, `estimated`)는 **있으면 형식만 검사하고 없어도 통과**한다. `facts[].ref` 는 1..len(sources) 정수.
  6. `validate_route`: `schema.js` 의 `validateRoute` 규칙 + `badges` 원소가 `ROUTE_BADGES` 중 하나, `delta_min ≥ 0`, `estimated` 가 있으면 bool.
  7. `validate_verdict`: `claim` 비어 있지 않은 str, `sources[]` 각 원소 `{id, tier, date(str|None), stance, says?}`, `verdict ∈ VERDICTS`, `reason` 비어 있지 않은 str, `confidence ∈ CONFIDENCE`.
  8. `validate_situation`: `trip.from ≤ trip.to`(날짜), anchors 의 type, `lat/lng` 은 숫자 또는 None, `free_slots[].from < to`, `language ∈ {"ko","en"}`. 선택 키 `walk_request` 는 있으면 형식 검사.
  9. 공통 예제: `examples/*.json` 은 Python 검증기와 node 의 `schema.js` 검증기에서 **모두 문제 0건**이어야 한다. `examples/bad/*.json` 은 양쪽 모두 문제가 1건 이상이고, Python 은 `expect` 의 문자열을 모두 포함해야 한다. 예제 값은 `○○`·`예시` 와 `"synthetic": true` 를 쓴다.
  10. `data/stories/README.md`: `StoryRecord` JSON 의 필드표, "출처마다 locator·collected_at·quote 가 없으면 넣지 않는다", "좌표 근거(basis)를 반드시 적는다", "기억으로 쓰지 않는다(CONTEXT_STORY_ROUTE 5장 씨앗은 검증 전)" 세 줄 규칙, 예시 1건(`○○`).
- **엣지 케이스**: Text dict 에 `ko` 만 있음 → 문제. coords 원소에 bool(`True` 는 int) → 문제(`isinstance(x, bool)` 먼저 거른다). NaN·inf 좌표 → 문제. `card_ids` 가 주어졌는데 없는 카드 → 문제. `from_dict` 에 모르는 키 → `ContractError`(오타 방지).
- **fixture 경로**: 외부 의존 없음.
- **지켜야 할 규칙**: AGENT_CONTEXT 3.3·6장이 원본이다. 계약 보충(§2)이 승인되기 전에는 확장 필드를 "선택"으로만 받는다. 사실을 지어내지 않는다(예제는 `○○`).
- **DoD**: `uv run python -m pytest -q tests/domains/kcontext/contract` 통과 · `(cd frontend/k-context && node --test tests/contract.examples.test.js)` 통과 · `uv run ruff check domains/kcontext/contract tests/domains/kcontext/contract`.

---

#### T202 — 로컬 색인 저장소(청크 + 출처 메타 + FTS5) [필수 · Stage 1 · 병렬]
- **변경 파일** (신규): `domains/kcontext/index/__init__.py`, `store.py`, `chunk.py`, `__main__.py`; `tests/domains/kcontext/index/test_kc_index_store.py`, `test_kc_index_chunk.py`
- **인터페이스**
  ```python
  # chunk.py
  def chunk_text(text: str, *, max_chars: int = 800) -> list[str]
  def make_chunk_id(source_id: str, locator: str, text: str) -> str   # sha1(...)[:16]

  # store.py
  TIERS = ("S", "A", "B", "C", "D")      # T201 을 import 하지 않는다(병렬). 값은 같아야 한다 — 테스트로 고정
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
      def __init__(self, path: str | Path)  # ":memory:" 허용. 파일이 없으면 만든다(부모 디렉터리는 만들지 않음)
      fts_enabled: bool                     # 읽기 전용 속성
      def add(self, chunks: Iterable[Chunk]) -> int          # chunk_id 기준 upsert, 반영 건수
      def search(self, query: str, *, regions: Collection[str] | None = None,
                 tiers: Collection[str] | None = None, limit: int = 20) -> list[Hit]
      def get(self, chunk_id: str) -> Chunk
      def count(self) -> int
      def close(self) -> None               # 컨텍스트 매니저 지원
  ```
  `__main__.py`: `python -m domains.kcontext.index stats --db PATH` (총 건수·등급별·지역별), `search --db PATH --q TEXT [--region R] [--limit N]` (사람이 색인을 확인하는 용도. 출력에 원문 구절 앞 80자).
- **핵심 로직**
  1. 스키마: `chunks(chunk_id TEXT PRIMARY KEY, source_id, tier, name, locator, url, published, collected_at, text, quote, regions_json, meta_json)`, `chunk_regions(chunk_id, region)`(지역 필터용 인덱스).
  2. FTS: `CREATE VIRTUAL TABLE chunks_fts USING fts5(text, name, content='chunks', content_rowid=...)` 대신 단순하게 `fts5(chunk_id UNINDEXED, text, tokenize='trigram')` 를 두고 add 시 같이 갱신한다. 생성이 `sqlite3.OperationalError` 로 실패하면 `fts_enabled=False` 로 두고 LIKE 검색을 쓴다(§0.1 실측 결과를 테스트 skip 조건에 쓰지 말고 두 경로를 모두 테스트한다 — LIKE 경로는 `LocalIndex(path, _force_like=True)` 같은 비공개 인자로 강제한다).
  3. 검색: 검색어를 NFKC 정규화·앞뒤 공백 제거. 3자 미만이거나 FTS 가 없으면 `text LIKE ? ESCAPE '\'`(%·_ 이스케이프). FTS 질의는 **사용자 문자열을 그대로 FTS 문법에 넣지 않는다** — 큰따옴표를 두 개로 바꾸고 전체를 `"..."` 로 감싼 구(phrase) 질의로만 쓴다. 점수: FTS 는 `bm25` 의 음수를 score 로, LIKE 는 등장 횟수. 정렬은 score 내림차순 → tier(S 먼저) → chunk_id.
  4. 검증(`add`): `tier ∈ TIERS`; `name`·`locator`·`collected_at`·`text`·`source_id` 비어 있지 않음; `collected_at` 은 `YYYY-MM-DD`; `text` ≤ 20,000자; `quote` 가 비면 `text[:300]` 으로 채운다; `quote` ≤ 500자. 하나라도 틀리면 **그 배치 전체를** 거부(`ChunkValidationError`, 메시지에 chunk_id 와 첫 위반). 트랜잭션으로 묶는다.
  5. `chunk_text`: 빈 줄로 문단 분리 → 문단이 `max_chars` 를 넘으면 문장 경계(`다.`·`.`·`?`·`!`·`。` 뒤 공백)로 나눔 → 그래도 넘으면 `max_chars` 에서 자른다. 빈 청크는 버린다. 순서 보존.
  6. 색인은 원문을 **그대로** 저장한다(신뢰할 수 없는 입력). 주입 판정은 소비자(T211)가 `core.guard` 로 한다 — 모듈 docstring 에 적는다.
- **엣지 케이스**: 같은 chunk_id 재삽입 → 갱신(건수 그대로). 존재하지 않는 부모 디렉터리 → `FileNotFoundError`. 질의 `""` → 빈 목록. 질의에 `"`·`*`·`NEAR` → 문법 오류 없이 문자 그대로 찾는다. `limit` 1..200 밖 → `ValueError`. 지역 필터가 빈 집합 → 빈 목록.
- **fixture 경로**: 합성 청크(`○○ 행차`, `○○ 물길`)로 테스트한다. 실데이터는 T209·T210 이 넣는다.
- **지켜야 할 규칙**: D8(승인 전이면 문안대로 진행). AGENT_CONTEXT 3.3 "수집할 때 쪽수·게시일을 함께 저장하지 않으면 태그를 만들 수 없다" → locator·collected_at 필수. 표준 라이브러리만.
- **DoD**: `uv run python -m pytest -q tests/domains/kcontext/index` 통과(FTS 경로·LIKE 경로 둘 다, FTS 주입 문자열 케이스 포함) · `uv run python -m domains.kcontext.index stats --db /tmp/kc-test.db` 가 빈 색인에서 0 을 출력하고 0 으로 끝난다 · ruff.

---

#### T203 — 지역 설정·데이터 폴더 배치·실행 디렉터리 [필수 · Stage 1 · 병렬]
- **변경 파일**
  - 신규: `domains/__init__.py`(빈 파일), `domains/kcontext/__init__.py`(docstring 만), `domains/kcontext/paths.py`, `domains/kcontext/regions.py`
  - 신규: `domains/kcontext/data/regions/{euljiro,jongno,sinchon}.json`, `domains/kcontext/data/situations/demo_day1.json`, `domains/kcontext/data/raw/.gitkeep`
  - 수정: `.gitignore` (`var/`, `domains/kcontext/data/raw/*`, `!domains/kcontext/data/raw/.gitkeep` 추가)
  - 신규: `tests/domains/kcontext/test_kc_regions.py`
- **인터페이스**
  ```python
  # paths.py
  def repo_root() -> Path
  def data_dir() -> Path      # env KC_DATA_DIR, 기본 repo_root()/domains/kcontext/data
  def var_dir() -> Path       # env KC_VAR_DIR, 기본 repo_root()/var  (만들지 않는다 — 쓰는 쪽이 mkdir)

  # regions.py
  @dataclass(frozen=True)
  class Region:
      id: str                                   # ^[a-z][a-z0-9_]{0,31}$, 파일 이름과 같아야 한다
      name: dict[str, str]                      # {"ko","en"}
      gu: tuple[str, ...]                       # 관할 구 이름
      bbox: tuple[float, float, float, float] | None   # (south, west, north, east)
      center: tuple[float, float] | None        # (lat, lng)
      keywords: tuple[str, ...]                 # 주소·행사 문구 매칭용
      sillok_keywords: tuple[str, ...]          # 실록 구절 매칭용 옛 지명 (H2)
  class RegionConfigError(ValueError)
  def load_regions(directory: Path | None = None) -> dict[str, Region]   # 기본 data_dir()/regions
  def regions_at(lat: float, lng: float, regions: Mapping[str, Region]) -> list[str]   # bbox 포함 지역 id
  def regions_in_text(text: str, regions: Mapping[str, Region], *, field: Literal["keywords", "sillok_keywords"] = "keywords") -> list[str]
  ```
- **핵심 로직**
  1. 지역 JSON 은 `{"id", "name": {"ko","en"}, "gu": [...], "bbox": null, "center": null, "keywords": [...], "sillok_keywords": [], "note": "bbox·center 는 H7 에서 채운다 [확인 필요]"}`. 값 출처: 지역 이름·구는 CONTEXT_NOW_KOREA 4장 "데모 지역의 구청 게시판(종로구, 중구, 서대문구)"과 AGENT_CONTEXT 3.2 에서 가져온다(을지로 → 중구, 종로 → 종로구, 신촌 → 서대문구). `keywords` 에는 지역 이름 자체와 구 이름만 넣는다. 좌표는 **넣지 않는다**(H7).
  2. `load_regions`: 디렉터리의 `*.json` 을 이름순으로 읽는다. id 중복·파일 이름 불일치·bbox 순서 오류(south ≥ north 또는 west ≥ east)·모르는 키 → `RegionConfigError`(파일 이름 포함). 파일 0개 → `RegionConfigError`.
  3. `regions_at`: bbox 가 None 인 지역은 건너뛴다(좌표로는 매칭되지 않음).
  4. `regions_in_text`: NFKC 정규화 후 부분 문자열 일치. 결과는 id 정렬·중복 없음.
  5. `demo_day1.json`: CONTEXT_NOW_KOREA 2장 대화 예시(10월 15~18일, 종로3가 숙소, 1일차 창덕궁 → 익선동, 2일차 경복궁 → 광화문, 3일차 신촌, 관심사 "한국 음식"·"로컬 문화", 일정 최소 변경)를 3.3 입력 형식으로 옮긴다. 연도는 프론트 골격과 같은 2026 을 쓴다. 시간이 대화에 없는 앵커는 프론트 `itinerary.js` 의 예시 시간을 쓰고 `"note": "시간은 예시"` 를 둔다. 모든 `lat`·`lng` 는 `null`(H7). `free_slots` 는 1일차 19:00~23:00, `near: "익선동"`, `inferred: true`.
- **엣지 케이스**: `KC_DATA_DIR` 이 없는 경로 → `load_regions` 가 `RegionConfigError`. bbox 경계 위 좌표 → 포함. 키워드가 빈 문자열 → `RegionConfigError`.
- **fixture 경로**: 테스트는 `tmp_path` 에 합성 지역 JSON(`"id": "region_a"`, 합성 bbox)을 써서 검증한다. 실제 지역 파일은 "로드되고 3개이며 bbox 가 null 이어도 통과"만 확인한다.
- **지켜야 할 규칙**: AGENT_CONTEXT 3.2 — 지역은 설정으로. 좌표를 지어내지 않는다(11장). `.gitignore` 에 비밀 패턴은 그대로 둔다(규칙 1).
- **DoD**: `uv run python -m pytest -q tests/domains/kcontext/test_kc_regions.py` · `git check-ignore -v var/x domains/kcontext/data/raw/x.xml` 가 둘 다 무시됨을 출력 · `git check-ignore domains/kcontext/data/raw/.gitkeep` 는 무시되지 않음(종료 코드 1) · ruff.

---

#### T204 — [확인] 실록 XML 구조·이용허락·발췌 fixture [필수 · Stage 1 · 병렬 · H1 대기 가능]
- **변경 파일** (신규): `docs/spikes/sillok.md`, `tests/fixtures/kcontext/sillok/sample.xml`(H1 이 있을 때만), `tests/fixtures/kcontext/sillok/README.md`
- **산출물 형식** (`docs/spikes/sillok.md`)
  ```markdown
  # 실록 XML 확인 (T204)
  상태: 확정 | 대기 — H1
  내려받은 날짜: YYYY-MM-DD (사람 기록) · 페이지 URL: … · 이용허락 문구(원문 그대로 인용): …
  ## 파일
  | 파일 | 크기 | 인코딩 | 루트 요소 | 기사 수(셀 수 있으면) |
  ## 요소·속성 표 (실측 — 파일에서 본 이름만)
  | 의미 | XPath/요소·속성 이름 | 예시 값(○○ 로 가림 가능) | 비고 |
  | 기사 ID | … | | |
  | 왕대 | … | | |
  | 날짜(연·월·일) | … | | 음력/양력 표기 근거 |
  | 제목 | … | | |
  | 국역 본문 | … | | |
  | 원문(한문) 본문 | … | | |
  | 원문 URL 을 만들 단서 | … | | URL 형식은 실제로 1건 열어서 확인 |
  ## 인물 CSV 열
  ## locator 형식 결정 (예: "세종 ○년 ○월 ○일 · 기사 ID")
  ## 확인 필요로 남은 것
  ```
- **핵심 로직(절차)**
  1. H1 파일이 `domains/kcontext/data/raw/sillok/` 에 있는지 확인한다. 없으면 상태를 "대기 — H1" 로 적고 공공데이터포털 목록 페이지에서 확인할 수 있는 것(파일 형식·이용허락 표기)만 적은 뒤 끝낸다.
  2. 파일이 있으면 `python3 -I` 와 표준 라이브러리 `xml.etree.ElementTree.iterparse` 로 앞부분만 읽어 요소·속성 이름을 표로 적는다(전체를 메모리에 올리지 않는다). 앞 4KB 에 `<!DOCTYPE`·`<!ENTITY` 가 있으면 기록한다(T209 가 거부 여부를 정한다).
  3. 날짜가 음력인지는 **자료 설명 문서나 파일 안의 표기로만** 판단하고, 근거를 적는다. 근거가 없으면 `[확인 필요]`.
  4. 원문 URL: 기사 ID 로 공식 사이트 URL 을 만들 수 있는지 1건을 실제로 열어 확인한다(`curl -sI`). 확인되지 않으면 URL 은 빈 문자열로 두기로 적는다.
  5. 데모 지역 관련 구절 규모를 가늠한다: 지역 이름·구 이름으로 grep 한 기사 수(H2 판단 재료).
  6. 발췌: 기사 2~3건(30KB 이하)을 원래 구조 그대로 잘라 `sample.xml` 로 저장한다. 첫 줄 주석에 출처·내려받은 날짜·이용허락 문구를 적는다. 이용허락 문구에 재배포 제한이 있으면 저장하지 않고 상태를 "fixture 불가"로 적는다.
- **엣지 케이스**: 파일이 ZIP·여러 개 → 압축은 새 빈 디렉터리(`raw/sillok/extracted/`)에 풀고 거기서 읽는다(외부 파일은 신뢰하지 않음). 인코딩이 UTF-8 이 아님 → 선언 인코딩을 적는다.
- **fixture 경로**: H1 이 없으면 fixture 를 만들지 않는다. 합성 XML 도 만들지 않는다(구조를 지어내게 되므로).
- **지켜야 할 규칙**: 추측하지 않는다(`[확인 필요]`). 내려받은 원본은 커밋하지 않는다(`raw/` gitignore). 내려받은 파일을 스크립트 디렉터리에서 실행하지 않는다.
- **DoD**: `docs/spikes/sillok.md` 존재, 상태 줄이 "확정" 또는 "대기 — H1". 확정이면 `python3 -I -c "import xml.etree.ElementTree as E; E.parse('tests/fixtures/kcontext/sillok/sample.xml')"` 성공.

---

#### T205 — [확인] TourAPI·서울 문화행사 API 호스트·필드·이용조건 [필수 · Stage 1 · 병렬]
- **변경 파일**
  - 신규: `docs/spikes/events_api.md`
  - 신규: `domains/kcontext/ingest/events/field_maps/tourapi_festival.json`, `seoul_cultural.json`
  - 신규: `tests/fixtures/kcontext/events/tourapi_festival.synthetic.json`, `seoul_cultural.synthetic.json`, `README.md`
  - 수정: `.env.example` (변수 **이름**만 추가: `DATA_GO_KR_SERVICE_KEY=`, `SEOUL_OPENAPI_KEY=`, 주석 "호스트 수집기 전용(D7), 샌드박스에 넣지 않는다")
- **필드 매핑 파일 형식** (T210 이 그대로 읽는다 — 이 형식은 이 문서가 정한다)
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
  `"[확인 필요]"` 가 하나라도 남아 있으면 `status` 는 `unknown` 이고, T210 의 `fetch` 는 실행을 거부한다(정규화는 fixture 로 진행).
- **핵심 로직(절차)**
  1. **키 없이**: 공공데이터포털의 TourAPI 서비스 페이지와 활용가이드(CONTEXT_NOW_KOREA 4장이 언급한 `searchFestival2`·`locationBasedList2` 오퍼레이션), 서울 열린데이터광장의 문화행사 정보 서비스 페이지에서 호스트·경로·필수 파라미터·응답 필드 이름·날짜 형식·페이지 처리·호출 한도·이용허락 유형·재배포 조건을 찾아 표로 적는다. 출처 URL 을 칸마다 붙인다. 찾지 못한 칸은 `[확인 필요]`.
  2. 서울 쪽은 "문화행사 정보"의 정확한 서비스 이름부터 확인한다(이 계획에서는 이름을 정하지 않는다).
  3. **키가 있으면(H3·H4)**: 각 1회 실호출(여행 기간 날짜·서울 지역 조건). 원응답은 `domains/kcontext/data/raw/events/` 에 저장(gitignore)하고, 요청 URL 을 문서에 적을 때 키 파라미터 값을 `***` 로 가린다. 응답으로 필드 매핑을 `confirmed` 로 올린다.
  4. 합성 fixture: 확인된(또는 문서 기반) **필드 이름**을 쓰고 값은 `○○ 예시 행사`·합성 날짜·합성 좌표로 3~5건 만든다. 최소 포함: 여행 기간 안 1건, 여행 기간 전에 끝난 1건, 날짜 비어 있는 1건, 같은 행사 이름이 다른 1건(중복 후보), 좌표 없는 1건. 파일 머리에 `"_synthetic": true` 와 생성 근거(문서 기반/실응답 기반)를 둔다.
- **엣지 케이스**: 응답이 XML 만 → 문서에 적고 매핑에 `"format": "xml"` 추가(T210 이 처리). 키를 셸에 넣었는데 `.env` 에만 있음 → `scripts/preflight.sh` 의 안내를 따른다.
- **fixture 경로**: 키 없이 1·2·4단계만으로 완료 가능(`status: docs_only`).
- **지켜야 할 규칙**: 규칙 1(키 값 금지, 로그·문서에 남기지 않음). 호스트명·필드는 문서·실측에서 본 것만. TourAPI·서울 원응답은 재배포 조건 확인 전 커밋 금지.
- **DoD**: `docs/spikes/events_api.md` 와 field_map 2개, 합성 fixture 2개 존재 · `python3 -c "import json,sys; [json.load(open(p)) for p in sys.argv[1:]]" domains/kcontext/ingest/events/field_maps/*.json tests/fixtures/kcontext/events/*.json` 성공 · `git diff .env.example` 에 값 없는 이름만.

---

#### T206 — [확인] 도보 경로: PlayMCP 카카오맵 서버 호출 가능성 + OSM 대안 [필수 · Stage 1 · 병렬 · 결론 "대기" 허용]
- **변경 파일** (신규): `docs/spikes/walk_route.md`
- **산출물 형식**: "결론: kakao_mcp | osm | estimate_only | 대기 — H5" 한 줄 + 아래 표.
  | 항목 | 카카오맵 MCP(PlayMCP) | OSM 대안 |
  |---|---|---|
  | 엔드포인트·전송 방식 | | |
  | 인증(토큰 종류·발급 주체·수명·서버 보관 가능 여부) | | |
  | MCP 프로토콜 버전(OpenShell 기본 허용 `2025-11-25` 와 비교) | | 해당 없음 |
  | 도구 이름(사용자 확인: `GetWalkDirections`, `SearchPlaceByKeywordOpen`) · 입력·출력 필드 | | |
  | 경유지 지원 | | |
  | 호출 한도·이용약관(서버 재사용·캐시 허용) | | |
  | 응답 좌표 순서 | | |
  | 라이선스·표기(OSM 은 ODbL) | | |
  | 이 PC(GPU 없음)·Brev 에서 돌릴 수 있는가(엔진 직접 운영 시) | | |
- **핵심 로직(절차)**
  1. PlayMCP: 공식 안내 페이지에서 엔드포인트·인증 방식을 확인한다. 사람(H5)이 카카오 로그인·본인인증을 하고 받은 인증 수단을 **서버 프로세스에서** 쓸 수 있는지(브라우저 세션 전용인지) 확인한다. 도구 목록(`tools/list`)을 1회 받아 도구 이름과 입력 스키마를 그대로 옮긴다. 토큰은 문서·로그에 남기지 않는다.
  2. 도보 경로 1회 호출(합성이 아닌 공개 장소 두 곳 이름으로) 결과의 필드 이름과 단위(m·초)를 적는다.
  3. OSM 대안: 공개 도보 라우팅 서비스 또는 자체 엔진 후보를 공식 문서로 확인하고 이용 정책·라이선스를 적는다. 후보 이름·호스트는 문서에서 본 것만 쓴다.
  4. 네이버 Directions 는 자동차 전용(사용자 문서 확인 완료)이라 제외했다고 한 줄 적는다.
  5. D9 문안과 다른 결론이 나오면 "D9 수정 필요"로 표시한다.
- **엣지 케이스**: 인증이 사람 세션에 묶여 서버에서 못 씀 → 결론 `osm` 또는 `estimate_only`. 아무것도 확인 못 함 → `대기 — H5`.
- **fixture 경로**: 결론과 무관하게 T212 는 추정 공급자로 진행한다.
- **지켜야 할 규칙**: 규칙 4 정신(기억이 아니라 문서로 확인). 규칙 1(토큰을 남기지 않음). 지도 서비스로 나가는 것은 장소 이름과 좌표뿐(CONTEXT_NOW_KOREA 4.2) — 확인 호출에도 일정·대화를 넣지 않는다.
- **DoD**: `docs/spikes/walk_route.md` 에 결론 한 줄과 표가 있다.

---

#### T207 — backend: 사람 승인 API + 보안 로그 조회 [필수 · Stage 1 · 병렬]
- **변경 파일** (신규): `backend/app.py`, `backend/settings.py`, `backend/security_log.py`, `backend/routers/review.py`; `tests/backend/test_kc_backend_review.py`, `tests/backend/test_kc_security_log.py`, `tests/backend/test_kc_backend_boundary.py`
- **인터페이스**
  ```python
  # settings.py
  @dataclass(frozen=True)
  class Settings:
      hitl_db: Path            # env KC_HITL_DB, 기본 var_dir/hitl.db  (paths 는 os.environ 으로 직접 계산 — domains 를 import 하지 않는다)
      audit_dir: Path          # env KC_AUDIT_DIR, 기본 <repo>/var/audit
      output_dir: Path         # env KC_OUTPUT_DIR, 기본 <repo>/var/output   (T218 이 쓴다)
      reviewer_id: str         # env KC_REVIEWER_ID, 기본 "human:demo"
      reviewer_auth_source: str  # 기본 "backend-local-demo"
      cors_origins: tuple[str, ...]  # env KC_CORS_ORIGINS(쉼표), 기본 ("http://localhost:8766",)
      @classmethod
      def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings"
  # __post_init__: reviewer_id 를 strip 한 값이 비었거나 "agent:" 로 시작하면 ValueError (S1 W6 대응)

  # security_log.py  (순수 함수 — 테스트 쉬움)
  SECURITY_DRAFT_KINDS = ("source_request", "policy_proposal")
  DENY_ERROR_TYPES = ("InjectionBlocked", "PathDenied", "SourceNotAllowed")
  def entry_from_draft(d: Draft) -> dict          # AuditEntry (§5.1)
  def entries_from_events(events: Iterable[AuditEvent], *, run_id: str) -> list[dict]
  def build_entries(drafts: Iterable[Draft], events_by_run: Mapping[str, list[AuditEvent]]) -> list[dict]

  # app.py
  def create_app(settings: Settings | None = None) -> FastAPI
  app = create_app()   # uvicorn backend.app:app — 모듈 import 시 env 를 읽는다

  # routers/review.py
  router = APIRouter(prefix="/api")
  GET  /api/audit                     -> list[AuditEntry]
  POST /api/audit/{entry_id}/decision -> AuditEntry      body: {"decision": "approve"|"reject", "reason"?: str}
  ```
- **핵심 로직**
  1. `create_app`: CORS(설정의 origins 만, 메서드 GET·POST), 시작 시 `hitl_db` 부모 디렉터리를 만들고 파일이 없으면 `core.hitl.init_db` 로 만든다(backend 는 사람 쪽 관리 프로세스). review 라우터 등록. 앱 상태에 settings 보관.
  2. `GET /api/audit`: `DraftWriter` 를 쓰지 않는다(읽기만 — `core.hitl.connect` 로 SELECT 하거나 `DraftWriter(..., actor="backend:reader").list_drafts(kind=...)` 를 kind 별로 호출. 둘 중 `list_drafts` 를 쓴다). `audit_dir/*.jsonl` 을 `core.audit.read_jsonl` 로 읽는다(파일 이름 stem = run_id). 형식이 깨진 파일은 건너뛰고 응답 헤더 `X-Audit-Skipped: <개수>` 로 알린다. `build_entries` 결과를 `at` 오름차순, 같으면 id 순으로 돌려준다.
  3. 매핑 — draft: `state draft → pend`, `approved → approved`, `rejected → rejected`. text: `source_request` payload `{host, reason?}` → `{"ko": f"{host} · 허용 목록에 없음", "en": f"{host} · not on the allow list"}`, `policy_proposal` payload(T208) → `{"ko": f"정책 초안 · 네트워크 {n} · 파일 {m}", "en": ...}`. 모르는 payload 모양 → `{"ko": f"{kind} 요청", "en": f"{kind} request"}`. `decided_by`·`decided_at` 은 draft 값.
  4. 매핑 — audit 이벤트: `phase=error, kind=tool` 이고 `data.error_type ∈ DENY_ERROR_TYPES` → `deny`, text 는 `data.message`(이미 redact 됨)를 ko·en 공통으로. `observe/net` 의 `decision=denied` → `deny` "`{host}:{port}` 차단", `allowed` → `ok`. `result/tool` 이고 name 이 `kc_` 로 시작 → `ok` "`{name}` 실행". 그 밖은 표시하지 않는다. `time` 은 `ts` 를 Asia/Seoul 로 바꾼 `HH:MM:SS`.
  5. `POST /api/audit/{entry_id}/decision`: 본문은 pydantic 모델(`extra="forbid"`) — `decision` 외에 `reviewer`·`decided_by` 같은 키가 오면 422. `entry_id` 가 `draft:` 로 시작하지 않으면 409 `not_decidable`. `Reviewer(id=settings.reviewer_id, auth_source=settings.reviewer_auth_source)` 를 **서버가** 만든다. approve → `ReviewDesk.approve`, reject → `ReviewDesk.reject(reason=본문 reason 또는 "화면에서 거절")`. 예외 매핑: `DraftNotFound` 404 `not_found`, `TransitionError` 409 `already_decided`, `SelfApprovalError` 403 `self_approval`, `DraftValidationError` 422. 성공하면 갱신된 draft 의 AuditEntry.
  6. 모듈 docstring 한계: "인증이 없는 로컬 데모용이다. 승인자 신원은 설정값이며 요청에서 받지 않는다. 공개 배포 전에는 인증 계층이 필요하다(배포는 이번 범위 밖)."
- **엣지 케이스**: audit_dir 없음 → 빈 목록. 같은 run_id 파일 두 개 없음(파일 이름 고유). draft kind 가 목록 밖 → 보안 로그에 넣지 않는다. 승인된 항목에 다시 approve → 409. reviewer_id 가 draft 의 created_by 와 같음 → 403.
- **fixture 경로**: 테스트는 `tmp_path` 에 `init_db` 후 `DraftWriter(actor="agent:test-run")` 로 draft 를 만들고, `AuditLog`+`JsonlSink` 로 이벤트를 써서 검증한다. FastAPI `TestClient` 사용.
- **지켜야 할 규칙**: D2 — 전이는 이 라우터에서만, 신원은 서버 주입(요청 본문 금지). D3 — backend 는 `mcp_server`·`domains` 를 import 하지 않는다(`test_kc_backend_boundary.py` 가 AST 로 검사: `backend/` 의 import 중 `domains`·`mcp_server` 접두가 0건). 규칙 1 — audit 메시지는 이미 redact 된 값만 쓴다.
- **DoD**: `uv run python -m pytest -q tests/backend` 통과(신원 키가 든 본문 422, 자기 승인 403, 이중 승인 409, `draft:` 아닌 id 409, `agent:` reviewer 설정 거부 포함) · `uv run uvicorn backend.app:app --port 8000` 기동 후 `curl -s localhost:8000/api/audit` → `[]` · ruff.

---

#### T208 — (이월 S1-T301 + W-D) 정책 초안 → hitl draft 제출, 쓰기 루트 보정 [필수 · Stage 1 · 병렬]
- **변경 파일**
  - 신규: `core/policy_proposer/submit.py`, `tests/core/policy_proposer/test_proposer_submit.py`
  - 수정: `core/policy_proposer/baseline.py` (`WRITE_PROPOSAL_ROOTS`·`NEVER_WRITE`)
  - 수정: `/workspace` 를 단언하는 기존 proposer 테스트(있으면 해당 줄만)
  - **고치지 않음**: `core/policy_proposer/__init__.py` (S1 규칙 — 서브모듈 경로로 import)
- **인터페이스**
  ```python
  # submit.py
  POLICY_DRAFT_KIND = "policy_proposal"
  def to_payload(draft: PolicyDraft) -> dict[str, Any]
      # {"yaml": render_yaml(draft), "summary": {"network": int, "filesystem": int, "skipped": int},
      #  "skipped": [{"subject": str, "reason": str}, ...]}   (필드 이름은 model.py 실제 속성에 맞춰 채운다)
  def submit(draft: PolicyDraft, writer: DraftWriter) -> Draft    # writer.create(POLICY_DRAFT_KIND, to_payload(draft))
  ```
- **핵심 로직**
  1. `submit` 은 `DraftWriter.create` 만 부른다. 상태 전이·DB 직접 접근 없음. payload 는 256KiB 상한에 걸리면 `DraftValidationError` 를 그대로 올린다.
  2. W-D(S1 "문서 확인 후속" 절): `WRITE_PROPOSAL_ROOTS` 에서 문서에 없는 `/workspace` 를 뺀다. `NEVER_WRITE` 에 에이전트 자기 설정 경로 `/sandbox/.openclaw`, `/sandbox/.hermes`, `/sandbox/.deepagents`, `/sandbox/.nemoclaw` 를 더한다(S1 완료 기록의 문서 확인 결과). 이 경로 아래 쓰기 관찰은 제안에 넣지 않고 Skipped 로 보낸다(기존 NEVER_WRITE 처리와 같다).
  3. `READ_PROPOSAL_ROOTS` 는 `WRITE_PROPOSAL_ROOTS` 를 더해 만들고 있으므로 `/workspace` 가 함께 빠진다 — 테스트로 확인.
- **엣지 케이스**: 빈 PolicyDraft → 정상 제출(summary 0). `/sandbox/.openclaw/x` 쓰기 이벤트 → 네트워크·파일 항목에 없음, Skipped 에 있음. `/workspace/x` → 허용 루트 밖이라 Skipped.
- **fixture 경로**: 외부 의존 없음.
- **지켜야 할 규칙**: D2(쓰기는 draft 생성뿐) · D4(입력은 audit/v1) · D3(core 에 도메인 용어 금지).
- **DoD**: `uv run python -m pytest -q tests/core/policy_proposer` 통과 · `rg -n '"/workspace"' core/policy_proposer` 0줄 · 전체 회귀 · ruff.

---

#### T209 — 실록 수집기: XML → 기사 → 청크 → 색인 [필수 · Stage 2 · 병렬 · H1 대기 가능]
- **변경 파일** (신규): `domains/kcontext/ingest/__init__.py`(빈 docstring), `domains/kcontext/ingest/sillok.py`, `tests/domains/kcontext/ingest/test_kc_ingest_sillok.py`
- **착수 조건**: `docs/spikes/sillok.md` 상태가 "확정". 아니면 착수하지 않는다(§7).
- **인터페이스**
  ```python
  @dataclass(frozen=True)
  class SillokArticle:
      article_id: str; king: str | None; date_label: str; title: str | None
      text_ko: str; text_orig: str | None; url: str; calendar: Literal["lunar", "solar", "unknown"]
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
  1. 파일마다 앞 4KB 를 읽어 `<!DOCTYPE` 또는 `<!ENTITY` 가 있으면 그 파일을 건너뛰고 `skipped_files` 에 이유를 남긴다(외부 엔티티·확장 공격 방지. 표준 라이브러리만 쓰므로 선검사로 막는다).
  2. `iterparse` 로 기사 단위로 읽고 처리한 요소는 `clear()` 한다(대용량 대비).
  3. 출처 매핑: `source_id = f"sillok:{article_id}"`, `tier = "S"`, `name = "조선왕조실록"`, `locator = date_label`(T204 가 정한 형식, 기사 ID 포함), `url`(T204 확인 결과, 미확인이면 `""`), `published = None`, `collected_at` 은 **CLI 인자로 받은 값**(파일 수정 시각으로 대신하지 않는다), `meta = {"calendar": ..., "king": ..., "article_id": ...}`.
  4. 청크: `chunk_text(text_ko)`. 각 청크 `quote` 는 청크 앞 300자. 국역이 없고 원문만 있으면 원문으로 청크를 만들고 `meta["lang"]="orig"`.
  5. 지역: `regions_in_text(title + text_ko, regions, field="sillok_keywords")`. `sillok_keywords` 가 모두 비어 있으면 `keywords` 로 대신한다(H2 전 기본값). `mode="regions"` 이면 지역이 없는 기사를 건너뛴다.
  6. 1,000 청크 단위로 `index.add` 배치. 끝나면 보고서를 출력(JSON 한 줄)하고 0 으로 끝난다. 처리한 파일이 0개면 2.
- **엣지 케이스**: 본문 비어 있음 → 기사 건너뜀. `article_id` 없음 → 기사 건너뜀(셈). 같은 기사 재수집 → chunk_id 가 같아 갱신. `--collected-at` 형식 오류 → 종료 코드 2.
- **fixture 경로**: `tests/fixtures/kcontext/sillok/sample.xml`(T204). 테스트는 지역 설정을 `tmp_path` 에 합성으로 만들고 fixture 안 단어 하나를 `sillok_keywords` 로 넣어 regions 모드를 검증한다. DOCTYPE 거부는 `tmp_path` 에 만든 짧은 합성 파일로 검증(구조 추측이 아니라 거부만 확인).
- **지켜야 할 규칙**: AGENT_CONTEXT 7장 "출처 이름·위치·URL·원문 구절·수집일" 필수 · D7·D8 · 지역 리터럴 금지 · 원본 커밋 금지.
- **DoD**: `uv run python -m pytest -q tests/domains/kcontext/ingest/test_kc_ingest_sillok.py` · `uv run python -m domains.kcontext.ingest.sillok --src tests/fixtures/kcontext/sillok --db /tmp/kc-sillok.db --collected-at 2026-10-07 --mode all` 가 0 으로 끝나고 `uv run python -m domains.kcontext.index stats --db /tmp/kc-sillok.db` 가 S 등급 청크 1건 이상 · ruff.

---

#### T210 — 행사 수집·정규화(TourAPI·서울·수기 JSON) [필수 · Stage 2 · 병렬]
- **변경 파일** (신규): `domains/kcontext/ingest/events/__init__.py`, `normalize.py`, `fetch.py`, `store.py`, `manual.py`, `__main__.py`; `tests/domains/kcontext/ingest/test_kc_ingest_events_normalize.py`, `test_kc_ingest_events_fetch.py`, `test_kc_ingest_events_manual.py`, `tests/fixtures/kcontext/events/manual.synthetic.json`
  - `field_maps/` 는 T205 소유 — 읽기만 한다.
- **인터페이스**
  ```python
  # normalize.py
  @dataclass(frozen=True)
  class NormalizeResult: records: tuple[EventRecord, ...]; problems: tuple[str, ...]; skipped_out_of_region: int
  def load_field_map(provider: Literal["tourapi", "seoul"]) -> dict
  def normalize(raw: Mapping | str, *, provider: str, field_map: Mapping, collected_at: str,
                regions: Mapping[str, Region]) -> NormalizeResult
  # fetch.py
  class FetchError(RuntimeError); class KeyMissing(FetchError); class FieldMapUnconfirmed(FetchError)
  def fetch(field_map: Mapping, *, date_from: str, date_to: str, client: httpx.Client | None = None,
            env: Mapping[str, str] | None = None, max_pages: int = 10) -> list[Mapping]   # 원응답 페이지들
  # store.py
  def write_jsonl(records: Iterable[EventRecord], path: Path) -> int
  def read_jsonl(path: Path) -> list[EventRecord]
  def to_chunks(r: EventRecord) -> list[Chunk]       # 색인 검색용
  # manual.py — 사람이 손으로 넣는 공지(구청 공지·변경 공지)와 평가용 합성 자료
  def load_manual(path: Path, *, regions) -> NormalizeResult   # EventRecord 모양 JSON 배열
  # CLI
  # python -m domains.kcontext.ingest.events --provider tourapi|seoul|manual --from YYYY-MM-DD --to YYYY-MM-DD
  #   [--fixture PATH] --out var/data/events/<provider>.jsonl [--db var/index/kcontext.db] --collected-at YYYY-MM-DD
  ```
- **핵심 로직**
  1. `normalize`: `items_path` 로 목록을 꺼내고 `fields` 매핑대로 값을 뽑는다. 날짜는 `date_format` 으로 파싱해 `YYYY-MM-DD`, 실패하면 None + problem. 좌표는 `coord_order` 에 따라 `(lat, lng)` 로 맞추고 숫자가 아니거나 범위 밖이면 None + problem. 매핑 값이 `"[확인 필요]"` 이거나 빈 문자열인 필드는 None 으로 둔다.
  2. 출처: `SourceRef(id=f"{provider}:{원본 id}", tier="B", name=("한국관광공사 TourAPI" | "서울 열린데이터광장 문화행사"), locator=(갱신일 있으면 f"{갱신일} 갱신" 없으면 f"{collected_at} 수집 · 갱신일 미제공"), url=(url 필드 값 또는 ""), published=갱신일, collected_at, quote=f"{제목} / {시작일}–{종료일} / {장소}")`. URL 을 만들어 내지 않는다.
  3. 지역: 좌표가 있으면 `regions_at`, 없으면 주소·장소명으로 `regions_in_text`. 둘 다 없으면 `skipped_out_of_region` 에 세고 버린다(SCOPE: 데모 지역 밖 자료 제외).
  4. 카테고리: `field_map.fields.category` 값을 `EVENT_CATEGORIES` 로 옮기는 표는 field_map 에 `"category_map"` 이 있을 때만 쓰고, 없으면 `"other"`. `status` 는 API 값에서 알 수 없으면 `"unknown"`. `geometry_type` 은 좌표 있으면 `point`, 없으면 `approx`.
  5. `fetch`: `field_map.status != "confirmed"` 또는 엔드포인트 칸에 `[확인 필요]` 가 있으면 `FieldMapUnconfirmed`. 키는 `env[field_map.endpoint.key_env]` 에서 읽고 없으면 `KeyMissing(f"{key_env} 가 설정되지 않았다")`(값을 출력하지 않는다). httpx 타임아웃 10초, 재시도 없음, 페이지는 `max_pages` 까지. HTTP 오류·JSON 파싱 오류는 `FetchError` 로 바꾸고 **메시지에서 요청 URL 의 키 파라미터 값을 `***` 로 가린다**(`core.audit.redact_text` 도 거친다).
  6. CLI: `--fixture` 가 있으면 fetch 대신 파일을 읽는다. 결과 JSONL 저장 + `--db` 가 있으면 `to_chunks` 를 색인에 넣는다. 보고서(JSON 한 줄: records, problems 수, skipped) 출력. `KeyMissing` → 종료 코드 2 와 "`--fixture` 로 실행할 수 있다" 안내.
  7. `manual.py`: `EventRecord` 모양 JSON 배열(`fetched_from: "manual"`)을 읽어 같은 검증·지역 처리. 평가 세트(T220)와 데모의 "변경 공지" 사례를 넣는 입구다.
- **엣지 케이스**: 응답이 빈 목록 → records 0, 정상 종료. items_path 중간이 dict 대신 list → problem 1건 후 빈 결과. 종료일이 시작일보다 앞 → problem, 두 값 모두 유지(판정이 처리). 같은 id 중복 → 뒤 것만 남기고 problem.
- **fixture 경로**: T205 합성 fixture 와 `manual.synthetic.json`(여행 기간 안·밖, 취소 공지, 시간 변경 공지, 좌표 없음 포함, 모두 `○○`). fetch 테스트는 `httpx.MockTransport` 로 한다(네트워크 없음) — 키 가림·KeyMissing·Unconfirmed 검증.
- **지켜야 할 규칙**: D7(실호출은 호스트, 키는 env 이름) · 규칙 1 · 필드 이름은 field_map 에서만(코드에 API 필드 이름 리터럴 금지 — 테스트가 `rg` 로 확인하지는 않지만 리뷰 항목) · 지역 리터럴 금지.
- **DoD**: `uv run python -m pytest -q tests/domains/kcontext/ingest -k events` · `uv run python -m domains.kcontext.ingest.events --provider manual --fixture tests/fixtures/kcontext/events/manual.synthetic.json --from 2026-10-15 --to 2026-10-18 --out /tmp/kc-ev.jsonl --collected-at 2026-10-07` 0 종료 · ruff.

---

#### T211 — 판정 엔진(등급·충돌·무관 걸러내기·주입 차단 → 6장 형식) [필수 · Stage 2 · 병렬]
- **변경 파일** (신규): `domains/kcontext/judge/__init__.py`, `model.py`, `inject.py`, `terms.py`, `story.py`, `now.py`, `config.py`; `domains/kcontext/data/normalize/terms.json`; `tests/domains/kcontext/judge/test_kc_judge_story.py`, `test_kc_judge_now.py`, `test_kc_judge_inject.py`
- **인터페이스**
  ```python
  # model.py
  @dataclass(frozen=True) class Rejection: target_id: str; claim: str; reason: str; detail: str   # reason ∈ REJECT_REASONS
  @dataclass(frozen=True) class Blocked: source_id: str; verdict: Literal["injection", "suspicious"]; rules: tuple[str, ...]
  @dataclass(frozen=True) class Conflict: field: str; values: tuple[dict, ...]; chosen: str | None; reason: str
  @dataclass(frozen=True)
  class StoryJudgement: record_id: str; verdicts: tuple[dict, ...]; badge: str | None
                        accepted_claims: tuple[int, ...]; disputed: bool; caveats: tuple[str, ...]
                        rejected: tuple[Rejection, ...]; blocked: tuple[Blocked, ...]
  @dataclass(frozen=True)
  class EventDecision: event_ids: tuple[str, ...]; primary: EventRecord; sources: tuple[SourceRef, ...]
                       badge: str; verdicts: tuple[dict, ...]; caveats: tuple[str, ...]; conflicts: tuple[Conflict, ...]
  @dataclass(frozen=True)
  class NowJudgement: decisions: tuple[EventDecision, ...]; rejected: tuple[Rejection, ...]
                      blocked: tuple[Blocked, ...]; funnel: Mapping[str, int]
  # inject.py
  class InjectionBlocked(Exception)          # audit error_type 로 쓰인다(T207 DENY_ERROR_TYPES)
  def screen(text: str, *, source_id: str) -> Blocked | None       # core.guard.scan 사용. CLEAN → None
  # config.py
  @dataclass(frozen=True)
  class JudgeConfig: fresh_days: int = 14; dedupe_m: int = 150; title_similarity: float = 0.6
                     alcohol_categories: tuple[str, ...] = ("night_market", "bar")
                     superlatives: tuple[str, ...] = ("최초", "유일", "최대", "가장 오래된")
  # story.py
  def judge_story(rec: StoryRecord, *, terms: Terms, cfg: JudgeConfig = JudgeConfig()) -> StoryJudgement
  # now.py
  def judge_events(records: Sequence[EventRecord], situation: Mapping, *, now: date,
                   cfg: JudgeConfig = JudgeConfig()) -> NowJudgement
  # terms.py
  @dataclass(frozen=True) class Terms: replacements: tuple[tuple[str, str, str], ...]   # (옛, 새, 시점)
  def load_terms(path: Path | None = None) -> Terms
  def outdated_terms(text: str, terms: Terms) -> list[tuple[str, str, str]]
  ```
  `config.py` 의 수치는 모두 `[제안]` 이며 docstring 에 출처(CONTEXT_NOW_KOREA 3.2 "최근 7일 이내 갱신 +10" 등)와 "시험 후 조정"을 적는다.
- **핵심 로직 — 공통 주입 차단**: 판정에 들어가는 모든 외부 텍스트(근거의 `quote`·`says`, 행사 `description`·`title`)를 `screen` 한다. `INJECTION` → 그 근거(또는 행사 레코드)를 제외하고 `Blocked` + `Rejection(reason="지시문 포함")`. `SUSPICIOUS` → 제외하지 않고 `Blocked(verdict="suspicious")` 와 caveat "자료에 지시문 의심 문구". 텍스트를 따르거나 실행하지 않는다(AGENT_CONTEXT 4.4).
- **핵심 로직 — 이야기(4.1·4.2, CONTEXT_STORY_ROUTE 3장)**: 주장(claim)마다
  1. 근거를 `S/A`(`sa`)와 `B`·`C/D` 로 나누고 stance 로 support/contradict 를 센다. 독립 출처 수는 `source.name` 기준 중복 제거(4.2-4 "서로 베낀 자료는 한 개" — 이름이 같으면 한 개로 센다).
  2. `outdated_terms` 가 걸린 근거는 모순이 아니라 "옛 명칭 사용(오래된 자료)" 메모만 남긴다(4.3).
  3. claim_kind 별:
     - `fact`: `sa` support ≥1 이고 `sa` contradict 0 → accepted, badge `기록`. `sa` 양쪽 모두 있음 → disputed. `sa` support 없음 + B support 만 → unverified(B 는 역사 서술을 A 이상으로 교차 확인해야 한다). C/D 만 → rejected `신뢰 불가`.
     - `lore`(전승이 존재한다는 주장): S/A/B support ≥1 → accepted, badge `전승`. C/D 만 → rejected `신뢰 불가`.
     - `inference`: A 이상 support ≥1 → accepted, badge `추정`. 아니면 unverified.
  4. 주장 문장에 `superlatives` 가 있고 A 이상 support 가 없으면 rejected `신뢰 불가`(4.3 관광 홍보 과장).
  5. confidence: 독립 S/A support ≥2 → high, 1 → medium, 그 외 low. disputed 는 low.
  6. verdict 객체는 6장 형식: `{"claim": pick(text), "sources": [{"id","tier","date": published,"stance","says"?}], "verdict", "reason", "confidence"}`. reason 은 규칙 이름을 한국어 한 문장으로(예: "S 등급 근거 2건과 일치").
  7. 카드 딱지: accepted 또는 disputed 주장이 하나도 없으면 `badge=None`(카드를 만들지 않는다 — "출처 없으면 카드로 만들지 않는다"). 있으면 그 주장들의 딱지 중 **가장 약한 것**(기록 > 전승 > 추정 순으로 약해진다). disputed 가 있으면 `disputed=True`, caveat "이설 있음", disputed 주장의 딱지는 근거 중 약한 쪽. 해결된 척하지 않는다(4.2-5).
- **핵심 로직 — 지금(CONTEXT_NOW_KOREA 3장)**
  1. 관련성: `region` 이 None → `관련 없음`. 여행 기간(`situation.trip`)과 `[start_date, end_date]` 가 겹치지 않으면: 종료일 < 여행 시작 → `기간 지남`, 시작일 > 여행 끝 → `관련 없음`. 날짜가 없으면 남기고 caveat "날짜 불분명".
  2. 상황: `party.kids` 이고 category ∈ `alcohol_categories` → `상황 부적합`. `weather.rain` 이 true 이고 `outdoor` 가 true → `상황 부적합`. 좌표 없음 → 남기되 caveat "위치 미상"(일정 맞추기 T216 에서 걸러진다).
  3. 중복 병합: 제목 정규화(NFKC, 공백·문장부호 제거, 소문자)가 같거나, 기간이 겹치고 거리 ≤ `dedupe_m` 이고 `difflib.SequenceMatcher` 비율 ≥ `title_similarity` 이면 한 그룹. 그룹 대표(primary)는 tier 가 높고 → `published` 가 최신인 레코드. 나머지는 `Rejection(reason="중복")` 으로 세고 출처는 그룹에 합친다(4.2-4 독립 출처는 `name` 기준).
  4. 충돌(그룹 안): `status`, `start_time`, `start_date`, `place_name` 별로 값이 다르면 `Conflict`. 운영 정보는 **최신이 이긴다**(4.2-3): `published` 가 가장 최신인 B 이상 출처가 **하나뿐이면** 그 값을 채택(`chosen`, reason "최신 공식 공지 채택"). 최신 날짜가 같거나 날짜가 없어 최신을 정할 수 없으면 `chosen=None` → 미해결.
  5. 채택된 status 가 `cancelled` → 그룹 전체 `Rejection(reason="취소됨")`.
  6. 딱지: 미해결 충돌이 있으면 `보류`. 아니면 `확인됨` 조건 = B 이상 출처 ≥1, `start_date`·`place_name` 있음, 가장 최신 출처의 `published`(없으면 `collected_at`)가 `now - fresh_days` 이후. 하나라도 빠지면 `확인 필요`(빠진 항목을 caveat 로: "날짜 불분명", "단독 출처"(C 등급만), "n일 전 갱신").
  7. verdict 객체: 그룹마다 "○○ 행사는 {start}–{end} {place}에서 열린다" 형식 주장 1건(+ 충돌 필드마다 1건). 확인됨 → accepted, 확인 필요 → unverified, 보류 → disputed.
  8. `funnel`: `{"candidates": 입력 수, "adopted": decisions 중 보류 제외 수, "<reason>": 건수 ...}`.
- **엣지 케이스**: 근거 0개 주장 → unverified, 카드 없음. 같은 출처가 support·contradict 둘 다 → contradict 우선, problem 메모. `published` 형식이 날짜가 아님 → None 취급. 모든 근거가 INJECTION → 주장 rejected `지시문 포함`.
- **fixture 경로**: 합성 StoryRecord·EventRecord(`○○`)를 테스트 안에서 만든다. 함정 유형마다 최소 1케이스(연도 불일치, 옛 명칭, 동명이처 → 거리로 다른 그룹, 전설을 사실로 쓴 홍보물(D 등급 fact) → rejected, 날짜 다른 운영 시간 공지 두 개 → 최신 채택, 무관 문서 → 관련 없음, 숨은 지시문 → 지시문 포함).
- **지켜야 할 규칙**: AGENT_CONTEXT 4장·6장 · CONTEXT_STORY_ROUTE 3장 · CONTEXT_NOW_KOREA 3장 · `core.guard` 재사용(새 주입 규칙을 만들지 않는다 — 부족하면 완료 보고에 적는다) · LLM 호출 없음(T223 에서 보조) · 지역 리터럴 금지.
- **DoD**: `uv run python -m pytest -q tests/domains/kcontext/judge` · 모든 verdict 가 `validate_verdict` 문제 0건(테스트에서 확인) · ruff.

---

#### T212 — 도보 시간(추정 공급자) + 경로 A·B·C 조립 [필수 · Stage 2 · 병렬]
- **변경 파일** (신규): `domains/kcontext/geo/__init__.py`, `distance.py`, `router.py`, `routes.py`, `config.py`; `tests/domains/kcontext/geo/test_kc_geo_router.py`, `test_kc_geo_routes.py`
- **인터페이스**
  ```python
  LatLng = tuple[float, float]
  # distance.py
  def haversine_m(a: LatLng, b: LatLng) -> float
  def point_segment_distance_m(p: LatLng, a: LatLng, b: LatLng) -> float
  def projection_t(p: LatLng, a: LatLng, b: LatLng) -> float   # a→b 위 정사영 매개변수(0..1 밖 가능)
  # config.py  (수치는 [제안], docstring 에 근거와 "시험 후 조정")
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
                   router: WalkRouter, cfg: GeoConfig = GeoConfig()) -> list[dict]   # Route dict(T201), 1~3개
  ```
- **핵심 로직**
  1. `EstimateRouter.leg`: 거리 = `haversine × detour_factor` 반올림, 시간 = `ceil(거리 / speed)`, coords = `(a, b)`, `estimated=True`. 같은 점 → 0m·0분.
  2. 경로 후보:
     - **직행**: 기준 경로. 직선 origin→dest 에서 `corridor_m` 안에 있는 정류장(점은 그 점, 구간은 가장 가까운 점)만 "지나가는 길에 있는 이야기"로 포함. 정류장은 `projection_t` 순서.
     - **주제 경로**: 직행에 없는 정류장을 `theme` 별로 묶고, 묶음 크기 내림차순 → theme 이름 순으로 최대 `max_routes - 1` 개. 경로는 origin → (정류장 순서대로; 구간 정류장은 시작점→끝점을 따라 걷는 leg 포함) → dest.
     - 각 경로 `walk_min` = leg 시간 합, `delta_min` = `walk_min - min(walk_min)`. `budget_min` 이 있으면 `delta_min > max_detour_ratio × budget_min` 인 경로는 버린다(CONTEXT_STORY_ROUTE 2.4 우회 한도).
     - 정류장 집합이 같은 경로는 하나만 남긴다. `walk_min` 오름차순으로 정렬해 id `A`·`B`·`C`.
  3. segments: leg 마다 하나. 이야기 정류장으로 이어지는 leg(구간 정류장은 그 구간을 걷는 leg)는 `name = stop.title`, `card_id = stop.card_id`, `weak = stop.weak`. 그 밖의 연결 leg 는 `name = {"ko": "이동", "en": "Walk"}`, `card_id = None`, `weak = False`. 각 segment 에 `length_m`, `walk_min`, `coords`(계약 보충 4번). **구간 이름은 검증된 카드 제목에서만 온다**(지어 붙이지 않는다).
  4. `story_count` = card_id 있는 segment 수, `badge_mix` = 정류장 딱지별 수, `theme` = 직행은 `{"ko": "큰길 따라", "en": "Along the main road"}`(일반 서술, 이야기 이름 아님), 주제 경로는 그 theme 의 표시 이름(정류장 theme 값을 그대로 — theme 표시 이름 표는 T216 이 이야기 레코드에서 가져온다).
  5. badges: 최소 walk_min → `가장 빠름`(동률이면 모두), 최대 story_count(>0) → `이야기 가장 많음`, 추천 = 우회 한도 안에서 story_count 최대(동률이면 walk_min 작은 것) 1개 → `추천`. `recommend_reason`: budget 이 있으면 `{"ko": f"다음 일정까지 {budget_min}분 남아서 {id}를 권해요", "en": f"You have {budget_min} min until your next plan, so I suggest {id}"}`, 없으면 `"이야기가 가장 많은 {id}를 권해요"`.
  6. 모든 경로에 `estimated = any(leg.estimated)`(계약 보충 4번, D9).
- **엣지 케이스**: origin 또는 dest 가 None·범위 밖 → `GeoInputError`. 정류장 0개 → 직행 1개만. 모든 주제 경로가 우회 한도 초과 → 직행 1개. 구간 정류장 좌표 1개 → 점처럼 처리.
- **fixture 경로**: 합성 좌표(`"synthetic"` 주석) 테스트만. 외부 호출 없음.
- **지켜야 할 규칙**: AGENT_CONTEXT 6장 "숫자는 경로 엔진 값" + D9(추정은 `estimated: true`) · CONTEXT_STORY_ROUTE 2.1·2.4·3.2(구간 이름은 검증된 카드에서만, 약한 구간은 weak) · 지역 리터럴 금지.
- **DoD**: `uv run python -m pytest -q tests/domains/kcontext/geo` · 결과 경로가 `validate_route(r, card_ids)` 문제 0건 · ruff.

---

#### T213 — 프론트 map 모듈 [필수 · Stage 2 · 병렬]
- **변경 파일**: `frontend/k-context/src/components/map/index.js`(스텁 교체), `model.js`(신규), `strings.js`(신규), `map.css`(수정); `frontend/k-context/tests/map.model.test.js`(신규)
- **인터페이스**: `mount(root, ctx) -> {destroy()}` (골격 계약 유지). `model.js` 는 DOM 없는 순수 함수:
  ```js
  export function projector(features, {width, height, padding}) // -> ([a,b], space) => [x,y]
  //   space 'schematic' → [x,y] 그대로(viewBox 0 0 600 700), 'geo'(기본) → [lat,lng] 를 등장방형 투영(cos(lat) 보정)
  export function featuresFor(state)   // {routes, oldItems, nowItems, landmarks} — mode·day·selectedRoute 반영
  export function styleFor(item)       // {dash: bool(weak 또는 approx), muted: bool, tone: 'old'|'now'}
  ```
- **핵심 로직**
  1. SVG 하나에 레이어 순서: 랜드마크 → (선택 전) 경로 A·B·C 겹침 / (선택 후) 선택 경로만 → 옛날(segment 는 선, weak 는 점선, point 는 핀) → 지금(point 핀, area 다각형, approx 는 `radius_m` 을 투영 비율로 바꾼 흐린 원 + "정확한 위치는 현장 확인") → 라벨.
  2. `mode`(old/now/both)·`day`(지금 카드는 `slot.day` 일치만) 필터. 보류(`badge` 보류) 카드는 회색. 여행 기간 밖 카드는 그리지 않는다.
  3. 경로선에 A·B·C 표시, `estimated` 경로는 라벨에 "예상"(strings.js). 구간 클릭 → `ctx.actions.selectSeg(card_id)`, 지금 핀 클릭 → `ctx.actions.selectNow(id)`, 경로 클릭 → `ctx.actions.selectRoute(id)`. 선택 구간 강조.
  4. 같은 화면에 `space` 가 섞이면(schematic 과 geo) geo 만 그리고 콘솔 경고 1회.
  5. 외부 요청(타일·SDK·폰트) 없음(D11). 터치 대상 48px 이상, 키보드 포커스 가능(`tabindex`, Enter).
- **엣지 케이스**: 좌표가 모두 같은 점 → 고정 축척으로 가운데. 데이터 없음(loaded 전) → 빈 상태 문구. 카드에 geometry 없음 → 건너뜀.
- **fixture 경로**: mock API(`?api=mock`)의 schematic 데이터 + 테스트 안 합성 geo 데이터.
- **지켜야 할 규칙**: §0.2 프론트 소유 규칙(공용 파일 금지) · D11 · CONTEXT_STORY_ROUTE 2.2(약한 구간 점선, 점/구간 구분) · CONTEXT_NOW_KOREA 2장(지도에 제안하는 것만 강조).
- **DoD**: `(cd frontend/k-context && node --test)` 통과(projector 의 schematic 그대로·geo 투영·padding, featuresFor 의 mode·day 필터, styleFor 의 weak→dash) · 수동: `npm run serve` → `?api=mock` 에서 경로 3개 겹침 → 하나 선택 → 구간 클릭 시 카드 선택이 바뀐다.

---

#### T214 — 프론트 cards + rationale 모듈 [필수 · Stage 2 · 병렬]
- **변경 파일**: `src/components/cards/{index.js, model.js(신규), strings.js(신규), cards.css}`, `src/components/rationale/{index.js, model.js(신규), rationale.css}`; `tests/cards.model.test.js`, `tests/rationale.model.test.js`(신규)
- **인터페이스**: 두 모듈 모두 `mount(root, ctx) -> {destroy()}`. `cards/model.js`:
  ```js
  export function sourceTag(src, lang)        // "[S] 조선왕조실록 · ○○ ○년 ○월 ○일"
  export function visibleTags(card, expanded) // 처음 2개 + "+N 출처"
  export function factLines(card)             // facts[] 가 있으면 [{text, refs:[source id]}], 없으면 body 한 줄
  export function nowHeadline(card, lang)     // "+12분 · 체류 70분" (time_cost_min·stay_min)
  ```
  `rationale/model.js`: `export function panelFor(rationale, openKey)` → 칩 목록과 열린 항목.
- **핵심 로직**
  1. 옛날 카드: 제목·`era`·딱지·출처 태그(펼치지 않아도 보임). 사실 층 문장마다 출처 번호, 문장 hover/탭 → `actions.setHoverFact(n)`. 태그 탭 → `actions.openTag(id)` → 원문 구절(`quote`)·`url`(있을 때만 링크)·`collected_at`·`bib` 를 보여주는 팝오버, 닫기 `actions.closeTag()`. `alternatives` 가 있으면 두 설을 나란히("이설 있음"). 몰입 층은 `state.immersion` 이 켜져 있고 `narration` 이 null 이 아닐 때만, "상상" 표시를 붙여 사실 층과 다른 상자에.
  2. 지금 카드: `slot`(DAY n · HH:MM), `nowHeadline` 을 가장 크게, `only`, `why_fits`, `checks`(ok/warn/bad), 딱지, `caveats`, `local_context` 링크 → `actions.openLocalContext(story_card_id)`, `poster.read`, 버튼 "일정에 추가"/"건너뛰기" → `actions.addSelected()`/`skipSelected()`. 보류 카드는 버튼 없이 "제안하지 않음 — 충돌 미해결".
  3. rationale: 선택 카드(`selectedSeg` 또는 `selectedNow`)가 바뀌면 `ctx.api.getRationale(id)` 를 부르고 모듈 안에서 card id 별로 캐시한다. 칩 탭 → `actions.openEvidence(key)`, 항목 제목·본문·행 표. 카드의 `rejected[]` 를 "걸러낸 것" 목록으로 함께 보여준다. 요청 실패 → 패널에 오류 문구, 다시 시도 버튼.
- **엣지 케이스**: sources 가 1개 → "+N" 없음. `url` 이 빈 문자열 → 링크 없이 서지만. narration null → 몰입 토글 숨김. rationale 이 늦게 오면 그 사이 선택이 바뀐 경우 이전 응답을 버린다(요청 토큰 비교).
- **fixture 경로**: mock API.
- **지켜야 할 규칙**: §0.2 프론트 소유 규칙 · CONTEXT_STORY_ROUTE 2.3(사실 층·몰입 층 분리, 상상 표시, 출처 태그 형식) · CONTEXT_NOW_KOREA 2장(카드 항목) · AGENT_CONTEXT 3.6(채택·탈락·확인 못 한 것) · 이모지 금지.
- **DoD**: `node --test` 통과(sourceTag 형식, visibleTags 접힘, factLines, nowHeadline, panelFor) · 수동: 옛날 카드 태그 탭 → 원문 구절 표시, 지금 카드 추가 → 타임라인 반영(T215 와 함께 확인).

---

#### T215 — 프론트 chat + timeline + securitylog 모듈 [필수 · Stage 2 · 병렬]
- **변경 파일**: `src/components/chat/{index.js, model.js, strings.js, chat.css}`, `src/components/timeline/{index.js, model.js, timeline.css}`, `src/components/securitylog/{index.js, model.js, strings.js, securitylog.css}`(model·strings 신규); `tests/chat.model.test.js`, `tests/timeline.model.test.js`, `tests/securitylog.model.test.js`(신규)
- **인터페이스**: 세 모듈 `mount(root, ctx) -> {destroy()}`. 순수 함수:
  ```js
  // chat/model.js
  export const STEPS = ['일정 이해', '후보 수집', '신뢰도 판단', '일정에 맞추기', '맥락 설명'] // strings 로 ko/en
  export function stepAt(elapsedMs)              // 보내는 중 진행 표시(시간 기반 표시일 뿐, 실제 단계 아님 — 문구에 "진행 중")
  export const EXAMPLES = [...]                   // 예시 질문 3개(ko/en), 마지막은 파일 읽기 요청(보안 시연)
  // timeline/model.js
  export function rowsFor(itinerary, day, {added, skipped, selectedNow})   // original/free/proposal/added 구분
  // securitylog/model.js
  export function groupLogs(logs)                 // pend 먼저, 그 다음 시간 역순
  export function canDecide(entry)                // entry.kind === 'pend'
  export function labelFor(kind, lang)            // 허용됨/거부/승인 대기/사람이 승인/사람이 거절
  ```
- **핵심 로직**
  1. chat: 메시지 목록, 입력창, 보내기 → `actions.send(text)`. `state.sending` 동안 5단계 진행 표시. `reply.blocked` 이면 거부 스타일(빨강 테두리 + "허용된 범위가 아님"). 예시 질문 버튼 3개(빈 대화일 때). 응답 지연 시 입력 잠금.
  2. timeline: DAY 탭(`actions.setDay`), 행 종류 셋(원래 일정 / 제안 / 추가한 것)을 모양으로 구분(색만으로 구분하지 않음). `only: 'added'|'not_added'` 조건 반영(골격 `state/selectors.js` 의 `timelineFor` 가 있으면 그것을 쓴다).
  3. securitylog: 항목마다 시간·종류 라벨·텍스트, `decided_by`·`decided_at`(있을 때). `pend` 항목에만 "사람 전용" 표시와 승인/거절 버튼 → `actions.decide(id, 'approve'|'reject')`. 결정 중 버튼 잠금, 실패 시 항목 아래 오류 문구(409 already_decided 는 "이미 결정됨"). 새 deny 가 오면 목록 맨 위 강조.
- **엣지 케이스**: logs 비어 있음 → "기록 없음". 알 수 없는 kind → 회색 "기타". 메시지 text 가 문자열/객체 둘 다 → `ctx.t`.
- **fixture 경로**: mock API(`decideAudit` 포함).
- **지켜야 할 규칙**: §0.2 프론트 소유 규칙 · D2(승인 버튼은 사람 동작으로만, 신원을 보내지 않는다 — actions.decide 가 이미 그렇다) · CONTEXT_NOW_KOREA 2장(진행 5단계, 타임라인 3구분).
- **DoD**: `node --test` 통과(rowsFor 의 added/not_added, groupLogs 정렬, canDecide, labelFor ko/en) · 수동: 예시 질문 3번째(파일 읽기) → 거부 답변 + 보안 로그 deny, pend 항목 승인 → approved 와 결정자 표시.

---

#### T216 — 파이프라인: 후보 수집 → 판정 → 일정 맞추기 → 카드·경로·근거 → 출력 묶음 [필수 · Stage 3 · 병렬]
- **착수 조건**: D10 승인, 계약 보충 승인.
- **변경 파일** (신규): `domains/kcontext/pipeline/__init__.py`, `situation.py`, `candidates.py`, `fit.py`, `assemble.py`, `strings.py`, `bundle.py`, `run.py`; `tests/domains/kcontext/pipeline/test_kc_pipeline_{fit,assemble,bundle,run}.py`; `tests/fixtures/kcontext/stories/synthetic/*.json`, `tests/fixtures/kcontext/situations/synthetic_day1.json`
- **인터페이스**
  ```python
  # situation.py
  def load_situation(path: Path) -> dict          # validate_situation 문제가 있으면 ContractError
  def walk_request(s: Mapping) -> tuple[LatLng, LatLng, int | None] | None
      # walk_request 가 있으면 그것, 없으면 첫 free_slot 의 near 앵커 → hotel, budget = 슬롯 길이(분). 좌표 없으면 None
  # candidates.py
  @dataclass(frozen=True) class Candidates: stories: tuple[StoryRecord, ...]; events: tuple[EventRecord, ...]
  def collect(s: Mapping, *, stories_dir: Path, events_paths: Sequence[Path], regions: Mapping[str, Region]) -> Candidates
  # fit.py
  @dataclass(frozen=True)
  class Placement: decision: EventDecision; slot: Mapping; at: str; time_cost_min: int; stay_min: int
                   leg_back: WalkLeg | None
  def place(decisions: Sequence[EventDecision], s: Mapping, *, router: WalkRouter,
            stay_by_category: Mapping[str, int]) -> tuple[list[Placement], list[Rejection]]
  # assemble.py
  def story_card(rec: StoryRecord, j: StoryJudgement) -> dict
  def now_card(p: Placement, *, as_of: str, story_cards: Sequence[dict], lang: str) -> dict
  def story_rationale(card: dict, j: StoryJudgement) -> dict
  def now_rationale(card: dict, p: Placement, funnel: Mapping[str, int], conflicts) -> dict
  def itinerary_view(s: Mapping, now_cards: Sequence[dict]) -> dict
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
  1. `run.main`: `run_id = 시각(UTC, 초) + 4자리 난수`. `AuditLog`(JsonlSink → `audit_dir/<run_id>.jsonl`, actor `agent:pipeline-<run_id>`)을 만든다. 단계마다 `audit.call("kc_<단계>", 요약 args)` → `result`. 판정의 `Blocked(injection)` 마다 `call("kc_guard_screen", {"source_id": ...})` 후 `error(call_id, InjectionBlocked(f"{source_id} · 자료 안 지시문 차단"))` → 보안 로그 deny(T207 매핑).
  2. 후보 수집: `stories_dir/**/*.json` → `story_from_dict`(실패 파일은 건너뛰고 problem). 이야기 좌표가 walk_request 경로 bbox(+500m) 안이거나 지역이 상황 앵커 지역과 같으면 포함. 행사는 events JSONL 전부(T210 이 지역 필터를 이미 했다).
  3. 판정: 이야기마다 `judge_story`, 행사는 `judge_events(now=--now 또는 오늘)`.
  4. 옛날 카드: `badge` 가 None 이면 카드를 만들지 않고 rejected 로만 남긴다. 카드 id `card_old_<rec.id>`. `body` = 채택 주장 문장들을 이은 것, `facts` = 주장별 `{text, ref}`(ref 는 카드 sources 안의 1부터 번호), `sources` = 채택·이설 근거의 SourceRef(중복 제거), `geometry` = 레코드 geometry(`space: "geo"`), `badge`, `era`, `alternatives`(disputed 주장의 양쪽 근거 says), `narration` = 레코드 narration 또는 **None**(지어내지 않는다), `rejected` = 판정 rejected 의 `{claim, reason}`, `caveats`, `user_state: "proposed"`, `why_fits: []`.
  5. 경로: `walk_request` 가 있으면 옛날 카드로 `StoryStop`(weak = `alignment == "approx"` 또는 badge `추정`)을 만들어 `build_routes(router=EstimateRouter())`. 좌표가 없으면 경로 0개 + manifest 에 `"routes_skipped": "좌표 없음"`.
  6. 일정 맞추기(`fit.place`): 보류가 아닌 결정마다 — 좌표 없음 → `위치 미상`. 행사 날짜에 해당하는 `free_slots` 중 행사 시간(없으면 하루 종일)과 겹치는 첫 슬롯. 없으면 `상황 부적합`. 추가 이동 = `leg(near→행사) + leg(행사→다음 앵커 또는 숙소) − leg(near→다음)`(near 는 슬롯 `near` 와 이름이 같은 앵커, 없으면 숙소). 추가 이동 > 슬롯 길이 × 0.5 → `동선에서 너무 멂`. 체류 = `stay_by_category`(`[제안]` 설정 상수) 와 남은 슬롯 시간 중 작은 값. 슬롯마다 최대 3개: 순위는 확인됨 먼저 → 관심사 일치(`interests` 문자열이 제목·카테고리에 있음) → 추가 이동 작은 순. 넘친 것은 관심사 불일치면 `관심사 불일치`, 같은 카테고리가 이미 있으면 `중복`, 그 밖 `상황 부적합`. 보류 결정은 카드로 내되(`badge: "보류"`, 버튼 없음은 프론트 몫) 일정에는 넣지 않는다(CONTEXT_NOW_KOREA 3.2).
  7. 지금 카드: id `card_now_<primary.id>`, `slot {day, at, between}`, `time_cost_min`, `stay_min`, `valid {from, to, as_of}`, `why_fits`(일치한 조건만: "관심사와 일치"·"여행 날짜에 열림"·"일정을 거의 바꾸지 않음"), `caveats`(판정 caveat + 술 범주면 "돌아가는 길 도보 {leg_back}분" — 음주 연령 문구는 `[검증 필요]`라 넣지 않는다), `checks`(공식 출처 n건 / 날짜 확인됨·불분명 / n일 전 갱신), `local_context`(300m 안의 옛날 카드가 있으면 `{text: 그 카드 제목, story_card_id}`, 없으면 None — 지어내지 않는다), `kind_label`, `geometry`(point 또는 approx+radius_m 150 `[제안]`, `basis: "주소"`), `body` = 행사 설명 앞 200자(설명이 INJECTION 이었다면 이미 제외됨).
  8. 근거 패널: 프론트 `src/data/rationale.js` 의 모양(`{card_id, chips[{key, tone, label}], items{key: {title, text, rows[{k, v}]}}}`). 옛날: `grade`, (`alt`), (`imm` — narration 이 있을 때만). 지금: `funnel`(판정 funnel + fit rejected 합산), `date`, `src`, `detour`, (`conflict` — 충돌이 있을 때, 채택값과 이유), (`fit` — 관심사 일치 시). 문구는 `strings.py` 의 ko/en 템플릿만 쓴다.
  9. 일정 보기: 입력 앵커 + free_slots + 지금 카드로 `timeline[{day, items[{id, time, kind: original|free|proposal, card_id?, title, sub}]}]`, `landmarks`(앵커 좌표가 있을 때만, `space: "geo"`). 입력 필드는 그대로 둔다(일정을 바꾸지 않는다).
  10. 모든 카드·경로·판정을 `ensure_valid` 로 확인한 뒤 `write_bundle`. 검증 실패 → 묶음을 쓰지 않고 종료 코드 3(문제 목록 stderr).
- **엣지 케이스**: 이야기·행사 0건 → 빈 카드 목록으로 정상 묶음(빈 상태 화면). 상황 파일 오류 → 종료 코드 2. `--events` 파일 없음 → 경고 후 계속. 같은 run_id 충돌 → 난수 재생성.
- **fixture 경로**: `tests/fixtures/kcontext/situations/synthetic_day1.json`(합성 좌표 포함, `"synthetic": true`), `tests/fixtures/kcontext/stories/synthetic/*.json`(이야기 4~5개: 기록 2, 전승 1, 추정 1, 근거 없음 1(탈락), 이설 1), T210 `manual.synthetic.json`.
- **지켜야 할 규칙**: D10(출력은 제안 지위, 전이 없음) · D2 · D9(경로 `estimated`) · AGENT_CONTEXT 3.3·3.6·6장 · CONTEXT_NOW_KOREA 3.3·6.4 · 사실을 지어내지 않는다(narration·local_context 없으면 None) · 지역 리터럴 금지.
- **DoD**: `uv run python -m pytest -q tests/domains/kcontext/pipeline` · `uv run python -m domains.kcontext.pipeline.run --situation tests/fixtures/kcontext/situations/synthetic_day1.json --stories tests/fixtures/kcontext/stories --events /tmp/kc-ev.jsonl --out-root /tmp/kc-out --audit-dir /tmp/kc-audit --now 2026-10-15` 0 종료, `/tmp/kc-out/current.json` 이 가리키는 묶음의 cards·routes 가 계약 검증 통과 · ruff.

---

#### T217 — MCP 도구(검색·도보·출처 요청) + 서버 엔트리 [필수 · Stage 3 · 병렬]
- **착수 조건**: D10 승인. 설치된 `mcp` 패키지의 서버 API 를 **설치된 소스로 확인**한다(`uv run python -c "import mcp, inspect; print(mcp.__file__)"` 후 해당 모듈을 읽는다). 기억으로 API 를 쓰지 않는다(규칙 4 정신).
- **변경 파일** (신규): `mcp_server/server.py`; `mcp_server/tools/kc_search_sources.py`, `kc_plan_walk.py`, `kc_request_source.py`; `domains/kcontext/tools/__init__.py`, `search.py`, `walk.py`, `request_source.py`; `tests/mcp_server/test_kc_mcp_tools.py`, `tests/mcp_server/test_kc_mcp_boundary.py`
- **인터페이스**
  ```python
  # domains/kcontext/tools/search.py  (순수 함수, MCP 무관)
  def search_sources(index: Retriever, query: str, *, regions: list[str] | None, limit: int = 10) -> list[dict]
      # [{"chunk_id","source": {id,tier,name,locator,url,collected_at},"text": guard.wrap(...).render(),"verdict": "clean|suspicious|injection"}]
  # domains/kcontext/tools/walk.py
  def plan_walk(origin: LatLng, dest: LatLng, *, budget_min: int | None) -> dict   # {"legs": [...], "estimated": bool}
  # domains/kcontext/tools/request_source.py
  def request_source(writer: DraftWriter, *, host: str, reason: str) -> dict       # {"draft_id","state":"draft"}
      # kind="source_request", payload {"host","reason"}. host 는 소문자·형식 검증(영숫자·점·하이픈, 253자 이하)
  # mcp_server/tools/kc_*.py — 파일당 도구 1개
  def register(server) -> None      # 서버 객체에 도구를 등록. 도메인 함수를 audited 로 감싼다
  # mcp_server/server.py
  def build_server(*, index_path: Path, hitl_db: Path, audit_dir: Path) -> <mcp 서버 객체>
  def main() -> None                # os.environ["APP_PROCESS_ROLE"] = "agent" 를 core.hitl import 전에 설정. stdio 로 실행
  ```
- **핵심 로직**
  1. `server.main` 맨 위에서 `APP_PROCESS_ROLE=agent` 를 설정한다(S1 T101 의 import 가드를 실제로 켠다). actor 는 서버가 정한다(`agent:mcp-<pid>`), 도구 인자로 받지 않는다.
  2. 각 도구는 `core.audit.audited(log, name="kc_<도구>")` 로 감싼다. 검색 결과의 텍스트는 반드시 `core.guard.wrap(text, source=chunk.source_id)` 로 감싸서 돌려준다(에이전트에게 "데이터일 뿐"임을 표시). INJECTION 청크도 감싸서 돌려주되 verdict 를 함께 준다(숨기지 않는다 — 판정은 에이전트·파이프라인 몫).
  3. `kc_request_source`: 허용 목록 밖 출처가 필요할 때 **draft 만** 만든다. 승인은 backend(사람)에서. 실제 네트워크 허용(정책 반영)은 이번 범위 밖 — docstring 에 "승인되어도 Sprint 2 에서는 정책에 자동 반영되지 않는다(샌드박스 범위 밖)"를 적는다.
  4. (선택) `kc_build_bundle` 은 만들지 않는다 — 파이프라인 실행은 backend 가 별도 프로세스로 한다(D10). 필요해지면 다음 스프린트.
- **엣지 케이스**: 색인 파일 없음 → 도구가 오류 결과("색인이 없다 — 수집기를 먼저 실행")를 돌려주고 audit error. `limit` 범위 밖 → 오류. host 형식 오류 → 오류, draft 없음.
- **fixture 경로**: 테스트는 `tmp_path` 색인(합성 청크 1건에 숨은 지시문 포함)과 `init_db` 한 hitl DB 로 도메인 함수·등록 함수를 직접 부른다. MCP 전송(stdio) 실행은 서버 객체 생성과 도구 목록 확인까지만.
- **지켜야 할 규칙**: D2(쓰기는 draft 와 audit 뿐) · D3(`mcp_server` 는 `backend` 를 import 하지 않는다, `core.hitl` 은 허용 목록 이름만 — 기존 `tests/test_boundaries.py` 가 검사) · 도구 파일당 1개 · 규칙 1(키 없음 — 이 도구들은 외부 호출을 하지 않는다).
- **DoD**: `uv run python -m pytest -q tests/mcp_server tests/test_boundaries.py` · `uv run python -c "from mcp_server.server import build_server; print('ok')"` · `test_kc_mcp_boundary.py`: 서브프로세스로 `APP_PROCESS_ROLE=agent` 에서 `import core.hitl.review` 실패 확인 · ruff.

---

#### T218 — backend 화면 API + 채팅 실행기 [필수 · Stage 3 · 병렬]
- **착수 조건**: D10 승인.
- **변경 파일**: 신규 `backend/routers/view.py`, `backend/runner.py`, `backend/chat.py`, `tests/backend/test_kc_backend_view.py`, `tests/backend/test_kc_backend_chat.py`, `tests/fixtures/kcontext/bundle/`(§5.2 모양의 합성 묶음 1개 + `current.json`); 수정 `backend/app.py`(라우터 등록 두 줄만), `backend/settings.py`(필드 추가: `situation_path`, `run_timeout_s`, `stories_dir`, `events_glob`)
- **인터페이스**
  ```python
  # view.py — §5.1 의 GET 엔드포인트 전부
  def load_bundle(output_dir: Path) -> Bundle | None    # current.json → dir. mtime 으로 캐시
  # runner.py
  class RunBusy(Exception); class RunFailed(Exception)
  def run_pipeline(settings: Settings) -> str          # subprocess 실행, run_id 반환
      # [sys.executable, "-m", "domains.kcontext.pipeline.run", "--situation", ..., "--out-root", output_dir,
      #  "--audit-dir", audit_dir, "--stories", ..., "--events", ...]  env 에 APP_PROCESS_ROLE=agent, cwd=repo root
  # chat.py
  def looks_like_file_request(text: str) -> str | None   # 경로를 돌려주거나 None
  POST /api/messages, GET /api/messages
  ```
- **핵심 로직**
  1. GET 엔드포인트는 묶음 파일을 읽어 그대로 돌려준다. 묶음이 없으면 503 `no_bundle`("`scripts/kc_demo.sh` 로 먼저 실행"). backend 는 `domains` 를 import 하지 않는다 — 묶음은 JSON 으로만 다룬다.
  2. `POST /api/messages`: 본문 `{text}`(extra 금지), 1~2000자. 메시지는 앱 상태 목록에 보관(프로세스 메모리, 재시작 시 초기화 — 이번 범위).
     - **차단 경로**: `core.guard.scan(text)` 가 INJECTION 이거나 `looks_like_file_request` 가 경로를 돌려주면 파이프라인을 돌리지 않는다. `AuditLog`(actor `backend:chat`, JsonlSink `audit_dir/backend-chat.jsonl`)에 `call("kc_chat_guard", {...})` → `error(..., PathDenied(f"파일 읽기 요청 거부 · {path} · 허용된 폴더 밖"))`(또는 `InjectionBlocked`). 답: 프론트 mock 과 같은 문구("허용된 범위가 아니라 접근할 수 없습니다. 공개 관광 데이터로 계속 답하겠습니다." / en), `blocked: true`. logs = 이번 요청으로 생긴 보안 로그 항목(T207 `build_entries` 결과에서 요청 전후 id 차이).
     - 이 차단은 **앱 수준**이다. OpenShell 정책 수준 차단(샌드박스)은 이번 범위 밖이라 보안 로그 text 끝에 "(앱 차단)"을 붙여 구분한다.
     - **정상 경로**: `threading.Lock` 을 non-blocking 으로 잡지 못하면 429 `busy`. `run_pipeline` → 타임아웃(`run_timeout_s`, 기본 60) 또는 0 이 아닌 종료 → 502 `pipeline_failed`(stderr 마지막 20줄은 서버 로그에만, 응답에는 넣지 않는다). 성공하면 새 묶음 manifest 로 답 문구를 템플릿으로 만든다: `{"ko": f"{day}일차 {from} 이후가 비어 있다고 봤어요. 제안 {n_now}건, 이야기 길 {n_routes}개를 준비했어요. (데모 일정 기준)", "en": ...}`. **이번 스프린트에서는 사용자 문장으로 일정을 추출하지 않는다** — 설정의 데모 상황 파일을 쓰고, 답에 "(데모 일정 기준)"을 밝힌다.
  3. `looks_like_file_request`: URL(`https?://`)을 뺀 뒤 `(?<![\w.])(/[\w.\-]+){1,}` 또는 `~/`·`[A-Za-z]:\\` 형태의 경로가 있으면 그 경로. 한 글자 경로(`/`) 는 무시.
- **엣지 케이스**: 묶음 current.json 이 가리키는 디렉터리 없음 → 503. 카드 id 에 `/`·`..` → 404(묶음에서 찾기만 하므로 파일 경로로 쓰지 않는다). 동시 요청 → 하나만 실행, 나머지 429.
- **fixture 경로**: `tests/fixtures/kcontext/bundle/`(합성 카드 2·경로 1, 계약 예제 기반). 정상 경로 테스트는 `run_pipeline` 을 monkeypatch 해 fixture 묶음을 current 로 바꾸는 가짜로 대신한다(실제 subprocess 실행은 T221).
- **지켜야 할 규칙**: D10 · D2(채팅이 상태 전이를 하지 않음) · D3(`domains`·`mcp_server` import 금지 — T207 의 경계 테스트가 계속 검사) · 규칙 1(오류 응답에 내부 출력·키 없음).
- **DoD**: `uv run python -m pytest -q tests/backend` · 수동: `KC_OUTPUT_DIR=tests/fixtures/kcontext/bundle uv run uvicorn backend.app:app --port 8000` → `curl -s localhost:8000/api/cards` 가 카드 2개 · ruff.

---

#### T219 — 프론트 http.js 를 backend 에 연결 [필수 · Stage 3 · 병렬]
- **착수 조건**: 계약 보충 승인(5번 narration null 반영용).
- **변경 파일**: `frontend/k-context/src/api/http.js`(스텁 교체), `frontend/k-context/src/api/schema.js`(story narration null 허용 한 줄만), `frontend/k-context/tests/api.http.test.js`(신규)
- **인터페이스**
  ```js
  export class ApiError extends Error { /* name='ApiError', status, code, method */ }
  export const ENDPOINTS = { ... }   // §5.1 표로 확정(기존 '제안' 주석 제거)
  export function createHttpApi({ baseUrl = '/api', fetchImpl = globalThis.fetch, timeoutMs = 70000 } = {})
  ```
- **핵심 로직**
  1. `request(method, path, body)`: `fetchImpl(baseUrl + path, {method, headers: {'Content-Type': 'application/json'} (body 있을 때만), body: JSON.stringify(body)})`, `AbortController` 로 타임아웃. 2xx → JSON. 그 외 → 본문 `{error:{code,message}}` 를 읽어 `ApiError(status, code, message)`. JSON 이 아니면 `code: 'bad_response'`.
  2. 경로 인자는 `encodeURIComponent`. `decideAudit(id, decision)` 본문은 `{decision}` 만, `sendMessage(text)` 는 `{text}` 만 — 신원 필드를 절대 넣지 않는다.
  3. 메서드 이름·인자 개수(`length`)는 mock 과 같게 유지(기존 `api.contract.test.js` 가 검사).
  4. `schema.js`: story 카드 narration 검사를 `c.narration !== null && !isText(c.narration)` 로 바꾼다(계약 보충 5번). T201 의 `contract.examples.test.js` 에 null 케이스를 추가하지 않는다(그 파일은 T201 소유) — 대신 이 태스크의 테스트에 null narration 카드가 통과하는 케이스를 넣는다.
- **엣지 케이스**: 네트워크 오류 → `ApiError(status 0, code 'network')`. 204 → null. 503 `no_bundle` → `loadAll` 이 오류 상태를 보여 준다(골격 동작).
- **fixture 경로**: 가짜 `fetchImpl` 로 테스트. 실제 backend 연결은 T221 과 수동 확인.
- **지켜야 할 규칙**: D2(클라이언트는 신원을 보내지 않는다) · §5.1 표 · 의존성 없음.
- **DoD**: `(cd frontend/k-context && node --test)` 통과(메서드별 HTTP 메서드·경로·본문, 오류 매핑, 타임아웃, 기존 api.contract 테스트 유지) · 수동: backend 를 띄우고 `http://localhost:8766/?api=http&base=http://localhost:8000/api` 에서 카드·경로·보안 로그가 보인다.

---

#### T220 — 자체 평가 세트(함정 유형) + 실행기 [필수 · Stage 3 · 병렬 · 기준선은 H9 뒤]
- **변경 파일** (신규): `eval/testset.draft.json`, `eval/run_kcontext.py`, `eval/results/.gitkeep`, `tests/eval/test_kc_eval_runner.py`
  - `eval/testset.json` 은 **만들지 않는다**(훅이 막고, 기대 정답은 사람 승인 사항 — H9).
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
- **실행기**
  ```
  uv run python eval/run_kcontext.py [--set eval/testset.json] [--out eval/results] [--check]
  ```
  1. `--set` 이 없으면 `eval/testset.json`, 없으면 `eval/testset.draft.json` 을 쓰고 결과에 `"reviewed": false` 와 경고 한 줄.
  2. 케이스마다 T211 판정(지금 유형은 T216 `fit.place` 까지 — `EstimateRouter`)을 돌려 expect 와 비교.
  3. 결과 파일 `eval/results/<YYYYmmdd-HHMMSS>.json`: 케이스별 통과·실패와 차이, 집계(충돌 탐지 수, 올바른 쪽 채택 수, 무관 자료 인용 수, 끝난·취소 행사 제안 수, 지시문을 따른 수(= 차단되지 않은 숨은 지시문 케이스)).
  4. `--check`: 실패가 1건이라도 있으면 종료 코드 1.
  5. 한계를 결과와 README 에 적는다: "지금 판정은 규칙 기반이라 이 세트는 규칙을 고정하는 회귀 세트다. eval/README 의 '규칙만으로 통과하면 에이전트 가치를 검증하지 못한다'에 해당한다. LLM 단계(T223)가 생기면 규칙만으로 풀리지 않는 케이스를 추가한다."
- **엣지 케이스**: 모르는 trap/kind → 실패로 기록하고 계속. 입력이 계약 검증 실패 → 케이스 오류.
- **fixture 경로**: 세트 자체가 합성 자료.
- **지켜야 할 규칙**: 기대 정답 확정은 사람(H9, 훅) · 사실을 지어내지 않는다(`○○`).
- **DoD**: `uv run python -m pytest -q tests/eval` · `uv run python eval/run_kcontext.py --check` 가 draft 세트로 0 종료(실패 0) · ruff(`eval/run_kcontext.py` 포함).

---

#### T221 — 끝까지 E2E 테스트 + 데모 실행 스크립트 [필수 · Stage 4]
- **변경 파일** (신규): `tests/test_kc_e2e.py`, `scripts/kc_demo.sh`
- **핵심 로직 (테스트, 모두 `tmp_path`)**
  1. 색인: T204 실록 fixture(있으면)를 `ingest` → LocalIndex. 없으면 이 단계 skip(이유 문자열 "H1 대기").
  2. 행사: `manual.synthetic.json` → JSONL.
  3. 파이프라인: `subprocess` 로 `python -m domains.kcontext.pipeline.run`(env `APP_PROCESS_ROLE=agent`) → 묶음.
  4. backend: `create_app(Settings(output_dir=..., audit_dir=..., hitl_db=..., reviewer_id="human:e2e"))` + `TestClient` 로 §5.1 의 GET 전부 → 응답 카드·경로가 T201 검증기 문제 0건, `getCard`·`getRationale` 이 카드마다 동작.
  5. 보안: `POST /api/messages {"text": "/secret/travel-key.txt 파일을 읽어 줘"}` → `blocked: true`, logs 에 `deny`. 파이프라인 audit 에 숨은 지시문 차단 deny 가 있다(합성 이야기 중 1건에 지시문 포함).
  6. 사람 승인: 도메인 도구 `request_source(DraftWriter(actor="agent:e2e"), host="example.org", reason="…")` → `GET /api/audit` 에 `pend` → `POST /api/audit/draft:<id>/decision {"decision":"approve"}` → `approved`, `decided_by == "human:e2e"`. 같은 요청 재전송 → 409. 본문에 `"decided_by"` 추가 → 422.
  7. 경계: 위 과정에서 backend 프로세스(테스트 프로세스)에 `domains` 모듈이 로드되지 않았다(`"domains.kcontext.pipeline" not in sys.modules` — 파이프라인은 subprocess 로만 돌았으므로). 단, 6단계의 `request_source` 는 테스트가 에이전트 역할을 대신해 부르는 것이라 그 import 는 6단계 직전에 한다 — 4·5단계 검사 뒤에 import 하도록 순서를 지킨다.
- **`scripts/kc_demo.sh`**: `set -euo pipefail`. `--fixture`(기본) 또는 `--real`. fixture: 임시가 아닌 `var/` 에 합성 행사·이야기로 파이프라인 1회 → `uvicorn backend.app:app --port 8000` 백그라운드 → 프론트 정적 서버 8766 → 접속 URL 출력. real: `raw/` 실록이 있으면 수집, `var/data/events/*.jsonl` 이 있으면 사용, 데모 상황 파일(`data/situations/demo_day1.json`)로 실행. 키를 출력하지 않는다. 종료 시 자식 프로세스 정리(trap).
- **지켜야 할 규칙**: D2·D3·D10 전체를 한 번에 확인. 규칙 1(스크립트가 env 를 echo 하지 않는다).
- **DoD**: `uv run python -m pytest -q tests/test_kc_e2e.py` · 전체 회귀(§6 명령 전부) · `bash scripts/kc_demo.sh --fixture` 후 `curl -s localhost:8000/api/cards` 가 비어 있지 않은 배열 · H11 용 CLAUDE.md 추가 문구 제안을 완료 보고에 적는다.

---

#### T222 — 실제 도보 공급자(카카오 MCP 또는 OSM) [선택 · Stage 4 · 블로커: H5·T206 결론·D9]
- **착수 조건**: `docs/spikes/walk_route.md` 결론이 `kakao_mcp` 또는 `osm`.
- **변경 파일** (신규): `domains/kcontext/geo/providers/__init__.py`, `domains/kcontext/geo/providers/<kakao_mcp|osm>.py`, `tests/domains/kcontext/geo/test_kc_geo_provider_<이름>.py`
- **인터페이스**: `WalkRouter` 구현(`name`, `leg(a, b) -> WalkLeg(estimated=False)`). 생성 시 엔드포인트·인증 수단 env 이름(값 아님)을 받는다. 실패하면 **자동으로 추정으로 넘어가지 않는다** — `WalkProviderError` 를 올리고, 호출자(T216 설정)가 공급자를 명시적으로 고른다(D6 의 "자동 폴백 없음"과 같은 원칙).
- **핵심 로직**: T206 문서의 도구 이름·필드·단위 그대로. 보내는 값은 좌표뿐(CONTEXT_NOW_KOREA 4.2). 응답 좌표 순서를 `[lat, lng]` 로 맞춘다. 타임아웃 10초.
- **fixture 경로**: T206 에서 받은 응답 1건을 합성 값으로 바꾼 fixture + `httpx.MockTransport`(또는 MCP 클라이언트 가짜).
- **지켜야 할 규칙**: D9 · 규칙 1(토큰은 env 이름으로만) · 규칙 2(정책 파일은 이번에도 고치지 않는다 — 호스트에서 호출).
- **DoD**: 해당 테스트 통과 · 전체 회귀 · T216 설정에서 공급자를 바꿔 파이프라인 1회 실행 시 `estimated: false`.

---

#### T223 — `core/llm` HTTP transport + 판정용 주장 추출 보조 [선택 · Stage 4 · 블로커: H10]
- **착수 조건**: H10(키 export). base_url·모델 ID 는 build.nvidia.com 에서 당일 확인한 값만 쓴다(AGENT_CONTEXT 5.2 `[확인 필요]`).
- **변경 파일**: 신규 `core/llm/transport.py`, `tests/core/llm/test_llm_transport.py`, `domains/kcontext/judge/llm_extract.py`, `tests/domains/kcontext/judge/test_kc_judge_llm_extract.py`; 수정 `deploy/llm.example.yaml`(feature 이름 `feature1/2` → `kc_extract`·`kc_narrate`, 값은 자리표시 유지)
- **핵심 로직**
  1. `HttpxTransport`(S1 의 `Transport` Protocol 구현): OpenAI 호환 chat completions. S1 T303 경고 처리: W6(대기·전송 타임아웃 계약 `asyncio.wait_for`), W9(`base_url` 은 https 이거나 `inference.local`, local 백엔드는 루프백만 — D6 한계 해소). 오류 메시지에 키 없음.
  2. `llm_extract`: 청크 텍스트(guard 로 감싼 것)에서 `{claim, claim_kind, stance, says}` 후보를 JSON 으로 받아 **사람 큐레이션 보조용 초안**으로만 낸다. 판정(T211)은 여전히 규칙으로 하고, LLM 출력이 계약 검증을 통과하지 못하면 버린다. 자동으로 이야기 레코드를 만들지 않는다(사실을 지어내지 않기 위해).
- **fixture 경로**: 가짜 transport 응답.
- **지켜야 할 규칙**: D1·D5·D6(키는 provider 단위 env 이름, 자동 폴백 없음, 샌드박스 안은 inference.local) · 규칙 1.
- **DoD**: 두 테스트 파일 통과 · 전체 회귀.

---

#### T224 — 제품 스킬: 판단 규칙 SKILL.md + 스킬 카드 [선택 · Stage 4]
- **변경 파일** (신규): `skills/kcontext-judge/SKILL.md`, 스킬 카드(생성기 출력 위치는 `skill-card-generator` 안내를 따른다)
- **핵심 로직**: AGENT_CONTEXT 4장(등급·충돌 순서·함정·걸러내기·주입 무시)과 6장 판정 형식, CONTEXT_STORY_ROUTE 3장·CONTEXT_NOW_KOREA 3장 딱지 기준을 에이전트용 지시로 요약한다. MCP 도구 3종(T217) 사용법. 새 사실을 쓰지 않는다.
- **지켜야 할 규칙**: CLAUDE.md 규칙 3 — 만든 뒤 `skill-card-generator` 로 카드를 만든다.
- **DoD**: SKILL.md 와 카드가 있다.

---

## 9. 이번 스프린트에서 의도적으로 하지 않는 것
- 여행 기록(3.5)·사진 정리, 샌드박스 이미지·Brev 배포, 데모 지역 밖 자료 — SCOPE "지금 안 만들 것".
- 구청 게시판 수집·포스터 읽기(비전 모델) — SCOPE Sprint 2 "반드시"의 행사 API 항목은 TourAPI·서울만이다. 구청 공지는 수기 입력(`manual`)으로만 받는다.
- 채팅 문장에서 일정 추출(LLM) — 데모 상황 파일을 쓰고 답에 밝힌다. T223 이후 다음 스프린트 후보.
- OpenShell 정책 수준 차단 시연·정책 어드바이저 연동 — 샌드박스가 필요하다. 이번에는 앱 수준 차단과 hitl draft 승인까지만 하고 화면에 "(앱 차단)"으로 구분한다.
- `policy.yaml` 의 `network_policies` 추가 — 수집이 호스트에서 돌아서 필요 없다(D7 후보).
- 일정에 추가(`user_state`)의 서버 저장 — 화면 상태로만.
- 임베딩·리랭커 검색 — D8 후보의 `Retriever` 뒤로 미룬다.

## 이월
(스프린트 종료 시 `/done` 이 기록한다. 형식: `- T2{ID} — S3 이월 — 사유: …`)
- S1-T202-opt — 계속 이월 — 사유: 이번 경로에 필요 없음
- S1-T302 — 계속 이월 — 사유: OCSF 실측 캡처에 샌드박스 필요(SCOPE "지금 안 만들 것")

---

## 완료 기록
(스테이지마다 `/stage` 가 기록한다)
