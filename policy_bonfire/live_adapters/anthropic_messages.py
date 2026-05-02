"""Anthropic Messages adapter with injectable fake-client support."""

from __future__ import annotations

from typing import Any

from policy_bonfire.live_contracts import LiveModelRequest, LiveModelResponse, PROVIDER_ANTHROPIC, STATUS_EXCLUDED_MALFORMED_JSON

from .base import (
    elapsed_ms,
    exception_response,
    get_value,
    monotonic_ms,
    normalized_response,
    parse_strict_json_object,
    status_from_finish_reason,
)


class AnthropicMessagesAdapter:
    provider = PROVIDER_ANTHROPIC

    def __init__(self, *, client: Any, model_id: str, model_label: str = "anthropic live model", model_family: str = "anthropic_lineage") -> None:
        self.client = client
        self.model_id = model_id
        self.model_label = model_label
        self.model_family = model_family

    def build_payload(self, request: LiveModelRequest) -> dict[str, Any]:
        return {
            "model": self.model_id,
            "system": request.trusted_instructions + "\n\nReturn exactly one JSON object matching the supplied decision-envelope schema. Do not include markdown, prose, tool calls, or extra text.",
            "messages": [
                {
                    "role": "user",
                    "content": request.untrusted_packet_block,
                }
            ],
            "max_tokens": request.max_output_tokens,
            "temperature": request.temperature,
            "output_config": {
                "format": {
                    "type": "json_schema",
                    "name": "policy_bonfire_decision_envelope",
                    "schema": request.decision_schema,
                }
            },
        }

    def complete(self, request: LiveModelRequest) -> LiveModelResponse:
        payload = self.build_payload(request)
        start = monotonic_ms()
        try:
            raw = self._create_message(payload)
        except Exception as exc:
            return exception_response(
                exc,
                provider=self.provider,
                model_id=self.model_id,
                model_label=self.model_label,
                model_family=self.model_family,
                latency_ms=elapsed_ms(start),
            )
        finish_reason = self._finish_reason(raw)
        usage_in, usage_out = self._usage(raw)
        text, non_text = self._first_text(raw)
        status = status_from_finish_reason(finish_reason)
        parsed = None
        raw_hash_text = text
        if status is None:
            if non_text:
                status = STATUS_EXCLUDED_MALFORMED_JSON
            else:
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

    def _create_message(self, payload: dict[str, Any]) -> Any:
        messages = get_value(self.client, "messages")
        if messages is not None and hasattr(messages, "create"):
            return messages.create(**payload)
        if hasattr(self.client, "messages_create"):
            return self.client.messages_create(**payload)
        if hasattr(self.client, "create"):
            return self.client.create(**payload)
        raise TypeError("Anthropic client must expose messages.create, messages_create, or create")

    def _first_text(self, raw: Any) -> tuple[str | None, bool]:
        content = get_value(raw, "content", []) or []
        if not isinstance(content, list) or not content:
            return None, False
        first = content[0]
        content_type = get_value(first, "type")
        text = get_value(first, "text")
        if content_type == "text" and isinstance(text, str):
            return text, False
        return None, True

    def _finish_reason(self, raw: Any) -> str | None:
        for name in ("stop_reason", "finish_reason", "status"):
            value = get_value(raw, name)
            if isinstance(value, str):
                return value
        return None

    def _usage(self, raw: Any) -> tuple[int | None, int | None]:
        usage = get_value(raw, "usage", {}) or {}
        input_tokens = get_value(usage, "input_tokens")
        output_tokens = get_value(usage, "output_tokens")
        return (input_tokens if isinstance(input_tokens, int) else None, output_tokens if isinstance(output_tokens, int) else None)
