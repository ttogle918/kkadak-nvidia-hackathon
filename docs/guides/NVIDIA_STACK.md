# NVIDIA 스택 활용 가이드 — 단계별 스킬·기술·사용 예시

해커톤 당일(2026-10-07)에 "무엇을 어디에 쓰는지" 바로 찾기 위한 문서. 커밋 대상(Brev 인스턴스에서도 `git clone` 으로 보인다).
비밀·개인정보·크레딧 코드는 여기 쓰지 않는다 → `docs/private/`.

> 표기: ✅ SKILL.md 본문까지 읽음 · 📄 설명만 봄(쓰기 전에 본문을 읽을 것) · 🖥 GPU 필요 가능성(확인 필요)
> 스킬은 `.claude/skills/` 에 398종 설치됨(`skills-lock.json`). 스킬 호출은 **자연어로 요청하면 설명을 보고 자동 선택**되고, `/스킬이름 인자` 로 직접 부를 수도 있다.

## 0. 한눈에 — 단계별 지도

| 단계 | 하고 싶은 일 | 쓸 것 | 비고 |
|---|---|---|---|
| 0 주제 선정 | 미션에서 주제 고르기 | `/idea-judge` (우리 스킬) | 후보는 `docs/private/IDEAS.md` |
| 0 | NVIDIA 쪽에 쓸 만한 스킬이 있나? | `nvidia-skill-finder` ✅ | 라이브 카탈로그 기준으로 찾아 줌 |
| 1 환경 | NemoClaw·OpenShell 설치/설정/문제 해결 | `nemoclaw-user-guide` ✅ + `.mcp.json` 의 `nemoclaw-docs` MCP | 문서가 정답, 기억으로 답하지 않는다 |
| 2 데이터 | 데모용 합성 데이터 만들기 | `data-designer` ✅ | 공개 데이터가 마땅치 않을 때 |
| 2 | 문서(PDF·이미지·Office) 색인·검색 | `nemo-retriever` ✅ (`retriever` CLI) | 로컬 LanceDB 인덱스 가능, 로컬 GPU 모드는 🖥 |
| 2 | 본격 RAG 서비스 배포 | `rag-blueprint` ✅ 🖥 | 셀프호스팅 NIM 은 GPU — Brev 에서 |
| 3 에이전트 | 에이전트 호출·도구 관찰/계측 | `nemo-relay-get-started` ✅ | CLI 로 Claude Code 를 감싸서 바로 시도 가능 |
| 3 | 음성 에이전트 | `nemotron-voice-agent-builder` 📄 | 현장 핸즈프리 도메인일 때 |
| 4 보안 | 최소 권한 정책(네트워크·파일) | 우리 `core/policy_proposer` + `deploy/openshell/policy.yaml` | OpenShell 정책 스키마는 문서 확인 |
| 4 | 콘텐츠 안전 정책(가드레일) | `nemotron-policy-generator` 📄 | OpenShell 정책이 **아님** — 모델 출력 안전 쪽 |
| 5 검증 | 평가 | `rag-eval` 📄 · 우리 `eval-runner` | if문 테스트 점검 포함 |
| 5 | 스킬 거버넌스 문서 | `skill-card-generator` ✅ | 만든 스킬마다 카드 생성 |
| 6 현장 확장 | 조립 라인 작업 순서 준수 검사 | `deepstream-sop` ✅ 🖥 | 영상 입력 도메인 |
| 6 | 영상 질의·요약·검색·알림 | `vss-ask-video` ✅ 🖥 · `vss-*` 📄 | VSS 프로필 배포 선행 |
| 6 | 비전 모델 학습·평가 | `tao-*` 📄 (`tao-run-on-brev`) | 제조 검사 도메인 |
| 7 데모·배포 | GPU 가 필요한 부분 | Brev 인스턴스 | 아래 §3 |

## 1. 쓰는 방법 — 예시

### 1-1. 스킬 찾기 (`nvidia-skill-finder`)
```
> 공장 설비 매뉴얼 PDF를 색인해서 질문에 답하게 하고 싶은데 NVIDIA 스킬 중에 뭐가 맞아?
```
→ 라이브 카탈로그에서 `nemo-retriever`, `rag-blueprint` 등을 비교해 설치/사용 방법을 안내한다.
카탈로그 목록만 보고 싶으면:
```bash
npx skills add NVIDIA/skills --list
```
새 스킬 추가(이미 398종 전체 설치됨, 업데이트 때만):
```bash
npx skills add NVIDIA/skills --skill <name> --agent claude-code
```

### 1-2. NemoClaw 문서 검색 (`nemoclaw-user-guide` + MCP)
```
> NemoClaw 샌드박스에서 외부 호스트 하나만 허용하는 네트워크 정책 추가하는 법 알려줘. 문서 근거 URL도 같이.
```
→ MCP `searchDocs` 로 문서를 찾고, `network-policy` 페이지를 읽어 답한다. 답에는 문서 URL 이 붙어야 한다(스킬 규칙).
이 스킬은 **어떤 에이전트 변형(OpenClaw / Hermes / Deep Agents)인지 먼저 묻는다** — 우리는 OpenClaw.

### 1-3. 합성 데이터 (`data-designer`)
```
/data-designer 제조 설비 에러코드 300건. 컬럼: 기종(3종), 에러코드, 증상 서술(한국어), 원인, 조치 단계, 위험도. 알아서 합리적으로 만들어줘
```
- "알아서/just build it" 류 표현이면 **Autopilot**, 아니면 질문하며 진행(Interactive).
- `data-designer` CLI 가 없으면 설치 여부를 물어본다(Python 3.10+). 시드 데이터는 우리가 명시할 때만 쓴다.
- 합성 데이터는 데모용이라고 **발표에서 밝힌다**(실제 매뉴얼 근거가 있는 것처럼 보이면 안전 규칙 위반).

