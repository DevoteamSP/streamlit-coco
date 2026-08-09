# Feature: Text renderer

**Checklist:** `doc/features/text-renderer/test-checklist.md`  
**App:** `make chat`  
**API:** `panel(..., text_renderer=...)`, `render_transcript`, `render_output_field`

## Preconditions

- [ ] Package installed; chat demo runs

## Golden path

| # | Step | Expected |
| --- | --- | --- |
| 1 | Default `panel()` (no `text_renderer`) | Assistant/user messages render as markdown |
| 2 | Temporarily call `panel(..., text_renderer="text")` | Messages render as plain text (no markdown emphasis) |
| 3 | `text_renderer=st.write` | Messages still appear; no exception |
| 4 | Invalid name e.g. `text_renderer="nope"` | Clear `ValueError` listing known names |

## Sign-off

| Field | Value |
| --- | --- |
| Tester | |
| Date | |
| Pass? | |
