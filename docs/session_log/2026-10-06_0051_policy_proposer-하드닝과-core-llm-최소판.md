# policy_proposer 하드닝과 core/llm 최소판
**일시**: 2026-10-06 00:51 · **브랜치**: master · **범위**: D4·D5 승인·반영 → Stage 2 T202(policy_proposer) reviewer 4회 끝에 PASS → Stage 3 T303(core/llm 최소판) PASS → 대회 전날 준비(환경 점검 스크립트·API 백엔드 스위치 D6) → `nemoclaw-docs` MCP 재연결 후 문서 확인(정책 스키마·OCSF 로그·샌드박스 경로·추론 route) → T202 `name`=키 수정. Sprint 1 필수 경로 완료. 갱신 01:19.

## 완료
- **D4·D5 결정 반영** (`72c8d83`) — `docs/DECISIONS.md`, `docs/SCOPE.md`(`core/llm` 을 "지금 안 만들 것"에서 빼고 선택 항목 5번으로), `docs/sprints/sprint-1.md`(T303 명세·Stage 3 표·§2.4·§5·§7 문구).
- **T202 policy_proposer** (`bd9e3a2`) — `core/policy_proposer/{__init__,model,baseline,propose,render}.py`, `tests/core/policy_proposer/test_proposer_{propose,render,hardening}.py`. pytest 389 → 566. audit/v1 → OpenShell 정책 YAML 초안, 상태는 `draft` 고정·자동 적용 경로 없음.
- **T303 core/llm 최소판** (`c9d9f5a`) — `core/llm/{__init__,config,pool,client}.py`, `deploy/llm.example.yaml`, `tests/core/llm/test_llm_{config,pool,client}.py`. pytest 566 → 607. `core/audit` 는 수정하지 않음.
- **logger·done 스킬에 `model: sonnet` 지정** (`20a9a63`) — `.claude/skills/{logger,done}/SKILL.md`.
- Sprint 1 필수 경로(T101~T104, T201, T202) 완료, Stage 2 게이트 충족.
- **D6 + API↔로컬 백엔드 스위치** (`d5c6935`) — `core/llm/{config,client,__init__}.py`, `deploy/llm.example.yaml`, `tests/core/llm/test_llm_backend.py`, `docs/DECISIONS.md`. `LLM_BACKEND`·`LLM_BACKEND_<FEATURE>` 로 엔드포인트만 전환, 키 풀·세마포어는 (provider, backend) 별 분리, local 키가 api 키와 겹치면 거부, 기능 이름 정규화 충돌 거부.
- **환경 점검 스크립트와 `.env.example`** (`d5c6935`) — `scripts/preflight.sh`(읽기 전용, `--live` 키 검증), `.env.example`(`NVIDIA_API_KEY_A/_B`·`NGC_API_KEY`·`LLM_BACKEND` 이름 추가, 값 없음).
- **T202 `name` = 정책 키 수정** (`fc0f876`) — `core/policy_proposer/{propose,render,model}.py`, `test_proposer_render.py`. `render.py` docstring 을 문서 확인 결과에 맞게 정리.
- **대회 전날 준비 점검 문서** (gitignore, 미커밋) — `docs/private/대회 전날 준비 점검과 남은 작업.md`(적용 상태·남은 작업·단계별 NVIDIA 스킬·데이터 묶음·문서 확인 결과 10절).
- `docs/sprints/sprint-1.md` 에 Stage 3 T303 기록·T303 경고 W1~W9·문서 확인 후속 추가.

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

