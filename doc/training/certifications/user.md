# streamlit-coco — User certification

**Pass threshold: 24/30.** Prerequisite: Training completed.

### Q1. What is the recommended order of the three Training cases?

a) `03-advanced` → `02-intermediate` → `01-simple`
b) `01-simple` → `02-intermediate` → `03-advanced`
c) `02-intermediate` → `01-simple` → `03-advanced`
d) Any order — there is no recommended sequence

### Q2. What distinguishes `01-simple` from `02-intermediate`?

a) `01-simple` uses sample data and is fully guided; `02-intermediate` works on the learner's own data with checkpoints instead of click-by-click steps
b) `01-simple` is the only case that uses real Snowflake data
c) `02-intermediate` removes all data and all guidance
d) The two cases are identical except for their time budget

### Q3. What is the defining feature of `03-advanced`?

a) It repeats `01-simple` with a larger sample dataset
b) Something breaks — drawn from a real incident or a CHANGELOG "Fixed" entry — and the learner diagnoses it alone
c) It is entirely multiple-choice, with no hands-on component
d) It only covers the headless `query()` API

### Q4. Which sequence of calls does `examples/chat_app.py` use to implement the preferred pattern?

a) `chat()` → `render_approvals()` → `send_prompt()`
b) `check_environment()` → `render_start_gate()` → `get_or_create_session()` → `panel()` + `chat_input_bar()`
c) `require_environment()` → `copilot_rail()` → `app_viewer()`
d) `CocoSession()` → `query()` → `events_to_dataframe()`

### Q5. What does `panel()` return?

a) `None`
b) A `CocoChatResult`
c) A `CocoEnvironment`
d) A `CocoSession`

### Q6. In `panel()`, what does setting `output_label=None` do?

a) Renders the output with the default label "CoCo output"
b) Hides the bordered output container
c) Switches the output mode from `"transcript"` to `"field"`
d) Disables the Stop button

### Q7. Which `panel()` parameter switches between showing the running transcript and showing only the latest field-style output?

a) `output_mode` (`"transcript"` or `"field"`)
b) `show_status`
c) `status_expanded`
d) `text_renderer`

### Q8. What does `chat_input_bar(session, accept_file=True)` enable?

a) Structured JSON output rendering
b) File attachment, saved into the session's working directory via the upload helpers
c) A right-rail example-questions picker
d) A plan-mode banner with an Execute plan button

### Q9. Which of these is a real `copilot_rail()` parameter?

a) `example_questions`
b) `demo_mode`
c) `sidebar_width`
d) `rail_theme`

### Q10. What is `job=` used for in `copilot_rail()`?

a) It schedules a cron-based background task
b) It passes a dict such as `{prompt, label, status, expect_structured}` to queue a job for the rail to send
c) It sets the Snowflake warehouse for the session
d) It configures the CI job that builds the rail

### Q11. What does `transcript_display_config()` add to a rail-based UI?

a) A popover with "Last messages" and "First n characters" pills/sliders to control transcript display
b) A button that exports the transcript to CSV
c) A dark-mode toggle
d) A control to switch the UI between English and French labels

### Q12. What must `app_dir` point to for `app_viewer()` to work correctly?

a) The same directory as the host app that calls `app_viewer()`
b) A folder containing a `streamlit_app.py` (or the script named via `script_name`)
c) Any directory that contains a `Makefile`
d) The `dist/` folder produced by `make build`

### Q13. What does the "Fix with CoCo" button in `app_viewer()` do by default?

a) Automatically rewrites the generated app with no approval step
b) Calls `on_fix` with a prompt built from `default_fix_prompt(traceback, app_dir)`, typically queuing a job for CoCo
c) Restarts the child `streamlit run` process with default settings
d) Deletes the previous preview log

### Q14. How many `app_viewer()` previews are meant to point at the same `app_dir` at once?

a) Unlimited, as long as the ports differ
b) One
c) Two — one for the deterministic app and one for the CoCo-authored app
d) As many as fit in the port range 8511–8520

### Q15. Which `CocoOptions` field controls how long the app waits for a human decision on a pending approval before raising an error?

