"""``prepare_ao_review_brief`` tool module.

Spec reference: docs/spec.md section 4.5.1, FR-14, AC-15.  Central fusion
tool: combines packet, traveler profile, prior summaries, signals,
story-coherence findings, and policy citations into a single auditable
pre-decision review brief.  Persists a new ``review_briefs`` row and emits
``event_type=generation`` in the same transaction (audit invariant matrix).
When a prior brief already exists for the voucher, the tool returns it
verbatim and emits ``event_type=retrieval`` instead — repeated calls are
safe to make from a demo cockpit.
"""

from __future__ import annotations

from typing import Any

from .. import runtime
from ..audit import AuditEventTemplate, materialize
from ..repository import (
    briefs as briefs_repo,
)
from ..repository import (
    findings as findings_repo,
)
from ..repository import (
    missing_information as missing_repo,
)
from ..repository import (
    signals as signals_repo,
)
from ..repository import (
    vouchers as vouchers_repo,
)
from ..safety.refusal import REASON_MISSING_REQUIRED_INPUT, build
from ._common import _description, not_implemented_response, to_jsonable, with_boundary

TOOL_NAME = "prepare_ao_review_brief"

description = _description(
    "Assemble a pre-decision review brief that fuses packet evidence, "
    "traveler profile, prior summaries, signals, story-coherence findings, "
    "and synthetic demo reference-corpus citations. The brief packages "
    "evidence for AO review and never recommends an official disposition."
)

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "voucher_id": {
            "type": "string",
            "description": "Synthetic voucher identifier (e.g. V-1003).",
        },
        "actor_label": {
            "type": "string",
            "description": "Demo identity (e.g. demo_ao_user_1).",
        },
    },
    "required": ["voucher_id"],
    "additionalProperties": False,
}

_DEFAULT_ACTOR = "demo_ao_user_1"


def _missing_voucher_refusal(payload: dict[str, Any]) -> dict[str, Any]:
    return build(
        reason=REASON_MISSING_REQUIRED_INPUT,
        message="prepare_ao_review_brief requires a synthetic voucher_id input.",
        tool_name=TOOL_NAME,
        target_kind="voucher",
        target_id=None,
        voucher_id=None,
        rejected_request=payload,
    ).response.to_dict()


def _finding_payload(row: Any) -> dict[str, Any]:
    return {
        "finding_id": row.finding_id,
        "category": row.category,
        "severity": row.severity,
        "summary": row.summary,
        "explanation": row.explanation,
        "suggested_question": row.suggested_question,
        "needs_human_review": row.needs_human_review,
        "review_state": row.review_state,
        "primary_citation_id": row.primary_citation_id,
        "packet_evidence_pointer": to_jsonable(row.packet_evidence_pointer),
        "review_prompt_only": True,
    }


def _missing_payload(row: Any) -> dict[str, Any]:
    return {
        "missing_item_id": row.missing_item_id,
        "description": row.description,
        "why_it_matters": row.why_it_matters,
        "expected_location_hint": row.expected_location_hint,
        "linked_line_item_id": row.linked_line_item_id,
    }


def _signal_payload(row: Any) -> dict[str, Any]:
    return {
        "signal_id": row.signal_id,
        "signal_key": row.signal_key,
        "signal_type": row.signal_type,
        "synthetic_source_label": row.synthetic_source_label,
        "rationale_text": row.rationale_text,
        "confidence": row.confidence,
        "is_official_finding": row.is_official_finding,
        "not_sufficient_for_adverse_action": row.not_sufficient_for_adverse_action,
    }


def _brief_payload(brief: Any) -> dict[str, Any]:
    return {
        "brief_id": brief.brief_id,
        "voucher_id": brief.voucher_id,
        "version": brief.version,
        "generated_at": brief.generated_at.isoformat(),
        "priority_score": float(brief.priority_score),
        "priority_rationale": brief.priority_rationale,
        "suggested_focus": brief.suggested_focus,
        "evidence_gap_summary": brief.evidence_gap_summary,
        "story_coherence_summary": brief.story_coherence_summary,
        "draft_clarification_note": brief.draft_clarification_note,
        "policy_hooks": list(brief.policy_hooks),
        "signal_hooks": list(brief.signal_hooks),
        "finding_hooks": list(brief.finding_hooks),
        "missing_information_hooks": list(brief.missing_information_hooks),
        "brief_uncertainty": brief.brief_uncertainty,
        "human_authority_boundary_text": brief.human_authority_boundary_text,
        "is_partial": brief.is_partial,
        "partial_reason": brief.partial_reason,
    }