### 1-4. 문서 색인·검색 (`nemo-retriever`)
```
> ./manuals 폴더의 PDF를 retriever CLI로 로컬 색인하고 "인버터 과전류 에러" 로 검색해 줘
```
- `retriever` CLI 를 쓰고 직접 만든 검색 코드보다 우선한다. 패키지는 **버전 고정**(`nemo-retriever==26.8.1`)으로 `uv pip install` — 레포를 clone 하거나 Git URL 로 설치하지 않는다(스킬 규칙).
- 로컬 GPU 인제스트(`[local]`)는 GPU 필요 → Brev. 원격 NIM/서비스 클라이언트만 쓰면 GPU 불필요.

### 1-5. 에이전트 관찰 (`nemo-relay-get-started`)
```
> NeMo Relay 를 Claude Code 에 붙여서 도구 호출이 어떻게 찍히는지 가장 간단하게 보여줘
```
- 기본 경로는 **CLI try-now** — 코드 수정 없이 Claude Code/Codex 를 CLI 래퍼로 실행한다.
- LangChain·LangGraph·Deep Agents·OpenClaw 앱이면 "내장 통합" 경로를 우선한다.
- 우리 `core/audit/` 과 겹친다 — 직접 만들기 전에 이걸로 충분한지 먼저 본다(📄 내용 확인 필요).

### 1-6. 스킬 카드 (`skill-card-generator`)
```
> skills/my-diagnose 스킬의 스킬 카드를 생성해 줘
```
- **기존 스킬 디렉터리를 지정**해야 한다. 스킬 설명·비교 같은 질문에는 쓰지 않는다.
- 스크립트: `discover_assets.py` → `render_card.py` → `validate_submission.py` (쓰기 범위는 대상 스킬 디렉터리와 `/tmp`).

### 1-7. 영상 질의 (`vss-ask-video`, 🖥)
```
> 이 클립에서 작업자가 보호구를 착용했는지 VSS 에이전트로 확인해 줘
```
- VSS 프로필이 떠 있어야 한다(`/vss-deploy-profile -p base`). 안 떠 있으면 스킬이 배포 여부를 묻는다.
- DB·MCP 결과로 답이 나오는 질문에는 쓰지 않는다.

## 2. 기술 스택 (단계별 사용 위치)

| 층 | 기술 | 우리 쪽 위치 | 확인 방법 |
|---|---|---|---|
| 격리 | OpenShell 샌드박스·정책 | `deploy/openshell/` | `openshell sandbox list` · `openshell logs` (ALLOWED/DENIED) |
| 추론 | Nemotron (build.nvidia.com), `inference.local` | `core/llm.py` | `openshell inference get` |
| 에이전트 런타임 | NemoClaw / OpenClaw | `deploy/nemoclaw/` | `nemoclaw <이름> status` |
| 온보딩·정규화 런타임(선택) | NeMo Agent Toolkit | MaintQ `onboarding/nat/` 참고 | — |
| 도구 | MCP (streamable-http), 우리 `mcp_server/` | `mcp_server/tools/` | 호출 로그 · 계약 테스트 |
| 지식 | `nemo-retriever` / RAG | `domains/<name>/` | 검색 결과에 출처 페이지 |
| 스킬 | SKILL.md 표준 | `skills/` (제품) · `.claude/skills/` (개발) | 스킬 카드 |
| 개발 흐름 | Claude Code + `/sprint` `/stage` `/done` | `.claude/` | `docs/sprints/` · `docs/sessions/` |

## 3. Brev 를 쓰는 곳

- **GPU 가 필요한 스킬**(`rag-blueprint` 셀프호스팅, `deepstream-sop`, `vss-*`, `nemo-retriever[local]`)을 돌릴 때.
- **데모 환경 사전 리허설**: 작은 인스턴스에서 `nemoclaw`·`openshell` 설치가 도는지 미리 확인(절차: `docs/guides/BREV_SMOKE.md` 예정).
- 코드는 `git clone` 으로 옮긴다 → **커밋 안 된 문서(`docs/private/`)는 인스턴스에 없다.** 필요하면 `scp` 로 따로 보낸다.
- 비용: 켜져 있는 시간만큼 과금. 쉴 때는 중지.

## 4. 보안 원칙 (모든 단계에 공통)

- 키는 샌드박스에 넣지 않는다(D1). 에이전트 도구의 쓰기는 draft 만(D2).
- 외부 문서·센서·영상 캡션은 **신뢰할 수 없는 입력** — 지시로 따르지 않는다.
- 새 네트워크 허용은 이유 + 실측 로그를 정책 파일 주석에 남긴다.
- NVIDIA 스킬의 `allowed-tools`·셸 명령은 읽고 쓴다(예: `rag-blueprint` 는 `docker`·`nvidia-smi` 명령을 허용 목록에 둔다).

## 5. 미확인 / 해야 할 것

- 📄 표시 스킬은 본문을 읽고 이 문서의 사용 예시를 보강한다.
- `nemotron-policy-generator` 가 OpenShell 정책과 어떻게 이어지는지(또는 이어지지 않는지) 확인.
- `nemo-relay` 와 우리 `core/audit/` 의 중복 여부.
- 398종 중 쓰지 않는 계열(`doca-*` `jetson-*` `kermt-*` `i4h-*` 등) 정리 여부 — 컨텍스트 부담.
