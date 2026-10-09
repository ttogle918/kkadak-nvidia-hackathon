"""의존성 없는 공용 헬퍼 — git head 조회와 색인 임시 사본. (stdlib 만 쓴다.)"""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

__all__ = ["git_head", "temp_copy"]


def git_head(root: Path) -> str | None:
    try:
        head = (root / ".git" / "HEAD").read_text(encoding="utf-8").strip()
        if not head.startswith("ref:"):
            return head or None
        ref = head.split(None, 1)[1]
        try:
            return (root / ".git" / ref).read_text(encoding="utf-8").strip() or None
        except OSError:
            for line in (root / ".git" / "packed-refs").read_text(encoding="utf-8").splitlines():
                if line.endswith(" " + ref):
                    return line.split()[0]
    except (OSError, IndexError):
        pass
    return None


@contextmanager
def temp_copy(src: Path) -> Iterator[Path]:
    """src 파일의 임시 사본 경로를 주고, 빠져나올 때 지운다. 원본은 열지 않는다."""
    with tempfile.TemporaryDirectory(prefix="kc_eval_") as td:
        copy = Path(td) / "index.db"
        shutil.copyfile(src, copy)
        yield copy
