# Demo Script — Streamlit CoCo

> Scripted 12-minute live demo showcasing panel(), approval gates, and headless query.

**Audience**: Technical decision-makers, data engineers, Snowflake practitioners  
**Prerequisites**: Snowflake account with Cortex Code access, CoCo CLI installed, Python 3.11+  
**Demo app**: `examples/chat_app.py` (via `make chat`)

---

## Setup (before the demo)

1. Confirm CoCo CLI is authenticated: `cortex --version`
2. Activate the virtualenv: `source .venv/bin/activate` or `uv sync`
3. Have a Snowflake database with sample tables (e.g., `SNOWFLAKE_SAMPLE_DATA.TPCH_SF1`)
4. Terminal + browser side by side

---

## Act 1 — First impression (3 min)

### Talking point
> "What if your Streamlit app had a built-in AI coding agent that can query Snowflake, read files, and write code — with guardrails?"

### Steps

1. Show `examples/chat_app.py` — highlight it's ~20 lines of Python
2. Run: `make chat`
3. Browser opens → show the panel UI (empty state, model/connection header)
4. Type: *"What tables are available in SNOWFLAKE_SAMPLE_DATA.TPCH_SF1?"*
5. Watch the streaming transcript render in real-time
6. Point out: tool cards appear showing what the agent is doing (Glob, SQL)

### Key message
> "10 lines of code. Full agent UI with streaming, tool visibility, and session management."

---

## Act 2 — Approval gates (4 min)

### Talking point
> "AI agents doing things autonomously is powerful — but dangerous. We built safety in from day one."

### Steps

1. Type: *"Show me the top 5 customers by total order amount. Write the SQL and run it."*
2. Agent proposes SQL → **approval gate fires** (orange banner)
3. Walk through the approval UI:
   - Show the full SQL statement the agent wants to execute
   - Click **"Approve"** → SQL executes, results appear
4. Type: *"Now create a summary table called TOP_CUSTOMERS in my schema."*
5. Agent proposes CREATE TABLE → approval gate fires again
6. This time click **"Deny"** with reason: "Let's not create tables in the demo"
7. Agent acknowledges the denial and suggests an alternative

### Key message
> "Every destructive action — SQL, file writes, bash commands — requires explicit human approval. No surprises."

---

## Act 3 — Structured output (3 min)

### Talking point
> "The agent doesn't just chat — it can feed structured data into your own Streamlit widgets."

### Steps

1. Switch to `examples/structured_output.py`: `make structured`
2. Show the code: `output_schema` defines what we expect back
3. Type: *"Give me a breakdown of orders by status"*
4. Agent returns structured JSON → app renders it as a Streamlit bar chart
5. Highlight: no parsing, no regex — the agent respects the schema contract

### Key message
> "Agent output flows into your widgets. Build dashboards that update themselves via natural language."

---

## Act 4 — Headless mode (2 min)

### Talking point
> "Not everything needs a UI. Same library, no Streamlit required."

### Steps

1. Show `examples/headless_pipeline.py` — pure async Python
2. Run: `make headless`
3. Terminal shows events streaming as the agent works
4. Point out: same `query()` function, same approval hooks available programmatically

### Key message
> "CI pipelines, scheduled jobs, batch processing — embed CoCo anywhere Python runs."

---

## Wrap-up & Q&A (1 min)

### Summary slide points

- `pip install streamlit-coco[sdk]` — 5 minutes to first app
- Safety: approval gates on by default for all destructive tools
- Flexible: interactive panel, structured output, or headless
- Open source (Apache-2.0), built for Snowflake

### Common questions

| Question | Answer |
|----------|--------|
| Does it work with SiS? | Not yet — pure Python, waiting for the CoCo API |
| What LLM does it use? | Whatever Cortex Code uses (Claude, ChatGPT...) — no config needed |
| Can I customize which tools need approval? | Yes — `permission_mode` in `CocoOptions` |
| Is it production-ready? | Alpha (0.1.0) — use in internal tools today, production after N1 |

---

## Cleanup

```bash
# Stop the running app (Ctrl+C)
# No tables or artifacts were created (we denied the CREATE TABLE)
```

---

*Demo duration: ~12 minutes + Q&A*
