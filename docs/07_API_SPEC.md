# 07. API 명세 `[제안]`

> 화면과 백엔드 사이의 약속이다. 카드와 경로의 형식은 `AGENT_CONTEXT.md` 3.3의 공통 계약을 그대로 쓴다.
> 기본 경로는 `/api`. 응답은 JSON. 시각은 ISO 8601, 좌표는 `[위도, 경도]`.
>
> ⚠ 미해결 충돌: D10 와 어긋남(세션·SSE 중심 구조 전체) — 사람 결정 대기. 화면용 엔드포인트의 현재 기준은 `sprints/sprint-2.md` §5.1 이다. 승인 API 는 아래 §10.1 이 기준이고 이 문서의 나머지와 충돌하면 §10.1 을 따른다.

## 1. 한눈에 보기

| 메서드 | 경로 | 하는 일 |
|---|---|---|
| POST | `/api/sessions` | 세션을 만든다 |
| DELETE | `/api/sessions/{sid}` | 세션과 기록을 지운다 |
| POST | `/api/sessions/{sid}/messages` | 메시지를 보낸다. 응답은 이벤트 스트림 |
| GET | `/api/sessions/{sid}/trip` | 여행 상태(고정 일정, 빈 시간) |
| PATCH | `/api/sessions/{sid}/trip` | 설정 변경(변경 최소화, 관심사 등) |
| GET | `/api/sessions/{sid}/timeline` | 날짜별 타임라인 |
| GET | `/api/sessions/{sid}/routes?request_id=` | 경로 A·B·C |
| POST | `/api/sessions/{sid}/routes/{rid}/choose` | 경로를 고른다 |
| GET | `/api/sessions/{sid}/cards/{cid}` | 카드 하나 |
| PATCH | `/api/sessions/{sid}/cards/{cid}` | 카드 상태 변경(추가, 건너뜀, 다녀옴) |
| GET | `/api/sessions/{sid}/cards/{cid}/sources` | 출처 태그 상세 |
| GET | `/api/sessions/{sid}/decisions?request_id=` | 판단 근거 |
| GET | `/api/sessions/{sid}/map?day=&layer=` | 지도에 그릴 것 |
| GET | `/api/sessions/{sid}/record` | 여행 기록 |
| GET | `/api/security/events` | 보안 로그. 이벤트 스트림 |
| GET | `/api/health` | 상태 확인 |

로그인은 없다. 세션 ID가 열쇠다. 추측하기 어려운 긴 임의 값으로 만든다.

## 2. 세션

**POST `/api/sessions`**

```json
{"lang": "ko"}
```

```json
{"session_id": "s_8f2c…", "expires_at": "2026-10-08T09:00:00Z"}
```

**DELETE `/api/sessions/{sid}`** — 여행, 대화, 카드, 판단 기록을 모두 지운다. `204`.

## 3. 대화

**POST `/api/sessions/{sid}/messages`**

```json
{"text": "첫날 저녁에 뭐하지?"}
```

응답은 서버 전송 이벤트(`text/event-stream`)다. 단계가 끝날 때마다 이벤트가 온다.

| 이벤트 | 데이터 | 언제 |
|---|---|---|
| `stage` | `{"name": "understand", "status": "start"}` | 단계 시작·끝. 진행 표시에 쓴다 |
| `assumption` | `{"text": "1일차 저녁 7시 이후가 비어 있다고 봤어요"}` | 에이전트가 가정을 밝힐 때 |
| `trip` | 여행 상태 전체 | 일정이 바뀌었을 때 |
| `question` | `{"text": "숙소 이름을 알려 주세요"}` | 되물을 때 |
| `routes` | `{"request_id": "…", "routes": [경로…]}` | 경로 A·B·C가 준비됐을 때 |
| `cards` | `{"request_id": "…", "cards": [카드…]}` | 카드가 준비됐을 때 |
| `decisions` | `{"request_id": "…", "summary": {…}}` | 판단 근거 요약 |
| `message` | `{"text": "…"}` | 에이전트의 말 |
| `security` | 보안 이벤트 | 이 요청 중에 거부·허용이 있었을 때 |
| `error` | `{"code": "…", "text": "…"}` | 실패 |
| `done` | `{}` | 끝 |

