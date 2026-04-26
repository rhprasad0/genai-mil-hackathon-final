"""Unit tests for ``ao_radar_mcp.domain.brief_assembly``.

Source of truth: docs/application-implementation-plan.md section 7 step D.
"""

from __future__ import annotations

import os

import pytest

from ao_radar_mcp.domain.brief_assembly import (
    BriefInputs,
    assemble,
    render_json,
    render_markdown,
)
from ao_radar_mcp.safety.authority_boundary import HUMAN_AUTHORITY_BOUNDARY_TEXT


@pytest.fixture
def _inputs() -> BriefInputs:
    return BriefInputs(
        voucher_id="V-TEST-1003",
        finding_ids=("FIND-TEST-1", "FIND-TEST-2"),
        missing_information_ids=("MISS-TEST-1",),
        signal_ids=("SIG-TEST-1",),
        citation_ids=("CITE-TEST-1",),
        priority_score=0.4231,
        priority_rationale="workload-only",
        suggested_focus="Lodging line evidence",
        evidence_gap_summary="Two evidence rows weak on legibility.",
        story_coherence_summary="One out-of-window expense.",
        draft_clarification_note=(
            "Could the traveler clarify the date and amount on the lodging line? "
            "This draft is non-official and the system does not approve, deny, "
            "or certify the voucher."
        ),
        brief_uncertainty="medium",
        is_partial=False,
    )


def test_assemble_populates_hooks(_inputs: BriefInputs) -> None:
    draft = assemble(_inputs)
    assert draft.voucher_id == "V-TEST-1003"
    assert draft.finding_hooks == ("FIND-TEST-1", "FIND-TEST-2")
    assert draft.missing_information_hooks == ("MISS-TEST-1",)
    assert draft.policy_hooks == ("CITE-TEST-1",)
    assert draft.signal_hooks == ("SIG-TEST-1",)
    assert draft.brief_uncertainty == "medium"


def test_assemble_includes_canonical_boundary_text(
    _inputs: BriefInputs, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("BOUNDARY_REMINDER_TEXT", raising=False)
    draft = assemble(_inputs)
    assert draft.human_authority_boundary_text == HUMAN_AUTHORITY_BOUNDARY_TEXT


def test_assemble_rejects_unknown_uncertainty(_inputs: BriefInputs) -> None:
    bad = BriefInputs(**{**_inputs.__dict__, "brief_uncertainty": "extreme"})
    with pytest.raises(ValueError):
        assemble(bad)


def test_render_markdown_contains_boundary_and_hooks(_inputs: BriefInputs) -> None:
    draft = assemble(_inputs)
    md = render_markdown(draft)
    assert "AO Radar Review Brief — V-TEST-1003" in md
    assert "policy_hooks: ['CITE-TEST-1']" in md
    assert HUMAN_AUTHORITY_BOUNDARY_TEXT in md


def test_render_json_serializes_all_fields(_inputs: BriefInputs) -> None:
    draft = assemble(_inputs)
    payload = render_json(draft)
    assert payload["voucher_id"] == "V-TEST-1003"
    assert payload["finding_hooks"] == ["FIND-TEST-1", "FIND-TEST-2"]
    assert payload["human_authority_boundary_text"] == HUMAN_AUTHORITY_BOUNDARY_TEXT
    assert payload["brief_uncertainty"] == "medium"
