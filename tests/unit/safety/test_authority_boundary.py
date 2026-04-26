"""Authority-boundary canonical text validators.

Source of truth: docs/spec.md section 4.4.1 and
docs/schema-implementation-plan.md section 6.6.
"""

from __future__ import annotations

import pytest

from ao_radar_mcp.safety.authority_boundary import (
    HUMAN_AUTHORITY_BOUNDARY_TEXT,
    REQUIRED_CLAUSES,
    assert_boundary_text,
    validate_boundary_text,
)


def test_canonical_text_passes_required_clause_validator() -> None:
    result = validate_boundary_text(HUMAN_AUTHORITY_BOUNDARY_TEXT)
    assert result.ok, f"missing clauses: {result.missing_clauses}"
    assert result.missing_clauses == ()


def test_canonical_text_matches_spec_section_4_4_1_exactly() -> None:
    expected = (
        "AO Radar is a synthetic pre-decision review aid. It does not approve, "
        "deny, certify, return, cancel, amend, submit, determine entitlement, "
        "determine payability, accuse fraud, or contact external parties. The "
        "human Approving Official remains accountable for every official action "
        "in the official travel system."
    )
    assert HUMAN_AUTHORITY_BOUNDARY_TEXT == expected


def test_empty_text_fails() -> None:
    result = validate_boundary_text("")
    assert not result.ok
    assert "non_empty" in result.missing_clauses


def test_override_missing_fraud_clause_fails() -> None:
    weak = (
        "This is a synthetic review aid. It does not approve, deny, certify, "
        "return, cancel, amend, or submit any document. It does not determine "
        "entitlement or payability and does not contact external parties."
    )
    result = validate_boundary_text(weak)
    assert not result.ok
    assert "fraud" in result.missing_clauses


def test_override_missing_external_clause_fails() -> None:
    weak = (
        "Synthetic aid. Does not approve, deny, certify, return, cancel, "
        "amend, submit, determine entitlement, determine payability, or "
        "accuse fraud."
    )
    result = validate_boundary_text(weak)
    assert not result.ok
    assert "external" in result.missing_clauses


def test_assert_boundary_text_raises_on_weak_override() -> None:
    with pytest.raises(ValueError, match="missing required clauses"):
        assert_boundary_text("not a real boundary reminder")


def test_assert_boundary_text_returns_on_canonical() -> None:
    assert assert_boundary_text(HUMAN_AUTHORITY_BOUNDARY_TEXT) == HUMAN_AUTHORITY_BOUNDARY_TEXT


def test_required_clauses_cover_all_prohibited_action_categories() -> None:
    flat = {variants[0] for variants in REQUIRED_CLAUSES}
    expected = {
        "approve",
        "deny",
        "certify",
        "return",
        "cancel",
        "amend",
        "submit",
        "entitlement",
        "payability",
        "fraud",
        "external",
    }
    assert expected.issubset(flat)


def test_override_missing_negation_marker_fails() -> None:
    affirmative = (
        "AO Radar will approve, deny, certify, return, cancel, amend, submit, "
        "determine entitlement, determine payability, accuse fraud, and "
        "contact external parties as needed."
    )
    result = validate_boundary_text(affirmative)
    assert not result.ok
    assert "negation_marker" in result.missing_clauses
