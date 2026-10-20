# Architecture

## Components

| Component | File | Role |
|---|---|---|
| `CocoOptions` | `streamlit_coco/options.py` | Typed configuration wrapper. Converts to the SDK's `CortexCodeAgentOptions` via `to_sdk_options()`; computes `options_hash()` so the background worker restarts when tool permissions change. |
| `CocoSession` | `streamlit_coco/session.py` | Multi-turn session. Owns a background thread (`threading.Thread`, name `coco-session`) that runs an asyncio loop wrapping `CortexCodeSDKClient`. Exposes `send`, `run`, `stream`, `cancel`, `reset`, `close`, `execute_plan`, `set_permission_mode`. |
| `PermissionManager` | `streamlit_coco/permissions.py` | Coordinates `can_use_tool` callbacks from the SDK with UI approvals. Tracks pending requests, the per-session `always_allowed_tools` set, and resolves via `approve_pending` / `deny_pending`. |
| `panel()` / `copilot_rail()` | `streamlit_coco/ui.py`, `streamlit_coco/rail.py` | Native Streamlit UI. `panel()` is the transcript/field/approvals/Stop primitive; `copilot_rail()` composes it into a right-rail Copilot (connection picker, queued jobs, transcript display config, example questions). |
| `app_viewer()` | `streamlit_coco/viewer.py`, `streamlit_coco/app_preview.py` | Preview column for a CoCo-generated Streamlit app: spawns a child `streamlit run` process, embeds it in an iframe, and offers **Fix with CoCo** by scraping `.preview.log`. |
| `bootstrap` | `streamlit_coco/bootstrap.py` | `check_environment`-driven start gate (`render_start_gate`), `get_or_create_session`, `chat_input_bar`, `reset_session`, `stop_session`, `cwd_uploader`. |
| `diagnostics` | `streamlit_coco/diagnostics.py` | `check_environment()` / `require_environment()` — probes SDK install, CLI reachability, and Snowflake config without starting an agent. |

Other modules are implementation detail (not stable public API), but matter
for extension work: `tool_names.py` (tool → `ToolFamily` dispatch),
`tool_cards.py` / `tool_extract.py` (per-family rendering and diff/SQL
extraction), `text_renderer.py` (pluggable text rendering), `messages.py`
(`CocoEvent` normalization from SDK NDJSON), `upload.py` (browser → `cwd`
uploads), `ask_user.py` / `sql_tool.py` (per-tool UI helpers).

## Repo map

```text
streamlit_coco/          the library (importable package)
  options.py              CocoOptions
  session.py              CocoSession, CocoChatResult, CocoRunStatus
  permissions.py          PermissionManager, approve_pending/deny_pending
  query.py                headless query()
  messages.py             CocoEvent, NDJSON -> event normalization
  diagnostics.py          check_environment / require_environment
  bootstrap.py            start gate, chat_input_bar, session helpers
  ui.py                   panel(), render_approvals(), render_plan_banner()
  rail.py                 copilot_rail(), transcript_display_config()
  viewer.py, app_preview.py   app_viewer() and its process helpers
  display.py              render_transcript, render_output_field, status
  upload.py               upload_to_cwd, cwd_uploader
  tool_names.py, tool_cards.py, tool_extract.py   tool-family dispatch
  text_renderer.py        pluggable text rendering
  errors.py                typed CocoError hierarchy
  component.py, frontend/  legacy CCv2 chat() component
examples/                 first-party demo apps (see below)
tests/                    unit + smoke; tests/e2e/ Playwright
doc/                      product, security, deployment, testing docs
doc/training/             this training pack
.github/workflows/        ci.yml, security.yml, release.yml
Makefile                  install/test/lint/run/build/publish targets
```

## Data flow

```text
Streamlit app
  -> streamlit-coco  (CocoOptions, CocoSession, panel()/copilot_rail())
  -> cortex-code-agent-sdk  (CortexCodeSDKClient, CortexCodeAgentOptions)
  -> CoCo CLI ("cortex")  -- spawned as a local subprocess
  -> Snowflake Cortex  (LLM + tools, using the connected Snowflake role)
```

The session background thread drives the SDK client and receives an NDJSON
event stream back from the CLI subprocess over a local transport (no network
hop in the local deployment target). `message_to_events()` /
`_blocks_to_events()` in `messages.py` normalize each SDK message
(`AssistantMessage`, `ResultMessage`, `StreamEvent`, tool-use/tool-result
blocks) into `CocoEvent` records that the UI and headless callers both
consume. When a tool call needs approval, the SDK invokes `can_use_tool`
(built by `build_can_use_tool()` in `permissions.py`); this call **blocks
the worker thread** on `PermissionManager.wait_for_decision()` until the UI
resolves it (or `approval_timeout_seconds` elapses, raising
`ApprovalTimeoutError`) — no further tool executes on that turn until the
decision is made.

