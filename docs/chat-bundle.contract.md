# 챗봇 일정 흐름 계약 — `kc-chat-bundle/v1`·`v2` (구현용, v1 2026-10-07 · v2 2026-10-09)

상태: 구현 기준 문서. 배경: `docs/chat-context-router.proposal.md`, `docs/screen-api.proposal.md`, D2·D3·D10·D12·D13·D14·D15(보충 1·2 포함)·D16·D17·D18.
이름 메모: 스프린트 문서의 디렉터리형 `kc-bundle/v1`(T216b)과 겹치지 않게 이 단일 파일 묶음은 `kc-chat-bundle/v1`·`v2` 이다.
버전: v2 는 v1 필드를 모두 두고 필드를 더한 것이다(§ "v2 추가 필드"). backend 와 프론트는 **v1·v2 를 모두 받는다**. 생산자(파이프라인)가 v2 로 올리는 것은 받는 쪽(T313 backend · T314 프론트) 머지 뒤 마지막이다. 파이프라인은 v2 를 내보내고(`BUNDLE_SCHEMA = "kc-chat-bundle/v2"`), backend `story_runner` 의 허용 schema 는 v1·v2 다.

## 흐름
```
화면 --POST /api/messages {text, context?}--> backend
   backend: 일정 같은 메시지인가? (규칙 게이트)
      아니오 → 지금처럼 일반 챗봇(LLM)이 답한다 (bundle 없음)
      예     → 별도 프로세스 `python -m domains.kcontext.pipeline ...`(APP_PROCESS_ROLE=agent)
               → OUT/bundle.json (kc-chat-bundle/v2)
               → backend 가 같은 일정(anchors·free_slots)으로 행사 검색(catalog_runner, /api/events/search 와 같은 계산)
               → 앵커 0개: 이유에 따라 일반 챗봇 또는 고정 문구(아래 "일정 흐름 결과 표"), 앵커 ≥1 이면 reply + bundle 반환
화면 <-- {reply, logs, bundle?}
```
backend 는 `domains`·`mcp_server` 를 import 하지 않는다(D3·D10). 파이프라인과는 프로세스·파일로만 주고받는다. 신원 필드 없음(D2).

## 요청 (`POST /api/messages`)
- 기존: 본문이 정확히 `{"text": str(1~2000자)}` 일 때만 받는다.
- 추가: 선택 `context`. 허용 키만 받고 나머지는 422 `bad_text`.
```json
{"text": "...", "context": {"schema": "chat-context/v1", "lang": "ko",
  "trip": {"from": "2026-10-15", "to": "2026-10-18"}}}
```
`context` 는 신뢰하지 않는 입력이다: 날짜 형식·범위(from<=to, 최대 31일)·lang(ko|en) 검증. 없으면 파이프라인에 trip 을 넘기지 않고(연도 없는 날짜는 파이프라인이 problems 로 보고), 있으면 `--trip-from/--trip-to` 로 넘긴다. 일정은 화면이 들고 있다가 필요할 때 실어 보낸다(서버 보관 없음) — 이번 범위에서는 trip 만.

## 응답
기존과 같은 `{reply, logs}` 에 일정 흐름일 때만 `bundle` 이 붙는다. `reply.text` 는 `{ko, en}`(서버 고정 문구 + 숫자만 채움; LLM 이 쓴 문장 아님):
"일정 {n}개를 정리했어요. 실록에서 언급된 기록 {m}건, 주변 행사 {k}건을 찾았어요." (+ 가정·확인 필요가 있으면 한 줄) + 출처 없는 문장 금지.

