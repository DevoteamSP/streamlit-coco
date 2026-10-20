# Case 1 — Simple: the preferred pattern, guided

**Level:** Simple — fully guided, sample data. **Time:** 20–30 min.

## Context

Every integration of `streamlit-coco` starts from the same shape: you own
the Streamlit page, CoCo owns the session. `examples/chat_app.py` is the
bundled, working reference for that shape — the same four calls the
[README quickstart](../../../README.md#quickstart) shows in isolation:
`check_environment()`, `render_start_gate()`, `get_or_create_session()`, and
`panel()` + `chat_input_bar()`.

## Goal

Run the bundled reference app, identify each of the four calls in the
source, and exercise both a read-only turn and an approval-gated turn — so
you can point at any line of `chat_app.py` and say what it does.

## Data

**Supplied.** No Snowflake objects need creating: `SNOWFLAKE_SAMPLE_DATA`
(bundled in any Snowflake account with sample data enabled), specifically
the `TPCH_SF1` schema, is read-only and available by default. A curated set
of prompts is also supplied at `examples/testdata/prompts.json`, browsable
from the **Test prompts** sidebar toggle in `make chat`.

## Steps

1. Confirm your environment is ready — the [setup checklist](../enablement/setup.html)
   should be fully checked before you start.
2. Run `make chat`. This launches `examples/chat_app.py`.
3. Open `examples/chat_app.py` in an editor next to the browser tab. Find
   and read, in order:
   - `env = st_coco.check_environment(connection=connection)` — probes SDK,
     CLI, and Snowflake config without starting an agent.
   - `st_coco.render_start_gate(opts, session_key=SESSION_KEY, gate_key=GATE_KEY, env=env)`
     — the landing screen; returns `False` until you click **Start CoCo
     Chat**.
   - `session = st_coco.get_or_create_session(opts, key=SESSION_KEY)` — gets
     or creates the background worker, stored in `st.session_state`.
   - `st_coco.panel(session=session, ...)` followed by
     `st_coco.chat_input_bar(session, ...)` — the transcript/output UI and
     the input box.
4. In the browser, click **Start CoCo Chat** if you have not already.
5. Type: *"What tables are available in SNOWFLAKE_SAMPLE_DATA.TPCH_SF1?"*
   Watch the transcript stream progressively rather than appear all at once,
   and note the tool card that appears.
6. Type: *"Create a summary table called TOP_CUSTOMERS in my schema."* An
   approval banner appears with **Approve once**, **Always allow**, **Deny**.
   Click **Deny** with a reason — confirm the agent acknowledges it and does
   not create the table.

## Expected result

- The transcript for step 5 renders progressively, with at least one tool
  card visible (typically SQL or Glob).
- The transcript for step 6 pauses on an approval banner before any table is
  created; denying it leaves no new object in your schema.
- You can name, from memory, which of the four calls in `chat_app.py`
  produced the start gate, the session, and the panel.

## Where to look if stuck

- If the app never leaves the start gate or the transcript never starts
  streaming: [`help.html#session-stuck-connecting`](../technical-guide/help.html#session-stuck-connecting)
  and [`help.html#coco-connection-error`](../technical-guide/help.html#coco-connection-error).
- If no approval banner appears for the `CREATE TABLE` request, re-check
  `require_approval_for` in `chat_app.py`'s sidebar **Requires approval**
  pills, or the setup checklist's environment check step.
