"""Unit tests for the fraud-mock deterministic generator.

Source of truth: docs/application-implementation-plan.md section 9 and
docs/schema-implementation-plan.md section 5.7.
"""

from __future__ import annotations

import json
import os

import pytest

from ao_radar_fraud_mock.deterministic import generate_signals
from ao_radar_fraud_mock.handler import lambda_handler


@pytest.fixture(autouse=True)
def _set_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEMO_DATA_ENVIRONMENT", "synthetic_demo")
    monkeypatch.setenv("FRAUD_DETERMINISTIC_SEED", "ao-radar-test-seed")
    monkeypatch.setenv(
        "FRAUD_SIGNAL_SOURCE_LABEL", "synthetic_compliance_service_demo"
    )


def test_generate_signals_is_deterministic() -> None:
    a = generate_signals(
        "V-TEST-1003",
        seed="ao-radar-test-seed",
        source_label="synthetic_compliance_service_demo",
    )
    b = generate_signals(
        "V-TEST-1003",
        seed="ao-radar-test-seed",
        source_label="synthetic_compliance_service_demo",
    )
    assert tuple(s.signal_id for s in a) == tuple(s.signal_id for s in b)
    assert tuple(s.signal_key for s in a) == tuple(s.signal_key for s in b)


def test_signal_keys_are_unique_per_voucher() -> None:
    signals = generate_signals(
        "V-TEST-1003",
        seed="ao-radar-test-seed",
        source_label="synthetic_compliance_service_demo",
    )
    assert len({s.signal_key for s in signals}) == len(signals)
    for s in signals:
        assert s.signal_id == f"SIG-V-TEST-1003-{s.signal_key}"
        assert s.is_official_finding is False
        assert s.not_sufficient_for_adverse_action is True
        assert s.synthetic_source_label == "synthetic_compliance_service_demo"


def test_handler_returns_deterministic_response() -> None:
    request = {"voucher_id": "V-TEST-1003", "data_environment": "synthetic_demo"}
    response = lambda_handler(request, context=None)
    assert response["data_environment"] == "synthetic_demo"
    assert response["voucher_id"] == "V-TEST-1003"
    for signal in response["signals"]:
        assert signal["is_official_finding"] is False
        assert signal["not_sufficient_for_adverse_action"] is True


def test_handler_refuses_non_synthetic_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEMO_DATA_ENVIRONMENT", "prod")
    response = lambda_handler(
        {"voucher_id": "V-TEST-1003", "data_environment": "prod"}, context=None
    )
    assert response["errorType"] == "FraudMockRefusal"


def test_handler_refuses_request_without_synthetic_environment_field() -> None:
    response = lambda_handler(
        {"voucher_id": "V-TEST-1003", "data_environment": "prod"},
        context=None,
    )
    assert response["errorType"] == "FraudMockRefusal"


def test_handler_accepts_string_event() -> None:
    raw = json.dumps(
        {"voucher_id": "V-TEST-1003", "data_environment": "synthetic_demo"}
    )
    response = lambda_handler(raw, context=None)
    assert response["voucher_id"] == "V-TEST-1003"
