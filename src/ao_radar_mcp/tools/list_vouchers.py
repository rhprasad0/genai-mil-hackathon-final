"""``list_vouchers_awaiting_action`` tool module.

Spec reference: docs/spec.md section 4.5.1.
The response is workload-only guidance and never carries approval / payment
language (FR-9, AC-8).

Demo behaviour: ranks the synthetic queue by latest brief priority_score
(descending), with ties broken by demo_packet_submitted_at.  Each row
carries the open-finding count and a plain-English illustration hint so a
demo cockpit (e.g. ChatGPT Apps) can pick the most illustrative voucher
without inferring official action.
"""

from __future__ import annotations

from typing import Any

from .. import runtime
from ._common import _description, not_implemented_response, with_boundary

TOOL_NAME = "list_vouchers_awaiting_action"

description = _description(
    "Return the AO review queue ranked by composite review-difficulty "
    "indicators, labeled as workload guidance only."
)

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "limit": {
            "type": "integer",
            "minimum": 1,
            "maximum": 100,
            "description": "Optional cap on returned rows.",
        },
    },
    "additionalProperties": False,
}


_OPEN_REVIEW_STATUSES = (
    "needs_review",
    "in_review",
    "awaiting_traveler_clarification",
    "ready_for_human_decision",
)


def _illustration_hint(
    *,
    review_status: str,
    findings_count: int,
    needs_human_review_count: int,
    missing_info_count: int,
    funding_quality: str,
    pre_existing_flags: list[str],
) -> str:
    bits: list[str] = []
    if needs_human_review_count:
        bits.append(f"{needs_human_review_count} finding(s) flagged for human review")
    elif findings_count:
        bits.append(f"{findings_count} story-coherence finding(s)")
    if missing_info_count:
        bits.append(f"{missing_info_count} missing-information item(s)")
    if funding_quality and funding_quality != "clean":
        bits.append(f"{funding_quality} funding reference")
    if pre_existing_flags:
        bits.append("pre-existing review flags present")
    if not bits:
        bits.append("clean control case (workload guidance only)")
    return (
        "Synthetic review aid: "
        + "; ".join(bits)
        + f"; current internal review_status={review_status}."
    )


def handler(payload: dict[str, Any]) -> dict[str, Any]:
    if not runtime.is_db_available():
        return not_implemented_response(TOOL_NAME)

    limit_raw = payload.get("limit")
    try:
        limit = int(limit_raw) if limit_raw is not None else None
    except (TypeError, ValueError):
        limit = None

    sql = """
    WITH latest_brief AS (
        SELECT DISTINCT ON (voucher_id)
            voucher_id,
            priority_score,
            priority_rationale,
            suggested_focus,
            brief_uncertainty
        FROM review_briefs
        ORDER BY voucher_id, version DESC
    ),
    finding_counts AS (
        SELECT
            voucher_id,
            COUNT(*) AS findings_total,
            COUNT(*) FILTER (WHERE needs_human_review) AS needs_human_review_count
        FROM story_findings
        GROUP BY voucher_id
    ),
    missing_counts AS (
        SELECT voucher_id, COUNT(*) AS missing_total
        FROM missing_information_items
        GROUP BY voucher_id
    )
    SELECT
        v.voucher_id,
        v.traveler_id,
        v.trip_purpose_category,
        v.trip_start_date,
        v.trip_end_date,
        v.declared_origin,
        v.declared_destinations,
        v.funding_reference_label,
        v.funding_reference_quality,
        v.pre_existing_flags,
        v.demo_packet_submitted_at,
        v.review_status,
        COALESCE(lb.priority_score, 0)::float AS priority_score,
        lb.priority_rationale,
        lb.suggested_focus,
        lb.brief_uncertainty,
        COALESCE(fc.findings_total, 0) AS findings_total,
        COALESCE(fc.needs_human_review_count, 0) AS needs_human_review_count,
        COALESCE(mc.missing_total, 0) AS missing_total
    FROM vouchers v
    LEFT JOIN latest_brief lb ON lb.voucher_id = v.voucher_id
    LEFT JOIN finding_counts fc ON fc.voucher_id = v.voucher_id
    LEFT JOIN missing_counts mc ON mc.voucher_id = v.voucher_id
    WHERE v.review_status = ANY(%s)
    ORDER BY priority_score DESC, v.demo_packet_submitted_at ASC, v.voucher_id ASC
    """
    params: list[Any] = [list(_OPEN_REVIEW_STATUSES)]
    if limit is not None:
        sql += " LIMIT %s"
        params.append(limit)

    queue: list[dict[str, Any]] = []
    with runtime.transaction() as conn, conn.cursor() as cursor:
        cursor.execute(sql, tuple(params))
        for row in cursor.fetchall():
            (
                voucher_id,
                traveler_id,
                trip_purpose_category,
                trip_start_date,
                trip_end_date,
                declared_origin,
                declared_destinations,
                funding_reference_label,
                funding_reference_quality,
                pre_existing_flags,
                demo_packet_submitted_at,
                review_status,
                priority_score,
                priority_rationale,
                suggested_focus,
                brief_uncertainty,
                findings_total,
                needs_human_review_count,
                missing_total,
            ) = row
            destinations = list(declared_destinations or [])
            flags = list(pre_existing_flags or [])
            queue.append(
                {
                    "voucher_id": voucher_id,
                    "traveler_id": traveler_id,
                    "trip_label": (
                        f"{trip_purpose_category}: {declared_origin} -> "
                        + (", ".join(destinations) if destinations else "n/a")
                        + f" ({trip_start_date.isoformat()}..{trip_end_date.isoformat()})"
                    ),
                    "review_status": review_status,
                    "review_difficulty": {
                        "priority_score": float(priority_score),
                        "brief_uncertainty": brief_uncertainty,
                        "findings_total": int(findings_total),
                        "needs_human_review_count": int(needs_human_review_count),
                        "missing_information_total": int(missing_total),
                    },
                    "funding_reference_label": funding_reference_label,
                    "funding_reference_quality": funding_reference_quality,
                    "pre_existing_flags": flags,
                    "submitted_at": demo_packet_submitted_at.isoformat(),
                    "priority_rationale": priority_rationale,
                    "suggested_focus": suggested_focus,
                    "illustration_hint": _illustration_hint(
                        review_status=review_status,
                        findings_count=int(findings_total),
                        needs_human_review_count=int(needs_human_review_count),
                        missing_info_count=int(missing_total),
                        funding_quality=funding_reference_quality,
                        pre_existing_flags=flags,
                    ),
                }
            )

    return with_boundary(
        {
            "status": "ok",
            "tool": TOOL_NAME,
            "queue": queue,
            "count": len(queue),
            "guidance": (
                "Workload-only ranking. Higher priority_score means more "
                "review attention is likely needed. The score never represents "
                "approval, denial, payability, or readiness for payment."
            ),
            "review_prompt_only": True,
        }
    )


__all__ = ["TOOL_NAME", "description", "INPUT_SCHEMA", "handler"]
