# App Builder — shared generation

Use when generating **any** Streamlit app from a filled App Builder brief.
Type-specific skills (`csv-explorer`, `semantic-kpis`, …) extend this file;
they do not replace it. Always Read this skill first, then the type skill.

This folder is **not** a catalog type. Catalog cards are `types/<id>/type.json`
(Admin / Library). This directory has no `type.json`, so it never appears as a
Library card. Type-specific rules live in `types/<id>/SKILL.md`.

## Brief and scope

- Read `BRIEF.md` and `sketches/` before writing code.
- Honor **What the owner wants** (the free-text brief) for this instance.
- Honor **What this does not do**. Never invent tables, views, files, or APIs.
- Write `streamlit_app.py` in the current working directory only.
- Do not write outside this folder. Do not edit the host App Builder.
- Never `CREATE SEMANTIC VIEW` or migrate Tableau / Power BI.
- Never fetch the network. Use only files already in cwd (or a named view the
  brief already answered).
- If a required answer is missing, AskUser. Do not guess grounding.

## Streamlit craft (every type)

- Streamlit ≥ 1.57. `st.set_page_config` before any other `st.*` call.
- `width="stretch"` or `width="content"`. Never `use_container_width`.
- Sentence case on titles and widget labels.
- Material Symbols (`:material/icon_name:`) over emojis. Every icon-only
  control has a real label (`label_visibility` if the text is hidden).
- Prefer `st.container(horizontal=True)` for rows; `st.columns` only for a
  fixed grid.
- Cache expensive loads (`@st.cache_data` with a TTL). Filters that only
  subset already-loaded data go in `@st.fragment` so they do not refetch.
- Caption sits under the title, not under the last table.

## Empty and error states (required)

Handle these without a traceback:

- **No / empty source** — `st.error` naming what is missing, then `st.stop()`
- **Zero rows** after filters — `st.info`, no chart crash
- **Missing column or field** the brief asked for — `st.error` naming it, then stop

## Disconnected demo

- If the brief uses a demo pack, read the copied fixture in cwd (`data.csv`,
  `transcript.txt`, `notes.md`, `prompts.md`, …). Do not require a warehouse.
- If that file is missing, error and stop. Do not invent a warehouse or sample.

## Approvals and self-check

- You Write/Edit files; the human approves. Do not try to skip gates.
- After Write: if the type skill folder has `CHECKLIST.md`, verify against it
  and Edit once if needed. If there is no checklist, skip — do not mention it.
- If `.preview.log` shows a traceback, one corrective Edit, then stop.
