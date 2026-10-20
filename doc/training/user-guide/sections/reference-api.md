# API reference

The public Python API of `streamlit-coco`, as exported from
`streamlit_coco` (see the [index](../index.html) for the exact version this
guide describes). Private modules (`bridge`, `tool_cards`, `tool_extract`,
and others not listed here) are implementation details, not stable API —
they are not documented as reference entries.

## `CocoOptions`

The configuration dataclass for a session or a `query()` call
(`streamlit_coco/options.py`).

| Field | Type | Default | Effect |
|---|---|---|---|
| `connection` | `str \| None` | `None` | Snowflake CLI connection name to use |
| `cwd` | `str` | `"."` | Working directory the agent's tools operate in |
| `model` | `str \| None` | `None` | Model selection; prefer `"auto"` when set |
| `allowed_tools` | `list[str]` | `[]` | Tools that may run without approval |
| `disallowed_tools` | `list[str]` | `[]` | Tools blocked entirely |
| `permission_mode` | `str` | `"default"` | Overall permission mode, e.g. `"plan"` for `ExitPlanMode` flows |
| `profile` | `str \| None` | `None` | SDK profile name |
| `cli_path` | `str \| None` | `None` | Override the `cortex` CLI path (`CORTEX_CODE_CLI_PATH` env also works) |
| `mcp_servers` | `dict` | `{}` | MCP server configuration forwarded to the SDK |
| `hooks` | `dict` | `{}` | SDK hooks passthrough |
| `require_approval_for` | `list[str] \| Callable` | `[]` | Tools that pause for human approval; `AskUserQuestion`/`ExitPlanMode` always pause |
| `output_schema` | `dict \| None` | `None` | JSON Schema forwarded to the SDK as `output_format` (`$schema`/`$id` stripped before forwarding) |
| `max_turns` | `int \| None` | `None` | Caps the number of agent turns |
| `approval_timeout_seconds` | `float` | `600.0` | Seconds to wait for a pending approval before `ApprovalTimeoutError` |
| `extra_sdk_options` | `dict` | `{}` | Passthrough kwargs forwarded to the SDK's own options object |

### Methods

- `options_hash() -> str` — a stable hash of the options that changes only
  when a value affecting the running session changes (used to decide whether
  the background worker must restart).
- `to_sdk_options(*, can_use_tool=None)` — builds the SDK-native options
  object; raises `SDKNotInstalledError` if the SDK is not installed.
- `auto_allow_tools() -> list[str]` — the effective set of tools that run
  without approval.
- `tools_requiring_approval() -> list[str]` — the effective set of tools that
  pause for approval.

```python
options = st_coco.CocoOptions(
    connection="my_connection",
    cwd=".",
    allowed_tools=["Read", "Glob", "Grep"],
    require_approval_for=["Edit", "Write", "Bash"],
    approval_timeout_seconds=300.0,
)
```

Used by: [I want to build a minimal CoCo app](task-build-a-minimal-app.html)

## `CocoRunStatus`

A `str` enum (`streamlit_coco/session.py`) giving a session's current state.

| Value | Meaning |
|---|---|
| `idle` | No session activity started yet |
| `connecting` | Background worker starting |
| `ready` | Connected, waiting for a prompt |
| `running` | A turn is in progress |
| `awaiting_user` | A tool call is paused on a pending approval |
| `completed` | The turn finished normally |
| `error` | The turn or the session failed |
| `cancelled` | The turn was cancelled |

```python
if session.chat_result().status == st_coco.CocoRunStatus.awaiting_user:
    st.warning("Waiting on an approval.")
```

