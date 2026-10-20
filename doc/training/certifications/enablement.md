# streamlit-coco — Enablement certification

**Pass threshold: 8/10.** Prerequisite: Enablement track.

### Q1. What problem does `streamlit-coco` solve for a Streamlit app author?

a) It replaces the CoCo CLI entirely, so no CLI installation is ever needed
b) It provides ready-made session, streaming-render, tool-card, and approval-flow plumbing so the author does not build it by hand
c) It generates Snowflake role and grant definitions automatically
d) It provisions and manages the Snowflake warehouse a CoCo session runs against

### Q2. Which statement best describes `panel()`?

a) A right-rail Copilot composed for multipage apps
b) A native transcript/field/approvals/Stop primitive that returns a `CocoChatResult`
c) A legacy Custom Component v2 all-in-one chat widget
d) A preview column that embeds a child Streamlit app in an iframe

### Q3. What does `copilot_rail()` add on top of `panel()`?

a) A right-rail Copilot with a connection picker, queued jobs, and example questions
b) A pure async headless API with no Streamlit import
c) A JSON Schema based structured-output router
d) A guard against path-traversal in uploaded file names

### Q4. What does `app_viewer()` do?

a) Runs the agent's SQL tool against the connected Snowflake role
b) Spawns a child `streamlit run` process for a generated app, embeds it in an iframe, and offers a Fix action
c) Streams the agent's raw NDJSON events to the terminal
d) Uploads browser files into the agent's working directory

### Q5. Which command launches the first-party reference implementation of the preferred pattern (`panel()` + `chat_input_bar()`)?

a) `make demo`
b) `make chat`
c) `make run-app`
d) `make copilot`

### Q6. Which bundle of prerequisites is accurate for starting the Enablement track?

a) Python 3.10+, a Snowflake account with Cortex Code access, the CoCo CLI (`cortex`) reachable on `PATH` or via `CORTEX_CODE_CLI_PATH`, and a working Snowflake connections config
b) Node.js 18+, a dedicated Snowflake warehouse, and a paid GHAS license
c) Python 3.8+, Docker, and a Native App manifest
d) A Streamlit Community Cloud account and a `snowflake.yml` file

### Q7. Which of these are part of the preferred-pattern pipeline demonstrated in `examples/chat_app.py`? (Multiple choice — select all that apply)

a) `check_environment()`
b) `render_start_gate()`
c) `get_or_create_session()`
d) `panel()`
e) `chat_input_bar()`
f) `chat()` (legacy CCv2 component)

### Q8. Which command installs `streamlit-coco` for someone who only needs the published package, not a checkout of the development repo?

a) `pip install "streamlit-coco[sdk]"`
b) `npm install streamlit-coco`
c) `make install` (works only inside the dev repo checkout)
d) `uv build`

### Q9. Under what license is `streamlit-coco` released?

a) MIT
b) Apache-2.0
c) GPL-3.0
d) BSD-3-Clause

### Q10. What is the current package version and release status this training pack describes?

a) `0.1.6`, a stable release
b) `0.1.9`, alpha — the API may still move
c) `1.0.0`, general availability
d) `0.2.0`, beta

## Answer Key

| Q | Answer | Explanation |
|---|--------|-------------|
| 1 | **b** | The library provides session state, transcript streaming, tool cards, and approval plumbing as composable functions, so an app author writes the page and options, not the session bridge. |
| 2 | **b** | `panel(session, **kwargs) -> CocoChatResult` is the native transcript/field output primitive with approvals and a Stop control. |
| 3 | **a** | `copilot_rail()` composes `panel()` into a right-rail Copilot with a connection picker, queued jobs, transcript display config, and example questions. |
| 4 | **b** | `app_viewer(app_dir, ...)` spawns a child `streamlit run` process, embeds it in an iframe, and offers Fix with CoCo by scraping the preview log. |
| 5 | **b** | The Makefile maps `chat` to `Run examples/chat_app.py`; `demo`, `run-app`, and `copilot` are not Makefile targets. |
| 6 | **a** | Prerequisites are Python 3.10+, a Cortex-Code-enabled Snowflake account, the `cortex` CLI on PATH (or `CORTEX_CODE_CLI_PATH`), and a working `connections.toml`/`config.toml` — no dedicated warehouse, Docker, or Native App manifest is required. |
| 7 | **A, B, C, D, E** | `chat_app.py` chains `check_environment()` → `render_start_gate()` → `get_or_create_session()` → `panel()` + `chat_input_bar()`; `chat()` is the legacy CCv2 component used in `examples/approval_gate.py`, not this example. |
| 8 | **a** | The published-package-only path is `pip install "streamlit-coco[sdk]"`; `make install` targets a repo checkout, and the other two commands do not install this package. |
| 9 | **b** | `streamlit-coco` is released under Apache-2.0. |
| 10 | **b** | The pack describes version `0.1.9`, stated as alpha — the API may still move. |
