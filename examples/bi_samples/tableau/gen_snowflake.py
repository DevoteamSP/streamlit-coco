"""Generate Snowflake DDL + synthetic seed SQL from the schema extracted by extract_schema.py.

Identifiers are emitted as quoted lowercase so they match exactly what the Tableau
workbooks reference ([public].[users]) — Snowflake would otherwise uppercase them.
"""

import json
import sys
from collections import defaultdict

# rows generated per table; anything unlisted falls back to DEFAULT_ROWS
ROWS = {
    "domains": 3,
    "site_roles": 6,
    "sites": 5,
    "historical_event_types": 40,
    "hist_sites": 5,
    "hist_collections": 30,
    "hist_projects": 120,
    "projects": 120,
    "projects_contents": 900,
    "system_users": 2000,
    "_users": 2000,
    "users": 2400,
    "hist_users": 2400,
    "workbooks": 800,
    "hist_workbooks": 800,
    "views": 4000,
    "hist_views": 4000,
    "datasources": 300,
    "hist_datasources": 300,
    "flows": 40,
    "hist_flows": 40,
    "metrics": 60,
    "hist_metrics": 60,
    "tasks": 200,
    "hist_tasks": 200,
    "hist_schedules": 25,
    "asset_lists": 15,
    "historical_events": 200_000,
}
DEFAULT_ROWS = 100

# FK columns on the event fact table that should mostly be NULL:
# one event points at one object type, not all of them.
SPARSE_FK_TABLES = {"historical_events"}


def q(name):
    return '"' + name.replace('"', '""') + '"'


def order_tables(tables, fks):
    """Topological order so parents are inserted before children."""
    deps = defaultdict(set)
    for child, _, parent, _ in fks:
        if child != parent:
            deps[child].add(parent)
    done, out = set(), []
    remaining = set(tables)
    while remaining:
        ready = sorted(t for t in remaining if not (deps[t] - done))
        if not ready:  # cycle: break it deterministically
            ready = [sorted(remaining)[0]]
        for t in ready:
            out.append(t)
            done.add(t)
            remaining.discard(t)
    return out


def value_expr(table, col, typ, fk_target, rows_of, pk):
    """A Snowflake expression producing one synthetic value."""
    low = col.lower()

    # only the primary key is a dense sequence
    if col == pk:
        return "SEQ4() + 1"

    if fk_target:
        parent, _ = fk_target
        n = rows_of.get(parent, DEFAULT_ROWS)
        pick = f"UNIFORM(1, {n}, RANDOM())"
        if table in SPARSE_FK_TABLES:
            # ~1 event in 7 actually references this object type
            return f"IFF(UNIFORM(1, 7, RANDOM()) = 1, {pick}, NULL)"
        return pick

    if low.endswith("_id") and typ.startswith("NUMBER"):
        # An *_id column whose target table is outside the 4 workbooks we read.
        # Emit a sparse, mostly-NULL reference — never a dense sequence, which
        # would read like a primary key and fabricate a relationship.
        return "IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL)"

    if typ.startswith("NUMBER"):
        if any(k in low for k in ("count", "hits", "total", "num", "size", "bytes")):
            return "UNIFORM(0, 50000, RANDOM())"
        if "limit" in low:
            return "UNIFORM(0, 1000, RANDOM())"
        return "UNIFORM(0, 100, RANDOM())"

    if typ == "FLOAT":
        return "ROUND(UNIFORM(0::FLOAT, 1000::FLOAT, RANDOM()), 3)"

    if typ == "BOOLEAN":
        return "UNIFORM(0, 1, RANDOM()) = 1"

    if typ in ("DATE", "TIMESTAMP_NTZ"):
        # CURRENT_TIMESTAMP() is TIMESTAMP_LTZ — cast explicitly, do not rely on
        # an implicit conversion into the TIMESTAMP_NTZ column.
        base = (
            "DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), "
            "CURRENT_TIMESTAMP())::TIMESTAMP_NTZ"
        )
        return base if typ == "TIMESTAMP_NTZ" else f"TO_DATE({base})"

    # strings — shape them by column name so the model reads like real content
    seq = "(SEQ4() + 1)::VARCHAR"
    if low in ("name", "title", "caption", "friendly_name"):
        return f"'{table}_' || {seq}"
    if "email" in low:
        return f"'user' || {seq} || '@example.com'"
    if "url" in low or "path" in low or "uri" in low:
        return f"'/{table}/' || {seq}"
    if "description" in low or "comment" in low:
        return f"'Synthetic {table} record ' || {seq}"
    if "type" in low or "status" in low or "state" in low or "action" in low:
        return (
            "ARRAY_CONSTRUCT('create','update','delete','publish','refresh','access')"
            "[UNIFORM(0, 5, RANDOM())]::VARCHAR"
        )
    if "version" in low:
        return "ARRAY_CONSTRUCT('01.02','02.02','03.01','04.02')[UNIFORM(0, 3, RANDOM())]::VARCHAR"
    if low.endswith("_luid") or low == "luid":
        return "UUID_STRING()"
    return f"'{table}.{col}.' || {seq}"


