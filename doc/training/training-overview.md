# Training Overview — streamlit-coco

## What this asset is

`streamlit-coco` is a Python library (PyPI: `streamlit-coco`, alpha `0.1.6`) that embeds
Snowflake's **Cortex Code Agent SDK ("CoCo")** into Streamlit apps: a streaming agent
transcript with readable tool cards (SQL, Read, Write, Grep…), a reusable **`copilot_rail()`**
for multipage apps, human-in-the-loop approval gates for destructive tools, structured
output into your own widgets, and a headless `query()` API for scripts/CI. It removes the
"weeks of subprocess/NDJSON/streaming plumbing" that hand-rolling a CoCo integration into
Streamlit would otherwise cost.

Owner: Laurent Letourmy (Devoteam Snowflake Partner). Level: N0 (alpha), targeting N1.
Dev repo: [`DevoteamSP/streamlit-coco-dev`](https://github.com/DevoteamSP/streamlit-coco-dev) ·
public/PyPI source: [`lletourmy/streamlit-coco`](https://github.com/lletourmy/streamlit-coco).

## Learning objectives

After this training you will be able to:

1. Explain what `streamlit-coco` does and when to reach for it vs. a bare CoCo CLI/Snowsight session.
2. Install it, connect it to a Snowflake account, and run every bundled demo (`make chat`, `make backlog`, `make tableau-semantic`, `make headless`, …).
3. Build a minimal Streamlit app from scratch using `panel()` + `chat_input_bar()`, with approval gates configured — and recognize when to wrap that in `copilot_rail()`.
4. Deliver the 12-minute scripted demo (`doc/marketing/demo.md`) to a client or internal audience unassisted.
5. Know where to look when something breaks (`doc/deployment/local.md` §7 Troubleshooting) and where the roadmap/feature docs live.

## Time estimate

| Module | Time |
| --- | --- |
| Setup guide | 20–30 min |
| Hands-on lab (5 core + optional Tableau) | 90–120 min |
| Demo script read-through + one dry run | 30–40 min |
| Quiz | 15 min |
| **Total** | **~2.5–3.5 hours** |

## Prerequisites

- Python 3.10+ and `uv` installed locally.
- A Snowflake account with **Cortex Code** access, and a working `~/.snowflake/connections.toml` (or CLI default connection).
- The **CoCo CLI** (`cortex`) installed and on `PATH` — check with `cortex --version`.
- Git access to `DevoteamSP/streamlit-coco-dev` (ask the asset owner for repo access if you don't have it).
- Comfort with basic Streamlit (`st.chat_input`, `st.container`) is helpful but not required — the library hides most of the plumbing.

## How this pack fits together

- **`setup-guide.md`** — get the repo running locally, verify you're ready.
- **`hands-on-lab.md`** — 5 core exercises + optional Tableau / `copilot_rail` using the real `examples/` apps.
- **`demo-script.md`** — the client-facing 10–12 min demo (references `doc/marketing/demo.md`, the source of truth — kept in sync here).
- **`quiz.md`** — 10 questions, pass at 8/10 to be considered "trained" for the N0→N1 gate item.
- **`enablement-deck.html`** — slide deck for the same story (HTML is source of truth; regenerate the PDF if you need a printout).

This satisfies the Snow Builders N0→N1 gate criterion **"1 additional consultant trained"**
once a second consultant completes the lab and scores 8/10+ on the quiz.
