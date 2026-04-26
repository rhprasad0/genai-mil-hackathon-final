"""FK presence + volume range validator.

Synthetic-data plan section 13 + schema plan section 7.5.
"""

from __future__ import annotations

from typing import Any

# Volume ranges per schema plan section 7.5.
VOLUME_RANGES: dict[str, tuple[int, int]] = {
    "travelers": (5, 6),
    "vouchers": (12, 12),
    "voucher_line_items": (75, 100),
    "evidence_refs": (75, 150),
    "external_anomaly_signals": (20, 25),
    "story_findings": (35, 50),
    "missing_information_items": (20, 30),
    "review_briefs": (12, 12),
    "workflow_events": (50, 70),
}


# Required spread of vouchers.review_status (schema plan section 7.3).
REVIEW_STATUS_SPREAD: dict[str, set[str]] = {
    "needs_review": {"V-1006", "V-1009", "V-1010", "V-1012"},
    "in_review": {"V-1002", "V-1003", "V-1004", "V-1007", "V-1008", "V-1011"},
    "ready_for_human_decision": {"V-1001", "V-1005"},
}


class FkVolumeError(ValueError):
    pass


def validate_corpus(corpus: Any) -> None:
    # FK resolution.
    traveler_ids = {t["traveler_id"] for t in corpus.travelers}
    voucher_ids = {v["voucher_id"] for v in corpus.vouchers}
    line_ids = {li["line_item_id"] for li in corpus.voucher_line_items}
    citation_ids = {c["citation_id"] for c in corpus.policy_citations}
    finding_ids = {f["finding_id"] for f in corpus.story_findings}
    signal_ids = {s["signal_id"] for s in corpus.external_anomaly_signals}
    brief_ids = {b["brief_id"] for b in corpus.review_briefs}
    note_ids = {n["note_id"] for n in corpus.ao_notes}

    for v in corpus.vouchers:
        if v["traveler_id"] not in traveler_ids:
            raise FkVolumeError(f"vouchers.traveler_id={v['traveler_id']!r} not found")
    for ps in corpus.prior_voucher_summaries:
        if ps["traveler_id"] not in traveler_ids:
            raise FkVolumeError(
                f"prior_voucher_summaries.traveler_id={ps['traveler_id']!r} not found"
            )
    for li in corpus.voucher_line_items:
        if li["voucher_id"] not in voucher_ids:
            raise FkVolumeError(
                f"voucher_line_items.voucher_id={li['voucher_id']!r} not found"
            )
    for ev in corpus.evidence_refs:
        if ev["voucher_id"] not in voucher_ids:
            raise FkVolumeError(f"evidence_refs.voucher_id={ev['voucher_id']!r} not found")
        if ev.get("line_item_id") and ev["line_item_id"] not in line_ids:
            raise FkVolumeError(
                f"evidence_refs.line_item_id={ev['line_item_id']!r} not found"
            )
        # Schema-plan rule: every evidence row needs either line_item_id or
        # packet_level_role.
        if not ev.get("line_item_id") and not ev.get("packet_level_role"):
            raise FkVolumeError(
                f"evidence_refs[{ev['evidence_ref_id']}] needs line_item_id or packet_level_role"
            )
    for s in corpus.external_anomaly_signals:
        if s["voucher_id"] not in voucher_ids:
            raise FkVolumeError(
                f"external_anomaly_signals.voucher_id={s['voucher_id']!r} not found"
            )
    for f in corpus.story_findings:
        if f["voucher_id"] not in voucher_ids:
            raise FkVolumeError(f"story_findings.voucher_id={f['voucher_id']!r} not found")
        if f.get("primary_citation_id") and f["primary_citation_id"] not in citation_ids:
            raise FkVolumeError(
                f"story_findings.primary_citation_id={f['primary_citation_id']!r} not found"
            )
    for fl in corpus.finding_signal_links:
        if fl["finding_id"] not in finding_ids:
            raise FkVolumeError(
                f"finding_signal_links.finding_id={fl['finding_id']!r} not found"
            )
        if fl["signal_id"] not in signal_ids:
            raise FkVolumeError(
                f"finding_signal_links.signal_id={fl['signal_id']!r} not found"
            )
    for mi in corpus.missing_information_items:
        if mi["voucher_id"] not in voucher_ids:
            raise FkVolumeError(
                f"missing_information_items.voucher_id={mi['voucher_id']!r} not found"
            )
        if mi.get("linked_line_item_id") and mi["linked_line_item_id"] not in line_ids:
            raise FkVolumeError(
                f"missing_information_items.linked_line_item_id="
                f"{mi['linked_line_item_id']!r} not found"
            )
    for b in corpus.review_briefs:
        if b["voucher_id"] not in voucher_ids:
            raise FkVolumeError(f"review_briefs.voucher_id={b['voucher_id']!r} not found")
        for ph in b.get("policy_hooks", []):
            if ph not in citation_ids:
                raise FkVolumeError(f"review_briefs.policy_hooks entry {ph!r} not found")
        for sh in b.get("signal_hooks", []):
            if sh not in signal_ids:
                raise FkVolumeError(f"review_briefs.signal_hooks entry {sh!r} not found")
        for fh in b.get("finding_hooks", []):
            if fh not in finding_ids:
                raise FkVolumeError(f"review_briefs.finding_hooks entry {fh!r} not found")
        for mh in b.get("missing_information_hooks", []):
            if mh not in {mi["missing_item_id"] for mi in corpus.missing_information_items}:
                raise FkVolumeError(
                    f"review_briefs.missing_information_hooks entry {mh!r} not found"
                )
    for n in corpus.ao_notes:
        if n["voucher_id"] not in voucher_ids:
            raise FkVolumeError(f"ao_notes.voucher_id={n['voucher_id']!r} not found")
        if n.get("finding_id") and n["finding_id"] not in finding_ids:
            raise FkVolumeError(f"ao_notes.finding_id={n['finding_id']!r} not found")
    for ev in corpus.workflow_events:
        if ev.get("voucher_id") and ev["voucher_id"] not in voucher_ids:
            raise FkVolumeError(
                f"workflow_events.voucher_id={ev['voucher_id']!r} not found"
            )

    # Volume ranges.
    counts = {
        "travelers": len(corpus.travelers),
        "vouchers": len(corpus.vouchers),
        "voucher_line_items": len(corpus.voucher_line_items),
        "evidence_refs": len(corpus.evidence_refs),
        "external_anomaly_signals": len(corpus.external_anomaly_signals),
        "story_findings": len(corpus.story_findings),
        "missing_information_items": len(corpus.missing_information_items),
        "review_briefs": len(corpus.review_briefs),
        "workflow_events": len(corpus.workflow_events),
    }
    for name, (lo, hi) in VOLUME_RANGES.items():
        n = counts[name]
        if not (lo <= n <= hi):
            raise FkVolumeError(
                f"volume out of range: {name}={n}, expected [{lo}, {hi}]"
            )

    # is_partial=True must appear on >=1 brief (V-1011).
    partial = [b for b in corpus.review_briefs if b.get("is_partial")]
    if not partial:
        raise FkVolumeError("no review_briefs row has is_partial=True (expected V-1011)")
    if "V-1011" not in {b["voucher_id"] for b in partial}:
        raise FkVolumeError("V-1011 brief must have is_partial=True")

    # review_status spread.
    actual_spread: dict[str, set[str]] = {}
    for v in corpus.vouchers:
        actual_spread.setdefault(v["review_status"], set()).add(v["voucher_id"])
    for status, expected_vouchers in REVIEW_STATUS_SPREAD.items():
        actual = actual_spread.get(status, set())
        if actual != expected_vouchers:
            raise FkVolumeError(
                f"review_status={status!r} expected vouchers {sorted(expected_vouchers)}, "
                f"got {sorted(actual)}"
            )


__all__ = ["FkVolumeError", "VOLUME_RANGES", "REVIEW_STATUS_SPREAD", "validate_corpus"]
