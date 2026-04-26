"""Pydantic v2 models for the YAML story cards (synthetic-data plan section 10).

Each card under ``ops/seed/cards/`` is parsed into ``StoryCard``. The loader
walks ``cards/`` deterministically (sorted filename order), validates every
file against this schema, and returns the in-memory model objects to the
remaining generators.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Annotated, Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Enum literal lists (mirror schema plan section 5/6).

LINE_ITEM_CATEGORIES = (
    "lodging",
    "transport_air",
    "transport_ground",
    "meals",
    "incidentals",
    "cash_atm",
    "currency_exchange",
    "other_demo",
)

PAYMENT_INSTRUMENTS = (
    "gtcc_like_demo",
    "personal_card_demo",
    "cash_demo",
    "unknown_demo",
)

CONTENT_TYPES = (
    "receipt_image_demo",
    "receipt_pdf_demo",
    "itinerary_pdf_demo",
    "boarding_pass_image_demo",
    "handwritten_local_paper_demo",
    "email_confirmation_text_demo",
    "none_attached_demo",
)

LEGIBILITY_CUES = ("clear", "partial", "poor", "not_applicable")
ITEMIZATION_CUES = ("itemized", "partially_itemized", "not_itemized", "not_applicable")
PAYMENT_EVIDENCE_CUES = ("present", "absent", "ambiguous", "not_applicable")
PACKET_LEVEL_ROLES = (
    "trip_itinerary",
    "authorization_snapshot",
    "packet_justification",
    "funding_reference_attachment",
    "none_attached_summary",
)

SIGNAL_TYPES = (
    "duplicate_payment_risk",
    "high_risk_mcc_demo",
    "unusual_amount",
    "date_location_mismatch",
    "split_disbursement_oddity",
    "repeated_correction_pattern",
    "peer_baseline_outlier",
    "traveler_baseline_outlier",
)

CONFIDENCES = ("low", "medium", "high")

FINDING_CATEGORIES = (
    "missing_receipt",
    "weak_or_local_paper_receipt",
    "amount_mismatch",
    "duplicate_or_multiple_charge",
    "ambiguous_loa_or_funding_reference",
    "cash_atm_or_exchange_reconstruction",
    "stale_memory_old_transaction",
    "forced_audit_receipt_review",
    "paperwork_or_math_inconsistency",
    "unclear_or_possibly_unjustified_expense",
    "date_window_mismatch",
    "location_mismatch",
    "miscategorized_line_item",
    "insufficient_evidence_overall",
    "oconus_vendor_edge_case",
    "evidence_quality_concern",
    "story_coherence_break",
)

SEVERITIES = ("info", "low", "medium", "high")
BRIEF_UNCERTAINTY = ("low", "medium", "high")
AO_NOTE_KINDS = (
    "ao_note",
    "draft_clarification",
    "synthetic_clarification_request",
    "ao_feedback",
)
FUNDING_QUALITIES = ("clean", "ambiguous", "unparseable")
REVIEW_STATUSES = (
    "needs_review",
    "in_review",
    "awaiting_traveler_clarification",
    "ready_for_human_decision",
    "closed_in_demo",
)

VOUCHER_ID_RE = re.compile(r"^V-\d{4}$")
TRAVELER_ID_RE = re.compile(r"^T-\d{3}$")
LOA_RE = re.compile(r"^LOA-DEMO-FY26-(\d{4}|\?{3})$")
LOA_AMBIGUOUS_SENTINEL_LITERAL = "FUND-POT-DEMO-AMBIG"


class StrictModel(BaseModel):
    """Strict Pydantic v2 model — extra keys forbidden, types enforced."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False, frozen=False)


