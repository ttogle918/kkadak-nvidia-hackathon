#!/usr/bin/env python3
"""PreToolUse 훅: 사람 승인이 필요한 경로에 대한 Edit/Write 를 차단한다.

차단 대상
- `.env`, `.env.*` (단 `.env.example` 은 허용) — 비밀 파일. 키는 셸 env → 게이트웨이 provider 로만 (D1)
- `deploy/openshell/policy*.yaml` — 샌드박스 정책. 허용 추가는 이유와 실측 로그를 보고하고 사람이 승인한다
- `eval/testset.json` — 기대 정답 변경은 사람 승인 사항

exit 2 → 차단(stderr 가 Claude 에게 전달됨) · exit 0 → 통과.
파싱 실패 시 차단하지 않는다(훅이 개발을 막는 사고 방지).
"""
import json
import re
import sys

try:
    payload = json.load(sys.stdin)
except Exception:  # noqa: BLE001 — 파싱 실패로 개발을 막지 않는다
    sys.exit(0)

tool_input = payload.get("tool_input", {}) or {}
path = str(tool_input.get("file_path") or tool_input.get("path") or "").replace("\\", "/")
name = path.rsplit("/", 1)[-1]

if re.fullmatch(r"\.env(\..+)?", name) and name != ".env.example":
    print("차단: .env 계열은 비밀 파일입니다. 키는 셸 env 와 게이트웨이 provider 에만 둡니다 "
          "(docs/DECISIONS.md D1). .env.example 만 수정하세요.", file=sys.stderr)
    sys.exit(2)

if "/deploy/openshell/" in f"/{path}" and re.fullmatch(r"policy.*\.ya?ml", name):
    print("차단: OpenShell 정책 변경은 사람 승인이 필요합니다. 추가하려는 허용·이유·"
          "실측 로그(ALLOWED/DENIED)를 보고하고 승인을 받으세요.", file=sys.stderr)
    sys.exit(2)

if path.endswith("eval/testset.json"):
    print("차단: eval/testset.json 의 기대 정답 변경은 사람 승인이 필요합니다. "
          "이유를 보고하고 승인을 받으세요.", file=sys.stderr)
    sys.exit(2)

sys.exit(0)
