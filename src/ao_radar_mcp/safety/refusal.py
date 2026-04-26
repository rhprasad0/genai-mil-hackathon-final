"""Uniform refusal builder.

Sources of truth:
  - docs/spec.md sections 4.4 (refusal behavior) and 4.4.1 (canonical reminder).
  - docs/application-implementation-plan.md sections 10 and 11.
  - docs/schema-implementation-plan.md sections 6.4 and 8 (audit invariant).

Every refusal — whether DB-backed or in-process — funnels through this
module.  Tools never construct refusals ad hoc.  The builder produces both a
JSON-friendly response payload and a sanitized ``workflow_events`` row
template the audit helper inserts in the same transaction.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Final

from .authority_boundary import (
    HUMAN_AUTHORITY_BOUNDARY_TEXT,
    assert_boundary_text,
)


# ---------------------------------------------------------------------------
# Refusal reason codes (docs/application-implementation-plan.md section 11).
# ---------------------------------------------------------------------------

REASON_PROHIBITED_ACTION: Final[str] = "prohibited_action"
REASON_OUT_OF_SCOPE_ARTIFACT: Final[str] = "out_of_scope_artifact"
REASON_UNSUPPORTED_STATUS_VALUE: Final[str] = "unsupported_status_value"
REASON_UNSAFE_WORDING_IN_INPUT: Final[str] = "unsafe_wording_in_input"
REASON_MISSING_REQUIRED_INPUT: Final[str] = "missing_required_input"
REASON_UNGROUNDED_CLAIM: Final[str] = "ungrounded_claim"

REFUSAL_REASONS: Final[frozenset[str]] = frozenset(
    {
        REASON_PROHIBITED_ACTION,
        REASON_OUT_OF_SCOPE_ARTIFACT,
        REASON_UNSUPPORTED_STATUS_VALUE,
        REASON_UNSAFE_WORDING_IN_INPUT,
        REASON_MISSING_REQUIRED_INPUT,
        REASON_UNGROUNDED_CLAIM,
    }
)

_DEFAULT_NEUTRAL_MESSAGE: Final[str] = (
    "The requested action is outside the supported AO Radar review workflow."
)


def get_boundary_reminder() -> str:
    """Return the configured boundary reminder text (canonical or override)."""

    override = os.environ.get("BOUNDARY_REMINDER_TEXT")
    if override and override.strip():
        return assert_boundary_text(override)
    return HUMAN_AUTHORITY_BOUNDARY_TEXT


@dataclass(frozen=True)
class RefusalResponse:
    """User-facing refusal payload returned by tools/handlers."""

    refused: bool
    reason: str
    message: str
    boundary_reminder: str
    rejected_request: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "refused": self.refused,
            "reason": self.reason,
            "message": self.message,
            "boundary_reminder": self.boundary_reminder,
            "rejected_request": dict(self.rejected_request),
        }


@dataclass(frozen=True)
class RefusalAuditTemplate:
    """Audit row template for ``workflow_events`` (event_type=refusal)."""

    event_type: str
    tool_name: str | None
    target_kind: str
    target_id: str | None
    voucher_id: str | None
    rationale_metadata: dict[str, Any]
    human_authority_boundary_reminder: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "tool_name": self.tool_name,
            "target_kind": self.target_kind,
            "target_id": self.target_id,
            "voucher_id": self.voucher_id,
            "rationale_metadata": dict(self.rationale_metadata),
            "human_authority_boundary_reminder": self.human_authority_boundary_reminder,
        }


@dataclass(frozen=True)
class RefusalBundle:
    """Pair of (response, audit_template) returned by ``build``."""

    response: RefusalResponse
    audit_template: RefusalAuditTemplate

    def to_dict(self) -> dict[str, Any]:
        return {
            "response": self.response.to_dict(),
            "audit_template": self.audit_template.to_dict(),
        }


_SENSITIVE_KEYS: Final[frozenset[str]] = frozenset(
    {"password", "secret", "token", "authorization", "auth", "api_key", "apikey"}
)


def _sanitize_request(rejected_request: dict[str, Any] | None) -> dict[str, Any]:
    """Strip obvious credential-shaped keys before persistence.

    Refusal traceability is allowed to quote the rejected user request, but
    not anything that *looks* like a secret.  This is defense in depth; the
    application is synthetic-only and there is no real auth, but we keep the
    sanitizer so a future wiring mistake cannot leak credentials into the
    audit log.
    """

    if not rejected_request:
        return {}
    out: dict[str, Any] = {}
    for key, value in rejected_request.items():
        if key.lower() in _SENSITIVE_KEYS:
            out[key] = "[redacted]"
            continue
        if isinstance(value, dict):
            out[key] = _sanitize_request(value)
        else:
            out[key] = value
    return out


def build(
    *,
    reason: str,
    message: str | None = None,
    tool_name: str | None = None,
    target_kind: str = "none",
    target_id: str | None = None,
    voucher_id: str | None = None,
    rejected_request: dict[str, Any] | None = None,
    extra_metadata: dict[str, Any] | None = None,
) -> RefusalBundle:
    """Construct the (response, audit-template) pair for a refusal.

    ``reason`` must be one of ``REFUSAL_REASONS``.  The audit template uses
    ``event_type=refusal`` and points at the canonical boundary reminder.
    Callers pass it to the audit helper which writes it inside the same
    transaction as any domain rollback, before the response is returned to
    the client.
    """

    if reason not in REFUSAL_REASONS:
        raise ValueError(f"unknown refusal reason: {reason!r}")

    boundary = get_boundary_reminder()
    text = (message or _DEFAULT_NEUTRAL_MESSAGE).strip()
    rationale: dict[str, Any] = {
        "reason": reason,
        "message": text,
        "rejected_request": _sanitize_request(rejected_request),
    }
    if extra_metadata:
        rationale["extra"] = dict(extra_metadata)

    response = RefusalResponse(
        refused=True,
        reason=reason,
        message=text,
        boundary_reminder=boundary,
        rejected_request=_sanitize_request(rejected_request),
    )
    audit = RefusalAuditTemplate(
        event_type="refusal",
        tool_name=tool_name,
        target_kind=target_kind,
        target_id=target_id,
        voucher_id=voucher_id,
        rationale_metadata=rationale,
        human_authority_boundary_reminder=boundary,
    )
    return RefusalBundle(response=response, audit_template=audit)


__all__ = [
    "REFUSAL_REASONS",
    "REASON_PROHIBITED_ACTION",
    "REASON_OUT_OF_SCOPE_ARTIFACT",
    "REASON_UNSUPPORTED_STATUS_VALUE",
    "REASON_UNSAFE_WORDING_IN_INPUT",
    "REASON_MISSING_REQUIRED_INPUT",
    "REASON_UNGROUNDED_CLAIM",
    "RefusalResponse",
    "RefusalAuditTemplate",
    "RefusalBundle",
    "build",
    "get_boundary_reminder",
]
