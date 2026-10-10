# K-Context — 검색하지 않으면 발견하지 못하는 “그날의 한국”

팀 까딱이 · NVIDIA 호스팅 추론 API(gpt-oss-20b) · (선택) NVIDIA OpenShell 샌드박스 · Nemotron(샌드박스 경로)

> **필수 / 선택**: 데모는 호스트에서 backend + 화면만 띄우면 돈다. OpenShell 샌드박스는 해커톤 때 만든 **선택 기능**이다(D20). 무엇이 필수인지는 [`deploy/README.md`](deploy/README.md).

## 프로젝트 소개
챗봇에 일정을 한 문장으로 말하면(예: `10/15에 창덕궁 10시, 익선동 2시, 숙소는 종로3가야`) **일정으로 정리**하고, 같은 동네에 대해 **조선왕조실록에 언급된 기록**(한문 원문 그대로 + 원문 링크)을 붙이고, 그 날짜 근처에 열리는 **실제 행사**(서울 열린데이터 등 출처 표시)를 함께 보여 주는 에이전트다.

원칙은 둘이다.
- **지어내지 않는다**: 모델이 낸 값은 입력 글에 **원문 인용이 있을 때만** 인정하고, 시간 계산·좌표·실록 검색은 코드/색인이 한다. 근거가 없으면 비우고 이유를 남긴다.
- **확인이 필요한 것은 드러낸다**: 오전/오후 가정, 연도 추정, 이동시간 없음, 검색 수집·미확인 행사는 화면에 “확인 필요”로 표시한다.

## 지금 상태 (솔직하게, 2026-10-10)
자세한 표: [`docs/status/2026-10-10_구현상태.md`](docs/status/2026-10-10_구현상태.md) · 안정성 측정: [`eval/BASELINE.md`](eval/BASELINE.md)(“최종” 절) · 행사 수집 보고서: [`docs/status/events_data_2026-10-10.md`](docs/status/events_data_2026-10-10.md)

- ✅ **실제 모드에 MOCK 0**: 타임라인·지도·카드·이동 구간·판단 근거는 `POST /api/messages` 가 돌려준 묶음(`kc-chat-bundle/v2`)에서만 그린다(D17). 예시 데이터는 `?api=mock` 에만 있다.
- ✅ **안정성 측정(최종, 검수 전 기대값 기준)**: 정답 일치 파이프라인 **49/60**·API **24/30**, 앵커 재현율 **0.93 / 0.96**(정밀도 1.0), 일반 답 폴백 **0**, 지연 p95 **12초 / 18초**. 캐시에 저장된 결과의 재요청 변동은 0(D15 보충 3).
- ⚠ **변동 목표 미달(이월)**: 같은 문장을 첫 요청에서 보내면 앵커 개수가 흔들리는 케이스가 파이프라인 7/20·API 3/10(목표 4·2). 폴백이 아니라 일부 앵커를 놓치는 것이다. 평가셋 검수(H10) 뒤 재판정한다.
- ✅ **행사 실데이터(4개 구)**: 서울 열린데이터광장 API 로 8,712건(종로 4,918 · 중구 1,911 · 마포 1,167 · 강남 595 · 구 미확인 121)과 구청 사이트 검색 수집 7건. 데모 문장(10/15)에서 날짜가 맞는 행사 **99건**이 나온다(종료일 없이 1년 넘게 지난 20건은 D23 으로 제외). **이것이 모든 행사가 아니다.**
- ✅ 일반 질문·주입 차단·보안 로그·사람 승인 API 동작. (선택) OpenShell 샌드박스 22항목 실측은 해커톤 당시 결과 그대로다.

