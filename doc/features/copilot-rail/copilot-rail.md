# Copilot rail

Reusable right-rail Copilot for Streamlit apps: connection, queued jobs,
transcript compactness, `panel()`, and `chat_input_bar()`.

**Status:** Shipped in **`0.1.6`**.

## What

`copilot_rail()` is an app-agnostic column:

1. Title row: **Copilot**, **Cancel job** (when a job is active), **Close**
2. Connection popover with transcript pills beside it (**Last messages**, **First 200 characters**). While CoCo is busy, a compact **Working · thinking…** (or tool / needs-input) badge sits on that same row — not a tall status card.
3. Active job caption
4. `panel()` (approvals, stream, stop)
5. Chat input

`transcript_view_pills()` is also exported for apps that only call `panel()`.
The pill label is collapsed (no **Transcript** heading) and there is no
“Showing last N · …” caption.

`panel()` / `render_transcript()` gain `preview_chars=` (truncate user/assistant
text). Clipboard copy stays available via `show_copy=` (the rail defaults it
**off** — exec demos should not flash copy/paste controls).

Long `status_caption` paths (backtick segments over 100 characters) are shown
with `...` in the middle so the leaf of the cwd stays visible.

## Why

Embedding CoCo in a product demo needs one rail, not a chat window: connect
once, queue jobs from the app, keep the transcript short enough for a room.
The BI → Semantic example proved the pattern; it belongs in the library.

## How to use

```python
import streamlit_coco as st_coco

session = st_coco.get_or_create_session(opts, key="copilot")
st_coco.copilot_rail(
    session,
    connected=True,
    connections=["analytics"],
    connection_name="analytics",
    on_connect=lambda name: ...,
    on_disconnect=lambda: ...,
    job=st.session_state.get("job"),  # {prompt, label, status, expect_structured}
    on_job_sent=lambda job: st.session_state.update(job=job),
    on_job_finished=lambda job: st.session_state.pop("job", None),
    on_structured_output=on_payload,
    show_copy=False,
    show_transcript_filters=True,
)
```

Queued jobs: set `status="queued"` and a `prompt`. When the session is ready
the rail sends once and calls `on_job_sent` with `status="sent"`. When the
session leaves the turn (`COMPLETED` / `ERROR` / `CANCELLED`, or `READY` after
it has actually run), `on_job_finished` is called so **Cancel job** can hide.

Transcript pills (default **on**):

| Pill | Effect |
| --- | --- |
| Last messages | `max_messages=8` (+ Load earlier) |
| First 200 characters | `preview_chars=200` on user/assistant text |

## Limitations

- Callers still own session lifecycle (reset on cwd / schema change).
- Connection + pills live in a rail fragment: changing pills reruns Copilot
  only, not the host page. `panel()` still has its own streaming fragment so
  the pills stay clickable while CoCo runs.
- Tool cards are not character-truncated (they are already compact expanders).
- Version tag for this API is **`0.1.6`** (`pip install "streamlit-coco[sdk]==0.1.6"`).

## Related

- Checklist: [`test-checklist.md`](test-checklist.md)
- Panel primitive: [`../panel/panel.md`](../panel/panel.md)
