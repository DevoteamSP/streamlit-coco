# Help

By area and symptom. Every heading below carries a stable `{#anchor}` that
other pages link to as `help.html#<anchor>`.

## Environment and connection

### SDK not installed {#sdk-not-installed}

**You see:** `cortex-code-agent-sdk is required. Install with: pip install streamlit-coco[sdk]`
**Likely cause:** `streamlit-coco` was installed without the `[sdk]` extra, so `cortex_code_agent_sdk` is not importable.
**Diagnose:** `python -c "import cortex_code_agent_sdk"`
**Fix:** `pip install "streamlit-coco[sdk]"` (or `make install`, which runs `uv sync --extra dev`).
**If that fails:** confirm the active Python environment is the one Streamlit is actually run from (`which python`, `which streamlit`); a second virtualenv with the SDK installed does not help if the app runs in a different one.

### CoCo CLI not found {#cli-not-found}

**You see:** `CoCo CLI not found on PATH. Install the cortex CLI and ensure `cortex --version` works, or set CORTEX_CODE_CLI_PATH.` (or, when `cli_path` was passed explicitly, `CoCo CLI not found at '<path>'`)
**Likely cause:** the `cortex` binary is not installed, or is installed somewhere not on `PATH`.
**Diagnose:** `cortex --version`; `echo $CORTEX_CODE_CLI_PATH`.
**Fix:** install the CoCo CLI, or set `export CORTEX_CODE_CLI_PATH=/path/to/cortex`, or pass `cli_path=` on `CocoOptions` (see [configuration](sections/configuration.html)).
**If that fails:** check the CLI installation location matches what the shell that launches Streamlit actually sees — a CLI installed under a different user profile or shell will not be on `PATH` for the Streamlit process.

### CLI probe failed {#cli-probe-failed}

**You see:** `CoCo CLI at '<path>' did not respond to --version`
**Likely cause:** a binary exists at the resolved path but is not a working `cortex` CLI (wrong file, broken install, or permissions).
**Diagnose:** run `cortex --version` manually and check both the exit code and the output; `ls -l "$(which cortex)"` to check permissions.
**Fix:** reinstall the CLI; fix executable permissions (`chmod +x`) if needed.
**If that fails:** ask the CLI's maintainer/owner for a known-good binary and compare checksums.

### Snowflake config not found {#snowflake-config-not-found}

**You see:** `No Snowflake config found. Create ~/.snowflake/connections.toml (or legacy config.toml) with an authenticated connection.`
**Likely cause:** no `*.toml` file exists under `~/.snowflake/`.
**Diagnose:** `ls ~/.snowflake/*.toml`, or `st_coco.list_snowflake_toml_files()`.
**Fix:** create `~/.snowflake/connections.toml` with at least one `[connections.<name>]` entry — see [configuration](sections/configuration.html) for the shape.
**If that fails:** confirm `HOME` resolves to the expected directory in the environment running Streamlit (containers and service accounts sometimes have a different `HOME`).

### CoCo connection error {#coco-connection-error}

**You see:** a `CocoConnectionError` message — the underlying text names the connection or an auth failure (e.g. "connection not found," "unknown connection," or another auth/connection failure).
**Likely cause:** the connection name passed to `CocoOptions(connection=...)` does not match any profile in the resolved TOML file, or the profile's credentials are stale/invalid.
**Diagnose:** `st_coco.list_snowflake_connections(toml_file=...)` to list known profile names; test the same connection with the Snowflake CLI directly.
**Fix:** correct the connection name, or fix the profile's `account`/`user`/`authenticator` fields in `connections.toml`.
**If that fails:** confirm the account identifier and authenticator match what your Snowflake admin issued; re-run the external-browser or key-pair auth flow outside streamlit-coco first to isolate whether the problem is the connection file or the credential itself.

## Session lifecycle

### Session stuck on "Starting CoCo…" {#session-stuck-connecting}