`bundle` (모든 문자열은 신뢰할 수 없는 입력으로 취급 — 프론트는 textContent 로만 그린다):
```
{
 "schema": "kc-chat-bundle/v1", "generated_at": "...", "status": "ok" | "no_anchors",
 "trip": {"from","to"} | null,
 "itinerary": {"anchors": [{type: visit|hotel, name, day, from, to, lat, lng, source_quote}],
               "free_slots": [{day, from, to, near, inferred, assumption:{ko,en}}]},
 "mentions": kc-mention/v1  // anchors[].mentions[]: {article_id, king, date_label, title_summary, quote(한문 원문), lang:"orig", locator, url, tier, source{...}}; 행마다 excluded_count(int, 주입 검사로 뺀 수 — 근거 pick 칩의 값); 언급마다 `card_id`(문자열, 카드를 만든 언급에만) = 그 언급의 `cards[].card.id`(같은 기사가 두 앵커에 걸리면 `story_A`, `story_A_2`). 근거 키 = `"mention:" + card_id`. 프론트는 이 필드가 정확히 일치할 때만 찾는다(id 를 추정하지 않는다)
 "events": /api/events/search 응답 {events, excluded, problems, coverage} | null. 단 묶음에서는 `excluded` 를 앞 20건 표본으로 줄이고 `excluded_total`(int, 원본 전체 개수)·`excluded_by_reason`({사유: 개수}, 상위 20개 사유)를 더한다. 근거 수치(funnel)는 줄이기 전 원본으로 센다. 줄였으면 problems 에 내부용 `EXCLUDED_SUMMARIZED`(화면에서 숨김 — 행사 자체는 다 보이므로 "일부만 보여요"가 아니다). 공개 `/api/events/search` 응답은 그대로 둔다 (검색 불가 시 null + problems 에 EVENTS_UNAVAILABLE)
 "cards": [{card, card_ready, missing}],   // card_ready=false 인 것은 화면이 '언급 기록' 간이 카드로 그린다
 "problems": [{code, message}], "coverage_note": "..."
}
```
- 좌표(lat/lng)는 검증된 장소 사전(`domains/kcontext/data/places/demo_places.json`)에 있는 장소만. 없으면 null → 지도 핀 없음, 목록에만.
- 크기 상한: bundle.json 1MB, mentions 앵커당 최대 5건, 앵커 최대 20개. 상한 초과는 잘라서 problems 에 `TRUNCATED`.
- 오류: 파이프라인 실패·시간 초과(backend 한도 90초)·잘못된 bundle → **고정 문구**(`SCHEDULE_UNAVAILABLE_REPLY`)로 답한다. 일반 챗봇으로 덮지 않는다(D15 ⑤). 내부 출력은 노출하지 않고 로그에는 종류만 남긴다.
- 동시 실행은 1건(기존 `ChatBusy` 429 재사용).

## v2 추가 필드 (`schema: "kc-chat-bundle/v2"`, sprint-3 §5.2)
v1 필드를 모두 두고 아래를 더한다.
```
schema: "kc-chat-bundle/v2"
schedule: {"source": "llm" | "cache" | "rules"(T326 시에만), "attempts": int, "model": str | null,
           "prompt_sha": str, "cache_created_at": "YYYY-MM-DDTHH:MM:SSZ" | null}
           # T309 가 v1 에 가산 필드로 먼저 넣는다(프론트 v1 검증기는 무시). T312 가 schema 를 v2 로 올린다
routes: [{"id": "day1", "day": int | null, "date": "YYYY-MM-DD",
          "legs": [{"from": str, "to": str, "from_ll": [lat, lng], "to_ll": [lat, lng],
                    "straight_m": int, "walk_min": int | null, "provider": str, "estimated": bool}],
          "skipped": [{"from": str, "to": str(빈 문자열일 수 있음 — "시각 없음"은 이동 상대가 없다), "reason": "좌표 없음" | "시각 없음"}]}]
rationale: {"mention:<story card id>": Rationale}       # T312
events_rationale: {"event:<event id>": Rationale}       # T313. 생산자가 보내도 backend 가 항상 지우고 다시 만든다
story_routes_note: {"ko": "이야기 길 없음 — 근거 좌표가 있는 이야기가 없어요", "en": "No story route — no stories with grounded coordinates"}
```
- **id 공간**: 근거 맵의 키는 접두어 + 원래 id 다. 실록 언급 카드는 `mention:` + `cards[].card.id`(예 `mention:story_<article_id>`), 행사는 `event:` + `events.events[].id`. 각 값의 `card_id` 필드에도 접두어가 붙은 같은 키를 넣는다. 프론트는 선택한 항목 종류에 따라 접두어를 붙여 찾는다. 두 맵에 같은 키가 생길 수 없다.
- `Rationale` = 프론트 기존 형식 `{"card_id", "chips": [{"key", "tone": "old"|"now", "label": {ko,en}}], "items": {"<key>": {"title": {ko,en}, "text": {ko,en}, "rows": [{"k": {ko,en}, "v": {ko,en}}]}}}`.
- 상한(backend `clean_bundle`): routes 7 × legs 20 · 한 날 skipped `MAX_SKIPPED` 20, 근거 100개, chips 8, 근거당 items `MAX_ITEMS` 20, rows 12, 문자열은 v1 상한. 넘으면 자르고 `TRUNCATED`. 모양이 틀린 v2 필드는 그 필드만 버리고 `FIELD_DROPPED`(`straight_m`·`walk_min` 이 음수여도 `routes` 를 버린다).
- 직선 거리로 추정한 도보 시간은 표시에만 쓰고 판정에는 쓰지 않는다(D16). 화면 데이터의 단일 출처는 이 묶음이다(D17). 경로 A·B·C 는 근거 좌표가 있는 이야기가 있을 때만 만들고, 없으면 `story_routes_note` 를 보인다(D18).
- 경로 엔진(`KC_OSM_ROUTER_URL`): 에이전트(파이프라인) 프로세스는 호스트가 루프백(`localhost`·`127.0.0.1`·`::1`)일 때만 쓴다(D7·D20 ⑥ — 외부 자료는 호스트 수집기만). 원격 주소면 경로 공급자를 쓰지 않고(`walk_min: null`) problems 에 `ROUTE_PROVIDER_REMOTE_REFUSED`(이름만, URL 값 없음)를 남긴다. 파이프라인 안 경로 계산 시간은 R−B 여유 15초 중 10초가 상한이고 LLM 예산을 넘겨 쓴 만큼 줄어든다. 호스트 수집기(catalog)의 동작은 그대로다.
- 모든 문자열은 신뢰하지 않는 입력(textContent 로만).