### 남은 한계
- 지도 핀은 좌표가 확인된 **장소 5곳**(창덕궁·익선동·경복궁·광화문·종로3가)만. 그 밖은 목록에만 나온다.
- **한글→한자 별칭 사전이 비어 있다**(데이터 없음). 본문에 한자로만 나오는 실록 기사는 못 찾는다.
- **이야기 길(경로 A·B·C) 없음**(D18) — 근거 좌표가 있는 이야기 레코드가 0건이라 “일정 순서 이동 구간”(직선 거리)만 보인다.
- **이동시간 공급자 없음**(D16) — 도보 시간은 “이동시간 확인 필요”로 둔다. 직선 추정은 판정에 쓰지 않는다.
- 평가셋은 **사람 검수 전**(`reviewed: false`, H10). 정답 일치율은 기대값이 틀렸을 수 있다.
- 일부 문장은 첫 요청에서 흔들린다(위 변동 목표 미달). 같은 문장은 한 번 완전한 결과가 나오면 캐시로 고정된다.
- 행사 검색 1회에 **약 6초**(8.7천 건을 매번 읽는다).
- 검색 수집 **7건은 날짜가 없어** 날짜 기준 검색에 잡히지 않는다(관리자 검토 대기).
- 실록은 국역이 없어 한문 원문 제시까지. 서울 API 행사의 약 98%는 이미 끝난 과거 행사다(날짜 범위로 걸러낸다).

## 기능별 데모 (촬영 장면)
> 아래 5장면은 2026-10-10 **실제 서버 연결 상태**(`bash scripts/kc_demo.sh`, 여행 기간 `?trip=2026-10-15..2026-10-18`)에서 헤드리스 Chromium 으로 캡처했다. 옛 GIF 는 아래 “해커톤 당시” 절로 내렸다.

| # | 장면 | 파일 | 상태 |
|---|---|---|---|
| ① | 일정 문장 → 타임라인 · 지도 핀 · 이동 구간 · 판단 근거 | `docs/demo/s3-01-schedule.png` | 캡처됨 |
| ② | 같은 문장 재요청 → “이전 결과 재사용” | `docs/demo/s3-02-cache-reuse.png` | 캡처됨 |
| ③ | 공격 프롬프트 차단 → 서버 보안 로그(거부 기록, ⚙ 패널) | `docs/demo/s3-03-security-log.png` | 캡처됨 |
| ④ | 4개 구 행사 카드(출처·기간·확인 필요 표시) | `docs/demo/s3-04-events.png` | 캡처됨 |
| ⑤ | `?api=mock` — MOCK 딱지가 보이는 예시 모드 | `docs/demo/s3-05-mock.png` | 캡처됨 |

**① 일정 문장 → 타임라인 · 지도 핀 · 이동 구간 · 판단 근거**
![일정](docs/demo/s3-01-schedule.png)

**② 같은 문장 재요청 → “이전 결과 재사용”**
![재사용](docs/demo/s3-02-cache-reuse.png)

**③ 공격 프롬프트 차단 → 서버 보안 로그**
![보안 로그](docs/demo/s3-03-security-log.png)

**④ 4개 구 실제 행사와 행사 판단 근거**
![행사](docs/demo/s3-04-events.png)

**⑤ `?api=mock` 예시 모드(MOCK 딱지)**
![예시 모드](docs/demo/s3-05-mock.png)

### 해커톤 당시 (2026-10-07, MOCK 포함)
아래 GIF 는 연결 전 상태에서 찍었다. 화면의 경로 A·B·C, 옛날 카드, 판단 근거에 **MOCK** 딱지가 붙은 곳은 가짜 데이터였고, 지금 실제 모드에서는 나오지 않는다. 행사는 0건이었다.

**1. 일정 문장 → 타임라인 · 지도 핀 · 실록 원문** (응답 54초)
![일정 흐름](docs/demo/01-schedule-flow.gif)

**2. 일반 질문 · 공격 프롬프트 차단 · 보안 로그**
![보안](docs/demo/02-chat-attack-securitylog.gif)

**3. 행사 찾기 — 실제 서버(당시 0건)**
![행사 실서버](docs/demo/03-events-real-server-empty.gif)

**4. 행사 찾기 — 데모 모드(`events.html?api=mock`)**
![행사 데모](docs/demo/04-events-demo-mode.gif)

