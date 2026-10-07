# Sprint 2 보충(초안) — 구청 행사 검색 수집 (D12)

> 상태: **D12 승인됨(2026-10-07). T225·T226·T210·T211b 구현 완료, reviewer 검토 반영 중(아래 "검토 반영").** `docs/sprints/sprint-2.md`(확정본)는 건드리지 않는다. 승인되면 아래 두 태스크를 Stage 2 의 선택 항목으로 붙이거나 S3 로 보낸다.
> 대상 자치구: **중구 · 마포구 · 강남구.** 태스크 ID 는 확정본의 마지막(T224) 다음부터.

## 사람 선행
| # | 할 일 | 막히는 것 | 없을 때 |
|---|---|---|---|
| H11 | https://tavily.com 에서 키 발급 → 호스트 셸에 `export TAVILY_SEARCH_KEY=...` (커밋 금지) | T226 실호출 | 합성 fixture 로 T226 은 끝까지 녹색. 실호출만 못 한다 |
| H12 | 중구·마포구·강남구 **공식 도메인**을 직접 열어 확인해 T225 문서에 적는다 (**세 구 모두 사용자가 2026-10-07 에 URL 을 직접 제시 — 도메인 확인됨.** 아래 "확인된 도메인 메모" 참고) | T225 | 미확인 구는 `[확인 필요]` 로 두고 건너뛴다 |
| H13 | D12 승인 | 전부 | — |

## T225 — [확인·1쪽] Tavily 호출 규격·약관·구청 도메인 [선택 · 병렬]
- **착수 조건**: D12 승인(문서 확인만 하므로 키는 필요 없다).
- **변경 파일** (신규): `docs/spikes/web_search.md`, `domains/kcontext/data/web_sources/{junggu,mapo,gangnam}.json`
- **내용**
  1. `docs/spikes/web_search.md`: 첫 줄에 확인한 날짜. 엔드포인트·인증 방식·파라미터(`include_domains`·`time_range`·`max_results`·`search_depth`·`include_raw_content`)·응답 필드·크레딧(basic 1, advanced 2, extract 5 URL당 1)을 공식 문서 URL 과 함께 표로. **약관의 결과 저장·재사용·재배포 조건**을 찾아 원문 문구를 인용(못 찾으면 `[확인 필요]`). 각 구청 사이트의 robots.txt·이용조건 확인 결과.
  2. `web_sources/<id>.json` 형식(다른 키는 거부):
     ```json
     {"region": "<regions/*.json 의 id>", "gu": "중구", "domains": ["host", ...],
      "allow_url_prefixes": ["https://host/경로", ...],        // 선택. 응답 URL 이 이 접두 중 하나여야 통과
      "disallow_path_prefixes": ["/경로", ...],               // 선택. robots.txt 등에서 온 제외 경로
      "drop_urls_with_query": false,                          // 선택. true 면 '?' 가 든 URL 을 버린다
      "queries": ["{gu} 축제 행사 {month}", "{gu} 문화행사 {month}"], "status": "confirmed", "note": ""}
     ```
     `status` 는 `confirmed`(사람이 도메인을 열어 확인) 또는 `unconfirmed`. 도메인 값에 `[확인 필요]` 가 있으면 `unconfirmed`.
- **지켜야 할 규칙**: 호스트명·필드는 문서에서 본 것만(추측 금지). 키 값 금지(규칙 1).
- **DoD**: 문서 3칸(규격·약관·도메인)에 출처 URL 이 붙어 있다.

