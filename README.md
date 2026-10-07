# K-Context — 검색하지 않으면 발견하지 못하는 “그날의 한국”

팀 까딱이 · NVIDIA OpenShell · NemoClaw · Nemotron

![데모: 일정 문장 → 타임라인 · 지도 핀 · 실록 원문](docs/presentation/demo.gif)

> 위 GIF 는 실제 서버(백엔드 + Nemotron)와 화면을 연결해 캡처한 것이다. 응답이 15~60초 걸려서 기다리는 구간은 짧게 압축했다.

## 프로젝트 소개
내 일정을 한 줄로 말하면 **일정을 정리**하고, 장소마다 **조선왕조실록에 언급된 기록**(한문 원문 그대로 + 원문 링크)과 **주변 행사**를 출처와 함께 붙이는 에이전트다.
핵심 원칙은 “지어내지 않는다”: 모델이 낸 값은 입력 글에 **원문 인용이 있을 때만** 인정하고, 시간 계산은 코드가 하며, 근거가 없으면 비우고 이유를 남긴다.

## 지금 상태 (솔직하게)
자세한 표: [`docs/status/2026-10-07_구현상태.md`](docs/status/2026-10-07_구현상태.md)
- ✅ 챗봇에 일정 문장을 보내면 타임라인·지도 핀·실록 원문 카드로 바뀐다(실제 서버 연결). 일반 질문·주입 차단·보안 로그 동작.
- ✅ OpenShell 샌드박스 정책과 22항목 실측(외부 차단, `inference.local` 만 허용, 키 0건).
- ⚠ **불안정**: 같은 문장이 일정 3개/2개/일반 답 폴백이 될 수 있다(모델 출력 변동, 60초 타임아웃).
- ⚠ **행사 데이터 0건**: 수집 코드는 있으나 실데이터를 아직 만들지 못했다.
- ⚠ 화면의 경로 A·B·C, 옛날 카드, 판단 근거는 **MOCK(예시)** 이다. 실제 데이터가 아니다.