### D6 — 백엔드(api|local) 전환, 키는 provider 단위, 자동 폴백 없음 (2026-10-06, `docs/DECISIONS.md`)
- **계기**: "로컬 Nemotron 이 안 뜨면 환경변수 하나로 API 로 넘어가게" 요청. 사용자가 "환경변수 하나로 바꾸면 기능별로 다른 키를 쓰는 설계와 충돌한다"고 지적해, 전환 대상을 키가 아니라 **엔드포인트**로 한정했다. 이 PC 는 GPU 가 없어(`nvidia-smi` 없음) API 가 사실상 기본.
- **대안**: 환경변수 하나로 키까지 교체(기능별 키와 충돌) / 실패 시 자동 재시도로 다른 백엔드 사용(요청 본문이 의도치 않게 외부로 나갈 수 있고 추적이 흐려짐) / 호출마다 env 재읽기(실행 중 엔드포인트 변경) — 모두 기각.
- **reviewer 경고 반영**: 세마포어를 provider 단위로 두면 느린 로컬이 같은 provider 의 api 호출을 막는다 → `(provider, backend)` 분리. local 키가 api 키와 겹치면 NVIDIA 키가 로컬 서버로 갈 수 있다 → 거부. 기능 이름 `a.b`·`a-b` 가 같은 변수를 쓴다 → 거부. `local_base_url` 루프백 제한은 transport 구현 시로 미룸.

### 대회 준비 점검에서의 판단
- **"모든 NVIDIA 스킬 적용"**: 설치된 카탈로그(404 디렉터리)의 설명을 직접 읽어 단계별로 맞는 것만 매핑했다. TAO·DOCA·Jetson 등 무관한 것을 억지로 쓰면 "if문으로 바꿔도 되는 데모"가 되어 심도 평가에 손해라는 판단. `tao-run-on-brev`·`nemo-rl-brev-etiquette` 는 TAO·RL 전용이라 Brev 일반 세팅에 안 맞고, `rag-blueprint` 는 하루 대회에 과함. NeMo Guardrails 는 스킬이 아니라 라이브러리.
- **이 PC 환경(실측)**: GPU 없음·Brev CLI 없음·git 원격 없음·키 없음(`.env` 없음). 게이트웨이 provider `nvidia-prod` 는 등록돼 있으나 키가 지금도 유효한지는 미확인. 그래서 새 인스턴스 스크립트는 clone 단계를 끝까지 못 돌려 본다 → GitHub 원격 생성 승인이 선결.
- **원격 push 는 하지 않았다**(외부로 나가는 작업이라 승인 필요). `maintq*` 샌드박스는 다른 프로젝트 것이라 읽지도 않았다.

### 문서 확인 결과가 바꾼 것 (`nemoclaw-docs` MCP 재연결 후)
- **후보 2 관건 해소**: OpenShell 은 OCSF v1.8.0 JSONL 내보내기를 제공한다(`openshell settings set <sandbox> --key ocsf_json_enabled --value true`, 샌드박스 안 `/var/log/openshell-ocsf.YYYY-MM-DD.log`). 차단 레코드에 `dst_endpoint.domain/port`·`actor.process.name`·`action=Denied` 가 있다. method·path·타임스탬프 필드명은 문서에 없음. 일반 로그(`openshell logs`)는 텍스트이고 JSON 플래그 없음(`--help` 확인). → T302 착수 근거 확보, 실측 캡처 필요. WebFetch 는 작은 모델의 요약이라 원문 대조 권장.
- **`name` 은 정책 키와 같아야 한다**(NemoClaw 스키마가 강제, 어기면 온보딩 실패). 우리 초안은 `key.replace("_","-")` 로 어긋나 있었다. 이 변환은 **프리셋 이름 규칙(밑줄 금지)과 네트워크 정책 항목 이름을 혼동**한 것으로 보인다. T202 reviewer 4회 PASS 에서도 못 잡은 결함 — 스키마를 문서로 확인한 적이 없었기 때문.
- **샌드박스 경로**: 기본 쓰기는 `/sandbox`·`/tmp` 뿐. `/workspace` 는 문서에 없다(가정이었음). 에이전트 설정이 `/sandbox/.openclaw` 등에 있어 이 경로의 쓰기 제안은 자기 설정 변조가 된다 → `NEVER_WRITE` 추가 필요(미수정).
- **추론 route**: 샌드박스당·게이트웨이당 활성 route 는 하나. 기능별 다른 provider·키는 **호스트에서 도는 코드 경로에서만** 가능하고, 샌드박스 안은 Model Router provider 가 가장 가깝다. mcp_server 의 실행 위치(호스트/샌드박스)는 미확인 — 기능별 키의 사용 범위를 정한다.

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

