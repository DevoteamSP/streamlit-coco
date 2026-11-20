# Feature docs and test plans

Narrative docs follow DSP section 9 (What / Why / How / Limitations). Checklists are the manual, live sign-off, run before a release. Automated gates (unit tests and Playwright, on the scripted agent): [`../testing.md`](../testing.md).

Package API (every public name): [`../api.md`](../api.md).

## Index

| Feature | Narrative | Checklist | Run it |
| --- | --- | --- | --- |
| Ask CoCo (the window, rights, features, migration from 0.1.9) | [ask-coco/ask-coco.md](ask-coco/ask-coco.md) | [ask-coco/test-checklist.md](ask-coco/test-checklist.md) | `uv run --extra dev python -m streamlit run examples/chat_app.py`, `uv run --extra dev python -m streamlit run examples/approval_gate.py`, `uv run --extra dev python -m streamlit run examples/structured_output.py`, `uv run --extra dev python -m streamlit run examples/cwd_upload_chat.py` |
| A settings file of its own for the window's Cortex Code (0.3.1) | [settings-file/feature.md](settings-file/feature.md) | rows 34 to 36 of [ask-coco/test-checklist.md](ask-coco/test-checklist.md) | `CocoOptions(settings_file=...)` |
| App viewer | [app-viewer/app-viewer.md](app-viewer/app-viewer.md) | [app-viewer/test-checklist.md](app-viewer/test-checklist.md) | `uv run --directory examples/bi_to_semantic --project ../.. --extra dev --with 'streamlit-extras>=1.3.0' --with 'pbixray>=0.15.4' python -m streamlit run app.py`; `app_viewer()` |
| App Builder | [app-builder/app-builder.md](app-builder/app-builder.md) ([UX](app-builder/UX.md)) | [app-builder/test-checklist.md](app-builder/test-checklist.md) | `uv run --directory examples/app_builder --project ../.. --extra dev --with 'streamlit-extras>=1.3.0' python -m streamlit run app.py` |
| Headless query, multi-turn, a `Conversation` answered in code | [headless/headless.md](headless/headless.md) | [headless/test-checklist.md](headless/test-checklist.md) | `uv run --extra dev python examples/headless_pipeline.py` |
| Panel + chat input (0.1.9) | [panel/panel.md](panel/panel.md) | [panel/test-checklist.md](panel/test-checklist.md) | `uv run --extra dev python -m streamlit run examples/chat_app.py`; `tools_auto`, `streaming` |
| Copilot rail (0.1.9) | [copilot-rail/copilot-rail.md](copilot-rail/copilot-rail.md) | [copilot-rail/test-checklist.md](copilot-rail/test-checklist.md) | `uv run --directory examples/bi_to_semantic --project ../.. --extra dev --with 'streamlit-extras>=1.3.0' --with 'pbixray>=0.15.4' python -m streamlit run app.py`; `copilot_rail()` |
| Tool approvals (0.1.9) | [approvals/approvals.md](approvals/approvals.md) | [approvals/test-checklist.md](approvals/test-checklist.md) | category `approval` |
| Tools display + HITL (0.1.9) | [tools-display/tools-display.md](tools-display/tools-display.md) ([SPEC](tools-display/SPEC.md)) | [tools-display/test-checklist.md](tools-display/test-checklist.md) | categories `display_*` |
| Structured output (0.1.9) | [structured-output/structured-output.md](structured-output/structured-output.md) | [structured-output/test-checklist.md](structured-output/test-checklist.md) | `uv run --extra dev python -m streamlit run examples/structured_output.py`; `structured-json` |
| Pluggable text renderer (0.1.9) | [text-renderer/text-renderer.md](text-renderer/text-renderer.md) | [text-renderer/test-checklist.md](text-renderer/test-checklist.md) | `panel(..., text_renderer=…)` |
| File upload into `cwd` (0.1.9) | [file-upload/file-upload.md](file-upload/file-upload.md) | [file-upload/test-checklist.md](file-upload/test-checklist.md) | `uv run --extra dev python -m streamlit run examples/cwd_upload_chat.py` |
| Legacy CCv2 chat (0.1.9) | [chat-ccv2/chat-ccv2.md](chat-ccv2/chat-ccv2.md) | [chat-ccv2/test-checklist.md](chat-ccv2/test-checklist.md) | `uv run --extra dev python -m streamlit run examples/approval_gate.py` |

The chat family of 0.1.9 (`chat`, `panel`, `copilot_rail` and their helpers) stays the default in 0.2.0, and so do its feature files, listed below as they were written for 0.1.9. The window is opt-in; what each 0.1.9 name does in the window is the migration sheet in [`ask-coco/ask-coco.md`](ask-coco/ask-coco.md) section 2.

## Suggested run order (release)

1. **ask-coco** (the live checklist, on a real Cortex Code agent) 2. **app-viewer** 3. **app-builder** 4. **headless** 5. the chat family, as in 0.1.9: **panel**, **copilot-rail**, **approvals**, **tools-display**, **structured-output**, **text-renderer**, **file-upload**, **chat-ccv2**

Allow / Decline: the window's two buttons for a request. A request may also offer "Do not ask again for ...", a standing permission until the conversation ends. A question from CoCo: **Send answer**. A plan: **Approve plan**.

Exploratory prompts: [`examples/testdata/`](../../examples/testdata/).

## Last automated verification

| Suite | Result | Notes |
| --- | --- | --- |
| the fast gate (`uv run --extra dev ruff check .`, unit tests; [`../testing.md`](../testing.md)) | not recorded in this file | Run it before a merge. |
| `uv run --extra e2e python -m pytest tests/e2e tests/e2e_classic -m e2e` (Playwright, Edge, scripted agent) | not recorded in this file | Covers the walk of the window, the code block copy, "Latest exchange only", attached files and the page uploader. |
| Live run of the Ask CoCo checklist | **Not run for 0.2.0** | Needs the Cortex Code program and a Snowflake connection. |
| App viewer, App Builder, headless live checklists | Signed for earlier versions only | See the sign-off tables in each checklist. They predate 0.2.0. |
