# streamlit-coco — Advanced certification

**Pass threshold: 24/30.** Prerequisite: ≥ 3 months of use.

### Q1. What did the `0.1.8` fix change about App Builder's Studio page?

a) "Save & regenerate" now writes `BRIEF.md` from the expander widgets before queuing CoCo, closing a race where the Brief page could overwrite the just-edited file on the same turn
b) The Brief page gained a new "Publish" button
c) `output_schema` stopped stripping `$schema`/`$id`
d) The App Builder preview port changed from 8513 to 8511

### Q2. What did the `0.1.7` fix change about `make audit` / CI `pip-audit`?

a) It switched from `pip-audit` to `safety`
b) It added `--skip-editable`, avoiding a false-positive "dependency not found on PyPI" failure right after a pre-tag version bump
c) It disabled `pip-audit` in CI entirely
d) It moved the audit job from `security.yml` into `release.yml`

### Q3. Which two things did the `0.1.6` fix address?

a) Added a new `output_schema` field and removed `on_structured_output`
b) Stripped `$schema`/`$id` before passing JSON Schema to the CoCo SDK, and replaced deprecated `use_container_width` with `width="stretch"`
c) Added `max_turns` and removed `approval_timeout_seconds`
d) Switched the structured-output example from `panel()` to `chat()`

### Q4. Which JSON Schema error did the `0.1.6` fix specifically avoid?

a) `no schema with key or ref "https://json-schema.org/draft/2020-12/schema"`, from a contract file that includes a draft URI
b) `KeyError: 'properties'`
c) `TypeError: schema must be a dict`
d) `ValidationError: additionalProperties not allowed`

### Q5. What changed in the `0.1.5` security workflow?

a) CodeQL was added for the first time
b) CodeQL was dropped (a private org needs a GHAS license); Gitleaks and pip-audit were kept
c) Gitleaks was replaced by the licensed `gitleaks-action@v2`
d) pip-audit was dropped in favor of a different scanner

### Q6. What did the `0.1.0` fix change about completed Grep/Glob tool cards?

a) They now show a compact summary instead of a full result dump
b) They now show raw JSON only
c) They were removed from the transcript entirely
d) They now require manual approval every time

### Q7. A session raises `SDKNotInstalledError`. What does this indicate, and what is the fix?

a) The CoCo CLI is not on `PATH`; set `CORTEX_CODE_CLI_PATH`
b) The Python SDK (`cortex-code-agent-sdk`) is missing; run `pip install streamlit-coco[sdk]` (or `make install`)
c) The Snowflake connection name is wrong; fix `connections.toml`
d) The approval timed out; increase `approval_timeout_seconds`

### Q8. A session raises `CLIProbeError`. What does this mean?

a) The `cortex` binary was not found anywhere on `PATH`
b) A binary exists at the configured path but did not respond correctly to `--version`
c) The Snowflake connection name does not exist in `connections.toml`
d) The Python SDK package is not installed

### Q9. A session is stuck on "Starting CoCo…" with no further progress. What is the recommended first diagnostic step?

a) Reinstall `streamlit-coco` from PyPI
b) Check terminal logs and enable debug mode (`STREAMLIT_COCO_DEBUG=1`)
c) Delete `~/.snowflake/connections.toml` and recreate it
d) Switch `permission_mode` to `"plan"`

### Q10. The chat input stays disabled right after the app boots. What is the likely cause and fix?

a) `SessionNotReadyError` / an error status — fix the environment and reset the session from the sidebar
b) `CwdUploadError` from a rejected file extension
c) `ApprovalTimeoutError` after 600 seconds with no response
d) A missing `output_schema`

### Q11. What is the default `overwrite` behavior of `upload_to_cwd()`, and how does it differ from `chat_input_bar()`'s upload default?

a) Both default to `"replace"`
b) `upload_to_cwd()` defaults to `"error"`; `chat_input_bar()` defaults its `upload_overwrite` to `"replace"`
c) `upload_to_cwd()` defaults to `"skip"`; `chat_input_bar()` defaults to `"error"`
d) Both default to `"skip"`

### Q12. What does `app_viewer()`'s log parser look for to detect an error, and what is a known limitation?

a) It looks for `Uncaught app exception` / `Traceback (most recent call last):`; a later timestamped line can read as "error cleared" even if the error persists
b) It parses the previewed app's DOM directly, since it shares an origin with the host
c) It relies solely on the child process's exit code
d) It queries the Streamlit server's `/healthz` endpoint

### Q13. Why can't `app_viewer()`'s host app read the previewed app's DOM traceback directly?

a) The child app runs in an iframe on another origin, so "Fix with CoCo" is log-scrape only
b) Streamlit disables DOM access for all iframes by policy
c) The child app is rendered fully server-side with no DOM
d) `on_fix` is never wired in any first-party example

### Q14. When does `ApprovalTimeoutError` fire?

