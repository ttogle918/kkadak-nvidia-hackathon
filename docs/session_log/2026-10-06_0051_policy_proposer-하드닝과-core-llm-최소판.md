# policy_proposer 하드닝과 core/llm 최소판
**일시**: 2026-10-06 00:51 · **브랜치**: master · **범위**: D4·D5 승인·반영 → Stage 2 T202(policy_proposer) reviewer 4회 끝에 PASS → Stage 3 T303(core/llm 최소판) PASS. Sprint 1 필수 경로 완료. 별도로 logger·done 스킬 모델 지정.

## 완료
- **D4·D5 결정 반영** (`72c8d83`) — `docs/DECISIONS.md`, `docs/SCOPE.md`(`core/llm` 을 "지금 안 만들 것"에서 빼고 선택 항목 5번으로), `docs/sprints/sprint-1.md`(T303 명세·Stage 3 표·§2.4·§5·§7 문구).
- **T202 policy_proposer** (`bd9e3a2`) — `core/policy_proposer/{__init__,model,baseline,propose,render}.py`, `tests/core/policy_proposer/test_proposer_{propose,render,hardening}.py`. pytest 389 → 566. audit/v1 → OpenShell 정책 YAML 초안, 상태는 `draft` 고정·자동 적용 경로 없음.
- **T303 core/llm 최소판** (`c9d9f5a`) — `core/llm/{__init__,config,pool,client}.py`, `deploy/llm.example.yaml`, `tests/core/llm/test_llm_{config,pool,client}.py`. pytest 566 → 607. `core/audit` 는 수정하지 않음.
- **logger·done 스킬에 `model: sonnet` 지정** (`20a9a63`) — `.claude/skills/{logger,done}/SKILL.md`.
- Sprint 1 필수 경로(T101~T104, T201, T202) 완료, Stage 2 게이트 충족.

## 결정과 맥락
### D4 — policy_proposer 의 입력은 audit/v1 (2026-10-06 승인)
- **계기**: SCOPE 가 관찰 기록 형식을 스프린트에서 정하라고 위임. OpenShell 로그 형식을 문서로 확인하지 못했고, 도구 호출은 MCP 서버 안에서만 보임.
- **대안**: OpenShell 로그 직접 파싱 / 두 형식 직접 수용 / OCSF JSON 입력 — 형식 미확인·분기 증가·존재 미확인으로 기각. 어댑터(T302)로 audit/v1 net 이벤트로 바꿔 넣는 구조. 문안은 `docs/DECISIONS.md`.

### D5 — core/llm: 기능별 라우팅·동시 호출·키 풀 (2026-10-06 승인)
- **계기**: 사용자가 "기능마다 다른 LLM 호출, 병목 없이 동시 호출, API 키 여러 개"를 요청. SCOPE 의 "지금 안 만들 것"과 충돌해 결정으로 남기고 SCOPE 를 수정.
- **키 방식**: `NVIDIA_API_KEY_A`·`_B` 처럼 env 변수 **이름만** 설정에 적고 호출 시 읽는다. 키 값은 코드·설정·리포·로그에 없다(D1·규칙 1).
- **"샌드박스 밖 전용"의 뜻**: 기준은 `.env` 가 아니라 호출 코드가 어디서 도느냐. 호스트에서 도는 코드는 `.env` 키를 읽어도 되고, 샌드박스 안은 D1 에 따라 `inference.local` 만 쓰며 키는 게이트웨이 provider 에만 둔다. mcp_server 가 어디서 도는지, 게이트웨이의 다중 provider·모델 라우팅 지원은 **문서 미확인**이라 이번엔 호스트 경로만. 설정 구조는 게이트웨이 provider 이름으로 바꿔 끼울 수 있게 `resolve_keys` 한 곳에 모음.
- **feature**: 미션 공개(10/7) 전이라 `# TODO: feature1, feature2 채우기` + placeholder.
- **대안**: 단일 모델·키 고정 / 샌드박스 안 키 풀 주입(D1 위반) / 기능 확정 후 구현(당일 일정 때문에 기각).