## T226 — 검색 수집기(Tavily → 추출 → 인용 검증 → 정규화) [선택 · Stage 2 · T210 이후]
- **착수 조건**: D12 승인, T210(정규화·저장) 완료, T211b(`inject.screen`) 완료. T225 는 없어도 합성으로 진행(실호출만 `confirmed` 필요).
- **변경 파일**
  - 신규: `domains/kcontext/ingest/events/web.py`(Tavily 호출·후보 모으기), `extract.py`(LLM 추출 + 인용 검증), (CLI 는 새 파일 없이 기존 `__main__.py` 에 `--provider web` 을 추가한다); `domains/kcontext/data/regions/{gangnam,mapo}.json`(main 에서 팀원이 `jung`·`mapo`·`gangnam`·`jongno` 로 지역을 교체해 T226 이 만들 필요가 없어졌다 — 병합 때 팀원 것을 채택); `tests/domains/kcontext/ingest/test_kc_ingest_events_web.py`, `test_kc_ingest_events_extract.py`; `tests/fixtures/kcontext/events/web.synthetic.json`; `.env.example`(`TAVILY_SEARCH_KEY=` 이름만 + 주석 "호스트 수집기 전용(D12), 샌드박스에 넣지 않는다")
  - 수정(계약 보충, T201 소유 파일이라 담당 확인): `domains/kcontext/contract/records.py` 의 `EventRecord.fetched_from` Literal 에 `"web"` 추가, `tests/domains/kcontext/contract/` 에 해당 케이스
- **인터페이스**
  ```python
  # web.py
  class WebSearchError(RuntimeError); class KeyMissing(WebSearchError); class SourceUnconfirmed(WebSearchError)
  @dataclass(frozen=True) class Candidate: url: str; title: str; content: str; score: float
  def load_web_source(region_id: str, directory: Path | None = None) -> dict       # 없으면 FileNotFoundError
  def search_candidates(src: Mapping, *, month: str, client: httpx.Client | None = None,
                        env: Mapping[str, str] | None = None, max_calls: int = 30) -> list[Candidate]
      # status != "confirmed" 또는 domains 에 [확인 필요] → SourceUnconfirmed. 키는 env["TAVILY_SEARCH_KEY"], 없으면 KeyMissing
      # 요청은 include_domains=src["domains"], time_range="month", search_depth="basic", include_raw_content 사용
      # 응답 URL 의 호스트가 domains 밖이면 버린다(서버가 어겨도 코드가 거른다). 타임아웃 10초, 재시도 없음
  # extract.py
  Extractor = Callable[[str], list[dict]]     # 본문 -> [{title, start_date, end_date, place_name, category, quote}]
  @dataclass(frozen=True) class ExtractResult: records: tuple[EventRecord, ...]; problems: tuple[str, ...]; dropped: int
  def extract_events(c: Candidate, *, extractor: Extractor, screen: ScreenFn, region: Region,
                     collected_at: str) -> ExtractResult
  ```
  `ScreenFn` 은 T211a 의 `story.py` 와 같은 모양 `(text, source_id) -> Blocked | None`.
- **핵심 로직**
  1. `search_candidates`: `src["queries"]` 의 `{gu}`·`{month}` 를 채워 호출. 호출 횟수가 `max_calls` 를 넘으면 중단하고 problem. 키 값은 로그·예외에 `***`(`core.audit.redact_text`).
  2. `extract_events`: 먼저 `screen(content, f"web:{url}")` — `injection` 이면 이 후보를 통째로 버리고 `dropped`+1 과 problem. `suspicious` 면 caveat 를 description 에 붙이지 않고 problem 만 남긴다. extractor 는 `core.llm.LlmClient` 위에서 만든 함수를 주입받는다(테스트는 가짜 extractor).
  3. **인용 검증**: 항목의 `quote` 가 후보 `content`(공백 정규화 후)에 부분 문자열로 있어야 한다. 없으면 버리고 `dropped`+1. 통과해도 `start_date`·`end_date` 가 `quote` 안의 숫자에서 확인되지 않으면 해당 날짜를 `None` 으로 바꾼다(LLM 값을 믿지 않는다).
  4. 레코드: `fetched_from="web"`, `source=SourceRef(id=f"web:{url}#{순번}", tier="C", name=f"{구청 이름 [확인 필요 시 도메인]} (검색 수집)", locator=f"{collected_at} 수집 · 갱신일 미제공", url=c.url, published=None, collected_at, quote=quote)`. `status="unknown"`, `geometry_type="approx"`, 좌표 `None`, `region=region.id`. `category` 가 `EVENT_CATEGORIES` 밖이면 `"other"`. URL 을 만들어 내지 않는다.
  5. CLI: `python -m domains.kcontext.ingest.events --provider web --region junggu --month 2026-10 --out var/data/events/web.jsonl --collected-at YYYY-MM-DD [--fixture PATH] [--max-calls N]`. `--fixture` 가 있으면 Tavily 를 부르지 않고 합성 후보를 읽는다. `KeyMissing`·`SourceUnconfirmed` → 종료 코드 2 와 "`--fixture` 로 실행할 수 있다". 보고서 JSON 한 줄(candidates, records, dropped, problems).
  6. 같은 `(region, 제목, start_date)` 중복은 URL 이 다르면 `quote` 가 긴 쪽 하나만 남긴다.
