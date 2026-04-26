"""Unit tests for ``ao_radar_mcp.domain.missing_information``.

Source of truth: docs/application-implementation-plan.md section 7 step D.
"""

from __future__ import annotations

from datetime import date

from ao_radar_mcp.domain.missing_information import (
    detect_lines_without_evidence,
    detect_packet_level_gaps,
)
from ao_radar_mcp.domain.story_analysis import EvidenceSnapshot, LineItemSnapshot


def _line(line_id: str) -> LineItemSnapshot:
    return LineItemSnapshot(
        line_item_id=line_id,
        line_index=int(line_id.split("-")[-1]),
        expense_date=date(2026, 3, 2),
        amount_minor_units=10000,
        currency_code="USD",
        category="meals",
        vendor_label="Meals Vendor Demo",
    )


def _evidence(line_id: str | None, *, content: str = "receipt_pdf_demo") -> EvidenceSnapshot:
    return EvidenceSnapshot(
        evidence_ref_id=f"EV-{line_id or 'PACKET'}",
        line_item_id=line_id,
        content_type_indicator=content,
        legibility_cue="clear",
        itemization_cue="itemized",
        payment_evidence_cue="present",
        vendor_label_on_evidence=None,
        evidence_date_on_face=None,
        amount_on_face_minor_units=None,
        currency_code_on_face=None,
    )


def test_detect_lines_without_evidence_flags_unmatched_lines() -> None:
    lines = (_line("LI-TEST-1"), _line("LI-TEST-2"))
    evidence = (_evidence("LI-TEST-1"),)
    out = detect_lines_without_evidence(lines, evidence)
    assert len(out) == 1
    assert out[0].linked_line_item_id == "LI-TEST-2"


def test_detect_lines_without_evidence_treats_none_attached_as_missing() -> None:
    lines = (_line("LI-TEST-1"),)
    evidence = (_evidence("LI-TEST-1", content="none_attached_demo"),)
    out = detect_lines_without_evidence(lines, evidence)
    assert len(out) == 1


def test_detect_packet_level_gaps_lists_each_missing_attachment() -> None:
    out = detect_packet_level_gaps(False, False, False)
    descriptions = {row.description for row in out}
    assert "No trip itinerary attached to the packet." in descriptions
    assert "No authorization snapshot attached to the packet." in descriptions
    assert "No funding reference attachment is on file." in descriptions


def test_detect_packet_level_gaps_returns_empty_when_present() -> None:
    assert detect_packet_level_gaps(True, True, True) == ()
