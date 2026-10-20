# Concepts

The objects a `streamlit-coco` user handles directly, what they represent,
their states, and where each one lives in code.

## `CocoOptions`

Configuration for a CoCo session: connection, working directory, model,
allowed/disallowed tools, permission mode, approval rules, output schema,
turn limit, and SDK passthrough. It is a plain dataclass
(`streamlit_coco/options.py`) — create one, pass it to `get_or_create_session`
or `query()`, and mutate it (a new instance, not in place) when settings
change.

`CocoOptions` has no lifecycle of its own: it is a value object. Its
`options_hash()` is what a session compares against to decide whether it must
restart its background worker — changing `permission_mode` or `allowed_tools`
between reruns and calling `sync_options()` triggers a restart if the hash
differs.

Touched by every task page in this guide; the full field table is in
[API reference](reference-api.html).

## `CocoSession`

A multi-turn conversation with the agent, backed by a
`CortexCodeSDKClient` running on a background thread
(`streamlit_coco/session.py`). One session survives across Streamlit reruns
when stored in `st.session_state` via `get_or_create_session()`.

Lifecycle: created idle → `start()` connects the background worker →
`send()`/`run()`/`stream()` drive turns → `reset()` clears the transcript and
restarts the worker → `close()` tears the worker down. A session is looked up
by its `key` through `get_session(key)`, and torn down explicitly with
`stop_session()`.

## `CocoRunStatus`

The state a session (and the UI built on it) is in, as a string enum:
`idle` → `connecting` → `ready` → `running` → `awaiting_user` → `completed` /
`error` / `cancelled`. `awaiting_user` means a tool call is paused on a
pending approval; the UI shows the approval controls and stops polling for
new agent output until it resolves. `panel()` and the other display helpers
read this status to decide what chrome to show (status skeleton, Stop
button, input disabled state).

## `CocoEvent`

One normalized, JSON-serializable unit of agent activity
(`streamlit_coco/messages.py`), with `to_dict()`/`from_dict()` for storage or
transport. Common `type` values: `assistant_text`, `stream_event`,
`thinking`, `tool_use`, `tool_result`, `permission_request`, `result`,
`system`, `error`. A session accumulates events in `session.events`; the
transcript UI and `events_to_dataframe()` both consume the same event stream.
Events do not have a lifecycle beyond being appended — each one is a fact
about something that already happened.

## `CocoChatResult`

The return value of `panel()` and `chat()` (legacy CCv2): a snapshot of one
turn's outcome — `last_prompt`, `last_result`, `pending_approval`,
`structured_output`, `events`, and `status`. It is recomputed on every
rerun via `session.chat_result()`; nothing is mutated on it directly.

## `CocoEnvironment`

The result of `check_environment()`: whether the SDK is installed, the CLI
path and version, and whether a Snowflake config was found, plus the fields
needed to render that state (`connection_hint`, `toml_file`,
`snowflake_config_display`). `check_environment()` never raises — it always
returns a `CocoEnvironment`, so a caller can render a diagnostic screen
either way. `require_environment()` performs the same probe but raises a
typed error (see [API reference](reference-api.html)) instead of returning a
not-ready result, for code paths that should stop hard.

## The approval / permission model

Every tool call the agent wants to make is either auto-allowed (in
`CocoOptions.allowed_tools`, or matched by `permission_mode`) or paused for a
human decision, per `require_approval_for` (a list of tool names, or a
callable). `AskUserQuestion` and `ExitPlanMode` always pause regardless of
that configuration. A paused call becomes a pending approval on the session;
it is resolved with one of three outcomes — **Approve once**, **Always
allow**, or **Deny** — either through the `render_approvals()` UI inside
`panel()`, or programmatically with `approve_pending()` / `deny_pending()`.
"Always allow" is scoped to the current session only: it is cleared on
`reset()` or process restart, never written to a persisted policy. See
[I want to configure tool approvals](task-configure-tool-approvals.html).

## The transcript

The ordered sequence of turns and events a session has produced, as rendered
by `render_transcript()` (used inside `panel()` in `output_mode="transcript"`)
or read back via `session.transcript` / `session.messages`. Display-only
parameters (`max_messages`, `preview_chars`, `text_renderer`) control how much
of it is shown and how, without changing what is stored — "Load earlier"
reveals more of the same underlying transcript, it does not fetch anything
new.

## Glossary

| Term | Definition |
|------|------------|
| `CocoOptions` | Configuration value object for a session or a `query()` call |
| `CocoSession` | A multi-turn conversation, backed by a background SDK worker thread |
| `CocoRunStatus` | The session's current state (`idle` … `completed`/`error`/`cancelled`) |
| `CocoEvent` | One normalized unit of agent activity (assistant text, tool use, result, …) |
| `CocoChatResult` | Snapshot of one turn's outcome, returned by `panel()`/`chat()` |
| `CocoEnvironment` | Result of an environment probe (SDK/CLI/Snowflake config readiness) |
| Approval gate | The pause-and-resolve flow for a tool call matched by `require_approval_for` |
| "Always allow" | A session-scoped (not persisted) approval that skips future prompts for that tool |
| Transcript | The ordered turn/event history of a session |
| `cwd` | The working directory the agent's tools operate in (`CocoOptions.cwd`) |
| Headless | Running `query()` or `CocoSession` without any Streamlit UI |
