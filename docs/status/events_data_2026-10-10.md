# 행사 수집 실행·검증 보고 (2026-10-10)

> **이것이 모든 행사가 아니다.** 서울 열린데이터광장 문화행사 API 가 싣는 항목과, 공식 도메인 검색(Tavily)에서 LLM 이 추출한 일부 후보만 담았다. 목록에 없다고 행사가 없다는 뜻이 아니다. 검색 수집분은 "검색 수집 · 미확인"이며 사람 확인 전 사실로 쓰지 않는다 (D7·D12·D13).

Sprint 3 / Stage 5b / T321. 키 값·원응답·검색 본문은 싣지 않았다(규칙 1, D12 ⑦).

## 1. 실행 (2026-10-10)

| # | 명령(키 값 없음) | 호출 | 결과 |
|---|---|---|---|
| 1 | `KC_TARGET_REGION=jung,jongno,mapo,gangnam uv run python -m domains.kcontext.catalog --region jung,jongno,mapo,gangnam update --source seoul_openapi` | 서울 API 1회 실행(1000행 단위 페이지) | fetched 8712, new 8712, ok |
| 2 | `uv run python -m domains.kcontext.ingest.events.web_run --source junggu --month 2026-10 --out var/data/events/web.junggu.jsonl --collected-at 2026-10-10 --max-calls 10 --max-candidates 10` | Tavily 3회 | 후보 10, 레코드 4, 버림 3, problems 16 (LlmCallError 3건) |
| 3 | 같은 명령 `--source gangnam`, 출력 `web.gangnam.jsonl` | Tavily 2회 | 후보 10, 레코드 3, 버림 7, problems 15 |
| 4 | `catalog ... update --source junggu_site` / `--source gangnam_site` | 없음(파일 읽기) | 각각 4건 / 3건 |

스냅샷(D19): 서울 API 항목 중 스냅샷 날짜에 끝나지 않은 것만 저장한다. 건수는 `domains/kcontext/data/snapshots/catalog/SNAPSHOT.md` 참조.

## 2. `catalog status` 요약

built_at 2026-10-10T02:08, 항목 8719.

| 출처 | 상태 | 마지막 수집 |
|---|---|---|
| seoul_openapi | implemented | fetched 8712 / new 8712, 오류 없음 |
| junggu_site | partial | 4 / 4 |
| gangnam_site | partial | 3 / 3 |
| tourapi_kto | configurable_unverified | 키 없음(DATA_GO_KR_SERVICE_KEY), 실행 안 함 |
| junggu_sns · caci · jeongdong | manual_only | 자동 수집 안 함 |
| hanokmaeul | candidate_not_implemented | 없음 |

## 3. 구별 × 출처별 항목 수 (`var/catalog/entries.json` 직접 집계, 읽기만)

| 구 | seoul_openapi | junggu_site | gangnam_site | in_target |
|---|---:|---:|---:|---|
| 종로구 | 4,918 | 0 | 0 | yes 4,918 |
| 중구 | 1,911 | 0 | 0 | yes 1,911 |
| 마포구 | 1,167 | 0 | 0 | yes 1,167 |
| 강남구 | 595 | 0 | 0 | yes 595 |
| 구 미확인 | 121 | 4 | 3 | **unknown 128** |
| 합계 | 8,712 | 4 | 3 | yes 8,591 / unknown 128 |

- 합계 8,719 = 서울 API 8,712 + 검색 수집 7 (항목 수는 중복 병합 후).
- 검증 상태: verified 8,591(전부 서울 API) / needs_check 128(서울 API 121 + 검색 수집 7).
- 수명주기: ended 8,531 · ongoing 109 · scheduled 50 · unknown 29.
- 예약 상태는 8,719건 모두 unknown(출처가 예약 여부를 주지 않는다).
- 검색 수집 7건은 기간(시작·종료일)이 비어 있어 날짜 기준 검색에 잡히지 않는다. 구도 미확인이라 관리자 검토 대기다.
- 2026-10-15~18 에 열리는 행사(서울 API): 종로 55 · 중구 29 · 마포 15 · 강남 9.

## 4. 사람 확인용 무작위 5건 (seed 20261010, `random.Random`)

서울 API 는 구가 확인된 항목에서 3건, 검색 수집은 7건 중 2건. 링크의 내용과 일치하는지 사람이 열어 확인한다.

