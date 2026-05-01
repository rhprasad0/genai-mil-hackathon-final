"""Conservative live-provider cost helpers."""

from __future__ import annotations

from dataclasses import dataclass

from .live_contracts import STATUS_BLOCKED_COST_CAP


@dataclass(frozen=True)
class TokenRates:
    input_usd_per_1k: float
    output_usd_per_1k: float

    def __post_init__(self) -> None:
        if self.input_usd_per_1k < 0 or self.output_usd_per_1k < 0:
            raise ValueError("token rates must be non-negative")


@dataclass(frozen=True)
class CostProjection:
    allowed: bool
    projected_usd: float
    remaining_total_usd: float | None
    remaining_provider_usd: float | None
    status: str | None = None


def estimate_cost_usd(input_tokens: int, output_tokens: int, rates: TokenRates) -> float:
    if input_tokens < 0 or output_tokens < 0:
        raise ValueError("token counts must be non-negative")
    return (input_tokens / 1000.0 * rates.input_usd_per_1k) + (
        output_tokens / 1000.0 * rates.output_usd_per_1k
    )


def project_worst_case_cost(
    *,
    prompt_chars: int,
    max_output_tokens: int,
    rates: TokenRates,
    retry_count: int = 0,
    repair_turns: int = 0,
    current_total_usd: float = 0.0,
    current_provider_usd: float = 0.0,
    max_total_usd: float | None = None,
    max_provider_usd: float | None = None,
) -> CostProjection:
    """Project before scheduling, using a conservative char->token estimate."""

    if prompt_chars < 0 or max_output_tokens < 0 or retry_count < 0 or repair_turns < 0:
        raise ValueError("projection inputs must be non-negative")
    # Conservative enough for gating: one token per two chars, rounded up.
    estimated_input_tokens = (prompt_chars + 1) // 2
    per_attempt = estimate_cost_usd(estimated_input_tokens, max_output_tokens, rates)
    attempts = 1 + retry_count + repair_turns
    projected = per_attempt * attempts
    remaining_total = None if max_total_usd is None else max_total_usd - current_total_usd
    remaining_provider = None if max_provider_usd is None else max_provider_usd - current_provider_usd
    if remaining_total is not None and projected > remaining_total:
        return CostProjection(False, projected, remaining_total, remaining_provider, STATUS_BLOCKED_COST_CAP)
    if remaining_provider is not None and projected > remaining_provider:
        return CostProjection(False, projected, remaining_total, remaining_provider, STATUS_BLOCKED_COST_CAP)
    return CostProjection(True, projected, remaining_total, remaining_provider, None)
