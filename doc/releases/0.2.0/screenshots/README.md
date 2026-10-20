# Screenshots — 0.2.0

Store finals in this folder. Prefer PNG. Captured 2026-10-20 on the scripted agent (`STREAMLIT_COCO_AGENT=mock`).

**Demos:** `make modern-chat` (Rail / Window / Both) · `make simple-chat` (panel + Ask CoCo switch).

## Required shots

| File | Scene | Why |
| --- | --- | --- |
| `hero.png` | Modern chat on **Both**: Copilot column and the Ask CoCo window | LinkedIn + GitHub Release |
| `01-minimize.png` | After **Minimize**: the column is gone and the window is open | Shows Restore |
| `02-simple-chat.png` | Simple chat with Ask CoCo Off, then On | The default demo |

## Optional

| File | Scene |
| --- | --- |
| `demo.gif` or `demo.mp4` | 15–30s: Both → Minimize → Restore |

## Capture tips

- `STREAMLIT_COCO_AGENT=mock` needs no Snowflake login
- Crop personal connection names
- Light page, dark window header (the icons are white on that bar)

## After capture

- [x] Drop files here (`hero.png`, `01-minimize.png`, `02-simple-chat.png`; 2880 px wide, 2x)
- [x] Reference paths from `doc-dev/releases/0.2.0/linkedin.md` (the LinkedIn visual `visual-linkedin.svg` / `.png` is built from `hero.png`)
- [ ] Reference them in the GitHub Release body when it is created
- [ ] `demo.gif` / `demo.mp4`: not recorded

## What the pictures show, and what they do not

- Only the window runs on the scripted agent. In **Both** the Copilot column is the real 0.1.9 rail and is **not connected** ("Connect a Snowflake profile to start Copilot"): the classic session has no scripted agent. Replace `hero.png` with a live capture if the column should show a conversation.
- The request in `hero.png` ("Allow CoCo to run a command on this computer?") is the real policy and gate; the model and the program are scripted. Nothing was run.
- `02-simple-chat.png` puts **Off** (left) and **On** (right) side by side. The simple demo shows its start gate: no login, so no chat yet.
- No real connection name or home folder is in a picture: the capture runs with a throw-away `HOME` (`/tmp/coco_demo`).

## Regenerate

```bash
uv run --extra e2e python scripts/capture_release_screens.py            # all three, into this folder
uv run --extra e2e python scripts/capture_release_screens.py hero       # one of them
```

Look at each picture before it goes in. The script waits for the real state (the request card, the **Minimized** badge, the first-screen prompts).
