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
availability.  Phase 2/3/4 wire each handler into the repository layer and
the audit invariant.
"""

from __future__ import annotations

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


__all__ = ["_description", "not_implemented_response"]