## Invariants that must not be broken

- **Core headless imports never load Streamlit.** `CocoSession`, `query`,
  `CocoOptions`, the permission functions, and the error hierarchy import
  cleanly with no `streamlit` import on the path — this is what lets
  `examples/headless_pipeline.py` run from a plain terminal. UI exports
  (`panel`, `copilot_rail`, `chat_input_bar`, …) are resolved lazily through
  `streamlit_coco.__getattr__` (`_LAZY_ATTRS` in `streamlit_coco/__init__.py`),
  not imported eagerly at package import time.
- **Approval gates intercept before tool execution, not after.**
  `can_use_tool` is the SDK's pre-execution hook; `PermissionManager` creates
  the pending request and blocks the worker there. A tool that needs approval
  never runs speculatively and gets rolled back — it simply does not run
  until approved.
- **"Always allow" is per-session, in-memory only.** It lives in
  `PermissionManager.always_allowed_tools`, a plain `set` on the session
  object. It is never written to disk and never survives `reset()`,
  `close()`, or a process restart.
- **`AskUserQuestion` and `ExitPlanMode` never use "Always allow."**
  `permissions.py` special-cases both tool families to always create a fresh
  approval request, even if a prior "always allow" would otherwise apply.
- **The worker restarts when tool permissions change, not on every option
  edit.** `CocoOptions.options_hash()` only hashes fields that affect what a
  tool is allowed to do (`allowed_tools`, `disallowed_tools`,
  `permission_mode`, `require_approval_for`, `add_dirs`, …); `CocoSession`
  compares this hash and restarts the background worker only when it
  changes.
- **`app_viewer()` never imports `copilot_rail()`, and vice versa.** The
  preview component is host-agnostic: it does not know about job queues. A
  host app composes both and wires `on_fix` itself.

## Pipeline behind the Makefile demo commands

| Target | Example | Primitives wired |
|---|---|---|
| `make chat` | `examples/chat_app.py` | `check_environment()` → `render_start_gate()` → `get_or_create_session()` → `panel()` + `chat_input_bar()`. The preferred pattern. |
| `make approval` | `examples/approval_gate.py` | Legacy CCv2 `chat()` — all-in-one component with its own built-in input. |
| `make structured` | `examples/structured_output.py` | `CocoOptions.output_schema` + `on_structured_output` routing agent JSON into an app widget instead of chat text. |
| `make headless` | `examples/headless_pipeline.py` | `query()` and `CocoSession` driven from plain `async` Python — no Streamlit import anywhere in the run. |
| `make cwd-upload` | `examples/cwd_upload_chat.py` | `chat_input_bar(accept_file=...)` / `cwd_uploader()` → `upload_to_cwd()` into the agent's `cwd`. |
| `make backlog` | `examples/backlog_desk/` | Multipage app (Board / Epic / Ticket / Release) over local JSON, right-rail Copilot opened from a header button, no SQL tool. |
| `make bi-semantic` (alias `make tableau-semantic`) | `examples/bi_to_semantic/` | Deterministic parse (Estate map, KPI inventory) → `request_input(schema=...)` arbitration → approval-gated Write of a semantic view + row access policy + generated consumer, previewed via `app_viewer()`. |
| `make app-builder` | `examples/app_builder/` | Type catalog (`types/<id>/type.json`) drives a brief; `add_dirs` mounts the type's `SKILL.md` (+ `types/shared/SKILL.md`) so CoCo Writes `streamlit_app.py` under approval; `copilot_rail()` + `app_viewer()` for Build/Preview. |

## Example app orchestration

The three example apps that matter as distinct product surfaces:

- **`examples/chat_app.py`** — the reference implementation of the
  preferred pattern (`panel()` + `chat_input_bar`). Sidebar test-prompt
  runner reads `examples/testdata/prompts.json`.
- **`examples/backlog_desk/`** — first rail-based, no-SQL example. The
  Copilot is not a navigation page; it opens from a header **Copilot**
  button or an action link and closes with **Close**. Its "skills" are
  prompt templates (Summarize sprint, Draft release notes, Propose ticket
  update, Check definition of done), not `.cortex/skills/` files.
- **`examples/bi_to_semantic/`** and **`examples/app_builder/`** — the two
  examples that compose `copilot_rail()` with `app_viewer()`: a CoCo Write
  is followed by a live preview of the generated Streamlit app, with
  **Fix with CoCo** wired to `default_fix_prompt()` and a queued job.

See [extending](extending.html) for how to add a fourth example app to this
list, and [data-and-contracts](data-and-contracts.html) for the file
contracts each one reads and writes.