## 시간 예산 (D15 ②, sprint-3 §6.4 — 프론트 상한에서 거꾸로)
| 이름 | 값 | 위치 |
|---|---|---|
| `F` 프론트 요청 상한 | 100초 | `http.js` `REQUEST_TIMEOUT_MS = 100_000` |
| `R` backend 파이프라인 한도 | 90초 (= F − 10, backend 가 프론트보다 먼저 끝나 고정 문구를 돌려줄 여유) | `backend/story_runner.py` `TIMEOUT_S` |
| `B` 파이프라인 안 LLM 예산 | 75초 (= R − 15) | `story_runner.LLM_BUDGET_S` → 자식에 `--llm-budget-s` |
| `T_llm` LLM 1회 한도 | 40초 (기준선 p95 26.5초 × 1.5, `eval/BASELINE.md`) | `deploy/llm.chat.yaml` provider `timeout_s`(일반 챗봇에도 적용) |
| 재시도 허용 | 남은 LLM 예산이 `T_llm` 이상일 때만, 곧 첫 시도 경과 ≤ 35초 | 파이프라인 `understand_with_meta` |
| 행사 검색 한도 | min(60, 100 − 5 − 파이프라인 경과)초, 3초 미만이면 검색을 건너뜀 | `backend/chat_story.py` `search_budget_s` |
| 일반 챗봇 진입 | 파이프라인 경과 + `T_llm` ≤ F − 5, 곧 경과 ≤ 55초 | `backend/chat.py` `FRONT_LIMIT_S`·`FALLBACK_MARGIN_S` |

재시도: 대상은 LLM 실패(빈 응답·JSON 아님·형식 틀림 포함)와 `QUOTE_NOT_FOUND` 가 있는 부분 결과이고(D15 보충 2), 같은 백엔드로 예산 안에서만, 첫 시도를 포함해 **총 2회까지**다. 2회차 부분 결과는 검증된 앵커가 엄격히 더 많을 때만 쓴다(같거나 2회차가 LLM 실패면 1회차) — `domains/kcontext/schedule/understand.py` `understand_with_meta`.

## 일정 결과 캐시 (D15 ④, 보충 2)
- 캐시는 v2 형식으로 `var/cache/schedule/` 에 둔다(`KC_VAR_DIR`·`KC_SCHEDULE_CACHE` 로 조정, 평가는 끔). 키는 정규화한 입력 글·여행 기간·프롬프트 해시·LLM 설정 파일 해시·모델 덮어쓰기 env.
- `QUOTE_NOT_FOUND` 가 있는 결과, 실패 결과, 앵커 0개 결과는 **저장하지 않고 읽지도 않는다.**
- 적중하면 `schedule.source: "cache"`, `schedule.cache_created_at` 에 원래 생성 시각이 들어가고, backend 가 정리 문구 끝에 서버 고정 문구 "이전 결과 재사용."(en: "Reused a previous result.")을 붙인다. LLM 은 부르지 않는다.

## 일정 흐름 결과 표 (sprint-3 §6.5)
파이프라인 종료 코드 2 는 실행 조건 미충족(파일·색인 없음, `--require-llm` + 키 없음)뿐이다.