a) `max_turns`
b) `approval_timeout_seconds` (default `600.0`)
c) `permission_mode`
d) `require_approval_for`

### Q16. What is the default `CocoOptions.permission_mode`?

a) `"plan"`
b) `"auto"`
c) `"default"`
d) `"approve_all"`

### Q17. Which function probes the environment (SDK install, CLI reachability, Snowflake config) without starting an agent, and never raises?

a) `require_environment()`
b) `check_environment()`
c) `CocoSession.ensure_ready()`
d) `resolve_snowflake_config_path()`

### Q18. If `toml_file` is not passed and there is exactly one `*.toml` file under `~/.snowflake/`, what happens?

a) The library refuses to start and raises `SnowflakeConfigNotFoundError`
b) That one file is used, regardless of its name
c) The library looks only for a file literally named `connections.toml`
d) The user is prompted interactively to choose a file

### Q19. With several `*.toml` files under `~/.snowflake/` and no `toml_file` given, what is the selection order?

a) Alphabetical only
b) `connections.toml` first, then `config.toml`, then alphabetical
c) Most recently modified file first
d) `config.toml` first, then `connections.toml`, then alphabetical

### Q20. What does `examples/structured_output.py` demonstrate?

a) `output_schema` plus `on_structured_output`, routing agent JSON into an app widget instead of chat text
b) A pure async pipeline with no Streamlit import
c) File upload into the agent's working directory
d) A right-rail Copilot with no SQL tool

### Q21. What does `examples/headless_pipeline.py` demonstrate?

a) `panel()` embedded in a multipage app
b) Pure async Python using `query()` / `CocoSession`, with no Streamlit import, run from a terminal
c) `copilot_rail()` combined with `app_viewer()`
d) The legacy CCv2 `chat()` component

### Q22. What kind of demo is `examples/approval_gate.py`?

a) The preferred pattern (`panel()` + `chat_input_bar()`)
b) A headless script
c) The legacy CCv2 `chat()` all-in-one component
d) A rail-based example with no SQL tool

### Q23. What is distinctive about `examples/backlog_desk/`, compared to the other example apps?

a) It is the first example that is rail-based and uses no SQL tool at all — its data is file/JSON-backed
b) It is the only example that requires a dedicated Snowflake warehouse
c) It is the only example that uses the legacy CCv2 component
d) It is the only example with no Copilot at all

### Q24. In `examples/backlog_desk/`, how is its Copilot opened?

a) It is a dedicated navigation page in the sidebar
b) It opens automatically on every page load
c) From a header "Copilot" button or an action link, and closed with "Close" — it is not a navigation page
d) Only via the `make headless` target

### Q25. What kinds of source files does `examples/bi_to_semantic/` read as input?

a) Only Snowflake stage files
b) Tableau `.twb`/`.twbx` and/or Power BI `.pbix`/`.pbit` workbooks
c) Only CSV exports from a data warehouse
d) `.cortex/skills/*/SKILL.md` files

### Q26. Where do files uploaded via `upload_to_cwd()` / `cwd_uploader()` / `chat_input_bar(accept_file=...)` land by default?

a) `<CocoOptions.cwd>/_uploads/` (the subdirectory name is configurable)
b) The Streamlit app's own installation directory
c) `~/.snowflake/`
d) `dist/`

### Q27. What does the App Builder "Build" step write into `examples/app_builder/out/<slug>/`?

a) Only a compiled `.whl` file
b) `brief.json`, `BRIEF.md`, `sketches/*`, and `streamlit_app.py`
c) A CycloneDX SBOM
d) Only a `.preview.log` file

### Q28. Where does the release build's SBOM get published?

a) Into `examples/app_builder/out/`
b) As GitHub Release assets (CycloneDX JSON), generated CI-only
c) Into `_uploads/`
d) It is not generated anywhere yet

### Q29. What does `render_approvals()` present, and in what button order?

a) Deny, Always allow, Approve once
b) Approve once, Always allow, Deny
c) Approve once, Deny (there is no "Always allow" option)
d) A single "Approve" button with no deny option

### Q30. Which of these tool families never expose an "Always allow" option in the approval UI? (Multiple choice — select all that apply)

