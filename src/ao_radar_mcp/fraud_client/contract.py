"""Pydantic request/response contract for the fraud-mock Lambda.

Sources of truth:
  - docs/application-implementation-plan.md section 9.
  - docs/schema-implementation-plan.md section 5.7.

Both the MCP-side client and the fraud-mock Lambda import these models so
the request envelope and response shape cannot drift.  Every signal is
labeled as a review prompt only (``is_official_finding=False`` and
``not_sufficient_for_adverse_action=True``).
"""

from __future__ import annotations

from datetime import datetime
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field


SIGNAL_TYPES: Final[tuple[str, ...]] = (
    "duplicate_payment_risk",
    "high_risk_mcc_demo",
    "unusual_amount",
    "date_location_mismatch",
    "split_disbursement_oddity",
    "repeated_correction_pattern",
    "peer_baseline_outlier",
    "traveler_baseline_outlier",
)

SIGNAL_CONFIDENCES: Final[tuple[str, ...]] = ("low", "medium", "high")
ALLOWED_DATA_ENVIRONMENT: Final[str] = "synthetic_demo"


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class FraudMockRequest(_Frozen):
    """Request envelope sent from the MCP Lambda to the fraud-mock Lambda."""

    voucher_id: str
    data_environment: str
    requested_signal_types: tuple[str, ...] = ()
    line_item_ids: tuple[str, ...] = ()


class FraudSignal(_Frozen):
    """One synthetic signal returned by the fraud-mock Lambda."""

    voucher_id: str
    signal_key: str
    signal_id: str
    signal_type: Literal[
        "duplicate_payment_risk",
        "high_risk_mcc_demo",
        "unusual_amount",
        "date_location_mismatch",
        "split_disbursement_oddity",
        "repeated_correction_pattern",
        "peer_baseline_outlier",
        "traveler_baseline_outlier",
    ]
    synthetic_source_label: str
    rationale_text: str
    confidence: Literal["low", "medium", "high"]
    is_official_finding: bool = Field(default=False)
    not_sufficient_for_adverse_action: bool = Field(default=True)
    received_at: datetime


class FraudMockResponse(_Frozen):
    """Response envelope from the fraud-mock Lambda."""

    voucher_id: str
    data_environment: str
    signals: tuple[FraudSignal, ...] = ()


def derive_signal_id(voucher_id: str, signal_key: str) -> str:
    """Derive the deterministic ``signal_id`` from voucher_id + signal_key.

    Format documented in docs/schema-implementation-plan.md section 5.7.
    """

    safe_voucher = voucher_id.strip()
    safe_key = signal_key.strip()
    if not safe_voucher or not safe_key:
        raise ValueError("voucher_id and signal_key must be non-empty")
    return f"SIG-{safe_voucher}-{safe_key}"


__all__ = [
    "ALLOWED_DATA_ENVIRONMENT",
    "FraudMockRequest",
    "FraudMockResponse",
    "FraudSignal",
    "SIGNAL_CONFIDENCES",
    "SIGNAL_TYPES",
    "derive_signal_id",
]
