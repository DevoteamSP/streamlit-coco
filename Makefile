# streamlit-coco — local development
UV       ?= uv
PYTHON   ?= $(UV) run
STREAMLIT = $(PYTHON) streamlit run
EXAMPLE  ?= examples/chat_app.py

.DEFAULT_GOAL := help

.PHONY: help install sync test lint format check audit \
	run chat approval structured headless \
	build publish sync-release clean

# Public release clone (override: make sync-release RELEASE_REPO=/path/to/streamlit-coco)
RELEASE_REPO ?= $(abspath $(CURDIR)/../streamlit-coco)
RELEASE_REMOTE ?= https://github.com/DevoteamSP/streamlit-coco.git

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install: ## Install package + [dev] extras (editable via uv)
	$(UV) sync --extra dev

sync: install ## Alias for install

test: ## Run pytest
	$(PYTHON) pytest tests/ -v

lint: ## Lint with ruff
	$(PYTHON) ruff check .

format: ## Format with ruff
	$(PYTHON) ruff format .
	$(PYTHON) ruff check --fix .

audit: ## Dependency vulnerability scan (pip-audit)
	$(PYTHON) pip-audit

check: lint test ## Lint then test

run: ## Run EXAMPLE (default: examples/chat_app.py)
	$(STREAMLIT) $(EXAMPLE)

chat: ## Run examples/chat_app.py
	$(STREAMLIT) examples/chat_app.py

approval: ## Run examples/approval_gate.py
	$(STREAMLIT) examples/approval_gate.py

structured: ## Run examples/structured_output.py
	$(STREAMLIT) examples/structured_output.py

headless: ## Run examples/headless_pipeline.py
	$(PYTHON) examples/headless_pipeline.py

build: ## Build sdist + wheel into dist/
	$(UV) build

publish: build ## Upload dist/ to PyPI (prefer tagging streamlit-coco; see docs/deployment/publish.md)
	$(UV) publish

sync-release: ## Sync release tree → ../streamlit-coco (DRY_RUN=1 / COMMIT=1 / PUSH=1)
	RELEASE_REPO="$(RELEASE_REPO)" RELEASE_REMOTE="$(RELEASE_REMOTE)" \
		DRY_RUN="$(DRY_RUN)" COMMIT="$(COMMIT)" PUSH="$(PUSH)" MESSAGE="$(MESSAGE)" \
		bash scripts/sync_release.sh

clean: ## Remove caches and build artifacts
	rm -rf dist/ build/ *.egg-info .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -not -path './.venv/*' -exec rm -rf {} +
