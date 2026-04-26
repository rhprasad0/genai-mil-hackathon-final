"""Context-aware unsafe-wording validator (synthetic-data plan section 13).

Walks every narrative field generated for storage and rejects:
- statements that a voucher is approved/denied/certified/returned/cancelled/
  amended/submitted/payable/nonpayable/ready for payment;
- recommendations that the reviewer take an official disposition;
- allegations of fraud/misuse/abuse/misconduct;
- claims that the system has determined entitlement or payability;
- wording that says the system contacted, notified, or escalated to any
  external party.

Permits negative boundary text such as "the system does not approve",
synthetic checklist excerpts, and refusal-event rationale that quotes the
rejected input as long as it is typed as such.

Policy citation excerpts are excluded (they may legitimately mention boundary
verbs in synthetic checklist text).
"""

from __future__ import annotations

import re
from typing import Any

# Each pattern is a regex applied to a lowercased narrative string.
# Each pattern is paired with a small allowance set: if the surrounding text
# contains any of those tokens, the match is treated as boundary-safe.

_BLOCK_PATTERNS: tuple[tuple[re.Pattern[str], tuple[str, ...]], ...] = (
    # Affirmative voucher dispositions.
    (
        re.compile(
            r"\b(?:we|the system|ao radar|i)\s+(?:hereby\s+)?(?:approve|deny|certify|return|cancel|amend|submit)s?\s+(?:this|the)\s+voucher\b"
        ),
        (),
    ),
    (
        re.compile(
            r"\bthis\s+voucher\s+is\s+(?:approved|denied|certified|returned|cancelled|canceled|amended|submitted|payable|nonpayable|ready for payment)\b"
        ),
        (),
    ),
    (
        re.compile(r"\brecommend(?:ed)?\s+(?:to\s+)?(?:approve|deny|certify|return)\b"),
        ("does not", "shall not", "must not", "cannot", "neutral", "review prompt"),
    ),
    (
        re.compile(r"\bofficial\s+(?:approval|denial|return|cancellation|amendment|submission)\b"),
        ("does not", "no official", "without", "shall not", "must not", "cannot"),
    ),
    # Fraud/misuse allegations.
    (
        re.compile(
            r"\b(?:appears\s+(?:to\s+be\s+)?fraudulent|is\s+fraudulent|alleg\w+\s+fraud|commit(?:ted|s)?\s+fraud)\b"
        ),
        (),
    ),
    (
        re.compile(r"\b(?:misconduct|misuse|abuse)\s+(?:by|against|of)\b"),
        ("does not", "no allegation", "not accuse"),
    ),
    # Entitlement / payability determinations.
    (
        re.compile(r"\b(?:has\s+been\s+)?determined\s+(?:to\s+be\s+)?(?:entitled|payable|nonpayable)\b"),
        (),
    ),
    (
        re.compile(r"\bentitlement\s+determination\s+(?:made|complete)\b"),
        (),
    ),
    # External contact.
    (
        re.compile(r"\b(?:notified|contacted|escalated\s+to)\s+(?:investigators|command|law enforcement)\b"),
        (),
    ),
    (
        re.compile(r"\b(?:emailed|called|messaged)\s+the\s+traveler\b"),
        ("synthetic", "demo", "no real traveler"),
    ),
)


class UnsafeWordingError(ValueError):
    pass


def _apply(label: str, text: str | None) -> None:
    if text is None:
        return
    if not isinstance(text, str):
        return
    haystack = text.lower()
    for pattern, allow_tokens in _BLOCK_PATTERNS:
        match = pattern.search(haystack)
        if match is None:
            continue
        if any(tok in haystack for tok in allow_tokens):
            continue
        raise UnsafeWordingError(
            f"{label} contains unsafe wording: matched {pattern.pattern!r} in: {text[:200]}"
        )


def validate_corpus(corpus: Any) -> None:
    for v in corpus.vouchers:
        _apply(f"vouchers.justification_text[{v['voucher_id']}]", v.get("justification_text"))
    for li in corpus.voucher_line_items:
        _apply(
            f"voucher_line_items.free_text_notes[{li['line_item_id']}]",
            li.get("free_text_notes"),
        )
    for ps in corpus.prior_voucher_summaries:
        _apply(
            f"prior_voucher_summaries.summary_text[{ps['prior_summary_id']}]",
            ps.get("summary_text"),
        )
        _apply(
            f"prior_voucher_summaries.recurring_correction_pattern[{ps['prior_summary_id']}]",
            ps.get("recurring_correction_pattern"),
        )
    for s in corpus.external_anomaly_signals:
        _apply(
            f"external_anomaly_signals.rationale_text[{s['signal_id']}]",
            s.get("rationale_text"),
        )
    for f in corpus.story_findings:
        for col in ("summary", "explanation", "suggested_question"):
            _apply(f"story_findings.{col}[{f['finding_id']}]", f.get(col))
    for mi in corpus.missing_information_items:
        for col in ("description", "why_it_matters"):
            _apply(f"missing_information_items.{col}[{mi['missing_item_id']}]", mi.get(col))
    for b in corpus.review_briefs:
        for col in (
            "priority_rationale",
            "suggested_focus",
            "evidence_gap_summary",
            "story_coherence_summary",
            "draft_clarification_note",
        ):
            _apply(f"review_briefs.{col}[{b['brief_id']}]", b.get(col))
    for n in corpus.ao_notes:
        _apply(f"ao_notes.body[{n['note_id']}]", n.get("body"))


__all__ = ["UnsafeWordingError", "validate_corpus"]
