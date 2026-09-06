# KPI presentation

Use when the type id is `semantic-kpis`.

**Read `reference/streamlit_app.py` in this folder before writing.** Imitate its
layout, empty states, formatting, and widget choices. Then verify the output
against `CHECKLIST.md`.

## Layout contract

1. `st.set_page_config` before any other `st.*` call
2. Title + short caption (audience / grain from the brief answers)
3. KPI row (`st.metric` with a delta) for the requested metrics
4. One trend chart at the requested grain
5. One detail table — not a wall of dataframes

## Chart choice (by data shape)

- Time trend → **line** (`st.line_chart` or Altair line)
- ≤7 categories, comparison → **bar**
- Never pie
- A single number → `st.metric` with a delta (this period vs previous), not a one-point chart

## Filters

Filters from the brief are **visible widgets** (`st.multiselect`, `st.pills`,
`st.selectbox`) — never a hidden `WHERE` the user cannot see or undo. Wrap the
filter block (and the dashboard it drives) in `@st.fragment` so a filter change
does not refetch.

## Data loading

- Demo pack / `data.csv`: pandas read, no Snowflake. `@st.cache_data` with a TTL
  on the load (`ttl="5m"`).
- Named semantic view: query only that view (comment the SQL). Do not query base tables.
- Disconnected demo: if `data.csv` is missing, show an error and `st.stop()` — do
  not invent a warehouse.

## Empty and error states (required)

Handle all three without a traceback:

- **Zero rows** (file empty, or filters exclude everything) — `st.info`, no chart crash
- **Missing column** the brief asked for — `st.error` naming the column, then stop
- **Disconnected / no file** — `st.error` that `data.csv` is missing

## Number formatting

- Currency: `$1,280,000` (no raw `1280000.0`)
- Counts: thousands separators (`410`)
- Ratios already in 0–1: percent (`24.0%`)
- Deltas on metrics: signed percent vs the previous period at the same grain

## Other craft

- Honor **What this does not do** and `must_not` from the brief (shared skill
  already covers Streamlit APIs, labels, and captions).