### `preflight.sh --live` 의 거짓 PASS — 키 검증이 안 됨
- **증상**: 가짜 키(`dummy-not-a-key`)로 `--live` 를 돌렸더니 `[PASS] build.nvidia.com 응답 200`. **원인**: `/v1/models` 는 인증 없이도 200 이라 키 검증에 쓸 수 없다(실측: 채팅 호출은 가짜 키에 401). **해결**: 인증이 필요한 최소 채팅 호출(`max_tokens=1`)로 교체, 가짜 키가 401 로 FAIL 이 나는 것을 확인. **미확인**: 진짜 키로 200 이 나는 경로(키 없음). **커밋**: `d5c6935`.

### `--live` 에서 키가 curl 인자에 노출 (reviewer 경고)
- **원인**: `-H "Authorization: Bearer $val"` 는 `ps`·`/proc/<pid>/cmdline` 에 보인다(공유 Brev 인스턴스에서 실제 유출 경로). **해결**: `printf 'header = "..."' | curl -K -` 로 stdin 설정에 전달. **검증**: 처음 시도한 `ps | grep -c` 점검은 `sh -c` 명령줄에 더미 문자열이 들어 있어 거짓 신호(3)였다 → 가짜 `curl` 로 argv 를 기록해 argv 에 키 0건·stdin 에 1건 확인, 로컬 HTTP 서버로 `Authorization` 헤더가 실제 전달되는 것도 확인. **커밋**: `d5c6935`.

### 정책 항목 `name` 이 키와 달라 온보딩 실패 가능 (문서 확인으로 발견)
- **원인**: `NetworkEntry.name = key.replace("_","-")`. 스키마 문서는 `name` 이 정책 키와 같아야 한다고 명시. **해결**: `name == key`, 신규 테스트 `test_network_entry_name_equals_key`(여러 항목·tcp·해시 접미사·binary 별 분할 포함), 되돌리면 2건이 빨개지는 변형 실험. 재검토(reviewer) 없이 테스트로만 확인. **커밋**: `fc0f876`.
- **교훈**: 4회 PASS 한 코드도 가정으로 만든 스키마 부분은 못 지킨다. 문서가 열리면 가정 목록부터 대조한다.

## 검증 상태
- 회귀(CLAUDE.md 회귀 절 기준): `uv run python -m pytest -q` **636 passed**(skip 0; `tests/core/llm` 8회 반복 동일) · `uv run ruff check .` 통과. 직전 로그 시점 607건에서 +29(백엔드 스위치·경고 수정·name 수정).
- **재검토 없이 테스트로만 확인한 변경**: 백엔드 스위치의 경고 수정분(세마포어 분리·키 겹침·이름 충돌), `name`=키 수정.
- reviewer: Stage 2 T202 4차 **PASS**(1~3차 FAIL), Stage 3 T303 **PASS**(블로커 0, 경고 9). reviewer 는 읽기 전용이라 직접 실행 없이 코드·테스트를 읽어 추적한 판정.
- `eval/` 에는 README 만 있어 평가셋 실행은 해당 없음. 정책 스키마·허용 루트·rest 항목 중복은 문서 미확인(아래).
- 프론트(`frontend/web/`)의 실제 브라우저 확인은 이번 세션에서도 하지 않음.

