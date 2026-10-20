# AGENTS.md: streamlit-coco

Guidance for coding agents working in this repository.

## Product

A Streamlit library: **Ask CoCo**, in front of a Cortex Code agent (Cortex Code Agent SDK). The default UI is the 0.1.9 chat family: `chat`, `panel`, `copilot_rail`. The floating window (a launcher at the bottom right, one Streamlit component in a fragment) is opt-in: `mini=True` on those calls, or `st_coco.ask_coco(cwd)`. The host says what the window's agent may do through a policy (`streamlit_coco.policy`); the default is the safest: reading inside the working folder is free, everything else asks, each time. Headless `query()` and `CocoSession` stay for scripts.

The decisions, the migration sheet and the no-regression table for the window are in [`doc/features/ask-coco/ask-coco.md`](doc/features/ask-coco/ask-coco.md). Every public name: [`doc/api.md`](doc/api.md).

Canonical SDK docs: https://docs.snowflake.com/en/user-guide/cortex-code-agent-sdk/cortex-code-agent-sdk

## Layout

- `streamlit_coco/`: the library
  - `window.py` (`ask_coco`, `get_window`, the handle) · `conversation.py` (the contract between the window and the agent; its docstring is the reference) · `policy.py` · `gate.py` · `features.py` · `labels.py` · `cortex.py` (the Cortex adapter) · `waits.py`, `extras.py`, `messages.py` (parts of the conversation)
  - `static/coco/` (the window's script, styles, logos) and `static/fonts/` (Montserrat, OFL)
  - `testing/`: the scripted agent, the fixtures, the harness, `domdiff`
  - `session.py`, `query.py`, `options.py`, `permissions.py` (headless and `CocoOptions`) · `viewer.py`, `app_preview.py` (`app_viewer`) · `upload.py`, `uploader.py`
- `examples/`: chat, approval gate, structured output, file upload, headless, backlog desk, BI to Semantic, App Builder
- `apps/`: **dev-only** full applications (never synced to the public `streamlit-coco`)
- `doc/prd.md`, `doc/api.md`, `doc/roadmap.md`, `doc/features/`: product, API and feature docs with their checklists
- `doc/releases/X.Y.Z/`: the public release kit (history; do not edit past versions)
- `doc-dev/`: **dev-only** docs (never synced to the public repo)
- `doc/deployment/publish.md`: dual-repo sync, then a tag to PyPI (`streamlit-coco`)
- `CHANGELOG.md`: shipped history (not the roadmap)

**Repos:** develop in `DevoteamSP/streamlit-coco-dev`; publish from `lletourmy/streamlit-coco` (`make sync-release`, then tag `v*`) until DevoteamSP is PyPI-validated.

## Commands

```bash
make install      # uv sync --extra dev
make check        # ruff and the unit tests (not the browser tests)
make e2e          # Playwright, the window on the scripted agent (Edge if Chromium is missing)
make audit        # pip-audit
make test-all     # check, e2e, audit
make simple-chat # panel, a test-prompt picker, rights as pills (`make chat` still runs it)
make modern-chat # Copilot rail, floating window, or both
make approval     # a listed command, a file rule, SQL, a standing permission
make structured   # a result handed to the page as data
make cwd-upload   # files attached in the field, and an uploader
make headless     # query(), a CocoSession, a Conversation answered in code
make backlog      # Product Backlog Desk
make bi-semantic  # Tableau / Power BI to semantic view
make app-builder  # App Builder
make adoption-stats  # daily PyPI and GitHub traffic into doc-dev/metrics/
```

No login needed: set `STREAMLIT_COCO_AGENT=mock` and any example runs on the scripted agent. Adoption KPIs: [`doc-dev/metrics/README.md`](doc-dev/metrics/README.md). Refresh `doc/roadmap.md` Currents only when asked (`make adoption-stats UPDATE_ROADMAP=1`).

Full test process: [`doc/testing.md`](doc/testing.md).

## Conventions

- The window's buttons for a request are **Allow** and **Decline**. A request may offer "Do not ask again for ..." (a standing permission, only with `FolderPolicy(standing=True)`) until the conversation ends. A standing permission never covers the `.git` folder, a secret-named file, or a place the policy flags.
- A question from CoCo and a plan always wait for the user. They have no switch and no standing permission.
- The default policy is the safest. A switch that widens rights (`commands`, `changes`, `sql`, `lookups`, `standing`) is off until the host turns it on.
- A request is written by the application from the checked call (`policy.request(...)`), never from the agent's own description.
- Every sentence of the window and the conversation is a key of `streamlit_coco/labels.py`. Add the key there; do not write text in the script or the conversation.
- Do not show raw JSON tool payloads by default: a step shows a plain name; the exact input is one click away.
- Update `CHANGELOG.md` `[Unreleased]` for user-visible changes, and the feature file and checklist when the window's behaviour changes.
- **Before cutting a release:** complete `doc/releases/X.Y.Z/CHECKLIST.md` and the outreach in `doc-dev/releases/X.Y.Z/`, then `doc/deployment/publish.md`. Do not tag until the public docs and QA sections are done. Sync [public GitHub issues](https://github.com/DevoteamSP/streamlit-coco/issues): close resolved, comment on progressed, propose new ones from `doc/roadmap.md`.
- A 0.1.9 application upgrades with no change: the window and its controls (`mini=True`, `copilot_rail(ask=True)`, `ask_coco`) are opt-in, never a default.
- Prefer small, focused diffs; no drive-by refactors.

## Testing

- Unit tests: `tests/` (`make check`).
- Browser tests: `tests/e2e/` (the window) and `tests/e2e_classic/` (the 0.1.9 chat helpers) (`make e2e-install` once, then `make e2e`).
- 0.1.9 compatibility: `tests/test_compat_019.py` holds the package to `tests/fixtures/api_0.1.9.json`. A public name, parameter or default of 0.1.9 does not change; add new parameters last, keyword-only, with a default. Do not delete the 0.1.9 tests (`test_copilot_rail.py`, `test_rich_text.py`, `test_classic_*.py`, `tests/e2e_classic/`).
- Manual, live Cortex Code: [`doc/features/ask-coco/test-checklist.md`](doc/features/ask-coco/test-checklist.md) before a release.
- Process: [`doc/testing.md`](doc/testing.md).
