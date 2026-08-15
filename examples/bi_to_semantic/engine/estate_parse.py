"""Deterministic estate-map extract from Tableau ``.twb`` and Power BI sources.

Produces the ``estate_map.schema.json`` payload without CoCo — Tableau XML as in
``examples/tableau_legacy/extract_schema.py``, plus TMDL / ``.pbix`` for Power BI.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Any

from engine.bi_sources import source_kind
from engine.powerbi_parse import estate_part as powerbi_estate_part

_REF = re.compile(r"^\[(.+?)\]\.\[(.+?)\]$")


def _txt(node: ET.Element, tag: str) -> str | None:
    el = node.find(tag)
    return el.text if el is not None else None


def _clean(name: str | None) -> str | None:
    """``[public].[users]`` or ``[users]`` → ``users``."""
    if not name:
        return None
    parts = re.findall(r"\[([^\]]+)\]", name)
    return (parts[-1] if parts else name).strip() or None


def _extract_one(path: Path) -> dict[str, Any]:
    root = ET.parse(path).getroot()
    tables: set[str] = set()
    cols: dict[str, dict[str, str]] = defaultdict(dict)
    fks: set[tuple[str, str, str, str]] = set()

    for rel in root.iter("relation"):
        if rel.get("type") == "table" and rel.get("table"):
            cleaned = _clean(rel.get("table"))
            if cleaned:
                tables.add(cleaned)

    for expr in root.iter("expression"):
        if expr.get("op") != "=":
            continue
        pair = [m.groups() for e in expr if (m := _REF.match(e.get("op") or ""))]
        if len(pair) == 2:
            (lt, lc), (rt, rc) = pair
            fks.add((lt, lc, rt, rc))

    for rec in root.iter("metadata-record"):
        if rec.get("class") != "column":
            continue
        parent = _clean(_txt(rec, "parent-name"))
        col = _clean(_txt(rec, "remote-name"))
        if not parent or not col:
            continue
        local = _txt(rec, "local-type") or "string"
        cols[parent][col] = local

    worksheets = sum(1 for _ in root.iter("worksheet"))
    dashboards = sum(1 for _ in root.iter("dashboard"))

    return {
        "workbook": path.name,
        "tables": sorted(tables),
        "columns": {t: dict(sorted(c.items())) for t, c in cols.items()},
        "foreign_keys": sorted(fks),
        "worksheets": worksheets,
        "dashboards": dashboards,
    }


def _part_for(path: Path) -> dict[str, Any] | None:
    kind = source_kind(path)
    if kind == "tableau" and path.is_file():
        return _extract_one(path)
    if kind == "powerbi":
        return powerbi_estate_part(path)
    return None


def build_estate_map(paths: list[Path]) -> dict[str, Any]:
    """Merge workbook extracts into an estate-map structured payload."""
    parts = [p for path in paths if (p := _part_for(path))]

    # table -> columns (first-seen type wins; later workbooks fill gaps)
    col_map: dict[str, dict[str, str]] = defaultdict(dict)
    # (lt,lc,rt,rc) -> workbooks that contain this join
    join_wbs: dict[tuple[str, str, str, str], set[str]] = defaultdict(set)
    usage: list[dict[str, Any]] = []
    all_tables: set[str] = set()
    table_sources: list[dict[str, Any]] = []

    for part in parts:
        wb = str(part["workbook"])
        tables = [str(t) for t in part["tables"]]
        all_tables.update(tables)
        sources = part.get("sources") or {}
        for t, cmap in (part.get("columns") or {}).items():
            for cname, ctype in cmap.items():
                col_map[str(t)].setdefault(str(cname), str(ctype))
            table_sources.append(
                {
                    "table": str(t),
                    "workbook": wb,
                    "source": str(sources.get(t) or ""),
                    "columns": sorted(str(c) for c in cmap),
                }
            )
        for t in tables:
            if t not in (part.get("columns") or {}) and t not in {
                row["table"] for row in table_sources if row["workbook"] == wb
            }:
                table_sources.append(
                    {
                        "table": t,
                        "workbook": wb,
                        "source": str(sources.get(t) or ""),
                        "columns": [],
                    }
                )
        for fk in part.get("foreign_keys") or []:
            key = (str(fk[0]), str(fk[1]), str(fk[2]), str(fk[3]))
            join_wbs[key].add(wb)
        usage.append(
            {
                "workbook": wb,
                "tables": tables,
                "worksheets": int(part.get("worksheets") or 0),
                "dashboards": int(part.get("dashboards") or 0),
            }
        )

    # Prefer tables that have column metadata; still include relation-only tables.
    table_names = sorted(all_tables | set(col_map))
    tables_out = [
        {
            "name": t,
            "columns": [{"name": c, "type": typ} for c, typ in sorted(col_map.get(t, {}).items())],
        }
        for t in table_names
    ]

    joins_out = [
        {
            "left_table": lt,
            "left_column": lc,
            "right_table": rt,
            "right_column": rc,
            "workbooks": sorted(wbs),
        }
        for (lt, lc, rt, rc), wbs in sorted(join_wbs.items())
        if lt in all_tables and rt in all_tables
    ]

    return {
        "tables": tables_out,
        "joins": joins_out,
        "workbook_usage": sorted(usage, key=lambda u: u["workbook"]),
        "table_sources": sorted(
            table_sources, key=lambda r: (str(r.get("table")), str(r.get("workbook")))
        ),
    }
