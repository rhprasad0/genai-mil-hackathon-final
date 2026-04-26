"""``get_external_anomaly_signals`` tool module.

Spec reference: docs/spec.md section 4.5.1.  Each signal is explicitly a
review prompt, not an official finding (FR-4, TR-3, AC-14).
"""

from __future__ import annotations

from typing import Any

from ._common import _description, not_implemented_response

TOOL_NAME = "get_external_anomaly_signals"

description = _description(
    "Return synthetic risk indicators from the stand-in compliance/anomaly "
    "service for a voucher. Each signal is a review prompt only, not an "
    "official finding, and not sufficient for adverse action."
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
    # TODO Phase 3: read persisted signals via repository.signals and call
    # the fraud-mock client; persist new signals through an idempotent
    # ``(voucher_id, signal_key)`` upsert; emit a ``retrieval`` audit row.
    return not_implemented_response(TOOL_NAME)


__all__ = ["TOOL_NAME", "description", "INPUT_SCHEMA", "handler"]
