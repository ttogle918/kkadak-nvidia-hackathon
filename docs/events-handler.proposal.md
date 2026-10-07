# 행사 챗 핸들러 제안 — `domains/kcontext/chat/events.py`

상태: **제안**. 팀원과 필드를 맞추기 전에는 구현하지 않는다(chat-context-router.proposal.md 의 타입을 그대로 쓴다).

## 1. 입력 → 출력
- 입력: `ChatTurn {text, context, history}`, `Intent {name:"events", confidence, reason}`. `context` 는 `chat-context/v1`(신뢰하지 않는 입력).
- 출력: `HandlerResult {text, sources[], unverified, handler:"events", caveats[]}`.

## 2. context → 카탈로그 질의
| context | 쓰는 곳 |
|---|---|
| `date`·`day` | `trip.from/to` (그날 하루로 좁힘) |
| `location` | 거리 정렬용 기준점 (`mock: true` 면 답에 "예시 위치 기준"을 붙임) |
| `anchors[]` | `itinerary` 로 변환(`source:"user"`). `lat/lng` 가 null 이면 그 앞뒤 구간은 "이동시간 확인 필요" |
| `free_slots[]` | `fit` 의 빈 시간 한정 |
| `lang` | 언어 필터·답 언어 |
앵커 이름처럼 사용자에게서 온 문자열은 데이터로만 다루고 프롬프트에 지시로 넣지 않는다(`core.guard.wrap`).

## 3. 답을 만드는 방식
1. 질의는 `catalog.api` 의 `search` / `cards` 연산(자식 프로세스 JSON, D10)으로 한다. 핸들러가 `.env` 나 외부 사이트를 직접 읽지 않는다.
2. 답 본문은 카탈로그 레코드의 값만 쓴다. 모르는 값은 "확인 필요"로 쓴다(추측 금지). 행사 id·근거 링크·숫자는 `catalog.grounding` 으로 검증하고, 통과 못 한 문장은 버린다.
3. 결과가 0건이면 "찾은 행사가 없다 + 기준(기간·구)"만 말하고 지어내지 않는다.

## 4. sources[] / caveats[] 매핑 (팀원과 확인 필요)
| 행사 레코드 | `sources[]` 항목 | 화면 태그 |
|---|---|---|
| 등급 A/B(공식·보도) | `{name, locator, url, quote, tier}` | 이름 한 줄 |
| 등급 C(`fetched_from="web"`, 검색 수집) | 같은 모양 + `tier:"C"`, `unverified:true` | "검색 수집 · 미확인" |
| 충돌로 값이 비워진 필드 | `caveats[]`: "출처마다 달라 비워 둠: 가격" | 주의 문구 |
| 경로 추정값 | `caveats[]`: "예상 시간(경로 서비스 값 아님)" | 주의 문구 |
- `HandlerResult.unverified` 는 `sources[]` 중 하나라도 `unverified` 이면 true.
- `fetched_from="web"` 레코드는 **보조 후보**로만 쓴다: 확인된 행사가 있으면 먼저 말하고, web 레코드는 "미확인" 표시와 함께 뒤에 둔다. 예약·외국어·참여 조건 같은 판정에는 쓰지 않는다(D12·D13).

## 5. 분류 규칙 (키워드)
행사 쪽 키워드는 내 파일에 둔다: 행사·축제·공연·전시·페스티벌·"오늘/이번 주말 뭐 해"·"가까운" 등. 라우터가 호출하는 `classify` 는 팀원이 소유한다. 겹치는 질문("창덕궁 근처 축제 유래")은 `story` 우선인지 합의가 필요하다.

## 6. 팀원이 확인할 것
1. `sources[]` 필드 이름(`tier`, `unverified`, `quote`)과 화면 태그 문구.
2. `anchors[].lat/lng` null 허용(신촌 등).
3. 겹치는 질문의 우선순위, `history[-N:]` 의 N.
4. 핸들러 호출이 같은 프로세스인지 파이프라인 프로세스인지(라우터 제안의 A/B안).

## 7. 검증 계획 (구현 후)
단위: context→질의 변환, 0건·충돌·web 레코드 답, 주입 문자열이 지시로 안 먹히는지. 계약: `HandlerResult` 스키마. 미확인: 실제 챗 UI 연동.
