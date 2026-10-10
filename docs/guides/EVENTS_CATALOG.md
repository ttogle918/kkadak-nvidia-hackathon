# 행사 카탈로그 — 실행·설정·현황 (2026-10-07 작성, 2026-10-10 갱신: 4개 구 · 출처별 검색 수집 · 스냅샷)

사용자 흐름: 여행 날짜·숙소·기존 일정을 입력(또는 챗봇에 일정 문장) → 대상 구(중구·종로구·마포구·강남구)에서 열리는 행사와 참여 방법 확인 → 기존 일정에 추가·취소.
결정 근거: `docs/DECISIONS.md` D13(카탈로그), D12(검색 수집), D7·D10(호스트 수집·프로세스 분리), D19(스냅샷), D23(오래된 무기한 행사 제외). 실행 결과와 건수: `docs/status/events_data_2026-10-10.md`.

## 구성
```
domains/kcontext/catalog/   model · rules · merge · seoul · store · changes · runlog · updater · sources
                            query · fit · routes · reports · review · stories · grounding · api · __main__
domains/kcontext/data/catalog_sources.json   7개 출처의 실제 제공 방식과 구현 상태
backend/routers/events.py + backend/catalog_runner.py   HTTP API(계산은 별도 프로세스)
frontend/k-context/events.html · admin.html (+ src/events/)   행사 찾기·관리자 화면
deploy/catalog/README.md   주기 수집(cron·systemd·loop)
```

## 실행
```bash
uv sync
# 1) 수집 (키 없이 연결만 확인: sample 키 5행)
uv run python -m domains.kcontext.catalog --dir /tmp/kc-sample update --source seoul_openapi --sample
# (--sample 은 실제 카탈로그를 오염시키지 않도록 --dir <임시 폴더> 가 있어야만 돈다)
# 키가 있으면 전체 수집
uv run python -m domains.kcontext.catalog update --source seoul_openapi
uv run python -m domains.kcontext.catalog status            # 출처별 성공·오류·재시도 시각
# 2) 백엔드 (관리자 API 를 쓰려면 KC_ADMIN_TOKEN 설정)
KC_ADMIN_TOKEN=$(openssl rand -hex 16) uv run uvicorn backend.app:app --port 8000
# 3) 화면
cd frontend/k-context && python3 -m http.server 8766
#   http://127.0.0.1:8766/events.html            (서버 연결. 정적 서버 8766 이면 같은 호스트 8000 포트를 쓴다.
#                                                  ?base= 는 같은 출처 경로나 localhost·127.0.0.1 주소만 받는다)
#   http://127.0.0.1:8766/events.html?api=mock   (데모 데이터 — 배너로 표시, 실제 행사가 아님)
#   http://127.0.0.1:8766/admin.html             (관리자 토큰 입력)
```

## 대상 지역 — `KC_TARGET_REGION` 쉼표 목록
대상 구는 `KC_TARGET_REGION` 에 지역 id 를 **쉼표로** 적는다(기본 `jung`). id 는 `domains/kcontext/data/regions/*.json` 의 `jung`·`jongno`·`mapo`·`gangnam`.
```bash
export KC_TARGET_REGION=jung,jongno,mapo,gangnam
# 한 번만 지정하려면 --region (catalog 명령 공통 옵션)
uv run python -m domains.kcontext.catalog --region jung,jongno,mapo,gangnam update --source seoul_openapi
```
- 여럿이면 합친 지역으로 판정한다(`domains/kcontext/catalog/target.py` 에서만 쪼갠다). 모르는 id·빈 값은 오류.
- **백엔드도 같은 값으로 띄워야** 화면 검색이 4개 구를 본다: `KC_TARGET_REGION=jung,jongno,mapo,gangnam uv run uvicorn backend.app:app --port 8000`.
- 서울 API 는 출처의 `GUNAME` 으로 구를 정한다. 구가 비어 있는 항목은 대상 지역 미확인이라 검색 목록이 아닌 관리자 검토 대기다.