| # | 캐시 | LLM 결과(재시도 포함) | `schedule.source` | 앵커 | 파이프라인 종료 | backend 동작 → 사용자 응답 | 캐시 쓰기 |
|---|---|---|---|---|---|---|---|
| 1 | 적중 | (부르지 않음) | `cache` | ≥1 | 0 | 묶음 + 정리 문구 + "이전 결과 재사용." | 없음 |
| 2 | 미적중 | 정상, 앵커 ≥1 | `llm` | ≥1 | 0 | 묶음 + 정리 문구 | 씀(`QUOTE_NOT_FOUND` 없을 때만) |
| 3 | 미적중 | 정상, 앵커 0(일정 아님, `LLM_*` 문제 없음) | `llm` | 0 | 0 | 예산이 있으면 일반 챗봇 답, 없으면 고정 문구 `NO_SCHEDULE_REPLY` | 안 씀 |
| 4 | 미적중 | 실패(`LLM_FAILED·LLM_EMPTY·LLM_BAD_JSON·LLM_UNEXPECTED_SHAPE`, 재시도 후 또는 예산 부족으로 재시도 없음) | `llm` | 0 | 0 | **고정 문구 `SCHEDULE_UNAVAILABLE_REPLY`**(일반 챗봇으로 덮지 않음) | 안 씀 |
| 5 | 미적중 | 키 없음(`LLM_UNAVAILABLE`) | `llm`(attempts 0) | 0 | 0 | #4 와 같음 | 안 씀 |
| 6 | — | 파이프라인이 `R` 을 넘김·비정상 종료·묶음 없음/잘못됨 | (묶음 없음) | — | timeout/≠0 | #4 와 같은 고정 문구, audit 에 종류 | 안 씀 |
| 7 | — | 입력 주입 차단(`INJECTION_BLOCKED`) | `llm`(attempts 0) | 0 | 0 | #3 과 같음(LLM 실패가 아님) | 안 씀 |
| 8 | — | 색인 없음 | (실행 안 함) | — | — | 일반 챗봇(설치 문제 — README 안내), audit `index_missing` | — |
| (T326 시) | 미적중 | #4·#5 + 규칙 추출 앵커 ≥1 | `rules` | ≥1 | 0 | 묶음 + "규칙으로 정리(장소 사전 이름만)" | 안 씀 |

고정 문구(`backend/chat.py`, LLM 이 쓴 문장이 아니며 LLM 맥락에도 넣지 않는다):
- `SCHEDULE_UNAVAILABLE_REPLY` — ko "일정을 지금 정리하지 못했어요. 잠시 뒤 다시 보내 주세요." / en "I couldn't organize your schedule right now. Please try again shortly."
- `NO_SCHEDULE_REPLY` — ko "일정으로 정리할 항목을 찾지 못했어요." / en "I couldn't find schedule items to organize."

## 화면 표시 규칙(결정 사항)
- 출처는 아주 작은 태그. `tier` 글자 + 이름 한 줄. `tier C`(검색 수집·미확인) 행사도 같은 태그에 등급을 보인다("검색 수집 · 미확인").
- 실록 언급은 "실록에 이런 기록이 있어요" — 이야기라고 쓰지 않는다. 한문 원문 구절과 "한글 요약(원문 아님)"을 구분해 보이고, 누르면 실록 원문 링크(`url`, http/https 만)로 간다. 국역 없음 표시.
- 지도: 좌표 있는 앵커에 핀, 누르면 정보창(textContent). 옛길 선은 이번 범위 밖.
- 행사가 비어 있으면 "주변 행사를 아직 찾지 못했어요(데이터 준비 중)" 처럼 사실대로 보인다. 지어내지 않는다.

