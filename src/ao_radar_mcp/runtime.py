"""Runtime helpers shared by DB-backed tool handlers.

Sources of truth:
  - docs/application-implementation-plan.md sections 5 and 8.
  - docs/schema-implementation-plan.md section 8 (audit-event invariant).

Lazy imports of ``boto3`` and ``psycopg`` keep the test tier importable
without optional runtime deps.  The deployed Lambda has both available.
"""

from __future__ import annotations

import json
import os
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

_DB_URL_LOCK = threading.Lock()
_CACHED_DB_URL: str | None = None
_CACHED_SECRET_ARN: str | None = None


def get_secret_arn() -> str | None:
    arn = os.environ.get("DB_SECRET_ARN", "").strip()
    return arn or None


def is_db_available() -> bool:
    """Return ``True`` when DB connection params can be resolved at runtime."""

    return get_secret_arn() is not None


def reset_caches_for_tests() -> None:
    """Clear any cached secret payload (used by tests that swap DB env)."""

    global _CACHED_DB_URL, _CACHED_SECRET_ARN
    with _DB_URL_LOCK:
        _CACHED_DB_URL = None
        _CACHED_SECRET_ARN = None


def _resolve_db_url(secret_arn: str) -> str:
    global _CACHED_DB_URL, _CACHED_SECRET_ARN
    with _DB_URL_LOCK:
        if _CACHED_DB_URL is not None and _CACHED_SECRET_ARN == secret_arn:
            return _CACHED_DB_URL

        import boto3  # noqa: WPS433 - lazy import

        client = boto3.client("secretsmanager")
        response = client.get_secret_value(SecretId=secret_arn)
        secret_string = response.get("SecretString")
        if not secret_string:
            raise RuntimeError(f"secret {secret_arn!r} has no SecretString")
        payload = json.loads(secret_string)
        if not isinstance(payload, dict):
            raise RuntimeError(f"secret {secret_arn!r} payload is not an object")

        if "url" in payload and isinstance(payload["url"], str):
            url = payload["url"]
        else:
            host = payload["host"]
            port = payload.get("port", 5432)
            user = payload["username"]
            password = payload["password"]
            dbname = payload.get("dbname") or payload.get("database") or "ao_radar"
            url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"

        _CACHED_DB_URL = url
        _CACHED_SECRET_ARN = secret_arn
        return url


def _statement_timeout_ms() -> int:
    raw = os.environ.get("DB_STATEMENT_TIMEOUT_MS", "15000").strip()
    try:
        return max(1000, int(raw))
    except ValueError:
        return 15000


def _connect_timeout_s() -> int:
    raw = os.environ.get("DB_CONNECT_TIMEOUT_S", "5").strip()
    try:
        return max(1, int(float(raw)))
    except ValueError:
        return 5


@contextmanager
def transaction() -> Iterator[Any]:
    """Yield a psycopg connection inside a single transaction.

    Commits on clean exit, rolls back on exception, always closes.  Sets
    ``statement_timeout`` and ``application_name`` for the session.
    """

    secret_arn = get_secret_arn()
    if secret_arn is None:
        raise RuntimeError("DB_SECRET_ARN is not set; runtime DB is unavailable")

    url = _resolve_db_url(secret_arn)

    import psycopg  # noqa: WPS433 - lazy import

    connection = psycopg.connect(url, connect_timeout=_connect_timeout_s())
    try:
        # Postgres ``SET`` does not accept parameter binds, so configure these
        # session-level knobs through ``set_config`` (which does).  Both values
        # are server-controlled (env vars / hardcoded), not user input.
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT set_config('application_name', %s, false)",
                ("ao_radar_mcp",),
            )
            cursor.execute(
                "SELECT set_config('statement_timeout', %s, false)",
                (str(_statement_timeout_ms()),),
            )
        try:
            yield connection
        except Exception:
            connection.rollback()
            raise
        else:
            connection.commit()
    finally:
        connection.close()


__all__ = [
    "get_secret_arn",
    "is_db_available",
    "reset_caches_for_tests",
    "transaction",
]
