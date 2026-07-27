# Headless query & multi-turn session

## What

- `streamlit_coco.query(prompt, options=...)` — single-turn async iterator over `CocoEvent`s
- `CocoSession.stream()` — multi-turn async event stream from the background worker
- `await CocoSession.run(prompt)` — send a prompt and wait until the turn completes

No Streamlit browser UI is required. Approvals can be resolved programmatically with `approve_pending` / `deny_pending`.

## Why

Automation authors need jobs, wizards, and CI paths that share options and event parsing with the UI.

## How to use

```python
import asyncio
import streamlit_coco as coco

async def main():
    opts = coco.CocoOptions(cwd=".", allowed_tools=["Read", "Glob", "Grep"])

    # Single-turn
    async for event in coco.query("List files.", options=opts):
        ...

    # Multi-turn
    session = coco.CocoSession(options=opts)
    session.start()
    session.ensure_ready()
    result = await session.run("Summarize this repo.")
    session.send("Follow-up question")
    async for event in session.stream():
        if event.type == "result":
            break
    session.close()

asyncio.run(main())
```

Demo: `make headless` → `examples/headless_pipeline.py`.

## Limitations

- Streamlit remains a package dependency (apps install it), but **core headless imports do not load Streamlit** — `import streamlit_coco` + `CocoSession` / `query` / permissions stay UI-free. Accessing `panel` / `chat` loads Streamlit lazily.
- AskUserQuestion / ExitPlanMode always block until resolved or timed out — scripts must auto-approve or answer.
- Requires CoCo CLI + Snowflake connection like the UI.

## Related

- Checklist: [`test-checklist.md`](test-checklist.md)
- Roadmap: Phase 3 headless items (shipped)
