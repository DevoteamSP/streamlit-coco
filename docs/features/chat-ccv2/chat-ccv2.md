# Legacy CCv2 chat

## What

`st_coco.chat()` mounts the Custom Components v2 all-in-one CoCo panel (built-in input, transcript, approvals, Stop) backed by static assets under `streamlit_coco/frontend/`.

## Why

Older apps and demos that want a single component call without owning `st.chat_input`. New apps should prefer `panel()` + app-owned input.

## How to use

```python
session = st_coco.CocoSession(options=opts, key="demo")
session.start()
st_coco.chat(session=session, key="coco_chat")
```

Demo: `make approval` → `examples/approval_gate.py`.

## CCv2 skill notes

- Registered once with `isolate_styles=True` (shadow-root CSS; styles do not leak into the host app).
- Frontend `export default` returns a cleanup that aborts listeners and removes the DOM root on unmount.
- `@st.fragment(run_every=…)` **pauses** while an approval is pending (parity with `panel()`).
- Triggers: `submit_prompt`, `approve_tool`, `deny_tool`, `cancel_run` only — no `provide_input` channel.
- Theme via `--st-*` CSS variables (including yellow banner / red error tokens).

## Limitations

- AskUserQuestion interactive form is best on the native `panel()` path; CCv2 shows compact cards.
- App-owned clarification uses native `request_input` / AskUserQuestion — not a CCv2 `provide_input` trigger.
- Plan-mode banner includes an **Execute plan** CTA (same idea as native `panel()`).
- Frontend packaging is static (Vite/`asset_dir` polish is Later on the roadmap).

## Related

- Checklist: [`test-checklist.md`](test-checklist.md)
- Preferred UX: [`../panel/panel.md`](../panel/panel.md)
- API: [`../../api.md`](../../api.md)
