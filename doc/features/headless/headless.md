# Headless query & multi-turn session

## What

- `streamlit_coco.query(prompt, options=...)` — single-turn async iterator over `CocoEvent`s
- `CocoSession.stream()` — multi-turn async event stream from the background worker
- `await CocoSession.run(prompt)` — send a prompt and wait until the turn completes

- `streamlit_coco.conversation.Conversation` with a policy: the same rights as the Ask CoCo window, with each request answered in code

No Streamlit browser UI is required. A `CocoSession`'s own approvals are answered with `session.permission_manager.resolve(request_id, approved=...)`. A `Conversation`'s requests are plain data in `conv.view()["request"]`, answered with `conv.act({"type": "allow" | "decline", "id": ...})`.

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

Demo: `make headless` → `examples/headless_pipeline.py` (`query()`, a multi-turn `CocoSession`, and a `Conversation` with `policy.FolderPolicy` whose requests a script answers).

## Limitations

- Streamlit remains a package dependency (apps install it), but **core headless imports do not load Streamlit** — `import streamlit_coco` + `CocoSession` / `query` / `Conversation` / `policy` stay UI-free. Accessing `ask_coco` or `cwd_uploader` loads Streamlit lazily.
- AskUserQuestion / ExitPlanMode always block until resolved or timed out. Scripts must answer them (`conv.act({"type": "answer", ...})`, or `permission_manager.resolve` on a `CocoSession`).
- Requires CoCo CLI + Snowflake connection like the UI.

## Related

- Checklist: [`test-checklist.md`](test-checklist.md)
- Roadmap: Phase 3 headless items (shipped)
