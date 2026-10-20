# streamlit-coco — local development
UV       ?= uv
# Always include [dev] so cortex-code-agent-sdk is available for demos/tests.
PYTHON   ?= $(UV) run --extra dev
E2E_PYTHON ?= $(UV) run --extra e2e
STREAMLIT = $(PYTHON) python -m streamlit run
EXAMPLE  ?= examples/chat_app.py

.DEFAULT_GOAL := help

.PHONY: help install sync test lint format check audit e2e-install e2e test-all \
	run chat simple-chat modern-chat approval structured headless backlog cwd-upload e2e-harness \
	bi-semantic tableau-semantic app-builder \
	build publish sync-release clean adoption-stats adoption-chart \
	training training-html training-pdf training-check

# dsp-assets checkout that renders/validates the training pack (Steps 6-8 of
# $asset-owner-training run from there with DIR=). Override if yours lives elsewhere.
DSP_ASSETS ?= $(abspath $(CURDIR)/../dsp-assets)

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
	$(PYTHON) pytest tests/ --ignore=tests/e2e --ignore=tests/e2e_classic -v

lint: ## Lint with ruff
	$(PYTHON) ruff check .

format: ## Format with ruff
	$(PYTHON) ruff format .
	$(PYTHON) ruff check --fix .

audit: ## Dependency vulnerability scan (pip-audit)
	$(PYTHON) pip-audit --skip-editable

check: lint test ## Lint then unit tests

e2e-install: ## Install [e2e] extra + Chromium for Playwright
	$(UV) sync --extra e2e
	$(E2E_PYTHON) playwright install chromium

e2e: ## Run the Playwright tests: the window (scripted agent, no login) and the 0.1.9 chat helpers; Edge when Chromium is missing
	$(E2E_PYTHON) pytest tests/e2e tests/e2e_classic -m e2e -v

test-all: check e2e audit ## Full automated gate: lint + unit + e2e + audit

run: ## Run EXAMPLE (default: examples/chat_app.py)
	$(STREAMLIT) $(EXAMPLE)

simple-chat: ## Run examples/chat_app.py (STREAMLIT_COCO_AGENT=mock: no login)
	$(STREAMLIT) examples/chat_app.py

# Older docs and scripts still say `make chat`.
chat: simple-chat

modern-chat: ## Copilot rail or Ask CoCo window (examples/modern_chat)
	cd examples/modern_chat && $(UV) run --project ../.. --extra dev python -m streamlit run app.py

approval: ## Run examples/approval_gate.py
	$(STREAMLIT) examples/approval_gate.py

structured: ## Run examples/structured_output.py
	$(STREAMLIT) examples/structured_output.py

headless: ## Run examples/headless_pipeline.py
	$(PYTHON) examples/headless_pipeline.py

backlog: ## Run Product Backlog Desk demo (examples/backlog_desk)
	cd examples/backlog_desk && $(UV) run --project ../.. python -m streamlit run streamlit_app.py

cwd-upload: ## Run examples/cwd_upload_chat.py (attachments + uploader into cwd)
	$(STREAMLIT) examples/cwd_upload_chat.py

bi-semantic: ## Run BI → Semantic (Tableau / Power BI, repo streamlit-coco)
	cd examples/bi_to_semantic && $(UV) run --project ../.. --extra dev --with 'streamlit-extras>=1.3.0' --with 'pbixray>=0.15.4' python -m streamlit run app.py

tableau-semantic: bi-semantic ## Deprecated alias for bi-semantic

app-builder: ## Run App Builder (type library → brief → Copilot / Preview)
	cd examples/app_builder && $(UV) run --project ../.. --extra dev --with 'streamlit-extras>=1.3.0' python -m streamlit run app.py

e2e-harness: ## Run the CoCo-free harness the Playwright tests use (scripted agent)
	STREAMLIT_COCO_AGENT=mock $(STREAMLIT) examples/e2e_ux_harness.py

# Training pack targets (STANDARD §18). The same command means the same thing on
# every asset, dsp-assets included:
#
#   make training        browse the pack (this snippet)
#   make training-html   render the Markdown to companion HTML
#   make training-pdf    export the Enablement deck to PDF
#   make training-check  validate training.yml against the pack on disk
#
# Only `training` has to live here. The other three delegate to a dsp-assets
# checkout (DSP_ASSETS=) so the asset owner never leaves this repo.
training: ## Browse the training pack (Streamlit). PORT= pins a port
	@port=$${PORT:-8502}; \
	while lsof -nP -iTCP:$$port -sTCP:LISTEN >/dev/null 2>&1; do \
		port=$$((port + 1)); \
	done; \
	echo "Starting training app on http://localhost:$$port"; \
	cd doc/training/app && uv run --no-project --with streamlit --with pyyaml \
		--with '$(CURDIR)[sdk]' \
		streamlit run streamlit_app.py --server.port $$port; \
	code=$$?; if [ $$code -eq 130 ]; then exit 0; else exit $$code; fi

training-html: ## Render the pack Markdown to HTML (needs a dsp-assets checkout)
	@test -f "$(DSP_ASSETS)/Makefile" || { echo "set DSP_ASSETS=/path/to/dsp-assets"; exit 1; }
	@$(MAKE) --no-print-directory -C "$(DSP_ASSETS)" training-html \
		DIR="$(CURDIR)/doc/training" BRAND="Streamlit CoCo" PAGE="$(PAGE)"

training-pdf: ## Export the Enablement deck to PDF (needs a dsp-assets checkout)
	@test -f "$(DSP_ASSETS)/Makefile" || { echo "set DSP_ASSETS=/path/to/dsp-assets"; exit 1; }
	@$(MAKE) --no-print-directory -C "$(DSP_ASSETS)" training-pdf \
		DECK="$(CURDIR)/doc/training/enablement/deck.html"

training-check: ## Validate training.yml against the pack on disk (needs a dsp-assets checkout)
	@test -f "$(DSP_ASSETS)/Makefile" || { echo "set DSP_ASSETS=/path/to/dsp-assets"; exit 1; }
	@$(MAKE) --no-print-directory -C "$(DSP_ASSETS)" training-check \
		DIR="$(CURDIR)/doc/training" STRICT="$(STRICT)"

# Adoption metrics (PyPI + GitHub traffic). FORCE=1 overwrites today; UPDATE_ROADMAP=1 refreshes Current KPIs.
# BACKFILL=1 fills history.jsonl gaps from stored PyPI/GitHub daily series (no live re-fetch).
ADOPTION_STATS_FLAGS =
ifneq ($(FORCE),)
ADOPTION_STATS_FLAGS += --force
endif
ifneq ($(UPDATE_ROADMAP),)
ADOPTION_STATS_FLAGS += --update-roadmap
endif
ifneq ($(BACKFILL),)
ADOPTION_STATS_FLAGS += --backfill-missing
endif

adoption-stats: ## Collect PyPI + GitHub traffic into doc-dev/metrics/
	$(PYTHON) python scripts/collect_adoption_stats.py $(ADOPTION_STATS_FLAGS)

adoption-chart: ## Rebuild doc-dev/metrics/chart.html from history.jsonl
	$(PYTHON) python scripts/render_adoption_chart.py

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
