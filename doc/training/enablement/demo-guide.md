# Demo guide

A 10-minute scripted demo: opening hook, live walkthrough, close. Audience:
technical decision-makers, data engineers, Snowflake practitioners.

## Technical requirements checklist (before the demo)

- [ ] Snowflake account with Cortex Code access, connection configured
- [ ] `cortex --version` succeeds
- [ ] `make install` run, `make check` passes
- [ ] A Snowflake database with sample tables available (e.g.
      `SNOWFLAKE_SAMPLE_DATA.TPCH_SF1`)
- [ ] Terminal and browser windows arranged side by side
- [ ] Dry-run once, timed, within the last 24 hours

## Opening hook (30 sec — the problem)

> "Wiring a CoCo agent into a Streamlit app yourself means building session
> management across reruns, streaming render, tool-card display, and safety
> gates from scratch. `streamlit-coco` gives you that in a few lines of
> Python. Let me show you."

## Live walkthrough (7 min — step-by-step with talking points)

### Step 1 — First impression (2 min)

1. Show `examples/chat_app.py` — point out it is a short, readable file
   built from four calls: `check_environment()`, `render_start_gate()`,
   `get_or_create_session()`, `panel()` + `chat_input_bar()`.
2. Run `make chat`.
3. Browser opens → show the panel UI (start gate, then the empty transcript
   and status line once started).
4. Type: *"What tables are available in SNOWFLAKE_SAMPLE_DATA.TPCH_SF1?"*
5. Watch the streaming transcript render in real time; point out the tool
   card that appears (Glob/SQL).

> Talking point: "A short Python file. Full agent UI with streaming, tool
> visibility, and session management handled for you."

### Step 2 — Approval gates (3 min)

1. Type: *"Show me the top 5 customers by total order amount. Write the SQL
   and run it."*
2. Agent proposes SQL → approval banner fires. Walk through the full SQL
   shown, click **Approve once** → results appear.
3. Type: *"Now create a summary table called TOP_CUSTOMERS in my schema."*
4. Approval gate fires again — this time click **Deny** with a reason
   ("let's not create tables in the demo"). Agent acknowledges and suggests
   an alternative.

> Talking point: "Every destructive action — SQL, file writes, bash
> commands — requires explicit human approval, configured per tool in
> `CocoOptions.require_approval_for`."

### Step 3 — Structured output (1.5 min)

1. Switch to `make structured` (`examples/structured_output.py`).
2. Show the `output_schema` in the code.
3. Type: *"Give me a breakdown of orders by status."*
4. Agent returns structured JSON → app renders it as a chart, not raw text.

> Talking point: "Agent output can flow directly into your own widgets via
> an `on_structured_output` callback — no manual JSON parsing."

### Buffer (0.5 min)

Land on the close from wherever you are in Step 3. If there is time left in
the room after the scripted close, two things are worth showing but are
**not** part of the timed 10-minute script:

- `make headless` (`examples/headless_pipeline.py`) — the same `query()` API
  with no Streamlit import, for CI and batch jobs.
- `make bi-semantic` or `make backlog` — `copilot_rail()`, showing CoCo as a
  right column in a product app rather than a full-page chat.

## Closing (2.5 min — value recap + CTA)

Summary points to land on screen or verbally:

- `pip install "streamlit-coco[sdk]"` — a working app in a handful of lines
- Approval gates on by default for destructive tools
- One library covers interactive panel, structured output, and headless use
- Open source (Apache-2.0), built for Snowflake

**Call to action**: "Try it against your own Snowflake account this week —
the quickstart in the README gets you to a working app quickly. Reach out to
the asset owner if you hit setup issues."

## If they ask… (FAQ)

| Question | Answer |
| --- | --- |
| Does it work with Streamlit in Snowflake (SiS)? | Not shipped today. Local deployment (CLI + Streamlit + Snowflake config on the same host) is the only shipped topology; SiS/SPCS are threat-model scope only. |
| What LLM does it use? | Whatever Cortex Code uses under the hood — no model configuration in this library beyond `CocoOptions.model`. |
| Can I customize which tools need approval? | Yes — `allowed_tools` / `require_approval_for` in `CocoOptions`, per tool. |
| Is it production-ready? | Alpha (`0.1.9`) — the API may still move. |
| How is this different from using the CoCo CLI directly? | This library handles the Streamlit-specific plumbing: rerun-safe session state, streaming render, tool cards, and approval UI — the CLI alone has none of that. |
| What about file uploads? | `upload_to_cwd()` / `cwd_uploader()` / `chat_input_bar(accept_file=...)` upload into the agent's working directory; see `make cwd-upload`. |
| What's `copilot_rail()`? | A right-rail Copilot around `panel()` — connection, queued jobs, and a Display config popover (message/character limits) for a compact transcript. See `make bi-semantic` / `make backlog`. |
| Is there an audit log of approvals? | Not persisted today — "Always allow" is session-scoped only and clears on reset. |

## Cleanup

```bash
# Stop the running app (Ctrl+C)
# No tables/artifacts were created if the CREATE TABLE approval was denied as scripted
```
