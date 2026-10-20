# streamlit-coco — Expert certification

**Pass threshold: 24/30.** Prerequisite: ≥ 12 months of use.

### Q1. What does `CocoSession` use internally to drive the SDK client?

a) A synchronous blocking call from the main Streamlit thread
b) A background thread (`threading.Thread`, named `coco-session`) running an asyncio loop that wraps `CortexCodeSDKClient`
c) A separate Streamlit process per session
d) A task queue backed by an external broker

### Q2. Which invariant lets `examples/headless_pipeline.py` run from a plain terminal with no Streamlit installed?

a) UI exports (`panel`, `copilot_rail`, `chat_input_bar`, …) resolve lazily via `streamlit_coco.__getattr__`; core headless imports (`CocoSession`, `query`, `CocoOptions`, permission functions, the error hierarchy) never import `streamlit`
b) `streamlit` is bundled as a vendored dependency inside `streamlit_coco`
c) The headless example monkey-patches `sys.modules["streamlit"]`
d) `CocoSession` detects the absence of Streamlit and falls back to a CLI-only mode automatically

### Q3. When a tool call needs approval, what exactly blocks, and until when?

a) The Streamlit main thread blocks until the page is refreshed
b) The `can_use_tool` callback (built by `build_can_use_tool()`) blocks the session's worker thread on `PermissionManager.wait_for_decision()`, until the UI resolves it or `approval_timeout_seconds` elapses
c) Nothing blocks; the tool executes and is rolled back if denied
d) The CLI subprocess exits and must be restarted manually

### Q4. Which fields does `CocoOptions.options_hash()` hash, and what is it used for?

a) Every field on `CocoOptions`; it always restarts the worker on any change
b) Only the fields that affect what a tool is allowed to do (e.g. `allowed_tools`, `disallowed_tools`, `permission_mode`, `require_approval_for`, `add_dirs`); `CocoSession` restarts its worker only when this hash changes
c) Only `connection` and `cwd`, used purely for logging
d) A hash of the entire transcript, used for response caching

### Q5. Why does `app_viewer()` never import `copilot_rail()` (and vice versa)?

a) They are mutually incompatible and cannot be used in the same app
b) The preview component is kept host-agnostic — it does not know about job queues; a host app composes both and wires `on_fix` itself
c) `copilot_rail()` was deprecated in favor of `app_viewer()`
d) A circular-import bug has not yet been fixed

### Q6. Which tool families are special-cased in `permissions.py` to always create a fresh approval request, ignoring any prior "always allow"?

a) The SQL tool and Write
b) `AskUserQuestion` and `ExitPlanMode`
c) Grep and Glob
d) Edit and Read

### Q7. What message does `SnowflakeConfigNotFoundError` carry?

a) "CoCo CLI not found on PATH"
b) "No Snowflake config found. Create ~/.snowflake/connections.toml (or legacy config.toml)..."
c) "Approval timed out for tool {tool_name}"
d) "cortex-code-agent-sdk is required. Install with: pip install streamlit-coco[sdk]"

### Q8. Which exception is raised when a `cortex` binary is found at a configured path but does not respond correctly to `--version`?

a) `CLINotFoundError`
b) `CLIProbeError`
c) `CocoConnectionError`
d) `SessionStartError`

### Q9. How does `SessionStartError` differ from `SessionNotReadyError`?

a) They are the same exception under two names
b) `SessionStartError` covers a worker that fails to start; `SessionNotReadyError` covers a connect timeout or boot failure once the worker is running
c) `SessionStartError` is used only for headless `query()`
d) `CocoConnectionError` supersedes both

### Q10. What does `wrap_exception()`'s `context=` kwarg do?

a) It is purely cosmetic and does not affect which error type is raised
b) It steers the message-sniffing mapping (e.g. `"session_start"`, `"session_ready"`/`"session"`, `"query"`, `"approval"`) toward the right `CocoError` subclass for where the raw exception occurred
c) It sets the Streamlit session key
d) It logs the exception to a remote server

### Q11. What does `CwdUploadError` cover?

