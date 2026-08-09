# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Pre-PyPI history used date headings (`YYYY-MM-DD`). From `0.1.0` onward, use semver
(`## [X.Y.Z] — YYYY-MM-DD`). Package version lives in `pyproject.toml`.

Living plan (what’s next): [`doc/roadmap.md`](doc/roadmap.md).

---

## [Unreleased]

## [0.1.5] — 2026-08-09

Alpha follow-up: browser uploads into the agent workspace, safer transcript UX, Playwright e2e, and SBOM on GitHub Releases.
Published from temporary Trusted Publisher on [`lletourmy/streamlit-coco`](https://github.com/lletourmy/streamlit-coco); public tree also synced to [`DevoteamSP/streamlit-coco`](https://github.com/DevoteamSP/streamlit-coco).

### Added
- **File upload into `cwd`** — `upload_to_cwd()` (+ `UploadedPath`, `CwdUploadError`), optional `chat_input_bar(..., accept_file=…)`, and `cwd_uploader()`; demo `examples/cwd_upload_chat.py` (`make cwd-upload`); docs [`doc/features/file-upload/`](doc/features/file-upload/)
- **Copy-to-clipboard** — assistant messages + tool payloads via CCv2 copy control (`show_copy=` on `panel()` / `render_transcript()`)
- **Rich markdown / SQL highlighting** — fenced code blocks in chat render with `st.code` + language (SQL/Python/…); bash tool output uses highlighted code blocks
- **Transcript windowing** — optional `max_messages=` on `panel()` / `render_transcript()` with **Load earlier**
- **SBOM on release** — CycloneDX JSON attached to GitHub Release assets (`dist/sbom-v*.cdx.json`)
- **Browser UX e2e** — Playwright suite vs CoCo-free [`examples/e2e_ux_harness.py`](examples/e2e_ux_harness.py) (`make e2e` / CI); process doc [`doc/testing.md`](doc/testing.md)
- **Per-version release kits** — public [`doc/releases/`](doc/releases/README.md) (checklist, screenshots); outreach in **`doc-dev/releases/`** (LinkedIn, Medium, community — not synced)

### Changed
- **Copy control** — icon-only Material Symbols `content_copy` button (label is aria/tooltip only)
- Require **`cortex-code-agent-sdk>=1.0.7`** (`[sdk]` / `[dev]` extras)
- Security workflow: drop CodeQL (private org needs GHAS license); keep gitleaks + pip-audit

## [0.1.0] — 2026-08-06

First PyPI release of `streamlit-coco` (alpha).
Published from temporary Trusted Publisher on [`lletourmy/streamlit-coco`](https://github.com/lletourmy/streamlit-coco).

### Added
- **Product Backlog Desk** — multipage demo (`examples/backlog_desk/`, `make backlog`): Board / Epic / Ticket / Release with right-rail Copilot over local JSON/Markdown
- **Headless multi-turn** — `CocoSession.stream()`, `await session.run(prompt)`, `execute_plan()`, `set_permission_mode()`; extended `examples/headless_pipeline.py`
- **Streamlit-free core imports** — lazy UI exports so headless scripts never load Streamlit
- **Plan mode Execute CTA** — native `render_plan_banner()` in `panel()`; CCv2 banner **Execute plan** trigger
- **Edit/Write unified diff** — approval + transcript previews via `difflib` (`tool_extract.unified_diff`)
- **Pluggable text renderer** — `text_renderer=` on `panel()` / `render_transcript()` / `render_output_field()`
- **App-owned `request_input`** — form + optional multi-field `schema=`
- Dual-repo publish — `make sync-release` / `scripts/sync_release.sh`; guide [`doc/deployment/publish.md`](doc/deployment/publish.md); Apache-2.0 `LICENSE`
- GitHub CI/CD (ci / security / release + PyPI publish on `v*` tags)
- API reference [`doc/api.md`](doc/api.md); local deployment docs [`doc/deployment/local.md`](doc/deployment/local.md)
- Typed errors (`streamlit_coco.errors`); `require_environment()`
- NDJSON fixture corpus (`tests/fixtures/ndjson/`)
- Feature docs + checklist sign-offs (panel, approvals, tools-display, structured-output, chat-ccv2, headless, text-renderer)
- `doc-dev/` — development-only docs (excluded from sync + sdist)

### Changed
- **Compact tool cards** — collapsed expanders (family · status · meta); auto-open on error; CCv2 `<details>` parity ([`doc/features/tools-display/SPEC.md`](doc/features/tools-display/SPEC.md))
- Temporary PyPI release surface: [`lletourmy/streamlit-coco`](https://github.com/lletourmy/streamlit-coco) until DevoteamSP is PyPI-validated
- Clear tool “running” captions when done (SDK `UserMessage` / NDJSON tool results)
- CCv2 skill hygiene — AbortController cleanup; pause `run_every` on pending approval; `isolate_styles=True`
- Preferred pattern docs: `panel()` + app-owned input; PRD / roadmap reconciled with Phase 3
- Package / README URLs point at the public release repo; development stays on `streamlit-coco-dev`
- Examples / chat demo polish (session bootstrap, sidebar badges, Settings popover, test-prompt toggle)
- CCv2 `chat()` registration cached (`@lru_cache`)

### Fixed
- Grep / Glob completed cards: compact summary instead of full result dumps
- AskUserQuestion: free-form / “Other…” options always last
- Security workflow: free Gitleaks CLI instead of `gitleaks-action@v2` (org license)
- Headless example: separate event loops for `query()` vs `CocoSession` (SDK cancel-scope teardown)

### Security
- Transitive `cryptography` → `50.0.0` (Dependabot); `pyopenssl` → `26.4.0`; `GitPython` already at `3.1.58`

---

## [2026-07-24]

### Added
- **Tools display & user interactions** — full spec + implementation ([`doc/features/tools-display/SPEC.md`](doc/features/tools-display/SPEC.md))
  - Meaningful bordered tool cards (no default JSON expanders) for Glob, Grep, Read, Write, Edit, Bash, SQL / `sql_execute`, AskUserQuestion, ExitPlanMode, and generic / MCP tools
  - `streamlit_coco.tool_names`, `tool_extract`, `tool_cards` dispatch; CCv2 frontend parity
  - AskUserQuestion UI: radio / multiselect, **Other…** free-text, Submit / Cancel; always routed through `can_use_tool`
  - SQL card: query code block + dataframe / text results; SQL preview on approval
  - ExitPlanMode: Approve plan / Reject (with optional feedback); never “Always allow”
  - CoCo debug mode (`STREAMLIT_COCO_DEBUG` / `COCO_DEBUG` / `st.session_state["coco_debug"]`) for collapsed **Raw tool payload**
- Feature checklist + `display_*` test prompt pack ([`doc/features/tools-display/test-checklist.md`](doc/features/tools-display/test-checklist.md), [`examples/testdata/prompts.json`](examples/testdata/prompts.json) v2 — 50+ prompts)
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
- DSP N1 feature test checklists under `doc/features/*/test-checklist.md`
- `doc/roadmap.md` — Now / Next / Later plan aligned with the PRD
- `Makefile` targets for install, test, lint, format, check, build, and example apps
- Cursor rule pinning Cortex Code Agent SDK docs as source of truth

### Changed
- Preferred app pattern documented as `panel()` + `chat_input_bar` / `st.chat_input` (legacy `chat()` retained)
- `doc/prd.md` and `README.md` synced to the implemented `panel()`-first API and package layout
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
- `doc/prd.md` and `README.md`

---

<!-- Notes:
- Link PRs/issues when available: (#42) or (DevoteamSP/streamlit-coco-dev#42)
- One entry per user-visible change
- Security fixes always under "Security", never under "Fixed"
- Update [Unreleased] as you go; on release: move to ## [X.Y.Z] — YYYY-MM-DD, clean empty subsections, refresh doc/roadmap.md
-->
