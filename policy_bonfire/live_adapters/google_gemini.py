"""Google Gemini generateContent adapter with injectable fake-client support."""

from __future__ import annotations

from typing import Any

from policy_bonfire.live_contracts import (
    LiveModelRequest,
    LiveModelResponse,
    PROVIDER_GOOGLE,
    STATUS_EXCLUDED_MALFORMED_JSON,
    STATUS_PROVIDER_NO_CANDIDATE,
    STATUS_PROVIDER_SAFETY_REFUSAL,
)

from .base import (
    elapsed_ms,
    exception_response,
    get_value,
    monotonic_ms,
    normalized_response,
    parse_strict_json_object,
    status_from_finish_reason,
)


class GoogleGeminiAdapter:
    provider = PROVIDER_GOOGLE

    def __init__(self, *, client: Any, model_id: str, model_label: str = "google live model", model_family: str = "gemini_lineage") -> None:
        self.client = client
        self.model_id = model_id
        self.model_label = model_label
        self.model_family = model_family

    def build_payload(self, request: LiveModelRequest) -> dict[str, Any]:
        return {
            "model": self.model_id,
            "systemInstruction": {"parts": [{"text": request.trusted_instructions}]},
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": request.untrusted_packet_block}],
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": request.decision_schema,
                "temperature": request.temperature,
                "maxOutputTokens": request.max_output_tokens,
            },
        }

    def complete(self, request: LiveModelRequest) -> LiveModelResponse:
        payload = self.build_payload(request)
        start = monotonic_ms()
        try:
            raw = self._generate_content(payload)
        except Exception as exc:
            return exception_response(
                exc,
                provider=self.provider,
                model_id=self.model_id,
                model_label=self.model_label,
                model_family=self.model_family,
                latency_ms=elapsed_ms(start),
            )
        feedback_status = self._prompt_feedback_status(raw)
        candidates = get_value(raw, "candidates", []) or []
        usage_in, usage_out = self._usage(raw)
        text = None
        parsed = None
        finish_reason = feedback_status
        status = None
        if feedback_status is not None:
            status = status_from_finish_reason(feedback_status) or STATUS_PROVIDER_SAFETY_REFUSAL
        elif not isinstance(candidates, list) or not candidates:
            status = STATUS_PROVIDER_NO_CANDIDATE
            finish_reason = "no_candidate"
        else:
            first = candidates[0]
            finish_reason = self._finish_reason(first)
            status = self._candidate_safety_status(first) or status_from_finish_reason(finish_reason)
            text, non_text = self._candidate_text(first)
            if status is None:
                if non_text:
                    status = STATUS_EXCLUDED_MALFORMED_JSON
                else:
                    status, parsed, text = parse_strict_json_object(text)
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
            raw_text=text,
            parsed=parsed,
        )

    def _generate_content(self, payload: dict[str, Any]) -> Any:
        models = get_value(self.client, "models")
        if models is not None and hasattr(models, "generate_content"):
            return models.generate_content(**payload)
        if hasattr(self.client, "generate_content"):
            return self.client.generate_content(**payload)
        if hasattr(self.client, "generateContent"):
            return self.client.generateContent(**payload)
        raise TypeError("Gemini client must expose models.generate_content, generate_content, or generateContent")

    def _prompt_feedback_status(self, raw: Any) -> str | None:
        feedback = get_value(raw, "promptFeedback") or get_value(raw, "prompt_feedback")
        if not feedback:
            return None
        reason = get_value(feedback, "blockReason") or get_value(feedback, "block_reason")
        return reason if isinstance(reason, str) else None

    def _finish_reason(self, candidate: Any) -> str | None:
        reason = get_value(candidate, "finishReason") or get_value(candidate, "finish_reason")
        return reason if isinstance(reason, str) else None

    def _candidate_safety_status(self, candidate: Any) -> str | None:
        ratings = get_value(candidate, "safetyRatings") or get_value(candidate, "safety_ratings") or []
        for rating in ratings:
            blocked = get_value(rating, "blocked", False)
            probability = get_value(rating, "probability")
            if blocked is True or probability == "BLOCKED":
                return STATUS_PROVIDER_SAFETY_REFUSAL
        return None

    def _candidate_text(self, candidate: Any) -> tuple[str | None, bool]:
        content = get_value(candidate, "content", {}) or {}
        parts = get_value(content, "parts", []) or []
        if not isinstance(parts, list) or not parts:
            return None, False
        texts: list[str] = []
        for part in parts:
            text = get_value(part, "text")
            if isinstance(text, str):
                texts.append(text)
                continue
            return None, True
        return "".join(texts), False

    def _usage(self, raw: Any) -> tuple[int | None, int | None]:
        usage = get_value(raw, "usageMetadata") or get_value(raw, "usage_metadata") or {}
        input_tokens = get_value(usage, "promptTokenCount") or get_value(usage, "prompt_token_count")
        output_tokens = get_value(usage, "candidatesTokenCount") or get_value(usage, "candidates_token_count")
        return (input_tokens if isinstance(input_tokens, int) else None, output_tokens if isinstance(output_tokens, int) else None)
