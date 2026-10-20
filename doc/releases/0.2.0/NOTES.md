# Release notes bank — 0.2.0

Freeform. Feed LinkedIn / Medium / GitHub Release when this cut is published.

## Headline (one line)

> Ask CoCo floats over the page. The chat, panel, and Copilot rail stay until you ask for the window.

## Top 3 user-visible wins

1. **`ask_coco(cwd)`** — launcher and window, with a policy. Reading the working folder is free; everything else asks.
2. **Minimize / Restore** — hide the chat or Copilot rail and open the window, then bring that column back.
3. **`make modern-chat`** — Rail, Window, or Both, on the scripted agent with `STREAMLIT_COCO_AGENT=mock`.

## Use cases to feature

1. A page that already has a Copilot rail and wants the same agent in a window
2. A host that mounts only `ask_coco(cwd)` and never shows the 0.1.9 panel

## Learnings (candid)

- The window and the rail are two clients. A shared Snowflake profile does not mean a shared transcript.
- Header icons use the window surface colour. A light header fill makes them white on white; the header fill stays dark.
- The chat family was not removed. Docs that said it was have been corrected for this cut.

## Quotes / soundbites

- “The column stays. The window is one switch away.”
- “Both means the rail and Ask CoCo, with Minimize and Restore between them.”

## Test plan

- `make test-all` — green on 2026-10-20: ruff, 637 passed, 1 skipped, 742 subtests; 8 browser tests; `pip-audit` clean.
- 0.1.9 compatibility: `tests/test_compat_019.py` (API snapshot) and the 0.1.9 tests, kept.
- Not run: the manual live checklists (`features/ask-coco/test-checklist.md`) and the live smoke (`make modern-chat`, `make simple-chat` against Cortex Code).

## Explicit non-goals this cut

- Public sync (`make sync-release`) and the PyPI tag
- API mode (`mode="api"`, no CLI)
- Removing `chat`, `panel`, or `copilot_rail`
