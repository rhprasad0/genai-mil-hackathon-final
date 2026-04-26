# AO Radar test tiers (per docs/testing-plan.md section 11).
# Synthetic-only. No real data. No commits.

PY ?= python3
PYTEST ?= $(PY) -m pytest

.PHONY: help test test-unit test-contract test-schema test-fixtures \
        test-lambda-boundary test-integration test-e2e test-meta \
        test-local test-ci validate-cards validate-seed lint typecheck

help:
	@echo "AO Radar Make targets:"
	@echo "  test-unit             Tier 1 fast unit + contract + safety + meta"
	@echo "  test-fixtures         Synthetic-data fixture validators"
	@echo "  test-schema           Schema CHECK and constraint tests (needs Postgres)"
	@echo "  test-lambda-boundary  lambda_handler boundary tests"
	@echo "  test-integration      Repo + tools + audit invariants (needs Postgres)"
	@echo "  test-local            Tier 2: unit + schema + integration + boundary + fixtures"
	@echo "  test-ci               Tier 3: same as local with CI flags"
	@echo "  test-e2e              Tier 4: deployed MCP endpoint (needs AO_RADAR_MCP_BASE_URL)"
	@echo "  validate-cards        ops.seed.validate --cards-only"
	@echo "  validate-seed         ops.seed.validate (cards + in-memory rows)"
	@echo "  lint                  ruff lint"
	@echo "  typecheck             mypy on src/"

test-unit:
	$(PYTEST) tests/unit tests/contract tests/safety tests/meta -m 'not db and not e2e'

test-fixtures:
	$(PYTEST) tests/fixtures

test-schema:
	$(PYTEST) tests/schema -m 'db or not db'

test-lambda-boundary:
	$(PYTEST) tests/lambda_boundary

test-integration:
	$(PYTEST) tests/integration

test-meta:
	$(PYTEST) tests/meta

test-local: test-unit test-fixtures
	$(PYTEST) tests/schema tests/lambda_boundary tests/integration

test-ci:
	$(PYTEST) tests/unit tests/contract tests/safety tests/meta \
	          tests/fixtures tests/schema tests/lambda_boundary tests/integration \
	          --cov=src --cov-report=term-missing --strict-markers -p no:cacheprovider

test-e2e:
	@if [ -z "$$AO_RADAR_MCP_BASE_URL" ]; then \
	  echo "AO_RADAR_MCP_BASE_URL not set; skipping deployed E2E"; exit 1; \
	fi
	$(PYTEST) tests/e2e -m e2e

validate-cards:
	$(PY) -m ops.seed.validate --cards-only

validate-seed:
	$(PY) -m ops.seed.validate

lint:
	$(PY) -m ruff check src tests ops

typecheck:
	$(PY) -m mypy src
