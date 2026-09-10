# Feature: Copilot rail

**Checklist:** `doc/features/copilot-rail/test-checklist.md`  
**App:** `make bi-semantic` (adapter) or any `panel()` app + `transcript_display_config()`  
**Library:** `st_coco.copilot_rail` / `st_coco.transcript_display_config`

## Preconditions

- [ ] `uv sync --extra dev` from the **repo checkout** (or `pip install "streamlit-coco[sdk]==0.1.6"`)
- [ ] CoCo CLI + Snowflake connection for live jobs
- [ ] Fresh browser session

## Golden path

| # | Step | Expected |
| --- | --- | --- |
| 1 | Open an app that mounts `copilot_rail` disconnected | Connection popover; no session |
| 1a | Open Connection | **Config file** and **Connection** selectboxes sit on one row. One `~/.snowflake/*.toml` → one config option; several → pick among them. Profiles and the environment probe follow the selected file |
| 2 | Connect | Environment status; Copilot ready caption. If the app passed `example_questions`, starter buttons appear under the empty transcript (title on the button) |
| 2a | Hover a starter button | Tooltip shows the **question** text (not just the title) |
| 2b | Click a starter | The question is sent as a user turn; starters hide; CoCo runs |
| 2b-deferred | Click a starter with `deferred=True` (rail or item) | The question text appears in the chat input and is **not** sent. Starters stay visible. Submit from the input to run |
| 2c | Clear chat | Transcript empty; starter buttons return |
| 3 | Open the icon-only **Display config** popover (Material `display_settings`, no label) | Pills **Last messages** / **First n characters** plus two sliders. Hover on the icon shows **Display config**. No **Transcript** heading on the rail |
| 4 | Leave both pills on (default) | Only recent turns (default 8); user/assistant text capped at 200 chars |
| 5 | Drag **Last messages** / **First n characters** sliders | Transcript updates live; popover stays open; host page (left) does not rerun |
| 6 | Turn **Last messages** off | Full transcript length (still truncated if the other pill is on). Last-messages slider is disabled |
| 7 | Turn **First n characters** off | Full message bodies. Character slider is disabled |
| 8 | Long cwd in the status caption | Path over 100 characters shows `...` in the middle; status token stays intact |
| 9 | Queue a job from the app | Caption shows job label · queued/sent; prompt appears as a user turn. **Working · thinking…** is a badge beside Display config (not a large bordered box) |
| 10 | Confirm **no copy/paste control** on assistant messages (`show_copy=False`) | No clipboard button in the rail |
| 11 | Clear chat | Transcript empty; session still connected |

## Sign-off

| Field | Value |
| --- | --- |
| Tester | |
| Date | |
| Pass? | Pending `0.1.6` live CoCo sign-off |
