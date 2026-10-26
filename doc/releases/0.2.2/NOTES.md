# Release notes bank — 0.2.2

Freeform. Feed LinkedIn / Medium / GitHub Release when this cut is published.

## Headline (one line)

> Ask CoCo can dock to the side of your app, and your page makes room for it.

## Top 3 user-visible wins

1. **Three icons in the title bar** — attach the window to the left or the right edge (full height), or fill the page. The pressed icon puts it back. A click on the title bar minimises. Each icon shows a hint after 750 ms.
2. **The page knows** — `ask_coco(on_layout=fn)` and `get_window(key).place` say where the window is; `split=True` gives the page the rest of the screen.
3. **No more blink** — while the window waited for an answer, Streamlit faded the stale component every poll, and the page's own layers drew over the window.

## Use cases to feature

1. A copilot beside a working app: the page keeps its screen, the agent keeps its column (`make modern-chat`, Split)
2. App Builder and BI → Semantic with Ask CoCo only: Build, Fix and the BI jobs go to one conversation, and each screen suggests its own questions

## Learnings (candid)

- A fixed element inside a component is only as stable as its ancestors: one `opacity: 0.8` on the container made it a stacking context, and the page's dataframes and headers drew over a window with `z-index: 8`.
- Streamlit's header, menu bar and sidebar sit at 999990–999995. A full-height window has to be above them, and below dialogs and popovers.
- The page does not need a new API to share the screen: Streamlit's app container is absolutely positioned, so moving its `left` or `right` by the dock width is enough, and nothing fixed in the page breaks.
- The three-icon title bar needed its own hint: the browser's `title` takes about a second and cannot be styled.

## Quotes / soundbites

- “The window docks. The page makes room.”
- “One agent surface, on every screen. Each screen suggests its own questions.”

## Test plan

- `make test-all` — green on 2026-10-25: ruff, 637 passed, 1 skipped, 742 subtests; 15 browser tests; `pip-audit` clean (Streamlit 1.66.1 locked).
- Browser tests: `tests/e2e/test_window_layout.py` (places, switches, callback and split, hint, title bar over the header).
- Not run: the manual live checklists (`features/ask-coco/test-checklist.md`) and the live smoke against Cortex Code.

## Explicit non-goals this cut

- Public sync (`make sync-release`), the tag and PyPI
- API mode (`0.3.0`)
- A resizable dock (the width is `min(30rem, 100vw)`)