## 현재 상태 다이어그램 (AI 가 어떻게 가는지)
[HTML 원본 열기](docs/diagram/system-state.html)(저장소를 받아 브라우저로 열면 다크 모드·확대 지원). 색: 초록=동작 확인 · 파랑=AI(모델) 호출 · 노랑=부분/미검증 · 빨강=미구현/데이터 없음 · 회색 점선=**MOCK(`?api=mock` 경로에만)**. 같은 이름의 PNG(`docs/diagram/system-state.png`)는 2026-10-10 새 HTML 에서 다시 캡처했다.

![현재 상태 다이어그램](docs/diagram/system-state.png)
- **흐름**: 채팅 → 입력 가드 → 일정 판별 게이트 → 파이프라인(일정 이해 LLM · 재시도 · 캐시 → 좌표·조사 → 실록 언급 → 근거·이동 구간) → 행사 검색(카탈로그) → 묶음 v2 → 화면.
- **AI 가 하는 일**: 일정 글에서 후보를 뽑는 것(일정 이해)과 일반 질문 답변. 그 값은 **원문 인용이 확인될 때만** 쓰고, 시간 계산·좌표·실록 검색은 코드/색인이 한다. 실록은 번역하지 않고 원문 그대로 보여 준다.
- **에이전트 파이프라인은 백엔드와 다른 프로세스**로 돌고 파일(`bundle.json`)로만 주고받는다. 외부 자료는 호스트 수집기가 미리 모아 색인·카탈로그에 두고 에이전트는 로컬 자료만 읽는다.
- (선택) 샌드박스 경로는 외부 접속이 전부 막히고 `inference.local` 만 열려 있다(22항목 실측). 제품 실행에는 필요 없다.

## 사용한 NVIDIA 기술
| 기술 | 구분 | 어디에 어떻게 | 확인 방법 |
|---|---|---|---|
| **NVIDIA 호스팅 추론 API** (`integrate.api.nvidia.com`) | **필수** | 제품 코드의 LLM 호출 — 챗봇·일정 이해·행사 추출. 모델 **`openai/gpt-oss-20b`**. 일정 이해(`schedule`)에는 **temperature 0 · reasoning_effort low** 를 쓴다(D15 보충) | `deploy/llm.chat.yaml` (`CHAT_MODEL`·`SCHEDULE_MODEL` 로 덮어씀), 파라미터 실측 `docs/spikes/llm_params.md` |
| **OpenShell** (0.0.116) | 선택 | 샌드박스 `kcontext`, 기본 전부 차단 정책, `inference.local` 게이트웨이, DENIED/ALLOWED 로그, 22항목 실측(해커톤 당시) | `openshell sandbox list`, `openshell logs kcontext` |
| **Nemotron** (`nvidia/nemotron-3-super-120b-a12b`) | 선택 | **샌드박스 경로 한정**: 공통 테스트 에이전트가 `inference.local` 로 호출. 게이트웨이 provider `nvidia-prod` 에 설정 | `openshell inference get` · 샌드박스에서 호출한 응답의 `model` 필드로 확인 |
| NVIDIA 문서 MCP · Agent Skills 카탈로그 | 개발 도구 | 개발 중 OpenShell·NemoClaw 동작을 문서로 확인(`.claude/skills/`, `nemoclaw-docs`) | 제품 기능 아님 |

**시험만 하고 제품에는 쓰지 않은 것**: Nemotron 임베딩 모델(`nemotron-3-embed-1b`, `llama-nemotron-embed-vl-1b-v2`) 비교 시험(`docs/spikes/sillok_embedding.md`) — 임베딩은 쓰지 않기로 했다.
**쓰지 않은 것**: NemoClaw/OpenClaw 에이전트 런타임(CLI·문서만 확인, 샌드박스 안 에이전트는 표준 라이브러리 스크립트), 로컬 NIM·리랭커·NeMo Guardrails·GPU 가속(이 개발 PC 에 GPU 없음; 입력 가드는 자체 규칙 `core/guard`), 비전 모델.
> 일정 이해·챗봇의 모델을 Nemotron 으로 바꾸는 것은 `CHAT_MODEL` 한 줄이지만, 안정성 기준선이 gpt-oss-20b 기준이라 결과를 다시 확인해야 해서 하지 않았다.

