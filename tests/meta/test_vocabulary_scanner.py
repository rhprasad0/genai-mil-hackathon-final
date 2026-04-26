"""Vocabulary scanner over generated/seeded narrative + product metadata.

Flags affirmative approval/denial/etc. statements while permitting negative
boundary text and refusal fixtures. Walks the same files as the public-safety
scanner and additionally runs against the in-memory generator output.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from ops.seed.generators.corpus import build_corpus


REPO_ROOT = Path(__file__).resolve().parents[2]


# Affirmative statement patterns. Each entry maps a regex to allowance tokens
# that must NOT both appear in the line for the match to be allowed.
_FLAGS: tuple[tuple[str, re.Pattern[str], tuple[str, ...]], ...] = (
    (
        "affirmative_voucher_disposition",
        re.compile(
            r"\b(?:we|i|the system|ao radar)\s+(?:hereby\s+)?(?:approve|deny|certify|return|cancel|amend|submit)s?\s+the\s+voucher\b",
            re.IGNORECASE,
        ),
        (),
    ),
    (
        "voucher_is_payable",
        re.compile(
            r"\bthis\s+voucher\s+is\s+(?:approved|denied|certified|returned|cancelled|canceled|amended|submitted|payable|nonpayable|ready for payment)\b",
            re.IGNORECASE,
        ),
        (),
    ),
    (
        "fraud_allegation",
        re.compile(
            r"\b(?:appears\s+(?:to\s+be\s+)?fraudulent|is\s+fraudulent|alleg\w+\s+fraud|commit(?:ted|s)?\s+fraud)\b",
            re.IGNORECASE,
        ),
        ("does not", "do not", "no allegation", "never", "not accuse", "rejected_input"),
    ),
    (
        "external_contact",
        re.compile(
            r"\b(?:notified|contacted|escalated\s+to)\s+(?:investigators|command|law enforcement)\b",
            re.IGNORECASE,
        ),
        (),
    ),
)


_FILE_GLOBS: tuple[str, ...] = ("*.py", "*.yaml", "*.yml", "*.md")

# Test fixtures that intentionally inject prohibited strings to verify
# validators reject them. The vocabulary scanner skips these by absolute path.
_INTENTIONAL_NEGATIVE_FIXTURES: frozenset[Path] = frozenset(
    {
        REPO_ROOT / "tests" / "fixtures" / "test_unsafe_wording.py",
    }
)


@pytest.mark.parametrize(
    "scan_dir",
    [
        pytest.param(REPO_ROOT / "ops" / "seed", id="ops/seed"),
        pytest.param(REPO_ROOT / "tests" / "fixtures", id="tests/fixtures"),
    ],
)
def test_vocabulary_scanner_files(scan_dir: Path) -> None:
    if not scan_dir.exists():
        pytest.skip(f"{scan_dir} does not exist")
    for pattern in _FILE_GLOBS:
        for path in sorted(scan_dir.rglob(pattern)):
            if path in _INTENTIONAL_NEGATIVE_FIXTURES:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for line_no, line in enumerate(text.splitlines(), start=1):
                for label, regex, allow_tokens in _FLAGS:
                    match = regex.search(line)
                    if match is None:
                        continue
                    if any(tok in line for tok in allow_tokens):
                        continue
                    # The scanner file itself enumerates the words it flags.
                    if path == Path(__file__):
                        continue
                    raise AssertionError(
                        f"vocabulary hit ({label}) at {path}:{line_no}: {line.strip()[:200]}"
                    )


def test_vocabulary_scanner_in_memory_corpus() -> None:
    """Generated narrative must not contain affirmative dispositions."""

    corpus = build_corpus()
    payloads = []
    for v in corpus.vouchers:
        payloads.append(v["justification_text"])
    for li in corpus.voucher_line_items:
        payloads.append(li["free_text_notes"])
    for f in corpus.story_findings:
        payloads.extend([f["summary"], f["explanation"], f["suggested_question"]])
    for mi in corpus.missing_information_items:
        payloads.extend([mi["description"], mi["why_it_matters"]])
    for b in corpus.review_briefs:
        payloads.extend(
            [
                b["priority_rationale"],
                b["suggested_focus"],
                b["evidence_gap_summary"],
                b["story_coherence_summary"],
                b["draft_clarification_note"],
            ]
        )
    for n in corpus.ao_notes:
        payloads.append(n["body"])

    for text in payloads:
        if not text:
            continue
        for label, regex, allow_tokens in _FLAGS:
            if regex.search(text):
                if not any(tok in text for tok in allow_tokens):
                    raise AssertionError(
                        f"in-memory narrative vocabulary hit ({label}): {text[:200]}"
                    )
