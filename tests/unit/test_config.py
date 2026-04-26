"""Unit tests for ``ao_radar_mcp.config``.

Source of truth: docs/application-implementation-plan.md section 5.
"""

from __future__ import annotations

import pytest

from ao_radar_mcp.config import (
    ALLOWED_DATA_ENVIRONMENT,
    ConfigurationError,
    load,
)


_BASE_PHASE_1: dict[str, str] = {
    "LOG_LEVEL": "INFO",
    "MCP_SERVER_NAME": "ao-radar-mcp",
    "MCP_SERVER_VERSION": "0.1.0",
    "DEMO_DATA_ENVIRONMENT": ALLOWED_DATA_ENVIRONMENT,
}


def test_phase_1_loads_with_minimum_env() -> None:
    config = load(phase=1, env=dict(_BASE_PHASE_1))
    assert config.log_level == "INFO"
    assert config.mcp_server_name == "ao-radar-mcp"
    assert config.mcp_server_version == "0.1.0"
    assert config.data_environment == "synthetic_demo"
    assert config.db_secret_arn is None
    assert config.fraud_function_name is None
    assert config.phase == 1


def test_phase_1_rejects_non_synthetic_environment() -> None:
    bad_env = dict(_BASE_PHASE_1, DEMO_DATA_ENVIRONMENT="prod")
    with pytest.raises(ConfigurationError, match="DEMO_DATA_ENVIRONMENT"):
        load(phase=1, env=bad_env)


def test_phase_1_rejects_missing_required_var() -> None:
    bad_env = dict(_BASE_PHASE_1)
    del bad_env["MCP_SERVER_NAME"]
    with pytest.raises(ConfigurationError, match="MCP_SERVER_NAME"):
        load(phase=1, env=bad_env)


def test_phase_2_requires_db_vars() -> None:
    with pytest.raises(ConfigurationError, match="DB_SECRET_ARN"):
        load(phase=2, env=dict(_BASE_PHASE_1))


def test_phase_2_loads_when_db_vars_present() -> None:
    env = dict(
        _BASE_PHASE_1,
        DB_SECRET_ARN="arn:aws:secretsmanager:us-east-1:000000000000:secret:demo",
        DB_CONNECT_TIMEOUT_S="5",
        DB_STATEMENT_TIMEOUT_MS="15000",
    )
    config = load(phase=2, env=env)
    assert config.db_secret_arn.startswith("arn:aws:secretsmanager:")
    assert config.db_connect_timeout_s == 5.0
    assert config.db_statement_timeout_ms == 15000


def test_phase_3_requires_fraud_vars() -> None:
    env = dict(
        _BASE_PHASE_1,
        DB_SECRET_ARN="arn:aws:secretsmanager:us-east-1:000000000000:secret:demo",
        DB_CONNECT_TIMEOUT_S="5",
        DB_STATEMENT_TIMEOUT_MS="15000",
    )
    with pytest.raises(ConfigurationError, match="FRAUD_FUNCTION_NAME"):
        load(phase=3, env=env)


def test_boundary_override_must_pass_validator() -> None:
    bad_override = "AO Radar approves everything."
    env = dict(_BASE_PHASE_1, BOUNDARY_REMINDER_TEXT=bad_override)
    with pytest.raises(ValueError, match="missing required clauses"):
        load(phase=1, env=env)


def test_boundary_override_canonical_passes() -> None:
    canonical = (
        "AO Radar is a synthetic pre-decision review aid. It does not approve, "
        "deny, certify, return, cancel, amend, submit, determine entitlement, "
        "determine payability, accuse fraud, or contact external parties. The "
        "human Approving Official remains accountable for every official action "
        "in the official travel system."
    )
    env = dict(_BASE_PHASE_1, BOUNDARY_REMINDER_TEXT=canonical)
    config = load(phase=1, env=env)
    assert config.boundary_reminder_text == canonical


def test_phase_2_rejects_bad_numeric_env() -> None:
    env = dict(
        _BASE_PHASE_1,
        DB_SECRET_ARN="arn",
        DB_CONNECT_TIMEOUT_S="not-a-number",
        DB_STATEMENT_TIMEOUT_MS="15000",
    )
    with pytest.raises(ConfigurationError, match="DB_CONNECT_TIMEOUT_S"):
        load(phase=2, env=env)
