# nvidia-hackathon

NVIDIA 에이전트 스택(OpenShell · NemoClaw · NVIDIA Agent Skills) 위에서 만드는 프로젝트. 팀 까딱이.
방향: 한국의 문화와 역사를 새롭게 탐색·해석·활용하는 에이전트 (해커톤 때는 OpenShell 사용이 목적이었고, 이후 선택 기능 — D20). 세부 주제는 미정 —
정해지면 이 문서 맨 위에 한 줄 소개와 절대 규칙을 추가한다.
참고: `/home/hyun/MaintQ-NVIDIA` 는 같은 스택을 쓴 선행 프로젝트다. 코드는 가져오지 않고, 필요할 때만 패턴을 참고한다.

## 스택 배치
> 해커톤(10/7) 이후 OpenShell·NemoClaw 는 **선택 기능**이다(D20). 제품은 호스트에서 돌고, 필수 보안은 앱 코드 장치로 보장한다. 필수·선택 구분: `deploy/README.md`.
- **OpenShell** (선택) — 샌드박스 시연 경로. 정책 템플릿 `deploy/openshell/policy.yaml`(기본 전부 차단).
- **NemoClaw / OpenClaw** — 샌드박스 안 에이전트 런타임. 도구는 MCP 로 붙인다.
- **추론** — 샌드박스 안에서는 `https://inference.local` 로만 호출. API 키는 게이트웨이 provider 에만 있다(`scripts/gateway_setup.sh`).
- **Agent Skills** — 우리 스킬은 `skills/`, NVIDIA 카탈로그 스킬은 `.claude/skills/`.

## 레포 구조
```
core/          도메인 무관 뼈대 — llm · hitl · guard · audit · policy_proposer (README 참고)
mcp_server/    MCP 서버, 도구는 tools/ 에 파일당 1개
backend/       사람 전용 승인 API (routers/)
domains/<n>/   미션 공개 후 채우는 슬롯 — data · tools · skills · evals
skills/        제품 스킬(에이전트에게 주는 SKILL.md)
deploy/        openshell(정책·이미지) · nemoclaw(presets·workspace) · brev
eval/ tests/   평가셋 · pytest(tests/ 는 소스 구조를 따라간다)
docs/          SCOPE · DECISIONS · guides · session_log · sprints · private(gitignore)
```
MCP 서버와 backend 는 프로세스를 분리하고 서로 import 하지 않는다. 공통 로직은 `core/` 로 둔다 (D3).

## 절대 규칙
1. 샌드박스 이미지·빌드 컨텍스트·리포에 `NVIDIA_API_KEY` 등 비밀을 넣지 않는다. `.env` 는 gitignore, 키는 셸 env → 게이트웨이 provider.
2. `network_policies` 는 비어 있는 것이 기본. 허용을 추가하면 이유와 실측(로그의 ALLOWED/DENIED)을 정책 파일 주석에 남긴다.
3. 새 스킬은 만든 뒤 `skill-card-generator` 로 카드를 생성한다. NVIDIA 공식 카탈로그(`npx skills add NVIDIA/skills`, 398종 전체 설치, `skills-lock.json` 기록)는 신뢰하고 스캔하지 않는다. 그 외 출처의 스킬은 설치 전 SkillSpector 로 스캔한다.
4. NemoClaw/OpenShell 동작은 기억이 아니라 문서로 확인한다 — `.mcp.json` 의 `nemoclaw-docs` MCP(`searchDocs`) 또는 `nemoclaw-user-guide` 스킬.

## 로컬 환경 (실측 2026-10-03)
openshell 0.0.116 · nemoclaw v0.0.124 · 게이트웨이 `nemoclaw`(127.0.0.1:8080). 다른 프로젝트의 샌드박스(`maintq*`)가 같은 게이트웨이에 있으니 이름 충돌·삭제에 주의.

## 작업 흐름
`/idea-judge`(주제 선택) → `/sprint`(계획) → `/stage N`(구현·검증·커밋) → `/done`(세션 마무리·로그). 마무리 없이 로그만은 `/logger`, 작업 상태 저장은 `/checkpoint`.
에이전트(`.claude/agents/`): `pm`(계획) · `dev`(구현) · `reviewer`(설계·보안 게이트, 읽기 전용) · `eval-runner`(회귀·평가).
문서: `docs/SCOPE.md`(범위) · `docs/DECISIONS.md`(결정) · `docs/guides/`(스킬·스택 가이드, 커밋) · `docs/private/`(후보·팀 정보, **gitignore**) · `docs/sprints/` · `docs/session_log/`(`/done`·`/logger` 가 `날짜_시각_주요작업.md` 로 저장).
`skills/` 는 **제품이 에이전트에게 주는** 스킬, `.claude/skills/` 는 **개발 중 Claude Code 가 쓰는** 스킬이다.

## 회귀 테스트 — 코드 변경 후 실행
`eval-runner` 와 `/stage` 가 이 절을 기준으로 삼는다. 명령은 레포 루트에서:
- pytest: `uv run python -m pytest -q` (건수는 러너 출력이 기준 — 직전보다 줄었다면 테스트가 사라진 것)
- 린트: `uv run ruff check .` (`.claude/skills/` 는 NVIDIA 카탈로그라 제외)
- 프론트: `(cd frontend/k-context && node --test)`
- 평가셋(결정적, LLM 없음): `uv run python eval/kc.py validate` · `uv run python eval/kc.py run --check --known-failures eval/BASELINE.md` (실행이 만든 `eval/results/*` 는 커밋하지 않는다 — 측정 결과만 라벨을 붙여 남긴다)
- 데모 점검: `bash scripts/kc_demo.sh --check`
- 실호출 측정(`eval/kc.py stability`)은 비용이 있어 회귀에 넣지 않는다 — `eval/BASELINE.md` 절차대로 사람 승인 후
