"""Authority-boundary validator.

Asserts every seeded ``review_briefs.human_authority_boundary_text`` and
``workflow_events.human_authority_boundary_reminder`` equals the canonical
string imported from ``ao_radar_mcp.safety.authority_boundary``.
"""

from __future__ import annotations

from typing import Any

from ao_radar_mcp.safety.authority_boundary import HUMAN_AUTHORITY_BOUNDARY_TEXT


class AuthorityBoundaryError(ValueError):
    pass


def validate_corpus(corpus: Any) -> None:
    for b in corpus.review_briefs:
        actual = b.get("human_authority_boundary_text")
        if actual != HUMAN_AUTHORITY_BOUNDARY_TEXT:
            raise AuthorityBoundaryError(
                f"review_briefs[{b['brief_id']}].human_authority_boundary_text "
                f"does not match canonical text"
            )
    for ev in corpus.workflow_events:
        actual = ev.get("human_authority_boundary_reminder")
        if actual != HUMAN_AUTHORITY_BOUNDARY_TEXT:
            raise AuthorityBoundaryError(
                f"workflow_events[{ev['event_id']}].human_authority_boundary_reminder "
                f"does not match canonical text"
            )


__all__ = ["AuthorityBoundaryError", "validate_corpus"]
