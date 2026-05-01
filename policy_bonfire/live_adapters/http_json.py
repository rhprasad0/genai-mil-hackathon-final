"""Tiny stdlib JSON HTTP client used only inside the live adapter boundary."""

from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .base import AdapterTimeoutError, AdapterTransientError


class JsonHttpClient:
    """Minimal POST-only JSON client that never logs request or response bodies."""

    def __init__(self, *, timeout_seconds: float = 30.0) -> None:
        self.timeout_seconds = timeout_seconds

    def post_json(self, url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        safe_headers = dict(headers)
        safe_headers.setdefault("Content-Type", "application/json")
        request = Request(url, data=body, headers=safe_headers, method="POST")
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310 - adapter-boundary HTTPS only in callers
                response_body = response.read().decode("utf-8")
        except TimeoutError as exc:
            raise AdapterTimeoutError("provider timeout") from exc
        except HTTPError as exc:
            status = getattr(exc, "code", 0)
            if status in {408, 409, 425, 429, 500, 502, 503, 504}:
                raise AdapterTransientError(f"provider transient http_{status}") from exc
            raise AdapterTransientError("provider http error") from exc
        except URLError as exc:
            raise AdapterTransientError("provider transport error") from exc
        try:
            parsed = json.loads(response_body)
        except json.JSONDecodeError as exc:
            raise AdapterTransientError("provider returned non-json body") from exc
        if not isinstance(parsed, dict):
            raise AdapterTransientError("provider returned non-object body")
        return parsed
