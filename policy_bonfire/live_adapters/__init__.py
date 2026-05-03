"""Approved live adapter boundary.

Provider SDK/HTTP imports are allowed by import policy only in this package. The
current default registry exposes offline fake adapters; real provider adapters can
be added here without making core harness modules import network clients.
"""

from __future__ import annotations

import os
from typing import Mapping

from .anthropic_messages import AnthropicMessagesAdapter
from .base import FakeLiveAdapter, LiveProviderAdapter
from .google_gemini import GoogleGeminiAdapter
from .http_json import JsonHttpClient
from .openai_responses import OpenAIResponsesAdapter
from ..live_config import PROVIDER_KEY_ENV, PROVIDER_KEY_TEST_ENV, ProviderLiveConfig
from ..live_contracts import PROVIDER_ANTHROPIC, PROVIDER_GOOGLE, PROVIDER_IDS, PROVIDER_OPENAI


def default_adapter_registry(
    configs: tuple[ProviderLiveConfig, ...],
    *,
    env: Mapping[str, str] | None = None,
    offline_fake: bool = False,
    timeout_seconds: float = 30.0,
) -> dict[str, LiveProviderAdapter]:
    if offline_fake:
        return fake_adapter_registry(configs)
    env_map = os.environ if env is None else env
    adapters: dict[str, LiveProviderAdapter] = {}
    for config in configs:
        if config.provider not in PROVIDER_IDS or not config.enabled or not config.model_id:
            continue
        key = _provider_key(env_map, config.provider)
        if not key:
            continue
        client = JsonHttpClient(timeout_seconds=timeout_seconds)
        if config.provider == PROVIDER_OPENAI:
            adapters[config.provider] = OpenAIResponsesAdapter(client=_OpenAIHttpClient(client, key), model_id=config.model_id, model_label=config.public_model_label)
        elif config.provider == PROVIDER_ANTHROPIC:
            adapters[config.provider] = AnthropicMessagesAdapter(client=_AnthropicHttpClient(client, key), model_id=config.model_id, model_label=config.public_model_label)
        elif config.provider == PROVIDER_GOOGLE:
            adapters[config.provider] = GoogleGeminiAdapter(client=_GeminiHttpClient(client, key), model_id=config.model_id, model_label=config.public_model_label)
    return adapters


def fake_adapter_registry(configs: tuple[ProviderLiveConfig, ...]) -> dict[str, LiveProviderAdapter]:
    return {
        config.provider: FakeLiveAdapter(
            config.provider,
            model_id_exact=config.model_id or "offline-fake-model",
            model_id_public_label=config.public_model_label,
        )
        for config in configs
        if config.provider in PROVIDER_IDS
    }


def _provider_key(env: Mapping[str, str], provider: str) -> str | None:
    return env.get(PROVIDER_KEY_ENV[provider]) or env.get(PROVIDER_KEY_TEST_ENV[provider]) or None


class _OpenAIHttpClient:
    def __init__(self, http: JsonHttpClient, api_key: str) -> None:
        self.http = http
        self.api_key = api_key

    def responses_create(self, **payload):
        return self.http.post_json(
            "https://api.openai.com/v1/responses",
            payload,
            {"Authorization": f"Bearer {self.api_key}"},
        )


class _AnthropicHttpClient:
    def __init__(self, http: JsonHttpClient, api_key: str) -> None:
        self.http = http
        self.api_key = api_key

    def messages_create(self, **payload):
        return self.http.post_json(
            "https://api.anthropic.com/v1/messages",
            payload,
            {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
        )


class _GeminiHttpClient:
    def __init__(self, http: JsonHttpClient, api_key: str) -> None:
        self.http = http
        self.api_key = api_key

    def generate_content(self, **payload):
        model = payload.pop("model")
        return self.http.post_json(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            payload,
            {"x-goog-api-key": self.api_key},
        )


__all__ = ["FakeLiveAdapter", "LiveProviderAdapter", "default_adapter_registry", "fake_adapter_registry"]
