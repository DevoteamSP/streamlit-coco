# Release kit — 0.3.1

Patch cut: **a settings file of its own for the window's Cortex Code** (`CocoOptions.settings_file`, passed to the program as `cortex --config`), so the user's own plugins, hooks and environment do not reach an application's sessions. Also: the full-page conversation uses the whole width; Markdown said before a call shows as a message; a batch of file changes is judged change by change (the tick *Do not ask again* covers it); the `result` event carries the usage the CLI reports; no Makefile (everything runs through `uv`); the training pack is removed. No new screenshots: nothing new to show on a first screen.

Tag date: 2026-11-20 (planned; see the checklist for what actually happened).

| File | Purpose |
| --- | --- |
| [CHECKLIST.md](CHECKLIST.md) | Master pre-release gate |
| [NOTES.md](NOTES.md) | Themes / learnings |

Outreach (dev-only): [`../../../doc-dev/releases/0.3.1/`](../../../doc-dev/releases/0.3.1/).

Feature: [`../../features/settings-file/feature.md`](../../features/settings-file/feature.md) · [`../../features/ask-coco/ask-coco.md`](../../features/ask-coco/ask-coco.md).

Mechanics: [`../../deployment/publish.md`](../../deployment/publish.md) · QA: [`../../testing.md`](../../testing.md).
