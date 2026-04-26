"""Environment-variable configuration loader.

Sources of truth:
  - docs/application-implementation-plan.md section 5 (env var matrix).
  - docs/application-implementation-plan.md section 12 (phased env vars).
  - docs/spec.md section 4.4.1 (canonical boundary reminder).

This module never logs secret values.  Every getter validates the variables
required for the active *phase* of the rollout:

  - Phase 1 (stub MCP): LOG_LEVEL, MCP_SERVER_NAME, MCP_SERVER_VERSION,
    DEMO_DATA_ENVIRONMENT.
  - Phase 2 (DB attached): + DB_SECRET_ARN, DB_CONNECT_TIMEOUT_S,
    DB_STATEMENT_TIMEOUT_MS.
  - Phase 3 (fraud mock attached): + FRAUD_FUNCTION_NAME,
    FRAUD_INVOKE_TIMEOUT_S.

Calling ``load(phase=1)`` returns a frozen ``AppConfig``.  Higher phases do
not break Phase 1 callers; they merely require additional variables.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Final

from .safety.authority_boundary import (
    HUMAN_AUTHORITY_BOUNDARY_TEXT,
    assert_boundary_text,
)


REQUIRED_PHASE_1: Final[tuple[str, ...]] = (
    "LOG_LEVEL",
    "MCP_SERVER_NAME",
    "MCP_SERVER_VERSION",
    "DEMO_DATA_ENVIRONMENT",
)

REQUIRED_PHASE_2: Final[tuple[str, ...]] = REQUIRED_PHASE_1 + (
    "DB_SECRET_ARN",
    "DB_CONNECT_TIMEOUT_S",
    "DB_STATEMENT_TIMEOUT_MS",
)

REQUIRED_PHASE_3: Final[tuple[str, ...]] = REQUIRED_PHASE_2 + (
    "FRAUD_FUNCTION_NAME",
    "FRAUD_INVOKE_TIMEOUT_S",
)

ALLOWED_DATA_ENVIRONMENT: Final[str] = "synthetic_demo"


class ConfigurationError(RuntimeError):
    """Raised at startup when env vars are missing or invalid."""


@dataclass(frozen=True)
class AppConfig:
    """Frozen runtime configuration for the MCP Lambda."""

    log_level: str
    mcp_server_name: str
    mcp_server_version: str
    data_environment: str
    boundary_reminder_text: str
    db_secret_arn: str | None = None
    db_connect_timeout_s: float | None = None
    db_statement_timeout_ms: int | None = None
    fraud_function_name: str | None = None
    fraud_invoke_timeout_s: float | None = None
    phase: int = 1
    extras: dict[str, str] = field(default_factory=dict)


def _missing(env: dict[str, str], required: tuple[str, ...]) -> list[str]:
    return [name for name in required if not env.get(name, "").strip()]


def _required_for_phase(phase: int) -> tuple[str, ...]:
    if phase == 1:
        return REQUIRED_PHASE_1
    if phase == 2:
        return REQUIRED_PHASE_2
    if phase == 3:
        return REQUIRED_PHASE_3
    raise ConfigurationError(f"unknown phase: {phase!r}")


def _coerce_float(name: str, value: str) -> float:
    try:
        return float(value)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be a number, got {value!r}") from exc


def _coerce_int(name: str, value: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be an integer, got {value!r}") from exc


def load(
    *,
    phase: int = 1,
    env: dict[str, str] | None = None,
) -> AppConfig:
    """Load the configuration for the active phase.

    ``env`` defaults to ``os.environ`` so tests can pass an explicit dict.
    Raises ``ConfigurationError`` if any required variable is missing or
    malformed.  Never logs the values.
    """

    raw_env: dict[str, str] = dict(env if env is not None else os.environ)

    required = _required_for_phase(phase)
    missing = _missing(raw_env, required)
    if missing:
        raise ConfigurationError(
            "missing required environment variables for phase "
            f"{phase}: {', '.join(sorted(missing))}"
        )

    data_env = raw_env["DEMO_DATA_ENVIRONMENT"].strip()
    if data_env != ALLOWED_DATA_ENVIRONMENT:
        raise ConfigurationError(
            f"DEMO_DATA_ENVIRONMENT must equal {ALLOWED_DATA_ENVIRONMENT!r}; got {data_env!r}"
        )

    override = raw_env.get("BOUNDARY_REMINDER_TEXT", "").strip()
    if override:
        boundary_reminder = assert_boundary_text(override)
    else:
        boundary_reminder = HUMAN_AUTHORITY_BOUNDARY_TEXT

    db_secret_arn: str | None = None
    db_connect_timeout: float | None = None
    db_statement_timeout: int | None = None
    if phase >= 2:
        db_secret_arn = raw_env["DB_SECRET_ARN"].strip()
        db_connect_timeout = _coerce_float(
            "DB_CONNECT_TIMEOUT_S", raw_env["DB_CONNECT_TIMEOUT_S"].strip()
        )
        db_statement_timeout = _coerce_int(
            "DB_STATEMENT_TIMEOUT_MS", raw_env["DB_STATEMENT_TIMEOUT_MS"].strip()
        )

    fraud_function: str | None = None
    fraud_invoke_timeout: float | None = None
    if phase >= 3:
        fraud_function = raw_env["FRAUD_FUNCTION_NAME"].strip()
        fraud_invoke_timeout = _coerce_float(
            "FRAUD_INVOKE_TIMEOUT_S", raw_env["FRAUD_INVOKE_TIMEOUT_S"].strip()
        )

    return AppConfig(
        log_level=raw_env["LOG_LEVEL"].strip().upper(),
        mcp_server_name=raw_env["MCP_SERVER_NAME"].strip(),
        mcp_server_version=raw_env["MCP_SERVER_VERSION"].strip(),
        data_environment=data_env,
        boundary_reminder_text=boundary_reminder,
        db_secret_arn=db_secret_arn,
        db_connect_timeout_s=db_connect_timeout,
        db_statement_timeout_ms=db_statement_timeout,
        fraud_function_name=fraud_function,
        fraud_invoke_timeout_s=fraud_invoke_timeout,
        phase=phase,
        extras={},
    )


__all__ = [
    "ALLOWED_DATA_ENVIRONMENT",
    "AppConfig",
    "ConfigurationError",
    "REQUIRED_PHASE_1",
    "REQUIRED_PHASE_2",
    "REQUIRED_PHASE_3",
    "load",
]
