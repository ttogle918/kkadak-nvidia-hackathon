"""평가 입구: ``uv run python eval/kc.py <run|validate|stability|snapshot-mentions|gen-judge> ...``

run·validate 는 여기서 실행한다. 나머지는 해당 모듈을 지연 import 해 ``main(argv) -> int`` 를 부른다
(모듈이 아직 없으면 "아직 없음", 종료 코드 2).
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

_EVAL = Path(__file__).resolve().parent
sys.path.insert(0, str(_EVAL.parent))  # 레포 루트 — domains·backend 를 부르는 offline 실행기용
sys.path.insert(0, str(_EVAL))  # kc_eval 패키지 (eval 은 패키지가 아니다)

_LAZY = {
    "stability": "kc_eval.stability",
    "snapshot-mentions": "kc_eval.snapshot_mentions",
    "gen-judge": "kc_eval.gen_judge",
}
_USAGE = "사용법: kc.py {run|validate|" + "|".join(_LAZY) + "} [옵션]"


def _lazy(command: str, argv: list[str]) -> int:
    name = _LAZY[command]
    try:
        mod = importlib.import_module(name)
    except ModuleNotFoundError as e:
        if e.name != name:
            raise  # 모듈 안의 다른 import 실패는 숨기지 않는다
        print(f"{command}: 아직 없음 ({name})", file=sys.stderr)
        return 2
    return int(mod.main(argv))


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(_USAGE)
        return 0 if argv else 2
    command, rest = argv[0], argv[1:]
    if command == "run":
        from kc_eval import offline

        return offline.main(rest)
    if command == "validate":
        from kc_eval import schema

        return schema.main_validate(rest)
    if command in _LAZY:
        return _lazy(command, rest)
    print(f"모르는 하위 명령: {command}\n{_USAGE}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
