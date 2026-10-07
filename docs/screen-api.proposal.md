# 제안 — 화면용 API 계약 (구현 전, 팀원과 맞추기용)

상태: **제안**. 코드는 만들지 않았다. 번호·병합은 사람이 정한다(DECISIONS 에는 넣지 않음). 관련: D3·D10, `docs/09_DEV_PLAN.md` 1단계("가짜 데이터로 끝에서 끝까지"), `docs/chat-context-router.proposal.md`.

## 1. 현황 (2026-10-07 실행 확인)
프론트(`frontend/k-context/src/api/`)는 10개 메서드를 쓴다. 백엔드에 있는 것은 아래 표의 ✓ 뿐이고, 나머지는 404 다. 프론트 `http.js` 는 ✓ 인 것 중에서도 `getMessages`·`sendMessage` 만 연결했다.

| 프론트 메서드 | 제안 엔드포인트 | 백엔드 | 프론트(http) | 담당(제안) |
|---|---|---|---|---|
| getMessages / sendMessage | `GET·POST /api/messages` | ✓ | ✓ | 본인(챗봇) |
| getAuditLog | `GET /api/audit` | ✓ | 미연결 | 본인 |
| decideAudit | `POST /api/audit/{id}/decision` | ✓ (사람 전용, D2) | 미연결 | 본인 |
| getItinerary | `GET /api/itinerary` | 없음 | 미연결 | 팀원 |
| getRoutes | `GET /api/routes` | 없음 | 미연결 | 팀원(경로·geo) + 본인(이야기 구간) |
| getCards / getCard | `GET /api/cards`, `/api/cards/{id}` | 없음 | 미연결 | 본인(story) · 팀원(now) |
| getSources | `GET /api/sources` | 없음 | 미연결 | 본인 |
| getRationale | `GET /api/cards/{id}/rationale` | 없음 | 미연결 | 본인·팀원 각자 |
| (행사 화면) | `/api/events/*`, `/api/admin/*` | ✓ | 별도 페이지(`events.html`, `admin.html`) | 팀원 |

## 2. 원칙
1. **형식의 기준은 이미 있다.** 카드·경로·출처 형식은 `AGENT_CONTEXT.md` 3.3 과 `frontend/.../api/schema.js`(`validateCard`·`validateRoute`·`validateSource`)다. 새 형식을 만들지 않고, 서버가 같은 검증을 통과하는 값을 준다. 바꿀 때는 문서를 먼저 고친다.
2. **backend 는 `domains` 를 import 하지 않는다**(D3·D10). 카드·경로는 파이프라인이 쓴 출력 묶음(`kc-bundle/v1` JSON 파일)을 backend 가 읽어서 돌려준다. 파이프라인이 아직 없는 동안은 같은 형식의 **고정 파일**(fixture)을 읽는다 — 프론트 mock 데이터를 JSON 으로 옮긴 것.
3. **신원 필드 없음**(D2). 요청자·승인자는 서버가 정한다.
4. **오류 형식**은 지금과 같다: `{"error": {"code", "message"}}`, 메시지는 고정 문구.
5. **문자열 필드**는 `string` 또는 `{ko,en}`(`schema.js` 의 `isText`). 서버는 `lang` 쿼리가 있으면 그 언어 string 으로 줄 수 있다 `[선택]`.
6. **좌표**는 실제 API 에서 `[lat, lng]`. 프론트 mock 의 `geometry.space = "schematic"` 은 mock 에서만 쓴다.

## 3. 전환 순서 (프론트가 깨지지 않게)
1. **읽기 전용 5개를 fixture 로 연다**: `itinerary`·`routes`·`cards`·`sources`·`cards/{id}/rationale`. 프론트 mock 과 같은 내용을 JSON 으로 두고 backend 가 읽는다. 이 단계의 DoD: `?api=http` 로 화면이 mock 과 같게 그려진다 + 서버 응답이 `validateCard`/`validateRoute` 0건.
2. **프론트 `resolveApi` 를 메서드 단위로 섞는다.** 지금 `auto` 는 backend 가 떠 있으면 챗봇만 backend, 나머지는 mock 이다. 1단계가 끝난 엔드포인트부터 `http` 쪽으로 옮긴다(목록 하나를 고치면 된다).
3. **fixture 를 진짜로 하나씩 교체**: 이야기 카드(본인)와 행사 카드(팀원)가 각자 파이프라인 출력 묶음을 쓰게 하고, backend 는 같은 파일 경로만 읽는다.
4. `getAuditLog`·`decideAudit` 는 백엔드가 이미 있으므로 프론트 `http.js` 에서 연결만 한다(`nope()` 제거 + 테스트).

## 4. 합의가 필요한 것
- 일정(`itinerary`)을 서버가 보관하는지, 화면이 들고 있다가 요청에 실어 보내는지. 행사 API 는 이미 요청에 일정을 실어 보낸다(`/api/events/search` 의 `trip`·`itinerary`). 같은 방식이면 `GET /api/itinerary` 는 샘플 전용이다 `[제안: 화면이 들고 있는다]`.
- `routes` 에서 이야기 구간(본인)과 도보 시간·우회 계산(팀원 `geo/`)의 경계: 경로 id·구간·`walk_min`/`delta_min` 을 누가 채우는지.
- 출처 `Source.tier` 가 `C`(검색 수집·미확인)인 행사 카드의 화면 표기(D12 열린 질문).
- fixture 위치(`domains/kcontext/data/fixtures/`? backend 가 읽으니 `backend` 쪽 경로 설정이 필요).
