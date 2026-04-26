"""Traveler + prior-summary row builders.

Reads ``ops/seed/travelers.yaml`` and ``ops/seed/prior_summaries.yaml`` and
returns plain ``dict`` rows ready for insertion into ``travelers`` and
``prior_voucher_summaries``.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from ops.seed.constants import DATA_ENVIRONMENT
from ops.seed.generators.determinism import derive_id, derive_timestamp


def load_travelers(path: Path) -> list[dict[str, Any]]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not raw or "travelers" not in raw:
        raise ValueError(f"{path} missing 'travelers' top-level key")
    rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    # Anchor created_at on a deterministic FY26 base date.
    base = date(2025, 10, 1)
    for idx, entry in enumerate(raw["travelers"]):
        traveler_id = entry["traveler_id"]
        if traveler_id in seen_ids:
            raise ValueError(f"duplicate traveler_id {traveler_id} in {path}")
        seen_ids.add(traveler_id)
        rows.append(
            {
                "traveler_id": traveler_id,
                "display_name": entry["display_name"],
                "role_label": entry["role_label"],
                "home_unit_label": entry["home_unit_label"],
                "typical_trip_pattern": entry["typical_trip_pattern"],
                "prior_correction_summary": entry["prior_correction_summary"],
                "data_environment": DATA_ENVIRONMENT,
                "created_at": derive_timestamp(base, offset_minutes=idx).astimezone(timezone.utc),
            }
        )
    return rows


def load_prior_summaries(path: Path) -> list[dict[str, Any]]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not raw or "prior_summaries" not in raw:
        raise ValueError(f"{path} missing 'prior_summaries' top-level key")
    rows: list[dict[str, Any]] = []
    counter_per_traveler: dict[str, int] = {}
    base = date(2025, 10, 5)
    for entry in raw["prior_summaries"]:
        traveler_id = entry["traveler_id"]
        counter_per_traveler[traveler_id] = counter_per_traveler.get(traveler_id, 0) + 1
        ordinal = counter_per_traveler[traveler_id]
        prior_summary_id = (
            f"PRIOR-{traveler_id}-{ordinal:02d}-{derive_id('prior', traveler_id, str(ordinal))[:8]}"
        )
        rows.append(
            {
                "prior_summary_id": prior_summary_id,
                "traveler_id": traveler_id,
                "period_label": entry["period_label"],
                "summary_text": entry["summary_text"],
                "recurring_correction_pattern": entry.get("recurring_correction_pattern"),
                "created_at": derive_timestamp(base, offset_minutes=len(rows)).astimezone(
                    timezone.utc
                ),
            }
        )
    return rows


__all__ = ["load_travelers", "load_prior_summaries"]
