# Feature: App viewer

**Checklist:** `doc/features/app-viewer/test-checklist.md`  
**App:** `make bi-semantic` (adapter)  
**Library:** `st_coco.app_viewer` / `st_coco.default_fix_prompt` / `st_coco.last_preview_exception`

## Preconditions

- [ ] `uv sync --extra dev` from the **repo checkout**
- [ ] CoCo CLI + Snowflake connection for the Fix → job path
- [ ] Fresh browser session
- [ ] A generated consumer under `examples/bi_to_semantic/out/streamlit_dash/` (Build with python)

## Golden path

| # | Step | Expected |
| --- | --- | --- |
| 1 | Open Preview on a generated app (not running) | Title **Preview**; **Run** enabled; **Stop** disabled; **Fix with CoCo** enabled; no iframe |
| 2 | **Run** | Caption shows `http://127.0.0.1:8511` (Python) or `:8512` (CoCo); iframe loads the child |
| 3 | **Open** | New tab on the same URL |
| 4 | Break `streamlit_app.py` so the child raises | **Preview exception** expander shows the traceback; **Fix with CoCo** is primary |
| 5 | **Fix with CoCo** while connected | Job queued (“Fix Streamlit app”); Copilot rail sends the prompt; prompt includes the traceback and `streamlit_app.py` |
| 6 | **Fix with CoCo** while disconnected | Copilot opens; connect hint; no job until connected (BI adapter) |
| 7 | After CoCo Writes a fix | Child hot-reloads; expander clears once a later timestamped log line appears |
| 8 | **Stop** | Iframe gone; pid/port files cleared; **Run** enabled again |
| 9 | **Close** | Preview column hides; host `on_close` ran |

## Sign-off

| Field | Value |
| --- | --- |
| Tester | |
| Date | |
| Pass? | Pending `0.1.7` live CoCo sign-off |
