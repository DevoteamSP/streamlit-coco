# Configuration

Every configuration surface streamlit-coco exposes: `CocoOptions` fields,
environment variables, and the Snowflake connections file it reads.

## `CocoOptions` fields

`CocoOptions` (`streamlit_coco/options.py`) is a dataclass. All fields are
keyword-settable; there is no config file for the library itself — an app
builds one `CocoOptions` instance in code.

| Name | Type | Default | Effect | Example |
|---|---|---|---|---|
| `connection` | `str \| None` | `None` | Snowflake CLI connection name to use. `None` uses the CLI's default connection. | `CocoOptions(connection="analytics")` |
| `cwd` | `str` | `"."` | Working directory the agent's tools (Read/Write/Bash/…) operate in. | `CocoOptions(cwd="./workspace")` |
| `model` | `str \| None` | `None` | Model identifier passed to the SDK. Prefer `"auto"` when set explicitly. | `CocoOptions(model="auto")` |
| `allowed_tools` | `list[str]` | `[]` | Tools that may run without an approval prompt when list-based approval is in effect. | `CocoOptions(allowed_tools=["Read", "Glob", "Grep"])` |
| `disallowed_tools` | `list[str]` | `[]` | Tools blocked outright, regardless of approval. | `CocoOptions(disallowed_tools=["Bash"])` |
| `permission_mode` | `str` | `"default"` | SDK permission mode, e.g. `"plan"` for `ExitPlanMode` flows. | `CocoOptions(permission_mode="plan")` |
| `profile` | `str \| None` | `None` | SDK profile name. | `CocoOptions(profile="ci")` |
| `cli_path` | `str \| None` | `None` | Override path to the `cortex` CLI binary. Same effect as `CORTEX_CODE_CLI_PATH`; this field takes precedence when both are set. | `CocoOptions(cli_path="/opt/cortex/bin/cortex")` |
| `mcp_servers` | `dict` | `{}` | MCP server configuration forwarded to the SDK. | `CocoOptions(mcp_servers={"docs": {...}})` |
| `hooks` | `dict` | `{}` | SDK hook configuration. | `CocoOptions(hooks={})` |
| `require_approval_for` | `list[str] \| Callable` | `[]` | Tools that pause for human-in-the-loop approval. `AskUserQuestion` and `ExitPlanMode` always prompt regardless of this list. A callable receives `(tool_name, tool_input, context)` and returns `bool`. | `CocoOptions(require_approval_for=["Edit", "Write", "Bash"])` |
| `output_schema` | `dict \| None` | `None` | JSON Schema forwarded to the SDK as `output_format`. The library strips `$schema` / `$id` before passing it on (see [help.html#schema-dollar-schema-rejected](../help.html#schema-dollar-schema-rejected)). | `CocoOptions(output_schema={"type": "object", "properties": {...}})` |
| `max_turns` | `int \| None` | `None` | Caps the number of agent turns in a run. | `CocoOptions(max_turns=10)` |
| `approval_timeout_seconds` | `float` | `600.0` | Seconds to wait for a human-in-the-loop decision before raising `ApprovalTimeoutError`. | `CocoOptions(approval_timeout_seconds=120.0)` |
| `extra_sdk_options` | `dict` | `{}` | Passthrough kwargs merged into the SDK options, e.g. `add_dirs` for mounting extra directories (used by App Builder's `types/` skill packs). | `CocoOptions(extra_sdk_options={"add_dirs": ["/path/to/types/shared"]})` |

Two methods worth knowing when configuring a session:

- `options_hash()` — a stable hash over the fields that affect tool
  permissions. `CocoSession` restarts its background worker only when this
  hash changes between calls (see [architecture](architecture.html)).
- `to_sdk_options(*, can_use_tool=None)` — builds the SDK's
  `CortexCodeAgentOptions`; raises `SDKNotInstalledError` if
  `cortex-code-agent-sdk` is not installed.

## Environment variables

| Name | Type | Default | Effect | Example |
|---|---|---|---|---|
| `CORTEX_CODE_CLI_PATH` | path string | unset (falls back to `PATH` lookup) | Overrides the `cortex` CLI path used by diagnostics and option resolution when it is not on `PATH` and `CocoOptions.cli_path` is not set. | `export CORTEX_CODE_CLI_PATH=/opt/cortex/bin/cortex` |
| `STREAMLIT_COCO_DEBUG` | `"1"` / `"true"` / `"yes"` / `"on"` (case-insensitive) | unset / false | Shows raw tool request/response payloads in the transcript ("Raw tool payload"). Same effect as `COCO_DEBUG`; either one being truthy enables debug mode. | `export STREAMLIT_COCO_DEBUG=1` |
| `COCO_DEBUG` | same truthy set as above | unset / false | Alias for `STREAMLIT_COCO_DEBUG`. `is_debug_mode()` also checks `st.session_state["coco_debug"]` when no env var is set. | `export COCO_DEBUG=1` |
| `TTS_DATA_MODE` | string | `"disconnected"` when set by the example | Read only by the `examples/bi_to_semantic` generated consumer app (passed through `app_viewer(env=...)`), not by the library itself. Selects disconnected vs. connected data mode for that generated app. | `app_viewer(app_dir, env={"TTS_DATA_MODE": "disconnected"})` |

`is_debug_mode(*, session_state=None)` (`streamlit_coco/tool_names.py`
re-export, defined in `streamlit_coco/debug.py`) is the single source of
truth for whether debug UI is shown; it checks the two env vars first, then
`st.session_state["coco_debug"]`.

## Snowflake connection file

CoCo authenticates through the Snowflake CLI's own connection file, never
through library configuration:

- Default location: `~/.snowflake/connections.toml`.
- Legacy `~/.snowflake/config.toml` is also detected (its profiles live
  under a top-level `[connections]` table instead of `[connections.<name>]`
  entries at the root).
- `toml_file` resolution (used by `check_environment`, `copilot_rail`'s
  Config file selector, and `list_snowflake_connections`):
  - a bare filename is resolved under `~/.snowflake/`; a path is used as-is.
  - if omitted: when exactly one `*.toml` file exists under
    `~/.snowflake/`, that file is used regardless of its name; with several
    files present, `connections.toml` wins, then `config.toml`, then the
    remaining files alphabetically.

Example connection entry:

```toml
[connections.analytics]
account = "xy12345"
user = "you@company.com"
authenticator = "externalbrowser"
# warehouse, role, database, schema as needed — see security.html
```

Related helpers: `list_snowflake_toml_files()`, `list_snowflake_connections(toml_file=None)`,
`resolve_snowflake_config_path(toml_file=None, *, must_exist=True)`,
`default_snowflake_connection_name(toml_file=None)`. All live in
`streamlit_coco/diagnostics.py` and are exercised by `check_environment()` /
`require_environment()` — see [install](install.html) for the verification
flow and [help.html#snowflake-config-not-found](../help.html#snowflake-config-not-found)
when the probe fails.