Used by: [Concepts](concepts.html#cocorunstatus)

## `CocoChatResult`

A dataclass snapshot of one turn's outcome, returned by `panel()`, `chat()`
and `session.chat_result()`.

| Field | Type | Default | Effect |
|---|---|---|---|
| `last_prompt` | `str \| None` | — | The most recent prompt sent |
| `last_result` | `CocoEvent \| None` | — | The most recent terminal event |
| `pending_approval` | `dict \| None` | — | The pending approval request, if any |
| `structured_output` | `Any` | — | The last structured payload, if `output_schema` was set |
| `events` | `list[CocoEvent]` | — | All events for the session so far |
| `status` | `CocoRunStatus` | — | The current run status |

```python
result = session.chat_result()
if result.pending_approval:
    st.info(f"Waiting on: {result.pending_approval['tool_name']}")
```

Used by: [I want to configure tool approvals](task-configure-tool-approvals.html)

## `CocoSession`

A multi-turn session backed by a `CortexCodeSDKClient` on a background
thread (`streamlit_coco/session.py`).

| Member | Effect |
|---|---|
| `send(prompt)` | Queue a prompt; raises `SessionStartError`/`SessionNotReadyError` if not ready |
| `start()` | Start the background worker |
| `ensure_ready(timeout=120)` | Await readiness; raises `SessionNotReadyError` on timeout or boot failure |
| `run(prompt, *, timeout=None)` | Send a prompt and await its result |
| `stream()` | Async-iterate events for the current/next turn |
| `set_permission_mode(mode)` | Change the permission mode |
| `execute_plan(...)` | Execute a plan produced under `permission_mode="plan"` |
| `cancel()` | Cancel the in-flight turn |
| `close()` | Tear down the background worker |
| `reset()` | Clear the transcript and restart the worker |
| `chat_result()` | Return the current `CocoChatResult` |
| `is_running` / `is_ready` / `is_connecting` / `needs_polling` | Boolean state properties |
| `transcript` / `messages` / `events` | The accumulated turn/event history |
| `last_error` / `init_info` / `structured_output` | Diagnostics and the last structured payload |
| `permission_manager` | The session's approval-state manager |
| `add_event_listener(cb)` | Register a callback invoked per new event |
| `sync_options(options)` | Apply new `CocoOptions`; restarts the worker if `options_hash()` changed |
| `set_show_structured_inline(bool)` | Toggle inline structured-output rendering |

```python
session = st_coco.CocoSession(options=options, key="copilot")
session.start()
result = await session.run("List the tables in my schema.")
```

Used by: [I want to run CoCo headless](task-run-headless.html)

### Session registry helpers

| Function | Effect |
|---|---|
| `get_session(key) -> CocoSession \| None` | Look up an existing session by key in the process registry |
| `get_or_create_session(options, *, key="coco", sync_options=True) -> CocoSession` | Streamlit helper: get or create a session in `st.session_state[key]` |
| `reset_session(options, session_key="coco", warm_up=False) -> CocoSession` | Reset (or create) the session at `session_key` |
| `stop_session(session_key="coco", gate_key="coco_started") -> None` | Tear down the session and clear the start-gate flag |

```python
session = st_coco.get_or_create_session(options, key="coco")
```

Used by: [I want to build a minimal CoCo app](task-build-a-minimal-app.html)

## UI — preferred pattern

### `panel(session, **kwargs) -> CocoChatResult`

Renders the native transcript or field output, approval controls, and a
Stop button for a session.

| Parameter | Type | Default | Effect |
|---|---|---|---|
| `output_mode` | `str` | `"transcript"` | `"transcript"` or `"field"` |
| `output_label` | `str \| None` | `"CoCo output"` | `None` hides the bordered output container |
| `show_tool_details` | `bool` | `True` | Show tool card detail |
| `show_thinking` | `bool` | `False` | Show thinking blocks |
| `show_approvals` | `bool` | `True` | Render the approval controls |
| `show_stop` | `bool` | `True` | Show the Stop button while polling |
| `show_status` | `bool` | `True` | Show connect/turn status chrome |
| `show_plan_banner` | `bool` | `True` | Show the plan-mode banner and Execute plan CTA |
| `warm_up` | `bool` | `False` | Call `session.start()` on mount when idle |
| `status_expanded` | `str` | `"auto"` | `"auto"` / `"always"` / `"never"` |
| `approval_key_prefix` | `str` | `"coco"` | Widget key namespace |
| `use_fragment` | `bool` | `True` | Poll inside an `@st.fragment` |
| `run_every` | `float` | `0.25` | Poll interval in seconds; paused while an approval is pending |
| `text_renderer` | `str \| Callable \| None` | `None` | `"markdown"` (default) / `"write"` / `"text"` / `"caption"` / `"code"` or a callable |
| `show_copy` | `bool` | `True` | Show clipboard controls |
| `max_messages` | `int \| None` | `None` | Transcript window; **Load earlier** reveals older items |
| `preview_chars` | `int \| None` | `None` | Cap user/assistant text to the first N characters |
| `on_structured_output` | `Callable[[dict, CocoChatResult], None] \| None` | `None` | Called when a structured payload arrives |
| `structured_output_container` | container \| `None` | `None` | Container to render structured output into |

```python
st_coco.panel(session, output_mode="transcript", show_thinking=False)
```

Used by: [I want to build a minimal CoCo app](task-build-a-minimal-app.html)

### `copilot_rail(session, *, title="Copilot", …) -> None`

A right-rail Copilot around `panel()`, for multipage apps.

| Parameter | Type | Default | Effect |
|---|---|---|---|
| `session` | `CocoSession` | — | The session to render |
| `connected` | `bool` | `True` | Whether the rail shows as connected |
| `connections` | `list \| None` | `None` | Connection choices, if switching is offered |
| `toml_file` | `str \| None` | `None` | Snowflake config file to read connections from |
| `on_connect` / `on_disconnect` | `Callable \| None` | `None` | Connection lifecycle callbacks |
| `job` | `dict \| None` | `None` | A queued job: `{prompt, label, status, expect_structured}` |
| `on_job_sent` / `on_job_finished` | `Callable \| None` | `None` | Job lifecycle callbacks |
| `show_copy` | `bool` | `False` | Show clipboard controls |
| `show_transcript_filters` | `bool` | `True` | Show the transcript display-config popover |
| `example_questions` | `list \| None` | `None` | `{title, question}` dicts or `(title, question)` tuples |
| `deferred` | `bool` | `False` | Defer rendering (also settable per example question) |

```python
st_coco.copilot_rail(session, title="Copilot", example_questions=[
    ("Summarize", "Summarize this sprint."),
])
```

Used by: [Example apps reference](reference-examples.html)

### `transcript_display_config` / `transcript_view_pills`

`transcript_display_config(*, key=…, last_n=8, preview_chars=200) -> tuple[int | None, int | None]`
— the display-settings icon popover (`:material/display_settings:`) with
Last messages / First n characters pills and sliders.

`transcript_view_pills(*, key=…, last_n=8, preview_chars=200)` — the same
pills as a standalone widget, without the popover chrome.

```python
last_n, preview_chars = st_coco.transcript_display_config(key="rail")
```

Used by: [Concepts](concepts.html#the-transcript)

### `app_viewer(app_dir, *, key="coco_app_viewer", …) -> None`

Embeds a live preview of an app the agent just wrote.

| Parameter | Type | Default | Effect |
|---|---|---|---|
| `app_dir` | `str` | — (required) | Folder containing `streamlit_app.py` |
| `key` | `str` | `"coco_app_viewer"` | Widget key namespace |
| `port` | `int \| None` | `None` | First free port from 8511–8520 if unset |
| `address` | `str` | `"127.0.0.1"` | Bind address for the preview process |
| `env` | `dict \| None` | `None` | Extra environment variables for the child process |
| `iframe_height` | `int` | `520` | Preview iframe height in pixels |
| `show_fix` | `bool` | `True` | Show the "Fix with CoCo" action |
| `on_fix` | `Callable[[str], None] \| None` | `None` | Callback receiving the fix prompt |
| `on_close` | `Callable \| None` | `None` | Callback when the preview closes |
| `title_extra` | `str \| None` | `None` | Extra text appended to the title |
| `title` | `str` | `"Preview"` | Panel title |
| `script_name` | `str` | `"streamlit_app.py"` | Entry-point filename inside `app_dir` |

Streamlit-free helper functions: `start_app_preview`, `stop_app_preview`,
`preview_running`, `preview_url`, `last_preview_exception`,
`preview_log_tail`, `default_fix_prompt(traceback, app_dir) -> str`.

```python
st_coco.app_viewer("examples/app_builder/out/my-app", title="Preview")
```

Used by: [I want to run the example apps](task-run-the-example-apps.html)

### `chat_input_bar(session, *, placeholder=…, connecting_placeholder=…, key=None, accept_file=False, …) -> str | None`

The chat input bar, with optional file attachment.

| Parameter | Type | Default | Effect |
|---|---|---|---|
| `accept_file` | `bool \| str` | `False` | `True` or `"multiple"` to accept uploads |
| `file_type` | `list[str] \| None` | `None` | Restrict accepted extensions |
| `max_upload_size` | `int \| None` | `None` | Override the default max upload size |
| `upload_subdir` | `str` | `"_uploads"` | Subdirectory of `cwd` uploads are written to |
| `upload_overwrite` | `str` | `"replace"` | `"error"` / `"replace"` / `"skip"` |
| `inject_upload_paths` | `bool` | `True` | Append uploaded file paths to the prompt text |

```python
prompt = st_coco.chat_input_bar(session, accept_file=True, upload_overwrite="replace")
```

Used by: [I want to add file uploads](task-add-file-uploads.html)

## Upload helpers

### `upload_to_cwd(target, files, *, subdir="_uploads", overwrite="error", max_bytes=DEFAULT_MAX_BYTES, allowed_extensions=DEFAULT_ALLOWED_EXTENSIONS) -> list[UploadedPath]`

Writes uploaded files into a session's, options', or path's working
directory. `target` may be a path, a `CocoOptions`, or a `CocoSession`.
Raises `CwdUploadError` on a bad filename (path-traversal guard), a
disallowed extension, an oversize payload, or an overwrite conflict.

```python
paths = st_coco.upload_to_cwd(session, files, overwrite="error")
```

Used by: [I want to add file uploads](task-add-file-uploads.html)

### `cwd_uploader(target, *, label=…, overwrite="error", …) -> list[UploadedPath]`

A sidebar/chrome `st.file_uploader` wired to `upload_to_cwd()`, with an
inventory caption of files already uploaded.

```python
uploaded = st_coco.cwd_uploader(session, label="Upload a reference file")
```

Used by: [I want to add file uploads](task-add-file-uploads.html)

### Upload constants (`streamlit_coco/upload.py`)

| Name | Type | Default | Effect |
|---|---|---|---|
| `DEFAULT_UPLOAD_SUBDIR` | `str` | `"_uploads"` | Default upload subdirectory name |
| `DEFAULT_MAX_BYTES` | `int` | `10 * 1024 * 1024` (10 MiB) | Default per-file size limit |
| `DEFAULT_ALLOWED_EXTENSIONS` | `frozenset[str]` | a fixed allowlist | Default allowed file extensions; read the source constant for the exact list rather than assuming one |

Used by: [I want to add file uploads](task-add-file-uploads.html)

## Approvals and prompting

### `send_prompt(session, prompt) -> None`

Strips and queues a prompt on a session; surfaces any `CocoError` via
`st.error` instead of raising into the page.

```python
st_coco.send_prompt(session, "Summarize this sprint.")
```

Used by: [I want to build a minimal CoCo app](task-build-a-minimal-app.html)

### `render_approvals(session, *, key_prefix="coco") -> bool`

Renders the HITL approval UI for a pending request. Button order: **Approve
once** · **Always allow** · **Deny**. `AskUserQuestion` and `ExitPlanMode`
requests never show **Always allow**.

```python
st_coco.render_approvals(session, key_prefix="coco")
```

Used by: [I want to configure tool approvals](task-configure-tool-approvals.html)

### `render_plan_banner(session, …) -> bool`

Renders the plan-mode banner with an **Execute plan** call to action.

```python
st_coco.render_plan_banner(session)
```

Used by: [I want to configure tool approvals](task-configure-tool-approvals.html)

### `approve_pending(session, request_id, *, always=False, updated_input=None)` / `deny_pending(session, request_id, *, reason=None)`

Low-level resolvers for a pending approval, for custom approval UIs.

```python
st_coco.approve_pending(session, request_id, always=False)
st_coco.deny_pending(session, request_id, reason="not now")
```

Used by: [I want to configure tool approvals](task-configure-tool-approvals.html)

## Display helpers

| Function | Effect |
|---|---|
| `render_transcript(session, …, text_renderer=None)` | Render the transcript standalone (what `panel()` uses internally) |
| `render_output_field(session, …, text_renderer=None)` | Render only the latest output field |
| `render_session_status(session, …)` | Render the status/connect chrome standalone |
| `get_latest_assistant_text(session) -> str` | Return the latest assistant text as a plain string |

```python
latest = st_coco.get_latest_assistant_text(session)
```

Used by: [Concepts](concepts.html#the-transcript)

## Bootstrap and gate

### `render_environment_status(env=None, *, connection=None, toml_file=None, stacked=False, show_title=True)`

Renders the SDK/CLI/Snowflake-config status block, given a `CocoEnvironment`
(or probing one itself if `env` is omitted).

```python
st_coco.render_environment_status(connection="my_connection")
```

Used by: [Getting started](getting-started.html)

### `render_start_gate(options, *, session_key=…, gate_key=…, warm_up=True, env=None) -> bool`

Renders the landing screen (environment status plus a **Start** action) and
returns `False` while the environment is not ready or the user has not
confirmed. The caller must call `st.stop()` on `False` — the gate does not
stop the script itself.

```python
if not st_coco.render_start_gate(options):
    st.stop()
```

Used by: [I want to build a minimal CoCo app](task-build-a-minimal-app.html)

## Legacy CCv2

### `chat(**kwargs) -> CocoChatResult`

An all-in-one Custom Component v2 widget with a built-in input, predating
`panel()`. Prefer `panel()` for new apps. Notable parameters: `session` /
`options`, `key`, `height`, `placeholder`, `use_fragment`, `run_every`,
`output_mode`, `on_structured_output`, and optional `on_event` / submit /
approval / cancel callbacks.

```python
result = st_coco.chat(options=options, key="legacy")
```

Used by: [I want to run the example apps](task-run-the-example-apps.html)

### `request_input(question, *, key="coco_input", default="", schema=None, …) -> str | dict | None`

An app-owned clarification form shown between turns — not a CCv2 channel.
Returns a `dict` when `schema=` is given, otherwise a `str` (or `None` if
unanswered).

```python
answer = st_coco.request_input("Which environment?", schema={"type": "string"})
```

Used by: [Example apps reference](reference-examples.html)

## Headless

### `async query(prompt, *, options=None, output_schema=None) -> AsyncIterator[CocoEvent]`

A single-turn wrapper that runs without any session object or Streamlit
import. Raises `SDKNotInstalledError`, `QueryError`, or another `CocoError`
subclass on failure.

```python
async for event in st_coco.query("List the tables in my schema.", options=options):
    ...
```

Used by: [I want to run CoCo headless](task-run-headless.html)

### `events_to_dataframe(events) -> DataFrame`

Flattens a list of `CocoEvent` into a pandas `DataFrame` (requires pandas
installed).

```python
df = st_coco.events_to_dataframe(session.events)
```

Used by: [I want to run CoCo headless](task-run-headless.html)

## `CocoEvent`

A normalized, JSON-serializable unit of agent activity
(`streamlit_coco/messages.py`), with `to_dict()` / `from_dict()` for storage
or transport.

| Field | Effect |
|---|---|
| `type` | One of `assistant_text`, `stream_event`, `thinking`, `tool_use`, `tool_result`, `permission_request`, `result`, `system`, `error` |
| `text` / `delta` | Text content or streamed delta |
| `name` / `tool_use_id` / `tool_name` / `tool_input` / `input` | Tool-call identification and arguments |
| `content` / `is_error` | Tool result content and error flag |
| `request_id` | Identifies a pending approval request |
| `subtype` / `duration_ms` / `cost_usd` | Result metadata |
| `structured_output` | The structured payload, when present |
| `message` / `code` / `metadata` | Error/system detail |

```python
event = st_coco.CocoEvent.from_dict(raw)
event.to_dict()
```

Used by: [Concepts](concepts.html#cocoevent)

## Environment and errors

### `check_environment(*, connection=None, cli_path=None, toml_file=None) -> CocoEnvironment`

Probes the SDK, CLI and Snowflake config. Never raises.

| Field / property | Effect |
|---|---|
| `sdk_installed` / `sdk_version` | Whether the SDK is importable, and its version |
| `cli_path` / `cli_version` | The resolved CLI path and its reported version |
| `snowflake_config_file` / `connection_hint` / `toml_file` | Snowflake config resolution detail |
| `ready` | `True` when everything needed to start a session is present |
| `cli_ok` | `True` when the CLI probed successfully |
| `snowflake_config_found` / `snowflake_config_display` / `snowflake_config_missing_label` | Snowflake config presence and display text |

```python
env = st_coco.check_environment(connection="my_connection")
```

Used by: [Getting started](getting-started.html)

### `require_environment(*, connection=None, cli_path=None, toml_file=None, require_snowflake_config=False) -> CocoEnvironment`

Like `check_environment()`, but raises a typed error instead of returning a
not-ready result.

```python
env = st_coco.require_environment(connection="my_connection", require_snowflake_config=True)
```

Used by: [Getting started](getting-started.html)

### Snowflake config helpers

| Function | Effect |
|---|---|
| `list_snowflake_toml_files() -> list[Path]` | `*.toml` files under `~/.snowflake/`, `connections.toml`/`config.toml` first |
| `list_snowflake_connections(toml_file=None) -> list[str]` | Profile names; legacy `config.toml` reads `[connections]`, other files read top-level tables |
| `resolve_snowflake_config_path(toml_file=None, *, must_exist=True)` | Resolves a bare filename or path to a config file under `~/.snowflake/` |
| `default_snowflake_connection_name(toml_file=None)` | The connection name used when none is given |

```python
files = st_coco.list_snowflake_toml_files()
```

Used by: [Getting started](getting-started.html)

### Exception hierarchy (`streamlit_coco/errors.py`)

| Class | Raised when | Message |
|---|---|---|
| `CocoError` | Base class for every exception below | — |
| `SDKNotInstalledError` (also `ImportError`) | The SDK is not installed | `cortex-code-agent-sdk is required. Install with: pip install streamlit-coco[sdk]` |
| `CLINotFoundError` | The `cortex` CLI is not on `PATH` | `CoCo CLI not found on PATH... or set CORTEX_CODE_CLI_PATH.` (or `not found at {cli_path!r}`) |
| `CLIProbeError` | The CLI binary exists but does not answer `--version` | `CoCo CLI at {cli_path!r} did not respond to --version` |
| `SnowflakeConfigNotFoundError` | No Snowflake config file found | `No Snowflake config found. Create ~/.snowflake/connections.toml (or legacy config.toml)...` |
| `CocoConnectionError` | Bad connection name or auth failure | — |
| `SessionStartError` | The background worker failed to start | — |
| `SessionNotReadyError` | The session is not ready (connect timeout / boot failure) | — |
| `ApprovalTimeoutError` (also `TimeoutError`) | No approval response within `approval_timeout_seconds` | `Approval timed out for tool {tool_name}` |
| `QueryError` | A headless `query()` call failed | — |
| `CwdUploadError` | An upload failed (size / extension / path / overwrite) | — |

`wrap_exception()` maps raw SDK/runtime exceptions to these by message and a
`context=` kwarg (`"session_start"`, `"session_ready"`/`"session"`,
`"query"`, `"approval"`).

```python
try:
    env = st_coco.require_environment(connection="my_connection")
except st_coco.SDKNotInstalledError:
    st.error("Install the SDK: pip install streamlit-coco[sdk]")
```

Used by: [FAQ](faq.html)

## Tool helpers

| Function | Effect |
|---|---|
| `tool_family(name)` | Maps a tool name to its family enum, for tool-card display |
| `is_sql_tool(name)` | `True` for the SQL tool |
| `is_ask_user_question(name)` | `True` for `AskUserQuestion` |
| `is_exit_plan_mode(name)` | `True` for `ExitPlanMode` |
| `is_debug_mode(*, session_state=None)` | `True` when `STREAMLIT_COCO_DEBUG` or `COCO_DEBUG` is truthy (`1`/`true`/`yes`/`on`, case-insensitive), or `st.session_state["coco_debug"]` is truthy |

```python
if st_coco.is_debug_mode():
    st.caption("Debug mode is on.")
```

Used by: [FAQ](faq.html)

## Package metadata

`st_coco.__version__` — the installed package version, for example `"0.1.9"`.

```python
import streamlit_coco as st_coco
print(st_coco.__version__)
```

Used by: [Getting started](getting-started.html)