a) The tool automatically executes anyway once "Always allow" would apply
b) After `approval_timeout_seconds` (default 600s / 10 min) elapses with no response
c) Only for the SQL tool family
d) Immediately whenever a tool card is rendered, regardless of the timeout setting

### Q15. Is "Always allow" ever persisted across a Streamlit process restart?

a) Yes, it is written to `~/.snowflake/` config
b) No — it is session-scoped only and clears on reset or restart
c) Yes, but only for the SQL tool family
d) Yes, if `require_approval_for` is a list rather than a callable

### Q16. What does the `CORTEX_CODE_CLI_PATH` environment variable override?

a) The Snowflake connection name
b) The `cortex` CLI path, when it is not on `PATH` or passed as `CocoOptions.cli_path`
c) The upload subdirectory used by `cwd_uploader()`
d) The approval timeout duration

### Q17. Which values does `is_debug_mode()` treat as truthy for `STREAMLIT_COCO_DEBUG` / `COCO_DEBUG`?

a) Any non-empty string
b) `"1"`, `"true"`, `"yes"`, `"on"` (case-insensitive), or a truthy `st.session_state["coco_debug"]`
c) Only the integer `1`, nothing else
d) `"debug"` or `"verbose"`

### Q18. Where is `TTS_DATA_MODE` read, and what does it affect?

a) It is a global env var read by `streamlit_coco/diagnostics.py` to select the Snowflake connection
b) It is read only by the `examples/bi_to_semantic` child preview process (via `app_viewer(env=...)`) to select disconnected vs. connected data mode for the generated consumer app
c) It controls whether `STREAMLIT_COCO_DEBUG` payloads are shown
d) It is a required variable for every example app

### Q19. What is the status of security finding SEC-01?

a) Resolved in `0.1.5` — an approval audit log is now persisted
b) Open, target v0.2 — persist an approval audit log (who approved what, when)
c) Not tracked; there is no audit-log requirement
d) Resolved in `0.1.0`

### Q20. What is the status of SEC-02?

a) Resolved — a dedicated least-privilege role recommendation document is committed to the repo
b) Open, target v0.2 — document a dedicated least-privilege role recommendation; today's security page gives only interim guidance
c) Not applicable; the library manages Snowflake grants directly
d) Resolved in `0.1.5` alongside the CodeQL removal

### Q21. What is the current status of CodeQL in this repository's CI?

a) It runs on every PR, as `findings-report.md`'s summary table still states
b) It was dropped in `0.1.5` because the private GitHub org lacks a GHAS license; only Gitleaks and pip-audit run today
c) It runs only on the weekly Monday schedule, not on PRs
d) It was replaced by a different static analyzer in `0.1.6`

### Q22. Which two scanners actually run in `security.yml` today, and on what triggers?

a) CodeQL and Gitleaks, on every push only
b) Gitleaks (CLI) and `pip-audit --skip-editable`, on every PR, every push to `main`, and weekly (Monday)
c) pip-audit and a dependency scanner, nightly only
d) Gitleaks only, on release tags

### Q23. Which security items are OPEN (not resolved) per the threat model? (Multiple choice — select all that apply)

a) SEC-01 — persisted approval audit log
b) SEC-02 — least-privilege role recommendation document
c) SEC-03 — commit `uv.lock`
d) SEC-04 — SBOM generation in CI

### Q24. Per the manual review in `findings-report.md` (version audited `0.1.0`), which of these did the review NOT find in the source?

a) `shell=True`, hardcoded credentials, or `eval()`/`exec()` usage
b) Any use of `pandas`
c) Any Streamlit widget
d) Any type hints

### Q25. What triggers a `CocoSession`'s background worker to restart?

a) Any change to any `CocoOptions` field
b) A change to `options_hash()`, computed only from fields that affect tool permissions (e.g. `allowed_tools`, `disallowed_tools`, `permission_mode`, `require_approval_for`)
c) Every call to `session.send()`
d) A Streamlit rerun, regardless of option changes

### Q26. What does `wrap_exception()` do?

a) It retries a failed SDK call up to three times before raising
b) It maps raw SDK/runtime exceptions to the library's typed `CocoError` subclasses, by message-sniffing plus a `context=` kwarg (e.g. `"session_start"`, `"query"`, `"approval"`)
c) It suppresses all exceptions and logs them silently
d) It converts any exception into `SDKNotInstalledError`

### Q27. What does `ApprovalTimeoutError` also subclass, alongside `CocoError`?

a) `ValueError`
b) `TimeoutError`
c) `ConnectionError`
d) `KeyError`

### Q28. What does `SDKNotInstalledError` also subclass, alongside `CocoError`?

a) `ImportError`
b) `RuntimeError`
c) `OSError`
d) `AttributeError`

### Q29. What does the CI workflow `ci.yml` run on every PR to `main`?

