"""Synthetic-marker validator.

Mirrors synthetic-data plan section 13:
- every display_name has '(Synthetic Demo)' or 'DEMO-'
- every vendor_label and vendor_label_on_evidence contains 'Demo'
- every home_unit_label contains 'Demo'
- every funding_reference_label matches LOA-DEMO-FY26-#### or the
  FUND-POT-DEMO-AMBIG sentinel
- every traveler/voucher row has data_environment = synthetic_demo
"""

from __future__ import annotations

import re
from typing import Any

from ops.seed.constants import (
    DATA_ENVIRONMENT,
    LOA_AMBIGUOUS_DASHED,
    LOA_AMBIGUOUS_SENTINEL,
    LOA_PREFIX,
)


_LOA_RE = re.compile(r"^LOA-DEMO-FY26-\d{4}$")


class SyntheticMarkerError(ValueError):
    pass


def validate_travelers(travelers: list[dict[str, Any]]) -> None:
    for row in travelers:
        name = row.get("display_name", "")
        if "(Synthetic Demo)" not in name and not name.startswith("DEMO-"):
            raise SyntheticMarkerError(
                f"travelers.display_name={name!r} missing synthetic marker"
            )
        if "Demo" not in row.get("home_unit_label", ""):
            raise SyntheticMarkerError(
                f"travelers.home_unit_label={row.get('home_unit_label')!r} missing 'Demo'"
            )
        if row.get("data_environment") != DATA_ENVIRONMENT:
            raise SyntheticMarkerError(
                f"travelers row data_environment must equal {DATA_ENVIRONMENT}"
            )


def validate_vouchers(vouchers: list[dict[str, Any]]) -> None:
    for row in vouchers:
        if row.get("data_environment") != DATA_ENVIRONMENT:
            raise SyntheticMarkerError(
                f"vouchers row data_environment must equal {DATA_ENVIRONMENT}"
            )
        loa = row.get("funding_reference_label", "")
        if loa == LOA_AMBIGUOUS_SENTINEL or loa == LOA_AMBIGUOUS_DASHED:
            continue
        if not _LOA_RE.match(loa):
            raise SyntheticMarkerError(
                f"vouchers.funding_reference_label={loa!r} not matching {LOA_PREFIX}#### "
                f"or {LOA_AMBIGUOUS_SENTINEL}"
            )
        # Each declared destination should be Demo-marked.
        for dest in row.get("declared_destinations", []):
            if "Demo" not in dest:
                raise SyntheticMarkerError(
                    f"vouchers.declared_destinations entry {dest!r} missing 'Demo' marker"
                )
        if "Demo" not in row.get("declared_origin", ""):
            raise SyntheticMarkerError(
                f"vouchers.declared_origin={row.get('declared_origin')!r} missing 'Demo' marker"
            )


def validate_line_items(line_items: list[dict[str, Any]]) -> None:
    for row in line_items:
        if "Demo" not in row.get("vendor_label", ""):
            raise SyntheticMarkerError(
                f"voucher_line_items.vendor_label={row.get('vendor_label')!r} missing 'Demo'"
            )


def validate_evidence(evidence: list[dict[str, Any]]) -> None:
    for row in evidence:
        label = row.get("vendor_label_on_evidence")
        if label is not None and "Demo" not in label:
            raise SyntheticMarkerError(
                f"evidence_refs.vendor_label_on_evidence={label!r} missing 'Demo'"
            )


def validate_corpus(corpus: Any) -> None:
    validate_travelers(corpus.travelers)
    validate_vouchers(corpus.vouchers)
    validate_line_items(corpus.voucher_line_items)
    validate_evidence(corpus.evidence_refs)


__all__ = [
    "SyntheticMarkerError",
    "validate_corpus",
    "validate_travelers",
    "validate_vouchers",
    "validate_line_items",
    "validate_evidence",
]
