"""Lambda entrypoint for the private DB-ops Lambda.

Sources of truth:
  - docs/application-implementation-plan.md section 12.

Accepts payloads of the form ``{"operation": "migrate"}`` or
``{"operation": "seed", "reset": true}``.  Refuses anything other than
``synthetic_demo``.  Never connected to API Gateway.
"""

from __future__ import annotations

import json
from typing import Any

from .operations import DBOpsRefusal, dispatch


def _refusal(detail: str) -> dict[str, Any]:
    return {
        "errorType": "DBOpsRefusal",
        "errorMessage": detail,
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda entrypoint for ``ao-radar-db-ops``."""

    if isinstance(event, str):
        try:
            event = json.loads(event)
        except json.JSONDecodeError as exc:
            return _refusal(f"invalid JSON event: {exc}")
    if not isinstance(event, dict):
        return _refusal("event must be an object")

    try:
        return dispatch(event)
    except DBOpsRefusal as exc:
        return _refusal(str(exc))
    except Exception as exc:  # noqa: BLE001
        return _refusal(f"unexpected error: {exc.__class__.__name__}")


__all__ = ["lambda_handler"]
