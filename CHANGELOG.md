# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Pre-PyPI history used date headings (`YYYY-MM-DD`). From `0.1.0` onward, use semver
(`## [X.Y.Z] — YYYY-MM-DD`). Package version lives in `pyproject.toml`.

Living plan (what’s next): [`doc/roadmap.md`](doc/roadmap.md).

---

## [Unreleased]

## [0.1.8] — 2026-09-06

App Builder for business users, plus rail starter questions and Display config.

### Added

- Copilot rail **example questions** — `copilot_rail(example_questions=…)` shows starter buttons after Connect on an empty transcript. Each item is `{title, question}`: the title is the button label, hover shows the question, click sends that text to CoCo. They hide once a user/assistant turn or a queued job is present (and come back after **Clear chat**). App Builder and BI → Semantic pass a short set.
- **App Builder** example (`examples/app_builder`, `make app-builder`) — type library with **topic pills**, local types that need **no Snowflake** (CSV explorer, call transcription, meeting recap, prompt library), filled brief, demo scaffold or CoCo Write, Preview via `app_viewer()`.
- App Builder **profile step** — dropping the KPI presentation demo fixture runs a deterministic pandas profile (`engine/profile.py`, no CoCo) and pre-fills metrics / grain / filters as findings to confirm. Audience and must-not stay blank (only a person can answer them). Library cards and the Brief chrome show a **grounding** pill (Files / Semantic view / Documents / URLs).
- App Builder chrome — pages **Welcome · Library · Brief · Studio · Admin**, **Open Copilot** / **Open Preview** labels, a rewritten Welcome, a three-step Brief (your data · what we found · only you can answer), and an **Admin** screen (type cards on the left, editor on the right) to view / add / edit / delete app types.
- App Builder **KPI guidelines** — `types/semantic-kpis/` ships `SKILL.md` + `reference/streamlit_app.py` + `CHECKLIST.md`. After an approved Write, Preview auto-runs; the generate prompt self-checks once against the checklist / `.preview.log`, then stops (manual **Fix with CoCo** if still red).
- App Builder Copilot — **App brief** expander on the rail to edit the owner brief **and every type question**, with **Save** and **Save & regenerate** (queues CoCo to rewrite the app from `BRIEF.md`).
- App Builder **shared generation skill** (`types/shared/SKILL.md`) — every Build / regenerate prompt tells CoCo to Read this file plus the type `SKILL.md` (absolute paths; both folders mounted via `add_dirs`). Admin can edit both files. Type skills extend shared; they do not replace it.

### Changed

- App Builder Welcome — only **Get started — browse types** remains; **Try a demo type** and the Welcome **Open Copilot** button are gone (Copilot stays in the header).
- App Builder skills live under `types/` — each type’s `SKILL.md` sits next to `type.json`; the shared pack is `types/shared/SKILL.md` (no `type.json`, so it is not a catalog card).
- Copilot rail **Display config** — the **Last messages** / **First 200 characters** pills move into an icon-only Material popover (`:material/display_settings:`, no label). Inside: the same on/off pills plus sliders for last-message count (1–50) and first-*n* characters (40–1000). Slider and pill changes fragment-rerun the rail (popover stays open) so the transcript updates live. New helper: `transcript_display_config()`. `transcript_view_pills()` stays for apps that call `panel()` directly. While CoCo runs, **Working · …** and the model name sit on one row.
- App Builder generate prompt — self-check against `CHECKLIST.md` only when the type ships one (KPI does; other types skip without commenting).
- App Builder **Brief** — **Build this app**, **Try a local demo**, **Open Copilot**, **Open Studio**, and **Delete app** sit at the top of the page. **App name** is its own card above **Your brief** (display name; folder slug stays). No expanders; type story / allows / will-not in columns; sketches under the brief; one **Questions** card on the right. Profile metrics appear only when a file was read.
- App Builder apps are **named** — Library **Create a new project** (type card popover + App name) writes `out/<slug>/`; header **New app** is gone; Resume and the header badge show the app name. Resume and Brief can **delete** an app (confirm popover).
- App Builder **Library** — **Resume** and **Create a new project** both use a 6-column grid. Topic pills sit at the top and filter saved apps and types. Resume cards show name, type, grounding, last updated, Open / Delete.
- App Builder catalog — each type brief gained two extra questions (audience, tone, layout, comparison, …). **`0.1.8` live set locked** to the six folders under `types/` (KPI presentation, Data quality, Call transcription, Meeting recap, Prompt library, CSV explorer). Document comparison and every `urls` type are later.
- App Builder **Admin** — type cards and the type editor sit in bordered panes with a vertical resize slider; short fields use three-column rows; icon is a Material Symbol popover; Brief questions sit in tabs (add / edit / delete), not a JSON textarea.
- BI demo fixtures live under [`examples/bi_samples/`](examples/bi_samples/) (`tableau/` + `powerbi/`). Chat exploratory prompts stay in [`examples/testdata/`](examples/testdata/).

### Fixed

- App Builder **Save & regenerate** now writes `BRIEF.md` from the expander widgets before queuing CoCo, and does not let the Brief page overwrite that file on the same turn.

