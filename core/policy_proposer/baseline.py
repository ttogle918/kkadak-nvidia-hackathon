"""기본 정책 베이스라인 — `deploy/openshell/policy.yaml` 과 같은 값(golden 테스트로 대조).

런타임에 deploy 파일을 읽지 않는다.
"""

VERSION = 1
INCLUDE_WORKDIR = False
READ_ONLY = ("/usr", "/lib", "/etc", "/proc", "/dev/urandom", "/app")
READ_WRITE = ("/tmp", "/dev/null")
LANDLOCK_COMPAT = "best_effort"
RUN_AS_USER = "1000"
RUN_AS_GROUP = "1000"
NEVER_WRITE = ("/usr", "/lib", "/etc", "/proc", "/dev", "/app")
GATEWAY_HOSTS = ("inference.local",)

# --- 제안 허용 루트 (허용 목록, fail-closed) ---
# 문서 미확인 가정: NemoClaw/OpenShell 문서에서 에이전트 workspace 경로를 확인하지 못했다.
# 그래서 가장 흔한 관례인 /sandbox · /workspace 두 개만 최소로 둔다. 확인되면 이 값만 고친다.
# /tmp 는 이미 READ_WRITE 베이스라인이라 제안 대상이 아니다.
# 쓰기 제안은 이 루트 아래에서만 낸다. 그 밖은 Skipped(사람이 판단).
WRITE_PROPOSAL_ROOTS = ("/sandbox", "/workspace")
# 읽기 제안 허용 루트: 쓰기 루트 + 읽기 전용 시스템 디렉터리(실행·라이브러리). 거부 목록으로는
# /root·/home/*/.ssh·소켓 등 열거하지 못한 민감 경로가 새므로 읽기도 허용 목록을 쓴다.
# (/sys·/boot·/run·/var·/mnt·/home 은 의도적으로 제외 — 필요하면 사람이 추가)
READ_PROPOSAL_ROOTS = WRITE_PROPOSAL_ROOTS + ("/bin", "/sbin", "/lib32", "/lib64", "/opt")