`stage.name` 값: `understand`(일정 이해) / `collect`(후보 수집) / `judge`(신뢰도 판단) / `fit`(일정에 맞추기 또는 경로 구성) / `explain`(맥락 설명).

## 4. 여행과 타임라인

**GET `/api/sessions/{sid}/trip`** — 공통 계약의 입력 형식 그대로.

**PATCH `/api/sessions/{sid}/trip`**

```json
{"minimize_changes": false, "interests": ["한국 음식", "시장"]}
```

고정 일정(`anchors`)은 이 경로로 바꾸지 않는다. 사용자가 대화로 말했을 때만 바뀐다.

**GET `/api/sessions/{sid}/timeline`**

```json
{
  "days": [
    {
      "day": 1,
      "date": "2026-10-15",
      "items": [
        {"type": "anchor", "anchor_id": "a_1", "name": "창덕궁", "from": "14:00", "to": "16:30"},
        {"type": "free", "slot_id": "f_1", "from": "19:00", "to": "23:00", "inferred": true},
        {"type": "card", "card_id": "card_017", "state": "proposed", "at": "19:30", "title": "…"}
      ]
    }
  ]
}
```

`items[].type`: `anchor`(원래 일정) / `free`(빈 시간) / `card`(제안 또는 추가한 것, `state`로 구분).

## 5. 경로

**GET `/api/sessions/{sid}/routes?request_id=…`**

```json
{
  "request_id": "r_31",
  "from": {"name": "익선동", "lat": 0, "lng": 0},
  "to": {"name": "덕수궁", "lat": 0, "lng": 0},
  "routes": [
    {
      "id": "A", "route_id": "rt_101", "theme": "왕의 길",
      "walk_min": 18, "delta_min": 4, "distance_m": 1250, "estimated": false,
      "story_count": 3, "badge_mix": {"기록": 2, "전승": 1},
      "badges": ["추천"], "recommend_reason": "…",
      "geometry": [[0, 0], [0, 0]],
      "segments": [
        {"seq": 1, "name": "왕이 지나던 길", "card_id": "card_004",
         "length_m": 240, "walk_min": 4, "weak": false, "geometry": [[0, 0], [0, 0]]}
      ]
    }
  ]
}
```

- `estimated: true`면 경로 엔진 대신 어림한 값이다. 화면에 "예상 시간"으로 표시한다.
- 이야기가 없는 구간은 `name`이 `null`이다. 흐리게 그린다.

**POST `/api/sessions/{sid}/routes/{route_id}/choose`** — `204`. 걸었다고 표시할 때는 `{"walked": true}`.

## 6. 카드

**GET `/api/sessions/{sid}/cards/{cid}`** — 공통 계약의 카드 형식 그대로.

**PATCH `/api/sessions/{sid}/cards/{cid}`**

```json
{"user_state": "added"}
```

허용되는 전이는 `02_USER_FLOW.md` 8.1을 따른다. 그 밖의 전이는 `409`. 이 경로는 **사람이 쓰는 사용자 API** 이고 에이전트 도구는 호출하지 않는다(D2).

**GET `/api/sessions/{sid}/cards/{cid}/sources`**

```json
{
  "sources": [
    {
      "id": "doc_03", "tier": "A", "name": "서울지명사전",
      "tag": "[A] 서울지명사전 · p.214",
      "locator": "p.214", "url": "…",
      "published": "2009", "collected_at": "2026-10-06",
      "quote": "근거가 된 원문 구절",
      "supports": ["본문 1번째 문장", "본문 3번째 문장"]
    }
  ]
}
```

`tag`는 화면에 그대로 찍는 문자열이다. 서버가 만든다.

## 7. 판단 근거

**GET `/api/sessions/{sid}/decisions?request_id=…`**

