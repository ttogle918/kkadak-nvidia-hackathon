# 중구 행사 카탈로그 — 실행·설정·현황 (2026-10-07)

사용자 흐름: 여행 날짜·숙소·기존 일정을 입력 → 중구에서 열리는 행사와 참여 방법 확인 → 기존 일정에 추가·취소.
결정 근거: `docs/DECISIONS.md` D13(카탈로그), D12(검색 수집), D7·D10(호스트 수집·프로세스 분리).

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

## 환경변수 (이름만. 값은 호스트 셸 env 또는 `.env` — 커밋 금지)
| 이름 | 용도 | 없으면 |
|---|---|---|
| `SEOUL_OPENAPI_KEY` | 서울 열린데이터광장 인증키 | 수집 불가. `--sample` 로 연결 확인만 |
| `DATA_GO_KR_SERVICE_KEY` | 공공데이터포털(TourAPI) | 사용하지 않음(활용가이드 확인 전) |
| `TAVILY_SEARCH_KEY` | 구청 행사 검색 수집(D12) | 해당 경로 사용 불가 |
| `KC_ADMIN_TOKEN` | 관리자 API·화면 | 관리자 API 닫힘 |
| `KC_CATALOG_DIR` · `KC_TARGET_REGION` | 저장 폴더(기본 `var/catalog`) · 지역 id(기본 `jung`) | 기본값 |

## 실제 연동한 출처 / 하지 않은 출처
| 출처 | 제공 방식(확인) | 상태 |
|---|---|---|
| 서울 열린데이터광장 문화행사 정보(OA-15486) | OpenAPI. 공식 가이드·sample 키 응답으로 호출 형식·필드 확인. 매일 1회 갱신 | **연동**(키 필요, 전체 수집은 키 발급 후) |
| 한국관광공사 TourAPI(data.go.kr 15101578) | 공공데이터포털 페이지에 작업·파라미터·응답 필드가 없음 | **미연동** — 키·활용가이드 확인 필요 |
| 서울 중구청 홈페이지·보도자료 | HTML. D12 검색 수집(Tavily) | **일부** — LLM 추출기(T223) 연결 전엔 레코드를 만들지 못함 |
| 중구 공식 SNS(cmsid=15920) | 안내 페이지만 있고 API·RSS 없음. 네이버 블로그는 AI·RAG 접근 금지 | **수동 확인 링크**로 등록(관리자 화면) |
| 중구문화재단(caci.or.kr) | 클라이언트 렌더링, 호출 방식 미문서화 | **수동 확인 링크** |
| 남산골한옥마을 | 서버 렌더링 HTML, robots 허용. 행사 목록 구조 미확인 | **후보(미구현)** |
| 국립정동극장 | robots.txt 가 일반 크롤러 전체 차단 | **수동 확인 링크**(수집하지 않음) |

## 아직 안 된 것 / 확인할 수 없는 것
- **이동시간**: 경로·지도 서비스가 연결돼 있지 않아 모든 제안이 "이동시간 확인 필요"로 나온다(`catalog/routes.py` 의 `RouteProvider` 만 준비). 연결할 서비스(카카오맵 등)의 호출 방식·키·약관을 확인해야 한다.
- **전체 수집**: 서울시 API 키가 없어 실제 중구 행사 전체를 받지 못했다. sample 키 5행에는 중구 행사가 없었다. 일일 호출 한도는 데이터셋 페이지에 없다(`[확인 필요]`).
- **비정형 공지·이미지·PDF 추출**: AI 추출은 D12 의 `extract.py`(인용 검증) 구조만 있고 LLM 연결(T223)이 없다. 근거 필드(`ai_extracted`·`location`)와 검토 대상 표시는 준비됐다.
- **공간의 이야기**: 구조·검증 규칙(`stories.py`)은 있으나 `data/stories/` 에 검증된 이야기가 아직 없다. 지어내지 않았다.
- 남산골한옥마을·TourAPI 파서, 포스터 이미지 읽기(비전), 실제 브라우저·모바일 화면 확인(테스트는 가짜 DOM).
- 전체 행사 수를 입증할 수 없으므로 화면에 "모든 행사"라고 쓰지 않고 수집 출처와 마지막 확인 시각을 보여 준다.

## 검토 반영과 알려진 한계 (2026-10-07, reviewer)
- 고친 것: `?base=` 로 관리자 토큰이 새는 경로(주소 검증 + CSP), 외국인 "가능"·거주·회원·연령 문구 오탐, 미해결 충돌 값을 사실처럼 보이던 것(이제 비움),
  같은 체계 식별자가 다른 행사의 병합, 낮은 등급(제보·SNS·AI) 값의 사실 필드 유입, 제보 사유의 공개 노출, 시작일만으로 "종료" 단정,
  주소 속 다른 도시의 같은 구 이름, 원자적 쓰기에 파일 잠금, 요청 크기 제한·입력 화이트리스트, 일정 localStorage 검증, 데모/실제 저장 키 분리 등.
- **속도 제한은 없다**: 공개 API 는 요청마다 파이썬 서브프로세스를 띄운다. 공개 배포 전에 앞단(리버스 프록시)에서 제한해야 한다.
- 관리자는 한 토큰·한 신원(`KC_REVIEWER_ID`)이다. 사람별 신원·감사(`core.audit`) 기록은 아직 없다.
- 서울시 API 는 공식 가이드가 http 주소를 쓴다(키가 평문으로 간다). https 지원 여부는 확인하지 못했다.
- 서울 API 의 `GUNAME` 이 개최 장소 기준인지는 데이터셋 페이지에 명시가 없다. 주소와 어긋나면 지역을 확정하지 않는다.
- 사라진 행사는 취소가 아니라 "마지막 확인이 오래됨" 표시(72시간)로만 드러난다.
