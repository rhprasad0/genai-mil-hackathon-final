"""Pydantic / dataclass models shared by repository modules.

Sources of truth:
  - docs/schema-implementation-plan.md sections 5 and 6.

The repository layer never returns raw psycopg rows to upstream code; it
returns these typed shapes so tools see structured data with the canonical
column names.  Pydantic v2 is the canonical model framework (see
``pyproject.toml``).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class _Frozen(BaseModel):
    """Frozen base model with strict-extra rejection."""

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)


class TravelerRow(_Frozen):
    traveler_id: str
    display_name: str
    role_label: str
    home_unit_label: str
    typical_trip_pattern: str
    prior_correction_summary: str
    data_environment: str
    created_at: datetime


class PriorVoucherSummaryRow(_Frozen):
    prior_summary_id: str
    traveler_id: str
    period_label: str
    summary_text: str
    recurring_correction_pattern: str | None
    created_at: datetime


class VoucherRow(_Frozen):
    voucher_id: str
    traveler_id: str
    trip_purpose_category: str
    trip_start_date: date
    trip_end_date: date
    declared_origin: str
    declared_destinations: list[str]
    funding_reference_label: str
    funding_reference_quality: str
    justification_text: str
    pre_existing_flags: list[str] = Field(default_factory=list)
    demo_packet_submitted_at: datetime
    review_status: str
    data_environment: str
    created_at: datetime
    updated_at: datetime


class LineItemRow(_Frozen):
    line_item_id: str
    voucher_id: str
    line_index: int
    expense_date: date
    amount_minor_units: int
    currency_code: str
    exchange_rate_to_usd: float | None
    category: str
    vendor_label: str
    payment_instrument_indicator: str
    free_text_notes: str
    claimed_by_traveler_at: datetime


class EvidenceRefRow(_Frozen):
    evidence_ref_id: str
    voucher_id: str
    line_item_id: str | None
    packet_level_role: str | None
    content_type_indicator: str
    legibility_cue: str
    itemization_cue: str
    payment_evidence_cue: str
    vendor_label_on_evidence: str | None
    evidence_date_on_face: date | None
    amount_on_face_minor_units: int | None
    currency_code_on_face: str | None
    notes: str


class PolicyCitationRow(_Frozen):
    citation_id: str
    source_identifier: str
    topic: str
    excerpt_text: str
    retrieval_anchor: str
    applicability_note: str
    created_at: datetime


class ExternalAnomalySignalRow(_Frozen):
    signal_id: str
    voucher_id: str
    signal_key: str
    signal_type: str
    synthetic_source_label: str
    rationale_text: str
    confidence: str
    is_official_finding: bool = False
    not_sufficient_for_adverse_action: bool = True
    received_at: datetime


class StoryFindingRow(_Frozen):
    finding_id: str
    voucher_id: str
    category: str
    severity: str
    summary: str
    explanation: str
    suggested_question: str
    packet_evidence_pointer: dict[str, Any]
    primary_citation_id: str | None
    confidence: str
    needs_human_review: bool
    review_state: str
    created_at: datetime


class MissingInformationItemRow(_Frozen):
    missing_item_id: str
    voucher_id: str
    description: str
    why_it_matters: str
    expected_location_hint: str
    linked_line_item_id: str | None
    created_at: datetime


class ReviewBriefRow(_Frozen):
    brief_id: str
    voucher_id: str
    version: int
    generated_at: datetime
    priority_score: float
    priority_rationale: str
    suggested_focus: str
    evidence_gap_summary: str
    story_coherence_summary: str
    draft_clarification_note: str
    policy_hooks: list[str] = Field(default_factory=list)
    signal_hooks: list[str] = Field(default_factory=list)
    finding_hooks: list[str] = Field(default_factory=list)
    missing_information_hooks: list[str] = Field(default_factory=list)
    brief_uncertainty: str
    human_authority_boundary_text: str
    is_partial: bool = False
    partial_reason: str | None = None


class AONoteRow(_Frozen):
    note_id: str
    voucher_id: str
    finding_id: str | None
    kind: str
    body: str
    actor_label: str
    created_at: datetime
    superseded_by_note_id: str | None = None


class WorkflowEventRow(_Frozen):
    event_id: str
    voucher_id: str | None
    actor_label: str
    occurred_at: datetime
    event_type: str
    tool_name: str | None
    target_kind: str
    target_id: str | None
    resulting_status: str | None
    rationale_metadata: dict[str, Any] = Field(default_factory=dict)
    human_authority_boundary_reminder: str


__all__ = [
    "AONoteRow",
    "EvidenceRefRow",
    "ExternalAnomalySignalRow",
    "LineItemRow",
    "MissingInformationItemRow",
    "PolicyCitationRow",
    "PriorVoucherSummaryRow",
    "ReviewBriefRow",
    "StoryFindingRow",
    "TravelerRow",
    "VoucherRow",
    "WorkflowEventRow",
]
