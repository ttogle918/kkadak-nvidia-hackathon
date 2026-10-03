# nvidia-hackathon

NVIDIA 에이전트 스택(OpenShell · NemoClaw · NVIDIA Agent Skills) 위에서 만드는 프로젝트. 제품 도메인은 아직 미정 —
정해지면 이 문서 맨 위에 한 줄 소개와 절대 규칙을 추가한다.
참고 구현: `/home/hyun/MaintQ-NVIDIA` (같은 스택을 쓴 선행 프로젝트. 결정 기록은 그쪽 `docs/10_DECISIONS.md`).

## 스택 배치
- **OpenShell** — 에이전트가 도는 샌드박스. 정책 템플릿 `deploy/openshell/policy.yaml`(기본 전부 차단).
- **NemoClaw / OpenClaw** — 샌드박스 안 에이전트 런타임. 도구는 MCP 로 붙인다.
- **추론** — 샌드박스 안에서는 `https://inference.local` 로만 호출. API 키는 게이트웨이 provider 에만 있다(`scripts/gateway_setup.sh`).
- **Agent Skills** — 우리 스킬은 `skills/`, NVIDIA 카탈로그 스킬은 `.claude/skills/`.

## 절대 규칙
1. 샌드박스 이미지·빌드 컨텍스트·리포에 `NVIDIA_API_KEY` 등 비밀을 넣지 않는다. `.env` 는 gitignore, 키는 셸 env → 게이트웨이 provider.
2. `network_policies` 는 비어 있는 것이 기본. 허용을 추가하면 이유와 실측(로그의 ALLOWED/DENIED)을 정책 파일 주석에 남긴다.
3. 새 스킬은 만든 뒤 `skill-card-generator` 로 카드를 생성한다. NVIDIA 공식 카탈로그(`npx skills add NVIDIA/skills`, 398종 전체 설치, `skills-lock.json` 기록)는 신뢰하고 스캔하지 않는다. 그 외 출처의 스킬은 설치 전 SkillSpector 로 스캔한다.
4. NemoClaw/OpenShell 동작은 기억이 아니라 문서로 확인한다 — `.mcp.json` 의 `nemoclaw-docs` MCP(`searchDocs`) 또는 `nemoclaw-user-guide` 스킬.

## 로컬 환경 (실측 2026-10-03)
openshell 0.0.116 · nemoclaw v0.0.124 · 게이트웨이 `nemoclaw`(127.0.0.1:8080). 다른 프로젝트의 샌드박스(`maintq*`)가 같은 게이트웨이에 있으니 이름 충돌·삭제에 주의.
