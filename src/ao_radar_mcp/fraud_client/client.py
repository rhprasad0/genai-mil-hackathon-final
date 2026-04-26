"""Fraud-mock Lambda client.

Sources of truth:
  - docs/application-implementation-plan.md section 9.

Lazy import of ``boto3`` so unit tests can import this module without
boto3 installed.  The client never reaches outside the documented loop:
it only invokes the synchronously-invoked fraud-mock Lambda specified by
``FRAUD_FUNCTION_NAME`` and returns parsed contract objects.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .contract import (
    ALLOWED_DATA_ENVIRONMENT,
    FraudMockRequest,
    FraudMockResponse,
)


class FraudClientError(RuntimeError):
    """Raised when the fraud-mock Lambda invocation fails."""


@dataclass(frozen=True)
class FraudClientConfig:
    function_name: str
    invoke_timeout_s: float = 5.0


def invoke(
    config: FraudClientConfig,
    request: FraudMockRequest,
    *,
    lambda_client: Any | None = None,
) -> FraudMockResponse:
    """Synchronously invoke the fraud-mock Lambda and parse the response.

    Test code passes a stub via ``lambda_client``.  In Lambda runtime the
    helper imports ``boto3`` lazily.
    """

    if request.data_environment != ALLOWED_DATA_ENVIRONMENT:
        raise FraudClientError(
            f"data_environment must equal {ALLOWED_DATA_ENVIRONMENT!r}; "
            f"got {request.data_environment!r}"
        )

    client = lambda_client
    if client is None:
        import boto3  # noqa: WPS433 - intentional lazy import

        client = boto3.client("lambda")

    payload = json.dumps(request.model_dump()).encode("utf-8")
    response = client.invoke(
        FunctionName=config.function_name,
        InvocationType="RequestResponse",
        Payload=payload,
    )
    if response.get("FunctionError"):
        raise FraudClientError(
            f"fraud-mock Lambda returned FunctionError={response['FunctionError']}"
        )
    payload_obj = response.get("Payload")
    if payload_obj is None:
        raise FraudClientError("fraud-mock Lambda returned no Payload")
    raw = payload_obj.read() if hasattr(payload_obj, "read") else payload_obj
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    parsed = json.loads(raw)
    return FraudMockResponse.model_validate(parsed)


__all__ = ["FraudClientConfig", "FraudClientError", "invoke"]
