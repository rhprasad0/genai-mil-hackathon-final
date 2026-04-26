"""Pure helpers for missing-information detection.

Sources of truth:
  - docs/spec.md FR-6 (Missing-Information Detection), AC-3.
  - docs/schema-implementation-plan.md section 5.9.

These helpers convert the declared-vs-attached comparison into explicit
``MissingInformationDraft`` rows the brief assembly layer renders into the
checklist.  They contain no IO and never recommend an official disposition.
"""

from __future__ import annotations

from dataclasses import dataclass

from .story_analysis import EvidenceSnapshot, LineItemSnapshot


@dataclass(frozen=True)
class MissingInformationDraft:
    """Domain-shaped missing-information item (no IDs, no audit fields)."""

    description: str
    why_it_matters: str
    expected_location_hint: str
    linked_line_item_id: str | None = None


def detect_lines_without_evidence(
    line_items: tuple[LineItemSnapshot, ...],
    evidence: tuple[EvidenceSnapshot, ...],
) -> tuple[MissingInformationDraft, ...]:
    """Return one row per line item that has no attached evidence."""

    have_evidence: set[str] = set()
    for ev in evidence:
        if ev.line_item_id and ev.content_type_indicator != "none_attached_demo":
            have_evidence.add(ev.line_item_id)
    out: list[MissingInformationDraft] = []
    for item in line_items:
        if item.line_item_id in have_evidence:
            continue
        out.append(
            MissingInformationDraft(
                description=(
                    f"No attached evidence for line {item.line_index} "
                    f"({item.category}, vendor {item.vendor_label})."
                ),
                why_it_matters=(
                    "Without supporting evidence the reviewer cannot verify "
                    "the claimed line item against the trip and the traveler "
                    "may need to provide a receipt or clarification."
                ),
                expected_location_hint=(
                    f"evidence_refs row linked to line_item_id={item.line_item_id}"
                ),
                linked_line_item_id=item.line_item_id,
            )
        )
    return tuple(out)


def detect_packet_level_gaps(
    has_trip_itinerary: bool,
    has_authorization_snapshot: bool,
    has_funding_reference_attachment: bool,
) -> tuple[MissingInformationDraft, ...]:
    """Return packet-level gaps the reviewer would expect to see."""

    out: list[MissingInformationDraft] = []
    if not has_trip_itinerary:
        out.append(
            MissingInformationDraft(
                description="No trip itinerary attached to the packet.",
                why_it_matters=(
                    "The reviewer reconstructs the trip from declared dates "
                    "and locations; an itinerary makes the reconstruction "
                    "verifiable."
                ),
                expected_location_hint=(
                    "evidence_refs row with packet_level_role=trip_itinerary"
                ),
            )
        )
    if not has_authorization_snapshot:
        out.append(
            MissingInformationDraft(
                description="No authorization snapshot attached to the packet.",
                why_it_matters=(
                    "An authorization snapshot lets the reviewer compare the "
                    "claimed trip to the originally authorized trip."
                ),
                expected_location_hint=(
                    "evidence_refs row with packet_level_role=authorization_snapshot"
                ),
            )
        )
    if not has_funding_reference_attachment:
        out.append(
            MissingInformationDraft(
                description="No funding reference attachment is on file.",
                why_it_matters=(
                    "A funding reference attachment helps the reviewer confirm "
                    "the LOA-shaped string on the packet without inferring it."
                ),
                expected_location_hint=(
                    "evidence_refs row with packet_level_role="
                    "funding_reference_attachment"
                ),
            )
        )
    return tuple(out)


__all__ = [
    "MissingInformationDraft",
    "detect_lines_without_evidence",
    "detect_packet_level_gaps",
]