## 검색 수집(Tavily) — 출처별 JSONL, 2단계 (D12)
구청 사이트 행사는 두 단계다. 1단계만 검색·LLM 을 부르고 2단계는 파일을 읽을 뿐이다. 키는 `TAVILY_SEARCH_KEY`(호스트 env, 없으면 `.env`).
```bash
# 1단계 — 검색 + LLM 추출. 출처(web_sources 의 id)마다, 달마다 실행. 호출 수 상한 --max-calls (기본 30)
uv run python -m domains.kcontext.ingest.events.web_run --source junggu  --month 2026-10 \
  --out var/data/events/web.junggu.jsonl  --collected-at YYYY-MM-DD --max-calls 10 --max-candidates 10
uv run python -m domains.kcontext.ingest.events.web_run --source gangnam --month 2026-10 \
  --out var/data/events/web.gangnam.jsonl --collected-at YYYY-MM-DD --max-calls 10 --max-candidates 10
# 2단계 — 카탈로그 반영(검색·LLM 호출 없음). 파일 이름은 출처별: web.<id>.jsonl
uv run python -m domains.kcontext.catalog update --source junggu_site
uv run python -m domains.kcontext.catalog update --source gangnam_site
```
- 출력은 출처별 `var/data/events/web.<id>.jsonl` 이다(예전 단일 `web.jsonl` 은 `web.<id>.jsonl` 이 없을 때만 읽는다). `junggu_site` ↔ `web_sources/junggu.json`, `gangnam_site` ↔ `gangnam.json`. 수집기는 레코드의 지역을 하나만 쓰므로 4개 구는 구마다 따로 실행한다. 마포는 후보가 없어 서울 API 로 덮는다.
- 검색 결과만 먼저 보려면 `--candidates-only`, 결과를 레포 밖 임시 파일에 저장하려면 `--save-candidates <파일>`, 저장한 후보로 검색 없이 추출만 하려면 `--candidates-file <파일>`. 저장 파일은 레포에 두거나 커밋하지 않는다(D12 ⑦).
- 결과는 `fetched_from="web"`, 출처 등급 C, "검색 수집 · 미확인" 표시이고, 기간이 비면 날짜 검색에 잡히지 않는다. 2026-10-10 실행에서는 7건 모두 기간·구가 비었다.

## 스냅샷 복원 — 키 없이 행사 보기 (D19)
`domains/kcontext/data/snapshots/catalog/` 에 서울 열린데이터광장(공공누리 1유형, 출처 표시) 유래 행사 162건(수집 2026-10-10)이 있다. 건수·범위·이용 조건은 그 폴더의 `SNAPSHOT.md`. Tavily 유래·제보·원응답·키는 담지 않는다.
```bash
uv run python scripts/snapshot_catalog.py --restore --from domains/kcontext/data/snapshots/catalog --to var/catalog   # 대상 폴더가 이미 있으면 --force 로 교체
uv run python scripts/snapshot_catalog.py --from var/catalog --to domains/kcontext/data/snapshots/catalog              # 다시 만들기(서울 API 항목만 남김)
```
스냅샷은 시점 자료다. 스냅샷 날짜에 끝나지 않은 행사만 담으므로 시간이 지나면 오래된 자료가 되어 다시 만든다.

## 환경변수 (이름만. 값은 호스트 셸 env 또는 `.env` — 커밋 금지)
| 이름 | 용도 | 없으면 |
|---|---|---|
| `SEOUL_OPENAPI_KEY` | 서울 열린데이터광장 인증키 | 수집 불가. `--sample` 로 연결 확인만 |
| `DATA_GO_KR_SERVICE_KEY` | 공공데이터포털(TourAPI) | 사용하지 않음(활용가이드 확인 전) |
| `TAVILY_SEARCH_KEY` | 구청 행사 검색 수집(D12) | 해당 경로 사용 불가 |
| `KC_ADMIN_TOKEN` | 관리자 API·화면 | 관리자 API 닫힘 |
| `KC_CATALOG_DIR` · `KC_TARGET_REGION` | 저장 폴더(기본 `var/catalog`) · 지역 id **쉼표 목록**(기본 `jung`) | 기본값(중구 하나) |

