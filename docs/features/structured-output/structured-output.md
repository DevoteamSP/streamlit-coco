# Structured output

## What

When the agent returns structured JSON (SDK `output_format` / `CocoOptions.output_schema`, or result payload), streamlit-coco can show it inline in the transcript or hand it to the app via `on_structured_output` / `structured_output_container`.

## Why

Downstream Streamlit widgets (metrics, dataframes, forms) should consume typed agent results without scraping free text.

## How to use

1. **Inline (default):** `panel(session)` with no callback — structured items may appear in the transcript when enabled.
2. **Callback:** `panel(..., on_structured_output=fn)` or legacy `chat(..., on_structured_output=fn)` — default inline structured panel is skipped.
3. **Schema (SDK):** set `CocoOptions.output_schema={...}` so the agent is constrained; read `session.chat_result().structured_output`.

Demos: `make structured` (`examples/structured_output.py`); chat prompt `structured-json`.

## Limitations

- Chat prompt `structured-json` asks for JSON in the reply; it does not by itself set `output_schema` unless the app configures it.
- Callback fires once per result id (fragment remount should not duplicate).
- Non-dict payloads are wrapped as `{"value": ...}` when needed.

## Related

- Checklist: [`test-checklist.md`](test-checklist.md)
