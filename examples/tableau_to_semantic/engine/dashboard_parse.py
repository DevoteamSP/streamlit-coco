"""List Tableau dashboards + worksheets from ``.twb`` XML (deterministic)."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

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
    """Return ``{id, workbook, name, worksheets}`` for each dashboard in the pile."""
    out: list[dict[str, Any]] = []
    for path in paths:
        if not path.is_file():
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
                    "worksheets": worksheets,
                }
            )
    return out
