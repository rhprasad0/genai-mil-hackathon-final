"""Unit tests for ``ao_radar_mcp.domain.story_analysis``.

Source of truth: docs/application-implementation-plan.md section 7 step D.
"""

from __future__ import annotations

from datetime import date

from ao_radar_mcp.domain.story_analysis import (
    EvidenceSnapshot,
    LineItemSnapshot,
    TripWindow,
    analyze,
    detect_amount_mismatches,
    detect_evidence_quality_concerns,
    detect_out_of_window_expenses,
)


_WINDOW = TripWindow(
    voucher_id="V-TEST-1003",
    trip_start=date(2026, 3, 1),
    trip_end=date(2026, 3, 5),
)


def _line(line_id: str, expense_date: date | None, amount: int = 12000) -> LineItemSnapshot:
    return LineItemSnapshot(
        line_item_id=line_id,
        line_index=int(line_id.split("-")[-1]),
        expense_date=expense_date,
        amount_minor_units=amount,
        currency_code="USD",
        category="lodging",
        vendor_label="Hotel Coastal Demo",
    )


def _evidence(
    ev_id: str,
    line_id: str | None,
    *,
    amount_on_face: int | None = None,
    legibility: str = "clear",
    itemization: str = "itemized",
    content: str = "receipt_pdf_demo",
) -> EvidenceSnapshot:
    return EvidenceSnapshot(
        evidence_ref_id=ev_id,
        line_item_id=line_id,
        content_type_indicator=content,
        legibility_cue=legibility,
        itemization_cue=itemization,
        payment_evidence_cue="present",
        vendor_label_on_evidence="Hotel Coastal Demo",
        evidence_date_on_face=None,
        amount_on_face_minor_units=amount_on_face,
        currency_code_on_face="USD" if amount_on_face is not None else None,
    )


def test_detect_out_of_window_expense_flags_outside_dates() -> None:
    items = (
        _line("LI-TEST-1", date(2026, 3, 2)),
        _line("LI-TEST-2", date(2026, 4, 1)),
    )
    findings = detect_out_of_window_expenses(_WINDOW, items)
    assert len(findings) == 1
    assert findings[0].category == "date_window_mismatch"
    assert findings[0].packet_evidence_pointer["line_item_id"] == "LI-TEST-2"


def test_detect_out_of_window_expense_handles_missing_dates() -> None:
    items = (_line("LI-TEST-1", None),)
    assert detect_out_of_window_expenses(_WINDOW, items) == ()


def test_detect_amount_mismatch_flags_diff() -> None:
    items = (_line("LI-TEST-1", date(2026, 3, 2), amount=12000),)
    evidence = (_evidence("EV-TEST-1", "LI-TEST-1", amount_on_face=15000),)
    findings = detect_amount_mismatches(items, evidence)
    assert len(findings) == 1
    assert findings[0].category == "amount_mismatch"
    assert findings[0].contributing_evidence_ids == ("EV-TEST-1",)


def test_detect_amount_mismatch_skips_when_evidence_amount_missing() -> None:
    items = (_line("LI-TEST-1", date(2026, 3, 2), amount=12000),)
    evidence = (_evidence("EV-TEST-1", "LI-TEST-1", amount_on_face=None),)
    assert detect_amount_mismatches(items, evidence) == ()


def test_detect_evidence_quality_concern_flags_none_attached() -> None:
    evidence = (
        _evidence("EV-TEST-1", "LI-TEST-1", content="none_attached_demo",
                  legibility="not_applicable", itemization="not_applicable"),
    )
    findings = detect_evidence_quality_concerns(evidence)
    assert len(findings) == 1
    assert findings[0].category == "missing_receipt"


def test_detect_evidence_quality_concern_flags_poor_legibility() -> None:
    evidence = (_evidence("EV-TEST-1", "LI-TEST-1", legibility="poor"),)
    findings = detect_evidence_quality_concerns(evidence)
    assert len(findings) == 1
    assert findings[0].category == "evidence_quality_concern"


def test_analyze_composes_all_helpers() -> None:
    items = (
        _line("LI-TEST-1", date(2026, 3, 2), amount=12000),
        _line("LI-TEST-2", date(2026, 4, 1), amount=8000),
    )
    evidence = (
        _evidence("EV-TEST-1", "LI-TEST-1", amount_on_face=15000),
        _evidence("EV-TEST-2", "LI-TEST-2", legibility="poor"),
    )
    result = analyze("V-TEST-1003", _WINDOW, items, evidence)
    categories = {f.category for f in result.findings}
    assert categories == {
        "date_window_mismatch",
        "amount_mismatch",
        "evidence_quality_concern",
    }
    assert result.review_prompt_only is True
