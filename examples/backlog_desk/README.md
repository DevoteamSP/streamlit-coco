# Product Backlog Desk

Multipage Streamlit demo for [streamlit-coco](https://github.com/DevoteamSP/streamlit-coco): a small **product backlog** workspace (epics, tickets, releases) backed by local JSON/Markdown — **no SQL**.

CoCo reads the files with Read/Glob/Grep and can Edit/Write only after **Allow / Decline**.

## Run

From the **streamlit-coco** repo root:

```bash
make install
make backlog
```

Or:

```bash
cd examples/backlog_desk
uv run --project ../.. streamlit run streamlit_app.py
```

Theme lives in [`.streamlit/config.toml`](.streamlit/config.toml) (Devoteam + Snowflake accents). Run with this folder as the working directory so Streamlit picks it up (`make backlog` does that).

## Pages

| Page | Purpose |
| --- | --- |
| **Board** | KPIs + filterable tickets |
| **Epic** | Epic detail + child tickets |
| **Ticket** | Ticket detail + open Copilot skills |
| **Release** | Release notes Markdown |

**Ask CoCo** is the package's floating window: a launcher at the bottom right opens it on any page. Connect (config file, profile) from the window itself; Board pages work without connecting. The Ticket, Epic and Release buttons send a skill to CoCo (`coco.ask`), and **Run a skill** in the page header is the application's own picker (skill, ticket, epic, release, prompt preview): the thread shows the skill's name as your message, **Show full request** shows the whole prompt.

Rights (`streamlit_coco.policy.FolderPolicy`): reading under `data/` is free; every Edit or Write asks (Allow / Decline) each time, and anything outside `data/` asks as unusual.

## Skills

| Skill | What it does |
| --- | --- |
| Summarize sprint | Standup summary from `data/tickets/` |
| Draft release notes | Write/update `data/releases/*.md` (**approval**) |
| Propose ticket update | Edit a ticket JSON (**approval**) |
| Check definition of done | Compare ticket vs `data/policies/dod.md` |

## Data

```
data/
  epics/*.json
  tickets/*.json
  releases/*.md
  policies/dod.md
```

Edits from CoCo are real file writes under `data/` — use git to discard demo changes.
