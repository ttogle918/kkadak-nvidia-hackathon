# deploy/ — 무엇이 필수이고 무엇이 선택인가

제품(backend · 파이프라인 · 화면)은 **호스트에서** 돈다. OpenShell 샌드박스는 선택 기능이다(D20).
데모를 띄우는 데 필요한 것은 아래 "필수" 줄뿐이다.

| 경로 | 구분 | 무엇 | 없으면 |
|---|---|---|---|
| `llm.chat.yaml` | **필수** | 백엔드·파이프라인의 LLM 설정(provider·모델 `openai/gpt-oss-20b`·한도). `CHAT_MODEL`·`SCHEDULE_MODEL` env 로 덮어씀 | 챗봇·일정 이해가 돌지 않는다 |
| `llm.example.yaml` | 참고 | 기능별 provider·키 풀 설정 예시(D5) | 영향 없음 |
| `catalog/` | 선택 | 행사 카탈로그 주기 수집(cron·systemd) 안내. 키는 호스트 env 에만 | 행사는 수동 수집(`python -m domains.kcontext.catalog …`)으로만 갱신 |
| `openshell/` | 선택 | 샌드박스 정책 2종과 해커톤 당시 22항목 실측 기록 | 제품 동작에 영향 없음. 샌드박스 시연만 못 한다 |
| `nemoclaw/` | 미사용 | OpenClaw workspace 자리(파일 안내만) | 영향 없음 |
| `brev/` | 미사용 | GPU 인스턴스 안내 자리 | 영향 없음 |

## 필수 — 데모 실행에 필요한 것
- Python 3.12 + uv, (프론트 테스트용) Node 18+
- `.env` 에 `NVIDIA_API_KEY` (`.env.example` 복사. `.env` 는 gitignore)
- 실록 색인 `var/index/kcontext.db` (README "실록 색인 만들기")
- `deploy/llm.chat.yaml`

## 필수 보안 — OpenShell 없이도 항상 켜져 있는 장치 (D20)
OpenShell 을 쓰지 않아도 아래는 앱 코드가 보장한다. 바꾸려면 결정부터 추가한다.

| 장치 | 어디 | 근거 |
|---|---|---|
| 키는 `.env`·셸 env 에만, 허용 목록 이름만 읽음 | `core/llm/envfile.py`, `.gitignore` | 규칙 1, D1 |
| 에이전트 역할 프로세스에는 허용 목록 env 만 전달 | `backend/story_runner.py` `_ENV_ALLOW`, `backend/catalog_runner.py` | D7 ③ |
| 외부 글은 신뢰하지 않는 입력으로 감싸고 주입 차단 | `core/guard`, `domains/kcontext/judge/inject.py` | D7 |
| 에이전트 쓰기는 초안까지, 확정은 사람 전용 API | `core/hitl`, `backend/routers/` | D2 |
| 도구·판정 기록 | `core/audit` → 화면 보안 로그 | `core/README.md` |
| 외부 자료는 호스트 수집기만 받고 에이전트는 로컬 색인만 읽음 | `domains/kcontext/ingest`, `index` | D7 |
| LLM 엔드포인트는 https 만(루프백 예외) | `core/llm/http_transport.py` | 코드 검사 |

## 선택 — OpenShell 샌드박스 시연
해커톤(2026-10-07) 때 만든 경로다. 외부 접속이 전부 막히고 `inference.local` 만 열린 샌드박스에서
공통 테스트 에이전트(`scripts/kculture_practice.py`)를 돌린다. 키는 게이트웨이 provider 에만 있다(D1).

필요한 것: Docker, OpenShell 0.0.116, 게이트웨이(`scripts/gateway_setup.sh`, 호스트에서 1회).
절차와 기대 결과: README "선택: OpenShell 샌드박스 시연", 정책·실측: `openshell/policy.kculture.yaml` 하단 주석.
정책 파일은 사람만 고친다(규칙 2, D7). 허용을 추가하면 이유와 실측 로그를 주석에 남긴다.

다시 필수로 검토할 때: LLM 에 도구(파일·네트워크)를 주거나, 공개 서비스로 띄우거나, 에이전트를 샌드박스 안에서 돌릴 때(D20).
