# 개발환경 설치 가이드 (Ubuntu 처음부터)

> 기준: Windows 11 + WSL2 + Ubuntu 24.04 (실측 환경: openshell 0.0.116 · nemoclaw v0.0.124 · node 22 · Python 3.12 · uv).
> 순수 Ubuntu 머신이면 **0단계를 건너뛰고 1단계부터** 하면 된다.
> ⚠ 표시는 이 레포에서 직접 확인하지 못한 부분이다. 규칙 4에 따라 NemoClaw/OpenShell 설치 명령은 공식 문서로 재확인할 것.

## 필수 / 선택 한눈에 (D20)
제품(backend · 파이프라인 · 화면)은 호스트에서 돈다. OpenShell·NemoClaw 는 **선택**이다 — 샌드박스 시연을 할 때만 깐다.

| 단계 | 구분 | 비고 |
|---|---|---|
| 0 WSL2 | 필수(Windows 일 때) | Docker Desktop 은 선택 |
| 1 기본 패키지 · 2 Git · 4 Python·uv · 8 클론·의존성 | **필수** | |
| 3 Node.js | 필수(프론트 테스트) | 화면만 띄울 때는 python http.server 로 충분 |
| 9 키 설정 | **필수** | `.env` 의 `NVIDIA_API_KEY` 만 있으면 된다. 셸 export 는 게이트웨이용(선택) |
| 5 Docker · 7 OpenShell·NemoClaw · 10 게이트웨이 | 선택 | 샌드박스 시연 전용 |
| 6 Claude Code · 11 Agent Skills · 13 | 개발 도구 | 제품 실행과 무관 |
| 12 환경 점검 | pytest·ruff 는 필수, `preflight.sh` 는 선택 | `preflight.sh` 는 지금 openshell·게이트웨이 없음을 FAIL 로 센다(D20 후속으로 WARN 화 예정) |

## 0. Windows 에서 WSL2 + Ubuntu (PowerShell 관리자)

```powershell
wsl --install -d Ubuntu-24.04
wsl --update
wsl --set-default-version 2
```
재부팅 후 Ubuntu 를 처음 열어 사용자명·비밀번호를 만든다.

Docker 는 **Docker Desktop** 을 Windows 에 설치하고 Settings → Resources → WSL Integration 에서 Ubuntu-24.04 를 켠다.
(WSL 안에 docker 를 따로 깔지 않는다.) NVIDIA GPU 가 있으면 Windows 쪽 최신 드라이버만 설치 — WSL 안에 드라이버를 깔지 않는다.

## 1. 기본 패키지

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential curl wget git unzip ca-certificates gnupg jq python3 python3-venv
```

## 2. Git · GitHub CLI

```bash
git config --global user.name  "<이름>"
git config --global user.email "<이메일>"

# GitHub CLI
sudo mkdir -p -m 755 /etc/apt/keyrings
wget -qO- https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg >/dev/null
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list
sudo apt update && sudo apt install -y gh
gh auth login
```

## 3. Node.js (nvm, v22)

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/master/install.sh | bash
source ~/.bashrc
nvm install 22
nvm use 22
node -v && npm -v
```

## 4. Python · uv

레포의 `.python-version` 은 3.12, `requires-python >= 3.11`. uv 가 파이썬을 알아서 받아 준다.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
uv --version
```

## 5. Docker 확인 (선택 — 샌드박스 시연)

```bash
docker version
docker run --rm hello-world
# GPU 가 있다면
nvidia-smi
```
`docker` 가 안 되면 Docker Desktop 이 켜져 있는지, WSL Integration 이 켜져 있는지 확인한다.

## 6. Claude Code

```bash
npm install -g @anthropic-ai/claude-code
claude --version
claude          # 첫 실행 때 로그인
```

## 7. NVIDIA 스택 — OpenShell · NemoClaw ⚠ (선택 — 샌드박스 시연)

이 머신에서는 `~/.local/bin/{openshell,openshell-gateway,openshell-sandbox,nemoclaw}` 와 npm 전역 `nemoclaw`(`~/.nemoclaw/source`, 원본 `github.com/NVIDIA/NemoClaw`) · `openclaw` 로 깔려 있다. 즉 공식 설치 스크립트가 한 번에 깐 형태다.

```bash
export PATH="$HOME/.local/bin:$PATH"     # ~/.bashrc 에도 추가