class EvidenceCard(StrictModel):
    content_type_indicator: str
    legibility_cue: str
    itemization_cue: str
    payment_evidence_cue: str
    vendor_label_on_evidence: str | None = None
    evidence_date_on_face: date | None = None
    amount_on_face_minor_units: int | None = None
    currency_code_on_face: str | None = None
    notes: str = ""
    packet_level_role: str | None = None

    @field_validator("content_type_indicator")
    @classmethod
    def _check_content_type(cls, v: str) -> str:
        if v not in CONTENT_TYPES:
            raise ValueError(f"content_type_indicator must be one of {CONTENT_TYPES}")
        return v

    @field_validator("legibility_cue")
    @classmethod
    def _check_legibility(cls, v: str) -> str:
        if v not in LEGIBILITY_CUES:
            raise ValueError(f"legibility_cue must be one of {LEGIBILITY_CUES}")
        return v

    @field_validator("itemization_cue")
    @classmethod
    def _check_itemization(cls, v: str) -> str:
        if v not in ITEMIZATION_CUES:
            raise ValueError(f"itemization_cue must be one of {ITEMIZATION_CUES}")
        return v

    @field_validator("payment_evidence_cue")
    @classmethod
    def _check_payment_cue(cls, v: str) -> str:
        if v not in PAYMENT_EVIDENCE_CUES:
            raise ValueError(f"payment_evidence_cue must be one of {PAYMENT_EVIDENCE_CUES}")
        return v

    @field_validator("packet_level_role")
    @classmethod
    def _check_packet_role(cls, v: str | None) -> str | None:
        if v is not None and v not in PACKET_LEVEL_ROLES:
            raise ValueError(f"packet_level_role must be one of {PACKET_LEVEL_ROLES}")
        return v

    @model_validator(mode="after")
    def _none_attached_forces_na(self) -> EvidenceCard:
        if self.content_type_indicator == "none_attached_demo":
            for cue_name in ("legibility_cue", "itemization_cue", "payment_evidence_cue"):
                if getattr(self, cue_name) != "not_applicable":
                    raise ValueError(
                        f"{cue_name} must be 'not_applicable' when content_type_indicator='none_attached_demo'"
                    )
        return self


class LineItemCard(StrictModel):
    line_index: int = Field(ge=1)
    expense_date: date
    amount_minor_units: int = Field(ge=0)
    currency_code: str
    exchange_rate_to_usd: float | None = None
    category: str
    vendor_label: str
    payment_instrument_indicator: str
    free_text_notes: str = ""
    claimed_by_traveler_at: datetime | None = None
    evidence_refs: list[EvidenceCard] = Field(default_factory=list)

    @field_validator("category")
    @classmethod
    def _check_category(cls, v: str) -> str:
        if v not in LINE_ITEM_CATEGORIES:
            raise ValueError(f"category must be one of {LINE_ITEM_CATEGORIES}")
        return v

    @field_validator("payment_instrument_indicator")
    @classmethod
    def _check_payment(cls, v: str) -> str:
        if v not in PAYMENT_INSTRUMENTS:
            raise ValueError(f"payment_instrument_indicator must be one of {PAYMENT_INSTRUMENTS}")
        return v

    @model_validator(mode="after")
    def _currency_requires_rate(self) -> LineItemCard:
        if self.currency_code != "USD" and self.exchange_rate_to_usd is None:
            raise ValueError(
                f"line_index={self.line_index}: exchange_rate_to_usd required when currency_code != 'USD'"
            )
        return self


class PacketEvidencePointer(StrictModel):
    line_item_id: str | None = None
    evidence_ref_id: str | None = None
    excerpt_hint: str

    @model_validator(mode="after")
    def _at_least_one_id(self) -> PacketEvidencePointer:
        if not self.line_item_id and not self.evidence_ref_id:
            raise ValueError("packet_evidence_pointer requires line_item_id or evidence_ref_id")
        return self


class FindingCard(StrictModel):
    category: str
    severity: str
    confidence: str
    needs_human_review: bool = False
    summary: str
    explanation: str
    suggested_question: str
    primary_citation_id: str | None = None
    packet_evidence_pointer: PacketEvidencePointer
    signal_links: list[str] = Field(default_factory=list)

    @field_validator("category")
    @classmethod
    def _check_category(cls, v: str) -> str:
        if v not in FINDING_CATEGORIES:
            raise ValueError(f"category must be one of {FINDING_CATEGORIES}")
        return v

    @field_validator("severity")
    @classmethod
    def _check_severity(cls, v: str) -> str:
        if v not in SEVERITIES:
            raise ValueError(f"severity must be one of {SEVERITIES}")
        return v

    @field_validator("confidence")
    @classmethod
    def _check_conf(cls, v: str) -> str:
        if v not in CONFIDENCES:
            raise ValueError(f"confidence must be one of {CONFIDENCES}")
        return v


