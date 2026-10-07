# 행사 `now` 카드 계약 제안 (행사·현재 한국 담당)

상태: **제안** — 합의 전에는 `schema.js`·AGENT_CONTEXT.md·`/api/cards` 를 바꾸지 않는다.
구현은 이미 있다: `POST /api/events/cards` (`domains/kcontext/catalog/cards.py`). 화면용 `GET /api/cards` 에 합치는 방법만 합의가 필요하다.

## 1. 지금 나오는 모양
`POST /api/events/cards` 본문은 `/api/events/search` 와 같다(여행 기간·언어·일정 `itinerary`·한도). 응답:
`{cards[], rationale, funnel, skipped, coverage, problems}`. 카드는 `kind: "now"`, `badge` ∈ 확인됨 / 확인 필요 / 보류,
`sources[]`(등급·인용·`unverified`), `slot`, `time_cost_min`, `why_fits[]`, `checks[]`, `caveats[]`, `valid`, `demo`.
합성 데이터로 만든 예는 `frontend/k-context/tests/fixtures/now_cards.json` 이고, `validateCard` 를 통과하는 것을 테스트가 확인한다.

## 2. 바꾸자고 제안하는 것 (결정 필요)
1. **`time_cost_min: number | null`.** 경로 서비스가 없으면 추가 이동시간을 모른다. 0 이나 추측값을 넣을 수 없어서 null 이 필요하다.
   카드 컴포넌트는 이미 null 이면 동선 수치를 숨긴다. `validateCard` 는 지금 숫자만 허용하므로 완화가 필요하다. 카드에는 `time_cost_unknown: true` 를 같이 보낸다.
   화면 문구 제안: "이동시간 확인 필요".
2. **`time_cost_estimated: boolean`** (신규, 선택). 직선 추정으로 얻은 값이면 true. 화면은 "동선 +7분 (예상 시간)"처럼 표시한다.
3. **출처 태그.** 이미 정한 대로 카드마다 작은 태그 하나. 검색 수집(등급 C·미확인)은 같은 태그에 등급을 넣는다(`sources[].tier`, `unverified`).
4. 위 두 필드를 `schema.js` 와 AGENT_CONTEXT.md 에 먼저 적고(문서 우선), 그다음 화면을 맞춘다.

## 3. `/api/cards` 와의 관계 (screen-api.proposal.md §3)
- 화면은 일정을 들고 있다가 요청에 실어 보낸다(결정됨). 행사 카드는 `itinerary` 를 받아 `fit` 으로 `slot`·`time_cost_min` 을 계산한다.
- backend 는 domains 를 import 하지 않는다(D3·D10). `/api/cards` 가 행사 카드를 합칠 때도 `catalog.api` 자식 프로세스의 JSON 을 그대로 병합한다. story 카드와 now 카드는 `kind` 로 구분하고 서로의 필드를 건드리지 않는다.
- 경로 파일은 담당별로 나눈다(`routes.story.json` = 팀원, `routes.walk.json` = 나). 합치는 규칙은 아직 미정 — 제안: 화면이 두 파일을 순서대로 읽어 그리고, 같은 `id` 는 만들지 않는다.

## 4. 팀원이 확인할 것
- `time_cost_min` null 허용이 story 카드 검증에 영향이 없는지(story 카드는 해당 필드를 안 쓰는 것으로 안다).
- 두 종류 카드를 한 목록에 섞을 때의 정렬 기준(제안: 서버는 정렬하지 않고 화면이 일정 순서로).
- `routes.*.json` 병합 방식.

## 5. 검증한 것 / 못한 것
- 검증: 합성 카드가 `validateCard` 를 통과(node 테스트), 충돌·미확인·검색 수집 카드의 배지·문구, 카드 생성 단위 테스트.
- 못함: 실제 카탈로그(서울 OpenAPI 키 없음)로 만든 카드 확인, 브라우저 화면 확인.
