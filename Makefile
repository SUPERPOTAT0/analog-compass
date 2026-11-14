.DEFAULT_GOAL := help
UV ?= uv
PY := $(UV) run python

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

.PHONY: setup
setup: ## Install deps (runtime + dev + extras)
	$(UV) sync --all-extras --group dev

.PHONY: doctor
doctor: ## Print tool versions and check required env var NAMES (no secrets)
	$(PY) scripts/doctor.py

.PHONY: lint
lint: ## Ruff lint
	$(UV) run ruff check src tests scripts

.PHONY: fmt
fmt: ## Ruff format
	$(UV) run ruff format src tests scripts

.PHONY: type
type: ## mypy
	$(UV) run mypy

.PHONY: spec-check
spec-check: ## Validate api/openapi.yaml + internal refs
	$(PY) scripts/spec_check.py

.PHONY: config-check
config-check: ## Validate config cross-references
	$(PY) scripts/check_config_crossrefs.py

.PHONY: test
test: ## Run unit tests
	$(UV) run pytest

.PHONY: test-contract
test-contract: ## Contract tests
	$(PY) scripts/run_contract_tests.py

.PHONY: ci
ci: lint type spec-check config-check test test-contract ## Full CI gate

.PHONY: synthetic
synthetic: ## Build the synthetic data bundle
	$(PY) scripts/make_synthetic.py

.PHONY: data-inspect
data-inspect: ## Run the reference inspector on a bundle
	$(PY) scripts/inspect_bundle.py $(BUNDLE)

.PHONY: serve
serve: ## Run the API locally
	$(UV) run uvicorn analog_compass.api.app:app --reload --port 8000

.PHONY: agent-eval
agent-eval: ## Run the AI agent eval battery (offline, stubbed tools)
	$(UV) run pytest tests/agent -q

# --- later-ticket placeholders -------------------------------------------------
.PHONY: bundle-real qa-real licence-check spotcheck smoke-real freeze deploy rollback
bundle-real:  ; @echo "not implemented yet (ticket T-060)"; exit 1
qa-real:      ; @echo "not implemented yet (ticket T-060)"; exit 1
licence-check:; @echo "not implemented yet (ticket T-042)"; exit 1
spotcheck:    ; @echo "not implemented yet (ticket T-012)"; exit 1
smoke-real:   ; @echo "not implemented yet (ticket T-060)"; exit 1
freeze:       ; @echo "not implemented yet (ticket T-051)"; exit 1
deploy:       ; @echo "not implemented yet (ticket T-051)"; exit 1
rollback:     ; @echo "not implemented yet (ticket T-051)"; exit 1
