# Assessment Quiz — streamlit-coco

Pass threshold: **8/10**. Answer key at the bottom — no peeking until you've attempted all
10.

1. **(Multiple choice)** What does `streamlit-coco` primarily add on top of the raw Cortex
   Code Agent SDK for a Streamlit developer?
   a) A different LLM
   b) Session management, streaming render, tool cards, and approval UI wired for Streamlit reruns
   c) A replacement for the CoCo CLI
   d) SQL query optimization

2. **(Short answer)** In the preferred integration pattern, what four function calls make
   up the typical app flow (in order)?

3. **(Multiple choice)** Which tools are **not** auto-approved by default when you set
   `require_approval_for=["Edit", "Write", "Bash"]`?
   a) Read, Glob, Grep
   b) Edit, Write, Bash
   c) Everything is auto-approved
   d) None — everything requires approval regardless of config

4. **(Short answer)** Name one function you would use to run `streamlit-coco` with **no**
   Streamlit UI at all (e.g. from a CI script).

5. **(Multiple choice)** What must be true for `check_environment(...).ready` to return `True`?
   a) Only that Streamlit is installed
   b) SDK installed, CoCo CLI reachable, and a valid Snowflake connection configured
   c) Only that the Snowflake account has Cortex Code access
   d) Only that `cortex --version` succeeds

6. **(Short answer)** Which `make` target runs the Product Backlog Desk demo, and what
   makes it different from `make chat`? Name one other multipage demo that uses the same
   right-rail pattern.

7. **(Multiple choice)** As of `0.1.6`, which of these features is available in the library?
   a) `copilot_rail()` (right-rail Copilot around `panel()`)
   b) Native SPCS deployment
   c) Multi-tenant billing
   d) Slack integration

8. **(Short answer)** If a user denies an approval request, what happens next in the agent flow?

9. **(Multiple choice)** Where would you find the manual golden-path checklists that must
   be signed off before a release?
   a) `README.md`
   b) `doc/features/<feature>/test-checklist.md`
   c) `CHANGELOG.md`
   d) `pyproject.toml`

10. **(Short answer)** What is the current Snow Builders level of this asset, and name one
    concrete gap that is currently blocking promotion to the next level.

---

## Answer key

1. **b** — it's the Streamlit-specific plumbing (session, streaming, tool cards, approvals), not a different model or a CLI replacement.
2. `check_environment()` → `render_start_gate()` → `get_or_create_session()` → `panel()` (+ `chat_input_bar()`).
3. **b** — Edit, Write, and Bash are exactly the tools you named as requiring approval; Read/Glob/Grep in `allowed_tools` auto-run.
4. `query()` (the headless async API — see `examples/headless_pipeline.py`, `make headless`).
5. **b** — all three: SDK installed, CLI reachable, valid Snowflake connection.
6. `make backlog` — a multipage, file-backed (no SQL) business demo (Board/Epic/Ticket/Release) with a right-rail Copilot, distinct from the single-page chat demo in `make chat`. The other first-party rail demo is `make bi-semantic` (BI → Semantic: Tableau and Power BI).
7. **a** — `copilot_rail()` shipped in `0.1.6`. File upload into `cwd` shipped earlier (`0.1.5`). SPCS deployment, multi-tenant billing, and Slack integration are not implemented.
8. The agent acknowledges the denial (optionally with the user's reason) and can propose an alternative — the destructive action does not execute.
9. **b** — `doc/features/<feature>/test-checklist.md`, indexed from `doc/features/README.md`.
10. **N0 (alpha), targeting N1.** Remaining gaps include: community sample-app count still below 3 contributed apps, no additional consultant trained via W01 beyond the owner, copilot-rail live checklist still pending. (Check the latest gap report in `dsp-assets/audits/streamlit-coco/` for the current list.)
