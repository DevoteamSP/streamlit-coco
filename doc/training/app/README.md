# Training navigator (mini-app)

Streamlit app that browses this asset's training pack and documentation.
Copied here by `$asset-owner-training` from
`.cortex/skills/asset-owner-training/app/`. Do not edit to depend on
dsp-assets. Re-copy from the skill when the navigator changes.

## Run

From the **asset repo root**:

```bash
make training              # any asset, dsp-assets included
PORT=8600 make training    # start looking for a free port at 8600
```

From this directory, with Streamlit 1.57+ (the asset's venv if it already has it):

```bash
cd doc/training/app
uv run --with streamlit --with pyyaml streamlit run streamlit_app.py
```

Or, if the asset already uses uv + Streamlit:

```bash
cd doc/training/app && uv run streamlit run streamlit_app.py
```

The app reads `doc/training/training.yml` (the parent of `app/`) and the
files it declares. The title bar shows the **product name** (never the
generic word "asset"), **Ask CoCo**, country flags (🇬🇧 🇫🇷 🇪🇸), and pack
KPIs. `main(directory)` points the same viewer at another pack — the Navigator
Docs page uses that to open any local asset's `doc/training/`.

**Ask CoCo** opens from the floating launcher and talks to the pack: cwd is
`doc/training/`. Reads inside the pack are allowed; other actions ask for approval.
Connect a Snowflake CLI profile in the window. The pack still browses without CoCo.

## Layout

| View | What you see |
|------|----------------|
| Home | Title bar, suggested path (Enablement → Training → Certify), reference guides. Cards share a height; each lists what it includes, then Open |
| Track | Home + heading aligned with two-column document cards |
| Guide | User Guide and Technical Guide list their pages by chapter family, in reading order: Start · Tasks · Reference · Answers, and Understand · Run · Build on it · Answers. Other stems appear under **More** |
| Page navigation | **Previous** / **Next** under the document follow the track's reading order — the same order the standalone pages use. The page keeps its own table of contents inside the frame |
| Document | Companion **HTML** in a full-width frame (the page scrolls inside it). In-pack links stay in the app; `help.html#<anchor>` opens the page at that heading. Quizzes are interactive here |

Never navigate the browser to a Streamlit route such as
`/sections/getting-started.html` — that is not how the pack is served.
Cross-links inside the iframe open the matching document in the same view.

## Requirements

- `streamlit`
- `pyyaml`
- `streamlit-coco[sdk]` (optional — Ask CoCo window)

No secrets. No network calls except the optional CoCo session.