```json
{
  "request_id": "r_42",
  "summary": {
    "total": 12, "accepted": 2,
    "rejected": {"expired": 5, "too_far": 2, "interest_mismatch": 2, "duplicate": 1}
  },
  "items": [
    {"candidate": "○○ 야장", "outcome": "accepted", "card_id": "card_017"},
    {"candidate": "△△ 팝업", "outcome": "rejected", "reason_code": "expired",
     "reason": "10월 9일에 끝났습니다"},
    {"candidate": "□□ 행사", "outcome": "accepted", "reason_code": "conflict_resolved",
     "reason": "포스터는 18시, 변경 공지는 17시. 더 최근의 공식 공지를 따랐습니다",
     "conflict": {
       "a": {"says": "18시", "source_tag": "[B] 포스터에서 읽음 · 중구청 게시물 첨부"},
       "b": {"says": "17시", "source_tag": "[B] 중구청 공지 · 2026-10-09 게시"},
       "chosen": "b"
     }}
  ]
}
```

`reason_code`: `expired` / `too_far` / `interest_mismatch` / `duplicate` / `unsuitable` / `no_evidence` / `irrelevant` / `on_hold` / `conflict_resolved`.

## 8. 지도

**GET `/api/sessions/{sid}/map?day=1&layer=both`** — `layer`: `past` / `now` / `both`.

```json
{
  "anchors": [{"anchor_id": "a_1", "type": "hotel", "name": "…", "lat": 0, "lng": 0}],
  "day_path": [[0, 0], [0, 0]],
  "features": [
    {"card_id": "card_004", "kind": "story", "geometry": {"type": "segment", "coords": [[0, 0], [0, 0]]},
     "label": "왕이 지나던 길", "badge": "기록", "weak": false, "highlight": true},
    {"card_id": "card_017", "kind": "now", "category": "야장",
     "geometry": {"type": "area", "coords": [[0, 0], [0, 0], [0, 0]]},
     "label": "○○ 야장", "badge": "확인됨", "when": "19시 시작", "highlight": true},
    {"card_id": "card_018", "kind": "now", "category": "축제",
     "geometry": {"type": "approx", "coords": [[0, 0]], "radius_m": 150},
     "label": "□□ 축제", "badge": "확인 필요", "note": "정확한 위치는 현장 확인", "highlight": false}
  ],
  "detour": {"card_id": "card_017", "geometry": [[0, 0], [0, 0]], "extra_min": 12}
}
```

- `geometry.type`에 따라 핀, 선, 영역, 흐린 원으로 그린다.
- `highlight: false`인 것은 흐리게 두거나 숨긴다.
- `detour`는 카드를 눌렀을 때 그리는 "들렀다 가는 길"이다.
- 끝난 행사와 여행 기간 밖의 행사는 응답에 넣지 않는다.

## 9. 여행 기록

> `[제안]` **이번 범위 밖.** 마지막에 별도 agent 하나로 붙인다. 아래는 그때를 위한 초안이다.

**GET `/api/sessions/{sid}/record`**

```json
{
  "summary": {"walked_m": 5400, "stories": 7, "places": 4},
  "days": [
    {
      "day": 1, "date": "2026-10-15",
      "route": {"route_id": "rt_101", "theme": "왕의 길", "geometry": [[0, 0], [0, 0]],
                "segments": [{"name": "왕이 지나던 길", "badge": "기록"}]},
      "visited": [{"card_id": "card_004", "kind": "story", "title": "…", "badge": "기록", "tags": ["[S] …"]},
                  {"card_id": "card_017", "kind": "now", "title": "…", "badge": "확인됨",
                   "as_of": "2026-10-15", "tags": ["[B] …"]}],
      "not_visited": [{"card_id": "card_018", "title": "…"}]
    }
  ]
}
```

`visited`에는 사용자 상태가 `visited`이거나 `added`인 것만 넣는다. `proposed`와 `skipped`는 `not_visited`.

## 10. 보안 로그

**GET `/api/security/events`** — 이벤트 스트림.

```json
{"ts": "2026-10-15T18:21:07Z", "action": "deny", "target_kind": "network",
 "target": "blog.example.com", "reason": "허용 목록에 없음", "origin": "openshell"}
```

`action`: `allow` / `deny` / `pending` / `approved` / `rejected`. `target_kind`: `network` / `file` / `tool`.

OpenShell 정책 어드바이저의 `openshell rule approve` 는 **운영자 터미널 전용**이며 앱 API 와 별개다. 화면 버튼이나 중계 스크립트가 이 명령을 실행하지 않는다. 앱 안의 승인·거부는 아래 승인 API 로만 한다.

