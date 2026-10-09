"""``kc_eval`` 을 import 할 수 있게 ``<repo>/eval`` 을 sys.path 앞에 넣는다 (sprint-3 §5.0)."""

import sys
from pathlib import Path

_EVAL = str(Path(__file__).resolve().parents[2] / "eval")
if _EVAL not in sys.path:
    sys.path.insert(0, _EVAL)
