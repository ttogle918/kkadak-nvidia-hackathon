# 챗봇 일정 흐름 계약 — `kc-chat-bundle/v1` (구현용, 2026-10-07)

상태: 구현 기준 문서. 배경: `docs/chat-context-router.proposal.md`, `docs/screen-api.proposal.md`, D2·D3·D10·D12·D13·D14.
이름 메모: 스프린트 문서의 디렉터리형 `kc-bundle/v1`(T216b)과 겹치지 않게 이 단일 파일 묶음은 `kc-chat-bundle/v1` 이다.

## 흐름
```
화면 --POST /api/messages {text, context?}--> backend
   backend: 일정 같은 메시지인가? (규칙 게이트)
      아니오 → 지금처럼 일반 챗봇(LLM)이 답한다 (bundle 없음)
      예     → 별도 프로세스 `python -m domains.kcontext.pipeline ...`(APP_PROCESS_ROLE=agent)
               → OUT/bundle.json (kc-chat-bundle/v1)
               → backend 가 같은 일정(anchors·free_slots)으로 행사 검색(catalog_runner, /api/events/search 와 같은 계산)
               → 앵커 0개면 일반 챗봇으로 폴백, 아니면 reply + bundle 반환
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
 "mentions": kc-mention/v1  // anchors[].mentions[]: {article_id, king, date_label, title_summary, quote(한문 원문), lang:"orig", locator, url, tier, source{...}}
 "events": /api/events/search 응답 본문 그대로 {events, excluded, problems, coverage} | null (검색 불가 시 null + problems 에 EVENTS_UNAVAILABLE)
 "cards": [{card, card_ready, missing}],   // card_ready=false 인 것은 화면이 '언급 기록' 간이 카드로 그린다
 "problems": [{code, message}], "coverage_note": "..."
}
```
- 좌표(lat/lng)는 검증된 장소 사전(`domains/kcontext/data/places/demo_places.json`)에 있는 장소만. 없으면 null → 지도 핀 없음, 목록에만.
- 크기 상한: bundle.json 1MB, mentions 앵커당 최대 5건, 앵커 최대 20개. 상한 초과는 잘라서 problems 에 `TRUNCATED`.
- 오류: 파이프라인 실패·시간 초과(90초)·잘못된 bundle → 일반 챗봇으로 폴백하거나 502 `pipeline_failed`(내부 출력 노출 금지, 로그에는 종류만).
- 동시 실행은 1건(기존 `ChatBusy` 429 재사용).

## 화면 표시 규칙(결정 사항)
- 출처는 아주 작은 태그. `tier` 글자 + 이름 한 줄. `tier C`(검색 수집·미확인) 행사도 같은 태그에 등급을 보인다("검색 수집 · 미확인").
- 실록 언급은 "실록에 이런 기록이 있어요" — 이야기라고 쓰지 않는다. 한문 원문 구절과 "한글 요약(원문 아님)"을 구분해 보이고, 누르면 실록 원문 링크(`url`, http/https 만)로 간다. 국역 없음 표시.
- 지도: 좌표 있는 앵커에 핀, 누르면 정보창(textContent). 옛길 선은 이번 범위 밖.
- 행사가 비어 있으면 "주변 행사를 아직 찾지 못했어요(데이터 준비 중)" 처럼 사실대로 보인다. 지어내지 않는다.
