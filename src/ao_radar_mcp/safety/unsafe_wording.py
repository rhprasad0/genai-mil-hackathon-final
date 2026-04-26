"""Context-aware unsafe-wording validator for AO Radar narrative text.

Sources of truth:
  - docs/spec.md sections 3.8 (TR-1, TR-3, TR-4, TR-11) and 4.3.
  - docs/schema-implementation-plan.md section 6.4 (free-text rules).
  - docs/application-implementation-plan.md section 11.

The status-like CHECK constraints are the canonical, hard rejection path for
``vouchers.review_status``, ``story_findings.review_state``, and
``workflow_events.resulting_status``.  This validator applies to *narrative*
fields where the words ``approve``, ``return``, ``payable``, ``entitlement``,
and ``fraud`` may legitimately appear inside negative boundary statements,
verbatim policy/checklist excerpts, or refusal traceability metadata.  The
validator is therefore advisory: it rejects unsafe assertions, recommendations
of official disposition, fraud allegations, payability/entitlement
determinations, and claims that the system contacted external parties — while
allowing negative boundary statements ("this is not an official approval"),
verbatim citations, and refusal-context strings that quote the rejected
request for traceability.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class UnsafeWordingResult:
    """Result of running ``check`` over a candidate string."""

    is_safe: bool
    reason: str | None
    matched_phrase: str | None

    @property
    def violation_reason(self) -> str | None:
        """Backwards-friendly alias for ``reason``."""

        return self.reason


# ---------------------------------------------------------------------------
# Canonical set of unsafe assertion patterns.
# ---------------------------------------------------------------------------
# Each pattern below is keyed to a refusal reason category.  The pattern is a
# compiled case-insensitive regular expression.  Patterns are deliberately
# specific so they can fire on system-authored claims while leaving negative
# boundary statements alone.

_OFFICIAL_DISPOSITION_PATTERNS: Final[tuple[re.Pattern[str], ...]] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        # System-authored assertions of approval / denial / certification / etc.
        r"\bvoucher\s+is\s+(?:approved|denied|certified|paid|payable|"
        r"non\s*payable|nonpayable|ready\s+for\s+payment|payment\s+ready|"
        r"officially\s+returned|officially\s+cancelled|officially\s+amended|"
        r"officially\s+submitted)\b",
        r"\bthis\s+(?:voucher|packet|line\s+item|expense)\s+is\s+(?:approved|"
        r"denied|certified|paid|payable|nonpayable|ready\s+for\s+payment)\b",
        r"\b(?:approves|denies|certifies|returns|cancels|amends|submits)\s+"
        r"(?:the|this)\s+(?:voucher|packet|claim)\b",
        r"\bsystem\s+(?:approves|denies|certifies|has\s+approved|has\s+denied|"
        r"has\s+certified|has\s+returned|has\s+submitted)\b",
        # Recommendations of official disposition.
        r"\b(?:reviewer|ao|approving\s+official)\s+should\s+(?:approve|deny|"
        r"certify|return|cancel|amend|submit|pay)\b",
        r"\brecommend(?:s|ed)?\s+(?:approval|denial|certification|return|"
        r"cancellation|amendment|submission|payment)\b",
        r"\bplease\s+(?:approve|deny|certify|return|cancel|amend|submit)\s+"
        r"(?:the|this)\s+(?:voucher|packet|claim)\b",
    )
)

_FRAUD_ALLEGATION_PATTERNS: Final[tuple[re.Pattern[str], ...]] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\b(?:traveler|vendor|transaction|claim|expense|line\s+item)\s+is\s+"
        r"(?:fraudulent|fraud|misuse|abusive|misconduct|engaged\s+in\s+misconduct)\b",
        r"\bcommitted\s+(?:fraud|misuse|abuse|misconduct)\b",
        r"\bappears\s+to\s+be\s+(?:fraud|fraudulent|misuse|abuse|misconduct)\b",
        r"\bthis\s+is\s+(?:fraud|fraudulent|misuse|abuse|misconduct)\b",
    )
)

_ENTITLEMENT_PAYABILITY_PATTERNS: Final[tuple[re.Pattern[str], ...]] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bsystem\s+(?:has\s+)?determined\s+(?:entitlement|payability)\b",
        r"\bdetermined\s+to\s+be\s+(?:payable|nonpayable|entitled|"
        r"not\s+entitled|payment\s+ready)\b",
        r"\bofficially\s+(?:entitled|not\s+entitled|payable|nonpayable)\b",
    )
)

_EXTERNAL_CONTACT_PATTERNS: Final[tuple[re.Pattern[str], ...]] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\b(?:we|i|the\s+system|ao\s+radar)\s+(?:have\s+)?contacted\s+the\s+"
        r"(?:traveler|investigator|investigators|command|law\s+enforcement)\b",
        r"\b(?:we|i|the\s+system|ao\s+radar)\s+(?:have\s+)?notified\s+the\s+"
        r"(?:traveler|investigator|investigators|command|law\s+enforcement)\b",
        r"\b(?:we|i|the\s+system|ao\s+radar)\s+(?:have\s+)?escalated\s+to\s+"
        r"(?:investigators|command|law\s+enforcement)\b",
        r"\bemail(?:ed)?\s+the\s+traveler\b",
        r"\bcalled\s+the\s+traveler\b",
        r"\bsent\s+(?:an?\s+)?(?:email|message|notification)\s+to\s+"
        r"(?:the\s+)?(?:traveler|investigator|investigators|command)\b",
    )
)

# Patterns describing legitimate negative-boundary or refusal-context strings.
# A candidate that contains any of these AND looks like an unsafe phrase will
# be classified as safe, because the surrounding text is explicitly negating
# the prohibited action or quoting it for traceability.
_NEGATIVE_BOUNDARY_PATTERNS: Final[tuple[re.Pattern[str], ...]] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bnot\s+an?\s+official\b",
        r"\bis\s+not\s+(?:approved|denied|certified|payable|nonpayable|"
        r"ready\s+for\s+payment|fraud|fraudulent)\b",
        r"\bdoes\s+not\s+(?:approve|deny|certify|return|cancel|amend|submit|"
        r"determine|accuse|contact)\b",
        r"\bdoes\s+not\s+contact\s+external\s+parties\b",
        r"\bcannot\s+(?:approve|deny|certify|return|cancel|amend|submit|"
        r"determine|accuse|contact)\b",
        r"\bshall\s+not\s+(?:approve|deny|certify|return|cancel|amend|submit|"
        r"determine|accuse|contact)\b",
        r"\bwill\s+not\s+(?:approve|deny|certify|return|cancel|amend|submit|"
        r"determine|accuse|contact)\b",
        r"\bnot\s+sufficient\s+for\s+adverse\s+action\b",
        r"\bnot\s+an\s+official\s+finding\b",
        r"\breview\s+prompt\s+only\b",
        r"\brefused\s+with\s+reason\b",
        r"\brejected\s+request\b",
        r"\brequested\s+action\s+is\s+outside\b",
    )
)


_REASON_OFFICIAL_DISPOSITION: Final[str] = "system_authored_official_disposition"
_REASON_FRAUD_ALLEGATION: Final[str] = "system_authored_fraud_allegation"
_REASON_ENTITLEMENT_PAYABILITY: Final[str] = "system_authored_entitlement_or_payability"
_REASON_EXTERNAL_CONTACT: Final[str] = "system_authored_external_contact"


def _looks_like_negative_boundary(text: str) -> bool:
    """Return True when the text contains an explicit negation/refusal phrase."""

    return any(p.search(text) for p in _NEGATIVE_BOUNDARY_PATTERNS)


def check(text: str) -> UnsafeWordingResult:
    """Run the context-aware validator over ``text``.

    Returns ``UnsafeWordingResult(is_safe=True, reason=None)`` for safe text
    (including empty input).  Returns ``is_safe=False`` plus a violation
    reason for system-authored unsafe assertions.  Negative boundary phrases
    such as ``"this is not an official approval"`` are explicitly accepted.
    """

    if text is None or not text.strip():
        return UnsafeWordingResult(is_safe=True, reason=None, matched_phrase=None)

    candidate = text

    # When the text is dominated by an explicit negation/boundary statement,
    # let it through.  This is the normal case for boundary reminders, refusal
    # narrative, and safe brief paragraphs.
    if _looks_like_negative_boundary(candidate):
        # We still check fraud / external contact patterns, since "we
        # contacted the traveler" cannot be sanitized by a separate negative
        # phrase elsewhere in the same document.
        for pattern in _FRAUD_ALLEGATION_PATTERNS:
            match = pattern.search(candidate)
            if match:
                return UnsafeWordingResult(
                    is_safe=False,
                    reason=_REASON_FRAUD_ALLEGATION,
                    matched_phrase=match.group(0),
                )
        for pattern in _EXTERNAL_CONTACT_PATTERNS:
            match = pattern.search(candidate)
            if match:
                return UnsafeWordingResult(
                    is_safe=False,
                    reason=_REASON_EXTERNAL_CONTACT,
                    matched_phrase=match.group(0),
                )
        return UnsafeWordingResult(is_safe=True, reason=None, matched_phrase=None)

    for pattern in _OFFICIAL_DISPOSITION_PATTERNS:
        match = pattern.search(candidate)
        if match:
            return UnsafeWordingResult(
                is_safe=False,
                reason=_REASON_OFFICIAL_DISPOSITION,
                matched_phrase=match.group(0),
            )
    for pattern in _FRAUD_ALLEGATION_PATTERNS:
        match = pattern.search(candidate)
        if match:
            return UnsafeWordingResult(
                is_safe=False,
                reason=_REASON_FRAUD_ALLEGATION,
                matched_phrase=match.group(0),
            )
    for pattern in _ENTITLEMENT_PAYABILITY_PATTERNS:
        match = pattern.search(candidate)
        if match:
            return UnsafeWordingResult(
                is_safe=False,
                reason=_REASON_ENTITLEMENT_PAYABILITY,
                matched_phrase=match.group(0),
            )
    for pattern in _EXTERNAL_CONTACT_PATTERNS:
        match = pattern.search(candidate)
        if match:
            return UnsafeWordingResult(
                is_safe=False,
                reason=_REASON_EXTERNAL_CONTACT,
                matched_phrase=match.group(0),
            )

    return UnsafeWordingResult(is_safe=True, reason=None, matched_phrase=None)


def is_safe(text: str) -> bool:
    """Convenience: return ``True`` iff ``check(text).is_safe``."""

    return check(text).is_safe


__all__ = [
    "UnsafeWordingResult",
    "check",
    "is_safe",
]