| 제목 | 구 | 기간 | 출처 | 링크 |
|---|---|---|---|---|
| [서울무형유산교육전시장] 일일체험 \| 전통주 일일체험 - 석탄주 빚기 | 종로구 | 2025-02-22~2025-04-26 | seoul_openapi | https://culture.seoul.go.kr/culture/culture/cultureEvent/view.do?cultcode=152247&menuNo=200011 |
| [마포문화재단 해피 메이] 뮤지컬 [이상한 과자가게 전천당] - 천옥원, 소원과자 대결전 | 마포구 | 2024-05-04~2024-05-06 | seoul_openapi | https://culture.seoul.go.kr/culture/culture/cultureEvent/view.do?cultcode=145534&menuNo=200008 |
| 이나래의 대금 [이철주 전승 민간 관악영산회상] | 종로구 | 2022-06-04~2022-06-04 | seoul_openapi | https://culture.seoul.go.kr/culture/culture/cultureEvent/view.do?cultcode=138052&menuNo=200008 |
| 2026년 남산자락숲길 페스타 | 미확인 | 없음 | junggu_site(검색 수집·미확인) | https://www.junggu.seoul.kr/dong/donghwa/content.do?cmsid=13329 |
| 16일 저녁엔 남산으로 퇴근하세요... 중구, '남산동행 중구민 걷기대회' 개최 | 미확인 | 없음 | junggu_site(검색 수집·미확인) | https://www.junggu.seoul.kr/news |

관찰: 무작위 서울 API 3건은 모두 이미 끝난 과거 행사다(전체의 98%가 ended). 검색 수집 2건 중 하나의 링크는 개별 글이 아닌 목록 페이지(`/news`)다.

## 5. 문제 상위 사유

- **Tavily 쪽 LlmCallError 3건(중구)**: 원인은 **확인 필요**. 이번 실행의 오류 메시지를 보존하지 않았다. 클라이언트 코드(`core/llm/client.py`)상 LlmCallError 는 전송 오류(transport 예외) 또는 비정상 status 일 때 난다. 가능성 1순위는 LLM 1회 한도 40초(provider 공통)를 넘긴 시간 초과(본문이 긴 후보 추출)이고, 429·5xx 도 배제하지 못한다. 확인하려면 같은 후보로 재실행하며 예외 종류만 기록한다.
- problems 는 중구 16·강남 15건. 상위 사유별 분류는 수집기 출력에 요약이 없어 이 보고서에서 세지 못했다(확인 필요).
- 후보 10 중 레코드가 되는 것은 3~4건(30~40%). 나머지는 행사 정보 부족 또는 구 불일치로 버려졌다(중구 3, 강남 7).
- 서울 API 121건은 구 정보(GUNAME)가 비어 대상 지역 미확인이다.

## 6. 실제 서버 확인 1회 (포트 8001)

`uv run uvicorn backend.app:app --port 8001` (KC_TARGET_REGION 4개 구), 직접 띄워 확인 후 종료(8001 리슨 없음 확인).
`POST /api/messages`, 문장 "10/15에 창덕궁 10시, 익선동 2시, 숙소는 종로3가야", context `{"schema":"chat-context/v1","lang":"ko"}`, trip 없음. 같은 요청을 2번 보냈고(두 번째는 일정 이해 캐시 사용, `schedule.source == "cache"`), 아래는 두 번째 응답이다.

- 응답 상태 ok, 답변: 일정 3개, 실록 언급 3건, 주변 행사 119건, 가정·확인 필요 5건.
- `events.events` 개수 **119**, 제외(excluded) 8,600 (합 8,719), catalog_empty false.
- coverage_note 끝 문구: "…일정 날짜 범위로 찾았어요." (D22 날짜 기준 검색이 적용됨)
- 행사 제목 3개:
  1. 재능 혜화 마티네 (2026-10-15 11:00, JCC아트센터)
  2. [세종문화회관] 2026 대한민국국악관현악축제 [부산시립국악관현악단] (2026-10-15 19:30, 세종M씨어터)
  3. [2021자치구 문화 예술 특성화사업]'M페스티벌시리즈'꼬레아리듬터치#3〈마포삼해주이야기〉 (시작 2021-12-09, 종료일 없음)
- 주의: 3번은 2021년 시작·종료일 없음 항목이 10/15 결과에 들어왔다. 종료일 없는 항목의 처리 규칙을 검토할 가치가 있다(확인 필요, 이번 범위에서 고치지 않음).
- LLM 호출: 첫 요청의 일정 이해에서 발생(1~2회).
- D23 적용 뒤 같은 요청의 행사 99건(종료일 없이 1년 넘은 20건 제외). query 를 직접 호출해 실측한 값이다.
