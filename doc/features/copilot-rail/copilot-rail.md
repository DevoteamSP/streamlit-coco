# Copilot rail

Reusable right-rail Copilot for Streamlit apps: connection, queued jobs,
transcript compactness, `panel()`, and `chat_input_bar()`.

**Status:** Shipped in **`0.1.6`**. Example questions + Display config popover in **`0.1.8`**.

## What

`copilot_rail()` is an app-agnostic column:

1. Title row: **Copilot**, **Cancel job** (when a job is active), **Close**
2. Connection popover with an icon-only **Display config** popover beside it (`:material/display_settings:`, no label; hover = **Display config**). While CoCo is busy, a compact **Working · thinking…** (or tool / needs-input) badge sits on that same row — not a tall status card.
3. Active job caption
4. `panel()` (approvals, stream, stop)
5. After Connect, on an empty transcript: **example question** buttons (`title` on the button, `question` on hover). Click sends the question to CoCo. They hide after the first user/assistant turn or while a job is queued.
6. Chat input

`transcript_display_config()` is the rail control: pills plus sliders for
last-message count and first-*n* characters. `transcript_view_pills()` stays
exported for apps that only call `panel()`. The pill label is collapsed (no
**Transcript** heading) and there is no “Showing last N · …” caption.

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
    example_questions=[
        {"title": "List the files", "question": "What files are in cwd?"},
    ],
)
```

Queued jobs: set `status="queued"` and a `prompt`. When the session is ready
the rail sends once and calls `on_job_sent` with `status="sent"`. When the
session leaves the turn (`COMPLETED` / `ERROR` / `CANCELLED`, or `READY` after
it has actually run), `on_job_finished` is called so **Cancel job** can hide.

Display config (default **on**):

| Control | Effect |
| --- | --- |
| Last messages (pill + slider) | `max_messages=` (default 8, slider 1–50) + Load earlier |
| First n characters (pill + slider) | `preview_chars=` (default 200, slider 40–1000) on user/assistant text |

Slider and pill changes fragment-rerun the rail only; the popover stays open
so the transcript updates live.

Example questions (opt-in via `example_questions=`): after Connect, starter
buttons sit under the empty transcript. Hover shows the full question; click
calls `send_prompt`. They disappear once a turn starts, the chat has a user
or assistant message, or a job is present, and return after **Clear chat**.

## Limitations

- Callers still own session lifecycle (reset on cwd / schema change).
- Connection + Display config live in a rail fragment: changing pills or
  sliders reruns Copilot only, not the host page. The popover stays open.
  `panel()` still has its own streaming fragment so the icon stays clickable
  while CoCo runs.
- Tool cards are not character-truncated (they are already compact expanders).
- Version tag for this API is **`0.1.6`** (`pip install "streamlit-coco[sdk]==0.1.6"`).

## Related

- Checklist: [`test-checklist.md`](test-checklist.md)
- Panel primitive: [`../panel/panel.md`](../panel/panel.md)