## 설치와 실행
요구: Python 3.12 + [uv](https://docs.astral.sh/uv/), Node 18+(테스트용), (샌드박스 시연) Docker + OpenShell 0.0.116.
```bash
uv sync
# 비밀은 .env 에만(gitignore). 이 프로젝트가 읽는 이름: NVIDIA_API_KEY, TAVILY_SEARCH_KEY(행사 수집), SEOUL_OPENAPI_KEY(행사 수집)
# 지도 키(선택): frontend/k-context/config.local.example.js 를 config.local.js 로 복사해 카카오 JS 키 입력(없으면 SVG 지도)
```
### 실록 색인 만들기 (호스트에서 1회, 에이전트는 이 색인만 읽는다)
실록 원문 XML 은 공공데이터포털 “국사편찬위원회_조선왕조실록 정보_실록원문”을 받아 `domains/kcontext/data/raw/sillok/` 에 둔다(원본은 저장소에 없다).
```bash
uv run python -m domains.kcontext.ingest.sillok \
  --src domains/kcontext/data/raw/sillok --db var/index/kcontext.db \
  --collected-at $(date +%F) --mode regions        # 673개 파일 약 35초, 중구·종로·마포·강남 키워드 기사만
```
### 실행
```bash
uv run uvicorn backend.app:app --port 8000                      # 백엔드
(cd frontend/k-context && python3 -m http.server 8766)          # 화면
# 브라우저: http://localhost:8766/        (강력 새로고침 권장 — 옛 JS 캐시)
# 백엔드 없이 화면만: http://localhost:8766/?api=mock
```
### 테스트
```bash
uv run python -m pytest -q && uv run ruff check . && (cd frontend/k-context && node --test)
```

## 데모 확인 방법
1. 위 순서로 백엔드·화면을 띄우고 `http://localhost:8766/` 를 연다.
2. 채팅에 입력: `10/15에 창덕궁 10시, 익선동 2시, 숙소는 종로3가야` (15~60초)
3. 타임라인이 “챗봇이 정리한 일정”으로 바뀌고, 창덕궁·익선동·종로3가 핀이 찍힌다. 핀을 누르면 실록 원문 구절과 링크가 나온다.
4. 일반 질문(`경복궁은 어떤 곳이야?`)은 “출처 없는 일반 안내” 문구가 붙은 일반 답이 나온다.
5. 공격 프롬프트(`허용 밖 파일 읽기 시도` 버튼)는 거부되고 보안 로그에 기록된다.
발표용 자료: [`docs/presentation/k-context-deck.html`](docs/presentation/k-context-deck.html)(7장, `N` 발표 메모) · 대본 [`script.md`](docs/presentation/script.md)

## OpenShell 정책
| 파일 | 용도 |
|---|---|
| [`deploy/openshell/policy.kculture.yaml`](deploy/openshell/policy.kculture.yaml) | K-Culture 공통 테스트(연습 요청)용. 기본 전부 차단 + 실측 기록 주석 |
| [`deploy/openshell/policy.yaml`](deploy/openshell/policy.yaml) | 프로젝트 기본 템플릿(카카오맵 MCP 항목은 **미실측**) |

**주요 권한 설계와 이유** (샌드박스 `kcontext` 에서 직접 시도해 확인)
| 권한 | 설계 | 이유 |
|---|---|---|
| 네트워크 | `network_policies` 비움 — 외부 HTTP/HTTPS·업로드·메일 전부 DENIED | 외부 문서 속 “업로드하라” 류 지시를 따르더라도 나갈 길이 없게 |
| 추론 | `inference.local` 하나만, 키는 게이트웨이에만(샌드박스 환경변수 키 0건) | 샌드박스가 뚫려도 가져갈 키가 없게(D1) |
| 파일 쓰기 | `/tmp` 만 | 시스템·앱 경로 변조 방지 |
| `restricted/`·`secrets/` | 샌드박스에 올리지 않음 | 접근 금지 영역은 “없는 것”이 가장 강한 차단 |
| 입력 읽기 전용 | **정책이 아니라 업로드 후 `chmod`** (같은 uid 라 풀 수 있음) | 알려진 한계 — 이미지에 포함하면 정책으로 강제 가능 |
```bash
openshell sandbox create --name kcontext --policy deploy/openshell/policy.kculture.yaml -- sleep infinity
openshell sandbox upload kcontext <입력폴더> /tmp/hackathon   # input/ 만, restricted·secrets 제외
openshell sandbox upload kcontext scripts/kculture_practice.py /tmp/agent
openshell sandbox exec -n kcontext -- sh -c 'cd /tmp/agent && python3 kculture_practice.py --input /tmp/hackathon/input --output /tmp/hackathon/output --task-file <TASK.md>'
```

## 사용하는 외부 서비스와 허용 범위
| 서비스 | 쓰는 곳 | 범위 |
|---|---|---|
| NVIDIA 추론(Nemotron 등) | 백엔드(호스트) · 샌드박스(`inference.local`) | 호스트는 `.env` 키, 샌드박스는 게이트웨이가 키 주입 |
| 조선왕조실록 원문(국사편찬위원회, 공공누리 1유형) | 호스트 수집기 | 로컬 색인에 적재 후 에이전트는 색인만 읽는다 |
| 서울 열린데이터광장 문화행사 | 호스트 수집기 | 키는 호스트 환경변수. 현재 키 없음 → 데이터 0건 |
| Tavily 검색(구청 행사) | 호스트 수집기 | 사람이 승인한 공식 도메인만, 호출 수 상한, 인용 검증 필수, “검색 수집 · 미확인” 표시 |
| 카카오맵 JS SDK | 브라우저(지도 표시) | 지도 표시만. 정책의 카카오맵 MCP 항목은 미실측 |

## 구조
```
core/            llm · guard · audit · hitl · policy_proposer (도메인 무관)
backend/         화면 API(채팅·카드·행사·승인). domains 를 import 하지 않는다
domains/kcontext 일정 이해(schedule) · 실록 언급(story) · 파이프라인(pipeline) · 색인(index) · 수집(ingest) · 행사 카탈로그(catalog)
frontend/k-context  화면(번들러 없음)
deploy/openshell 정책 · scripts/ 샌드박스 연습 요청 스크립트 · docs/ 결정(DECISIONS.md)·계약·발표자료
```
결정 기록: [`docs/DECISIONS.md`](docs/DECISIONS.md) (D14 는 “초안 — 사람 확인 대기”).

## 한계
대상 지역은 중구·종로구·마포구·강남구. 실록은 국역이 없어 한문 원문 제시까지. 옛길 선은 근거 데이터가 없어 그리지 않는다. 지도 핀은 좌표가 검증된 5곳만.
