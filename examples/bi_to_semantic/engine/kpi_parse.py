"""Deterministic KPI inventory from Tableau calculated fields and Power BI measures.

Produces the ``kpi_inventory.schema.json`` payload without CoCo.
Cross-source grouping by caption matches the MIT Tableau finding and the
authored Power BI ops pack (``Visibility Score``).
"""

from __future__ import annotations

import html
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Any

from engine.bi_sources import source_kind
from engine.powerbi_parse import kpi_rows as powerbi_kpi_rows


def _display_name(col: ET.Element) -> str:
    caption = (col.get("caption") or "").strip()
    if caption:
        return caption
    name = (col.get("name") or "").strip()
    return name.strip("[]")


def _plain_english(
    name: str,
    *,
    datatype: str,
    role: str,
    is_conflicting: bool,
    workbooks: list[str],
) -> str:
    kind = "measure" if (role or "").lower() == "measure" else f"calculated {role or 'field'}"
    base = f"BI {kind} `{name}`"
    if datatype:
        base += f" ({datatype})"
    if is_conflicting:
        return f"{base}. Formula differs across {', '.join(workbooks)} — needs arbitration."
    if len(workbooks) > 1:
        return f"{base}. Same formula in {', '.join(workbooks)}."
    return f"{base}."


def _extract_one(path: Path) -> list[dict[str, Any]]:
    kind = source_kind(path)
    if kind == "powerbi":
        return powerbi_kpi_rows(path)
    if kind != "tableau" or not path.is_file():
        return []
    root = ET.parse(path).getroot()
    rows: list[dict[str, Any]] = []
    for col in root.iter("column"):
        calc = col.find("calculation")
        if calc is None:
            continue
        formula = html.unescape(calc.get("formula") or "").strip()
        name = _display_name(col)
        if not name or not formula:
            continue
        rows.append(
            {
                "name": name,
                "workbook": path.name,
                "formula": formula,
                "aggregation": (col.get("aggregation") or "unknown").lower(),
                "datatype": col.get("datatype") or "",
                "role": col.get("role") or "",
            }
        )
    return rows


def build_kpi_inventory(paths: list[Path]) -> dict[str, Any]:
    """Merge calculated fields across workbooks into a KPI inventory payload."""
    # name -> workbook -> list of (formula, aggregation, datatype, role)
    grouped: dict[str, dict[str, list[dict[str, str]]]] = defaultdict(lambda: defaultdict(list))

    for path in paths:
        for row in _extract_one(path):
            grouped[row["name"]][row["workbook"]].append(
                {
                    "formula": row["formula"],
                    "aggregation": row["aggregation"],
                    "datatype": row["datatype"],
                    "role": row["role"],
                }
            )

    metrics: list[dict[str, Any]] = []
    for name, by_wb in grouped.items():
        definitions: list[dict[str, str]] = []
        formulas: set[str] = set()
        datatype = ""
        role = ""
        for workbook, variants in sorted(by_wb.items()):
            # Deduplicate identical formulas within one workbook
            seen: set[str] = set()
            for v in variants:
                formula = v["formula"]
                if formula in seen:
                    continue
                seen.add(formula)
                formulas.add(formula)
                datatype = datatype or v["datatype"]
                role = role or v["role"]
                definitions.append(
                    {
                        "workbook": workbook,
                        "formula": formula,
                        "aggregation": v["aggregation"] or "unknown",
                    }
                )

        workbooks = sorted(by_wb.keys())
        is_conflicting = len(formulas) > 1
        metrics.append(
            {
                "name": name,
                "workbooks": workbooks,
                "definitions": definitions,
                "is_conflicting": is_conflicting,
                "plain_english": _plain_english(
                    name,
                    datatype=datatype,
                    role=role,
                    is_conflicting=is_conflicting,
                    workbooks=workbooks,
                ),
            }
        )

    # Conflicts / multi-workbook first (stable secondary sort by name)
    metrics.sort(
        key=lambda m: (
            not bool(m["is_conflicting"]),
            len(m["workbooks"]) < 2,
            str(m["name"]).lower(),
        )
    )
    return {"metrics": metrics}
