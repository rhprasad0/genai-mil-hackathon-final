"""Static guardrail: repository modules expose no generic SQL access.

Source of truth: docs/spec.md section 3.3 (no raw SQL), section 4.3
(prohibited tools), docs/testing-plan.md section 6 G2.

The scanner walks the AST so docstrings and comments that *describe* the
absence of generic data access (e.g. "No ``execute_sql``…") are not flagged
as violations.  We look at function names, attribute references, call
expressions, and import names.
"""

from __future__ import annotations

import ast
import pathlib

import pytest


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_SCAN_DIRS = (
    _REPO_ROOT / "src" / "ao_radar_mcp" / "tools",
    _REPO_ROOT / "src" / "ao_radar_mcp" / "repository",
)
_FORBIDDEN_NEEDLES: tuple[str, ...] = (
    "query_database",
    "execute_sql",
    "run_query",
    "read_file",
    "list_dir",
    "download_file",
    "fetch_url",
    "http_get",
)
_FORBIDDEN_CALLABLES: tuple[str, ...] = (
    "eval",
    "os.system",
    "subprocess.run",
    "subprocess.Popen",
    "subprocess.call",
)


def _collect_identifiers(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                names.add(func.id)
            elif isinstance(func, ast.Attribute):
                names.add(func.attr)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
                if alias.asname:
                    names.add(alias.asname)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            names.add(module)
            for alias in node.names:
                names.add(alias.name)
                if alias.asname:
                    names.add(alias.asname)
    return names


def _collect_call_expression_strings(tree: ast.AST) -> set[str]:
    """Collect dotted names of every callable expression."""

    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            out.add(_dotted_name(node.func))
    return out


def _dotted_name(node: ast.AST) -> str:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    parts.reverse()
    return ".".join(parts)


@pytest.mark.parametrize("needle", _FORBIDDEN_NEEDLES)
def test_no_forbidden_identifier_appears_in_tools_or_repository(needle: str) -> None:
    for scan_dir in _SCAN_DIRS:
        for path in scan_dir.rglob("*.py"):
            tree = ast.parse(path.read_text())
            names = _collect_identifiers(tree)
            assert needle not in names, f"{path}: forbidden identifier {needle}"


@pytest.mark.parametrize("callable_name", _FORBIDDEN_CALLABLES)
def test_no_forbidden_callable_appears_in_tools_or_repository(callable_name: str) -> None:
    for scan_dir in _SCAN_DIRS:
        for path in scan_dir.rglob("*.py"):
            tree = ast.parse(path.read_text())
            calls = _collect_call_expression_strings(tree)
            assert callable_name not in calls, (
                f"{path}: forbidden callable {callable_name}"
            )
