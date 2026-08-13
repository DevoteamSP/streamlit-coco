# Feature: File upload into `cwd`

**Feature:** Browser upload → CoCo agent workspace  
**Status:** Implemented (CLI / local `cwd`) — target **`0.1.5`**  
**Surfaces:** `upload_to_cwd`, `cwd_uploader`, `chat_input_bar(..., accept_file=…)`  
**Related:** PRD NG7 / §14.3 · [`api.md`](../../api.md) (`CocoOptions.cwd`) · API-mode sandbox mapping (follow-up once remote API ships)

---

## What

Let users drop files from the Streamlit UI into the CoCo working directory so Read / Grep / Edit / Write can use them without a separate SCP or stage step.

## Why

- Operators often have CSVs, SQL scripts, or configs on their laptop that the agent should analyze.
- Today they must place files on the Streamlit host (or in Snowflake) before the session starts.
- A small upload helper closes that gap while keeping CoCo server-side (no browser-side agent).

## How

```python
paths = st_coco.upload_to_cwd(
    session,                 # or cwd=opts.cwd / Path
    uploaded_files,          # from st.file_uploader / chat attachments
    subdir="_uploads",       # quarantine under cwd
    overwrite="error",       # or "replace" / "skip"
)

# Chat bar with attachments (Streamlit builds that support accept_file):
st_coco.chat_input_bar(session, accept_file="multiple")

# Or sidebar / chrome:
st_coco.cwd_uploader(session, overwrite="replace")
```

| Area | Intent |
| --- | --- |
| **UX** | Chat attachments via `chat_input_bar(accept_file=…)` and/or `cwd_uploader` beside app chrome |
| **Write path (CLI)** | Persist under `CocoOptions.cwd/_uploads/` (configurable `subdir`); never overwrite unless `overwrite="replace"` |
| **Write path (API)** | Later: map uploads into the Agent API sandbox workspace (`/workspace` / V-stage), not the Streamlit host disk |
| **Guards** | Size + extension allowlist; basename sanitization (no path traversal); quarantine path outside secrets dirs |
| **API surface** | `upload_to_cwd` returns `UploadedPath` rows; chat bar can inject paths into the next prompt |
| **Rollout** | Example `examples/cwd_upload_chat.py` (`make cwd-upload`); documented in [`api.md`](../../api.md) |

## Limitations / out of scope (this slice)

- Full file-tree IDE or multi-tab workspace (NG3)
- Drag-drop into CCv2 transcript chrome
- Fetching arbitrary remote URLs into `cwd`
- Replacing Snowflake stage / V-stage workflows for large datasets
- API-mode sandbox upload (defer until remote API is on `main`)

## Related

- Checklist: [`test-checklist.md`](test-checklist.md)
- Roadmap: [`../../roadmap.md`](../../roadmap.md) (shipped in `0.1.5`)
- Demo: `make cwd-upload`
