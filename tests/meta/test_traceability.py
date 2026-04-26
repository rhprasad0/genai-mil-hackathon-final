"""Lead-owned traceability matrix.

Per docs/testing-plan.md section 12, every spec FR/AC/TR maps to at least one
test file. This module:

  1. Lists the matrix as data (FR/AC/TR → repo-relative test paths).
  2. Asserts every named test path exists.
  3. Asserts every test path resolves to at least one ``test_*`` function so
     the file is not an empty shell.

The matrix is intentionally explicit: when a test is descoped, the entry
moves to ``KNOWN_GAPS`` in the same change. ``KNOWN_GAPS`` is empty at plan
publication.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Matrix: spec requirement → list of test paths that prove the requirement.
# Paths are repo-relative. Every path must exist; every path must contain at
# least one ``test_*`` function. Add tests, do not delete entries.
# ---------------------------------------------------------------------------

# Functional requirements (docs/spec.md section 3.4).
FR_MATRIX: dict[str, tuple[str, ...]] = {
    "FR-1": (
        "tests/fixtures/test_synthetic_markers.py",
        "tests/integration/test_brief_assembly.py",
    ),
    "FR-2": (
        "tests/unit/domain/test_story_analysis.py",
        "tests/integration/test_brief_assembly.py",
    ),
    "FR-3": (
        "tests/schema/test_evidence_refs_rules.py",
    ),
    "FR-4": (
        "tests/unit/domain/test_story_analysis.py",
        "tests/schema/test_signal_constraints.py",
    ),
    "FR-5": (
        "tests/contract/test_tools_list.py",
        "tests/fixtures/test_coverage_map.py",
    ),
    "FR-6": (
        "tests/unit/domain/test_missing_information.py",
        "tests/integration/test_brief_assembly.py",
    ),
    "FR-7": (
        "tests/unit/test_unsafe_wording.py",
        "tests/fixtures/test_unsafe_wording.py",
    ),
    "FR-8": (
        "tests/schema/test_finding_pointer.py",
        "tests/integration/test_brief_assembly.py",
    ),
    "FR-9": (
        "tests/unit/domain/test_priority.py",
        "tests/integration/test_brief_assembly.py",
    ),
    "FR-10": (
        "tests/safety/test_application_boundary.py",
        "tests/unit/test_refusal_builder.py",
        "tests/integration/test_refusal_audit.py",
    ),
    "FR-11": (
        "tests/integration/test_audit_invariants.py",
        "tests/fixtures/test_audit_invariants.py",
    ),
    "FR-12": (
        "tests/contract/test_export_review_brief_schema.py",
        "tests/integration/test_export_review_brief.py",
    ),
    "FR-13": (
        "tests/fixtures/test_signal_keys.py",
        "tests/fixtures/test_seeded_refusals.py",
        "tests/schema/test_finding_pointer.py",
    ),
    "FR-14": (
        "tests/integration/test_brief_assembly.py",
        "tests/contract/test_tools_list.py",
    ),
    "FR-15": (
        "tests/integration/test_audit_invariants.py",
        "tests/lambda_boundary/test_handler_routes.py",
    ),
    "FR-16": (
        "tests/unit/safety/test_controlled_status.py",
        "tests/schema/test_blocked_status.py",
    ),
}

# Acceptance criteria (docs/spec.md section 5).
AC_MATRIX: dict[str, tuple[str, ...]] = {
    "AC-1": (
        "tests/integration/test_brief_assembly.py",
        "tests/fixtures/test_volumes.py",
    ),
    "AC-2": (
        "tests/schema/test_finding_pointer.py",
        "tests/integration/test_brief_assembly.py",
    ),
    "AC-3": (
        "tests/unit/domain/test_missing_information.py",
        "tests/fixtures/test_coverage_map.py",
    ),
    "AC-4": (
        "tests/contract/test_tools_list.py",
        "tests/fixtures/test_unsafe_wording.py",
    ),
    "AC-5": (
        "tests/integration/test_brief_assembly.py",
        "tests/fixtures/test_partial_brief.py",
    ),
    "AC-6": (
        "tests/integration/test_refusal_audit.py",
        "tests/fixtures/test_seeded_refusals.py",
        "tests/e2e/refusal/test_blocked_status_deployed.py",
    ),
    "AC-7": (
        "tests/unit/test_refusal_builder.py",
        "tests/safety/test_application_boundary.py",
    ),
    "AC-8": (
        "tests/unit/domain/test_priority.py",
        "tests/fixtures/test_review_status_spread.py",
    ),
    "AC-9": (
        "tests/contract/test_export_review_brief_schema.py",
        "tests/integration/test_export_review_brief.py",
    ),
    "AC-10": (
        "tests/integration/test_audit_invariants.py",
        "tests/schema/test_authority_boundary.py",
    ),
    "AC-11": (
        "tests/fixtures/test_synthetic_markers.py",
        "tests/meta/test_public_safety_scanner.py",
    ),
    "AC-12": (
        "tests/unit/safety/test_authority_boundary.py",
        "tests/schema/test_authority_boundary.py",
    ),
    "AC-13": (
        "tests/fixtures/test_signal_keys.py",
        "tests/fixtures/test_seeded_refusals.py",
    ),
    "AC-14": (
        "tests/fixtures/test_signal_keys.py",
        "tests/integration/test_fraud_mock_invoke.py",
    ),
    "AC-15": (
        "tests/contract/test_tools_list.py",
        "tests/safety/test_repository_no_generic_sql.py",
    ),
    "AC-16": (
        "tests/schema/test_blocked_status.py",
        "tests/integration/test_audit_invariants.py",
    ),
}

# Trust requirements (docs/spec.md section 3.8).
TR_MATRIX: dict[str, tuple[str, ...]] = {
    "TR-1": (
        "tests/schema/test_blocked_status.py",
        "tests/safety/test_application_boundary.py",
    ),
    "TR-2": (
        "tests/safety/test_application_boundary.py",
        "tests/meta/test_vocabulary_scanner.py",
    ),
    "TR-3": (
        "tests/schema/test_signal_constraints.py",
        "tests/meta/test_vocabulary_scanner.py",
    ),
    "TR-4": (
        "tests/contract/test_tools_list.py",
        "tests/safety/test_application_boundary.py",
    ),
    "TR-5": (
        "tests/schema/test_finding_pointer.py",
        "tests/integration/test_brief_assembly.py",
    ),
    "TR-6": (
        "tests/unit/test_refusal_builder.py",
        "tests/integration/test_refusal_audit.py",
    ),
    "TR-7": (
        "tests/integration/test_brief_assembly.py",
        "tests/fixtures/test_partial_brief.py",
    ),
    "TR-8": (
        "tests/schema/test_data_environment.py",
        "tests/fixtures/test_synthetic_markers.py",
        "tests/meta/test_public_safety_scanner.py",
    ),
    "TR-9": (
        "tests/integration/test_audit_invariants.py",
        "tests/fixtures/test_audit_invariants.py",
    ),
    "TR-10": (
        "tests/schema/test_authority_boundary.py",
        "tests/unit/safety/test_authority_boundary.py",
    ),
    "TR-11": (
        "tests/safety/test_application_boundary.py",
        "tests/integration/test_refusal_audit.py",
    ),
    "TR-12": (
        "tests/safety/test_repository_no_generic_sql.py",
        "tests/contract/test_tools_list.py",
    ),
}

# Explicitly descoped tests with reasons. Empty at plan publication.
KNOWN_GAPS: dict[str, str] = {}


def _all_test_paths() -> set[str]:
    paths: set[str] = set()
    for matrix in (FR_MATRIX, AC_MATRIX, TR_MATRIX):
        for entries in matrix.values():
            paths.update(entries)
    return paths


def _file_has_test_function(path: Path) -> bool:
    """Return True if ``path`` contains at least one top-level ``test_*`` function."""

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return False
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            return True
        if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            for sub in node.body:
                if isinstance(sub, ast.FunctionDef) and sub.name.startswith("test_"):
                    return True
    return False


@pytest.mark.parametrize("rel_path", sorted(_all_test_paths()))
def test_traceability_path_exists(rel_path: str) -> None:
    full = REPO_ROOT / rel_path
    assert full.exists(), f"traceability matrix references missing file: {rel_path}"
    assert _file_has_test_function(full), (
        f"traceability matrix references {rel_path} but no ``test_*`` function found"
    )


@pytest.mark.parametrize("requirement", sorted(FR_MATRIX))
def test_every_fr_has_at_least_one_test(requirement: str) -> None:
    assert FR_MATRIX[requirement], f"{requirement} has no tests in matrix"


@pytest.mark.parametrize("requirement", sorted(AC_MATRIX))
def test_every_ac_has_at_least_one_test(requirement: str) -> None:
    assert AC_MATRIX[requirement], f"{requirement} has no tests in matrix"


@pytest.mark.parametrize("requirement", sorted(TR_MATRIX))
def test_every_tr_has_at_least_one_test(requirement: str) -> None:
    assert TR_MATRIX[requirement], f"{requirement} has no tests in matrix"


def test_known_gaps_documented() -> None:
    """Every entry in ``KNOWN_GAPS`` carries a non-empty reason string."""

    for requirement, reason in KNOWN_GAPS.items():
        assert reason and reason.strip(), f"{requirement} in KNOWN_GAPS without reason"


def test_traceability_test_trees_exist() -> None:
    """Sanity: the test trees referenced by the matrix exist."""

    for sub in ("fixtures", "meta", "schema", "lambda_boundary", "integration", "e2e", "unit", "contract", "safety"):
        assert (REPO_ROOT / "tests" / sub).exists(), f"tests/{sub} missing"


def test_fr_matrix_covers_fr_1_through_16() -> None:
    expected = {f"FR-{i}" for i in range(1, 17)}
    assert set(FR_MATRIX.keys()) == expected


def test_ac_matrix_covers_ac_1_through_16() -> None:
    expected = {f"AC-{i}" for i in range(1, 17)}
    assert set(AC_MATRIX.keys()) == expected


def test_tr_matrix_covers_tr_1_through_12() -> None:
    expected = {f"TR-{i}" for i in range(1, 13)}
    assert set(TR_MATRIX.keys()) == expected
