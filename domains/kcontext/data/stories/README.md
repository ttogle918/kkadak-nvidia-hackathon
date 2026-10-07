# 이야기 레코드 작성법 (StoryRecord)

이 폴더의 `*.json` 한 파일이 이야기 하나다. 형식은 `domains/kcontext/contract/records.py` 의
`StoryRecord` 이고, 읽을 때 `story_from_dict` 가 검사한다. **모르는 키가 있거나 기본값 없는 키가
빠지면 읽지 않는다**(값이 null 이어도 키는 쓴다).

## 규칙 (세 줄)
1. **출처마다 `locator`·`collected_at`·`quote` 가 없으면 넣지 않는다.** 화면의 출처 태그
   `[등급] 출처 이름 · 위치` 를 만들 수 없는 출처는 근거가 아니다.
2. **좌표 근거(`geometry.basis`)를 반드시 적는다.** 발굴·고지도 비정·표석 위치·주소 중 무엇에 기댄
   위치인지, 대략이면 `alignment: "approx"` 로 표시한다.
3. **기억으로 쓰지 않는다.** `CONTEXT_STORY_ROUTE` 5장의 씨앗은 검증 전이다. 원문을 직접 확인한
   구절만 `quote` 로 옮기고, 확인하지 못한 값은 비워 두거나 `[확인 필요]` 로 남긴다.

## 필드

| 필드 | 형식 | 설명 |
|---|---|---|
| `id` | str | 레코드 고유 id |
| `region` | str | 지역 id (`data/regions/*.json` 의 id) |
| `title` | Text | 제목. 문자열 또는 `{"ko": …, "en": …}` (두 키 모두 비어 있지 않게) |
| `theme` | str | 경로 주제 |
| `era` | str \| null | 시대 표기 |
| `geometry` | 객체 | 카드 geometry 와 같은 모양. `type`(point/segment/area/approx), `coords`(`[[lat, lng], …]`), `basis`, approx 면 `radius_m`(양수). `space` 는 `"geo"`(생략 가능) |
| `alignment` | `"exact"` \| `"approx"` | 옛 위치와 지금 위치가 정확히 맞는가, 대체로 겹치는가 |
| `claims` | 배열 | 주장 목록 (아래) |
| `narration` | Text \| null | 몰입 층. 근거가 없으면 지어내지 말고 null |
| `synthetic` | bool | 합성·예시 데이터면 true (기본 false) |

`claims[]` 한 원소: `{"text": Text, "evidence": [Evidence, …]}`

`evidence[]` 한 원소: `{"source": 출처, "stance": "support"|"contradict", "says": str|null, "claim_kind": "fact"|"lore"|"inference"}`
(`says`·`claim_kind` 는 생략 가능, 기본 null·`"fact"`)

`source` 는 카드 `sources[]` 와 같다: `id`, `tier`(S/A/B/C/D), `name`, `locator`, `url`(없으면 `""`),
`published`(str \| null), `collected_at`(`YYYY-MM-DD`), `quote`, `bib`(선택).
등급 기준은 `docs/AGENT_CONTEXT.md` 4.1.

## 예시 (전부 `○○` 합성 값 — 실제 사실·위치가 아니다)

```json
{
  "id": "story_example_1",
  "region": "region_example",
  "title": {"ko": "○○ 길 (합성 예시)", "en": "○○ Road (synthetic example)"},
  "theme": "○○",
  "era": null,
  "geometry": {
    "type": "segment",
    "coords": [[37.0, 127.0], [37.001, 127.001]],
    "basis": "합성 예시 — 실제 위치 아님",
    "space": "geo"
  },
  "alignment": "approx",
  "claims": [
    {
      "text": "○○ 기록에 이 구간이 나온다 (합성 예시)",
      "evidence": [
        {
          "source": {
            "id": "doc_ex_01", "tier": "S", "name": "○○실록 (합성 예시)",
            "locator": "○○ ○년 ○월 ○일", "url": "", "published": null,
            "collected_at": "2026-10-05", "quote": "「○○○○ 행차 ○○…」 (합성 예시 구절)"
          },
          "stance": "support",
          "claim_kind": "fact"
        }
      ]
    }
  ],
  "narration": null,
  "synthetic": true
}
```
