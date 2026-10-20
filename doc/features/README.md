# Feature docs and test plans

Narrative docs follow DSP section 9 (What / Why / How / Limitations). Checklists are the manual, live sign-off, run before a release. Automated gates (unit tests and Playwright, on the scripted agent): [`../testing.md`](../testing.md).

Package API (every public name): [`../api.md`](../api.md).

## Index

| Feature | Narrative | Checklist | Run it |
| --- | --- | --- | --- |
| Ask CoCo (the window, rights, features, migration from 0.1.9) | [ask-coco/ask-coco.md](ask-coco/ask-coco.md) | [ask-coco/test-checklist.md](ask-coco/test-checklist.md) | `make chat`, `make approval`, `make structured`, `make cwd-upload` |
| App viewer | [app-viewer/app-viewer.md](app-viewer/app-viewer.md) | [app-viewer/test-checklist.md](app-viewer/test-checklist.md) | `make bi-semantic`; `app_viewer()` |
| App Builder | [app-builder/app-builder.md](app-builder/app-builder.md) ([UX](app-builder/UX.md)) | [app-builder/test-checklist.md](app-builder/test-checklist.md) | `make app-builder` |
| Headless query, multi-turn, a `Conversation` answered in code | [headless/headless.md](headless/headless.md) | [headless/test-checklist.md](headless/test-checklist.md) | `make headless` |
| Panel + chat input (0.1.9) | [panel/panel.md](panel/panel.md) | [panel/test-checklist.md](panel/test-checklist.md) | `make chat`; `tools_auto`, `streaming` |
| Copilot rail (0.1.9) | [copilot-rail/copilot-rail.md](copilot-rail/copilot-rail.md) | [copilot-rail/test-checklist.md](copilot-rail/test-checklist.md) | `make bi-semantic`; `copilot_rail()` |
| Tool approvals (0.1.9) | [approvals/approvals.md](approvals/approvals.md) | [approvals/test-checklist.md](approvals/test-checklist.md) | category `approval` |
| Tools display + HITL (0.1.9) | [tools-display/tools-display.md](tools-display/tools-display.md) ([SPEC](tools-display/SPEC.md)) | [tools-display/test-checklist.md](tools-display/test-checklist.md) | categories `display_*` |
| Structured output (0.1.9) | [structured-output/structured-output.md](structured-output/structured-output.md) | [structured-output/test-checklist.md](structured-output/test-checklist.md) | `make structured`; `structured-json` |
| Pluggable text renderer (0.1.9) | [text-renderer/text-renderer.md](text-renderer/text-renderer.md) | [text-renderer/test-checklist.md](text-renderer/test-checklist.md) | `panel(..., text_renderer=…)` |
| File upload into `cwd` (0.1.9) | [file-upload/file-upload.md](file-upload/file-upload.md) | [file-upload/test-checklist.md](file-upload/test-checklist.md) | `make cwd-upload` |
| Legacy CCv2 chat (0.1.9) | [chat-ccv2/chat-ccv2.md](chat-ccv2/chat-ccv2.md) | [chat-ccv2/test-checklist.md](chat-ccv2/test-checklist.md) | `make approval` |

The chat family of 0.1.9 (`chat`, `panel`, `copilot_rail` and their helpers) stays the default in 0.2.0, and so do its feature files, listed below as they were written for 0.1.9. The window is opt-in; what each 0.1.9 name does in the window is the migration sheet in [`ask-coco/ask-coco.md`](ask-coco/ask-coco.md) section 2.

## Suggested run order (release)

1. **ask-coco** (the live checklist, on a real Cortex Code agent) 2. **app-viewer** 3. **app-builder** 4. **headless** 5. the chat family, as in 0.1.9: **panel**, **copilot-rail**, **approvals**, **tools-display**, **structured-output**, **text-renderer**, **file-upload**, **chat-ccv2**

Allow / Decline: the window's two buttons for a request. A request may also offer "Do not ask again for ...", a standing permission until the conversation ends. A question from CoCo: **Send answer**. A plan: **Approve plan**.

Exploratory prompts: [`examples/testdata/`](../../examples/testdata/).

## Last automated verification

| Suite | Result | Notes |
| --- | --- | --- |
| `make check` (ruff, unit tests) | not recorded in this file | Run it before a merge. |
| `make e2e` (Playwright, Edge, scripted agent) | not recorded in this file | Covers the walk of the window, the code block copy, "Latest exchange only", attached files and the page uploader. |
| Live run of the Ask CoCo checklist | **Not run for 0.2.0** | Needs the Cortex Code program and a Snowflake connection. |
| App viewer, App Builder, headless live checklists | Signed for earlier versions only | See the sign-off tables in each checklist. They predate 0.2.0. |
