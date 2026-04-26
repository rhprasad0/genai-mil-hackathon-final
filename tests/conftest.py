"""Shared pytest fixtures.

Per docs/testing-plan.md section 14, tier markers are:
- ``db``: requires a Postgres connection (DATABASE_URL).
- ``e2e``: requires a deployed MCP endpoint (AO_RADAR_MCP_BASE_URL).

Tests without a marker run in tier 1 (fast, hermetic).
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest


def _has_db_url() -> bool:
    return bool(os.environ.get("DATABASE_URL"))


def _has_mcp_base_url() -> bool:
    return bool(os.environ.get("AO_RADAR_MCP_BASE_URL"))


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Auto-skip ``db`` tests without DATABASE_URL and ``e2e`` tests without AO_RADAR_MCP_BASE_URL."""

    skip_db = pytest.mark.skip(reason="DATABASE_URL not set")
    skip_e2e = pytest.mark.skip(reason="AO_RADAR_MCP_BASE_URL not set")
    has_db = _has_db_url()
    has_e2e = _has_mcp_base_url()
    for item in items:
        if "db" in item.keywords and not has_db:
            item.add_marker(skip_db)
        if "e2e" in item.keywords and not has_e2e:
            item.add_marker(skip_e2e)


@pytest.fixture(scope="session")
def database_url() -> str:
    """Return the Postgres URL or skip if unset."""

    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set")
    return url


@pytest.fixture(scope="session")
def mcp_base_url() -> str:
    """Return the deployed MCP base URL or skip if unset."""

    url = os.environ.get("AO_RADAR_MCP_BASE_URL")
    if not url:
        pytest.skip("AO_RADAR_MCP_BASE_URL not set")
    return url.rstrip("/")


@pytest.fixture
def synthetic_demo_environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    """Set ``DEMO_DATA_ENVIRONMENT=synthetic_demo`` for the duration of a test."""

    monkeypatch.setenv("DEMO_DATA_ENVIRONMENT", "synthetic_demo")
    yield "synthetic_demo"