a) Only oversize uploads
b) Bad file names (path-traversal guard), disallowed extensions, oversize payloads, and overwrite conflicts
c) Only Snowflake connection failures during upload
d) Only extension mismatches, never size

### Q12. Which exception is also a `TimeoutError`, in addition to being a `CocoError`?

a) `SessionNotReadyError`
b) `ApprovalTimeoutError`
c) `CLIProbeError`
d) `QueryError`

### Q13. In the STRIDE threat model, what severity is assigned to prompt injection triggering dangerous tools, and what mitigates it?

a) Low severity; mitigated by input sanitization
b) High severity; mitigated by approval gates (`PermissionManager` intercepts before execution), with a least-privilege role also recommended
c) Critical severity; mitigated by disabling all tools by default
d) Medium severity; mitigated by rate limiting

### Q14. What severity and mitigation apply to the "Always allow" escalation risk?

a) High severity; mitigated by requiring a password re-entry
b) Medium severity; mitigated by scope — per-tool, per-session only, cleared on reset or restart
c) Low severity; no mitigation is applied
d) High severity; mitigated by a persistent audit log (already shipped)

### Q15. What is the status of the repudiation risk (no persisted log of approved destructive actions)?

a) Resolved in `0.1.8`
b) Open, Medium severity, tracked as SEC-01 — the transcript exists only in Streamlit session state, nothing durable is written
c) Not a recognized risk in the threat model
d) Mitigated by CodeQL scanning

### Q16. How is the information-disclosure risk of secrets appearing in the transcript/logs mitigated?

a) The library encrypts the transcript at rest
b) The library does not log credentials, and the SDK redacts them from its output
c) It is not mitigated; this is an open item
d) By disabling the transcript entirely

### Q17. What supply-chain risk does the threat model flag, and how is it mitigated?

a) Elevation of privilege via a compromised dependency; mitigated by `pip-audit` in CI and Gitleaks scanning, with `uv.lock` committed for reproducible builds
b) SQL injection in the agent's tool calls; mitigated by parameterized queries
c) Session hijacking; mitigated by rotating API keys
d) DNS spoofing of the PyPI registry; mitigated by certificate pinning

### Q18. Per the "Roles and grants" guidance, why is connecting with `ACCOUNTADMIN` (or a grant like `MANAGE WAREHOUSES`) discouraged, even with approval gates in place?

a) Approval gates control whether a statement runs, not what it is allowed to touch once approved — the effective SQL permissions are exactly the connected role's grants
b) `ACCOUNTADMIN` sessions are technically incompatible with the CoCo CLI
c) The library actively blocks `ACCOUNTADMIN` connections
d) `MANAGE WAREHOUSES` disables the approval flow entirely

### Q19. Which of these are explicitly out of scope for this product's guide pack, per the shape-module scoping decision? (Multiple choice — select all that apply)

a) A Skills reference chapter for repo-root `.cortex/skills/*/SKILL.md`
b) A `reference-procedures` chapter for Snowflake objects
c) A Native App deployment chapter
d) A `reference-commands` chapter for Makefile targets
e) A `reference-api` chapter for the Python API
f) A controls-catalogue chapter (rule files / scoring rubric)

### Q20. Which deployment targets does the threat model consider, and which actually ship today?

a) Local, SiS, and SPCS all ship today
b) Only SiS ships today; local and SPCS are threat-model scope only
c) Local, SiS, and SPCS are all considered in the threat model, but only local actually ships today
d) Only SPCS ships today

### Q21. Why does the guide pack omit an "Infrastructure as code" chapter?

a) Terraform files exist but were left undocumented
b) There is no `*.tf` file in this repo
c) IaC is out of scope for security reasons only
d) It is planned for a future release and intentionally deferred

### Q22. Why does `reference-examples` treat each of the three example apps as one section, rather than documenting every internal Streamlit page of each app?

a) Going page-by-page for three example apps would restate the example READMEs already linked, so each app gets one H2 instead
b) Streamlit pages cannot be documented in Markdown
c) Only `chat_app.py` has more than one page
d) Page-level docs are generated automatically and need no writing