## 다음 세션
1. **후보 2 OCSF 실측 캡처**(임시 샌드박스 생성 승인 필요): `ocsf_json_enabled` 를 켜고 거부 요청 1건을 발생시켜 실제 JSONL 레코드의 method·path·시간 필드를 확인 → T302 어댑터(OCSF JSONL → audit/v1 net 이벤트) 구현. `maintq*` 샌드박스는 다른 프로젝트 것이라 승인 없이 읽지 않는다.
2. **T202 후속 수정**: `WRITE_PROPOSAL_ROOTS` 에서 `/workspace` 제거, `/sandbox/.openclaw`·`.hermes`·`.deepagents`·`.nemoclaw` 를 `NEVER_WRITE` 에 추가(문서 확인 근거: filesystem-controls), 테스트·변형 실험, 재검토.
3. **준비물**: GitHub private 원격 생성·push(승인) → `scripts/bootstrap.sh`(새 인스턴스용, 멱등·`--dry-run`) 작성 → Brev 로그인 후 새 인스턴스에서 1회 실행해 소요 시간 기록. 두 노트북에서 `scripts/preflight.sh --live`, `NVIDIA_API_KEY`(+`_A`/`_B`) export 후 `scripts/gateway_setup.sh` 로 provider 재등록.
4. **데이터 묶음**(`data-designer`, 키 필요): 공개 인버터 매뉴얼 인덱스(`nemo-retriever`), 합성 수리 이력·판례 카드 10여 건, 숨은 지시를 심은 주입 테스트 문서 1개, 합성 GPU 오류 로그. 라이선스·실제 코드 의미는 확인한 것만.
5. **후보 1 확인**: Wokwi→Brev MQTT 도달, Parakeet 의 "인버터"·"컨베이어" 인식(합성 음성 오류율). 텍스트 입력 폴백.
6. **10/7 09:00 미션 공개 후**: `docs/SCOPE.md` 미션 절 갱신, `domains/<name>/` 채우기, `deploy/llm.example.yaml` 의 `feature1·feature2` 를 실제 기능 이름으로, 모델명은 문서 확인 후 확정.
7. **문서 미확인으로 남은 것**: OCSF 차단 레코드의 method/path·타임스탬프 필드명 · mcp_server 의 실행 위치(호스트/샌드박스) · `openshell gateway info`·`provider list`·`sandbox list`, `brev ls` 가 상태를 바꾸지 않는지 · rule path 퍼센트 디코딩·접두 일치 · 같은 host:port rest 항목 다중의 명시적 허용 여부.
8. **코드 이월(대회 후)**: `core/llm` 경고 W1·W2(키 노출 방어)·W4·W5·W6·W9·`local_base_url` 루프백 제한(실제 transport 구현 시), T202 경고 W-A·W-B·W-E, T301·T202-opt, hitl 이월 3건, guard 개행 오탐, Stage 1 권고 중 미처리(redact 패턴·docstring·100자 초과 줄·§6 명세 동기화). 상세는 `docs/sprints/sprint-1.md` 의 "이월 · 미결".
9. 다음 스프린트 후보: mcp_server 엔트리포인트·도구, backend 승인 API, 프로세스·DB 권한 분리, MCP 도구로 `core/llm` 노출 시 `audited`·guard 적용.

## 사람 승인 대기
- [ ] **GitHub private 원격 저장소 생성·push**(새 인스턴스 clone 의 전제, 외부로 나가는 작업).
- [ ] **후보 2 검증용 임시 샌드박스 생성**(`maintq*` 는 건드리지 않음).
- [ ] **두 노트북 점검**: `scripts/preflight.sh --live` 결과, 키 export, Brev 설치·로그인·크레딧.
- [ ] **쓰기·읽기 허용 루트 값**: `/workspace` 는 문서에 없음을 확인 → 제거 승인. 읽기 루트(`/bin`·`/sbin`·`/lib32`·`/lib64`·`/opt`)가 의도에 맞는지.
- [ ] **dev 에이전트 모델 상향**(sonnet → opus) 여부(보안 하드닝 라운드가 길어진 점 고려).
- [ ] **hitl 이월 3건(W1·W2·W6) 수용 여부**, **guard 개행 오탐 강등 여부**(이전 세션부터).
- [ ] **`frontend/`**: 커밋하지 않고 둠(사용자 지시). `frontend/CLAUDE.md` 파일 형식 절 갱신 여부는 이전 세션부터 미결.
