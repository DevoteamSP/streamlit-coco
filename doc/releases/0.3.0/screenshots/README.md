# Screenshots — 0.3.0

Store finals in this folder. Prefer PNG. Captured 2026-10-26 on the scripted stream of Snowflake's client (`examples/e2e_managed_harness.py`, no login) and on the Skills shop's sample skills, Streamlit 1.66.1, light theme, 2x. The account name in the pictures is `fake`.

Regenerate all of them: `.venv/bin/python scripts/capture_release_screens.py managed shop` (needs the `e2e` extra).

## Required shots

| File | Scene | Why |
| --- | --- | --- |
| `hero.png` | The window on the managed agent: a command waiting for Allow, **Where: The Snowflake sandbox** | The headline: the sandbox, and the user's Allow |

## More shots

| File | Scene | Why |
| --- | --- | --- |
| `01-first-screen.png` | The first screen: "It works in a Snowflake sandbox, not on this computer" | The managed agent says what it is |
| `02-attach.png` | A CSV attached; the agent is told `/uploads/<id>/orders_q3.csv`, never a local path | Files go to the sandbox |
| `03-audit.png` | The audit file after an Allow: the decision (who, tool, where, the exact command) and its `outcome` line | The audit log |
| `04-shop-library.png` | The Skills shop on its three sample skills | The example apps |

Not captured: the Native App page behind its ingress (needs a Snowflake login), the chat with a skill (the demo chat is the scripted agent, whose first screen speaks of "project files", which would mislead on a managed-agent release).

Also in the kit, dev-only: [`doc-dev/releases/0.3.0/intro-video.html`](../../../../doc-dev/releases/0.3.0/intro-video.html), a 20-second animated introduction (open it in a browser; space pauses, `r` replays, click the bar to seek).

## Optional

| File | Scene |
| --- | --- |
| `demo.gif` | 15–30s: attach a CSV, ask, Allow, answer (the intro video is the motion piece) |

## Capture tips

- Same window width across a carousel (~1280px).
- Never show a real account name: the harness uses `fake`.