class SignalCard(StrictModel):
    signal_type: str
    confidence: str
    rationale_text: str
    scenario_slug: str

    @field_validator("signal_type")
    @classmethod
    def _check_signal_type(cls, v: str) -> str:
        if v not in SIGNAL_TYPES:
            raise ValueError(f"signal_type must be one of {SIGNAL_TYPES}")
        return v

    @field_validator("confidence")
    @classmethod
    def _check_conf(cls, v: str) -> str:
        if v not in CONFIDENCES:
            raise ValueError(f"confidence must be one of {CONFIDENCES}")
        return v

    @field_validator("scenario_slug")
    @classmethod
    def _check_scenario(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9_]+$", v):
            raise ValueError("scenario_slug must be lowercase alnum/underscore")
        return v


class MissingItemCard(StrictModel):
    description: str
    why_it_matters: str
    expected_location_hint: str
    linked_line_index: int | None = None


class BriefCard(StrictModel):
    priority_score: float = Field(ge=0.0, le=1.0)
    priority_rationale: str
    suggested_focus: str
    evidence_gap_summary: str
    story_coherence_summary: str
    draft_clarification_note: str
    brief_uncertainty: str
    is_partial: bool = False
    partial_reason: str | None = None

    @field_validator("brief_uncertainty")
    @classmethod
    def _check_uncertainty(cls, v: str) -> str:
        if v not in BRIEF_UNCERTAINTY:
            raise ValueError(f"brief_uncertainty must be one of {BRIEF_UNCERTAINTY}")
        return v

    @model_validator(mode="after")
    def _partial_requires_reason(self) -> BriefCard:
        if self.is_partial and not (self.partial_reason and self.partial_reason.strip()):
            raise ValueError("is_partial=true requires partial_reason")
        return self


class AONoteCard(StrictModel):
    kind: str
    body: str
    finding_index: int | None = None  # Reference into the finding list (1-based).

    @field_validator("kind")
    @classmethod
    def _check_kind(cls, v: str) -> str:
        if v not in AO_NOTE_KINDS:
            raise ValueError(f"kind must be one of {AO_NOTE_KINDS}")
        return v


class VoucherFields(StrictModel):
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

    @field_validator("funding_reference_quality")
    @classmethod
    def _check_quality(cls, v: str) -> str:
        if v not in FUNDING_QUALITIES:
            raise ValueError(f"funding_reference_quality must be one of {FUNDING_QUALITIES}")
        return v

    @field_validator("review_status")
    @classmethod
    def _check_status(cls, v: str) -> str:
        if v not in REVIEW_STATUSES:
            raise ValueError(f"review_status must be one of {REVIEW_STATUSES}")
        return v

    @field_validator("funding_reference_label")
    @classmethod
    def _check_loa(cls, v: str) -> str:
        if v == LOA_AMBIGUOUS_SENTINEL_LITERAL:
            return v
        if not LOA_RE.match(v):
            raise ValueError(
                "funding_reference_label must match LOA-DEMO-FY26-#### (or "
                "the FUND-POT-DEMO-AMBIG sentinel; LOA-DEMO-FY26-??? for the "
                "V-1004 ambiguous case)"
            )
        return v

    @model_validator(mode="after")
    def _date_order(self) -> VoucherFields:
        if self.trip_end_date < self.trip_start_date:
            raise ValueError("trip_end_date must be >= trip_start_date")
        return self


class ExpectedAOExperience(StrictModel):
    first_focus: str
    required_citations: list[str] = Field(default_factory=list)
    required_signals: list[str] = Field(default_factory=list)
    required_findings: list[str] = Field(default_factory=list)
    required_labels: list[str] = Field(default_factory=list)
    required_missing_information_items: int = Field(ge=0)
    brief_uncertainty: str
    is_partial: bool = False

    @field_validator("brief_uncertainty")
    @classmethod
    def _check_uncertainty(cls, v: str) -> str:
        if v not in BRIEF_UNCERTAINTY:
            raise ValueError(f"brief_uncertainty must be one of {BRIEF_UNCERTAINTY}")
        return v


