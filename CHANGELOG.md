# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning: date-based (`YYYY-MM-DD`) until v1.0.0 is cut, then semantic versioning.
Package version in `pyproject.toml` remains `0.1.0` (alpha) until the first PyPI release is cut.

Living plan (what’s next): [`docs/roadmap.md`](docs/roadmap.md).

---

## [Unreleased]

### Added

#### Dual-repo publish
- Public release repo [`DevoteamSP/streamlit-coco`](https://github.com/DevoteamSP/streamlit-coco); `make sync-release` / `scripts/sync_release.sh`; guide [`docs/deployment/publish.md`](docs/deployment/publish.md)
- Apache-2.0 `LICENSE`; PyPI Trusted Publisher gate in `release.yml` (`github.repository == DevoteamSP/streamlit-coco` only)

#### Phase 3 — HITL, headless, render flexibility
- **Headless multi-turn** — `CocoSession.stream()` and `await session.run(prompt)`; `execute_plan()` / `set_permission_mode()`; extended `examples/headless_pipeline.py`
- **Streamlit-free core imports** — lazy `__getattr__` for UI exports so headless scripts never load Streamlit; smoke test + example assert
- **Plan mode Execute CTA** — native `render_plan_banner()` in `panel()`; CCv2 banner **Execute plan** trigger
- **Edit/Write unified diff** — approval + transcript previews via `difflib` (`tool_extract.unified_diff`); Before/After fallback when empty
- **Pluggable text renderer** — `text_renderer=` on `panel()`, `render_transcript()`, `render_output_field()` (`markdown` / `write` / `text` / … or callable); feature docs under `docs/features/text-renderer/`
- **App-owned `request_input`** — form + optional multi-field `schema=` (AskUserQuestion remains the in-turn CoCo channel)
- Headless checklist re-signed (2026-07-27): `query()` + `run()` + `stream()` live path; no Streamlit import

#### Earlier unreleased (pre–Phase 3 on this branch)
- **Clear tool “running” captions when done** — parse SDK `UserMessage` / NDJSON `user` tool results; finalize leftover `running` tools on turn `result`
- **CCv2 skill hygiene** — JS cleanup via AbortController; pause `run_every` on pending approval; drop `provide_input`; `isolate_styles=True`; CSS via `--st-yellow-*` / `--st-red-*` / radius tokens
- **API reference** — [`docs/api.md`](docs/api.md)
- **Deployment docs (local)** — [`docs/deployment/local.md`](docs/deployment/local.md)
- **Typed error hierarchy** — `streamlit_coco.errors`; `require_environment()`
- **NDJSON fixture corpus** — `tests/fixtures/ndjson/` + `tests/test_ndjson_fixtures.py`
- Feature docs pack + checklist sign-offs (panel, approvals, tools-display, structured-output, chat-ccv2, headless)
- GitHub CI/CD (ci / security / release + optional PyPI publish on `v*` tags); `make publish`; hatch sdist excludes for agent/IDE dirs
- Smoke tests: CCv2 register-once; core import does not load Streamlit

### Changed
- Package / README / identity URLs point at the public [`streamlit-coco`](https://github.com/DevoteamSP/streamlit-coco) repo; development continues on [`streamlit-coco-dev`](https://github.com/DevoteamSP/streamlit-coco-dev)
- GitHub repository renamed to [`DevoteamSP/streamlit-coco-dev`](https://github.com/DevoteamSP/streamlit-coco-dev) (package name remains `streamlit-coco`)
- Examples `structured_output.py` / `approval_gate.py`: `get_or_create_session` + eager `start()` for CCv2 transcript across reruns
- Chat demo sidebar: compact status badges; Settings popover; test prompts behind a toggle
- [`docs/roadmap.md`](docs/roadmap.md) — Phase 3 marked shipped; Next is tag/PyPI + Docker/SPCS docs only
- CCv2 `chat()` registration cached (`@lru_cache`) so `st.components.v2.component` runs once per process
- Headless example: separate event loops for `query()` vs `CocoSession` to avoid SDK cancel-scope teardown issues

### Fixed
- Grep / Glob completed cards: compact summary instead of dumping full result bodies
- AskUserQuestion: free-form / “Other…” options always last in radio / multiselect
- Security workflow: free Gitleaks CLI instead of `gitleaks-action@v2` (org license)

---

## [2026-07-24]

### Added
- **Tools display & user interactions** — full spec + implementation ([`docs/features/tools-display/SPEC.md`](docs/features/tools-display/SPEC.md))
  - Meaningful bordered tool cards (no default JSON expanders) for Glob, Grep, Read, Write, Edit, Bash, SQL / `sql_execute`, AskUserQuestion, ExitPlanMode, and generic / MCP tools
  - `streamlit_coco.tool_names`, `tool_extract`, `tool_cards` dispatch; CCv2 frontend parity
  - AskUserQuestion UI: radio / multiselect, **Other…** free-text, Submit / Cancel; always routed through `can_use_tool`
  - SQL card: query code block + dataframe / text results; SQL preview on approval
  - ExitPlanMode: Approve plan / Reject (with optional feedback); never “Always allow”
  - CoCo debug mode (`STREAMLIT_COCO_DEBUG` / `COCO_DEBUG` / `st.session_state["coco_debug"]`) for collapsed **Raw tool payload**
- Feature checklist + `display_*` test prompt pack ([`docs/features/tools-display/test-checklist.md`](docs/features/tools-display/test-checklist.md), [`examples/testdata/prompts.json`](examples/testdata/prompts.json) v2 — 50+ prompts)
- Chat demo: Plan mode toggle, debug checkbox, test-prompt runner by category

### Changed
- Approval button order (left → right): **Approve once** · **Always allow** · **Deny** (Deny rightmost); AskUser Submit · Cancel; plan Approve · Reject
- Tool approvals show family-specific previews (path, content, Before/After, command, SQL) instead of raw JSON by default

---

## [2026-07-23]

### Added
- `streamlit_coco.bootstrap` — `check_environment` / start gate helpers, `get_or_create_session`, `chat_input_bar`, `reset_session`, `stop_session`
- `streamlit_coco.diagnostics` — `CocoEnvironment` probe (CLI, SDK, Snowflake config) without starting an agent
- Session readiness lifecycle — `CONNECTING` → `READY` / `ERROR`, `ensure_ready()`, init metadata capture
- Soft status chrome in `panel()` — Starting / Thinking / tool activity / Needs approval without remount flicker
- DSP N1 feature test checklists under `docs/features/*/test-checklist.md`
- `docs/roadmap.md` — Now / Next / Soon / Later plan aligned with `docs/PRD.md`
- `Makefile` targets for install, test, lint, format, check, build, and example apps
- Cursor rule pinning Cortex Code Agent SDK docs as source of truth

### Changed
- Preferred app pattern documented as `panel()` + `chat_input_bar` / `st.chat_input` (legacy `chat()` retained)
- `docs/PRD.md` and `README.md` synced to the implemented `panel()`-first API and package layout
- Example `examples/chat_app.py` simplified around bootstrap helpers

### Fixed
- Avoid double-display of Snowflake connections TOML path in the environment / start gate UI
- `chat_input_bar` — graceful fallback when Streamlit lacks `submit_mode` (< 1.59)
- Session status skeleton — fallback placeholder when `st.skeleton` is unavailable (< 1.59)

---

## [2026-07-22] — Alpha baseline (shipped)

Core library and preferred Streamlit UX first landed:

- [x] Pip-installable package + `CocoOptions` / `CocoSession` / `query()`
- [x] Native UI: `panel()` + app-owned input (`chat_input_bar` / `send_prompt`)
- [x] Streaming transcript, tool cards, Stop, fragment polling
- [x] Human-in-the-loop approvals (`require_approval_for`, Deny / Approve once / Always)
- [x] Structured output (inline JSON or `on_structured_output`)
- [x] Legacy CCv2 `chat()` (still supported)
- [x] Examples: chat, approval gate, structured output, headless pipeline

### Added (detail)
- Initial `streamlit-coco` package (`0.1.0` alpha): Python API + Streamlit embedding for Snowflake CoCo
- Normalized `CocoEvent` model and unit tests (`tests/test_core.py`)
- Legacy CCv2 `chat()` component with static frontend assets under `streamlit_coco/frontend/`
- `docs/PRD.md` and `README.md`

---

<!-- Notes:
- Link PRs/issues when available: (#42) or (DevoteamSP/streamlit-coco-dev#42)
- One entry per user-visible change
- Security fixes always under "Security", never under "Fixed"
- Update [Unreleased] as you go; rename to a date (or semver after v1.0.0) on release
-->
