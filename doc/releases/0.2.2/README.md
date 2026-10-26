# Release kit — 0.2.2

Feature cut: **Ask CoCo leaves the corner.** The window attaches to the left or the right edge on the full height of the page, or fills the page. The page is told where the window is (`ask_coco(on_layout=)`, `get_window(key).place`) and can take the rest of the screen (`ask_coco(split=True)`). Fix: the window no longer blinks while it waits.

Prepared `2026-10-25`. **Not published.**

| File | Purpose |
| --- | --- |
| [CHECKLIST.md](CHECKLIST.md) | Master pre-release gate |
| [NOTES.md](NOTES.md) | Themes / learnings |
| [screenshots/README.md](screenshots/README.md) | Capture brief |

Outreach (dev-only): [`../../../doc-dev/releases/0.2.2/`](../../../doc-dev/releases/0.2.2/).

Feature: [`../../features/ask-coco/ask-coco.md`](../../features/ask-coco/ask-coco.md).

Mechanics: [`../../deployment/publish.md`](../../deployment/publish.md) · QA: [`../../testing.md`](../../testing.md).
