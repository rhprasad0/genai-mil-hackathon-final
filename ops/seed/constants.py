"""Constants shared across the seed package.

The canonical human-authority boundary text and the blocked-status set are
imported from the application's safety package so the wording cannot drift.
The validators in ``ops/seed/validators/`` re-export these via thin wrappers;
this module exists to keep import order obvious.
"""

from __future__ import annotations

from typing import Final

from ao_radar_mcp.safety.authority_boundary import HUMAN_AUTHORITY_BOUNDARY_TEXT
from ao_radar_mcp.safety.controlled_status import (
    ALLOWED_FINDING_REVIEW_STATES,
    ALLOWED_VOUCHER_REVIEW_STATUSES,
    BLOCKED_STATUS_VALUES,
)

# Deterministic seed value used by every helper in ``generators/determinism.py``.
DETERMINISTIC_SEED: Final[str] = "ao-radar-synthetic-v1"

# Synthetic identity conventions (synthetic-data plan section 8).
DATA_ENVIRONMENT: Final[str] = "synthetic_demo"
SYNTHETIC_SOURCE_LABEL: Final[str] = "synthetic_compliance_service_demo"
DEMO_AO_ACTOR_LABEL: Final[str] = "demo_ao_user_1"
SYSTEM_SEED_ACTOR_LABEL: Final[str] = "synthetic_demo_seed"
LOA_PREFIX: Final[str] = "LOA-DEMO-FY26-"
LOA_AMBIGUOUS_SENTINEL: Final[str] = "FUND-POT-DEMO-AMBIG"
LOA_AMBIGUOUS_DASHED: Final[str] = "LOA-DEMO-FY26-???"

# Citation source-identifier prefixes (schema plan section 5.6).
CITATION_SOURCE_DTMO_DEMO: Final[str] = "synthetic_dtmo_checklist_demo_v1"
CITATION_SOURCE_GENERIC_DEMO: Final[str] = "synthetic_demo_reference_v1"

# Canonical seeded IDs for the reset path (synthetic-data plan section 11).
TRAVELER_IDS: Final[tuple[str, ...]] = ("T-101", "T-102", "T-103", "T-104", "T-105")
VOUCHER_IDS: Final[tuple[str, ...]] = (
    "V-1001",
    "V-1002",
    "V-1003",
    "V-1004",
    "V-1005",
    "V-1006",
    "V-1007",
    "V-1008",
    "V-1009",
    "V-1010",
    "V-1011",
    "V-1012",
)

# FY26 window used to anchor every card date.
FY26_START: Final[str] = "2025-10-01"
FY26_END: Final[str] = "2026-09-30"


__all__ = [
    "HUMAN_AUTHORITY_BOUNDARY_TEXT",
    "BLOCKED_STATUS_VALUES",
    "ALLOWED_VOUCHER_REVIEW_STATUSES",
    "ALLOWED_FINDING_REVIEW_STATES",
    "DETERMINISTIC_SEED",
    "DATA_ENVIRONMENT",
    "SYNTHETIC_SOURCE_LABEL",
    "DEMO_AO_ACTOR_LABEL",
    "SYSTEM_SEED_ACTOR_LABEL",
    "LOA_PREFIX",
    "LOA_AMBIGUOUS_SENTINEL",
    "LOA_AMBIGUOUS_DASHED",
    "CITATION_SOURCE_DTMO_DEMO",
    "CITATION_SOURCE_GENERIC_DEMO",
    "TRAVELER_IDS",
    "VOUCHER_IDS",
    "FY26_START",
    "FY26_END",
]
