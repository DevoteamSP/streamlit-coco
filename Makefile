# streamlit-coco — local development
UV       ?= uv
# Always include [dev] so cortex-code-agent-sdk is available for demos/tests.
PYTHON   ?= $(UV) run --extra dev
E2E_PYTHON ?= $(UV) run --extra e2e
STREAMLIT = $(PYTHON) python -m streamlit run
EXAMPLE  ?= examples/chat_app.py

.DEFAULT_GOAL := help

.PHONY: help install sync test lint format check audit e2e-install e2e test-all \
	run chat approval structured headless backlog cwd-upload e2e-harness \
	build publish sync-release clean adoption-stats

# Public release clone (override: make sync-release RELEASE_REPO=/path/to/streamlit-coco)
# Temporary: personal repo until DevoteamSP is validated on PyPI (see doc/deployment/publish.md).
RELEASE_REPO ?= $(abspath $(CURDIR)/../streamlit-coco)
RELEASE_REMOTE ?= https://github.com/lletourmy/streamlit-coco.git

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install: ## Install package + [dev] extras (editable via uv)
	$(UV) sync --extra dev

sync: install ## Alias for install

test: ## Run unit/smoke pytest (excludes browser e2e)
	$(PYTHON) pytest tests/ --ignore=tests/e2e -v

lint: ## Lint with ruff
	$(PYTHON) ruff check .

format: ## Format with ruff
	$(PYTHON) ruff format .
	$(PYTHON) ruff check --fix .

audit: ## Dependency vulnerability scan (pip-audit)
	$(PYTHON) pip-audit

check: lint test ## Lint then unit tests

e2e-install: ## Install [e2e] extra + Chromium for Playwright
	$(UV) sync --extra e2e
	$(E2E_PYTHON) playwright install chromium

e2e: ## Run Playwright UX e2e against examples/e2e_ux_harness.py
	$(E2E_PYTHON) pytest tests/e2e -m e2e -v

test-all: check e2e audit ## Full automated gate: lint + unit + e2e + audit

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

backlog: ## Run Product Backlog Desk demo (examples/backlog_desk)
	cd examples/backlog_desk && $(UV) run --project ../.. python -m streamlit run streamlit_app.py

cwd-upload: ## Run examples/cwd_upload_chat.py (upload into cwd)
	$(STREAMLIT) examples/cwd_upload_chat.py

tableau-semantic: ## Run Tableau → Semantic (repo streamlit-coco, not PyPI)
	cd examples/tableau_to_semantic && $(UV) run --project ../.. --extra dev --with 'streamlit-extras>=1.3.0' python -m streamlit run app.py

e2e-harness: ## Run CoCo-free UX harness used by Playwright
	$(STREAMLIT) examples/e2e_ux_harness.py

# Adoption metrics (PyPI + GitHub traffic). FORCE=1 overwrites today; UPDATE_ROADMAP=1 refreshes Current KPIs.
ADOPTION_STATS_FLAGS =
ifneq ($(FORCE),)
ADOPTION_STATS_FLAGS += --force
endif
ifneq ($(UPDATE_ROADMAP),)
ADOPTION_STATS_FLAGS += --update-roadmap
endif

adoption-stats: ## Collect PyPI + GitHub traffic into doc-dev/metrics/
	$(PYTHON) python scripts/collect_adoption_stats.py $(ADOPTION_STATS_FLAGS)

build: ## Build sdist + wheel into dist/
	$(UV) build

publish: build ## Upload dist/ to PyPI (prefer tagging streamlit-coco; see doc/deployment/publish.md)
	$(UV) publish

sync-release: ## Sync release tree → ../streamlit-coco (DRY_RUN=1 / COMMIT=1 / PUSH=1)
	RELEASE_REPO="$(RELEASE_REPO)" RELEASE_REMOTE="$(RELEASE_REMOTE)" \
		DRY_RUN="$(DRY_RUN)" COMMIT="$(COMMIT)" PUSH="$(PUSH)" MESSAGE="$(MESSAGE)" \
		bash scripts/sync_release.sh

clean: ## Remove caches and build artifacts
	rm -rf dist/ build/ *.egg-info .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -not -path './.venv/*' -exec rm -rf {} +
