"""Schema-tier pytest fixtures.

This conftest is owned by the schema teammate (per
docs/claude-agent-teams-execution-plan.md).

It applies migrations once per test session against a Postgres 16 database
addressed by ``DATABASE_URL`` and provides a per-test connection that always
runs inside a transaction the test will roll back. The lead's
``tests/conftest.py`` already auto-skips ``db`` tests when ``DATABASE_URL`` is
unset.

The fixtures below also seed the minimum referential rows that schema tests
need (a synthetic traveler and voucher) into a single setup transaction that
each test inherits via ``BEGIN ... ROLLBACK``.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = REPO_ROOT / "ops" / "migrations"


def _maybe_psycopg() -> Any:
    try:
        import psycopg  # type: ignore[import-not-found]
    except ImportError:  # pragma: no cover - covered indirectly by collection skip
        return None
    return psycopg


@pytest.fixture(scope="session")
def _psycopg_module() -> Any:
    psycopg = _maybe_psycopg()
    if psycopg is None:
        pytest.skip("psycopg not installed; schema tests need it")
    return psycopg


@pytest.fixture(scope="session")
def _migrations_applied(database_url: str, _psycopg_module: Any) -> str:
    """Apply migrations once for the session; return the URL for chaining."""

    # Force the synthetic-only environment so the runner does not refuse.
    os.environ["DEMO_DATA_ENVIRONMENT"] = "synthetic_demo"

    # Local import: keeps the module out of the import graph for non-db tiers.
    from ops.scripts import run_migrations as runner

    runner.run(database_url=database_url, migrations_dir=MIGRATIONS_DIR)
    return database_url


@pytest.fixture
def postgres(
    _migrations_applied: str,
    _psycopg_module: Any,
) -> Iterator[Any]:
    """Yield a connection inside a transaction; ROLLBACK on test exit."""

    psycopg = _psycopg_module
    conn = psycopg.connect(_migrations_applied, autocommit=False)
    try:
        yield conn
    finally:
        try:
            conn.rollback()
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# Helpers shared by individual tests. They run inside the per-test transaction
# and produce deterministic synthetic IDs so the rolled-back state is clean.
# ---------------------------------------------------------------------------


@pytest.fixture
def synthetic_ids() -> dict[str, str]:
    nonce = uuid.uuid4().hex[:8]
    return {
        "traveler_id": f"T-TEST-{nonce}",
        "voucher_id": f"V-TEST-{nonce}",
        "line_item_id": f"LI-TEST-{nonce}",
        "evidence_ref_id": f"ER-TEST-{nonce}",
        "finding_id": f"F-TEST-{nonce}",
        "brief_id": f"BR-TEST-{nonce}",
        "event_id": f"EV-TEST-{nonce}",
        "signal_id": f"SIG-TEST-{nonce}",
        "missing_item_id": f"MI-TEST-{nonce}",
        "note_id": f"N-TEST-{nonce}",
    }


def insert_traveler(conn: Any, traveler_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO travelers (
                traveler_id, display_name, role_label, home_unit_label,
                typical_trip_pattern, prior_correction_summary, data_environment
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                traveler_id,
                f"Demo Traveler Test {traveler_id} (Synthetic Demo)",
                "staff_nco_demo",
                "1st Synthetic Logistics Detachment (Demo)",
                "test pattern",
                "none on file",
                "synthetic_demo",
            ),
        )


def insert_voucher(
    conn: Any,
    voucher_id: str,
    traveler_id: str,
    *,
    review_status: str = "needs_review",
    data_environment: str = "synthetic_demo",
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO vouchers (
                voucher_id, traveler_id, trip_purpose_category,
                trip_start_date, trip_end_date, declared_origin,
                declared_destinations, funding_reference_label,
                funding_reference_quality, justification_text,
                pre_existing_flags, demo_packet_submitted_at,
                review_status, data_environment
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s::jsonb, NOW(), %s, %s
            )
            """,
            (
                voucher_id,
                traveler_id,
                "tdy_conference_demo",
                "2026-04-01",
                "2026-04-05",
                "Demo Origin",
                '["Demo Destination"]',
                "LOA-DEMO-FY26-0001",
                "clean",
                "synthetic justification",
                "[]",
                review_status,
                data_environment,
            ),
        )


def insert_line_item(
    conn: Any,
    line_item_id: str,
    voucher_id: str,
    *,
    line_index: int = 1,
    currency_code: str = "USD",
    exchange_rate_to_usd: Any = None,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO voucher_line_items (
                line_item_id, voucher_id, line_index, expense_date,
                amount_minor_units, currency_code, exchange_rate_to_usd,
                category, vendor_label, payment_instrument_indicator,
                free_text_notes, claimed_by_traveler_at
            ) VALUES (
                %s, %s, %s, '2026-04-02', 10000, %s, %s,
                'lodging', 'Hotel Coastal Demo', 'gtcc_like_demo', '', NOW()
            )
            """,
            (line_item_id, voucher_id, line_index, currency_code, exchange_rate_to_usd),
        )