a) `AskUserQuestion`
b) `ExitPlanMode`
c) The SQL tool
d) Edit
e) Write
f) Grep

## Answer Key

| Q | Answer | Explanation |
|---|--------|-------------|
| 1 | **b** | The cases are numbered and progress `01-simple` → `02-intermediate` → `03-advanced`, increasing in difficulty. |
| 2 | **a** | `01-simple` is the fully guided, sample-data happy path; `02-intermediate` uses the learner's own data with checkpoints instead of click-by-click steps. |
| 3 | **b** | `03-advanced` presents a real breakage (real incident or CHANGELOG "Fixed" entry) that the learner diagnoses without guided steps. |
| 4 | **b** | This is the exact call chain the preferred-pattern reference example uses. |
| 5 | **b** | `panel(session, **kwargs) -> CocoChatResult`. |
| 6 | **b** | `output_label=None` hides the bordered output container; the default label otherwise is `"CoCo output"`. |
| 7 | **a** | `output_mode` toggles between `"transcript"` (default) and `"field"` rendering. |
| 8 | **b** | `accept_file=True` (or `"multiple"`) turns on file attachment, which is saved via the upload helpers into the session's `cwd`. |
| 9 | **a** | `example_questions` is a documented `copilot_rail()` parameter; the other three are not part of its signature. |
| 10 | **b** | `job=` takes a dict (`prompt`, `label`, `status`, `expect_structured`) that queues a prompt for the rail to send. |
| 11 | **a** | `transcript_display_config()` renders the display-settings popover with Last-messages/First-n-characters controls. |
| 12 | **b** | `app_viewer(app_dir, ...)` requires a folder with `streamlit_app.py` (or the `script_name` override); it must never point at the host app's own directory. |
| 13 | **b** | The Fix action calls `on_fix` with a prompt from `default_fix_prompt(traceback, app_dir)`, normally queuing a CoCo job. |
| 14 | **b** | The documented limitation is one preview per `app_dir`. |
| 15 | **b** | `approval_timeout_seconds` (default `600.0`, i.e. 10 minutes) governs the HITL wait before `ApprovalTimeoutError`. |
| 16 | **c** | `CocoOptions.permission_mode` defaults to `"default"`; `"plan"` is used explicitly for ExitPlanMode flows. |
| 17 | **b** | `check_environment()` is the non-raising probe; `require_environment()` raises typed errors instead. |
| 18 | **b** | When exactly one `*.toml` exists under `~/.snowflake/`, it is used regardless of its filename. |
| 19 | **b** | With multiple files, `connections.toml` wins first, then `config.toml`, then alphabetical order. |
| 20 | **a** | `structured_output.py` shows `output_schema` + `on_structured_output` routing JSON into a widget instead of chat text. |
| 21 | **b** | `headless_pipeline.py` is pure async Python using `query()`/`CocoSession`, with no Streamlit import. |
| 22 | **c** | `approval_gate.py` demonstrates the legacy CCv2 `chat()` all-in-one component. |
| 23 | **a** | `backlog_desk` is the first rail-based, no-SQL example, backed by local JSON files. |
| 24 | **c** | Its Copilot is opened from a header "Copilot" button or an action link and closed with "Close" — it is not a navigation page. |
| 25 | **b** | `bi_to_semantic` reads Tableau `.twb`/`.twbx` and/or Power BI `.pbix`/`.pbit` workbooks. |
| 26 | **a** | Upload helpers write into `<CocoOptions.cwd>/_uploads/` by default (subdirectory name configurable). |
| 27 | **b** | The Build step writes `brief.json`, `BRIEF.md`, `sketches/*`, and `streamlit_app.py` into `out/<slug>/`. |
| 28 | **b** | The SBOM (CycloneDX) is attached to GitHub Release assets and is produced only in CI, on tag release. |
| 29 | **b** | `render_approvals()` orders its controls Approve once, Always allow, Deny. |
| 30 | **A, B** | `AskUserQuestion` and `ExitPlanMode` always prompt fresh and never show "Always allow"; the SQL tool and Edit/Write/Grep can be always-allowed. |
