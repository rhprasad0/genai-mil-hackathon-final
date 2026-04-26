"""Public-safety scanner across committed test artifacts.

Walks every committed file under ``ops/seed/`` and ``tests/fixtures/`` and
fails on patterns that imply real PII, real GTCC PANs, real bank routing
numbers, real DoD/JTR/DTMO text, or machine-local paths.

The scanner is deliberately conservative: false positives should be fixed by
keeping fixtures synthetic, not by widening the allowlist. Real public
validation hooks live inside ``docs/`` (those are excluded).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


# Files we scan: every fixture/seed source the synthetic-data team owns.
_SCAN_DIRS: tuple[Path, ...] = (
    REPO_ROOT / "ops" / "seed",
    REPO_ROOT / "tests" / "fixtures",
    REPO_ROOT / "tests" / "meta",
)


# Each pattern is paired with optional allowance substrings: matches are
# permitted when the surrounding line contains one of these tokens, e.g.
# ``LOA-DEMO-FY26-1234`` is a 9-digit pattern hit only when broken across
# fields.
_PATTERNS: tuple[tuple[str, re.Pattern[str], tuple[str, ...]], ...] = (
    (
        "credit_card_pan_shape",
        re.compile(r"\b\d{16}\b"),
        (),
    ),
    (
        "ssn_shape",
        re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        (),
    ),
    (
        "bank_routing_shape",
        re.compile(r"(?<![\w-])\d{9}(?![\w-])"),
        ("LOA-DEMO-FY26-",),
    ),
    (
        "machine_local_path_home",
        re.compile(r"/home/[a-z0-9._-]+/"),
        (),
    ),
    (
        "machine_local_path_users",
        re.compile(r"/Users/[a-z0-9._-]+/"),
        (),
    ),
    (
        "real_domain_email",
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        ("@example.com", ".demo", "(Synthetic Demo)"),
    ),
    (
        "aws_access_key",
        re.compile(r"\b(AKIA|ASIA)[A-Z0-9]{16}\b"),
        (),
    ),
    (
        # Slack channel IDs follow C + 10 uppercase alphanumeric and always
        # contain at least one digit. The digit requirement avoids matching
        # Python identifiers such as CONFIDENCES.
        "slack_channel_id",
        re.compile(r"\bC(?=[A-Z0-9]{10}\b)[A-Z0-9]*[0-9][A-Z0-9]*\b"),
        ("CITE-", "_DEMO_", "DEMO-", "T-", "V-", "SIG-"),
    ),
    (
        "slack_token",
        re.compile(r"\bxox[baprs]-[A-Za-z0-9-]+\b"),
        (),
    ),
    (
        "real_dod_jtr_dtmo_text",
        re.compile(
            r"\b("
            r"JTR section|JTR Section|"
            r"DoDFMR Vol\.? ?5|DoD FMR Volume 5|"
            r"DTMO Acquisition Vendor|DTMO acquisition vendor|"
            r"Travel Policy Compliance Tool"
            r")\b"
        ),
        (),
    ),
)


@pytest.mark.parametrize(
    "scan_dir",
    [pytest.param(d, id=str(d.relative_to(REPO_ROOT))) for d in _SCAN_DIRS],
)
def test_public_safety_scanner(scan_dir: Path) -> None:
    if not scan_dir.exists():
        pytest.skip(f"{scan_dir} does not exist")
    for path in sorted(scan_dir.rglob("*")):
        if path.is_dir():
            continue
        if path.suffix not in {".py", ".yaml", ".yml", ".json", ".md", ".txt"}:
            continue
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line_no, line in enumerate(text.splitlines(), start=1):
            for label, pattern, allow_tokens in _PATTERNS:
                match = pattern.search(line)
                if match is None:
                    continue
                if any(tok in line for tok in allow_tokens):
                    continue
                # Allow the public-safety scanner itself to enumerate the
                # tokens it flags.
                if path == Path(__file__):
                    continue
                raise AssertionError(
                    f"public-safety hit ({label}) at {path}:{line_no}: {line.strip()[:200]}"
                )
