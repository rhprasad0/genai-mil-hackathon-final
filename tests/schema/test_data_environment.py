"""Tests that ``data_environment = synthetic_demo`` is enforced.

Schema plan section 5.1 / 5.2 / 6.4 require this CHECK on ``travelers`` and
``vouchers``. Any other value (production, staging, real, etc.) must be
rejected.

``pytest.raises(Exception)`` is used because the CHECK rejects via psycopg's
CheckViolation; we care that the DB rejects rather than which class fires.
"""

# ruff: noqa: B017

from __future__ import annotations

from typing import Any

import pytest

from tests.schema.conftest import insert_traveler, insert_voucher

NON_SYNTHETIC_VALUES = (
    "production",
    "staging",
    "real",
    "live",
    "demo",  # missing the synthetic_ prefix
    "synthetic",  # close but not the canonical token
    "",
    "SYNTHETIC_DEMO",  # case-sensitive
)


@pytest.mark.db
class TestTravelersDataEnvironment:
    @pytest.mark.parametrize("bad_value", NON_SYNTHETIC_VALUES)
    def test_non_synthetic_rejected_on_insert(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
        bad_value: str,
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        with pytest.raises(Exception):
            with postgres.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO travelers (
                        traveler_id, display_name, role_label, home_unit_label,
                        typical_trip_pattern, prior_correction_summary,
                        data_environment
                    ) VALUES (%s, %s, 'staff_nco_demo', 'unit (Demo)',
                              'pattern', 'summary', %s)
                    """,
                    (
                        traveler_id,
                        f"Demo Traveler {traveler_id} (Synthetic Demo)",
                        bad_value,
                    ),
                )

    def test_synthetic_demo_accepted(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        insert_traveler(postgres, traveler_id)
        with postgres.cursor() as cur:
            cur.execute(
                "SELECT data_environment FROM travelers WHERE traveler_id = %s",
                (traveler_id,),
            )
            row = cur.fetchone()
            assert row is not None
            assert row[0] == "synthetic_demo"


@pytest.mark.db
class TestVouchersDataEnvironment:
    @pytest.mark.parametrize("bad_value", NON_SYNTHETIC_VALUES)
    def test_non_synthetic_rejected_on_insert(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
        bad_value: str,
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        voucher_id = synthetic_ids["voucher_id"]
        insert_traveler(postgres, traveler_id)
        with pytest.raises(Exception):
            insert_voucher(
                postgres,
                voucher_id,
                traveler_id,
                data_environment=bad_value,
            )

    @pytest.mark.parametrize("bad_value", NON_SYNTHETIC_VALUES)
    def test_non_synthetic_rejected_on_update(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
        bad_value: str,
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        voucher_id = synthetic_ids["voucher_id"]
        insert_traveler(postgres, traveler_id)
        insert_voucher(postgres, voucher_id, traveler_id)
        with pytest.raises(Exception):
            with postgres.cursor() as cur:
                cur.execute(
                    "UPDATE vouchers SET data_environment = %s WHERE voucher_id = %s",
                    (bad_value, voucher_id),
                )

    def test_synthetic_demo_accepted(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        voucher_id = synthetic_ids["voucher_id"]
        insert_traveler(postgres, traveler_id)
        insert_voucher(postgres, voucher_id, traveler_id)
        with postgres.cursor() as cur:
            cur.execute(
                "SELECT data_environment FROM vouchers WHERE voucher_id = %s",
                (voucher_id,),
            )
            row = cur.fetchone()
            assert row is not None
            assert row[0] == "synthetic_demo"
