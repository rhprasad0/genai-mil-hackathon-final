"""Static import policy scan for the mock-only package."""

from __future__ import annotations

import ast
from pathlib import Path


FORBIDDEN_IMPORT_ROOTS = frozenset(
    {
        "openai",
        "anthropic",
        "google.generativeai",
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "urllib",
        "urllib3",
        "subprocess",
    }
)


def _is_forbidden(name: str) -> bool:
    for forbidden in FORBIDDEN_IMPORT_ROOTS:
        if name == forbidden or name.startswith(forbidden + "."):
            return True
    return False


def _is_allowed_adapter_path(path: Path) -> bool:
    parts = path.parts
    return "policy_bonfire" in parts and "live_adapters" in parts


def scan_forbidden_imports(package_dir: str | Path) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for path in sorted(Path(package_dir).rglob("*.py")):
        adapter_boundary = _is_allowed_adapter_path(path)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if _is_forbidden(alias.name) and not adapter_boundary:
                        findings.append({"path": str(path), "line": node.lineno, "import": alias.name})
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if _is_forbidden(module) and not adapter_boundary:
                    findings.append({"path": str(path), "line": node.lineno, "import": module})
    return findings
