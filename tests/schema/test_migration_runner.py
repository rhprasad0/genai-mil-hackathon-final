"""Tests for ``ops.scripts.run_migrations``.

These exercise the local-only path: when ``DATABASE_URL`` is set the runner
should apply migrations once and skip them the second time. The lead's
session-scoped ``_migrations_applied`` fixture has already applied them, so
this test just checks idempotency by invoking the runner again and asserting
the result reports zero applied migrations.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = REPO_ROOT / "ops" / "migrations"


@pytest.mark.db
def test_runner_is_idempotent(_migrations_applied: str) -> None:
    """Run the migration twice; the second run is a no-op."""

    os.environ["DEMO_DATA_ENVIRONMENT"] = "synthetic_demo"
    from ops.scripts import run_migrations as runner

    # First call (the session fixture already ran one before us, so this is
    # effectively the second pass against an already-migrated DB).
    result = runner.run(database_url=_migrations_applied, migrations_dir=MIGRATIONS_DIR)
    assert result.applied == ()
    assert set(result.skipped_already_applied) == set(result.discovered)
    assert result.dry_run is False

    # Run a third time to be explicit about idempotency.
    result_again = runner.run(database_url=_migrations_applied, migrations_dir=MIGRATIONS_DIR)
    assert result_again.applied == ()
    assert set(result_again.skipped_already_applied) == set(result_again.discovered)


@pytest.mark.db
def test_runner_refuses_when_environment_not_synthetic(_migrations_applied: str) -> None:
    """The runner must refuse when DEMO_DATA_ENVIRONMENT is not synthetic_demo."""

    from ops.scripts import run_migrations as runner

    previous = os.environ.get("DEMO_DATA_ENVIRONMENT")
    os.environ["DEMO_DATA_ENVIRONMENT"] = "production"
    try:
        with pytest.raises(RuntimeError, match="synthetic_demo"):
            runner.run(database_url=_migrations_applied, migrations_dir=MIGRATIONS_DIR)
    finally:
        if previous is None:
            del os.environ["DEMO_DATA_ENVIRONMENT"]
        else:
            os.environ["DEMO_DATA_ENVIRONMENT"] = previous


@pytest.mark.db
def test_runner_dry_run_does_not_connect() -> None:
    """`--dry-run` should succeed without DATABASE_URL or DB_SECRET_ARN."""

    os.environ["DEMO_DATA_ENVIRONMENT"] = "synthetic_demo"
    from ops.scripts import run_migrations as runner

    result = runner.run(dry_run=True, migrations_dir=MIGRATIONS_DIR)
    assert result.dry_run is True
    assert result.applied == ()
    assert len(result.discovered) >= 2
    assert "0001_create_tables.sql" in result.discovered
    assert "0002_add_constraints_and_indexes.sql" in result.discovered


@pytest.mark.db
def test_schema_migrations_table_records_filenames(
    _migrations_applied: str,
) -> None:
    """After the runner has applied migrations, schema_migrations records each filename."""

    import psycopg

    with psycopg.connect(_migrations_applied) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT filename FROM schema_migrations ORDER BY filename")
            rows = [r[0] for r in cur.fetchall()]

    assert "0001_create_tables.sql" in rows
    assert "0002_add_constraints_and_indexes.sql" in rows
