# Feature: File upload into `cwd`

**Checklist:** `doc/features/file-upload/test-checklist.md`  
**App:** `examples/cwd_upload_chat.py` (`make cwd-upload`)  
**API:** `upload_to_cwd` / `cwd_uploader` / `chat_input_bar(accept_file=…)` — see [`file-upload.md`](file-upload.md)  
**Status:** Implemented for CLI / local `cwd` (sign off before `0.1.5`)

## Preconditions

- [ ] Feature documented in [`../../api.md`](../../api.md)
- [ ] Demo available: `make cwd-upload`
- [ ] CLI mode: writable `CocoOptions.cwd`
- [ ] Unit tests: `uv run pytest tests/test_upload.py`

## Golden path

| # | Step | Expected | Pass |
| --- | --- | --- | --- |
| 1 | Open demo; upload one allowed file (e.g. `.csv`) via sidebar or chat attach | File appears under `_uploads/`; path shown in UI | |
| 2 | Ask the agent to Read / summarize that path | Tool card uses the uploaded file | |
| 3 | Upload a second file with the same name (sidebar `overwrite="replace"`) | File replaced; chat bar also replaces by default | |
| 4 | Upload a disallowed extension / oversize file (via `upload_to_cwd` / strict caller) | Clear error; nothing unexpected under `cwd` | |
| 5 | List workspace files in sidebar inventory | Uploaded names visible under `_uploads/` | |

## Edge cases

- [ ] Empty file
- [ ] Multi-file batch (partial failure)
- [ ] Path traversal in uploaded filename (`../`)
- [ ] Session reset / new `cwd` does not leave orphaned secrets outside quarantine

## Sign-off

| Date | Tester | Result | Notes |
| --- | --- | --- | --- |
| — | — | Not run | Pending manual UI pass |
