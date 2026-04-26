"""Policy-citation row builder."""

from __future__ import annotations

from datetime import date, timezone
from pathlib import Path
from typing import Any

import yaml

from ops.seed.generators.determinism import derive_timestamp


def load_citations(path: Path) -> list[dict[str, Any]]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not raw or "citations" not in raw:
        raise ValueError(f"{path} missing 'citations' top-level key")
    rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    base = date(2025, 10, 1)
    for idx, entry in enumerate(raw["citations"]):
        cid = entry["citation_id"]
        if cid in seen_ids:
            raise ValueError(f"duplicate citation_id {cid} in {path}")
        seen_ids.add(cid)
        rows.append(
            {
                "citation_id": cid,
                "source_identifier": entry["source_identifier"],
                "topic": entry["topic"],
                "excerpt_text": entry["excerpt_text"],
                "retrieval_anchor": entry["retrieval_anchor"],
                "applicability_note": entry["applicability_note"],
                "created_at": derive_timestamp(base, offset_minutes=idx).astimezone(timezone.utc),
            }
        )
    return rows


__all__ = ["load_citations"]
