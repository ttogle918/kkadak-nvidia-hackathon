import importlib

import pytest

PACKAGES = [
    "core",
    "core.hitl",
    "core.guard",
    "core.audit",
    "core.policy_proposer",
    "mcp_server",
    "mcp_server.tools",
    "backend",
    "backend.routers",
]


@pytest.mark.parametrize("name", PACKAGES)
def test_package_imports(name):
    importlib.import_module(name)
