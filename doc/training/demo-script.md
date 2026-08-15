# Demo Script (Training Copy) — streamlit-coco

> This is the training-pack copy of the demo script, restructured to the Devoteam N0→N1
> demo template (hook / walkthrough / close / FAQ). **Source of truth for content updates
> is [`doc/marketing/demo.md`](../marketing/demo.md)** — if you change one, update the other.

**Audience**: Technical decision-makers, data engineers, Snowflake practitioners
**Total time**: ~10–12 minutes + Q&A

## Technical requirements checklist (before the demo)

- [ ] Snowflake account with Cortex Code access, connection configured
- [ ] `cortex --version` succeeds
- [ ] `make install` run, `make check` passes
- [ ] A Snowflake database with sample tables available (e.g. `SNOWFLAKE_SAMPLE_DATA.TPCH_SF1`)
- [ ] Terminal and browser windows arranged side by side
- [ ] Dry-run once, timed, within the last 24 hours

---

## Opening hook (30 sec — the problem)

> "What if your Streamlit app had a built-in AI coding agent that can query Snowflake,
> read files, and write code — with guardrails? Today, wiring that up yourself means
> building session management, streaming rendering, tool-card display, and safety gates
> from scratch. `streamlit-coco` gives you all of that in about 10 lines of code."

---

## Live walkthrough (7 min — step-by-step with talking points)

### Step 1 — First impression (2 min)

1. Show `examples/chat_app.py` — point out it's ~20 lines of Python.
2. Run `make chat`.
3. Browser opens → show the panel UI (empty state, model/connection header).
4. Type: *"What tables are available in SNOWFLAKE_SAMPLE_DATA.TPCH_SF1?"*
5. Watch the streaming transcript render in real time; point out the tool card that
   appears (Glob/SQL).

> Talking point: "10 lines of code. Full agent UI with streaming, tool visibility, and
> session management."

### Step 2 — Approval gates (3 min)

1. Type: *"Show me the top 5 customers by total order amount. Write the SQL and run it."*
2. Agent proposes SQL → approval banner fires. Walk through the full SQL shown, click
   **Approve once** → results appear.
3. Type: *"Now create a summary table called TOP_CUSTOMERS in my schema."*
4. Approval gate fires again — this time click **Deny** with a reason ("let's not create
   tables in the demo"). Agent acknowledges and suggests an alternative.

> Talking point: "Every destructive action — SQL, file writes, bash commands — requires
> explicit human approval. No surprises."

### Step 3 — Structured output (1.5 min)

1. Switch to `make structured` (`examples/structured_output.py`).
2. Show the `output_schema` in the code.
3. Type: *"Give me a breakdown of orders by status."*
4. Agent returns structured JSON → app renders it as a chart, not raw text.

> Talking point: "Agent output flows into your widgets. Build dashboards that update
> themselves via natural language."

### Step 4 — Headless mode (0.5 min, optional if time is tight)

1. Show `examples/headless_pipeline.py`.
2. Run `make headless` — terminal streams events, no browser involved.

> Talking point: "CI pipelines, scheduled jobs, batch processing — embed CoCo anywhere
> Python runs."

### Step 5 — Copilot rail (optional if time allows, ~1 min)

1. Run `make bi-semantic` (or `make backlog`).
2. Point at the **right rail**: connection, compact transcript pills, jobs queued from the
   left-hand wizard — not a full-page chat.

> Talking point: "`copilot_rail()` is how CoCo sits *in* a product, not beside it as a
> chat toy. BI → Semantic is the long demo; Backlog Desk is the shorter one."

---

## Closing (2.5 min — value recap + CTA)

Summary points to land on screen or verbally:

- `pip install streamlit-coco[sdk]` — 5 minutes to first working app
- Safety by default — approval gates on for all destructive tools
- Flexible — interactive panel, structured output, or headless, same library
- Open source (Apache-2.0), purpose-built for Snowflake

**Call to action**: "Try it against your own Snowflake account this week — the quickstart
in the README gets you to a working app in under 10 minutes. Ping [owner] if you hit any
setup issues."

---

## If they ask… (FAQ)

| Question | Answer |
| --- | --- |
| Does it work with Streamlit in Snowflake (SiS)? | Not yet — pure Python, waiting on the CoCo API path; see roadmap. |
| What LLM does it use? | Whatever Cortex Code uses under the hood — no model config needed in this library. |
| Can I customize which tools need approval? | Yes — `allowed_tools` / `require_approval_for` in `CocoOptions`. |
| Is it production-ready? | Alpha (`0.1.7`) — fine for internal tools today; production readiness targeted at N1. |
| How is this different from just using the CoCo CLI directly? | This library handles the Streamlit-specific plumbing: rerun-safe session state, streaming render, tool cards, and approval UI — the CLI alone has none of that. |
| What about file uploads? | Supported since `0.1.5` — `upload_to_cwd()` / `cwd_uploader()`; see `make cwd-upload`. |
| What's `copilot_rail()`? | Shipped in `0.1.6` — a right-rail Copilot (connection, queued jobs, compact transcript) around `panel()`. See `make bi-semantic` / `make backlog`. |

---

## Cleanup

```bash
# Stop the running app (Ctrl+C)
# No tables/artifacts were created if the CREATE TABLE approval was denied as scripted
```
