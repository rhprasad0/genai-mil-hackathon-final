"""Unit tests for ``ao_radar_mcp.safety.unsafe_wording``.

Source of truth: docs/schema-implementation-plan.md section 6.4 and
docs/application-implementation-plan.md section 11.
"""

from __future__ import annotations

import pytest

from ao_radar_mcp.safety.unsafe_wording import check, is_safe


@pytest.mark.parametrize(
    "phrase",
    [
        "Voucher is approved.",
        "This voucher is paid.",
        "The reviewer should approve the voucher.",
        "Recommend approval for this packet.",
        "System has approved the voucher.",
    ],
)
def test_official_disposition_phrases_rejected(phrase: str) -> None:
    result = check(phrase)
    assert not result.is_safe
    assert result.reason == "system_authored_official_disposition"


@pytest.mark.parametrize(
    "phrase",
    [
        "Traveler is fraudulent.",
        "Vendor committed fraud.",
        "This is misuse of the program.",
        "Transaction appears to be fraudulent.",
    ],
)
def test_fraud_allegations_rejected(phrase: str) -> None:
    result = check(phrase)
    assert not result.is_safe
    assert result.reason == "system_authored_fraud_allegation"


@pytest.mark.parametrize(
    "phrase",
    [
        "System has determined entitlement.",
        "Determined to be payable.",
        "Officially entitled to reimbursement.",
        "This expense is not payable.",
        "The traveler is not entitled to reimbursement.",
        "This is not payable and the traveler is not entitled to reimbursement.",
    ],
)
def test_entitlement_payability_rejected(phrase: str) -> None:
    result = check(phrase)
    assert not result.is_safe
    assert result.reason == "system_authored_entitlement_or_payability"


@pytest.mark.parametrize(
    "phrase",
    [
        "AO Radar contacted the traveler about this voucher.",
        "We notified the investigator.",
        "Emailed the traveler regarding the receipt.",
    ],
)
def test_external_contact_rejected(phrase: str) -> None:
    result = check(phrase)
    assert not result.is_safe
    assert result.reason == "system_authored_external_contact"


@pytest.mark.parametrize(
    "phrase",
    [
        "AO Radar does not approve, deny, certify, return, or submit any voucher.",
        "This is not an official approval.",
        "The system does not contact external parties.",
        "Refused with reason prohibited_action.",
        "Review prompt only; not sufficient for adverse action.",
    ],
)
def test_negative_boundary_phrases_allowed(phrase: str) -> None:
    assert is_safe(phrase), f"expected safe: {phrase}"


def test_empty_text_is_safe() -> None:
    assert is_safe("")
    assert is_safe("    ")


def test_neutral_review_language_allowed() -> None:
    text = (
        "Lodging line 3 has no attached receipt. Reviewer should ask the "
        "traveler to provide a receipt; this is review prompt language and "
        "does not approve, deny, or certify the voucher."
    )
    assert is_safe(text)


def test_fraud_phrase_inside_negative_boundary_still_rejected() -> None:
    """External-contact / fraud phrases are not whitewashed by a negative phrase."""

    text = (
        "AO Radar does not approve any voucher. We contacted the traveler "
        "about this transaction."
    )
    result = check(text)
    assert not result.is_safe
    assert result.reason == "system_authored_external_contact"
