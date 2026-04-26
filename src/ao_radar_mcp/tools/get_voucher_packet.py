"""``get_voucher_packet`` tool module.

Spec reference: docs/spec.md section 4.5.1.  Returns the synthetic voucher
packet shape (declared trip, line items, evidence references, justification,
funding label, pre-existing flags, current internal review status).
"""

from __future__ import annotations

from typing import Any

from ._common import _description, not_implemented_response

TOOL_NAME = "get_voucher_packet"

description = _description(
    "Return the synthetic voucher packet for a voucher_id (declared trip, "
    "line items, evidence references, justification, funding/LOA label, "
    "pre-existing flags, internal review status)."
)

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "voucher_id": {
            "type": "string",
            "description": "Synthetic voucher identifier (e.g. V-1003).",
        },
    },
    "required": ["voucher_id"],
    "additionalProperties": False,
}


def handler(payload: dict[str, Any]) -> dict[str, Any]:
    # TODO Phase 2: fetch from repository.vouchers / line_items / evidence /
    # missing_information and assemble into the read-side response shape.
    return not_implemented_response(TOOL_NAME)


__all__ = ["TOOL_NAME", "description", "INPUT_SCHEMA", "handler"]
