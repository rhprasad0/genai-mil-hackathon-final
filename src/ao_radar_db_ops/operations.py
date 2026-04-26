"""Operation dispatcher for the private DB-ops Lambda.

Sources of truth:
  - docs/application-implementation-plan.md section 12.
  - docs/schema-implementation-plan.md section 7.7.

Operations:
  - ``migrate``: apply forward-only SQL migrations from ``ops/migrations``.
  - ``seed`` or ``seed`` with ``reset=true``: invoke the synthetic-data
    teammate's seed loader (``ops.seed.load`` / ``ops.seed.reset``).

Every operation refuses unless ``DEMO_DATA_ENVIRONMENT == synthetic_demo``.
"""

from __future__ import annotations

import importlib
import os
from typing import Any


ALLOWED_DATA_ENVIRONMENT: str = "synthetic_demo"


class DBOpsRefusal(RuntimeError):
    """Raised when the DB-ops Lambda refuses an operation."""


def _ensure_synthetic_environment() -> None:
    if os.environ.get("DEMO_DATA_ENVIRONMENT", "").strip() != ALLOWED_DATA_ENVIRONMENT:
        raise DBOpsRefusal(
            "DB-ops Lambda refuses to run unless DEMO_DATA_ENVIRONMENT == synthetic_demo"
        )


def run_migrations() -> dict[str, Any]:
    """Apply migrations via ``ops.scripts.run_migrations.main``.

    Lazy import so the package can load even when the migration runner
    module is not yet on the Python path.
    """

    _ensure_synthetic_environment()
    runner = importlib.import_module("ops.scripts.run_migrations")
    if not hasattr(runner, "main"):
        raise DBOpsRefusal("ops.scripts.run_migrations.main is not defined")
    return runner.main()


def run_seed(*, reset: bool = False) -> dict[str, Any]:
    """Invoke the synthetic-data seed loader.

    Lazy import so the application package does not depend on
    ``ops.seed`` (owned by the synthetic-data teammate).  The package
    ``__init__`` is documentation-only, so import the concrete loader module.
    """

    _ensure_synthetic_environment()
    loader = importlib.import_module("ops.seed.load")
    if not hasattr(loader, "run_load"):
        raise DBOpsRefusal("ops.seed.load.run_load is not defined")
    loader.run_load(reset=reset)
    return {"status": "ok", "reset": reset}


def dispatch(payload: dict[str, Any]) -> dict[str, Any]:
    """Dispatch a single DB-ops payload."""

    operation = (payload.get("operation") or "").strip().lower()
    if operation == "migrate":
        return {"operation": operation, "result": run_migrations()}
    if operation == "seed":
        reset_flag = bool(payload.get("reset", False))
        return {
            "operation": operation,
            "reset": reset_flag,
            "result": run_seed(reset=reset_flag),
        }
    raise DBOpsRefusal(
        f"unknown DB-ops operation: {operation!r}; allowed values are 'migrate' or 'seed'"
    )


__all__ = ["DBOpsRefusal", "dispatch", "run_migrations", "run_seed"]
