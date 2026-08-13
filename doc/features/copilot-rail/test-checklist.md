# Feature: Copilot rail

**Checklist:** `doc/features/copilot-rail/test-checklist.md`  
**App:** `make tableau-semantic` (adapter) or any `panel()` app + `transcript_view_pills()`  
**Library:** `st_coco.copilot_rail` / `st_coco.transcript_view_pills`

## Preconditions

- [ ] `uv sync --extra dev` from the **repo checkout** (or `pip install "streamlit-coco[sdk]==0.1.6"`)
- [ ] CoCo CLI + Snowflake connection for live jobs
- [ ] Fresh browser session

## Golden path

| # | Step | Expected |
| --- | --- | --- |
| 1 | Open an app that mounts `copilot_rail` disconnected | Connection popover; no session |
| 2 | Connect | Environment status; Copilot ready caption |
| 3 | Leave both transcript pills on (default) | Pills sit beside Connection (no **Transcript** label, no “Showing …” caption). Only recent turns; user/assistant text capped at 200 chars |
| 4 | Turn **Last messages** off | Full transcript length (still truncated to 200 chars if the other pill is on). Host page (left) does not rerun |
| 5 | Turn **First 200 characters** off | Full message bodies |
| 6 | Long cwd in the status caption | Path over 100 characters shows `...` in the middle; status token stays intact |
| 7 | Queue a job from the app | Caption shows job label · queued/sent; prompt appears as a user turn. **Working · thinking…** is a badge beside the transcript pills (not a large bordered box) |
| 8 | Confirm **no copy/paste control** on assistant messages (`show_copy=False`) | No clipboard button in the rail |
| 9 | Clear chat | Transcript empty; session still connected |

## Sign-off

| Field | Value |
| --- | --- |
| Tester | |
| Date | |
| Pass? | Pending `0.1.6` live CoCo sign-off |
