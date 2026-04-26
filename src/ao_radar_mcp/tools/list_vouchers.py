"""``list_vouchers_awaiting_action`` tool module.

Spec reference: docs/spec.md section 4.5.1.
The response is workload-only guidance and never carries approval / payment
language (FR-9, AC-8).
"""

from __future__ import annotations

from typing import Any

from ._common import _description, not_implemented_response

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


def handler(payload: dict[str, Any]) -> dict[str, Any]:
    # TODO Phase 2: query ``vouchers`` ordered by review_status partial index
    # and ``demo_packet_submitted_at`` and decorate with priority hints from
    # the latest brief per voucher (workload-only language).
    return not_implemented_response(TOOL_NAME)


__all__ = ["TOOL_NAME", "description", "INPUT_SCHEMA", "handler"]
