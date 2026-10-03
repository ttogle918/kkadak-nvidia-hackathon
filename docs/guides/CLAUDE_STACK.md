# Claude Code 스킬 모음집 — 호출하기 전에 보는 추천표

호출 전에 "지금 상황에 뭘 부를까"를 찾기 위한 문서. NVIDIA 쪽 스킬은 `NVIDIA_STACK.md` 에 있다.
스킬은 **자연어로 요청해도 설명을 보고 자동 선택**되지만, 확실히 부르려면 `/스킬이름 인자` 로 직접 호출한다.

> 표기: ✅ 이 레포에 있음(바로 사용) · 🌐 계정에 설치돼 있음 · ⬇ 설치 안 됨(설치하면 쓸 수 있음) · 📄 설명만 보고 적음(본문 미확인)
> 설명은 세션에 보이는 스킬 목록 기준이다. 설치 여부는 시점에 따라 바뀐다 — `/` 입력 시 나오는 목록이 정답.

## 1. 상황 → 부를 것 (빠른 선택표)

| 상황 | 부를 것 | 비고 |
|---|---|---|
| 미션 공개 직후, 주제 고르기 | `/idea-judge` ✅ | 탈락 필터 → 점수 → 추천 3 |
| 아이디어가 뭉뚱그려서 **계속 질문받으며 구체화**하고 싶다 | `/grill-me` ⬇ · `superpowers:brainstorming` ⬇ · 또는 "질문 도구로 인터뷰해줘" (§4) | 4지선다 UI는 §4 |
| 범위·스프린트 계획 | `/sprint` ✅ | `docs/SCOPE.md` 가 비어 있으면 거부함 |
| 구현·검증·커밋 한 사이클 | `/stage N` ✅ | dev → eval-runner → reviewer → 커밋 |
| 중간에 끊고 나중에 이어서 | `/checkpoint` ✅ | |
| 지금까지를 로그로 남기기(계속 작업) | `/logger` ✅ | `docs/session_log/날짜_시각_주요작업.md` |
| 세션 마무리 | `/done` ✅ | 커밋 확인 + 결정 정합성 + 로그 |
| 설계 논의 (구조 대안 비교) | `engineering:system-design` 🌐 · `engineering:architecture` 🌐 | ADR 형태로 남기려면 architecture |
| 버그 원인 추적 | `engineering:debug` 🌐 | |
| 변경분 검토 | `/code-review` 🌐 · `/security-review` 🌐 | 에이전트 보안 주제라면 둘 다 |
| 코드 정리 | `/simplify` 🌐 | 버그는 안 찾는다(그건 code-review) |
| 테스트 전략 | `engineering:testing-strategy` 🌐 | |
| 승인 화면·문구 다듬기 | `design:ux-copy` 🌐 · `design:design-critique` 🌐 | 사람 승인 UI가 제품의 핵심이라 가치 큼 |
| 발표 자료 | `anthropic-skills:pptx` 🌐 · Canva 도구 🌐 | 피칭 덱 |
| 데모 대시보드·시각화 | `dataviz` 🌐 · `data:build-dashboard` 🌐 · `artifact` 🌐 | 차트 그리기 전에 `dataviz` 먼저 |
| 문서 작성 | `engineering:documentation` 🌐 | README·가이드 |
| 권한 프롬프트 줄이기 | `/fewer-permission-prompts` 🌐 | 해커톤 전날 한 번 |
| 훅·설정 변경 | `/update-config` 🌐 | "수정할 때마다 ruff 돌려줘" 같은 자동화 |
| 반복 확인(배포·CI) | `/loop` 🌐 | 폴링용 |
| 새 스킬 만들기 | `anthropic-skills:skill-creator` 🌐 → 스킬 카드는 `skill-card-generator` | 제품 스킬은 `skills/` |

## 2. 이 레포의 스킬·에이전트 ✅

| 이름 | 하는 일 | 호출 예 |
|---|---|---|
| `idea-judge` | 미션·후보 심사 | `/idea-judge 미션: "공장 에이전트를 안전하게 운영하라"` |
| `sprint` | 계획만 세움 (pm→dev 평가) | `/sprint 1` |
| `stage` | 스테이지 실행·검증·커밋 | `/stage 1` · 재개 `/stage 2 resume` |
| `checkpoint` | 작업 상태 저장 | `/checkpoint` |
| `logger` | 세션 로그 저장(마무리 없이) | `/logger` |
| `done` | 세션 마무리 | `/done` |
| agents: `pm` `dev` `reviewer` `eval-runner` | 위 스킬들이 부름 | "reviewer 로 이번 변경 검토해줘" |

권장 흐름: `idea-judge` → `SCOPE.md` 채우기 → `sprint` → (`stage` ×N) → `done`. 중간에 `logger`.

## 3. 계정에 설치된 것 중 쓸 만한 것 🌐

### 개발 흐름
- `engineering:system-design` — 구조·API·데이터 모델 설계. 예: `/engineering:system-design core 에 hitl·guard·audit 를 어떻게 나눌지`
- `engineering:architecture` — 결정을 ADR 로 남김. 우리 `docs/DECISIONS.md` 와 형식을 맞춰 쓸 것
- `engineering:debug` — 재현 → 격리 → 수정
- `engineering:testing-strategy` · `engineering:deploy-checklist` · `engineering:tech-debt`
- `/code-review` — 예: `/code-review high`(범위·강도 지정). `--fix` 로 적용까지
- `/security-review` — 현재 브랜치 변경분의 보안 검토. **우리 reviewer 와 별개로 한 번 더 돌릴 만하다**
- `/simplify` — 변경 코드를 재사용·단순화·효율 관점으로 정리
- `claude-api` — Anthropic API 코드를 짤 때만. 우리 추론은 Nemotron 이라 보통 불필요

