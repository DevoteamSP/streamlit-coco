# App viewer

Reusable Streamlit preview column: child process, iframe, and **Fix with CoCo**.

**Status:** Shipped in **`0.1.7`**.

## What

`app_viewer()` is an app-agnostic column:

1. Title row: **Preview**, optional `title_extra` (host chrome), optional **Close**
2. Toolbar: **Run** · **Stop** · **Open** · **Fix with CoCo**
3. Current traceback expander (when `.preview.log` has a live exception)
4. Iframe of the child Streamlit app

Helpers (Streamlit-free) are also exported:

| Helper | Role |
| --- | --- |
| `start_app_preview` / `stop_app_preview` | Spawn / kill `streamlit run` in `app_dir` |
| `preview_running` / `preview_url` | Recover from `.preview.pid` / `.preview.port` |
| `last_preview_exception` / `preview_log_tail` | Scrape `.preview.log` |
| `default_fix_prompt` | Prompt text only — the host queues the job |

The component does **not** import `copilot_rail` or know about job queues.
Hosts compose `app_viewer` | `copilot_rail` and wire `on_fix`.

## Why

Embedding a generated Streamlit app next to CoCo needs one preview column, not
a studio widget. The BI → Semantic example proved the pattern (child process,
iframe, log scrape); it belongs in the library the same way `copilot_rail()`
was extracted in `0.1.6`.

## How to use

```python
import streamlit_coco as st_coco

def _on_fix(trace: str) -> None:
    queue_job(
        "streamlit",
        prompt=st_coco.default_fix_prompt(trace, dest),
        label="Fix Streamlit app",
    )
    open_copilot_for_job()

st_coco.app_viewer(
    dest,  # folder with streamlit_app.py — not the host app
    key="preview",
    port=8511,
    env={"TTS_DATA_MODE": "disconnected"},
    on_fix=_on_fix,
    on_close=lambda: set_preview_open(False),
)
```

**Fix with CoCo** is primary when a current traceback exists; it stays
clickable otherwise (sends the log tail, or an empty string that
`default_fix_prompt` turns into an inspect stub). `on_fix` is required for
the button to do work; if omitted, the button toasts “wire `on_fix=`”.

## Limitations

- The child is another origin (`127.0.0.1:8511`–`:8520`). The parent **cannot**
  read the red exception from the iframe DOM. Fix is **log scrape + optional
  log tail**, not DOM capture.
- Streamlit in Snowflake / Native App (`0.2.5` / `0.3.0`) cannot spawn a local
  `streamlit run`. Out of scope for this cut.
- One preview per `app_dir`. Do not point `app_dir` at the host app.
- After CoCo Writes, the child hot-reloads on its own; the viewer only
  re-scrapes the log.
- Log format drift: the parser looks for `Uncaught app exception` /
  `Traceback (most recent call last):` and treats a later timestamped line as
  “error cleared”. Fix still sends the tail if the parse misses.
- Version tag for this API is **`0.1.7`**.

## Related

- Checklist: [`test-checklist.md`](test-checklist.md)
- Copilot rail: [`../copilot-rail/copilot-rail.md`](../copilot-rail/copilot-rail.md)
- Example: [`examples/bi_to_semantic/`](../../../examples/bi_to_semantic/)
