"""Shared helpers for tool modules.

Every spec section 4.5 tool module exports the same four attributes:

  - ``TOOL_NAME``: the canonical tool name used by ``tools/list``.
  - ``description``: a short reviewer-readable description that mentions
    the human-authority boundary in plain language.
  - ``INPUT_SCHEMA``: a JSON Schema dict describing the accepted inputs.
  - ``handler``: a callable that accepts the parsed input and returns either
    a domain response or a refusal response.

In Phase 1 every handler returns a ``not_implemented`` placeholder so the
catalog can advertise correctly without depending on database or fraud-mock
availability.  In Phase 2/3/4/5 each handler dispatches to the repository
layer when the runtime DB is available; otherwise it still returns the
Phase 1 stub so the contract tests continue to dispatch without error.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from ..safety.authority_boundary import HUMAN_AUTHORITY_BOUNDARY_TEXT
from ..safety.refusal import get_boundary_reminder

_BOUNDARY_PHRASE: str = (
    "AO Radar produces review aids only; the human Approving Official remains "
    "accountable for every official action in the official travel system."
)


def _description(prefix: str) -> str:
    """Compose a tool description that mentions the boundary in plain language."""

    return f"{prefix.strip()} {_BOUNDARY_PHRASE}"


def not_implemented_response(tool_name: str) -> dict[str, Any]:
    """Return a stub response that respects the schema and is safe to log.

    Used by Phase 1 handlers before the repository / fraud-client paths are
    wired.  Includes the canonical boundary reminder so downstream cockpits
    see it even from a stub.
    """

    return {
        "status": "not_implemented",
        "tool": tool_name,
        "boundary_reminder": get_boundary_reminder(),
        "human_authority_boundary_text": HUMAN_AUTHORITY_BOUNDARY_TEXT,
        "note": "Phase 1 stub. The handler will be wired in a later phase per "
        "docs/application-implementation-plan.md section 7.",
    }


def with_boundary(payload: dict[str, Any]) -> dict[str, Any]:
    """Ensure every tool response carries the canonical boundary reminder."""

    enriched = dict(payload)
    enriched.setdefault("boundary_reminder", get_boundary_reminder())
    enriched.setdefault("human_authority_boundary_text", HUMAN_AUTHORITY_BOUNDARY_TEXT)
    return enriched


def to_jsonable(value: Any) -> Any:
    """Recursively convert datetimes/dates/Decimals/None into JSON-friendly types."""

    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): to_jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(item) for item in value]
    return str(value)


__all__ = [
    "_description",
    "not_implemented_response",
    "to_jsonable",
    "with_boundary",
]
