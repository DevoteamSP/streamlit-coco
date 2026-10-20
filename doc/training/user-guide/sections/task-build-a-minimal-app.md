# I want to build a minimal CoCo app

**For** a Python developer building a Streamlit app · **10 min** · **a working Python environment**

You end up with a single-page Streamlit app that embeds a CoCo panel and
input bar, using the preferred integration pattern.

## Before you start

- `streamlit-coco[sdk]` installed (see Enablement
  [`setup.html`](../../enablement/setup.html)).
- A Snowflake connection configured and reachable —
  `check_environment().ready` should already be `True`; see
  [Getting started](getting-started.html).
- No prior CoCo app is required; this is the starting point for every other
  task page in this guide.

## Steps

1. Create `streamlit_app.py` and construct a `CocoOptions` with at least a
   connection name:

   ```python
   import streamlit as st
   import streamlit_coco as st_coco

   st.set_page_config(page_title="Minimal CoCo app")

   options = st_coco.CocoOptions(
       connection="my_connection",
       cwd=".",
   )
   ```

2. Call `check_environment()` through the landing gate, and stop the script
   if it is not ready:

   ```python
   if not st_coco.render_start_gate(options):
       st.stop()
   ```

   `render_start_gate()` renders the landing screen itself (SDK/CLI/Snowflake
   status, a **Start** action) and returns `False` while the environment or
   the user has not confirmed — your app must call `st.stop()` in that case,
   `render_start_gate()` does not stop the script for you.

3. Get or create the session for this page, and mount the panel and its
   input bar:

   ```python
   session = st_coco.get_or_create_session(options)
   st_coco.panel(session)
   st_coco.chat_input_bar(session)
   ```

   `get_or_create_session()` stores the session in
   `st.session_state["coco"]` by default (override with `key=`) and reuses it
   across reruns.

4. Run the app:

   ```bash
   streamlit run streamlit_app.py
   ```

5. Type a prompt in the input bar at the bottom of the page and confirm the
   transcript streams a response above it.

## Result

A browser tab showing the CoCo panel: a status header, an empty transcript,
and the chat input bar. After a prompt, the transcript fills with the
agent's streamed response and any tool cards it used. No file is written by
this minimal app on its own — file output starts once you add uploads
([I want to add file uploads](task-add-file-uploads.html)) or the agent
writes to `cwd`.

## Variations

- Use `copilot_rail()` instead of `panel()` + `chat_input_bar()` to embed CoCo
  as a right-hand rail inside a larger, multipage app rather than a
  single-page chat — see the Backlog Desk and BI → Semantic examples in
  [Example apps reference](reference-examples.html).
- Set `panel(session, output_mode="field")` to render only the latest
  assistant output instead of the full transcript.
- Set `warm_up=True` on `render_start_gate()` (the default) to start the
  session as soon as the gate passes, instead of waiting for the first
  prompt.

## If it fails

- [`SDKNotInstalledError`](../../technical-guide/help.html#sdk-not-installed)
- [`CLINotFoundError`](../../technical-guide/help.html#cli-not-found)
- [Session stuck on "Starting CoCo…"](../../technical-guide/help.html#session-stuck-connecting)
- [Input disabled after boot](../../technical-guide/help.html#input-disabled-after-boot)
