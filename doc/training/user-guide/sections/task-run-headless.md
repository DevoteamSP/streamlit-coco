# I want to run CoCo headless

**For** a developer scripting CoCo from a CI job or a terminal · **15 min** · **a terminal, no Streamlit UI needed**

You end up with a script that drives the agent without importing Streamlit,
either for a single turn or a multi-turn session, resolving any approvals in
code.

## Before you start

- `streamlit-coco[sdk]` installed; `check_environment().ready` is `True` for
  the connection you will use (see [Getting started](getting-started.html)).
- Core headless symbols (`CocoSession`, `query`, `CocoOptions`, the
  permission and error types) import without loading Streamlit — UI exports
  resolve lazily, so a plain `import streamlit_coco` is safe in a script that
  never touches Streamlit.

## Steps

1. For a single turn, use `query()`:

   ```python
   import asyncio
   import streamlit_coco as st_coco

   async def main() -> None:
       options = st_coco.CocoOptions(connection="my_connection")
       async for event in st_coco.query("Summarize sales by region.", options=options):
           if event.type == "assistant_text":
               print(event.text)

   asyncio.run(main())
   ```

2. For a multi-turn session without any UI, drive `CocoSession` directly:

   ```python
   session = st_coco.CocoSession(options=options, key="headless")
   session.start()
   await session.ensure_ready(timeout=120)
   result = await session.run("List the tables in my schema.")
   async for event in session.stream():
       ...
   session.close()
   ```

3. Resolve approvals in code instead of a UI — check
   `session.chat_result().pending_approval` after a run and call
   `approve_pending()` / `deny_pending()` as shown in
   [I want to configure tool approvals](task-configure-tool-approvals.html),
   or pre-approve everything you expect via `allowed_tools` so the script
   never blocks.

4. Convert accumulated events to a table when you need to inspect or log
   them in bulk:

   ```python
   df = st_coco.events_to_dataframe(session.events)  # needs pandas
   ```

## Result

`query()` yields `CocoEvent` objects for a single turn and returns nothing
else — there is no session object to keep around afterwards. `CocoSession`
run outside Streamlit behaves exactly as it does inside a `panel()`: the same
transcript, the same `CocoRunStatus` transitions, the same approval pauses —
only the rendering is missing.

## Variations

- `examples/headless_pipeline.py` (`make headless`) shows both `query()` and
  `CocoSession` from a plain terminal script, each in its own event loop.
- `query()` raises `SDKNotInstalledError` or `QueryError` (or another
  `CocoError` subclass) instead of returning a partial result on failure —
  wrap the call accordingly for a CI job.

## If it fails

- [`SDKNotInstalledError`](../../technical-guide/help.html#sdk-not-installed)
- [Session not ready](../../technical-guide/help.html#session-not-ready)
