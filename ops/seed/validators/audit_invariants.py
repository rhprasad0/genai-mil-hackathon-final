"""Audit-invariant validator.

Walks the schema plan section 8 audit-event matrix and asserts every seeded
scoped write, every seeded brief generation, every seeded
``story_findings.needs_human_review = true`` finding, and the two seeded
refusals produce a matching ``workflow_events`` row in the generator output.
"""

from __future__ import annotations

from typing import Any


class AuditInvariantError(ValueError):
    pass


def validate_corpus(corpus: Any) -> None:
    events_by_target: dict[tuple[str, str | None], list[dict[str, Any]]] = {}
    for ev in corpus.workflow_events:
        events_by_target.setdefault((ev["event_type"], ev.get("target_id")), []).append(ev)

    # 1. Every seeded brief produces a generation event referencing brief_id.
    for brief in corpus.review_briefs:
        matches = events_by_target.get(("generation", brief["brief_id"]), [])
        if not matches:
            raise AuditInvariantError(
                f"review_briefs[{brief['brief_id']}] has no matching generation workflow_event"
            )
        if not any(m.get("tool_name") == "prepare_ao_review_brief" for m in matches):
            raise AuditInvariantError(
                f"review_briefs[{brief['brief_id']}] generation event missing "
                f"tool_name=prepare_ao_review_brief"
            )

    # 2. Every seeded ao_note produces a scoped_write event.
    for note in corpus.ao_notes:
        # synthetic_clarification_request targets the voucher; other kinds target the note.
        if note["kind"] == "synthetic_clarification_request":
            target_id = note["voucher_id"]
        else:
            target_id = note["note_id"]
        matches = events_by_target.get(("scoped_write", target_id), [])
        if not matches:
            raise AuditInvariantError(
                f"ao_notes[{note['note_id']}] has no matching scoped_write workflow_event"
            )

    # 3. Every needs_human_review=true finding produces a needs_human_review_label event.
    for finding in corpus.story_findings:
        if finding["needs_human_review"]:
            matches = events_by_target.get(("needs_human_review_label", finding["finding_id"]), [])
            if not matches:
                raise AuditInvariantError(
                    f"story_findings[{finding['finding_id']}] needs_human_review=true "
                    f"has no matching needs_human_review_label workflow_event"
                )

    # 4. The two seeded refusals exist (V-1001 set_voucher_review_status; V-1010
    # prepare_ao_review_brief).
    refusal_keys = {(ev["voucher_id"], ev["tool_name"]) for ev in corpus.workflow_events
                    if ev["event_type"] == "refusal"}
    required = {("V-1001", "set_voucher_review_status"), ("V-1010", "prepare_ao_review_brief")}
    missing = required - refusal_keys
    if missing:
        raise AuditInvariantError(f"missing required seeded refusals: {missing}")


__all__ = ["AuditInvariantError", "validate_corpus"]
