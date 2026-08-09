# Product Backlog Desk

Multipage Streamlit demo for [streamlit-coco](https://github.com/DevoteamSP/streamlit-coco): a small **product backlog** workspace (epics, tickets, releases) backed by local JSON/Markdown — **no SQL**.

CoCo reads the files with Read/Glob/Grep and can Edit/Write only after **Approve once / Deny**.

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

**Copilot** is a right-hand rail (not a nav page). Open via the header **Copilot** button or any “Ask Copilot / Check DoD / Draft notes” action; close with **Close** in the rail. Connect CoCo from the **Connection** popover next to **Close** (CLI auth only — no SQL). Board pages work without connecting.

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