**You see:** the panel/rail status stays on "Starting CoCo…" and never reaches ready.
**Likely cause:** a CLI or network issue during connect (the CLI subprocess never returns a ready signal).
**Diagnose:** check the terminal running Streamlit for CLI errors; enable debug output with `STREAMLIT_COCO_DEBUG=1` (see [debug-mode-not-showing-payloads](#debug-mode-not-showing-payloads)).
**Fix:** fix the underlying environment problem (CLI/connection — see the Environment and connection entries above), then reset the session.
**If that fails:** capture the terminal output and file it against the CLI/SDK, since the failure is happening below the library's own error mapping.

### Session not ready {#session-not-ready}

**You see:** a `SessionNotReadyError`, or the session status shows `error`.
**Likely cause:** connect timeout or boot failure — `ensure_ready(timeout=120)` gave up, or the worker reported a boot failure.
**Diagnose:** check `session.last_error` and `session.init_info`; check `render_session_status()` output in the UI.
**Fix:** fix the environment issue `last_error` points at, then call `reset_session(...)` (or use the sidebar/start-gate reset action) to restart the session.
**If that fails:** re-run `check_environment()` standalone to confirm SDK/CLI/Snowflake status outside of a live session before retrying.

### Input disabled after boot {#input-disabled-after-boot}

**You see:** the chat input stays disabled even after the start gate says the session started.
**Likely cause:** the session ended up in `SessionNotReadyError` / `ERROR` status right after boot (same underlying cause as [session-not-ready](#session-not-ready)).
**Diagnose:** check the session status badge / `render_session_status()`.
**Fix:** fix the environment, then reset the session from the sidebar (`stop_session()` followed by restarting the start gate).
**If that fails:** see [session-not-ready](#session-not-ready)'s escalation step.

## Approvals

### Approval timed out {#approval-timeout}

**You see:** `Approval timed out for tool <tool_name>` (`ApprovalTimeoutError`).
**Likely cause:** no one resolved the pending approval within `CocoOptions.approval_timeout_seconds` (default `600.0`, 10 minutes).
**Diagnose:** confirm `show_approvals=True` was passed to `panel()`/`copilot_rail()` so the approval UI was actually rendered; check whether the approval buttons were reachable (not covered by another dialog).
**Fix:** respond within the window next time, or raise `approval_timeout_seconds` for sessions that expect longer human review, then resend the prompt.
**If that fails:** call `approve_pending()` / `deny_pending()` directly against the session for a custom approval UI that does not rely on `render_approvals()`'s default timing.

### "Always allow" does not persist {#always-allow-scope}

**You see:** a tool that was "Always allowed" earlier prompts for approval again after a session reset or app restart.
**Likely cause:** this is expected. `PermissionManager.always_allowed_tools` is an in-memory set on the live `CocoSession`; it is never written to disk and is cleared by `session.reset()`, `session.close()`, and process restart.
**Diagnose:** check whether a reset/restart happened between the two approvals (sidebar reset, `stop_session()`, or a page reload that created a new session).
**Fix:** click **Always allow** again in the new session; there is no way to make "Always allow" survive a reset, by design (see [security](sections/security.html)).
**If that fails:** if durable per-tool policy across sessions is required, that is not implemented today — track it against SEC-01 in [limits](sections/limits.html) rather than looking for a hidden setting.

## File uploads

### Upload rejected: extension {#upload-rejected-extension}

**You see:** `Disallowed file extension for '<name>' (allowed: <list>)` (`CwdUploadError`).
**Likely cause:** the uploaded file's suffix is not in `DEFAULT_ALLOWED_EXTENSIONS` (or a caller-supplied `allowed_extensions`).
**Diagnose:** compare the file's extension against the allowlist constant in `streamlit_coco/upload.py`.
**Fix:** convert/rename the file to an allowed type, or call `upload_to_cwd(..., allowed_extensions={...})` with a wider allowlist for that app.
**If that fails:** confirm the file actually needs to reach the agent's `cwd` at all — some workflows only need the agent to be told the content, not the raw file.

### Upload rejected: size {#upload-rejected-size}

**You see:** `File '<name>' is <n> bytes; max allowed is <max_bytes>` (`CwdUploadError`).
**Likely cause:** the file exceeds `DEFAULT_MAX_BYTES` (10 MiB) or a caller-supplied `max_bytes`.
**Diagnose:** check the file's actual size against the configured limit.
**Fix:** split or compress the file, or call `upload_to_cwd(..., max_bytes=...)` with a higher limit for that app.
**If that fails:** consider whether the file belongs in a Snowflake stage instead of the local `cwd` quarantine — large datasets are explicitly out of scope for this upload path (see `doc/features/file-upload/file-upload.md`).

### Upload name conflict {#upload-name-conflict}

**You see:** `File already exists: <relative path> (pass overwrite='replace' or 'skip')` (`CwdUploadError`).
**Likely cause:** `overwrite="error"` (the `upload_to_cwd` default) and a file with the same sanitized name already exists under the upload subdirectory.
**Diagnose:** list the upload directory (`list_cwd_uploads(target)`) to see the existing file.
**Fix:** pass `overwrite="replace"` or `overwrite="skip"` to `upload_to_cwd()` / `cwd_uploader()`, or rename the file before uploading. Note `chat_input_bar(accept_file=...)` already defaults `upload_overwrite="replace"`, so this mainly surfaces through direct `upload_to_cwd()` calls or a `cwd_uploader()` configured with `overwrite="error"`.
**If that fails:** if collisions are expected and should always win, switch the caller's default overwrite mode rather than handling each conflict manually.

## App preview

### Preview won't start {#preview-wont-start}

**You see:** clicking **Run** in `app_viewer()` produces no iframe and no reachable URL.
**Likely cause:** the free-port range (`8511`–`8520`) is exhausted, `app_dir` has no `streamlit_app.py` (or a different `script_name`), or a stale preview process for the same `app_dir` is already holding the port.
**Diagnose:** check `preview_running(app_dir)` / `preview_url(app_dir)`; check `.preview.log`, `.preview.pid`, `.preview.port` inside `app_dir`; check `last_preview_exception(app_dir)`.
**Fix:** call `stop_app_preview(app_dir)` to clear a stale process, confirm `app_dir` actually contains `streamlit_app.py`, then **Run** again.
**If that fails:** free up the `8511`–`8520` port range on the host (another preview or unrelated process may be holding it), and confirm only one `app_viewer()` targets this `app_dir` (see [limits](sections/limits.html)).

### "Fix with CoCo" is not wired {#fix-with-coco-not-wired}

**You see:** clicking **Fix with CoCo** does nothing, or shows a toast asking to "wire `on_fix=`".
**Likely cause:** the host app called `app_viewer()` without an `on_fix=` callback. `app_viewer()` does not queue a job on its own — it only builds the prompt via `default_fix_prompt()`.
**Diagnose:** check the `app_viewer(...)` call for `on_fix=`.
**Fix:** pass `on_fix=<callback>` that queues `default_fix_prompt(traceback, app_dir)` as a job on the host's own Copilot session and opens the Copilot rail — see `doc/features/app-viewer/app-viewer.md` for the reference pattern.
**If that fails:** confirm the host actually composes `copilot_rail()` alongside `app_viewer()` — `app_viewer()` deliberately does not import or know about `copilot_rail()` (see [architecture](sections/architecture.html)).

### Preview log parse miss {#preview-log-parse-miss}

**You see:** the child app is visibly broken, but the **Preview exception** expander does not show a traceback.
**Likely cause:** log-format drift. The parser looks for the literal markers `Uncaught app exception` and `Traceback (most recent call last):` in `.preview.log`, and treats any later timestamped line as "error cleared" — a log that does not match those markers, or that logs a later unrelated line, reads as cleared even though the app is still broken.
**Diagnose:** read `.preview.log` directly (or `preview_log_tail(app_dir)`) rather than relying on the expander.
**Fix:** click **Fix with CoCo** anyway — it still sends the log tail as part of the prompt even when the parser did not detect a live exception.
**If that fails:** copy the relevant log lines into a manual prompt to CoCo, since the automatic markers do not cover this log shape.

## Structured output

### Structured output not rendering {#structured-output-not-rendering}

**You see:** the agent's reply is JSON-shaped, but no structured panel or callback-driven widget appears.
**Likely cause:** one of two things — either `on_structured_output` / `structured_output_container` was set, which intentionally skips the default inline structured panel (mutual exclusivity), or `CocoOptions.output_schema` was never set, so the agent was not actually constrained to produce a schema-conformant `structured_output` payload even if the reply text looks like JSON.
**Diagnose:** check `session.chat_result().structured_output` after the turn; check whether `on_structured_output=` or `structured_output_container=` was passed to `panel()` / `copilot_rail()`.
**Fix:** set `CocoOptions.output_schema={...}` so the SDK enforces `output_format`, and either rely on the default inline panel (no callback/container set) or read `structured_output` from the callback.
**If that fails:** confirm the reply is coming from a turn that actually ran with the schema-carrying `CocoOptions` — a session created before the schema was added keeps its original worker until `options_hash()` changes (see [architecture](sections/architecture.html)).

### `$schema` / `$id` rejected {#schema-dollar-schema-rejected}

**You see:** `no schema with key or ref "https://json-schema.org/draft/2020-12/schema"`.
**Likely cause:** a JSON Schema contract file (such as the ones under `examples/bi_to_semantic/contracts/`) includes a `$schema` (or `$id`) key, and this was passed straight through to the SDK without stripping it — the SDK's schema resolver tries to fetch that URI and fails.
**Diagnose:** check the version of `streamlit-coco` in use; check whether `output_schema` is built by hand-merging a contract file after construction (which could re-add `$schema`).
**Fix:** upgrade to `>=0.1.6` — `CocoOptions.to_sdk_options()` now strips `$schema`/`$id` automatically (`_schema_for_sdk()` in `streamlit_coco/options.py`) before forwarding the schema to the SDK.
**If that fails:** if still on `>=0.1.6` and the error persists, confirm nothing downstream re-inserts `$schema` into the dict passed as `output_schema` after `CocoOptions` construction.

## Release and CI

### `pip-audit` false positive on the editable package {#pip-audit-editable-false-positive}

**You see:** `pip-audit` reports `streamlit-coco … Dependency not found on PyPI and could not be audited (<version>)`.
**Likely cause:** running plain `pip-audit` against a pre-tag or editable install of `streamlit-coco` itself, which is not yet published at that version.
**Diagnose:** check which command was run — `pip-audit` alone will surface this; `make audit` / `pip-audit --skip-editable` will not.
**Fix:** use `make audit` (or `pip-audit --skip-editable` directly) — this was fixed in `0.1.7` for both the Makefile target and CI so a pre-tag version bump is not reported as a false-positive audit failure.
**If that fails:** if the same message appears with `--skip-editable` already set, treat it as a real audit gap and file it rather than assuming it is this known false positive.

## Debug mode

### Debug mode not showing payloads {#debug-mode-not-showing-payloads}

**You see:** `STREAMLIT_COCO_DEBUG` (or `COCO_DEBUG`) was set, but no "Raw tool payload" section appears in the transcript.
**Likely cause:** the value is not one of the recognized truthy strings (`"1"`, `"true"`, `"yes"`, `"on"`, case-insensitive), or the variable was exported in a different shell/process than the one running Streamlit.
**Diagnose:** `echo $STREAMLIT_COCO_DEBUG` in the exact shell that launches `streamlit run`; confirm `is_debug_mode()`'s truthy set matches the value used.
**Fix:** `export STREAMLIT_COCO_DEBUG=1` (or `COCO_DEBUG=1`) before starting Streamlit in that same shell, or set `st.session_state["coco_debug"] = True` inside the app for a UI-driven toggle.
**If that fails:** confirm the Streamlit process was actually restarted after setting the variable — env vars are read at call time by `is_debug_mode()`, but a process started before the export was set in its own shell will not see it.

## App Builder

### App Builder brief overwrite race {#app-builder-brief-overwrite-race}

**You see:** edits made in the Studio **App brief** expander appear to be lost, or a **Save & regenerate** run uses a stale brief.
**Likely cause:** before `0.1.8`, **Save & regenerate** could queue CoCo before `BRIEF.md` was written from the expander's current field values, and the Brief page could overwrite `BRIEF.md` again on the same turn — a race between the two writes.
**Diagnose:** check the installed version (`streamlit_coco.__version__`).
**Fix:** upgrade to `>=0.1.8` — **Save & regenerate** now writes `BRIEF.md` from the expander widgets before queuing CoCo, and the Brief page no longer overwrites that file on the same turn.
**If that fails:** if still seeing this on `>=0.1.8`, capture the exact sequence of clicks (which page, which button, in what order) and file it — the ordering fix targeted the specific Save & regenerate path, not every possible concurrent-edit sequence.