### Security

- Lockfile: `gitpython` 3.1.58 → 3.1.61 and `pip` 26.1.2 → 26.2.1 (`make audit`).

## [0.1.7] — 2026-08-15

Alpha follow-up: a reusable Streamlit App Viewer, and BI → Semantic now loads Tableau **or** Power BI.

### Added
- **App viewer** (`app_viewer()`, `start_app_preview` / `stop_app_preview`, `last_preview_exception`, `default_fix_prompt`) — child Streamlit process, iframe, **Fix with CoCo** via `on_fix`. Optional `title_extra=` sits on the title row immediately left of **Close**. The host queues the job; the viewer does not import `copilot_rail`. Feature: [`doc/features/app-viewer/`](doc/features/app-viewer/)
- Power BI parse for the BI → Semantic example: **`pbixray` is the primary** `.pbix` / `.pbit` reader (VertiPaq `DataModel`); `DataModelSchema` is a `.pbit` fallback. Default pack is Microsoft's MIT Obvience samples (`Customer Profitability Sample (auto).pbix` + `Corporate Spend.pbix`). Screen 4 compares colliding table contracts (`Fact` / `Scenario` / `Date`) — public samples have no RLS.

### Changed
- README: **When not to use** and **Ownership** sections; **Architecture** explains `panel()` → session → SDK → CLI (not a file tree)
- **Example: BI → Semantic** — `examples/tableau_to_semantic` is now `examples/bi_to_semantic` (`make bi-semantic`; `make tableau-semantic` still aliases). Load accepts Tableau **or** Power BI. Load puts **Upload** / **Use MIT Tableau** / **Use MIT Power BI** on one row and lists sources as type-icon cards (size, format, modified) with a **Remove** action. A **Welcome** screen explains the app, the six-step flow, and how to use Copilot / Preview. The generated Power BI consumer composes a KPI row, chart cards, and one detail table from report visuals (skips slicers / textboxes / tooltip pages; no longer one dataframe per tile). The CoCo brief is a BI UX spec (page tabs, slicers, cross-filter, Altair, focus mode, distinct theme) instead of a restyle of the Python scaffold. Preview chrome is `st_coco.app_viewer()` (Python consumer on **:8511**, CoCo consumer on **:8512**). **Generate with CoCo** opens the Copilot rail and asks you to connect if the session is not up. Copilot and Preview can open together; **Fix with CoCo** queues `default_fix_prompt` as a job.

### Fixed
- `make audit` / CI `pip-audit` use `--skip-editable` so a pre-tag version bump is not reported as “Dependency not found on PyPI”

## [0.1.6] — 2026-08-13

Alpha follow-up: a reusable Copilot rail, consultant training pack, and a Tableau → Semantic example that uses the rail as a product copilot (not a chat window).

### Added
- **Copilot rail** (`copilot_rail()`, `transcript_view_pills()`) — generic right-rail Copilot (connection, queued jobs, transcript pills: last messages / first 200 characters). `panel()` / `render_transcript()` gain `preview_chars=`. Feature: [`doc/features/copilot-rail/`](doc/features/copilot-rail/)
- **Example: Tableau → Semantic** — multipage demo (`examples/tableau_to_semantic`, `make tableau-semantic`) that extracts estate/KPI/access drift from MIT Tableau Server workbooks, arbitrates with `request_input`, Writes a semantic view + row access policy, and generates a Streamlit consumer (**Build with python** or **Build with CoCo** with **Save Brief** → generate; brief reloads from `BRIEF.md`) with **disconnected** (no warehouse) and live `SEMANTIC_VIEW(...)` modes. **Preview** shares the Copilot right-rail slot (inline studio or run-on-the-fly at `:8511`); the split uses `streamlit_extras.resizable_columns`. Screens 2–5 restore `out/*.json` when the session reopens.
- **Training pack** — consultant enablement under [`doc/training/`](doc/training/) (overview, setup, hands-on lab, demo script, quiz, enablement deck) plus workshop [`W01`](doc/methodology/workshops/w01-setup-architecture-first-app.md)

### Changed
- README: document `make cwd-upload`, `make e2e-install` / `make e2e`, `make test-all`, and `make tableau-semantic`
- **Copilot rail** — transcript pills sit beside Connection (no **Transcript** label / “Showing …” caption); changing them fragment-reruns Copilot only. Long cwd paths in the status caption use `...` in the middle (100-character cap). **Working · thinking…** is a badge on that same row instead of a tall status card. **Cancel job** sits on the title row beside Close and hides when the CoCo turn finishes (`on_job_finished`).

### Fixed
- **Structured output** — strip `$schema` / `$id` before passing JSON Schema to the CoCo SDK (avoids `no schema with key or ref "https://json-schema.org/draft/2020-12/schema"` when contract files include a draft URI)
- Replace deprecated `use_container_width` with `width="stretch"` (Streamlit ≥1.57)
- **Example: Tableau → Semantic** — Generate selectors (step, how-to-build, dashboards, preview mode) keep their values when Copilot opens; a saved `BRIEF.md` is loaded into the CoCo editor from disk; multiple `.md` files are switched with pills.

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
