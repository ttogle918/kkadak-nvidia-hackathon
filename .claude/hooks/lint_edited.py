#!/usr/bin/env python3
"""PostToolUse 훅: 방금 편집한 .py 파일 하나만 `ruff check --fix` 로 점검한다.

- 안전한 자동 수정만 한다(미사용 import 등). `ruff format` 은 켜지 않는다 — 리뷰 가능한 diff 유지.
- uv 가 없으면 **조용히 넘어가지 않고** stderr 로 알린다(종료코드는 0 — 훅이 개발을 막지 않는다).
- `.claude/skills/` 는 NVIDIA 카탈로그라 건드리지 않는다.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

try:
    payload = json.load(sys.stdin)
except Exception:  # noqa: BLE001 — 파싱 실패로 개발을 막지 않는다
    sys.exit(0)

tool_input = payload.get("tool_input", {}) or {}
raw = str(tool_input.get("file_path") or tool_input.get("path") or "")
path = Path(raw) if raw else None
if not path or path.suffix != ".py":
    sys.exit(0)
if not path.is_absolute():
    path = ROOT / path
if not path.exists() or ".claude/skills" in path.as_posix():
    sys.exit(0)

if shutil.which("uv") is None:
    print("[lint_edited] uv 를 찾지 못해 ruff 점검을 건너뜁니다.", file=sys.stderr)
    sys.exit(0)

try:
    proc = subprocess.run(["uv", "run", "ruff", "check", "--fix", str(path)],
                          cwd=ROOT, capture_output=True, text=True, timeout=60, check=False)
except (subprocess.SubprocessError, OSError) as exc:
    print(f"[lint_edited] ruff 실행 실패: {exc}", file=sys.stderr)
    sys.exit(0)

out = (proc.stdout or "").strip()
if proc.returncode != 0 and out:
    print(f"[lint_edited] {path.name}\n{out}", file=sys.stderr)
sys.exit(0)
