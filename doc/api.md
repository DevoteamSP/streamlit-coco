# API reference — streamlit-coco

Public surface exported from `import streamlit_coco as st_coco`.  
Alpha `0.1.6` — signatures may still move; prefer this page over the PRD sketch.

**Related:** [README quickstart](../README.md) · [Local deployment](deployment/local.md) · [Feature docs](features/README.md) · [SDK docs](https://docs.snowflake.com/en/user-guide/cortex-code-agent-sdk/cortex-code-agent-sdk)

---

## Prefer this pattern

```python
import streamlit as st
import streamlit_coco as st_coco

opts = st_coco.CocoOptions(
    connection="analytics",
    cwd=".",
    allowed_tools=["Read", "Glob", "Grep"],
    require_approval_for=["Edit", "Write", "Bash"],
)

env = st_coco.check_environment(connection=opts.connection)
if not st_coco.render_start_gate(opts, session_key="copilot", env=env):
    st.stop()

session = st_coco.get_or_create_session(opts, key="copilot")
st_coco.panel(session=session, warm_up=True, show_status=True, run_every=0.25)
st_coco.chat_input_bar(session, placeholder="Ask CoCo…")
```

Use legacy `chat()` only when you want the all-in-one CCv2 component with built-in input.

---

## Options & session

### `CocoOptions`

User-facing configuration; converted to SDK `CortexCodeAgentOptions` via `to_sdk_options()`.

| Field | Type | Default | Notes |
| --- | --- | --- | --- |
| `connection` | `str \| None` | `None` | Snowflake CLI connection name |
| `cwd` | `str` | `"."` | Working directory for tools |
| `model` | `str \| None` | `None` | Prefer `"auto"` when set; see SDK model IDs |
| `allowed_tools` | `list[str]` | `[]` | Tools that may run without approval (when list-based approvals are set) |
| `disallowed_tools` | `list[str]` | `[]` | Blocked tools |
| `permission_mode` | `str` | `"default"` | e.g. `"plan"` for ExitPlanMode flows |
| `profile` | `str \| None` | `None` | SDK profile |
| `cli_path` | `str \| None` | `None` | Override CoCo CLI path (`CORTEX_CODE_CLI_PATH` also works) |
| `mcp_servers` | `dict` | `{}` | MCP server config forwarded to SDK |
| `hooks` | `dict` | `{}` | SDK hooks |
| `require_approval_for` | `list[str] \| Callable` | `[]` | Pause for HITL; AskUserQuestion / ExitPlanMode always prompt |
| `output_schema` | `dict \| None` | `None` | JSON Schema → SDK `output_format` |
| `max_turns` | `int \| None` | `None` | Cap agent turns |
| `approval_timeout_seconds` | `float` | `600.0` | HITL wait timeout |
| `extra_sdk_options` | `dict` | `{}` | Passthrough kwargs to SDK options |

**Methods**

- `options_hash() -> str` — stable hash used to restart the worker when permissions change
- `to_sdk_options(*, can_use_tool=None)` — build SDK options (`SDKNotInstalledError` if SDK missing)
- `auto_allow_tools() -> list[str]` — `allowed_tools` minus approval list
- `tools_requiring_approval()` — iterable of tools that need HITL (empty if policy is a callable)

### `CocoRunStatus`

`str` enum: `idle` · `connecting` · `ready` · `running` · `awaiting_user` · `completed` · `error` · `cancelled`.

### `CocoChatResult`

Snapshot returned by `panel()` / `chat()` / `session.chat_result()`:

| Field | Type |
| --- | --- |
| `last_prompt` | `str \| None` |
| `last_result` | `CocoEvent \| None` |
| `pending_approval` | `dict \| None` |
| `structured_output` | `Any` |
| `events` | `list[CocoEvent]` |
| `status` | `CocoRunStatus` |

### `CocoSession`

Multi-turn session backed by `CortexCodeSDKClient` on a background thread.

```python
session = st_coco.CocoSession(options=opts, key="copilot")
session.start()          # connect CLI eagerly
session.send("…")        # queue a turn
result = await session.run("…")  # headless: drain until turn completes
async for event in session.stream():  # headless event stream
    ...
session.execute_plan()   # leave plan mode (+ optional execute prompt)
session.cancel()
session.reset()
session.close()
```

| Member | Notes |
| --- | --- |
| `send(prompt)` | Queue prompt; raises `SessionStartError` / `SessionNotReadyError` on boot failure |
| `start()` / `ensure_ready(timeout=120)` | Connect worker; `ensure_ready` raises `SessionNotReadyError` |
| `run(prompt, *, timeout=None)` | Awaitable one-shot turn → `CocoChatResult` |
| `stream()` | Async iterator of `CocoEvent` (call after `send` / during turns) |
| `set_permission_mode(mode)` / `execute_plan(...)` | Leave plan mode; approve pending ExitPlanMode when present |
| `cancel()` / `close()` / `reset()` | Stop turn, shut down worker, or full clear + new permission manager |
| `chat_result()` | Build `CocoChatResult` |
| `is_running` / `is_ready` / `is_connecting` / `needs_polling` | UI polling helpers |
| `transcript` / `messages` / `events` | Transcript dicts and normalized events |
| `last_error` / `init_info` / `structured_output` | Diagnostics + last structured payload |
| `permission_manager` | Internal HITL coordinator |
| `add_event_listener(cb)` | `cb(CocoEvent)` on each ingest |
| `sync_options(options)` | Apply options; restart worker if hash changes |
| `set_show_structured_inline(bool)` | Whether result JSON is appended to transcript |

### `get_session(key) -> CocoSession | None`

Lookup in the process registry (sessions created with `key=`).

### `get_or_create_session(options, *, key="coco", sync_options=True) -> CocoSession`

Streamlit helper: store session in `st.session_state[key]`, optionally `sync_options`.

### `reset_session` / `stop_session`

```python
st_coco.reset_session(options, session_key="coco", warm_up=False) -> CocoSession
st_coco.stop_session(session_key="coco", gate_key="coco_started") -> None
```

`stop_session` tears down the session and clears the start-gate flag.

---

## Preferred UI

### `panel(session, **kwargs) -> CocoChatResult`

Native transcript / field output + approvals + Stop. App owns input.

| Param | Default | Notes |
| --- | --- | --- |
| `output_mode` | `"transcript"` | `"transcript"` or `"field"` |
| `output_label` | `"CoCo output"` | `None` hides the bordered output container |
| `show_tool_details` | `True` | Tool card detail |
| `show_thinking` | `False` | Thinking blocks |
| `show_approvals` | `True` | Render HITL controls |
| `show_stop` | `True` | Stop button while polling |
| `show_status` | `True` | Connect / turn status chrome |
| `show_plan_banner` | `True` | Plan-mode banner + **Execute plan** CTA |
| `warm_up` | `False` | `session.start()` on mount when idle |
| `status_expanded` | `"auto"` | `"auto"` / `"always"` / `"never"` |
| `approval_key_prefix` | `"coco"` | Widget key namespace |
| `use_fragment` | `True` | `@st.fragment` polling |
| `run_every` | `0.25` | Seconds; paused while approval pending |
| `text_renderer` | `None` | `"markdown"` (default) / `"write"` / `"text"` / … or callable. Default markdown highlights fenced code blocks via `st.code` |
| `show_copy` | `True` | Clipboard controls on assistant messages and tool cards |
| `max_messages` | `None` | Transcript window size; **Load earlier** reveals older items |
| `preview_chars` | `None` | Cap user/assistant text to the first N characters |
| `on_structured_output` | `None` | `Callable[[dict, CocoChatResult], None]` |
| `structured_output_container` | `None` | Container for structured render |

Feature doc: [`features/panel/panel.md`](features/panel/panel.md).

### `copilot_rail(session, *, title="Copilot", …) -> None`

Right-rail Copilot: connection popover with transcript pills beside it, queued job,
`panel()`, chat input. App-agnostic — callers own session lifecycle and job dicts.
While CoCo is busy, **Working · thinking…** is a badge on the pills row (not a
tall status card).

| Param | Default | Notes |
| --- | --- | --- |
| `session` | — | `CocoSession` or `None` until connected |
| `connected` | `True` | Whether Connect has been confirmed |
| `connections` | `None` | Snowflake connection names for the popover |
| `on_connect` / `on_disconnect` | `None` | Callbacks; omit to hide the popover |
| `job` | `None` | `{prompt, label, status, expect_structured, …}` |
| `on_job_sent` | `None` | Called after a queued prompt is `session.send`'d |
| `on_job_finished` | `None` | Called when that turn ends (`COMPLETED` / `ERROR` / `CANCELLED`, or `READY` after a run) so the app can drop the job |
| `show_copy` | `False` | Clipboard controls off for demo rails |
| `show_transcript_filters` | `True` | Pills: **Last messages** · **First 200 characters** |

### `transcript_view_pills(*, key=…, last_n=8, preview_chars=200) -> tuple[int \| None, int \| None]`

Standalone pills for apps that call `panel()` directly. Returns `(max_messages, preview_chars)`.
Label is collapsed by default (no **Transcript** heading).

Feature doc: [`features/copilot-rail/copilot-rail.md`](features/copilot-rail/copilot-rail.md).

### `chat_input_bar(session, *, placeholder=…, connecting_placeholder=…, key=None, accept_file=False, …) -> str | None`

`st.chat_input` wired to connect/run state; sends via `send_prompt` on submit. Disabled only after a failed boot (`ERROR` and not ready).

Optional file attachments (when the installed Streamlit supports `accept_file` on `st.chat_input`):

| Param | Default | Notes |
| --- | --- | --- |
| `accept_file` | `False` | `True` / `"multiple"` enables chat attachments |
| `file_type` | `None` | Passed to chat input; also used as extension allowlist |
| `max_upload_size` | `None` | Soft cap forwarded to Streamlit + library `max_bytes` |
| `upload_subdir` | `"_uploads"` | Quarantine under `CocoOptions.cwd` |
| `upload_overwrite` | `"replace"` | `"error"` / `"replace"` / `"skip"` |
| `inject_upload_paths` | `True` | Prefix the prompt with saved ``_uploads/…`` paths |

### `upload_to_cwd(target, files, *, subdir="_uploads", overwrite="error", max_bytes=…, allowed_extensions=…) -> list[UploadedPath]`

Streamlit-free helper: write browser uploads (or `(name, bytes)` tuples) under `cwd/subdir`.  
`target` may be a path, `CocoOptions`, or `CocoSession`. Raises `CwdUploadError` on bad names, disallowed extensions, oversize payloads, or overwrite conflicts.

### `cwd_uploader(target, *, label=…, overwrite="error", …) -> list[UploadedPath]`

Sidebar / chrome helper: `st.file_uploader` + `upload_to_cwd`, with an inventory caption for files already in `_uploads/`.

### `send_prompt(session, prompt) -> None`

Strip and queue; surfaces `CocoError` with `st.error`.

### `render_approvals(session, *, key_prefix="coco") -> bool`

HITL UI for pending tool approvals, AskUserQuestion, and ExitPlanMode.  
Button order: **Approve once** · **Always allow** · **Deny**. AskUser / plan never show Always allow.

### `render_plan_banner(session, …) -> bool`

Plan-mode banner with **Execute plan** (skipped while ExitPlanMode approval is showing).

### `approve_pending` / `deny_pending`

```python
st_coco.approve_pending(session, request_id, *, always=False, updated_input=None)
st_coco.deny_pending(session, request_id, *, reason=None)
```

Low-level resolve for custom approval UIs.

### Display helpers

| Function | Role |
| --- | --- |
| `render_transcript(session, …, text_renderer=None)` | Chat-style transcript with tool cards |
| `render_output_field(session, …, text_renderer=None)` | Latest assistant text as a field |
| `render_session_status(session, …)` | Soft status strip |
| `get_latest_assistant_text(session) -> str` | Last assistant text chunk |

### Bootstrap / gate

| Function | Role |
| --- | --- |
| `render_environment_status(env=None, *, connection=None, stacked=False, show_title=True)` | SDK / CLI / Snowflake probe UI |
| `render_start_gate(options, *, session_key=…, gate_key=…, warm_up=True, env=None) -> bool` | Landing screen; `False` → call `st.stop()` |

---

## Legacy CCv2

### `chat(**kwargs) -> CocoChatResult`

All-in-one Custom Component v2 with built-in input. Prefer `panel()` for new apps.

Notable params: `session` / `options`, `key`, `height`, `placeholder`, `use_fragment`, `run_every`, `output_mode`, `on_structured_output`, optional `on_event` / submit / approval / cancel callbacks.

Feature doc: [`features/chat-ccv2/chat-ccv2.md`](features/chat-ccv2/chat-ccv2.md).

### `request_input(question, *, key="coco_input", default="", schema=None, …) -> str | dict | None`

App-owned clarification form between turns. Returns `None` until Submit. With `schema=` (list of field dicts), returns a `dict` of values.

**Not** a CoCo clarification channel (no CCv2 `provide_input` trigger). Mid-turn questions use AskUserQuestion via `panel()`.

---

## Headless

### `async query(prompt, *, options=None, output_schema=None) -> AsyncIterator[CocoEvent]`

Single-turn wrapper around SDK `query()`. Raises `SDKNotInstalledError` / `QueryError` (and other `CocoError` subclasses via wrapping).

```python
async for event in st_coco.query("Profile CUSTOMERS", options=opts):
    if event.type == "result":
        print(event.structured_output)
```

### Multi-turn (`CocoSession`)

```python
session = st_coco.CocoSession(options=opts)
session.start()
session.ensure_ready()
result = await session.run("Summarize this repo.")
session.send("Follow-up")
async for event in session.stream():
    if event.type == "result":
        break
```

Resolve approvals from another task with `approve_pending` / `deny_pending` (see `examples/headless_pipeline.py`).

Feature doc: [`features/headless/headless.md`](features/headless/headless.md).

Core headless symbols (`CocoSession`, `query`, options, permissions, errors) import **without loading Streamlit**. UI exports (`panel`, `chat`, …) resolve lazily on first access.

### `CocoEvent`

Normalized, JSON-serializable event (`to_dict` / `from_dict`).

Common `type` values: `assistant_text`, `stream_event`, `thinking`, `tool_use`, `tool_result`, `permission_request`, `result`, `system`, `error`.

Useful fields: `text`, `delta`, `name`, `tool_use_id`, `input`, `content`, `is_error`, `request_id`, `tool_name`, `tool_input`, `subtype`, `duration_ms`, `structured_output`, `cost_usd`, `message`, `code`, `metadata`.

### `events_to_dataframe(events) -> DataFrame`

Flatten events for audit views (requires pandas).

---

## Environment & errors

### `check_environment(*, connection=None, cli_path=None) -> CocoEnvironment`

Probe without starting an agent. Does not raise.

`CocoEnvironment` fields: `sdk_installed`, `sdk_version`, `cli_path`, `cli_version`, `snowflake_config_file`, `connection_hint`.  
Properties: `ready`, `cli_ok`, `snowflake_config_found`, `snowflake_config_display`.

### `require_environment(*, connection=None, cli_path=None, require_snowflake_config=False) -> CocoEnvironment`

Like `check_environment`, but raises typed errors when SDK/CLI (and optionally Snowflake config) are missing.

### Exception hierarchy

```text
CocoError
├── SDKNotInstalledError          (also ImportError)
├── CLINotFoundError
├── CLIProbeError
├── SnowflakeConfigNotFoundError
├── CocoConnectionError
├── SessionStartError
├── SessionNotReadyError
├── ApprovalTimeoutError          (also TimeoutError)
├── QueryError
└── CwdUploadError
```

Catch `CocoError` for app-level handling; use subclasses for specific recovery.

---

## Tool helpers

| Function | Role |
| --- | --- |
| `tool_family(name)` | Map tool name → family enum used by cards |
| `is_sql_tool(name)` | SQL / `sql_execute` variants |
| `is_ask_user_question(name)` | AskUserQuestion name variants |
| `is_exit_plan_mode(name)` | ExitPlanMode |
| `is_debug_mode(*, session_state=None)` | `STREAMLIT_COCO_DEBUG` / `COCO_DEBUG` / `st.session_state["coco_debug"]` |

Tool card UX: [`features/tools-display/SPEC.md`](features/tools-display/SPEC.md).

---

## Package metadata

```python
st_coco.__version__  # e.g. "0.1.6"
```

Private modules (`bridge`, `tool_cards`, `tool_extract`, …) are implementation details and are not part of the stable public surface.