## 실제 연동한 출처 / 하지 않은 출처
| 출처 | 제공 방식(확인) | 상태 |
|---|---|---|
| 서울 열린데이터광장 문화행사 정보(OA-15486) | OpenAPI. 공식 가이드·sample 키 응답으로 호출 형식·필드 확인. 매일 1회 갱신 | **연동** — 2026-10-10 전체 수집 8,712건(4개 구). 키 필요 |
| 한국관광공사 TourAPI(data.go.kr 15101578) | 공공데이터포털 페이지에 작업·파라미터·응답 필드가 없음 | **미연동** — 키·활용가이드 확인 필요 |
| 서울 중구청 홈페이지·보도자료 (`junggu_site`) | HTML. D12 검색 수집(Tavily) | **일부** — 2단계 수집으로 4건 반영(기간 없음) |
| 강남구청 홈페이지·강남페스티벌 (`gangnam_site`) | HTML. D12 검색 수집(Tavily) | **일부** — 3건 반영(기간 없음). 서울 API 가 강남도 덮으므로 보조 |
| 중구 공식 SNS(cmsid=15920) | 안내 페이지만 있고 API·RSS 없음. 네이버 블로그는 AI·RAG 접근 금지 | **수동 확인 링크**로 등록(관리자 화면) |
| 중구문화재단(caci.or.kr) | 클라이언트 렌더링, 호출 방식 미문서화 | **수동 확인 링크** |
| 남산골한옥마을 | 서버 렌더링 HTML, robots 허용. 행사 목록 구조 미확인 | **후보(미구현)** |
| 국립정동극장 | robots.txt 가 일반 크롤러 전체 차단 | **수동 확인 링크**(수집하지 않음) |

## 아직 안 된 것 / 확인할 수 없는 것
- **이동시간**: 경로·지도 서비스가 연결돼 있지 않아 모든 제안이 "이동시간 확인 필요"로 나온다(`catalog/routes.py` 의 `RouteProvider` 만 준비). 연결할 서비스(카카오맵 등)의 호출 방식·키·약관을 확인해야 한다.
- **전체 수집**: 2026-10-10 에 서울 API 키로 전체를 받았다(8,712건). 그중 약 98% 는 이미 끝난 행사다. 일일 호출 한도는 데이터셋 페이지에 없다(`[확인 필요]`). 서울 API 에도 없는 행사는 있을 수 있다 — 화면에 "모든 행사"라고 쓰지 않는다.
- **검색 수집 7건은 기간이 없다**(날짜 검색에 안 잡힘). 종료일·회차 없이 시작한 지 1년 넘은 행사는 검색에서 뺀다(D23).
- **검색 속도**: 행사 검색 1회 약 6초(8.7천 건을 매번 읽는다).
- **비정형 공지·이미지·PDF 추출**: 구청 공지 텍스트는 D12 의 `extract.py`(인용 검증)로 추출한다(위 "검색 수집"). 이미지·PDF·포스터는 읽지 않는다. 추출 LLM 호출 실패 3건의 원인은 미확인이다.
- **공간의 이야기**: 구조·검증 규칙(`stories.py`)은 있으나 `data/stories/` 에 검증된 이야기가 아직 없다. 지어내지 않았다.
- 남산골한옥마을·TourAPI 파서, 포스터 이미지 읽기(비전), 실제 브라우저·모바일 화면 확인(테스트는 가짜 DOM).
- 전체 행사 수를 입증할 수 없으므로 화면에 "모든 행사"라고 쓰지 않고 수집 출처와 마지막 확인 시각을 보여 준다.

## 검토 반영과 알려진 한계 (2026-10-07, reviewer 3회)
고친 것
- `?base=` 로 관리자 토큰·일정이 외부로 가던 경로: 같은 출처 경로 또는 `localhost`·`127.0.0.1` 의 **8000 포트**만 받는다(index·events·admin 모두). 두 페이지에 CSP(`connect-src` 는 같은 출처와 루프백만).
  `?base=` 를 바꿔 연 관리자 화면은 저장된 토큰을 자동으로 보내지 않는다.