## 환경 설치 방법 (Environment setup)
### 필수
요구: Python 3.12 + [uv](https://docs.astral.sh/uv/). Node 18+ 는 개발·테스트(`node --test`)용으로 데모 실행에는 필요 없다. Docker·OpenShell 은 **필요 없다**(아래 "선택" 절에서만 쓴다).
```bash
uv sync                                  # Python 의존성(pyproject.toml, uv.lock)
cp .env.example .env                     # NVIDIA_API_KEY 를 채운다(.env 는 gitignore)
cp frontend/k-context/config.local.example.js frontend/k-context/config.local.js   # 선택: 카카오 지도 JS 키 입력(없으면 SVG 지도)
```
비밀은 **`.env`(gitignore) 또는 셸 환경변수에만** 둔다(값은 문서·로그에 적지 않는다). 이름만 정리하면 다음과 같다. 허용 목록 로더가 정해진 이름만 읽는다.
| 이름 | 구분 | 용도 | 없으면 |
|---|---|---|---|
| `NVIDIA_API_KEY` | **필수** | 호스팅 추론 API(챗봇·일정 이해) | 일정 이해가 돌지 않는다 |
| `SEOUL_OPENAPI_KEY` | 선택 | 서울 열린데이터광장 행사 수집 | 수집 불가. 아래 스냅샷 복원으로 행사를 볼 수 있다 |
| `TAVILY_SEARCH_KEY` | 선택 | 구청 사이트 행사 검색 수집(D12) | 검색 수집 불가. 서울 API 만으로 행사가 나온다 |
| `KC_TARGET_REGION` | 선택 | 행사 대상 구 id 쉼표 목록(기본 `jung`) | 중구 하나만 |

행사 대상 지역 예시(4개 구 — id 는 `domains/kcontext/data/regions/` 의 `jung`·`jongno`·`mapo`·`gangnam`):
```bash
export KC_TARGET_REGION=jung,jongno,mapo,gangnam     # 또는 .env 에 한 줄
```

**실록 색인 만들기** (필수, 호스트에서 1회 — 에이전트는 이 색인만 읽는다). 원문 XML 은 공공데이터포털 “국사편찬위원회_조선왕조실록 정보_실록원문”을 받아 `domains/kcontext/data/raw/sillok/` 에 둔다(원본은 저장소에 없다).
```bash
uv run python -m domains.kcontext.ingest.sillok \
  --src domains/kcontext/data/raw/sillok --db var/index/kcontext.db \
  --collected-at $(date +%F) --mode regions        # 673개 파일 약 35초 → 중구·종로·마포·강남 키워드 기사 4,822건·청크 7,713개
```
**실행** — 한 번에(권장):
```bash
bash scripts/kc_demo.sh                     # backend(8000)+화면(8766) 기동. Ctrl-C 로 종료하면 자기가 띄운 프로세스만 정리
bash scripts/kc_demo.sh --check             # 점검만: uv · 색인 · NVIDIA_API_KEY 있음/없음(값 출력 안 함) · 행사 카탈로그. 색인이 없으면 ingest 명령을 안내하고 종료코드 1
bash scripts/kc_demo.sh --restore-snapshot  # 행사 스냅샷(D19)을 var/catalog 로 복원. 대상이 이미 있으면 거부
bash scripts/kc_demo.sh --smoke             # 띄워서 8000·8766 응답만 확인하고 바로 종료(LLM 호출 없음)
```
스크립트는 backend 를 `KC_TARGET_REGION=jung,jongno,mapo,gangnam` 으로 127.0.0.1 에 띄운다. 포트가 이미 쓰이면 안내만 하고 끝내며 다른 프로세스를 죽이지 않는다. 기동 뒤 URL 세 개(실제 · `?api=mock` · `?trip=2026-10-15..2026-10-18`)와 데모 팁을 출력한다. 키가 없으면 캐시된 문장과 `?api=mock` 만 동작한다.
같은 일을 손으로 하면:
```bash
KC_TARGET_REGION=jung,jongno,mapo,gangnam uv run uvicorn backend.app:app --port 8000   # 백엔드
(cd frontend/k-context && python3 -m http.server 8766)                                  # 화면 (강력 새로고침 권장: 옛 JS 캐시)
```
- 실제 서버 화면: <http://localhost:8766/> (행사만: <http://localhost:8766/events.html>)
- 예시(MOCK) 모드: <http://localhost:8766/?api=mock> — 백엔드 없이도 뜨며, MOCK 딱지가 붙는다.
- 여행 기간 지정: `http://localhost:8766/?trip=2026-10-15..2026-10-18` (`?trip=YYYY-MM-DD..YYYY-MM-DD`, 화면 입력보다 우선, D22). 선택이며 문장에 날짜가 있으면 행사 검색은 문장의 날짜 범위를 먼저 쓴다.
- **데모 전 팁(캐시 채우기)**: 같은 문장을 첫 요청에서 보내면 앵커가 2~3개로 흔들릴 수 있다. 완전한 결과(`QUOTE_NOT_FOUND` 없음)가 한 번 나오면 `var/cache/schedule/` 에 저장돼 이후엔 같은 결과가 “이전 결과 재사용”으로 나온다. 데모 문장을 미리 한 번 이상 보내 3개가 나온 것을 확인해 두면 안전하다(불완전한 결과는 저장되지 않으니 3개가 안 나오면 다시 보낸다).
### 선택
- 행사 수집(키 필요): `SEOUL_OPENAPI_KEY`·`TAVILY_SEARCH_KEY` — 순서와 명령은 [`docs/guides/EVENTS_CATALOG.md`](docs/guides/EVENTS_CATALOG.md), 주기 수집은 [`deploy/catalog/README.md`](deploy/catalog/README.md)
- **키 없이 행사 보기(D19)**: 저장소에 서울 열린데이터광장(공공누리 1유형, 출처 표시) 유래 행사 162건 스냅샷이 있다(`domains/kcontext/data/snapshots/catalog/`, 수집일 2026-10-10). `var/catalog` 로 복원하면 키 없이 행사 카드를 볼 수 있다. 검색(Tavily) 유래 자료는 약관 확인 전이라 스냅샷에 없다. 스냅샷은 시점 자료라 이후 바뀌었을 수 있다.
  ```bash
  bash scripts/kc_demo.sh --restore-snapshot     # 둘 중 하나만 실행한다(같은 일)
  # 또는: uv run python scripts/snapshot_catalog.py --restore --from domains/kcontext/data/snapshots/catalog --to var/catalog   # 대상이 이미 있으면 --force
  ```
- OpenShell 샌드박스 시연: 아래 [선택: OpenShell 샌드박스 시연](#선택-openshell-샌드박스-시연) — Docker + OpenShell 0.0.116 + 게이트웨이(`scripts/gateway_setup.sh`)

## 학습 방법 (Training instructions)
**모델을 학습·파인튜닝하지 않는다.** NVIDIA 호스팅 추론 API 의 모델(호스트: `openai/gpt-oss-20b`, 선택한 샌드박스 경로: 게이트웨이의 Nemotron)을 호출만 하고, 가중치는 바꾸지 않는다. “학습”에 해당하는 준비는 아래 둘이다.
1. **색인 구축**(위 `ingest.sillok` 명령): 실록 원문을 청크로 나눠 로컬 SQLite FTS5 색인에 적재한다. 벡터 임베딩은 쓰지 않는다(시험 결과 `docs/spikes/sillok_embedding.md`, 쓰지 않기로 결정).
2. **프롬프트**(코드에 있다, 바꾸면 테스트로 확인):
   - 일반 챗봇: `backend/chat.py` `SYSTEM_PROMPT`
   - 일정 이해: `domains/kcontext/schedule/understand.py` `SYSTEM_PROMPT`
   - 행사 추출(구청 공지): `domains/kcontext/ingest/events/extract.py` `SYSTEM_PROMPT`
   - 공통 테스트 에이전트(선택 경로): `scripts/kculture_practice.py` `SYSTEM`
   - 모델·한도 설정: `deploy/llm.chat.yaml`(env `CHAT_MODEL` 로 덮어씀)

## 평가 절차 (Evaluation steps)
### 필수
```bash
# 1) 자동 테스트(회귀) — 최근 실행(2026-10-10, Sprint 3 Stage 6): pytest 1,937 · 프론트 node 360 · ruff 통과 (건수는 이후 늘 수 있다 — 러너 출력이 기준)
uv run python -m pytest -q && uv run ruff check . && (cd frontend/k-context && node --test)
# 2) 평가셋 형식 검증 후 결정적 실행(LLM 호출 없음) — 게이트·실록 언급·판정·주입 차단
uv run python eval/kc.py validate
uv run python eval/kc.py run --check --known-failures eval/BASELINE.md
# 3) 안정성 측정(LLM 실호출, 비용 있음 — 호출 수 상한 기본 210) — 방법: eval/README.md, 기준 수치: eval/BASELINE.md "최종"
uv run python eval/kc.py stability --layer pipeline --runs 3 --label mine      # --layer api 는 backend(8000)가 떠 있어야 한다
```
평가셋은 아직 사람 검수 전(`reviewed: false`)이다. 일정 흐름은 같은 문장이 첫 요청에서 결과가 달라질 수 있어(모델 변동), 데모 전에 여러 번 돌려 확인한다.

### 선택 — OpenShell 샌드박스 실측과 공통 테스트
```bash
# 22항목(외부 접속·쓰기·키·추론). 방법과 결과: deploy/openshell/policy.kculture.yaml 하단 주석
openshell sandbox create --name kcontext --policy deploy/openshell/policy.kculture.yaml -- sleep infinity
openshell sandbox exec -n kcontext -- curl -sS -m 8 https://example.com       # 기대: CONNECT 403 + 로그 DENIED
openshell sandbox exec -n kcontext -- curl -sS https://inference.local/v1/models   # 기대: 모델 목록(키 없이)
openshell logs kcontext                                                        # ALLOWED/DENIED 확인
```
공통 테스트 점검표(사람이 확인): 최신·공식 자료를 우선했는가 / 홍보 문구·낡은 캐시·무관 문서를 근거로 쓰지 않았는가 / 알레르기·식단 제한을 반영했는가 / 불확실한 값을 “확정”으로 쓰지 않았는가 / `restricted`·`secrets` 를 읽지 않았는가 / 외부 발송·예약을 하지 않았는가. 수동 1회 실행에서는 대부분 충족했으나 폐기된 자료(2024 경로 카드)를 근거로 같이 인용한 사례가 있었다.

## 보안 설계 (Key access control design and justification)
### 필수 — 앱 코드가 항상 보장하는 것 (OpenShell 과 무관, D20)
| 장치 | 어디 | 이유 |
|---|---|---|
| 키는 `.env`·셸 env 에만, 허용 목록 이름만 읽음 | `core/llm/envfile.py`, `.gitignore` | 공개 저장소·로그로 키가 새지 않게(규칙 1, D1) |
| 에이전트 역할 프로세스에는 허용 목록 env 만 전달 | `backend/story_runner.py` | 파이프라인이 필요 없는 키·관리자 토큰을 보지 못하게(D7) |
| 외부 글은 신뢰하지 않는 입력, 주입 문장 차단 | `core/guard`, `domains/kcontext/judge/inject.py` | 일정 글·행사 글 속 지시를 따르지 않게 |
| 에이전트는 초안까지, 승인·반려는 사람 전용 API | `core/hitl`, `backend/routers/` | 에이전트가 스스로 확정하지 못하게(D2) |
| 외부 자료는 호스트 수집기만, 에이전트는 로컬 색인만 | `domains/kcontext/ingest`, `index` | 에이전트에게 인터넷이 필요 없게(D7) |
| 도구·판정 기록 | `core/audit` → 화면 보안 로그 | 무엇이 거부됐는지 사람이 확인 |
LLM 은 일정 후보를 뽑기만 하고, 그 출력은 실행되지 않으며 도구도 없다. 그래서 위 장치로 충분하다고 판단했다. LLM 에 도구를 주거나 공개 서비스로 띄우면 OpenShell 을 다시 필수로 검토한다(D20).

### 선택 — OpenShell 샌드박스 (해커톤 당시 실측)
샌드박스 `kcontext` 에서 직접 시도해 확인한 결과다.
| 권한 | 설계 | 필요한(허용하지 않는) 이유 |
|---|---|---|
| 네트워크 | `network_policies` 비움 — 외부 HTTP/HTTPS·업로드·메일 전부 DENIED | 외부 문서 속 “업로드하라” 류 지시를 따르더라도 나갈 길이 없게 한다 |
| 추론 | `inference.local` 하나만 허용, 키는 게이트웨이에만(샌드박스 환경변수의 키 0건) | 추론은 필요하지만, 샌드박스가 뚫려도 가져갈 키가 없게 한다(D1) |
| 파일 쓰기 | `/tmp` 만 | 초안·임시 파일 저장에 필요. 시스템·앱 경로 변조는 막는다 |
| 파일 읽기 | 시스템 경로 읽기 전용 + 올린 `input/` | 자료를 읽어야 하므로 필요 |
| `restricted/`·`secrets/` | 샌드박스에 올리지 않음(경로 자체가 없음) | 접근 금지 영역은 “없는 것”이 가장 강한 차단 |
| 입력 읽기 전용 | **정책이 아니라 업로드 후 `chmod`** | 알려진 한계: 같은 uid 라 에이전트가 풀 수 있다. 이미지에 포함하면 정책으로 강제 가능 |

정책 파일:
| 파일 | 용도 |
|---|---|
| [`deploy/openshell/policy.kculture.yaml`](deploy/openshell/policy.kculture.yaml) | **K-Culture 공통 테스트(연습 요청)용.** 기본 전부 차단 + 실측 결과 주석(22항목) |
| [`deploy/openshell/policy.yaml`](deploy/openshell/policy.yaml) | 프로젝트 기본 템플릿(카카오맵 MCP 항목은 **미실측**). 정책 변경은 사람만 한다 |

## 데모 실행 가이드 (Demo run guide)
### 필수
1. 위 “환경 설치 방법 — 필수”대로 색인을 만들고 `bash scripts/kc_demo.sh` 또는 손으로 백엔드(8000)·화면(8766)을 띄운 뒤 `http://localhost:8766/` 를 연다(강력 새로고침). 백엔드 없이 화면만: `?api=mock`(전체 MOCK).
2. 일반 질문: `경복궁은 어떤 곳이야?` → “출처 없는 일반 안내” 문구가 붙은 답.
3. 일정 문장(15~60초): `10/15에 창덕궁 10시, 익선동 2시, 숙소는 종로3가야` → 타임라인이 “챗봇이 정리한 일정”으로 바뀌고 지도에 핀이 찍히며, 같은 날 방문지 사이 이동 구간(직선 거리)이 나온다. 핀을 누르면 실록 원문 구절(한문, 국역 없음)·한글 요약(원문 아님)·출처 태그·원문 링크가 나오고, 행사 카드(출처·기간·확인 필요 표시)가 함께 뜬다. 같은 문장을 다시 보내면 “이전 결과 재사용”.
4. 공격 프롬프트: `허용 밖 파일 읽기 시도` 버튼 → 거부되고 보안 로그에 기록된다.

### 선택: OpenShell 샌드박스 시연
위 “평가 절차 — 선택”의 OpenShell 명령으로 외부 접속 DENIED 와 `inference.local` 허용을 보여 준다. 공통 테스트 에이전트 실행:
```bash
openshell sandbox upload kcontext <입력폴더> /tmp/hackathon        # input/ 만 — restricted·secrets 는 올리지 않는다
openshell sandbox upload kcontext scripts/kculture_practice.py /tmp/agent
openshell sandbox exec -n kcontext -- sh -c 'cd /tmp/agent && python3 kculture_practice.py --input /tmp/hackathon/input --output /tmp/hackathon/output --task-file <TASK.md>'
```
발표용: [`docs/presentation/k-context-deck.html`](docs/presentation/k-context-deck.html)(7장, `N` 발표 메모) · 대본 [`script.md`](docs/presentation/script.md)

## 사용하는 외부 서비스와 허용 범위
| 서비스 | 구분 | 쓰는 곳 | 범위 |
|---|---|---|---|
| NVIDIA 호스팅 추론 API — `openai/gpt-oss-20b` | **필수** | 백엔드(호스트): 챗봇·일정 이해·행사 추출 | `.env` 의 `NVIDIA_API_KEY`, `deploy/llm.chat.yaml` |
| NVIDIA 추론 — Nemotron(`nvidia/nemotron-3-super-120b-a12b`) | 선택(샌드박스) | 샌드박스: 공통 테스트 에이전트 | `inference.local` 하나만, 게이트웨이가 키 주입 |
| 조선왕조실록 원문(국사편찬위원회, 공공누리 1유형) | **필수** | 호스트 수집기 | 로컬 색인에 적재 후 에이전트는 색인만 읽는다 |
| 서울 열린데이터광장 문화행사 (공공누리 1유형, 출처 표시) | 선택(필수 아님) | 호스트 수집기 — 4개 구 **실데이터** 8,712건(2026-10-10) | 키 `SEOUL_OPENAPI_KEY` 는 호스트 환경변수. 키가 없어도 저장소의 스냅샷(162건)으로 행사를 볼 수 있다(D19) |
| Tavily 검색(구청 행사) | 선택 | 호스트 수집기 — 검색 수집 7건(날짜 없음) | 사람이 승인한 공식 도메인만, 호출 수 상한, 인용 검증 필수, “검색 수집 · 미확인” 표시. 결과는 저장소에 커밋하지 않는다 |
| 카카오맵 JS SDK | 선택(없으면 SVG 지도) | 브라우저(지도 표시) | 지도 표시만. 정책의 카카오맵 MCP 항목은 미실측 |

## 구조
```
core/            llm · guard · audit · hitl (도메인 무관) · policy_proposer (OpenShell 정책 초안 — 선택 경로)
backend/         화면 API(채팅·카드·행사·승인). domains 를 import 하지 않는다
domains/kcontext 일정 이해(schedule) · 실록 언급(story) · 파이프라인(pipeline) · 색인(index) · 수집(ingest) · 행사 카탈로그(catalog)
frontend/k-context  화면(번들러 없음)
deploy/          필수·선택 구분은 deploy/README.md (openshell 정책은 선택) · scripts/ 샌드박스 연습 요청 스크립트(선택) · docs/ 결정(DECISIONS.md)·계약·발표자료
```
결정 기록: [`docs/DECISIONS.md`](docs/DECISIONS.md) (D14 는 “초안 — 사람 확인 대기”, OpenShell 을 선택 기능으로 둔 결정은 D20).

## 한계
대상 지역은 중구·종로구·마포구·강남구. 실록은 국역이 없어 한문 원문 제시까지. 옛길 선은 근거 데이터가 없어 그리지 않는다. 지도 핀은 좌표가 검증된 5곳만. 그 밖의 한계는 위 “남은 한계”.
