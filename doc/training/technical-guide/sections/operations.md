# Operations

## Run

There is no standalone server process for the library itself — it runs
inside whatever Streamlit app embeds it. The example apps are run through
Makefile targets:

| Target | Runs |
|---|---|
| `make run` | `examples/chat_app.py` (default `EXAMPLE`) |
| `make chat` | `examples/chat_app.py` |
| `make approval` | `examples/approval_gate.py` (legacy CCv2) |
| `make structured` | `examples/structured_output.py` |
| `make headless` | `examples/headless_pipeline.py` (no Streamlit) |
| `make backlog` | `examples/backlog_desk/` |
| `make cwd-upload` | `examples/cwd_upload_chat.py` |
| `make bi-semantic` (alias `make tableau-semantic`) | `examples/bi_to_semantic/` |
| `make app-builder` | `examples/app_builder/` |

Or run any Streamlit example directly: `uv run streamlit run examples/chat_app.py`.

## Schedule

Not applicable. streamlit-coco has no scheduler, no background job runner,
and no cron-driven component. Every run is interactive, started by opening
a Streamlit app.

## Monitor

- The agent transcript exists only in Streamlit session state, in-memory,
  for the life of the browser session. Nothing is persisted by default.
- `app_viewer()` writes `.preview.log`, `.preview.pid`, and `.preview.port`
  inside the previewed `app_dir` while a child preview process is running —
  this is the only on-disk log the library produces, and it is scoped to
  the preview subprocess, not the agent session.
- There is no persisted approval audit log (who approved what tool call,
  when) — this is open item **SEC-01**; see [security](security.html) and
  [limits](limits.html).
- Debug visibility into raw tool payloads is controlled by
  `STREAMLIT_COCO_DEBUG` / `COCO_DEBUG` (see [configuration](configuration.html));
  it changes what is *shown in the UI*, not what is written to disk.

## Cost and latency

LLM calls go through Snowflake Cortex via the CoCo CLI / SDK. Cost and
latency for those calls are a Snowflake Cortex concern — streamlit-coco
does not track, report, or budget tokens, warehouse credits, or call
latency. `CocoEvent` carries a `cost_usd` field and a `duration_ms` field
when the underlying SDK message provides them, but the library does not
aggregate, persist, or alert on these values; an app that wants cost/latency
tracking has to read those fields itself, per event.

## Cleanup

Between demo runs or when tearing down a session:

- `stop_session(session_key="coco", gate_key="coco_started")` — tears down
  the `CocoSession` (closes the background worker) and clears the
  start-gate flag, so the app returns to the start-gate screen.
- `session.close()` — closes a specific session without touching the
  start-gate flag.
- Kill any running preview process before switching `app_dir` on
  `app_viewer()`: use `stop_app_preview()` (or the **Stop** button in the
  UI). Only one preview process runs per `app_dir` at a time (see
  [limits](limits.html)).
- Clear generated artifacts between demo passes as needed:
  `_uploads/` under the agent `cwd` (browser uploads),
  `examples/bi_to_semantic/out/` and `examples/bi_to_semantic/../workspaces/bi_to_semantic/`
  (gitignored), `examples/app_builder/out/<slug>/` (named app projects —
  delete via the Library/Brief **Delete app** action or by removing the
  folder). None of these directories are cleaned automatically.
