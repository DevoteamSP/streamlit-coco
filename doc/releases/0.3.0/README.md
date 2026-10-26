# Release kit — 0.3.0

Feature cut: **Ask CoCo without the `cortex` program.** Snowflake's managed coding agent runs in the same window (`ManagedOptions`, `managed_agent`, `options_from_connection`), with the same policy, gate, Allow and Decline; the SDK is now `snowflake-cortex-agent-sdk` for both paths. Every decision can be written to an audit log (`AuditLog`, `ask_coco(audit=)`), and the files a user attaches in the managed window go to a stage the sandbox mounts. Example apps: a Skills shop on a stage and a Native App on SPCS that chats with one chosen skill (experimental).

Published `2026-10-26` (`v0.3.0` on lletourmy/streamlit-coco, PyPI `0.3.0`). The managed agent, the upload and the Native App are experimental: the SDK is a public preview (`0.0.x`).

| File | Purpose |
| --- | --- |
| [CHECKLIST.md](CHECKLIST.md) | Master pre-release gate |
| [NOTES.md](NOTES.md) | Themes / learnings |
| [screenshots/README.md](screenshots/README.md) | Capture brief |

Outreach (dev-only): [`../../../doc-dev/releases/0.3.0/`](../../../doc-dev/releases/0.3.0/).

Feature: [`../../features/ask-coco/ask-coco.md`](../../features/ask-coco/ask-coco.md) section 8.

Mechanics: [`../../deployment/publish.md`](../../deployment/publish.md) · QA: [`../../testing.md`](../../testing.md).