### Q23. What is `text_renderer` as an extension point?

a) A required parameter with no default, used to select the Snowflake warehouse
b) A pluggable text-rendering option on `panel()` (and related display helpers) — a preset name (`"markdown"`, `"write"`, `"text"`, `"caption"`, `"code"`) or a callable
c) A CLI flag for `make chat`
d) A YAML file defining transcript colors

### Q24. How does the library decide how to render an unknown or MCP-provided tool's card?

a) It refuses to render anything for tools it does not recognize
b) Through tool-name dispatch (`tool_family(name)` in `tool_names.py`) mapping a tool name to a `ToolFamily`, with `tool_cards.py`/`tool_extract.py` handling per-family rendering
c) It always renders raw JSON for unrecognized tools, with no dispatch logic
d) Every tool must first be registered in `CocoOptions.allowed_tools` before it can render at all

### Q25. How does App Builder let a "type" bring its own CoCo guidance into a generation job?

a) By hardcoding prompts inside `streamlit_coco` itself
b) Each `types/<id>/` folder can include a `SKILL.md` (+ `reference/`, `CHECKLIST.md`) mounted via `add_dirs`, alongside `types/shared/SKILL.md` for rules that apply to every type
c) By calling a REST API hosted outside the repo
d) By writing directly into `streamlit_coco/tool_names.py`

### Q26. What decides whether an App Builder type's profiling step is a deterministic parser or a CoCo job?

a) The Streamlit version installed
b) The type's `grounding_kind` (`tabular`, `semantic_view`, `documents`, or `urls`) — tabular grounding uses a deterministic pandas parser (`engine/profile.py`); other kinds go through CoCo
c) Whether the user is on the Admin page
d) The global `permission_mode` set for the app

### Q27. Who fetches App Builder's "documents" or "urls" grounding sources — the CoCo session or the host app?

a) The CoCo session, via a granted network tool
b) The host application — documents/URLs are fetched by the host, never by the CoCo session, since no network tool is granted to it
c) Neither; grounding sources must be pre-downloaded manually before every run
d) A separate external function

### Q28. A colleague asks why the repo doesn't need a CLI-flags `reference-commands` chapter the way a typical CLI tool would. What's the accurate explanation?

a) The library ships no commands at all
b) The product's primary surface is a Python library (the API), not a CLI — the Makefile targets are documented as `reference-commands` for running the demos, while the library's own reference is the API surface, treated like a "Commands" analogue
c) CLI documentation is intentionally withheld from customers
d) The CoCo CLI's own docs fully replace the need for any local reference

### Q29. Two repos are involved in releasing to PyPI today. What is the current (temporary) arrangement, and why?

a) Releases are tagged and published directly from `DevoteamSP/streamlit-coco-dev`
b) Tags on `lletourmy/streamlit-coco` (a temporary public release surface) trigger the PyPI publish, until `DevoteamSP/streamlit-coco` is PyPI-validated and the Trusted Publisher setup moves there
c) PyPI releases are manual uploads with no repo tagging involved
d) `DevoteamSP/streamlit-coco` is already the publishing repo; `-dev` is only for issue tracking

### Q30. Teaching a new team member the release flow: which step comes immediately after `DRY_RUN=1 make sync-release` looks correct?

a) `git push --tags` on the `-dev` repo directly
b) `COMMIT=1 PUSH=1 MESSAGE="Release X.Y.Z" make sync-release`, then tag `vX.Y.Z` on `lletourmy/streamlit-coco` (not on `-dev`)
c) Immediately run `make publish` from the `-dev` checkout
d) Skip straight to `pip install streamlit-coco==X.Y.Z` to verify

## Answer Key

