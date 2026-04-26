"""Scoped repository module for the ``review_briefs`` table.

Sources of truth:
  - docs/schema-implementation-plan.md sections 5.10 and 8.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from ._models import ReviewBriefRow

_COLUMNS = (
    "brief_id",
    "voucher_id",
    "version",
    "generated_at",
    "priority_score",
    "priority_rationale",
    "suggested_focus",
    "evidence_gap_summary",
    "story_coherence_summary",
    "draft_clarification_note",
    "policy_hooks",
    "signal_hooks",
    "finding_hooks",
    "missing_information_hooks",
    "brief_uncertainty",
    "human_authority_boundary_text",
    "is_partial",
    "partial_reason",
)


def _row_to_model(row: tuple[Any, ...]) -> ReviewBriefRow:
    mapping = dict(zip(_COLUMNS, row, strict=False))
    return ReviewBriefRow(
        brief_id=mapping["brief_id"],
        voucher_id=mapping["voucher_id"],
        version=int(mapping["version"]),
        generated_at=mapping["generated_at"],
        priority_score=float(mapping["priority_score"]),
        priority_rationale=mapping["priority_rationale"],
        suggested_focus=mapping["suggested_focus"],
        evidence_gap_summary=mapping["evidence_gap_summary"],
        story_coherence_summary=mapping["story_coherence_summary"],
        draft_clarification_note=mapping["draft_clarification_note"],
        policy_hooks=list(mapping["policy_hooks"] or []),
        signal_hooks=list(mapping["signal_hooks"] or []),
        finding_hooks=list(mapping["finding_hooks"] or []),
        missing_information_hooks=list(mapping["missing_information_hooks"] or []),
        brief_uncertainty=mapping["brief_uncertainty"],
        human_authority_boundary_text=mapping["human_authority_boundary_text"],
        is_partial=bool(mapping["is_partial"]),
        partial_reason=mapping["partial_reason"],
    )


def get_latest_for_voucher(transaction: Any, voucher_id: str) -> ReviewBriefRow | None:
    sql = (
        f"SELECT {', '.join(_COLUMNS)} FROM review_briefs "
        "WHERE voucher_id = %s ORDER BY version DESC LIMIT 1"
    )
    with transaction.cursor() as cursor:
        cursor.execute(sql, (voucher_id,))
        row = cursor.fetchone()
    if row is None:
        return None
    return _row_to_model(row)


def get_by_id(transaction: Any, brief_id: str) -> ReviewBriefRow | None:
    sql = f"SELECT {', '.join(_COLUMNS)} FROM review_briefs WHERE brief_id = %s"
    with transaction.cursor() as cursor:
        cursor.execute(sql, (brief_id,))
        row = cursor.fetchone()
    if row is None:
        return None
    return _row_to_model(row)


def append_version(
    transaction: Any,
    *,
    voucher_id: str,
    draft: dict[str, Any],
    audit_event: dict[str, Any],
) -> ReviewBriefRow:
    """Insert a new versioned brief row plus the paired generation event."""

    with transaction.cursor() as cursor:
        cursor.execute(
            "SELECT COALESCE(MAX(version), 0) FROM review_briefs WHERE voucher_id = %s",
            (voucher_id,),
        )
        (current_max,) = cursor.fetchone()
        next_version = int(current_max) + 1
        brief_id = f"BRF-{uuid.uuid4().hex[:12]}"
        cursor.execute(
            "INSERT INTO review_briefs ("
            "brief_id, voucher_id, version, generated_at, priority_score, "
            "priority_rationale, suggested_focus, evidence_gap_summary, "
            "story_coherence_summary, draft_clarification_note, "
            "policy_hooks, signal_hooks, finding_hooks, missing_information_hooks, "
            "brief_uncertainty, human_authority_boundary_text, is_partial, partial_reason"
            ") VALUES (%s, %s, %s, NOW(), %s, %s, %s, %s, %s, %s, "
            "%s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s, %s, %s) "
            f"RETURNING {', '.join(_COLUMNS)}",
            (
                brief_id,
                voucher_id,
                next_version,
                float(draft["priority_score"]),
                draft["priority_rationale"],
                draft["suggested_focus"],
                draft["evidence_gap_summary"],
                draft["story_coherence_summary"],
                draft["draft_clarification_note"],
                json.dumps(list(draft.get("policy_hooks") or [])),
                json.dumps(list(draft.get("signal_hooks") or [])),
                json.dumps(list(draft.get("finding_hooks") or [])),
                json.dumps(list(draft.get("missing_information_hooks") or [])),
                draft["brief_uncertainty"],
                draft["human_authority_boundary_text"],
                bool(draft.get("is_partial", False)),
                draft.get("partial_reason"),
            ),
        )
        row = cursor.fetchone()

    persisted = _row_to_model(row)
    enriched_event = dict(audit_event)
    enriched_event["target_id"] = persisted.brief_id
    rationale = dict(enriched_event.get("rationale_metadata") or {})
    rationale.setdefault("brief_id", persisted.brief_id)
    rationale.setdefault("brief_version", persisted.version)
    enriched_event["rationale_metadata"] = rationale

    from . import workflow_events as _wf

    _wf.insert(transaction, event=enriched_event)
    return persisted


__all__ = ["append_version", "get_by_id", "get_latest_for_voucher"]
