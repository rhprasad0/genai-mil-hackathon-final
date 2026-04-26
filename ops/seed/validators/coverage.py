"""Coverage-map validator.

Walks ``ops/seed/coverage_map.yaml`` and asserts every required practitioner
case resolves to >=1 voucher with >=1 finding, >=1 packet_evidence_pointer
(satisfied automatically because every finding row has one), and either a
resolvable ``primary_citation_id`` or an explicit ``needs_human_review = true``
reason.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class CoverageError(ValueError):
    pass


def validate_corpus(corpus: Any, coverage_map_path: Path) -> None:
    raw = yaml.safe_load(coverage_map_path.read_text(encoding="utf-8"))
    if not raw or "coverage" not in raw:
        raise CoverageError(f"{coverage_map_path} missing 'coverage' top-level key")

    citation_ids = {c["citation_id"] for c in corpus.policy_citations}
    findings_by_voucher: dict[str, list[dict[str, Any]]] = {}
    for f in corpus.story_findings:
        findings_by_voucher.setdefault(f["voucher_id"], []).append(f)

    for entry in raw["coverage"]:
        case = entry["case"]
        vouchers = entry.get("vouchers", [])
        if not vouchers:
            raise CoverageError(f"coverage case {case!r} has no vouchers listed")
        resolved = False
        for voucher_id in vouchers:
            findings = findings_by_voucher.get(voucher_id, [])
            if not findings:
                continue
            for f in findings:
                pointer = f.get("packet_evidence_pointer") or {}
                has_pointer = bool(pointer.get("line_item_id") or pointer.get("evidence_ref_id"))
                if not has_pointer:
                    continue
                cite = f.get("primary_citation_id")
                if cite and cite in citation_ids:
                    resolved = True
                    break
                if f.get("needs_human_review"):
                    resolved = True
                    break
            if resolved:
                break
        if not resolved:
            raise CoverageError(
                f"coverage case {case!r} not resolved by any of vouchers={vouchers}: "
                f"need >=1 finding with provenance pointer plus citation OR "
                f"needs_human_review=True"
            )


__all__ = ["CoverageError", "validate_corpus"]