- **엣지 케이스**: 후보 0건 → 정상 종료. extractor 가 비정형 응답 → 그 후보만 problem. 본문이 매우 길면 앞 20,000자만 extractor 에 준다. 날짜 형식은 `YYYY-MM-DD` 로 정규화하되 실패하면 None.
- **fixture 경로**: `web.synthetic.json` 은 후보 3건(정상 / quote 가 본문에 없음 / 숨은 지시문 포함), 전부 `○○`·`"synthetic": true`. Tavily 호출은 `httpx.MockTransport` 로(네트워크 없음) — 키 가림·KeyMissing·Unconfirmed·도메인 밖 URL 제거·`max_calls`.
- **지켜야 할 규칙**: D1·D7·D12 · 규칙 1·2 · 구·도메인 리터럴은 `data/` JSON 에만(코드에 지명·도메인 금지) · Tavily 응답 원문 커밋 금지.
- **DoD**: `uv run python -m pytest -q tests/domains/kcontext/ingest -k "web or extract"` 통과 · `uv run python -m domains.kcontext.ingest.events --provider web --region junggu --month 2026-10 --fixture tests/fixtures/kcontext/events/web.synthetic.json --out /tmp/kc-web.jsonl --collected-at 2026-10-07` 0 종료 · `uv run ruff check .` · pytest 전체 건수가 직전(859)보다 줄지 않는다.

## 화면·판정 쪽 영향 (이 초안의 범위 밖, 승인 시 별도 태스크)
- 카드의 출처 태그에 "검색 수집 · 미확인" 딱지(`format.js` 문구 사전, ko·en 1:1)가 필요하다.
- T211b 의 행사 판정은 `fetched_from="web"` 이면 `status` 를 확정으로 올리지 않는다.

## 확인된 도메인 메모 (T225 가 `web_sources/` 에 옮긴다)
- 강남구: `www.gangnam.go.kr` (사용자 제시, 2026-10-07). 메인 페이지를 열어 보니 행사 목록 `/board/B_000045/list.do`, 공지사항 `/board/B_000001/list.do`, 보도자료 `/board/B_000031/list.do` 메뉴가 있었다(메뉴 경로는 한 번 읽은 값 — T225 에서 재확인). 강남페스티벌은 별도 도메인 `visitgangnam.net` 으로 연결돼 있다 — `include_domains` 에 넣을지는 사람이 정한다(구청 공식 연결이지만 `gangnam.go.kr` 밖).
- 중구: `www.junggu.seoul.kr` (사용자 제시, 2026-10-07). 메인에서 읽은 경로: 공지사항 `/content.do?cmsid=14231`, 중구소식 `/content.do?cmsid=14391`, 문화정책과 `/content.do?cmsid=14449`, 체육관광과 `/content.do?cmsid=15531`. 행사 홍보 일부는 공식 블로그 `blog.naver.com/junggu4u` 로 나간다 — 구청 도메인 밖이라 `include_domains` 에 넣을지는 사람이 정한다(넣으면 `naver.com` 전체가 아니라 블로그 경로만 허용할 방법이 있는지 T225 가 확인).
- 마포구: `www.mapo.go.kr` (사용자 제시, 2026-10-07). 메인에서 읽은 경로: 문화행사 `/site/main/board/culturevent/list`, 문화공연 `/site/main/content/mapo020403`, 공지사항 `/site/main/board/notice/list`. 별도 축제 도메인 없음.
- 세 곳 모두 메뉴 경로는 메인 페이지에서 한 번 읽은 값이다 — T225 가 `web_sources/` 에 옮기며 재확인한다. robots.txt·이용조건은 아직 안 봤다.

