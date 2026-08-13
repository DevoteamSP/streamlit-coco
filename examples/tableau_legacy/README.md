# Legacy BI demo material — Tableau Server `workgroup` model on Snowflake

The relational model reconstructed from the **implicit** model found inside four
Tableau workbooks, plus synthetic data. Nothing here was copied from a schema
document: the tables, columns, types and joins were read out of the `.twb` XML.

## Layout

```
tableau_legacy/
├── workbooks/          the four .twb source workbooks (attribution below)
├── sql/                generated DDL, seed, and the integrity check
├── extract_schema.py   .twb → schema.json
├── gen_snowflake.py    schema.json → DDL + seed
└── schema.json         the extracted model
```

## Source workbooks — attribution

`workbooks/` is redistributed from
[tableau/community-tableau-server-insights](https://github.com/tableau/community-tableau-server-insights),
**© Tableau Software, MIT licence**, live-connected to the Tableau Server `workgroup`
PostgreSQL repository. Keep this attribution if these files move.

Refresh them with:

```bash
B=https://raw.githubusercontent.com/tableau/community-tableau-server-insights/master/datasources
cd workbooks
curl -sLO "$B/ts_content/ts_content_04.02.twb"
curl -sLO "$B/ts_users/ts_users_04.01.twb"
curl -sLO "$B/ts_events/ts_events_04.02.twb"
curl -sLO "$B/ts_web_requests/ts_web_requests_04.02.twb"
```

## Rebuild

```bash
python3 extract_schema.py workbooks/*.twb > schema.json
python3 gen_snowflake.py schema.json sql/workgroup_ddl.sql sql/workgroup_seed.sql
```

## Load

```bash
snow sql -c <connection> -f sql/workgroup_ddl.sql
snow sql -c <connection> -f sql/workgroup_seed.sql
snow sql -c <connection> -f sql/verify.sql     # 26 foreign keys, expect 0 orphans
```

Creates `TABLEAU_LEGACY.PUBLIC`. The seed inserts ~221 000 rows; on an XS warehouse
expect a couple of minutes, most of it in `historical_events`.

## What you get

| | |
|---|---|
| Tables | 28 |
| Columns | 509 |
| Primary keys | 28 |
| Foreign keys | 26 (inferred from join clauses) |
| Rows | 220 869 |
| Custom SQL blocks captured | 19 |

The shape is a fact table `historical_events` surrounded by `hist_*` dimensions,
plus the identity chain `users → sites / site_roles / system_users → domains`.

Five tables are referenced by more than one workbook — `users`, `sites`, `projects`,
`system_users`, `site_roles`. That overlap is what makes a domain decomposition
worth arguing about.

## Deliberate choices

- **Quoted lowercase identifiers.** The workbooks reference `[public].[users]`;
  Snowflake would otherwise uppercase everything and the names would stop matching.
- **Snowflake does not enforce PK/FK constraints** — they are informational. They are
  emitted anyway because they document the model for anything reading the schema.
  Integrity is guaranteed by construction instead: parents are inserted first and every
  foreign key draws from its parent's real id range.
- **`*_id` columns whose target table is outside these four workbooks** get a sparse,
  mostly-NULL value — never a dense sequence, which would read like a primary key and
  fabricate a relationship that does not exist.
- **Timestamps are cast explicitly** to `TIMESTAMP_NTZ`; `CURRENT_TIMESTAMP()` returns
  `TIMESTAMP_LTZ`.

## Verified

Loaded and checked on Snowflake (account `XMB91291`, warehouse `LAURENT_WH`):

| Check | Result |
|---|---|
| Tables created | 28 / 28 |
| Inserts | 28 / 28, row counts as specified |
| Referential integrity (`sql/verify.sql`) | **26 / 26 foreign keys, 0 orphans** |
| Primary key uniqueness | `historical_events` 200 000 / 200 000 · `users` 2 400 / 2 400 |
| Sparse fact foreign keys | 14.4 % populated on `hist_workbook_id`, 14.3 % on `hist_view_id` (target ≈ 1 in 7) |
| Out-of-scope `*_id` columns | 5.1 % populated — sparse, as intended |

## Known limitation

String values are functional but transparent: `historical_event_types_31`,
`hist_users_463`. Fine for validating the model, not fine in front of an audience — an
event type should read `Publish Workbook`, not like a disguised identifier.

Roughly thirty label columns out of 509 need realistic value lists instead of
concatenation. Start with `historical_event_types."name"`, which any demo will surface
first.

## Ground truth

[tableau/tableau-data-dictionary](https://github.com/tableau/tableau-data-dictionary)
documents the same `workgroup` database. Use it to score what an agent extracts against
what the tables actually mean. **No licence on that repository** — reference only, do
not redistribute.