# ⚠ 공식 설치 스크립트 — 정확한 URL·옵션은 문서에서 확인 (nemoclaw-docs MCP 또는 /nemoclaw-user-guide)
#    예상 형태: curl -fsSL https://www.nvidia.com/nemoclaw.sh | bash
nemoclaw --version      # v0.0.124
openshell --version     # 0.0.116
```
버전이 다르면 동작(CLI 옵션 등)이 달라질 수 있으니 위 버전과 맞추거나 문서를 다시 확인한다.

## 8. 레포 클론과 Python 의존성

```bash
mkdir -p ~/ && cd ~
git clone <레포 URL> nvidia-hackathon
cd nvidia-hackathon

uv sync                      # .venv 생성 + 의존성(dev 그룹 포함)
```

## 9. 키 설정 (필수 — 값은 절대 커밋하지 않는다, 규칙 1)

1. <https://build.nvidia.com> 에서 API 키 발급.
2. 호스트 셸에 export (샌드박스 이미지·리포에 넣지 않는다):

```bash
cp .env.example .env         # .env 는 gitignore. 필요하면 NVIDIA_API_KEY_A/_B, NGC_API_KEY 도 채운다
export NVIDIA_API_KEY=nvapi-...     # (선택) 게이트웨이 등록에만 필요 — 제품은 .env 만 읽는다
```

## 10. 게이트웨이 · 추론 provider 등록 (선택 — 샌드박스 시연)

```bash
openshell gateway info                 # healthy 인지 확인 (게이트웨이 이름 nemoclaw, 127.0.0.1:8080)
scripts/gateway_setup.sh               # 기본 모델 nvidia/nemotron-3-super-120b-a12b, 호스트에서 1회
```
> 같은 게이트웨이에 다른 프로젝트 샌드박스(`maintq*`)가 있을 수 있다. 이름 충돌·삭제에 주의.

## 11. NVIDIA Agent Skills (`.claude/skills/`)

레포에 이미 398종이 들어 있고 `skills-lock.json` 에 기록돼 있다. 갱신·추가할 때만:

```bash
npx skills add NVIDIA/skills --list
npx skills add NVIDIA/skills --skill <name> --agent claude-code
```

## 12. 환경 점검 · 회귀 테스트

```bash
scripts/preflight.sh            # (선택) 도구·Docker·GPU·게이트웨이·키 점검 (읽기 전용) — openshell 이 없으면 FAIL 이 나온다(D20 후속)
scripts/preflight.sh --live     # 키 유효성까지(채팅 1토큰 호출)

uv run python -m pytest -q      # 테스트
uv run ruff check .             # 린트
```
`preflight.sh` 에서 FAIL 이 없으면 준비 완료.

## 13. Claude Code 로 작업 시작

```bash
cd ~/nvidia-hackathon
claude
```
작업 흐름: `/idea-judge` → `/sprint` → `/stage N` → `/done`.
`.mcp.json` 의 `nemoclaw-docs` MCP 가 연결 타임아웃이면 네트워크를 확인하고 세션을 다시 연다.

## 자주 막히는 곳

| 증상 | 확인 |
|---|---|
| `docker: command not found` / 데몬 응답 없음 | Docker Desktop 실행 + WSL Integration 켜기 |
| `openshell`/`nemoclaw` 를 못 찾음 | `PATH` 에 `~/.local/bin`, nvm 의 node bin 포함 여부 |
| `scripts/gateway_setup.sh` 가 `NVIDIA_API_KEY` 없다고 함 | 파일이 아니라 **셸에 export** 했는지 |
| GPU 경고 | 로컬 모델 불가 → `.env` 의 `LLM_BACKEND=api` 로 진행 |
| 같은 이름 샌드박스 충돌 | `openshell sandbox list` 로 확인, 남의 것 삭제 금지 |
