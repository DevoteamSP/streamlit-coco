# Data quality

Use when the type id is `data-quality`.

## Layout contract

1. Title + which tables/files were checked
2. Metric row: rows, null cells, duplicate rows (and any requested checks)
3. Chart for the primary check (nulls-by-column is the default)
4. One detail table of sample rows

## Data

- Demo pack / `data.csv`: local pandas profile.
- Named tables: document the FQDN in captions; disconnected mode still uses `data.csv` if present.
- Do not INSERT/UPDATE/DELETE. Read-only.
