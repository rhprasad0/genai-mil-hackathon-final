"""OpenAI Responses API adapter.

The adapter accepts an injected client; tests use fakes so no SDK import or network
access is required by default.
"""

from __future__ import annotations

from typing import Any

from policy_bonfire.live_contracts import LiveModelRequest, LiveModelResponse, PROVIDER_OPENAI

from .base import (
    elapsed_ms,
    exception_response,
    get_value,
    monotonic_ms,
    normalized_response,
    parse_strict_json_object,
    status_from_finish_reason,
)


class OpenAIResponsesAdapter:
    provider = PROVIDER_OPENAI

    def __init__(self, *, client: Any, model_id: str, model_label: str = "openai live model", model_family: str = "openai_lineage") -> None:
        self.client = client
        self.model_id = model_id
        self.model_label = model_label
        self.model_family = model_family

    def build_payload(self, request: LiveModelRequest) -> dict[str, Any]:
        return {
            "model": self.model_id,
            "instructions": request.trusted_instructions,
            "input": request.untrusted_packet_block,
            "store": False,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "policy_bonfire_decision_envelope",
                    "schema": request.decision_schema,
                    "strict": True,
                }
            },
            "temperature": request.temperature,
            "max_output_tokens": request.max_output_tokens,
        }

    def complete(self, request: LiveModelRequest) -> LiveModelResponse:
        payload = self.build_payload(request)
        start = monotonic_ms()
        try:
            raw = self._create_response(payload)
        except Exception as exc:  # fake clients use stdlib exceptions
            return exception_response(
                exc,
                provider=self.provider,
                model_id=self.model_id,
                model_label=self.model_label,
                model_family=self.model_family,
                latency_ms=elapsed_ms(start),
            )

        finish_reason = self._finish_reason(raw)
        text = self._output_text(raw)
        usage_in, usage_out = self._usage(raw)
        status = status_from_finish_reason(finish_reason)
        parsed = None
        raw_hash_text = text
        if status is None:
            status, parsed, raw_hash_text = parse_strict_json_object(text)
        return normalized_response(
            status=status,
            provider=self.provider,
            model_id=self.model_id,
            model_label=self.model_label,
            model_family=self.model_family,
            latency_ms=elapsed_ms(start),
            usage_input_tokens=usage_in,
            usage_output_tokens=usage_out,
            finish_reason=finish_reason,
            raw_text=raw_hash_text,
            parsed=parsed,
        )

    def _create_response(self, payload: dict[str, Any]) -> Any:
        responses = get_value(self.client, "responses")
        if responses is not None and hasattr(responses, "create"):
            return responses.create(**payload)
        if hasattr(self.client, "responses_create"):
            return self.client.responses_create(**payload)
        if hasattr(self.client, "create"):
            return self.client.create(**payload)
        raise TypeError("OpenAI client must expose responses.create, responses_create, or create")

    def _output_text(self, raw: Any) -> str | None:
        output_text = get_value(raw, "output_text")
        if isinstance(output_text, str):
            return output_text
        content = get_value(raw, "content")
        if isinstance(content, list) and content:
            first = content[0]
            text = get_value(first, "text")
            if isinstance(text, str):
                return text
        output = get_value(raw, "output")
        if isinstance(output, list):
            parts: list[str] = []
            for item in output:
                for content_item in get_value(item, "content", []) or []:
                    text = get_value(content_item, "text")
                    if isinstance(text, str):
                        parts.append(text)
            if parts:
                return "".join(parts)
        return None

    def _finish_reason(self, raw: Any) -> str | None:
        for name in ("finish_reason", "status", "stop_reason"):
            value = get_value(raw, name)
            if isinstance(value, str):
                if value == "incomplete":
                    details = get_value(raw, "incomplete_details", {})
                    reason = get_value(details, "reason")
                    return reason if isinstance(reason, str) else value
                return value
        return None

    def _usage(self, raw: Any) -> tuple[int | None, int | None]:
        usage = get_value(raw, "usage", {}) or {}
        input_tokens = get_value(usage, "input_tokens")
        output_tokens = get_value(usage, "output_tokens")
        return (input_tokens if isinstance(input_tokens, int) else None, output_tokens if isinstance(output_tokens, int) else None)
