"""Tests for ``external_anomaly_signals`` constraints.

Schema plan section 5.7 requires:

* ``is_official_finding = false`` always.
* ``not_sufficient_for_adverse_action = true`` always.
* ``(voucher_id, signal_key)`` unique.

These constraints make the spec's ``not an official finding, not sufficient
for adverse action`` framing un-bypass-able at the schema level.

``pytest.raises(Exception)`` is intentional; CHECK / UniqueViolation can fire
depending on the row.
"""

# ruff: noqa: B017

from __future__ import annotations

from typing import Any

import pytest

from tests.schema.conftest import insert_traveler, insert_voucher


def _insert_signal(
    conn: Any,
    *,
    signal_id: str,
    voucher_id: str,
    signal_key: str = "duplicate_payment_risk:lodging_overlap_1",
    is_official_finding: bool = False,
    not_sufficient_for_adverse_action: bool = True,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO external_anomaly_signals (
                signal_id, voucher_id, signal_key, signal_type,
                synthetic_source_label, rationale_text, confidence,
                is_official_finding, not_sufficient_for_adverse_action
            ) VALUES (
                %s, %s, %s, 'duplicate_payment_risk',
                'synthetic_compliance_service_demo',
                'demo rationale', 'medium', %s, %s
            )
            """,
            (
                signal_id,
                voucher_id,
                signal_key,
                is_official_finding,
                not_sufficient_for_adverse_action,
            ),
        )


@pytest.mark.db
class TestExternalSignalConstraints:
    def test_is_official_finding_true_rejected(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        voucher_id = synthetic_ids["voucher_id"]
        signal_id = synthetic_ids["signal_id"]
        insert_traveler(postgres, traveler_id)
        insert_voucher(postgres, voucher_id, traveler_id)
        with pytest.raises(Exception):
            _insert_signal(
                postgres,
                signal_id=signal_id,
                voucher_id=voucher_id,
                is_official_finding=True,
            )

    def test_not_sufficient_false_rejected(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        voucher_id = synthetic_ids["voucher_id"]
        signal_id = synthetic_ids["signal_id"]
        insert_traveler(postgres, traveler_id)
        insert_voucher(postgres, voucher_id, traveler_id)
        with pytest.raises(Exception):
            _insert_signal(
                postgres,
                signal_id=signal_id,
                voucher_id=voucher_id,
                not_sufficient_for_adverse_action=False,
            )

    def test_unique_voucher_signal_key(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        voucher_id = synthetic_ids["voucher_id"]
        insert_traveler(postgres, traveler_id)
        insert_voucher(postgres, voucher_id, traveler_id)

        _insert_signal(
            postgres,
            signal_id=synthetic_ids["signal_id"] + "-A",
            voucher_id=voucher_id,
            signal_key="duplicate_payment_risk:lodging_overlap_1",
        )
        with pytest.raises(Exception):
            _insert_signal(
                postgres,
                signal_id=synthetic_ids["signal_id"] + "-B",
                voucher_id=voucher_id,
                signal_key="duplicate_payment_risk:lodging_overlap_1",
            )

    def test_default_values(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        voucher_id = synthetic_ids["voucher_id"]
        signal_id = synthetic_ids["signal_id"]
        insert_traveler(postgres, traveler_id)
        insert_voucher(postgres, voucher_id, traveler_id)
        _insert_signal(postgres, signal_id=signal_id, voucher_id=voucher_id)
        with postgres.cursor() as cur:
            cur.execute(
                """
                SELECT is_official_finding, not_sufficient_for_adverse_action
                FROM external_anomaly_signals WHERE signal_id = %s
                """,
                (signal_id,),
            )
            row = cur.fetchone()
            assert row is not None
            assert row[0] is False
            assert row[1] is True
