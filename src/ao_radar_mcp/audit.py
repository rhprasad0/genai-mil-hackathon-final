"""Audit-event invariant helper.

Sources of truth:
  - docs/spec.md sections 4.5.2 and 4.5.4 (audit event shape).
  - docs/schema-implementation-plan.md section 8 (audit-event invariant
    matrix; same transaction as the domain write).
  - docs/application-implementation-plan.md section 10.

Every successful scoped write writes exactly one ``workflow_events`` row in
the same database transaction as the domain write.  Every DB-backed refusal
writes exactly one ``workflow_events`` row with ``event_type=refusal``
before the response returns.

Tools never construct workflow-event payloads ad hoc.  They build an
``AuditEventTemplate`` and pass it (with a domain callable) into
``run_with_audit``.  In Phase 1 the implementation is a thin in-process
helper that returns the assembled event payload; the repository layer
(Phase 2+) overrides ``persist_workflow_event`` to insert through psycopg
inside the same transaction as the domain write.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal, TypeVar

from .safety.refusal import RefusalAuditTemplate, get_boundary_reminder


EventType = Literal[
    "scoped_write",
    "refusal",
    "needs_human_review_label",
    "retrieval",
    "generation",
    "edit",
    "export",
]

TargetKind = Literal[
    "voucher",
    "finding",
    "note",
    "brief",
    "signal",
    "citation",
    "missing_item",
    "none",
]


@dataclass(frozen=True)
class AuditEventTemplate:
    """Audit row template for ``workflow_events``.

    ``run_with_audit`` materializes a concrete event row from this template,
    populating ``event_id``, ``occurred_at``, and the canonical boundary
    reminder.
    """

    event_type: EventType
    tool_name: str | None
    target_kind: TargetKind
    target_id: str | None
    voucher_id: str | None
    actor_label: str
    rationale_metadata: dict[str, Any] = field(default_factory=dict)
    resulting_status: str | None = None


@dataclass(frozen=True)
class AuditEventRecord:
    """Materialized audit row that the repository layer persists."""

    event_id: str
    voucher_id: str | None
    actor_label: str
    occurred_at: datetime
    event_type: str
    tool_name: str | None
    target_kind: str
    target_id: str | None
    resulting_status: str | None
    rationale_metadata: dict[str, Any]
    human_authority_boundary_reminder: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "voucher_id": self.voucher_id,
            "actor_label": self.actor_label,
            "occurred_at": self.occurred_at.isoformat(),
            "event_type": self.event_type,
            "tool_name": self.tool_name,
            "target_kind": self.target_kind,
            "target_id": self.target_id,
            "resulting_status": self.resulting_status,
            "rationale_metadata": dict(self.rationale_metadata),
            "human_authority_boundary_reminder": self.human_authority_boundary_reminder,
        }


T = TypeVar("T")


def _new_event_id() -> str:
    return f"EVT-{uuid.uuid4().hex[:12]}"


def materialize(template: AuditEventTemplate) -> AuditEventRecord:
    """Materialize an ``AuditEventTemplate`` into a concrete row."""

    return AuditEventRecord(
        event_id=_new_event_id(),
        voucher_id=template.voucher_id,
        actor_label=template.actor_label,
        occurred_at=datetime.now(tz=UTC),
        event_type=template.event_type,
        tool_name=template.tool_name,
        target_kind=template.target_kind,
        target_id=template.target_id,
        resulting_status=template.resulting_status,
        rationale_metadata=dict(template.rationale_metadata),
        human_authority_boundary_reminder=get_boundary_reminder(),
    )


def materialize_refusal(template: RefusalAuditTemplate, actor_label: str) -> AuditEventRecord:
    """Materialize the audit row that pairs with a refusal response."""

    return AuditEventRecord(
        event_id=_new_event_id(),
        voucher_id=template.voucher_id,
        actor_label=actor_label,
        occurred_at=datetime.now(tz=UTC),
        event_type=template.event_type,
        tool_name=template.tool_name,
        target_kind=template.target_kind,
        target_id=template.target_id,
        resulting_status=None,
        rationale_metadata=dict(template.rationale_metadata),
        human_authority_boundary_reminder=template.human_authority_boundary_reminder,
    )


@dataclass
class AuditedDomainResult:
    """Pair of (domain result, materialized audit event)."""

    domain_result: Any
    audit_event: AuditEventRecord


def run_with_audit(
    *,
    domain_callable: Callable[[], T],
    template: AuditEventTemplate,
    persist_workflow_event: Callable[[AuditEventRecord], None] | None = None,
) -> AuditedDomainResult:
    """Run the domain callable and emit a paired audit event.

    The Phase 1 implementation simply materializes the event and (optionally)
    invokes ``persist_workflow_event``.  The Phase 2 repository wires this
    helper into a single-transaction context manager so the audit row and the
    domain row commit or roll back together.
    """

    domain_result = domain_callable()
    event = materialize(template)
    if persist_workflow_event is not None:
        persist_workflow_event(event)
    return AuditedDomainResult(domain_result=domain_result, audit_event=event)


__all__ = [
    "AuditEventRecord",
    "AuditEventTemplate",
    "AuditedDomainResult",
    "EventType",
    "TargetKind",
    "materialize",
    "materialize_refusal",
    "run_with_audit",
]