- 에이전트 역할 자식 프로세스는 `.env` 를 읽지 않는다. 수동 재수집 때만 backend 가 셸 env(없으면 `.env`)에서 **그 출처의 키 하나**를 골라 env 로 넘긴다.
- 외국인 "가능" 오탐, 거주·회원·연령 문구 오탐(주민센터·거주지 무관·회원가입 없이·어린이날 등), 미해결 충돌의 값이 가격 문구·회차·예약 정보로 다시 나타나던 것(이제 같이 비움),
  같은 체계 식별자가 다른 행사의 병합, 낮은 등급(제보·SNS·AI) 값의 유입(예약·언어·참여조건·휴무·시간), 제보 사유의 공개 노출, 시작일만으로 "종료" 단정, 종료일을 모를 때 나머지 여행 날짜를 "열리지 않음"으로 제외하던 것,
  주소 속 다른 도시의 같은 구 이름, 장소 이름만 다른 같은 장소의 가짜 충돌, 카탈로그 쓰기 파일 잠금, 입력 화이트리스트, 일정 localStorage 검증, 데모/실제 저장 키 분리 등.

**알려진 한계 — 아직 안 된 것**
- **속도 제한 없음**: 공개 API 는 요청마다 파이썬 서브프로세스를 띄운다. 공개 배포 전에 앞단(리버스 프록시)에서 제한해야 한다.
- **요청 크기 제한은 부분적**: `Content-Length` 가 있는 요청만 256KB 로 자른다(chunked 본문은 통과). 413 응답에는 CORS 헤더가 없어 브라우저에는 network 오류로 보일 수 있다. 앞단 제한이 필요하다.
- **원격 배포**: CSP 가 같은 출처와 루프백 연결만 허용한다. 원격 호스트에서 열면 같은 출처의 `/api` 프록시를 둬야 한다(기본 backend 주소도 그때는 `/api`). `frame-ancestors` 는 meta CSP 로 지정할 수 없어 정적 서버 헤더로 줘야 한다. index.html 에는 CSP 가 없다(지도 SDK 때문).
- **병합 후보 검토 없음**: 같은 행사가 두 번 게시됐는데 외부 id 가 다르거나 행사명이 많이 다르면 목록에 두 번 나오고 독립 출처 수가 낮게 잡힌다. "병합 후보"를 관리자 목록에 띄우는 기능은 아직 없다.
- **수기 공지**: `kind="manual"` 은 신뢰 등급 밖이라 예약·참여조건을 채우거나 취소를 확정하지 못한다. 구청 공지를 사람이 옮겨 적는 용도가 생기면 원문 종류와 입력 방식을 나눠야 한다.
- 관리자는 한 토큰·한 신원(`KC_REVIEWER_ID`)이고 `core.audit` 기록이 없다. 관리자 토큰은 16자 이상이어야 서버가 뜬다.
- **지역 판정**: 서울 API 행사는 출처의 `GUNAME` 만 쓴다(주소 필드가 없어 주소와의 교차 검증은 제보 경로에서만 돈다). `GUNAME` 이 개최 장소 기준인지는 데이터셋 페이지에 명시가 없다.
- 서울시 API 호출 주소가 http 다(공식 가이드). https 지원 여부는 확인하지 못했다.
- 사라진 행사는 취소가 아니라 "마지막 확인이 오래됨"(72시간) 표시로만 드러난다. `append_changes` 는 덧붙이기라 쓰는 도중 읽으면 반쯤 쓴 줄을 만날 수 있다.
- `CatalogStore.lock()` 의 재진입 깊이는 인스턴스 필드(스레드 로컬 아님)다. 지금은 요청마다 새 프로세스라 문제없지만, 한 인스턴스를 여러 스레드가 공유하면 안 된다.
