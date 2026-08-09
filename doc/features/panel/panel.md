# Panel + chat input

## What

`panel()` renders CoCo session status, transcript (or field output), approvals, and Stop controls with `@st.fragment` polling. Apps own the prompt surface via `chat_input_bar()` / `st.chat_input` + `send_prompt()`.

## Why

Streamlit apps need a non-blocking CoCo embed: stream replies, pause for HITL, and keep the rest of the page interactive without remounting the whole agent UI.

## How to use

1. Build `CocoOptions`, optionally `check_environment` + `render_start_gate`.
2. `session = get_or_create_session(opts, key=...)`.
3. `panel(session, warm_up=True, show_status=True, run_every=0.25)`.
4. `chat_input_bar(session)` (or your own `st.chat_input` calling `send_prompt`).

Demo: `make chat` → `examples/chat_app.py`.

## Limitations

- Full-page reruns outside the fragment can still reset unrelated widgets if the app is not careful.
- Chat input lives outside the fragment; leaving `CONNECTING` triggers a full `st.rerun()` so the input re-enables.
- UI golden-path is manual (see checklist).

## Related

- Checklist: [`test-checklist.md`](test-checklist.md)
- Approvals / tools-display features for HITL cards