## 결정 반영 (2026-10-07, 사용자)
- 마포구 수집 **허용**. robots.txt 가 일반 크롤러를 막고 있다는 사실은 `web_sources/mapo.json` note 에 남겼다(허용은 사용자 결정). 코드는 `/CmsWeb/` 와 쿼리스트링 URL 을 거른다.
- 구청 도메인 밖 후보: 강남페스티벌 `visitgangnam.net` **포함**. 중구 공식 블로그 `blog.naver.com/junggu4u` 는 네이버 robots.txt 가 AI 학습·RAG 봇 접근을 금지해 **제외**(2026-10-07).
- T226 `search_candidates` 는 응답 URL 을 ① 호스트가 `domains` 안인지 ② `allow_url_prefixes` 접두인지(있으면) ③ `disallow_path_prefixes`·`drop_urls_with_query` 에 걸리지 않는지 순서로 거른다. 이 세 키는 T226 의 `load_web_source` 가 읽고 모르는 키는 여전히 거부한다.
- D12 ① "확인된 구청 공식 도메인만" 은 "사람이 승인한 도메인만"으로 읽는다(위 두 곳은 사용자 승인) — D12 본문 문구를 아래처럼 고쳤다.

## 구현 결과 (2026-10-07)
- **T225 완료**: `docs/spikes/web_search.md`, `domains/kcontext/data/web_sources/{junggu,mapo,gangnam}.json`.
- **T226 코어 완료, CLI 는 `web_run.py`**: `domains/kcontext/ingest/events/{web.py, extract.py, web_run.py}`, 지역 `regions/{mapo,gangnam}.json`, 계약 `FETCHED_FROM`·`EventRecord.fetched_from` 에 `"web"` 추가, 테스트 37건(전체 896 passed), `.env.example`.
- 명세와 달라진 점: ① `search_candidates` 는 `SearchOutcome(candidates, problems, calls, dropped_urls)` 를 돌려준다. ② CLI 는 T210 의 `__main__.py` 가 아직 없어 `python -m domains.kcontext.ingest.events.web_run` 이다(T210 이 생기면 `--provider web` 으로 합친다). ③ 좌표가 없는 레코드는 계약상 `approx` 가 반지름을 요구해 `geometry_type="point"`·좌표 None 으로 쓴다(`test_event_without_coordinates_is_allowed` 와 같은 형태). ④ `time_range` 는 기본 미사용(`--time-range` 로 선택) — 올해 행사 공지가 한 달 이상 전에 올라올 수 있어서. ⑤ `.env` 의 `TAVILY_SEARCH_KEY` 는 CLI 가 `os.environ` 을 바꾸지 않고 읽는다(셸 env 우선).
- **실행 가능 범위**: `--candidates-only`(실호출, screen·LLM 불필요)와 단위 테스트는 동작한다. 레코드 추출까지 가는 실행은 **T211b `inject.screen`(없음)** 과 **LLM transport(T223, 이월)** 가 생긴 뒤에 된다. 그 전에는 종료 코드 2 와 이유를 알려 준다.
- **실측**: 강남·중구는 도메인 매칭 확인. **마포구는 Tavily 로 본 사이트 결과 0건**(robots 전면 차단과 일치) — 마포는 다른 경로로 채운다.