def handler(payload: dict[str, Any]) -> dict[str, Any]:
    voucher_id = (payload.get("voucher_id") or "").strip()
    actor_label = (payload.get("actor_label") or _DEFAULT_ACTOR).strip() or _DEFAULT_ACTOR

    if not runtime.is_db_available():
        return not_implemented_response(TOOL_NAME)

    if not voucher_id:
        return _missing_voucher_refusal(payload)

    with runtime.transaction() as conn:
        voucher = vouchers_repo.get_by_id(conn, voucher_id)
        if voucher is None:
            return with_boundary(
                {
                    "status": "not_found",
                    "tool": TOOL_NAME,
                    "voucher_id": voucher_id,
                    "message": "No synthetic voucher with this id is present in demo data.",
                }
            )

        existing_brief = briefs_repo.get_latest_for_voucher(conn, voucher_id)
        findings = findings_repo.list_for_voucher(conn, voucher_id)
        missing = missing_repo.list_for_voucher(conn, voucher_id)
        signals = signals_repo.list_for_voucher(conn, voucher_id)

        if existing_brief is None:
            from ..domain.priority import PriorityInputs
            from ..domain.priority import compute as compute_priority

            severity_counts: dict[str, int] = {}
            needs_human_review = 0
            for finding in findings:
                severity_counts[finding.severity] = severity_counts.get(finding.severity, 0) + 1
                if finding.needs_human_review:
                    needs_human_review += 1
            priority = compute_priority(
                PriorityInputs(
                    finding_counts_by_severity=severity_counts,
                    missing_information_count=len(missing),
                    signal_count=len(signals),
                    needs_human_review_count=needs_human_review,
                )
            )

            from ..safety.authority_boundary import HUMAN_AUTHORITY_BOUNDARY_TEXT

            draft = {
                "priority_score": priority.score,
                "priority_rationale": priority.rationale,
                "suggested_focus": (
                    "Synthetic demo brief generated on demand from seeded findings; "
                    "review prompt only."
                ),
                "evidence_gap_summary": (
                    f"{len(missing)} missing-information item(s) flagged from synthetic packet."
                ),
                "story_coherence_summary": (
                    f"{len(findings)} story-coherence finding(s) surfaced for reviewer attention."
                ),
                "draft_clarification_note": (
                    "No clarification draft was pre-seeded; reviewer can author one. "
                    "Synthetic demo draft note only."
                ),
                "policy_hooks": [],
                "signal_hooks": [s.signal_key for s in signals],
                "finding_hooks": [f.finding_id for f in findings],
                "missing_information_hooks": [m.missing_item_id for m in missing],
                "brief_uncertainty": "medium" if findings or missing else "low",
                "human_authority_boundary_text": HUMAN_AUTHORITY_BOUNDARY_TEXT,
                "is_partial": False,
                "partial_reason": None,
            }
            audit_event = materialize(
                AuditEventTemplate(
                    event_type="generation",
                    tool_name=TOOL_NAME,
                    target_kind="brief",
                    target_id=None,  # filled in by repository after insert
                    voucher_id=voucher_id,
                    actor_label=actor_label,
                    rationale_metadata={"reason": "no_existing_brief"},
                )
            )
            persisted = briefs_repo.append_version(
                conn,
                voucher_id=voucher_id,
                draft=draft,
                audit_event=audit_event.to_dict(),
            )
            event_type = "generation"
            brief_payload = _brief_payload(persisted)
        else:
            audit_event = materialize(
                AuditEventTemplate(
                    event_type="retrieval",
                    tool_name=TOOL_NAME,
                    target_kind="brief",
                    target_id=existing_brief.brief_id,
                    voucher_id=voucher_id,
                    actor_label=actor_label,
                    rationale_metadata={
                        "reason": "existing_brief_returned",
                        "brief_id": existing_brief.brief_id,
                        "brief_version": existing_brief.version,
                    },
                )
            )
            from ..repository import workflow_events as _wf

            _wf.insert(conn, event=audit_event.to_dict())
            event_type = "retrieval"
            brief_payload = _brief_payload(existing_brief)

    response = {
        "status": "ok",
        "tool": TOOL_NAME,
        "voucher_id": voucher_id,
        "audit_event_type": event_type,
        "audit_event_id": audit_event.event_id,
        "voucher": {
            "voucher_id": voucher.voucher_id,
            "traveler_id": voucher.traveler_id,
            "review_status": voucher.review_status,
            "trip_purpose_category": voucher.trip_purpose_category,
            "funding_reference_quality": voucher.funding_reference_quality,
        },
        "brief": brief_payload,
        "findings": [_finding_payload(f) for f in findings],
        "missing_information_items": [_missing_payload(m) for m in missing],
        "signals": [_signal_payload(s) for s in signals],
        "review_prompt_only": True,
    }
    return with_boundary(response)


__all__ = ["TOOL_NAME", "description", "INPUT_SCHEMA", "handler"]