a) Unit and e2e tests, without a live CoCo agent
b) Only the manual/live checklists that require a real CLI and Snowflake
c) Only `make audit`
d) A full release build and publish to PyPI

### Q30. Why might `make audit` have failed spuriously right after a version bump, before the `0.1.7` fix?

a) `pip-audit` treated the freshly bumped, not-yet-published local version as "dependency not found on PyPI" — fixed by adding `--skip-editable`
b) `ruff` flagged the version string as invalid
c) The lockfile was not committed
d) CodeQL blocked the pipeline

## Answer Key

| Q | Answer | Explanation |
|---|--------|-------------|
| 1 | **a** | CHANGELOG `0.1.8` Fixed: Save & regenerate now writes `BRIEF.md` before queuing CoCo, closing the overwrite race. |
| 2 | **b** | CHANGELOG `0.1.7` Fixed: `--skip-editable` avoids a false "not found on PyPI" audit failure after a version bump. |
| 3 | **b** | CHANGELOG `0.1.6` Fixed covers both the `$schema`/`$id` stripping and the `use_container_width` → `width="stretch"` change. |
| 4 | **a** | The exact error text cited in `0.1.6`'s Fixed entry is the draft-URI schema-ref rejection. |
| 5 | **b** | CHANGELOG `0.1.5` Changed (Security): CodeQL dropped (GHAS license gap), Gitleaks and pip-audit kept. |
| 6 | **a** | CHANGELOG `0.1.0` Fixed: Grep/Glob completed cards show a compact summary instead of a full dump. |
| 7 | **b** | `SDKNotInstalledError` means the optional SDK extra is missing; the fix is `pip install streamlit-coco[sdk]` or `make install`. |
| 8 | **b** | `CLIProbeError` is specifically "binary found but `--version` failed," distinct from `CLINotFoundError`. |
| 9 | **b** | The troubleshooting table's fix for a stuck connect is checking terminal logs and enabling `STREAMLIT_COCO_DEBUG=1`. |
| 10 | **a** | Input disabled after boot maps to `SessionNotReadyError`/error status; fix the environment and reset from the sidebar. |
| 11 | **b** | `upload_to_cwd()`'s own default is `overwrite="error"`; `chat_input_bar()` sets its `upload_overwrite` default to `"replace"`. |
| 12 | **a** | The parser matches on those two strings; a later timestamped line can be misread as clearing the error. |
| 13 | **a** | The child preview is another origin (different port), so only the scraped log — not the DOM — is available to "Fix with CoCo." |
| 14 | **b** | `ApprovalTimeoutError` fires once `approval_timeout_seconds` (default 600s) elapses with no decision. |
| 15 | **b** | "Always allow" lives only in `PermissionManager.always_allowed_tools` in memory; it clears on `reset()`, `close()`, or restart. |
| 16 | **b** | `CORTEX_CODE_CLI_PATH` overrides the CLI path lookup when the CLI is not on `PATH` and `cli_path` was not passed. |
| 17 | **b** | `is_debug_mode()`'s documented truthy set is `"1"`/`"true"`/`"yes"`/`"on"` (case-insensitive) or a truthy session-state flag. |
| 18 | **b** | `TTS_DATA_MODE` is read only inside the `bi_to_semantic` child preview process, via `app_viewer(env=...)`. |
| 19 | **b** | SEC-01 is listed open, target v0.2, in `threat-model.md` §7. |
| 20 | **b** | SEC-02 is listed open, target v0.2; the security page's current guidance is interim, not the tracked deliverable. |
| 21 | **b** | `0.1.5` dropped the CodeQL job for license reasons; `security.yml` today runs only Gitleaks and pip-audit. |
| 22 | **b** | Gitleaks (CLI) and `pip-audit --skip-editable` run on PR, push-to-main, and the weekly Monday schedule. |
| 23 | **A, B** | SEC-01 and SEC-02 are open (target v0.2); SEC-03 (lockfile) and SEC-04 (SBOM) are both resolved. |
| 24 | **a** | The manual review explicitly states no `shell=True`, no hardcoded credentials, and no `eval()`/`exec()` were found. |
| 25 | **b** | `options_hash()` hashes only the tool-permission-affecting fields; `CocoSession` restarts its worker only when that hash changes. |
| 26 | **b** | `wrap_exception()` message-sniffs the raw exception and uses `context=` to pick the right `CocoError` subclass. |
| 27 | **b** | `ApprovalTimeoutError` is documented as also a `TimeoutError`. |
| 28 | **a** | `SDKNotInstalledError` is documented as also an `ImportError`. |
| 29 | **a** | CI runs unit and e2e tests on every PR to `main`, without a live CoCo agent; live checks are manual-only. |
| 30 | **a** | Before `0.1.7`, `pip-audit` without `--skip-editable` reported the just-bumped local version as missing from PyPI. |
