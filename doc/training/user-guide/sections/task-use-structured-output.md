# I want to use structured output

**For** a developer rendering agent output into a widget instead of chat text · **15 min** · **a working minimal app**

You end up with a session that returns JSON matching a schema you define,
routed into your own widget instead of the transcript.

## Before you start

- A working minimal app ([I want to build a minimal CoCo app](task-build-a-minimal-app.html)).
- A JSON Schema describing the shape you want back. Do not include
  `$schema` or `$id` keys — the library strips them before passing the
  schema to the SDK, but a schema authored elsewhere (for example a shared
  contract file) may still carry them.

## Steps

1. Set `output_schema` on `CocoOptions`:

   ```python
   options = st_coco.CocoOptions(
       connection="my_connection",
       output_schema={
           "type": "object",
           "properties": {
               "status": {"type": "string"},
               "count": {"type": "integer"},
           },
           "required": ["status", "count"],
       },
   )
   ```

2. Handle the structured payload as it arrives, either with a callback or by
   reading it back after the turn:

   ```python
   def on_structured(payload: dict, result: st_coco.CocoChatResult) -> None:
       st.metric("Count", payload["count"])

   st_coco.panel(session, on_structured_output=on_structured)
   ```

   Or read `session.structured_output` / `session.chat_result().structured_output`
   after a turn completes, without a callback.

3. Optionally give the structured render its own container instead of
   letting it appear inline in the transcript:

   ```python
   box = st.container()
   st_coco.panel(session, structured_output_container=box)
   ```

4. For a one-off headless call, pass `output_schema` directly to `query()`
   instead of through `CocoOptions` — see
   [I want to run CoCo headless](task-run-headless.html).

## Result

When the agent's final result carries a structured payload, `panel()` (or
your `on_structured_output` callback) receives it as a Python `dict` matching
your schema, and `session.chat_result().structured_output` holds the same
value. If the turn produces no structured payload, these stay `None` — the
transcript still shows the plain-text answer.

## Variations

- `structured_output.py` demonstrates the whole flow — run it with
  `make structured` (see
  [Example apps reference](reference-examples.html)).
- `request_input(question, schema=...)` is a different mechanism: it collects
  a structured answer from the *user* between turns, not from the agent — see
  [API reference](reference-api.html).

## If it fails

- [`no schema with key or ref "https://json-schema.org/draft/2020-12/schema"`](../../technical-guide/help.html#schema-dollar-schema-rejected)
- [Structured output not rendering](../../technical-guide/help.html#structured-output-not-rendering)
