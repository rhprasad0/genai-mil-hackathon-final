"""Environment-derived config for opt-in live provider calls."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .live_contracts import (
    ALLOWED_PROVIDERS,
    PROVIDER_ANTHROPIC,
    PROVIDER_GOOGLE,
    PROVIDER_OPENAI,
    STATUS_LIVE_CALLS_NOT_ENABLED,
    STATUS_PROVIDER_SKIPPED_MISSING_KEY,
    STATUS_PROVIDER_SKIPPED_MISSING_RATE,
    STATUS_PROVIDER_SKIPPED_MODEL_UNAVAILABLE,
)
from .live_costs import TokenRates, project_worst_case_cost

PROVIDER_KEY_ENV = {
    PROVIDER_OPENAI: "OPENAI_API_KEY",
    PROVIDER_ANTHROPIC: "ANTHROPIC_API_KEY",
    PROVIDER_GOOGLE: "GOOGLE_API_KEY",
}
PROVIDER_KEY_TEST_ENV = {
    PROVIDER_OPENAI: "OPENAI_API_KEY_TEST",
    PROVIDER_ANTHROPIC: "ANTHROPIC_API_KEY_TEST",
    PROVIDER_GOOGLE: "GEMINI_API_KEY_TEST",
}
PROVIDER_MODEL_ENV = {
    PROVIDER_OPENAI: "OPENAI_CHEAP_MODEL",
    PROVIDER_ANTHROPIC: "ANTHROPIC_CHEAP_MODEL",
    PROVIDER_GOOGLE: "GOOGLE_CHEAP_MODEL",
}


@dataclass(frozen=True)
class ProviderLiveConfig:
    provider: str
    enabled: bool
    has_key: bool
    model_id: str | None
    rates: TokenRates | None
    skip_status: str | None = None
    public_model_label: str = "runtime-configured cheap tier"

    @property
    def model_id_public_label(self) -> str:
        return self.public_model_label

    @property
    def endpoint_base_category(self) -> str:
        return f"{self.provider}_api_host"


ProviderRuntimeConfig = ProviderLiveConfig


@dataclass(frozen=True)
class LiveConfig:
    live_calls_enabled: bool
    providers: dict[str, ProviderLiveConfig]
    max_runs: int
    repetitions: int
    max_total_usd: float | None
    max_provider_usd: float | None
    timeout_seconds: float
    max_retries: int
    max_input_chars: int
    max_output_tokens: int
    raw_provider_allowlist: tuple[str, ...] = field(default_factory=tuple)

    def provider_config(self, provider: str) -> ProviderLiveConfig:
        return self.providers[provider]

    @property
    def provider_list(self) -> tuple[ProviderLiveConfig, ...]:
        return tuple(self.providers[provider] for provider in sorted(self.providers))

    def redacted_summary(self) -> dict[str, object]:
        return {
            "live_calls_enabled": self.live_calls_enabled,
            "providers": {
                provider: {
                    "enabled": cfg.enabled,
                    "has_key": cfg.has_key,
                    "model_configured": bool(cfg.model_id),
                    "rates_configured": cfg.rates is not None,
                    "skip_status": cfg.skip_status,
                }
                for provider, cfg in self.providers.items()
            },
            "max_runs": self.max_runs,
            "repetitions": self.repetitions,
            "max_total_usd": self.max_total_usd,
            "max_provider_usd": self.max_provider_usd,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "max_input_chars": self.max_input_chars,
            "max_output_tokens": self.max_output_tokens,
        }


def parse_live_config(env: Mapping[str, str]) -> LiveConfig:
    live_enabled = env.get("PB_LIVE_CALLS") == "1"
    allowlist = _parse_provider_allowlist(env.get("PB_LIVE_PROVIDERS"))
    max_runs = _int_env(env, "PB_LIVE_MAX_RUNS", 100, minimum=0)
    repetitions = _int_env(env, "PB_LIVE_REPETITIONS", 3, minimum=1)
    max_total_usd = _optional_float_env(env, "PB_LIVE_MAX_TOTAL_USD")
    max_provider_usd = _optional_float_env(env, "PB_LIVE_MAX_PROVIDER_USD")
    timeout_seconds = _float_env(env, "PB_LIVE_TIMEOUT_SECONDS", 30.0, minimum=0.1)
    max_retries = min(_int_env(env, "PB_LIVE_MAX_RETRIES", 1, minimum=0), 1)
    max_input_chars = _int_env(env, "PB_LIVE_MAX_INPUT_CHARS", 20000, minimum=1)
    max_output_tokens = _int_env(env, "PB_LIVE_MAX_OUTPUT_TOKENS", 1200, minimum=1)

    providers: dict[str, ProviderLiveConfig] = {}
    for provider in sorted(ALLOWED_PROVIDERS):
        enabled = live_enabled and provider in allowlist
        has_key = bool(env.get(PROVIDER_KEY_ENV[provider]) or env.get(PROVIDER_KEY_TEST_ENV[provider]))
        model_id = env.get(PROVIDER_MODEL_ENV[provider]) or None
        rates = _rates_for_provider(env, provider)
        skip_status = None
        if not live_enabled:
            skip_status = STATUS_LIVE_CALLS_NOT_ENABLED
        elif provider not in allowlist:
            enabled = False
        elif not has_key:
            skip_status = STATUS_PROVIDER_SKIPPED_MISSING_KEY
        elif not model_id:
            skip_status = STATUS_PROVIDER_SKIPPED_MODEL_UNAVAILABLE
        elif rates is None:
            skip_status = STATUS_PROVIDER_SKIPPED_MISSING_RATE
        providers[provider] = ProviderLiveConfig(
            provider=provider,
            enabled=enabled and skip_status is None,
            has_key=has_key,
            model_id=model_id,
            rates=rates,
            skip_status=skip_status,
        )

    return LiveConfig(
        live_calls_enabled=live_enabled,
        providers=providers,
        max_runs=max_runs,
        repetitions=repetitions,
        max_total_usd=max_total_usd,
        max_provider_usd=max_provider_usd,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
        max_input_chars=max_input_chars,
        max_output_tokens=max_output_tokens,
        raw_provider_allowlist=tuple(sorted(allowlist)),
    )


def can_schedule_call(
    config: LiveConfig,
    provider: str,
    *,
    scheduled_runs: int,
    prompt_chars: int,
    current_total_usd: float = 0.0,
    current_provider_usd: float = 0.0,
):
    if scheduled_runs >= config.max_runs:
        from .live_contracts import STATUS_BLOCKED_COST_CAP

        return False, STATUS_BLOCKED_COST_CAP, None
    cfg = config.provider_config(provider)
    if cfg.skip_status:
        return False, cfg.skip_status, None
    if cfg.rates is None:
        return False, STATUS_PROVIDER_SKIPPED_MISSING_RATE, None
    projection = project_worst_case_cost(
        prompt_chars=prompt_chars,
        max_output_tokens=config.max_output_tokens,
        rates=cfg.rates,
        retry_count=config.max_retries,
        repair_turns=1,
        current_total_usd=current_total_usd,
        current_provider_usd=current_provider_usd,
        max_total_usd=config.max_total_usd,
        max_provider_usd=config.max_provider_usd,
    )
    return projection.allowed, projection.status, projection


def _parse_provider_allowlist(raw: str | None) -> set[str]:
    if not raw:
        return set(ALLOWED_PROVIDERS)
    requested = {item.strip().lower() for item in raw.split(",") if item.strip()}
    return requested & set(ALLOWED_PROVIDERS)


def _rates_for_provider(env: Mapping[str, str], provider: str) -> TokenRates | None:
    prefix = provider.upper()
    input_rate = env.get(f"PB_LIVE_RATE_{prefix}_INPUT_USD_PER_1K")
    output_rate = env.get(f"PB_LIVE_RATE_{prefix}_OUTPUT_USD_PER_1K")
    if input_rate is None or output_rate is None:
        return None
    return TokenRates(float(input_rate), float(output_rate))


def _int_env(env: Mapping[str, str], name: str, default: int, *, minimum: int) -> int:
    value = int(env.get(name, str(default)))
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return value


def _float_env(env: Mapping[str, str], name: str, default: float, *, minimum: float) -> float:
    value = float(env.get(name, str(default)))
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return value


def _optional_float_env(env: Mapping[str, str], name: str) -> float | None:
    if name not in env or env[name] == "":
        return None
    value = float(env[name])
    if value < 0:
        raise ValueError(f"{name} must be non-negative")
    return value


LiveRuntimeConfig = LiveConfig