### 설정·자동화
- `/update-config` — 훅(`settings.json`) 설정. 예: "Write 후에 ruff 돌리는 훅 추가"
- `/fewer-permission-prompts` — 자주 쓰는 읽기 전용 명령을 허용 목록으로
- `/loop`, `/schedule` — 반복·예약 실행
- `/init` — CLAUDE.md 초기화 (이 레포는 이미 있음)

### 산출물
- `anthropic-skills:pptx` · `docx` · `xlsx` · `pdf` · `canvas-design` · `web-artifacts-builder`
- `dataviz` + `data:create-viz` + `data:build-dashboard` — 데모 화면의 차트·대시보드
- `design:ux-copy` · `design:design-critique` · `design:accessibility-review` · `design:design-handoff`
- Canva · Mermaid 차트 도구 — 아키텍처 다이어그램은 Mermaid 로 빠르게 (`mermaid` 도구)

### 거의 안 쓸 것 (컨텍스트만 차지)
- `small-business:*` · `finance:*` · `marketing:*` · `solana-dev` · `netlify-skills:*` · `supabase*` — 이 프로젝트와 무관. 목록이 길어 스킬 선택을 흐릴 수 있다
- NVIDIA 쪽의 `doca-*` `jetson-*` `kermt-*` `i4h-*` 등 — `NVIDIA_STACK.md` §5 참고

## 4. "질문하면서 구체화"하는 스킬

찾으시던 건 아래 계열이다. **지금은 설치돼 있지 않아서** 목록에 안 보인 것.

| 스킬 | 플러그인 | 동작 | 상태 |
|---|---|---|---|
| `grill-me` | `mattpocock-skills` | 모든 설계 가지가 풀릴 때까지 **선택지를 주며 끈질기게 인터뷰** (다지선다 질문) | ⬇ |
| `grilling` | `mattpocock-skills` | 위 인터뷰의 재사용 부품(`grill-with-docs`·`triage` 등이 내부에서 사용) | ⬇ |
| `grill-with-docs` | `mattpocock-skills` | 인터뷰하면서 프로젝트 도메인 모델과 문서를 갱신 | ⬇ |
| `to-questionnaire` | `mattpocock-skills` | 지금 못 정하는 결정을 **비동기 마크다운 설문**으로 변환 (오빠에게 보내 답받기 좋음) | ⬇ |
| `to-spec` · `to-tickets` | `mattpocock-skills` | 대화를 스펙으로, 계획을 티켓으로 | ⬇ |
| `handoff` | `mattpocock-skills` | 대화를 다른 에이전트용 인수인계 문서로 압축 | ⬇ |
| `superpowers:brainstorming` | `superpowers` | 코드 짜기 전 **소크라테스식 질문**으로 설계 정제, 섹션별로 확인받고 설계 문서 저장 (README 기준 다지선다는 아님) | ⬇ |

설치 (둘 다 공식 마켓플레이스, 세션 안에서):
```
/plugin install mattpocock-skills@claude-plugins-official
/plugin install superpowers@claude-plugins-official
```
설치하면 이 레포의 `/sprint` `/stage` 와 겹치는 스킬(`to-tickets`, `implement`, `code-review`, `writing-plans` 등)도 같이 생긴다. 겹치면 **우리 것을 우선**하고, 인터뷰류(`grill-me`, `brainstorming`)만 쓰는 편이 덜 혼란스럽다.
설치는 전역 설정을 바꾸므로 직접 실행한다.

### 설치 없이 지금 바로 되는 방법
Claude Code 에는 **질문 도구(AskUserQuestion)** 가 있어서, 이렇게 요청하면 2~4개 선택지 UI로 한 번에 몇 개씩 물어본다:
```
> 질문 도구로 인터뷰해줘. 주제는 "외국인 근로자 안전 에이전트". 한 번에 1~2개씩, 선택지 4개로, 내가 정할 때까지 계속 물어봐.
> 결정이 다 나오면 docs/SCOPE.md 초안으로 정리해줘.
```
자주 쓰게 되면 `.claude/skills/grill/` 로 직접 만들어 두는 것도 방법이다 (`anthropic-skills:skill-creator`).

## 5. 해커톤 당일 호출 순서(안)

| 시각대 | 할 일 | 부를 것 |
|---|---|---|
| 미션 공개 직후 | 해석·주제 선택 | `/idea-judge` → (필요 시) `/grill-me` 로 구체화 |
| 초반 | 범위 확정 → 계획 | `docs/SCOPE.md` 채우기 → `/sprint` |
| 본 구현 | 스테이지 반복 | `/stage 1` … 사이사이 `/logger` |
| 중반 | 보안 점검 | `/security-review` + reviewer |
| 후반 | 승인 화면·문구 | `design:ux-copy` · `design:design-critique` |
| 마감 전 | 덱·데모 | `anthropic-skills:pptx` · `dataviz` |
| 끝 | 마무리 | `/done` |

## 6. 이 문서 관리

- 설치·삭제로 목록이 바뀌면 이 문서의 ⬇/🌐 표시를 고친다.
- 📄 표시가 붙은 항목은 쓰면서 본문을 읽고 호출 예를 보강한다.
- 새로 만든 스킬은 §2 표에 한 줄 추가한다.
