"""Extract the implicit relational model from Tableau .twb workbooks.

Reads <relation> (tables, joins, custom SQL) and <metadata-record class='column'>
and emits a consolidated schema + inferred foreign keys as JSON.
"""

import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict

# Tableau local-type -> Snowflake type
TYPE_MAP = {
    "integer": "NUMBER(38,0)",
    "real": "FLOAT",
    "string": "VARCHAR(16777216)",
    "boolean": "BOOLEAN",
    "date": "DATE",
    "datetime": "TIMESTAMP_NTZ",
}


def txt(node, tag):
    el = node.find(tag)
    return el.text if el is not None else None


def clean(name):
    """'[public].[users]' or '[users]' -> 'users'"""
    if not name:
        return None
    parts = re.findall(r"\[([^\]]+)\]", name)
    return (parts[-1] if parts else name).strip()


def extract(path):
    root = ET.parse(path).getroot()
    tables, custom_sql, cols, fks = set(), {}, defaultdict(dict), set()

    for rel in root.iter("relation"):
        kind, name = rel.get("type"), rel.get("name")
        if kind == "table" and rel.get("table"):
            tables.add(clean(rel.get("table")))
        elif kind == "text" and rel.text:
            custom_sql[clean(name)] = " ".join(rel.text.split())

    # join clauses: op="[a].[x]" = op="[b].[y]"  ->  foreign key edge
    ref = re.compile(r"^\[(.+?)\]\.\[(.+?)\]$")
    for expr in root.iter("expression"):
        if expr.get("op") != "=":
            continue
        pair = [m.groups() for e in expr if (m := ref.match(e.get("op") or ""))]
        if len(pair) == 2:
            (lt, lc), (rt, rc) = pair
            fks.add((lt, lc, rt, rc))

    for rec in root.iter("metadata-record"):
        if rec.get("class") != "column":
            continue
        parent = clean(txt(rec, "parent-name"))
        col = clean(txt(rec, "remote-name"))
        if not parent or not col:
            continue
        cols[parent][col] = {
            "type": TYPE_MAP.get(txt(rec, "local-type"), "VARCHAR(16777216)"),
            "tableau_type": txt(rec, "local-type"),
        }

    return {
        "workbook": path,
        "tables": sorted(tables),
        "custom_sql": custom_sql,
        "columns": {k: v for k, v in cols.items()},
        "foreign_keys": sorted(fks),
    }


def merge(parts):
    tables, cols, fks, sql = set(), defaultdict(dict), set(), {}
    for p in parts:
        tables |= set(p["tables"])
        sql.update(p["custom_sql"])
        for t, c in p["columns"].items():
            cols[t].update(c)
        fks |= {tuple(f) for f in p["foreign_keys"]}

    # a custom-SQL block is not a base table; keep only real tables
    real = {t: dict(sorted(cols[t].items())) for t in sorted(tables) if t in cols}
    orphan = sorted(set(tables) - set(real))
    fks = sorted(f for f in fks if f[0] in real and f[2] in real)
    return {
        "tables": real,
        "tables_without_column_metadata": orphan,
        "custom_sql_blocks": sql,
        "foreign_keys": fks,
    }


if __name__ == "__main__":
    parts = [extract(p) for p in sys.argv[1:]]
    out = merge(parts)
    print(json.dumps(out, indent=2))