| Q | Answer | Explanation |
|---|--------|-------------|
| 1 | **b** | `CocoSession` owns a `threading.Thread` named `coco-session` running an asyncio loop that wraps `CortexCodeSDKClient`. |
| 2 | **a** | Core headless symbols import without loading Streamlit; UI exports resolve lazily through `__getattr__`/`_LAZY_ATTRS`, which is what makes `headless_pipeline.py` work with no Streamlit installed. |
| 3 | **b** | `can_use_tool` blocks the worker thread on `PermissionManager.wait_for_decision()` until resolved or `approval_timeout_seconds` elapses. |
| 4 | **b** | `options_hash()` hashes only tool-permission-affecting fields; the worker restarts only when that hash changes, not on every option edit. |
| 5 | **b** | This is a documented invariant: the preview component stays host-agnostic and does not know about job queues. |
| 6 | **b** | `permissions.py` special-cases `AskUserQuestion` and `ExitPlanMode` to always create a fresh request, regardless of prior "always allow." |
| 7 | **b** | This is the exact `SnowflakeConfigNotFoundError` message text. |
| 8 | **b** | `CLIProbeError` specifically means the binary exists but failed to answer `--version`; `CLINotFoundError` covers the not-on-PATH case. |
| 9 | **b** | `SessionStartError` is a worker-fails-to-start error; `SessionNotReadyError` covers timeout/boot-failure once started. |
| 10 | **b** | `context=` (`"session_start"`, `"session_ready"`/`"session"`, `"query"`, `"approval"`) steers which `CocoError` subclass the message-sniffing maps to. |
| 11 | **b** | `CwdUploadError` is raised for bad names, disallowed extensions, oversize payloads, and overwrite conflicts alike. |
| 12 | **b** | `ApprovalTimeoutError` is documented as also a `TimeoutError`. |
| 13 | **b** | Prompt injection is rated High severity; approval gates intercepting pre-execution are the primary mitigation, alongside a least-privilege role recommendation. |
| 14 | **b** | "Always allow" escalation is Medium severity, mitigated purely by its per-tool/per-session scope. |
| 15 | **b** | Repudiation is Medium severity, open as SEC-01 — nothing durable is written outside in-memory session state. |
| 16 | **b** | Mitigation is that the library never logs credentials and the SDK redacts them from its own output. |
| 17 | **a** | The flagged risk is elevation of privilege via a compromised dependency; mitigation is `pip-audit`, Gitleaks, and a committed `uv.lock`. |
| 18 | **a** | Approval gates only decide whether a statement runs; once approved, its reach is bounded solely by the connected role's actual grants. |
| 19 | **A, B, C, F** | Skills, Snowflake-procedures, Native App, and a controls catalogue are all listed as "did not fire" / out of scope; commands and the API reference did fire and are documented. |
| 20 | **c** | The threat model considers local/SiS/SPCS, but only local is actually shipped; SiS/SPCS are threat-model and roadmap scope only. |
| 21 | **b** | The scoping reason given is simply that there is no `*.tf` file anywhere in the repo. |
| 22 | **a** | The explicit scoping decision is one H2 per example app, to avoid restating the example READMEs page by page. |
| 23 | **b** | `text_renderer` accepts a preset name or callable on `panel()` and related display helpers. |
| 24 | **b** | `tool_family(name)` dispatch in `tool_names.py` maps tool names to a `ToolFamily`, consumed by `tool_cards.py`/`tool_extract.py` for rendering. |
| 25 | **b** | Each type folder can carry its own `SKILL.md` (+ reference/checklist), mounted via `add_dirs`, plus a shared `types/shared/SKILL.md`. |
| 26 | **b** | `grounding_kind` decides: `tabular` uses the deterministic `engine/profile.py` parser, the other kinds go through CoCo. |
| 27 | **b** | Documents/URLs are fetched by the host app; the CoCo session is granted no network tool. |
| 28 | **b** | The library's primary surface is the Python API, not a CLI; Makefile targets get `reference-commands` for the demos, while the API is the library's own "Commands" analogue. |
| 29 | **b** | `lletourmy/streamlit-coco` is the temporary public release surface tagged for PyPI publish, until `DevoteamSP/streamlit-coco` is PyPI-validated. |
| 30 | **b** | After a clean dry run, the documented next step is the committed/pushed sync, then tagging `vX.Y.Z` on `lletourmy/streamlit-coco`, never on `-dev`. |