### T202: 거부 목록 → 허용 목록으로 구조 전환 (reviewer 3차 FAIL 뒤)
- **계기**: 1~3차 모두 "정책 본문으로 나가는 외부 값을 거부 목록으로 걸러서" 같은 계열 우회가 라운드마다 하나씩 나옴. 3차 결과를 보고 개별 입력 대신 구조를 바꾸기로 하고 `dev` 에게 허용 목록 전환을 지시.
- **내용**: host 는 소문자 ASCII hostname/IPv4 형식, method 는 7종, rule path·binary·fs path 는 ASCII 문자 집합, fs 읽기·쓰기는 허용 루트(`READ_PROPOSAL_ROOTS`·`WRITE_PROPOSAL_ROOTS`) 아래만. 의심 입력은 제안하지 않고 Skipped 로 남긴다(fail-closed). 비밀 값을 `***REDACTED***` 로 바꿔 본문에 쓰지 않는다(`*` 가 glob 일 수 있어서).
- **대안**: 거부 목록 계속 보강 — 라운드마다 새 우회가 나와 수렴하지 않아 기각. 값을 REDACTED 로 치환 — glob 으로 해석될 수 있어 기각.
- **수렴 판단**: 4차 reviewer 가 "남은 지적은 문서 미확인 가정이거나 초안 + 사람 승인 게이트가 있는 상태의 낮은 위험 강화 항목이라 PASS 가능"으로 구분. 반복 재작업을 여기서 멈춤.
- **from_json 재검증 실패는 propose 전체 실패(AuditFormatError)로 유지**: 줄 하나를 Skipped 로 넘기면 변조된 줄로 근거를 조용히 지울 수 있어서(reviewer 판단). 대신 이벤트 번호를 메시지에 붙임.
- **쓰기 제안은 거의 안 나온다**: baseline 밖 쓰기 경로는 "사람이 판단"으로 Skipped. 데모에 필요하면 허용 루트를 같이 정해야 함.

### T303 최소판 범위
- **포함**: 설정 검증, KeyPool 라운드로빈·쿨다운, `LlmClient.complete`(async, provider 별 Semaphore, 주입식 transport), audit call/result/error.
- **제외**: 실제 HTTP transport(Protocol 과 가짜 구현까지), 스트리밍, 재시도 고도화, 비용 집계, 게이트웨이 연결.
- **PyYAML 이 없어 최소 YAML 부분집합 파서를 직접 작성**(한 줄 `{...}` 항목만, `.json` 도 읽음). reviewer 가 조용한 오파싱을 점검해 W4·W5 로 기록.
- **알 수 없는 feature·잘못된 messages 는 audit 전에 거부**: 외부 호출(부수효과)이 생기기 전이라 감사할 호출이 없다는 reviewer 판단. 호출자가 넣은 임의 문자열이 audit name 에 들어가지 않는 효과도 있음.
- **async `audited` 를 만들지 않음**: `AuditLog.call/result/error` 를 client 에서 직접 호출. §5 의 "T303 착수 시 최소 범위" 조건은 쓰지 않았다.

### logger 를 에이전트로 옮기는 안 — 옮기지 않기로 (사용자 제안에 대한 내 의견, 구조 변경은 하지 않음)
- 서브 에이전트는 대화를 볼 수 없어 "결정과 맥락"을 못 쓴다. fork 는 항상 메인 세션 모델로 돌아 sonnet 지정이 무시된다. `/logger` 명령도 사라진다. 지금 구조로 중복은 이미 해소(`done` 이 logger 스킬 형식을 참조). 모델 지정만 `model: sonnet` 으로 반영.
- **에이전트 모델 현황**: pm·reviewer = opus, dev·eval-runner = sonnet. 메인 세션은 `~/.claude/settings.json` 의 sonnet. 보안 하드닝 작업에서는 dev(sonnet)가 라운드마다 우회를 하나씩 남겼으므로 dev 를 opus 로 올리는 선택지가 있음(비용·속도 트레이드오프, 미정).

## 트러블슈팅
### reviewer 1~3차 FAIL — T202 정책 본문 값 처리 (코드 추적만으로 판정, 재현 입력을 dev 가 테스트로 만들어 확인)
- **1차 (B1~B3)**: 외부 jsonl 의 host·path·binary 가 redact·검증 없이 본문에 나감(비밀이 리포에 들어갈 경로). `/data/../app/x` 로 NEVER_WRITE 우회. `Inference.Local`·`inference.local.` 로 게이트웨이 제외(D1) 우회. 해결: `_unsafe` 검사, 정규화 후 비교, host strip·lower·끝 `.` 제거.
- **2차 (B4·B5)**: `/`·`/data/..`·`//` 가 정규화되어 `read_write: /` 제안(전체 쓰기). 주체 불명 이벤트(binary None·상대 경로)의 rule 이 유효 binary 에 귀속. 해결: `/` 거부·양방향 NEVER_WRITE 검사, 유효 binary 를 가진 이벤트만으로 rules·evidence 생성.
- **3차 (B6·B7)**: fs 쓰기가 NEVER_WRITE 거부 목록에만 의존해 `/bin`·`/sbin`·`/lib64`·`/sys`·`/run`·`docker.sock` 이 제안됨(merged-usr 이미지에서 `/bin` 은 `/usr/bin` 링크). `binaries` 가 거부된 rule 의 이벤트까지 포함. 해결: 허용 루트 방식, `binaries` 를 채택된 이벤트에서 계산, binary 별 항목 분할.
- **교훈**: 거부 목록 방식은 라운드마다 새 우회가 나온다. 구조 전환 시점을 더 일찍(2차 뒤) 잡았어야 한다.
- **커밋**: `bd9e3a2`

