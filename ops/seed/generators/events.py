"""Workflow-event row builder.

Every seeded scoped write, brief generation, needs-human-review label, and
the two seeded refusals must produce a matching ``workflow_events`` row in
the loader transaction. This module derives every row from card + supporting
fixture content. The event ordering is deterministic.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from ops.seed.constants import (
    DEMO_AO_ACTOR_LABEL,
    HUMAN_AUTHORITY_BOUNDARY_TEXT,
    SYSTEM_SEED_ACTOR_LABEL,
)
from ops.seed.generators.cards import StoryCard
from ops.seed.generators.determinism import derive_id, derive_timestamp


def event_id_for(*parts: str) -> str:
    return f"EVT-{derive_id('event', *parts)[:16]}"


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _kind_to_tool_name(kind: str) -> str:
    return {
        "ao_note": "record_ao_note",
        "draft_clarification": "draft_return_comment",
        "synthetic_clarification_request": "request_traveler_clarification",
        "ao_feedback": "record_ao_feedback",
    }[kind]


def _kind_to_resulting_status(kind: str) -> str | None:
    if kind == "synthetic_clarification_request":
        return "awaiting_traveler_clarification"
    return None


def build_card_workflow_events(
    card: StoryCard,
    brief_row: dict[str, Any],
    finding_rows: list[dict[str, Any]],
    note_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return every required workflow_events row derived from one card."""

    base = _ensure_utc(card.voucher.demo_packet_submitted_at)
    rows: list[dict[str, Any]] = []
    offset = 200

    # 1a. retrieval events per distinct citation hit on the brief
    citation_hits = sorted(
        {f["primary_citation_id"] for f in finding_rows if f.get("primary_citation_id")}
    )
    for citation_id in citation_hits:
        rows.append(
            {
                "event_id": event_id_for("retrieval", card.voucher_id, citation_id),
                "voucher_id": card.voucher_id,
                "actor_label": SYSTEM_SEED_ACTOR_LABEL,
                "occurred_at": derive_timestamp(base, offset_minutes=offset),
                "event_type": "retrieval",
                "tool_name": "get_policy_citation",
                "target_kind": "citation",
                "target_id": citation_id,
                "resulting_status": None,
                "rationale_metadata": {
                    "citation_id": citation_id,
                    "voucher_id": card.voucher_id,
                },
                "human_authority_boundary_reminder": HUMAN_AUTHORITY_BOUNDARY_TEXT,
            }
        )
        offset += 1

    # 1. brief generation event
    rows.append(
        {
            "event_id": event_id_for("generation", card.voucher_id, brief_row["brief_id"]),
            "voucher_id": card.voucher_id,
            "actor_label": SYSTEM_SEED_ACTOR_LABEL,
            "occurred_at": derive_timestamp(base, offset_minutes=offset),
            "event_type": "generation",
            "tool_name": "prepare_ao_review_brief",
            "target_kind": "brief",
            "target_id": brief_row["brief_id"],
            "resulting_status": None,
            "rationale_metadata": {
                "voucher_id": card.voucher_id,
                "brief_version": brief_row["version"],
                "is_partial": brief_row["is_partial"],
                "policy_hooks": brief_row["policy_hooks"],
                "finding_hooks": brief_row["finding_hooks"],
            },
            "human_authority_boundary_reminder": HUMAN_AUTHORITY_BOUNDARY_TEXT,
        }
    )
    offset += 5

    # 2. needs_human_review_label events for findings flagged that way
    for f_row, f_card in zip(finding_rows, card.findings, strict=True):
        if f_row["needs_human_review"]:
            rows.append(
                {
                    "event_id": event_id_for("nhr", card.voucher_id, f_row["finding_id"]),
                    "voucher_id": card.voucher_id,
                    "actor_label": SYSTEM_SEED_ACTOR_LABEL,
                    "occurred_at": derive_timestamp(base, offset_minutes=offset),
                    "event_type": "needs_human_review_label",
                    "tool_name": None,
                    "target_kind": "finding",
                    "target_id": f_row["finding_id"],
                    "resulting_status": None,
                    "rationale_metadata": {
                        "category": f_row["category"],
                        "needs_human_review": True,
                    },
                    "human_authority_boundary_reminder": HUMAN_AUTHORITY_BOUNDARY_TEXT,
                }
            )
            offset += 2

    # 3. scoped_write events for ao_notes
    for note_row in note_rows:
        kind = note_row["kind"]
        tool_name = _kind_to_tool_name(kind)
        resulting_status = _kind_to_resulting_status(kind)
        target_kind = "voucher" if kind == "synthetic_clarification_request" else "note"
        target_id = (
            card.voucher_id if target_kind == "voucher" else note_row["note_id"]
        )
        rows.append(
            {
                "event_id": event_id_for("note", card.voucher_id, note_row["note_id"]),
                "voucher_id": card.voucher_id,
                "actor_label": DEMO_AO_ACTOR_LABEL,
                "occurred_at": derive_timestamp(base, offset_minutes=offset),
                "event_type": "scoped_write",
                "tool_name": tool_name,
                "target_kind": target_kind,
                "target_id": target_id,
                "resulting_status": resulting_status,
                "rationale_metadata": {
                    "note_id": note_row["note_id"],
                    "kind": kind,
                },
                "human_authority_boundary_reminder": HUMAN_AUTHORITY_BOUNDARY_TEXT,
            }
        )
        offset += 2

    return rows


def build_refusal_events(refusal_yaml_path: Path) -> list[dict[str, Any]]:
    raw = yaml.safe_load(refusal_yaml_path.read_text(encoding="utf-8"))
    if not raw or "refusals" not in raw:
        raise ValueError(f"{refusal_yaml_path} missing 'refusals' top-level key")
    rows: list[dict[str, Any]] = []
    for entry in raw["refusals"]:
        occurred_on = entry["occurred_on"]
        offset = entry.get("occurred_offset_minutes", 0)
        occurred_at = derive_timestamp(occurred_on, offset_minutes=offset)
        rows.append(
            {
                "event_id": event_id_for("refusal", entry["voucher_id"], entry["tool_name"]),
                "voucher_id": entry["voucher_id"],
                "actor_label": DEMO_AO_ACTOR_LABEL,
                "occurred_at": occurred_at,
                "event_type": "refusal",
                "tool_name": entry["tool_name"],
                "target_kind": entry["target_kind"],
                "target_id": entry["target_id"],
                "resulting_status": None,
                "rationale_metadata": {
                    "rejected_input": entry["rejected_input"],
                    "rationale": entry["rationale"],
                    "refusal_reason": entry["refusal_reason"],
                    "tool_name": entry["tool_name"],
                },
                "human_authority_boundary_reminder": HUMAN_AUTHORITY_BOUNDARY_TEXT,
            }
        )
    return rows


__all__ = [
    "event_id_for",
    "build_card_workflow_events",
    "build_refusal_events",
]