## 구현 메모 (backend, 2026-10-07)
- 파일: `backend/schedule_gate.py`(게이트) · `backend/story_runner.py`(별도 프로세스 실행) · `backend/chat_story.py`(context 검증·bundle 정리·행사 검색 요청·고정 문구) · `backend/chat.py`(흐름 연결·고정 문구·예산 판정) · `backend/routers/messages.py`.
- 게이트: **시각·날짜 표현 하나 + (일정 어휘 또는 장소 이름) 하나 이상**일 때만 일정 흐름. 장소 이름은 `backend/fixtures/chat_places.json`(demo_places.json 의 사본; 사전이 바뀌면 같이 갱신). 한계: "10/15 경복궁은 어때?" 같은 질문은 오탐(비용은 파이프라인 1회, 앵커 0개이고 LLM 이 정상이면 남은 예산이 있을 때 일반 챗봇, 없으면 `NO_SCHEDULE_REPLY`). 날짜·시각이 없는 일정 글("경복궁 갔다가 익선동 갈 거야")은 미탐 — 일반 챗봇이 답한다.
- 환경변수: `KC_INDEX_DB`(기본 `var/index/kcontext.db`, 없으면 일반 챗봇으로 폴백하고 audit 에 `index_missing`). 자식에게는 `backend/story_runner.py` 의 허용 목록(`_ENV_ALLOW`) 참조 + `LLM_BACKEND` 로 시작하는 변수 + `APP_PROCESS_ROLE=agent` 만 넘긴다(`.env` 는 자식이 core.llm 허용 목록 로더로 직접 읽음).
- 실행: 임시 디렉터리에 text.txt 를 쓰고 `python -m domains.kcontext.pipeline --text-file --db --out [--trip-from --trip-to]`. 타임아웃 90초(`TIMEOUT_S`), 자식에 `--llm-budget-s 75` 를 넘긴다. bundle.json 1MB 상한, schema 가 허용 목록(v1·v2)에 없으면 거부, 끝나면 임시 디렉터리 삭제. 실패는 종류(timeout/exit/no_output/too_large/bad_json/bad_schema)만 audit 에 남기고 **고정 문구 `SCHEDULE_UNAVAILABLE_REPLY` 로 답한다**(일반 챗봇으로 폴백하지 않음, 자식 출력은 노출·기록하지 않음).
- `context` 가 없으면 `--trip-*` 을 넘기지 않는다(파이프라인 CLI 의 trip 인자를 선택으로 바꿨다). 이때 연도 없는 날짜는 파이프라인이 problems 로 보고하고 앵커 날짜가 비므로 행사 검색 기간을 정할 수 없어 `events: null` + `EVENTS_UNAVAILABLE` 이 될 수 있다. 이 설명은 D22 로 바뀌었다 — 아래 "행사 검색 범위·연도 추정(D22)" 참고.
- 행사 검색: 방문(visit) 앵커 중 날짜·시작 시각이 있는 것만 Plan 으로(끝 시각이 없으면 시작+60분 가정, `end_assumed: true`). 숙소는 Plan 에서 뺀다. free_slots 는 `{date, from, to}` 로 변환(자정을 넘기면 23:59 까지). 카탈로그가 비어 0건이어도 정상(`events.events == []`).
- 상한: 앵커 20 · 앵커당 언급 5 · 카드 100 · problems 100, 넘으면 잘라서 `TRUNCATED`. 동시 실행은 일정 흐름 1건(`ChatBusy` 429). backend 프로세스는 LLM 을 직접 부르지 않는다(일반 챗봇 답 제외).
- 일정 흐름 대화는 다음 턴 LLM 맥락에 넣지 않는다(고정 문구·bundle 은 맥락 아님). bundle 은 서버에 보관하지 않는다.

## 행사 검색 범위·연도 추정 (D22)
- **연도 추정**: trip 이 없고 연도도 없는 날짜는 오늘(KST, 오늘 포함) 이후 가장 가까운 그 월·일로 정하고 problems 에 `YEAR_ASSUMED`(메시지에 정한 날짜, "확인 필요")를 남긴다. 2/29 처럼 그 해에 없는 날은 다음에 존재하는 해. trip 이 있거나 연도를 쓴 날짜는 그대로. (`YEAR_UNKNOWN` 은 오늘 기준이 주어지지 않은 순수 함수 호출에서만 난다.)
- **행사 검색 범위 우선순위**(backend `attach_events`, 날짜는 묶음 JSON 에서만 읽는다): ① 모든 앵커 from·to 날짜의 최소~최대(31일 이내) — 문장에 날짜가 있으면 trip 이 있어도 언제나 이것 → ② 요청의 `context.trip` → ③ 오늘(KST)부터 7일. 쓴 기준을 `coverage_note` 끝에 고정 문구로 덧붙인다: ① "일정 날짜 범위로 찾았어요." ② "여행 기간으로 찾았어요." ③ "날짜를 몰라 오늘부터 7일 안에서 찾았어요." (시간이 모자라 건너뛴 경우는 기준 문구 없이 기존 "시간이 모자라 행사 검색을 건너뜀." 만.) 범위를 정할 수 없는 경우(오늘 기준 없음)에만 `EVENTS_UNAVAILABLE` "여행 기간과 일정 날짜를 몰라 행사를 찾지 않았어요".
