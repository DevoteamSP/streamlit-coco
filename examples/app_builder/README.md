# App Builder

Example for [streamlit-coco](https://github.com/DevoteamSP/streamlit-coco): a **library of app types**. Pick a type, fill its **brief** (context, what it allows, what it does not, questions), optionally attach **sketches** of the app you want, then CoCo writes a Streamlit app under approval. Preview and **Fix with CoCo** reuse `app_viewer()`; CoCo is the package's floating **Ask CoCo** window.

Product brief: [`doc/features/app-builder/UX.md`](../../doc/features/app-builder/UX.md).

This is **not** a BI migration (see [BI → Semantic](../bi_to_semantic/)) and not napkin-only generation.

## Run

From the repo root:

```bash
make install
make app-builder
```

Or:

```bash
cd examples/app_builder
uv run --project ../.. --extra dev --with 'streamlit-extras>=1.3.0' python -m streamlit run app.py
```

## Screens

| Screen | What |
| --- | --- |
| Welcome | You never start from a blank `app.py`; three steps |
| Library | **Resume** project cards; **Create a new project** type cards (icon, name, users, grounding, screenshot) |
| Brief | Columns: your brief + sketches · type questions |
| Studio | **Build this app** / regenerate; header **Open Preview**; the preview column has an **App brief** expander (owner brief + questions; **Save** / **Save & regenerate**) |
| Admin | Type cards on the left (Edit / Delete / Create); paired Topics / Context and Allows / Does not; question cards; **Guidelines skills** editors for `types/shared/SKILL.md` and the type `SKILL.md` |

**Build with CoCo** needs the CLI. **Build demo scaffold** writes a disconnected `streamlit_app.py` from the fixture CSV (no warehouse, no agent).

## Types

Filter saved apps and types with **topic pills** at the top of Library (multi-select). **Local** = no Snowflake.

| Type | Topics | Snowflake? | Grounding |
| --- | --- | --- | --- |
| KPI presentation | Snowflake, Analytics | Yes (demo CSV optional) | Semantic view or fixture |
| Data quality | Snowflake, Quality | Yes (demo CSV optional) | Tables or fixture |
| CSV explorer | Local, Analytics | No | Demo CSV |
| Call transcription | Local, Knowledge | No | Demo transcript |
| Meeting recap | Local, Productivity | No | Demo notes |
| Prompt library | Local, Knowledge | No | Demo markdown pack |

Add a type: **Admin** tab, or a new folder `types/<id>/` with `type.json` plus optional `SKILL.md`.

## Types and skills

Each app type is one folder under `types/`. The shared generation skill sits next to them but is not a catalog card.

| Path | What it is | Who reads it |
| --- | --- | --- |
| `types/<id>/type.json` | Catalog card — name, topics, questions, grounding, allows / does-not | Host app (Library, Brief, Admin) |
| `types/<id>/SKILL.md` | Type-specific layout + data rules; optional `reference/` + `CHECKLIST.md` | CoCo (`add_dirs`) |
| `types/shared/SKILL.md` | Generation rules for **every** app | CoCo (`add_dirs`) |

`types/shared/` has no `type.json`, so it never appears in Library / Admin. Edit both skill files on **Admin** (they are what Build tells CoCo to Read).

## Artifacts

Agent / generated files:

- Working folder of the Ask CoCo window: `examples/app_builder/out/<slug>/` (`brief.json`, `BRIEF.md`, `sketches/`, `streamlit_app.py`)
- Preview: `app_viewer()` on that folder (port **8513**)

## How it uses Ask CoCo

- `engine/coco_window.py` mounts `ask_coco(cwd)` on every run, with the current app folder as `cwd` (the workspace folder before an app is picked; switching app starts a new conversation). Connect (config file, profile) from the window.
- **Rights**: a `FolderPolicy` on the app folder. Read / Glob / Grep there are free, and so are the guidelines skills under `types/` that the build prompt names; every Write or Edit asks (Allow / Decline) each time.
- **Jobs**: **Build this app**, **Regenerate** and **Fix with CoCo** call `coco.ask(label, prompt, key="build" | "fix")`. Pressed before connecting, they wait in the window ("Sent when you connect"). When one finishes, `coco.result(key)` tells the page, which starts the preview on its own.
- **First screen**: three example questions (`prompts=`); the placeholder text is a `labels=` override; the window's menu offers "Latest exchange only" and "Shorten long messages" (`Features(display=...)`); Copy is off.
- The preview (`app_viewer`) and the sketches uploader stay page components.
- `APP_BUILDER_HOME=<folder>` moves the two folders the app writes to (a scratch run).