### 변형 실험의 거짓 신호
- dev 의 변형 실험에서 NEVER_WRITE 양방향 검사를 단방향으로 되돌려도 테스트가 안 빨개졌다(`/` 를 먼저 거부해 이중 방어라서) → 허용 루트 전환 후 monkeypatch 로 2단계 항목(`/var/lib/x`)을 넣는 테스트 추가. ASCII 대문자 변환 변형이 처음엔 살아남아 `poſt`·`optıons` 케이스 추가. 스크립트로 적용한 변형이 실제 적용 안 된 경우가 있었다(문법 오류·적용 실패) → "실제 적용을 diff 로 확인"을 dev 지시에 추가.

### 테스트 skip 1건
- **증상**: 2차 재작업 뒤 `454 passed, 1 skipped`. **원인**: `test_bad_rule_path` 의 빈 path parametrize 케이스가 `pytest.skip` 으로 건너뛰는 자리표시자. **해결**: 케이스 삭제, skip 0 으로. **미확인**: 빈 path → `/` 정규화를 직접 검증하는 별도 테스트가 있는지는 확인하지 못함.

## 검증 상태
- 회귀(CLAUDE.md 회귀 절 기준): `uv run python -m pytest -q` **607 passed**(skip 0, 전체 2회·`tests/core/llm` 5회 동일, 플레이크 없음) · `uv run ruff check .` 통과.
- reviewer: Stage 2 T202 4차 **PASS**(1~3차 FAIL), Stage 3 T303 **PASS**(블로커 0, 경고 9). reviewer 는 읽기 전용이라 직접 실행 없이 코드·테스트를 읽어 추적한 판정.
- `eval/` 에는 README 만 있어 평가셋 실행은 해당 없음. 정책 스키마·허용 루트·rest 항목 중복은 문서 미확인(아래).
- 프론트(`frontend/web/`)의 실제 브라우저 확인은 이번 세션에서도 하지 않음.

## 다음 세션
1. **10/7 09:00 미션 공개 후**: `docs/SCOPE.md` 의 미션 절 갱신, `domains/<name>/` 채우기, `deploy/llm.example.yaml` 의 `feature1·feature2` 를 실제 기능 이름으로, 모델명은 문서 확인 후 확정.
2. **`searchDocs` 확인**(MCP 가 로드된 세션에서): `openshell policy schema network_policies` — T202 스키마 대조, 같은 host:port 에 rest 항목 복수 허용 여부, rule path 매칭 방식, sandbox 홈·설정 경로(`WRITE_PROPOSAL_ROOTS` 근거), 게이트웨이 다중 provider·모델 라우팅(T303 의 게이트웨이 연결).
3. **T303 경고 우선 처리**: W1(붙여 넣은 키 방어)·W2(`__context__` 에 `api_key` 지역변수 traceback)가 규칙 1 관련이라 먼저. 이어 W4(`isfinite`)·W5(중복 거부)·W3(테스트 표지)·W7(취소 경로 테스트).
4. **T202 경고**: W-A(binary 위치를 시스템 실행 루트로 제한)·W-B(사설·메타데이터 사유 주석, ASCII 전용 lower)·W-E(허용 루트 sanity 양방향).
5. **이월 태스크**: T202-opt(정보성 항목) · T301(초안 → hitl 제출) · T302(OpenShell 로그 어댑터, 문서 확인 후).
6. **Stage 1 권고 중 미처리**: guard 개행 오탐 강등 · redact 패턴 보강 · `core/hitl/db.py` docstring 한계 문구 · 100자 초과 줄 3곳 · `sprint-1.md` §6 명세 본문을 코드에 맞춰 동기화.
7. **다음 스프린트 후보**: mcp_server 엔트리포인트·도구, backend 승인 API, 프로세스·DB 파일 권한 분리(hitl 의 W1·W2·W6 근본 해결), MCP 도구로 `core/llm` 을 노출할 때 `audited`·guard 적용.

## 사람 승인 대기
- [ ] **쓰기·읽기 허용 루트 값**: `WRITE_PROPOSAL_ROOTS = ("/sandbox", "/workspace")`, `READ_PROPOSAL_ROOTS` 에 `/opt` 포함 여부 — 문서 미확인 가정. 실제 경로를 알면 `core/policy_proposer/baseline.py` 상수만 수정.
- [ ] **dev 에이전트 모델 상향**(sonnet → opus) 여부.
- [ ] **hitl 이월 3건 수용 여부**(W1·W2·W6, 이전 세션부터): 트리거로 더 막을지 이월할지.
- [ ] **guard 개행 사본 오탐**: high → medium 강등 여부(이전 세션부터).
- [ ] **`frontend/`**: 커밋하지 않고 둠(사용자 지시). `frontend/CLAUDE.md` 의 파일 형식 절 갱신 여부는 이전 세션부터 미결.