def main(schema_path, ddl_path, seed_path):
    s = json.load(open(schema_path))
    tables, fks = s["tables"], [tuple(f) for f in s["foreign_keys"]]

    fk_of = {(c, col): (p, pcol) for c, col, p, pcol in fks}
    pk_of = {}
    rows_of = {t: ROWS.get(t, DEFAULT_ROWS) for t in tables}
    ordered = order_tables(tables, fks)

    ddl = [
        "-- Tableau Server `workgroup` model, reconstructed from the implicit model",
        "-- found in tableau/community-tableau-server-insights workbooks (MIT).",
        "-- Generated by gen_snowflake.py — do not edit by hand.",
        "",
        "CREATE DATABASE IF NOT EXISTS TABLEAU_LEGACY;",
        "CREATE SCHEMA IF NOT EXISTS TABLEAU_LEGACY.PUBLIC;",
        "USE SCHEMA TABLEAU_LEGACY.PUBLIC;",
        "",
    ]
    for t in ordered:
        cols = tables[t]
        lines = [f"  {q(c):40} {m['type']}" for c, m in cols.items()]
        pk = "id" if "id" in cols else ("type_id" if "type_id" in cols else None)
        pk_of[t] = pk
        if pk:
            lines.append(f"  CONSTRAINT {q('pk_' + t)} PRIMARY KEY ({q(pk)})")
        for (child, col), (parent, pcol) in fk_of.items():
            if child == t and col in cols and parent in tables:
                lines.append(
                    f"  CONSTRAINT {q(f'fk_{t}_{col}')} FOREIGN KEY ({q(col)}) "
                    f"REFERENCES {q(parent)} ({q(pcol)})"
                )
        ddl.append(f"CREATE OR REPLACE TABLE {q(t)} (\n" + ",\n".join(lines) + "\n);\n")

    seed = [
        "-- Synthetic data for the reconstructed workgroup model.",
        "-- Referential integrity is preserved: parents are loaded before children,",
        "-- and every foreign key draws from its parent's actual id range.",
        "",
        "USE SCHEMA TABLEAU_LEGACY.PUBLIC;",
        "",
    ]
    for t in ordered:
        cols = tables[t]
        n = rows_of[t]
        exprs = [
            f"  {value_expr(t, c, m['type'], fk_of.get((t, c)), rows_of, pk_of.get(t))} AS {q(c)}"
            for c, m in cols.items()
        ]
        seed.append(
            f"INSERT INTO {q(t)} ({', '.join(q(c) for c in cols)})\n"
            "SELECT\n" + ",\n".join(exprs) + "\n"
            f"FROM TABLE(GENERATOR(ROWCOUNT => {n}));\n"
        )

    open(ddl_path, "w").write("\n".join(ddl))
    open(seed_path, "w").write("\n".join(seed))

    total = sum(rows_of[t] for t in ordered)
    print(f"tables      : {len(ordered)}")
    print(f"colonnes    : {sum(len(c) for c in tables.values())}")
    pk_n = len([t for t in ordered if "id" in tables[t] or "type_id" in tables[t]])
    print(f"contraintes : {pk_n} PK, {len(fks)} FK")
    print(f"lignes      : {total:,}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
