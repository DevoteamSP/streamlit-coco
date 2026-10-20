# Hands-on exercises

6 progressive exercises using the real apps in `examples/`. Complete the
[setup checklist](setup.html) and the [guided tour](guided-tour.html) first.
Budget ~120–150 minutes total.

---

## Exercise 1 — Run the preferred pattern (`panel()` + `chat_input_bar()`)

**Objective**: See the recommended integration pattern end-to-end and
understand the division of ownership ("you own the page, CoCo owns the
session").

**Steps**:

1. `make chat` (runs `examples/chat_app.py`).
2. Open `examples/chat_app.py` in an editor. Identify the four calls that
   make up the pattern: `check_environment()`, `render_start_gate()`,
   `get_or_create_session()`, `panel()` + `chat_input_bar()`.
3. In the browser, type: *"What tables are available in
   SNOWFLAKE_SAMPLE_DATA.TPCH_SF1?"*
4. Watch the transcript stream, and note the tool card that appears (likely
   a SQL or Glob card).

**Expected result**: A streaming response renders progressively (not all at
once), with at least one tool card showing what the agent did.

**Troubleshooting**: If nothing streams, confirm `check_environment(...).ready`
was `True` in the setup checklist — a stuck session usually means the CLI or
connection is not right. See
[`help.html#session-stuck-connecting`](../technical-guide/help.html#session-stuck-connecting).

---

## Exercise 2 — Trigger and resolve an approval gate

**Objective**: Understand the human-in-the-loop safety model — the core
differentiator of this library over a bare agent integration.

**Steps**:

1. Still in `make chat`, type: *"Show me the top 5 customers by total order
   amount. Write the SQL and run it."*
2. When the approval banner appears, read the full SQL statement shown.
3. Click **Approve once** — confirm the query executes and results appear in
   the transcript.
4. Type: *"Now create a summary table called TOP_CUSTOMERS in my schema."*
5. When the approval gate fires again, click **Deny** with a reason (e.g.
   "not for this exercise") — confirm the agent acknowledges the denial.

**Expected result**: SQL execution pauses for approval both times; approving
lets it run, denying stops it and the agent adapts its next response.

**Troubleshooting**: If no approval gate appears for a `CREATE TABLE`, check
that `require_approval_for=["Edit", "Write", "Bash"]` (or similar) is set in
`CocoOptions` — open `examples/chat_app.py` and confirm the sidebar
**Requires approval** pills.

---

## Exercise 3 — Structured output into a widget

**Objective**: See how agent output can drive your own Streamlit widgets
instead of just rendering as chat text.

**Steps**:

1. Stop the previous demo (Ctrl+C) and run `make structured`
   (`examples/structured_output.py`).
2. Open the file and find the `output_schema` definition and the
   `on_structured_output` callback passed to `panel()`.
3. In the browser, type: *"Give me a breakdown of orders by status."*
4. Confirm the response renders as a Streamlit chart/dataframe, not raw JSON
   text.

**Expected result**: The agent's structured response is routed into a widget
you defined, with no manual JSON parsing in your app code.

**Troubleshooting**: If it renders as plain text instead of a widget, the
reply may not match `output_schema` — try rephrasing the prompt to be more
explicit about the fields you want. See
[`help.html#structured-output-not-rendering`](../technical-guide/help.html#structured-output-not-rendering).

---

## Exercise 4 — Headless mode (no Streamlit UI)

**Objective**: Confirm the same library works outside Streamlit — for CI,
scripts, and batch jobs.

**Steps**:

1. Run `make headless` (`examples/headless_pipeline.py`).
2. Open the file and note: no `streamlit` import anywhere, the same
   `query()` function used for the async event stream.
3. Watch the terminal output — events stream as the agent works, with the
   same event types (`assistant_text`, `tool_use`, `result`) as the UI mode.

**Expected result**: The script runs to completion, printing streamed events
entirely from the terminal — no browser involved.

**Troubleshooting**: If it hangs, check the same environment prerequisites
as Exercise 1 (`check_environment`) — headless mode has the identical
CLI/connection dependency.

---

## Exercise 5 — Build a minimal app from scratch

**Objective**: Prove you can reproduce the pattern without copying an
existing example — the real test of "trained." This is a real situation, not
a mechanical drill: you will hit at least one of the two tool-permission
mistakes people actually make with `CocoOptions`.

**Steps**:

1. Create a new file `my_first_app.py` at the repo root.
2. Using the [README quickstart](../../../README.md#quickstart) as your only
   reference (do not copy `examples/chat_app.py` directly), write an app
   that:
   - Uses `connection="analytics"` (or your configured connection name)
   - Sets `allowed_tools=["Read", "Glob", "Grep"]`
   - Sets `require_approval_for=["Edit", "Write", "Bash"]`
   - Renders the start gate, then `panel()` + `chat_input_bar()`
3. Run it: `uv run streamlit run my_first_app.py`
4. Ask it to read a file in the repo (e.g. *"Read the README and summarize
   it in 3 bullets"*) and confirm it runs without requiring approval (`Read`
   is in `allowed_tools`).
5. Ask it to write a new file — confirm the approval gate fires this time.

**Expected result**: A working app built from the README alone, correctly
distinguishing auto-run tools from approval-gated ones.

**Troubleshooting**: If `Read` still prompts for approval, double check you
did not also list it in `require_approval_for` — `allowed_tools` and
`require_approval_for` should not overlap for the same tool.

**Delete `my_first_app.py` when done** — it is a throwaway training
artifact, not part of the repo.

---

## Exercise 6 — Copilot rail in a product app

**Objective**: See `copilot_rail()` as a right-rail Copilot, not a full-page
chat, and use its Display config controls to keep a live transcript
readable.

**Steps**:

1. `make bi-semantic` (`examples/bi_to_semantic/`).
2. Load the MIT Tableau Server pack on screen 1 (no warehouse required).
3. Connect Copilot on the right. Note the **Connection** popover and, beside
   it, the icon-only **Display config** popover
   (`:material/display_settings:`). Open it: two sliders, **Last messages**
   (default 8) and **First n characters** (default 200), each toggled by a
   pill. Move each slider and confirm the transcript updates live while the
   popover stays open.
4. Queue an access-rule or generate job and watch the compact **Working ·
   thinking…** badge on the title row — not a tall status card. **Cancel
   job** sits on that same row, beside **Close**.

**Expected result**: CoCo lives in the rail; the app owns the left column.
The transcript stays compact regardless of how long the conversation runs,
because of the Display config sliders, not because of a fixed truncation.
Same underlying primitive (`panel()`) as `make backlog`.

**Troubleshooting**: If the Display config popover is missing, confirm your
checkout is at least `0.1.8` (`uv run python -c "import streamlit_coco as c;
print(c.__version__)"`) — the popover shipped in `0.1.8`; the connection
**Config file** picker shipped in `0.1.9`. The example's `pyproject.toml`
path-pins the library to this repo checkout.

---

## Wrap-up

You have now run every core interaction mode: interactive panel, approval
gates, structured output, headless, a from-scratch build, and a Copilot rail
embedded in a product app. Next: read through
[`demo-guide.md`](demo-guide.html) and do one timed dry run.