## 구현 결과 2 — T210·T211b (2026-10-07)
- **T211b 완료**: `domains/kcontext/judge/{inject.py, now.py}`, 테스트 `tests/domains/kcontext/judge/test_kc_judge_{inject,now}.py`(29건). `judge/__init__.py` 는 T211a 소유라 만들지 않았다(네임스페이스 패키지로 import 된다).
- **T210 완료**: `domains/kcontext/ingest/events/{__init__.py, normalize.py, store.py, manual.py, __main__.py}`, 테스트 `test_kc_ingest_events_{normalize,manual,store}.py`, 합성 fixture `tests/fixtures/kcontext/events/manual.synthetic.json`. `ingest/__init__.py`·`field_maps/` 는 T209·T205 소유라 만들지 않았다(`load_field_map` 은 파일이 없으면 `FieldMapMissing` → CLI 종료 코드 2).
- **T226 연결**: `web_run` 이 `store.write_jsonl`·`--db` 색인을 쓴다. `python -m domains.kcontext.ingest.events --provider web ...` 로도 부른다. 실제 `inject.screen` 이 연결돼 fixture DoD 명령이 0 으로 끝난다(후보 3 → 레코드 1, 지시문 후보와 인용 불일치 각 1건 버림).
- **검증**: pytest 954 passed(직전 896), ruff 통과, T210·T226 DoD 명령 0 종료.
- 명세와 달라진 점·해석한 점
  1. 종료일이 시작일보다 빠른 레코드: 명세는 "값 유지"였지만 계약(`EventRecord.from_dict`)이 거부해서 **종료일을 비우고 problem** 으로 남긴다(normalize·extract 공통).
  2. 좌표 없는 레코드: 명세는 `geometry_type="approx"` 였지만 계약상 approx 는 반지름이 필요해 `point`·좌표 None 으로 쓴다.
  3. 중복 병합: 명세는 "제목 정규화가 같으면 한 그룹"이지만 함정 항목 "동명이처(제목 같고 거리 멂)는 다른 그룹"과 충돌해, **둘 다 좌표가 있고 `dedupe_m` 보다 멀면 제목이 같아도 다른 행사**로 풀었다. 좌표가 없으면 제목만으로 합친다.
  4. 충돌 해결: 최신 공식 공지가 "하나뿐"일 때가 아니라, 최신 날짜의 공식 출처들이 **같은 값**이면 채택한다(같은 날짜 같은 값은 충돌이 아님). 값이 다르면 미해결 → 보류.
  5. 딱지 `확인 필요` 의 caveat 에 "장소 불분명"을 추가했다(명세는 날짜·단독 출처·n일 전 갱신 3종).
  6. `--from/--to` 는 fixture 실행에서 기간이 겹치지 않는 레코드를 거르는 데 쓴다(`skipped_out_of_range` 로 보고, 기간을 모르면 남긴다).
- **남은 것**: LLM 호출 연결(T223, 이월) — `web_run` 의 실검색 → 레코드 경로는 추출기가 붙어야 돈다. T210-fetch(TourAPI·서울 실호출)·T205 field_map 은 미착수.

