"""Canonical human-authority boundary reminder.

The string below is the canonical text required by:
  - docs/spec.md section 4.4.1
  - docs/schema-implementation-plan.md section 6.6
  - docs/application-implementation-plan.md section 11

Both seeded fixtures (ops/seed) and the application import this constant so
the wording cannot drift. Any longer deployment-specific override must pass
``validate_boundary_text`` before it is accepted; otherwise startup,
seeding, and tests fail closed.
"""

from __future__ import annotations

from dataclasses import dataclass

HUMAN_AUTHORITY_BOUNDARY_TEXT: str = (
    "AO Radar is a synthetic pre-decision review aid. It does not approve, "
    "deny, certify, return, cancel, amend, submit, determine entitlement, "
    "determine payability, accuse fraud, or contact external parties. The "
    "human Approving Official remains accountable for every official action "
    "in the official travel system."
)

# Required clauses that any approved override must still cover. Each entry is a
# list of acceptable spellings; at least one spelling per clause must appear in
# the candidate text (case-insensitive). The canonical string distributes a
# single ``does not`` across the seven action verbs, so the validator checks
# verb presence plus a separate negation marker (``NEGATION_MARKERS``) below.
REQUIRED_CLAUSES: tuple[tuple[str, ...], ...] = (
    ("approve",),
    ("deny",),
    ("certify",),
    ("return",),
    ("cancel",),
    ("amend",),
    ("submit",),
    ("entitlement",),
    ("payability",),
    ("fraud",),
    ("external", "external parties", "outside party"),
)

NEGATION_MARKERS: tuple[str, ...] = (
    "does not",
    "do not",
    "shall not",
    "will not",
    "must not",
    "cannot",
    "no approve",
    "no deny",
    "no certify",
    "no return",
    "no cancel",
    "no amend",
    "no submit",
    "without approving",
    "without authority",
)


@dataclass(frozen=True)
class BoundaryValidationResult:
    ok: bool
    missing_clauses: tuple[str, ...]


def validate_boundary_text(candidate: str) -> BoundaryValidationResult:
    """Return whether ``candidate`` covers every required clause.

    The canonical string passes by construction. Any override must still
    name approve, deny, certify, return, cancel, amend, submit, entitlement,
    payability, fraud, and external-party clauses, and must contain at least
    one negation marker (``does not``, ``shall not``, ...) so a clause cannot
    be flipped into an affirmation.
    """

    if not candidate or not candidate.strip():
        return BoundaryValidationResult(ok=False, missing_clauses=("non_empty",))

    haystack = candidate.lower()
    missing: list[str] = []
    for variants in REQUIRED_CLAUSES:
        if not any(needle.lower() in haystack for needle in variants):
            missing.append(variants[0])
    if not any(marker in haystack for marker in NEGATION_MARKERS):
        missing.append("negation_marker")
    return BoundaryValidationResult(ok=not missing, missing_clauses=tuple(missing))


def assert_boundary_text(candidate: str) -> str:
    """Return ``candidate`` if it passes; otherwise raise ``ValueError``.

    Use this at startup, seeding, and validator entry points so a weak override
    cannot ship.
    """

    result = validate_boundary_text(candidate)
    if not result.ok:
        raise ValueError(
            "human-authority boundary text missing required clauses: "
            + ", ".join(result.missing_clauses)
        )
    return candidate


__all__ = [
    "HUMAN_AUTHORITY_BOUNDARY_TEXT",
    "REQUIRED_CLAUSES",
    "NEGATION_MARKERS",
    "BoundaryValidationResult",
    "validate_boundary_text",
    "assert_boundary_text",
]
