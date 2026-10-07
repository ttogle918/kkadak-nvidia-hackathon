# 제안 — 챗봇 맥락 전달과 의도 분류 라우터 인터페이스 (구현 전, 팀원과 맞추기용)

상태: **제안만**. 코드는 만들지 않았다. 번호·병합은 사람이 정한다(DECISIONS 에는 넣지 않음).
관련: `docs/chat-llm.decision-draft.md`(B1: D10 파이프라인 경로와 챗봇 직접 호출의 공존 — 아직 미결), D2·D3·D10.

## 1. 맥락(context) 전달

지금 `POST /api/messages` 는 본문이 정확히 `{text}` 하나일 때만 받는다(`backend/routers/messages.py`). 여기에 선택 필드 `context` 를 하나 더 허용하자고 제안한다.

```json
{
  "text": "여기서 가까운 행사 있어?",
  "context": {
    "schema": "chat-context/v1",
    "lang": "ko",
    "date": "2026-10-15",
    "day": 1,
    "location": { "lat": 37.5658, "lng": 126.9751, "label": "내 위치 (예시)", "mock": true },
    "anchors": [
      { "type": "visit", "name": "창덕궁", "lat": 37.5796, "lng": 126.9910, "from": "2026-10-15T10:00", "to": "2026-10-15T12:30" },
      { "type": "visit", "name": "익선동", "lat": 37.5734, "lng": 126.9898, "from": "2026-10-15T14:00", "to": "2026-10-15T17:00" }
    ],
    "free_slots": [{ "from": "2026-10-15T19:00", "to": "2026-10-15T23:00" }]
  }
}
```

- 출처는 프론트 store: `day`·`date`(trip.from + day-1), `ITINERARY.anchors` 중 그날 것, `free_slots`, 지도의 mock 내 위치(`kakao-view.js` `MY_LOCATION`). 실제 위치(`navigator.geolocation`)는 쓰지 않고 `mock: true` 를 항상 단다.
- **신원 필드는 없다**(D2). 요청자·승인자는 서버가 정한다.
- **context 는 신뢰하지 않는 입력이다.** 서버는 허용 키만 남기고(나머지는 422 `bad_text`), 문자열 길이·좌표 범위·anchors 개수(예: 20개)·날짜 형식을 검사한다. 앵커 이름처럼 사용자 일정에서 온 문자열은 프롬프트에 **데이터로** 넣는다(`core.guard.wrap`, 지시와 구분).
- 하위 호환: `context` 가 없으면 지금과 같이 동작한다. 기존 `{text}` 만 보내는 클라이언트와 테스트는 그대로 통과한다.
- 열린 점: 일정의 원천이 지금은 프론트 mock 이라 클라이언트가 보내는 값이 곧 일정이다. 서버에 일정이 생기면 context 는 `day` 와 위치만 남기고 앵커는 서버가 채운다.

## 2. 의도 분류 라우터

목표: 한 질문을 **행사/현재 한국**(팀원) · **이야기/실록**(나) · **일반 안내**(현재 챗봇) 중 어느 핸들러가 답할지 정한다.

```
ChatTurn   {text, context, history[-N:]}                      # 입력(서버가 만든 값만 신뢰)
Intent     {name: "story" | "events" | "general" | "blocked", confidence: 0..1, reason: str}
Handler    handle(turn: ChatTurn, intent: Intent) -> HandlerResult
HandlerResult {text, sources[], unverified: bool, handler: str, caveats[]}
```

- `classify(turn) -> Intent`: 규칙(키워드·날짜·"행사/축제/공연" → events, "옛날/실록/이야기/유래" → story)을 먼저 보고, 애매할 때만 LLM 한 번(분류 전용 feature, 출력은 enum 하나로 제한). 확신 낮거나 알 수 없으면 `general`(지금 동작). 분류 결과는 audit 에 `intent` 와 `confidence` 만 남기고 본문은 남기지 않는다.
- **핸들러는 이름으로 등록한다.** 새 기능은 레지스트리에 한 줄만 추가한다.
  - `events` → 팀원: 구청 행사·현재 한국(D12 수집 결과, `fetched_from`·`tier`·딱지 규칙을 그대로 따른다)
  - `story` → 나: 실록 색인 검색 → 근거 구절·출처가 붙은 답(`unverified=false` 는 근거가 있을 때만)
  - `general` → 지금의 `ChatService` 경로
- `HandlerResult.sources[]` 는 출처 카드 한 장에 필요한 값(이름·위치·URL·quote·등급)만 담는다. `unverified` 는 서버 고정 문구 대신 이 필드로 옮기자는 `chat-llm.decision-draft.md` 의 제안과 같다.
- 각 핸들러는 자기 영역 파일만 건드린다: `domains/kcontext/chat/events.py`(팀원), `domains/kcontext/chat/story.py`(나). 라우터·타입은 둘 다 건드리지 않는 곳에 둔다.

## 3. 결정이 필요한 것 (B1 과 같은 뿌리)

D3·D10 때문에 backend 는 `domains` 를 import 할 수 없다. 핸들러가 `domains/` 에 있으면 호출 경로가 둘 중 하나다.

| 안 | 내용 | 장점 | 단점 |
|---|---|---|---|
| A. 파이프라인 프로세스 | backend 가 `{text, context}` 를 파일로 넘겨 `python -m domains.kcontext.pipeline.run` 이 라우팅·핸들러 실행, 결과 묶음(`kc-bundle/v1`)만 읽음 (D10 그대로) | D2·D3·D10 변경 없음. 에이전트 코드가 backend 에 안 들어옴 | 프로세스 기동 지연(질문마다), 챗봇 직접 호출 경로(`general`)와 이중화 |
| B. 라우터는 `core/`, 핸들러는 등록식 | `core/chat/router.py` 에 Protocol·레지스트리만 두고 핸들러는 별도 프로세스(MCP 도구)로 호출 | 기동 지연 없음 | MCP 서버 호출 규약·인증이 필요, 이번 범위 밖 |

추천: **A 로 시작**하고 `general` 만 backend 직접 호출을 유지한다(B1 의 "임시 공존"으로 기록). 지연이 문제로 실측되면 B 를 결정으로 올린다. 이 선택은 B1 과 함께 사람이 정한다.

## 4. 팀원과 맞출 항목

1. `chat-context/v1` 필드(특히 `anchors` 에 `lat/lng` 가 없는 신촌 같은 경우는 null 허용인지).
2. `HandlerResult.sources[]` 필드와 `caveats[]` 를 행사 레코드 딱지("검색 수집 · 미확인")와 어떻게 매핑할지.
3. `events` 핸들러가 `fetched_from="web"` 레코드를 답에 쓰는 조건(D12 열린 질문: 사람 승인 전에는 근거로만).
4. 분류 규칙 키워드 목록의 소유(규칙 파일은 한 곳, PR 로 서로 추가).

## 5. 구현 순서(확인 뒤)

1) `context` 검증·전달(프론트 `sendMessage(text, context)` + backend 검증 + 테스트) → 2) Intent/Handler 타입과 레지스트리, `general` 만 등록 → 3) 팀원 `events`, 내 `story` 핸들러 등록. 1)·2) 는 핸들러 없이도 기존 동작이 그대로라서 먼저 합칠 수 있다.
