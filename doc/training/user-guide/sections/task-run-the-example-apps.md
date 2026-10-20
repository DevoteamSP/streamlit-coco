# I want to run the example apps

**For** anyone evaluating or learning the library · **20 min** · **a Snowflake connection for the CoCo-backed demos**

You end up with each of the repo's example apps running locally, and know
which one demonstrates which part of the API.

## Before you start

- `streamlit-coco[sdk]` installed and `check_environment().ready` is `True`
  (see [Getting started](getting-started.html)).
- A checkout of the repo (the examples run from `make` targets, not from a
  pip install alone).
- `headless_pipeline.py` and the BI → Semantic estate-map/KPI screens run
  without a live Snowflake connection; the rest need one.

## Steps

1. Run the preferred-pattern chat demo:

   ```bash
   make chat
   ```

   This is `examples/chat_app.py` — the smallest working app built on
   `check_environment` → `render_start_gate` → `get_or_create_session` →
   `panel()` + `chat_input_bar()`. Its sidebar includes a test-prompt runner
   backed by `examples/testdata/prompts.json`.

2. Run the legacy all-in-one demo:

   ```bash
   make approval
   ```

   This is `examples/approval_gate.py`, built on the legacy CCv2 `chat()`
   helper instead of `panel()`.

3. Run the structured-output demo:

   ```bash
   make structured
   ```

   This is `examples/structured_output.py` — it sets `output_schema` and
   routes the agent's JSON into a widget via `on_structured_output` instead
   of chat text.

4. Run the headless demo from a terminal, no browser:

   ```bash
   make headless
   ```

   This is `examples/headless_pipeline.py` — pure async Python with no
   Streamlit import, driving `query()` and `CocoSession` directly.

5. Run the file-upload demo:

   ```bash
   make cwd-upload
   ```

   This is `examples/cwd_upload_chat.py` — `chat_input_bar(accept_file=...)`
   and `cwd_uploader()` wiring browser uploads into the agent's `cwd`.

6. Run the two multipage, right-rail demos:

   ```bash
   make backlog        # Product Backlog Desk — file/JSON-backed, no SQL
   make bi-semantic     # BI -> Semantic (alias: make tableau-semantic)
   ```

7. Run the guided app-generation demo:

   ```bash
   make app-builder
   ```

Each `make` target and its variables are listed in
[Command reference](reference-commands.html); what each example demonstrates
and what it needs is in [Example apps reference](reference-examples.html).

## Result

Each `make` target opens (or prints, for `make headless`) a running app on
its own port. Nothing outside `examples/` is modified by running a demo;
generated artifacts land under each example's own `out/` or `data/`
directory — see [Outputs](outputs.html).

## Variations

- `make run` runs `examples/chat_app.py` by default; set `EXAMPLE=` to point
  it at a different example file.
- `make tableau-semantic` is a deprecated alias for `make bi-semantic` — use
  the latter.

## If it fails

- [Preview won't start](../../technical-guide/help.html#preview-wont-start)
- ["Fix with CoCo" not wired for a screen](../../technical-guide/help.html#fix-with-coco-not-wired)
- [Preview log parse miss](../../technical-guide/help.html#preview-log-parse-miss)
