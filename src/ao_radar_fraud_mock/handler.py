"""Fraud-mock Lambda handler.

Sources of truth:
  - docs/application-implementation-plan.md section 9.
  - docs/schema-implementation-plan.md section 5.7.

Refuses any request whose ``data_environment`` is not ``synthetic_demo``.
Generates a deterministic synthetic signal set per voucher using the seed
string ``FRAUD_DETERMINISTIC_SEED``.  The handler never touches a database
and never reaches the network beyond the Lambda boundary.
"""

from __future__ import annotations

import json
import os
from typing import Any

from ao_radar_mcp.fraud_client.contract import (
    ALLOWED_DATA_ENVIRONMENT,
    FraudMockRequest,
    FraudMockResponse,
)

from .deterministic import generate_signals


_DEFAULT_SOURCE_LABEL: str = "synthetic_compliance_service_demo"
_DEFAULT_SEED: str = "ao-radar-synthetic-v1"


def _refusal(detail: str) -> dict[str, Any]:
    return {
        "errorType": "FraudMockRefusal",
        "errorMessage": detail,
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda entrypoint for the fraud-mock Lambda."""

    seed = os.environ.get("FRAUD_DETERMINISTIC_SEED", _DEFAULT_SEED)
    source_label = os.environ.get(
        "FRAUD_SIGNAL_SOURCE_LABEL", _DEFAULT_SOURCE_LABEL
    )
    if os.environ.get("DEMO_DATA_ENVIRONMENT", "").strip() != ALLOWED_DATA_ENVIRONMENT:
        return _refusal(
            "fraud-mock refuses to start unless DEMO_DATA_ENVIRONMENT == synthetic_demo"
        )

    if isinstance(event, str):
        try:
            event = json.loads(event)
        except json.JSONDecodeError as exc:
            return _refusal(f"invalid JSON event: {exc}")

    try:
        request = FraudMockRequest.model_validate(event)
    except Exception as exc:  # noqa: BLE001 - intentional broad catch
        return _refusal(f"invalid fraud-mock request: {exc.__class__.__name__}")

    if request.data_environment != ALLOWED_DATA_ENVIRONMENT:
        return _refusal(
            f"data_environment must equal {ALLOWED_DATA_ENVIRONMENT!r}; "
            f"got {request.data_environment!r}"
        )

    signals = generate_signals(
        request.voucher_id,
        seed=seed,
        source_label=source_label,
        requested_types=request.requested_signal_types,
    )
    response = FraudMockResponse(
        voucher_id=request.voucher_id,
        data_environment=request.data_environment,
        signals=signals,
    )
    return json.loads(response.model_dump_json())


__all__ = ["lambda_handler"]
