"""Postgres connection factory for the repository layer.

Sources of truth:
  - docs/application-implementation-plan.md sections 5 and 8.
  - docs/schema-implementation-plan.md section 7.7 (Postgres 16, schema
    migrations runner) and section 8 (audit-event invariant).

The factory cross-checks the ``DEMO_DATA_ENVIRONMENT`` guard, sets a
per-session ``statement_timeout``, and returns a context-manager so the
caller can compose a single transaction across the domain write and the
audit-event insert.

``psycopg`` is imported lazily so unit tests can import the module without
having psycopg installed.  Phase 1 callers should not call the runtime
methods; they exist for Phase 2+.
"""

from __future__ import annotations

import json
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ConnectionParameters:
    """Connection parameters resolved from Secrets Manager + env vars."""

    host: str
    port: int
    user: str
    password: str
    dbname: str
    connect_timeout_s: float
    statement_timeout_ms: int
    application_name: str = "ao_radar_mcp"

    def to_psycopg_kwargs(self) -> dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "dbname": self.dbname,
            "connect_timeout": int(self.connect_timeout_s),
            "application_name": self.application_name,
        }


def fetch_secret(secret_arn: str) -> dict[str, Any]:
    """Fetch the JSON payload for ``secret_arn`` from AWS Secrets Manager.

    Lazy import of ``boto3`` so unit tests can import this module without
    boto3 installed.  Real Lambda runtime always has boto3 available.
    """

    import boto3  # noqa: WPS433 - intentional lazy import

    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_arn)
    secret_string = response.get("SecretString")
    if not secret_string:
        raise RuntimeError(f"Secrets Manager response for {secret_arn!r} has no SecretString")
    payload = json.loads(secret_string)
    if not isinstance(payload, dict):
        raise RuntimeError(f"Secrets Manager payload for {secret_arn!r} is not an object")
    return payload


def build_parameters(
    secret_payload: dict[str, Any],
    *,
    connect_timeout_s: float,
    statement_timeout_ms: int,
) -> ConnectionParameters:
    return ConnectionParameters(
        host=str(secret_payload["host"]),
        port=int(secret_payload.get("port", 5432)),
        user=str(secret_payload["username"]),
        password=str(secret_payload["password"]),
        dbname=str(secret_payload.get("dbname", "ao_radar")),
        connect_timeout_s=connect_timeout_s,
        statement_timeout_ms=statement_timeout_ms,
    )


class TransactionScope(AbstractContextManager["TransactionScope"]):
    """Lightweight context manager around a psycopg connection + transaction.

    Phase 2+ wires this to ``psycopg.connect``.  Phase 1 stub raises if the
    caller actually attempts to enter the context — tools should remain on
    ``not_implemented`` paths until Phase 2 lands.
    """

    def __init__(self, parameters: ConnectionParameters) -> None:
        self._parameters = parameters
        self._connection: Any | None = None

    def __enter__(self) -> "TransactionScope":
        try:
            import psycopg  # noqa: WPS433 - intentional lazy import
        except ImportError as exc:  # pragma: no cover - exercised at runtime
            raise RuntimeError(
                "psycopg is not installed; the repository layer is not "
                "available in this environment"
            ) from exc

        self._connection = psycopg.connect(**self._parameters.to_psycopg_kwargs())
        with self._connection.cursor() as cursor:
            cursor.execute(
                "SET LOCAL statement_timeout = %s",
                (str(self._parameters.statement_timeout_ms),),
            )
            cursor.execute(
                "SET LOCAL application_name = %s",
                (self._parameters.application_name,),
            )
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object,
    ) -> bool | None:
        if self._connection is None:
            return False
        if exc is None:
            self._connection.commit()
        else:
            self._connection.rollback()
        self._connection.close()
        self._connection = None
        return False  # propagate exceptions


__all__ = [
    "ConnectionParameters",
    "TransactionScope",
    "build_parameters",
    "fetch_secret",
]
