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


def scan_forbidden_imports(package_dir: str | Path) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for path in sorted(Path(package_dir).rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if _is_forbidden(alias.name):
                        findings.append({"path": str(path), "line": node.lineno, "import": alias.name})
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if _is_forbidden(module):
                    findings.append({"path": str(path), "line": node.lineno, "import": module})
    return findings