class StoryCard(StrictModel):
    voucher_id: str
    traveler_id: str
    hero: bool = False
    hero_position: int | None = None
    narrative: str
    pain_patterns: list[str]
    expected_ao_experience: ExpectedAOExperience
    voucher: VoucherFields
    line_items: list[LineItemCard]
    external_anomaly_signals: list[SignalCard] = Field(default_factory=list)
    findings: list[FindingCard] = Field(default_factory=list)
    missing_information_items: list[MissingItemCard] = Field(default_factory=list)
    brief: BriefCard
    ao_notes: list[AONoteCard] = Field(default_factory=list)
    seeded_workflow_events: list[Any] = Field(default_factory=list)

    @field_validator("voucher_id")
    @classmethod
    def _check_voucher(cls, v: str) -> str:
        if not VOUCHER_ID_RE.match(v):
            raise ValueError("voucher_id must match V-####")
        return v

    @field_validator("traveler_id")
    @classmethod
    def _check_traveler(cls, v: str) -> str:
        if not TRAVELER_ID_RE.match(v):
            raise ValueError("traveler_id must match T-###")
        return v

    @field_validator("narrative")
    @classmethod
    def _narrative_short(cls, v: str) -> str:
        # Two or three plain sentences (synthetic-data plan section 4).
        sentence_count = sum(1 for ch in v if ch in ".!?")
        if sentence_count > 6:
            raise ValueError("narrative should be two or three plain sentences")
        if not v.strip():
            raise ValueError("narrative must not be empty")
        return v

    @model_validator(mode="after")
    def _hero_consistency(self) -> StoryCard:
        if self.hero and self.hero_position not in (1, 2, 3):
            raise ValueError("hero=true requires hero_position in {1, 2, 3}")
        if not self.hero and self.hero_position is not None:
            raise ValueError("hero_position only allowed when hero=true")
        # Each finding's signal_links must reference a declared signal.
        signal_types = {s.signal_type for s in self.external_anomaly_signals}
        for finding in self.findings:
            for link in finding.signal_links:
                if link not in signal_types:
                    raise ValueError(
                        f"finding category={finding.category} has signal_link={link} "
                        f"not present in card external_anomaly_signals"
                    )
        # missing_information_items linked_line_index must resolve.
        line_indexes = {li.line_index for li in self.line_items}
        for mi in self.missing_information_items:
            if mi.linked_line_index is not None and mi.linked_line_index not in line_indexes:
                raise ValueError(
                    f"missing_information_items linked_line_index={mi.linked_line_index} unknown"
                )
        # AO notes finding_index must resolve.
        for note in self.ao_notes:
            if note.finding_index is not None and not (
                1 <= note.finding_index <= len(self.findings)
            ):
                raise ValueError(
                    f"ao_notes finding_index={note.finding_index} out of range"
                )
        return self


def load_card_from_path(path: Path) -> StoryCard:
    """Parse a single card YAML into a ``StoryCard`` model."""

    with path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    if raw is None:
        raise ValueError(f"{path} is empty")
    if not isinstance(raw, dict):
        raise ValueError(f"{path} top level must be a mapping")
    try:
        return StoryCard.model_validate(raw)
    except Exception as exc:
        raise ValueError(f"{path}: {exc}") from exc


def load_all_cards(cards_dir: Path) -> list[StoryCard]:
    """Return every card under ``cards_dir`` sorted by voucher_id."""

    files = sorted(cards_dir.glob("V-*.yaml"))
    cards = [load_card_from_path(p) for p in files]
    if not cards:
        raise ValueError(f"no cards found under {cards_dir}")
    seen: set[str] = set()
    for card in cards:
        if card.voucher_id in seen:
            raise ValueError(f"duplicate voucher_id {card.voucher_id}")
        seen.add(card.voucher_id)
    return sorted(cards, key=lambda c: c.voucher_id)


__all__ = [
    "StoryCard",
    "VoucherFields",
    "LineItemCard",
    "EvidenceCard",
    "FindingCard",
    "SignalCard",
    "MissingItemCard",
    "BriefCard",
    "AONoteCard",
    "PacketEvidencePointer",
    "ExpectedAOExperience",
    "load_card_from_path",
    "load_all_cards",
    "FINDING_CATEGORIES",
    "SIGNAL_TYPES",
    "LINE_ITEM_CATEGORIES",
]
