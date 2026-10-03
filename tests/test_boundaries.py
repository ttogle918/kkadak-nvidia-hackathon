"""경계 정적 테스트 — D3(import 방향·도메인 용어)와 D2(review·db 사용 금지).

한계: 정적 스캔은 정직한 코드의 실수를 막는다. 동적 우회(문자열 조립 후 ``__import__`` 등)까지는
막지 못한다(``getattr(core.hitl, 'connect')`` 의 문자열 인자, 변수 재할당 후 별칭, 섀도잉 등).
``core.hitl.<이름>`` 속성 접근과 ``import ... as`` 별칭은 AST 로 잡는다. 실제 격리는 프로세스·파일 권한 분리의 몫이다(T101 한계와 같다).
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

MCP_HITL_ALLOWED = frozenset(
    {
        "Draft",
        "DraftState",
        "DraftWriter",
        "HitlError",
        "DraftNotFound",
        "TransitionError",
        "SelfApprovalError",
        "DraftValidationError",
        "SchemaMissingError",
        "DbNotFoundError",
    }
)

DOMAIN_TERMS = (
    "maintq",
    "설비",
    "에러코드",
    "정비",
    "발주",
    "수리",
    "equipment",
    "maintenance",
    "purchase_order",
    "purchase order",
    "work_order",
    "work order",
    "error_code",
)


def py_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)


def _import_names(path: Path, root: Path) -> list[tuple[str, str | None]]:
    """(module, alias_name) 쌍. Import 는 alias_name=None, module=alias.name."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    pkg = list(path.resolve().relative_to(root.resolve()).parent.parts)
    out: list[tuple[str, str | None]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.extend((a.name, None) for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level > 0:
                keep = len(pkg) - (node.level - 1)
                base_parts = pkg[: max(keep, 0)]
                module = ".".join([*base_parts, *([module] if module else [])])
            out.extend((module, a.name) for a in node.names)
    return out


def imported_modules(path: Path, *, root: Path = REPO) -> set[str]:
    names: set[str] = set()
    for module, alias in _import_names(path, root):
        names.add(module)
        if alias is not None:
            names.add(f"{module}.{alias}" if module else alias)
    return names


def _matches(name: str, prefix: str) -> bool:
    return name == prefix or name.startswith(prefix + ".")


def forbidden_imports(
    root: Path, prefixes: tuple[str, ...], *, base: Path = REPO
) -> list[tuple[Path, str]]:
    found: list[tuple[Path, str]] = []
    for path in py_files(root):
        for name in sorted(imported_modules(path, root=base)):
            if any(_matches(name, p) for p in prefixes):
                found.append((path, name))
    return found


def forbidden_strings(
    root: Path, needles: tuple[str, ...], *, glob: str = "*.py"
) -> list[tuple[Path, int, str]]:
    found: list[tuple[Path, int, str]] = []
    if not root.exists():
        return found
    lowered = [n.lower() for n in needles]
    for path in sorted(p for p in root.rglob(glob) if "__pycache__" not in p.parts):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            low = line.lower()
            for needle, low_needle in zip(needles, lowered, strict=True):
                if low_needle in low:
                    found.append((path, lineno, needle))
    return found


def hitl_import_violations(root: Path, *, base: Path = REPO) -> list[tuple[Path, str]]:
    found: list[tuple[Path, str]] = []
    for path in py_files(root):
        for module, alias in _import_names(path, base):
            if alias is None:  # import X
                if _matches(module, "core.hitl"):
                    found.append((path, f"import {module}"))
            elif module == "core":
                if alias == "hitl" or alias == "*":
                    found.append((path, f"from core import {alias}"))
            elif module == "core.hitl":
                if alias not in MCP_HITL_ALLOWED:
                    found.append((path, f"from core.hitl import {alias}"))
            elif module.startswith("core.hitl."):
                found.append((path, f"from {module} import {alias}"))
        found.extend((path, d) for d in hitl_attribute_violations(path))
    return found


def _alias_map(tree: ast.AST) -> dict[str, str]:
    """바인딩 이름 -> 정규화된 점 경로. ``import core.x`` 는 ``core`` 를 ``core`` 에 묶는다."""
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.asname:
                    aliases[a.asname] = a.name
                else:
                    top = a.name.split(".")[0]
                    aliases[top] = top
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            for a in node.names:
                aliases[a.asname or a.name] = f"{node.module}.{a.name}"
    return aliases


def _attr_chain(node: ast.Attribute) -> tuple[str, list[str]] | None:
    attrs: list[str] = []
    cur: ast.expr = node
    while isinstance(cur, ast.Attribute):
        attrs.append(cur.attr)
        cur = cur.value
    if not isinstance(cur, ast.Name):
        return None
    return cur.id, attrs[::-1]


def hitl_attribute_violations(path: Path) -> list[str]:
    """``core.hitl.<이름>`` 속성 접근(별칭 포함) 중 허용 목록 밖 이름 또는 모듈 객체 자체."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    aliases = _alias_map(tree)
    inner = {id(n.value) for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute) or id(node) in inner:
            continue  # 최대 체인만 본다
        chain = _attr_chain(node)
        if chain is None or chain[0] not in aliases:
            continue
        full = [*aliases[chain[0]].split("."), *chain[1]]
        if full[:2] != ["core", "hitl"]:
            continue
        if len(full) == 2 or full[2] not in MCP_HITL_ALLOWED:
            found.append("attr " + ".".join(full))
    return found


def _write(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------- 실제 레포 (D3, D2)


def test_mcp_server_does_not_import_backend():
    assert forbidden_imports(REPO / "mcp_server", ("backend",)) == []


def test_backend_does_not_import_mcp_server():
    assert forbidden_imports(REPO / "backend", ("mcp_server",)) == []


def test_core_does_not_import_app_layers():
    assert forbidden_imports(REPO / "core", ("mcp_server", "backend", "domains")) == []


def test_core_has_no_domain_terms():
    # core/README.md 는 금지어를 예시로 들고 있어 제외 — glob 이 *.py 라 README 는 보지 않는다.
    assert forbidden_strings(REPO / "core", DOMAIN_TERMS) == []


def test_mcp_server_cannot_import_hitl_review():
    assert forbidden_imports(REPO / "mcp_server", ("core.hitl.review",)) == []


def test_mcp_server_hitl_imports_allowlisted():
    assert hitl_import_violations(REPO / "mcp_server") == []


def test_mcp_server_does_not_use_sqlite_directly():
    assert forbidden_imports(REPO / "mcp_server", ("sqlite3",)) == []


def test_mcp_server_forbidden_strings():
    needles = ("sqlite3", "hitl.review", "hitl.db", "_connect_reviewer", "_open_existing")
    assert forbidden_strings(REPO / "mcp_server", needles) == []


# ---------------------------------------------------------------- 스캐너 자기 검증


def test_scanner_handles_missing_and_empty_dirs(tmp_path):
    assert py_files(tmp_path / "nope") == []
    assert forbidden_imports(tmp_path / "nope", ("backend",), base=tmp_path) == []
    assert forbidden_strings(tmp_path / "nope", ("x",)) == []
    assert hitl_import_violations(tmp_path / "nope", base=tmp_path) == []
    (tmp_path / "empty").mkdir()
    assert forbidden_imports(tmp_path / "empty", ("backend",), base=tmp_path) == []


def test_scanner_detects_absolute_import(tmp_path):
    _write(tmp_path, "mcp_server/a.py", "import backend.routers\n")
    got = forbidden_imports(tmp_path / "mcp_server", ("backend",), base=tmp_path)
    assert [n for _, n in got] == ["backend.routers"]


def test_scanner_does_not_flag_prefix_lookalike(tmp_path):
    _write(tmp_path, "mcp_server/a.py", "import backend_utils\n")
    assert forbidden_imports(tmp_path / "mcp_server", ("backend",), base=tmp_path) == []


def test_scanner_detects_from_import_submodule(tmp_path):
    _write(tmp_path, "mcp_server/a.py", "from core.hitl import review\n")
    got = forbidden_imports(tmp_path / "mcp_server", ("core.hitl.review",), base=tmp_path)
    assert [n for _, n in got] == ["core.hitl.review"]


def test_scanner_detects_relative_import(tmp_path):
    _write(tmp_path, "core/__init__.py", "")
    _write(tmp_path, "core/x/__init__.py", "")
    _write(tmp_path, "core/x/a.py", "from ..hitl import review\nfrom .. import backend\n")
    got = forbidden_imports(tmp_path / "core", ("core.hitl.review", "core.backend"), base=tmp_path)
    assert {n for _, n in got} == {"core.hitl.review", "core.backend"}


def test_scanner_detects_domain_term_case_insensitive(tmp_path):
    _write(tmp_path, "core/a.py", "x = 'MaintQ'\ny = '설비'\nz = 'Work Order'\nok = 1\n")
    got = forbidden_strings(tmp_path / "core", DOMAIN_TERMS)
    assert sorted((ln, n) for _, ln, n in got) == [(1, "maintq"), (2, "설비"), (3, "work order")]


def test_scanner_detects_importlib_string(tmp_path):
    _write(tmp_path, "mcp_server/a.py", "m = importlib.import_module('core.hitl.review')\n")
    got = forbidden_strings(tmp_path / "mcp_server", ("hitl.review",))
    assert len(got) == 1


def test_scanner_raises_on_syntax_error(tmp_path):
    import pytest

    _write(tmp_path, "mcp_server/a.py", "def (:\n")
    with pytest.raises(SyntaxError):
        forbidden_imports(tmp_path / "mcp_server", ("backend",), base=tmp_path)


def test_allowlist_flags_connect(tmp_path):
    _write(tmp_path, "mcp_server/a.py", "from core.hitl import connect\n")
    assert len(hitl_import_violations(tmp_path / "mcp_server", base=tmp_path)) == 1


def test_allowlist_flags_module_import(tmp_path):
    _write(tmp_path, "mcp_server/a.py", "import core.hitl\n")
    _write(tmp_path, "mcp_server/b.py", "from core import hitl\n")
    _write(tmp_path, "mcp_server/c.py", "import core.hitl.db\n")
    got = hitl_import_violations(tmp_path / "mcp_server", base=tmp_path)
    assert {p.name for p, _ in got} == {"a.py", "b.py", "c.py"}


def test_allowlist_flags_db_submodule(tmp_path):
    _write(tmp_path, "mcp_server/a.py", "from core.hitl.db import connect\n")
    assert len(hitl_import_violations(tmp_path / "mcp_server", base=tmp_path)) == 1


def test_allowlist_flags_relative_import(tmp_path):
    # mcp_server/sub/a.py 에서 level=3 은 루트까지 올라간다 -> core.hitl
    _write(tmp_path, "mcp_server/sub/a.py", "from ...core.hitl import init_db\n")
    got = hitl_import_violations(tmp_path / "mcp_server", base=tmp_path)
    assert len(got) == 1


def test_allowlist_permits_draftwriter(tmp_path):
    _write(tmp_path, "mcp_server/a.py", "from core.hitl import DraftWriter, DraftState\n")
    assert hitl_import_violations(tmp_path / "mcp_server", base=tmp_path) == []


# ---------------------------------------------------------------- 속성 접근 우회 (W5)


def test_attr_access_via_import_core_flagged(tmp_path):
    _write(tmp_path, "mcp_server/a.py", "import core\ncore.hitl.connect('x')\n")
    _write(tmp_path, "mcp_server/b.py", "import core.audit\ncore.hitl.init_db('x')\n")
    _write(tmp_path, "mcp_server/c.py", "import core\nx = core.hitl.review\n")
    _write(tmp_path, "mcp_server/d.py", "import core\nx = core.hitl.db.connect\n")
    _write(tmp_path, "mcp_server/e.py", "import core\nx = core.hitl._connect_reviewer\n")
    got = hitl_import_violations(tmp_path / "mcp_server", base=tmp_path)
    assert {p.name for p, _ in got} == {"a.py", "b.py", "c.py", "d.py", "e.py"}


def test_attr_access_via_alias_flagged(tmp_path):
    _write(tmp_path, "mcp_server/a.py", "import core.hitl as h\nh.connect('x')\n")
    _write(tmp_path, "mcp_server/b.py", "from core import hitl as h\nh.review\n")
    _write(tmp_path, "mcp_server/c.py", "import core as c\nc.hitl.init_db('x')\n")
    got = hitl_import_violations(tmp_path / "mcp_server", base=tmp_path)
    attr = [(p.name, d) for p, d in got if d.startswith("attr ")]
    assert {n for n, _ in attr} == {"a.py", "c.py", "b.py"}


def test_attr_access_bare_module_flagged(tmp_path):
    # 모듈 객체를 값으로 넘기는 것도 우회 통로다.
    _write(tmp_path, "mcp_server/a.py", "import core\nm = core.hitl\n")
    got = hitl_import_violations(tmp_path / "mcp_server", base=tmp_path)
    assert len(got) == 1


def test_attr_access_allowed_names_pass(tmp_path):
    _write(
        tmp_path,
        "mcp_server/a.py",
        "import core\n"
        "import core.audit as audit\n"
        "w = core.hitl.DraftWriter\n"
        "s = core.hitl.DraftState.PENDING\n"
        "audit.log_event\n",
    )
    assert hitl_import_violations(tmp_path / "mcp_server", base=tmp_path) == []


def test_attr_access_unrelated_names_pass(tmp_path):
    _write(tmp_path, "mcp_server/a.py", "import os\nx = os.hitl.connect\nhitl = 1\nhitl.connect\n")
    assert hitl_import_violations(tmp_path / "mcp_server", base=tmp_path) == []
