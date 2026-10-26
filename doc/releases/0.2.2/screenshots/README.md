# Screenshots — 0.2.2

Store finals in this folder. Prefer PNG. Captured 2026-10-25 on the scripted agent (`STREAMLIT_COCO_AGENT=mock`), Streamlit 1.66.1, 2x.

**Demo:** `make modern-chat` (Ask CoCo first; the Split screen selector is in the sidebar).

## Required shots

| File | Scene | Why |
| --- | --- | --- |
| `hero.png` | Ask CoCo attached to the right, **Split** on: the page beside it, a permission request waiting | LinkedIn + GitHub Release |
| `01-full-page.png` | The window on the **Full page** | The second place |
| `02-hint.png` | The title bar with the hint under the pressed icon (750 ms) | The icons |

## Optional

| File | Scene |
| --- | --- |
| `demo.gif` or `demo.mp4` | 15–30s: float → attach right (the page makes room) → full page → back |

## Capture tips

- `STREAMLIT_COCO_AGENT=mock` needs no Snowflake login
- No real connection name or home folder in a picture: the capture runs with a throw-away `HOME` (`/tmp/coco_demo`)

## After capture

- [x] Drop files here (`hero.png`, `01-full-page.png`, `02-hint.png`)
- [x] Reference paths from `doc-dev/releases/0.2.2/linkedin.md`
- [ ] Reference them in the GitHub Release body when it is created
- [ ] `demo.gif` / `demo.mp4`: not recorded

## What the pictures show, and what they do not

- The agent is scripted. The request ("Allow CoCo to list files in the .git folder?") is the real policy and gate; the model and the program are scripted. Nothing was run.
- The sidebar of `hero.png` is the demo's own (Surfaces, Split screen, the place the window reported through `on_layout`).

## Regenerate

```bash
uv run --extra e2e python scripts/capture_release_screens.py          # split full hint, into this folder
uv run --extra e2e python scripts/capture_release_screens.py split    # one of: split full hint
```

Look at each picture before it goes in. The script waits for the real state (the request card, the reported place, the visible hint).