### 10.1 승인 API (사람 전용, backend 의 review 라우터)

기준: `sprints/sprint-2.md` §5.1, `backend/routers/review.py`. 상태 전이(승인·반려)는 이 라우터에만 있다(D2).

> **승인 API 는 에이전트 프로세스가 닿는 곳에 두지 않고, 인증 계층 없이 공개하지 않는다(`backend/routers/review.py` 머리 주석: '인증이 없는 로컬 데모용 … 공개 배포 전에는 인증 계층이 필요하다'). 승인자는 기본 `human:demo` 이고(`KC_REVIEWER_ID` 로 바꿀 수 있다) 프로세스 단위로 고정된다(`backend/settings.py`).** 같은 샌드박스의 에이전트가 HTTP 로 승인을 부르거나 공개 주소 접속자가 승인할 수 있는 배치는 허용하지 않는다. 배치는 03 §6 `⚠ 미해결 충돌(D3·D10, 샌드박스 배치)` 참조.

| 메서드 | 경로 | 성공 | 오류 |
|---|---|---|---|
| GET | `/api/audit` | 200 AuditEntry[] | — |
| POST | `/api/audit/{id}/decision` `{decision, reason?}` | 200 AuditEntry | 404 `not_found`, 409 `not_decidable`·`already_decided`, 403 `self_approval`, 422 `validation_error`, 500 `internal_error` |

- `decision`: `approve` / `reject`. `reason` 은 선택(최대 1000자). 거부에 `reason` 이 없으면 서버가 기본 문구를 쓴다.
- **신원은 서버가 주입한다.** 요청 본문에 요청자·승인자 필드를 받지 않는다(정의되지 않은 키는 422). 승인자는 서버 설정에서 온다.
- 결정할 수 있는 것은 id 가 `draft:<draft.id>` 인 항목뿐이다. `audit:<run_id>:<seq>` 항목(읽기 전용 기록)은 409 `not_decidable`.
- 만든 주체는 자신의 요청을 결정할 수 없다(403 `self_approval`). 이미 결정된 항목은 다시 결정할 수 없다(409 `already_decided`). `agent:` 로 시작하는 신원은 승인자로 거부된다(`backend/settings.py`: 설정 로드 시 `ValueError`로 기동 실패, `backend/app.py`: `APP_PROCESS_ROLE=agent` 면 import 시 기동 거부). 이것은 **기동 시 설정값 검사**이며 요청마다 신원을 검사하는 것이 아니고, HTTP 호출 자체를 막지도 않는다.
- `AuditEntry`: `{id, time(HH:MM:SS, Asia/Seoul), at, kind: ok|deny|pend|approved|rejected, text: {ko, en}, decided_by, decided_at, origin: hitl|audit}`.
- 오류 본문은 `{"error": {"code": str, "message": str}}`. 코드는 `validation_error`(422), `http_error`(그 밖의 HTTP 오류), `internal_error`(500) 등이다(`backend/app.py`).

> ⚠ 미해결 충돌: D10 와 어긋남 — 위 `/api/security/events` 이벤트 스트림과 `decided_by` 없는 `action` 형식은 `/api/audit` 와 다르다. 사람 결정 대기

## 11. 오류

| 코드 | 의미 | 화면 |
|---|---|---|
| 400 | 요청 형식 오류 | — |
| 404 | 세션·카드·경로 없음 | 세션 만료 안내 |
| 409 | 허용되지 않는 상태 전이 | — |
| 422 | 일정을 이해하지 못함 | 되묻는다 |
| 503 | 모델·경로 서비스에 닿지 못함 | "지금은 판단할 수 없어요" |

```json
{"error": {"code": "route_unavailable", "text": "경로를 계산하지 못해 예상 시간으로 보여 드려요"}}
```

⚠ 미해결 충돌: D10 과 어긋남 — 위 오류 본문의 `text` 는 §10.1 과 `backend/` 의 `{code, message}` 와 다르다. §10.1 의 `{"error": {"code", "message"}}` 가 기준이고, 이 절의 코드 표(400·404·409·503 등)와 `route_unavailable` 은 화면용 API 가 정해질 때 맞춘다 — 사람 결정 대기