## 검토 반영 (2026-10-07, reviewer FAIL → 수정)
- **차단 3건 수정**: ① 날짜 확인이 연도를 따진다(quote 에 2025 가 적히면 2026 으로 못 바꿈, `1.2km`·`1-2층` 같은 수치는 날짜로 안 침). ② quote 200자 상한 + 제목 앞뒤 창 안에서만 날짜·장소 확인 + 제목 3자 이상. ③ `judge_events` 가 제목 전 언어·장소·설명·출처 이름·위치·인용을 한 번에 검사한다.
- **경고 수정**: W2 프롬프트 구분 태그 무력화 · W3 같은 지역·기간 필수, 묶음은 양쪽 모든 쌍이 같은 행사여야 합침(이행적 과병합 방지), 기간이 `merge_gap_days`(60) 이상 떨어지면 다른 행사 · W4 대표 레코드에 값이 없으면 다른 레코드에서 채움(C·D 의 취소·변경은 적용하지 않고 caveat) · W5 공식 출처만으로 최신성 계산, `published` 없으면 "갱신일 미제공" caveat · W6 공식 값이 있으면 C·D 값은 충돌 대신 caveat · W7 `situation.trip` 검증, 잘못되면 `NowJudgement.problems` · W8 URL 경로 정리(디코딩·`//`·`..`·대소문자·쿼리 키=값) · W9 합성 fixture 는 `synthetic=true`, 색인(`--db`) 거부 · W12·W13 문서 정합.
- **이중 탈락 버그**: 취소로 묶음이 빠질 때 비대표 레코드가 "중복"과 "취소됨"으로 두 번 기록되던 것을 고쳤다(깔때기 집계도 정정).
- **제안 반영**: S2 제목 최소 길이, S3 테스트 키 문자열을 실행 시 조립 + `core.audit.redact` 에 `tvly-` 패턴 추가, S4 낡은 문서 정리, S5 `web_run` 이 problem 내용을 stderr 로 출력.
- **미룬 것(경고)**: W1 색인 청크에 검사 결과 표시·소비 쪽 `wrap` · W10 "검색 수집 · 미확인" 화면 문구 · W11 Tavily 호출의 감사(audit) 기록 · S1 저장 quote 를 원문 구간으로. 모두 소비자(파이프라인 T216·MCP T217·LLM 연결 T223)가 생길 때 처리한다. 그 전에는 `fetched_from="web"` 을 화면 경로에 넣지 않는다.
- 위 "명세와 달라진 점" 중 정정: `time_range` 는 기본 미사용, CLI 옵션은 `--region` 이 아니라 `--source`, `geometry_type` 은 `point`. "web 레코드의 status 를 확정으로 올리지 않는다"는 `now.py` 가 C·D 의 취소·변경을 적용하지 않는 규칙으로 구현됐다.

- **병합 메모(2026-10-07)**: main 의 지역 교체(f77fd48: `euljiro`·`sinchon` 삭제, `jung`·`mapo`·`gangnam`·`jongno`)를 채택했다. `web_sources/junggu.json` 의 region 은 `jung`, 수기 fixture·테스트의 지역도 `jung` 으로 바꿨다. 지역 파일 충돌(`mapo`·`gangnam`)은 팀원 것을 그대로 썼다.

## 2차 검토 반영 (2026-10-07)
- **차단 2건 수정**: X1 비공식(C·D) 출처에서만 채운 시작일·장소는 값은 보여 주되 딱지를 "확인 필요"로 두고 caveat("…은(는) 비공식(검색 수집) 출처에서만 확인")를 남긴다(시작 시간은 caveat 만). X2 날짜와 떨어진 연도 표기("2025년 제10회", "작년(2025년)")도 연도로 모아 그 연도만 인정한다.
- **남은 경고**: W-a 연도 추정 표시 · W-b `_MD_NUM` 형식(공문서 `10. 15.(수)`, 범위 종료일, 허용 목록 방식 lookahead) · W-c 창 경계 · W-d 묶기 순서 의존(입력 정렬) · W-e 재일정(`changed` 공지가 기간 거르기보다 먼저 빠짐) · W-f C·D 대표의 취소 · W-g 시작·종료일 동시 채택 · W-h trip 오류 시 `per[1] < now` 거르기 · W-i fixture 기본을 합성으로. 제안 S-a~S-f 포함. 소비자(T216·T217) 연결 전에 처리하고, T216·T217 완료 조건에 "웹 레코드 wrap·딱지 테스트"를 넣는다.
