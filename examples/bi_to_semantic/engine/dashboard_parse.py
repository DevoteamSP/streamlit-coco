"""List Tableau dashboards and Power BI report pages (deterministic)."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from engine.bi_sources import source_kind
from engine.powerbi_parse import dashboard_rows as powerbi_dashboard_rows

_SKIP_ZONE = {
    "layout-basic",
    "layout-flow",
    "layout-fixed",
    "title",
    "text",
    "image",
    "paramctrl",
    "empty",
    "color",
    "filter",
    "legend",
}


def _dash_name(node: ET.Element) -> str:
    return (node.get("caption") or node.get("name") or "Dashboard").strip()


def _worksheet_names(root: ET.Element) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for ws in root.iter("worksheet"):
        name = (ws.get("name") or "").strip()
        if name and name not in seen:
            seen.add(name)
            names.append(name)
    return names


def _tableau_field(param: str, fallback: str = "") -> str:
    text = (param or "").rsplit(".", 1)[-1].strip("[]")
    parts = text.split(":")
    if len(parts) >= 2 and parts[0] in {"none", "usr", "qr"}:
        return parts[1].replace("_", " ").strip()
    name = text.replace("_", " ").strip()
    if "Display Tabs" in name or "Workbook Display" in name:
        return ""
    return name or fallback.strip()


def _dashboard_filters(dashboard: ET.Element) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    seen: set[str] = set()
    for zone in dashboard.iter("zone"):
        kind = zone.get("type-v2") or ""
        if kind == "filter":
            field = _tableau_field(zone.get("param") or "", zone.get("name") or "")
            role = "filter"
        elif kind == "paramctrl":
            field = _tableau_field(zone.get("param") or "")
            role = "parameter"
        else:
            continue
        if not field or field in seen:
            continue
        seen.add(field)
        found.append({"name": field, "field": field, "kind": role})
    return found


def _dashboard_worksheets(dashboard: ET.Element, known: set[str]) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for zone in dashboard.iter("zone"):
        kind = zone.get("type-v2") or ""
        if kind in _SKIP_ZONE:
            continue
        name = (zone.get("name") or "").strip()
        if name and name in known and name not in seen:
            seen.add(name)
            found.append(name)
    return found


def list_dashboards(paths: list[Path]) -> list[dict[str, Any]]:
    """Return ``{id, workbook, name, worksheets}`` for each dashboard / page."""
    out: list[dict[str, Any]] = []
    for path in paths:
        kind = source_kind(path)
        if kind == "powerbi":
            out.extend(powerbi_dashboard_rows(path))
            continue
        if kind != "tableau" or not path.is_file():
            continue
        root = ET.parse(path).getroot()
        known = set(_worksheet_names(root))
        for dash in root.iter("dashboard"):
            name = _dash_name(dash)
            worksheets = _dashboard_worksheets(dash, known) or list(known)
            dash_id = f"{path.stem}::{name}"
            out.append(
                {
                    "id": dash_id,
                    "workbook": path.name,
                    "name": name,
                    "source": "tableau",
                    "filters": _dashboard_filters(dash),
                    "worksheets": worksheets,
                }
            )
    return out
