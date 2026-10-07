import os
import tempfile

# backend.app 은 import 시 모듈 수준 app 을 만든다. 레포의 var/ 를 건드리지 않게 먼저 돌린다.
_TMP = tempfile.mkdtemp(prefix="kc_backend_")
os.environ.setdefault("KC_HITL_DB", os.path.join(_TMP, "hitl.db"))
os.environ.setdefault("KC_AUDIT_DIR", os.path.join(_TMP, "audit"))
os.environ.setdefault("KC_OUTPUT_DIR", os.path.join(_TMP, "output"))
os.environ.pop("APP_PROCESS_ROLE", None)
