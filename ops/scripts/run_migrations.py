"""Idempotent migration runner for AO Radar (Postgres 16).

Implements docs/schema-implementation-plan.md section 7.7 and the application
plan handoff in section 12 of docs/application-implementation-plan.md.

Connection sources, in order of precedence:

1. ``DATABASE_URL`` (libpq URI) for the developer/test path.
2. ``DB_SECRET_ARN`` resolved via AWS Secrets Manager for the deployed
   ``db_ops`` Lambda path.

The runner refuses unless ``DEMO_DATA_ENVIRONMENT == 'synthetic_demo'``. Both
``boto3`` and ``psycopg`` are lazily imported so this module imports cleanly in
test tiers that do not have either dependency.

Usage::

    DEMO_DATA_ENVIRONMENT=synthetic_demo \\
    DATABASE_URL=postgresql://... \\
    python -m ops.scripts.run_migrations [--dry-run]

The ``--dry-run`` flag scans ``ops/migrations/*.sql`` and prints which files
would be applied without opening a database transaction. The deployed db_ops
Lambda Phase 2 probe uses this flag to verify connectivity and migration
discovery without changing schema state.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger("ao_radar.run_migrations")

REQUIRED_DATA_ENVIRONMENT = "synthetic_demo"
SCHEMA_MIGRATIONS_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    filename    TEXT PRIMARY KEY,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


@dataclass(frozen=True)
class MigrationFile:
    """A migration file on disk."""

    filename: str
    path: Path

    @property
    def sql(self) -> str:
        return self.path.read_text(encoding="utf-8")


@dataclass(frozen=True)
class RunResult:
    """Outcome summary returned to callers (db_ops Lambda + tests)."""

    applied: tuple[str, ...]
    skipped_already_applied: tuple[str, ...]
    discovered: tuple[str, ...]
    dry_run: bool


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


def _migrations_dir(override: Path | None = None) -> Path:
    if override is not None:
        return override
    # ops/scripts/run_migrations.py -> ops/scripts -> ops
    here = Path(__file__).resolve().parent
    candidate = here.parent / "migrations"
    if candidate.is_dir():
        return candidate
    raise FileNotFoundError(
        f"migrations directory not found at expected path {candidate}"
    )


def _discover_migration_files(migrations_dir: Path) -> list[MigrationFile]:
    """Return every ``*.sql`` file under ``migrations_dir`` in lexicographic order."""

    files = sorted(p for p in migrations_dir.glob("*.sql") if p.is_file())
    return [MigrationFile(filename=p.name, path=p) for p in files]


def _check_data_environment() -> None:
    value = os.environ.get("DEMO_DATA_ENVIRONMENT", "")
    if value != REQUIRED_DATA_ENVIRONMENT:
        raise RuntimeError(
            "DEMO_DATA_ENVIRONMENT must equal "
            f"'{REQUIRED_DATA_ENVIRONMENT}' to run migrations; got '{value}'"
        )


def _resolve_database_url() -> str:
    """Return a Postgres URI from ``DATABASE_URL`` or ``DB_SECRET_ARN``."""

    direct = os.environ.get("DATABASE_URL")
    if direct:
        return direct

    secret_arn = os.environ.get("DB_SECRET_ARN")
    if not secret_arn:
        raise RuntimeError(
            "neither DATABASE_URL nor DB_SECRET_ARN is set; cannot connect"
        )

    # Lazy import: keeps boto3 out of the test tier.
    try:
        import boto3  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "DB_SECRET_ARN is set but boto3 is not available in this environment"
        ) from exc

    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_arn)
    secret_string = response.get("SecretString")
    if not secret_string:
        raise RuntimeError(f"secret {secret_arn} has no SecretString payload")

    try:
        payload = json.loads(secret_string)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"secret {secret_arn} is not valid JSON; expected libpq fields"
        ) from exc

    return _libpq_url_from_secret(payload)


def _libpq_url_from_secret(payload: dict[str, Any]) -> str:
    """Build a libpq URI from a Secrets Manager JSON payload.

    Supports the AWS RDS-managed master-secret shape (``host``, ``port``,
    ``username``, ``password``, ``dbname``/``database``) plus an optional
    ``url`` short-circuit so callers can ship a pre-formed URI.
    """

    if "url" in payload and isinstance(payload["url"], str):
        return payload["url"]

    required = ("host", "username", "password")
    missing = [k for k in required if k not in payload]
    if missing:
        raise RuntimeError(
            "DB_SECRET_ARN payload missing required fields: " + ", ".join(missing)
        )

    host = payload["host"]
    port = payload.get("port", 5432)
    user = payload["username"]
    password = payload["password"]
    dbname = payload.get("dbname") or payload.get("database") or "postgres"

    # libpq URI; psycopg parses this directly.
    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"


# ---------------------------------------------------------------------------
# Core run logic
# ---------------------------------------------------------------------------


def run(
    *,
    dry_run: bool = False,
    migrations_dir: Path | None = None,
    database_url: str | None = None,
) -> RunResult:
    """Apply unapplied migrations and return a summary.

    Parameters
    ----------
    dry_run:
        When ``True``, do not connect; just enumerate the migrations that would
        be applied.
    migrations_dir:
        Override migration directory (used by tests).
    database_url:
        Pre-resolved Postgres URI; when provided, environment lookup is
        skipped. Tests use this to avoid needing AWS credentials.
    """

    _check_data_environment()
    discovered = _discover_migration_files(_migrations_dir(migrations_dir))
    discovered_names = tuple(m.filename for m in discovered)

    if dry_run:
        LOGGER.info("dry-run: discovered %d migrations", len(discovered))
        return RunResult(
            applied=(),
            skipped_already_applied=(),
            discovered=discovered_names,
            dry_run=True,
        )

    url = database_url if database_url is not None else _resolve_database_url()

    # Lazy import psycopg so the module remains importable in test tiers
    # where the optional dependency is not installed.
    try:
        import psycopg  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "psycopg is required to apply migrations but is not installed"
        ) from exc

    applied: list[str] = []
    skipped: list[str] = []

    with psycopg.connect(url, autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_MIGRATIONS_TABLE_DDL)
        conn.commit()

        with conn.cursor() as cur:
            cur.execute("SELECT filename FROM schema_migrations")
            already_applied = {row[0] for row in cur.fetchall()}

        for migration in discovered:
            if migration.filename in already_applied:
                skipped.append(migration.filename)
                LOGGER.info("skip already-applied %s", migration.filename)
                continue

            LOGGER.info("apply %s", migration.filename)
            with conn.cursor() as cur:
                cur.execute(migration.sql)
                cur.execute(
                    "INSERT INTO schema_migrations (filename) VALUES (%s)",
                    (migration.filename,),
                )
            conn.commit()
            applied.append(migration.filename)

    return RunResult(
        applied=tuple(applied),
        skipped_already_applied=tuple(skipped),
        discovered=discovered_names,
        dry_run=False,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply AO Radar Postgres migrations idempotently.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List migrations that would be applied without connecting.",
    )
    parser.add_argument(
        "--migrations-dir",
        type=Path,
        default=None,
        help="Override the migrations directory (defaults to ops/migrations).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    args = _parse_args(argv)
    try:
        result = run(dry_run=args.dry_run, migrations_dir=args.migrations_dir)
    except Exception as exc:  # noqa: BLE001 - top-level CLI surface
        LOGGER.error("migration run failed: %s", exc)
        return 1

    summary = {
        "dry_run": result.dry_run,
        "discovered": list(result.discovered),
        "applied": list(result.applied),
        "skipped_already_applied": list(result.skipped_already_applied),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
