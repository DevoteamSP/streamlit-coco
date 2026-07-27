# NDJSON stream fixtures

Recorded **cortex CLI** NDJSON lines for parser regression tests. Each file is one or more newline-delimited JSON objects (same format as SDK stdout).

| File | Covers |
| --- | --- |
| `assistant_text.ndjson` | Plain assistant reply |
| `assistant_tool_glob.ndjson` | `tool_use` (Glob) |
| `assistant_tool_result.ndjson` | `tool_result` block |
| `user_tool_result.ndjson` | `tool_result` on user message (SDK path) |
| `result_success.ndjson` | Turn completion |
| `result_structured.ndjson` | `structured_output` on result |
| `stream_delta.ndjson` | Streaming `content_block_delta` |
| `system_init.ndjson` | Session init metadata |
| `turn_glob.ndjson` | Multi-line turn (stream → tool → result) |

**Manifest:** [`manifest.json`](manifest.json) — expected event types/fields per file.

**Tests:** `tests/test_ndjson_fixtures.py` (run via `make check`).

To add a fixture:

1. Append a `.ndjson` file with representative lines.
2. Add an entry to `manifest.json` with `expect` assertions (subset of `CocoEvent` fields).
3. Run `make test`.

Live prompts for manual UI validation remain in [`../../examples/testdata/prompts.json`](../../examples/testdata/prompts.json).
