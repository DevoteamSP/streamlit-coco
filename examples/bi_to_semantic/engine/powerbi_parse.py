"""Deterministic extract from Power BI ``.pbix`` / ``.pbit`` (pbixray) and PBIP/TMDL."""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path
from typing import Any

_COL_REF = re.compile(r"\[([^\]]+)\]")
_SQL_DB = re.compile(r"Sql\.Database\([^)]+\)")
_FILE_CONTENTS = re.compile(r'File\.Contents\("([^"]+)"\)')
_HIDDEN_DATE_PREFIXES = ("LocalDateTable_", "DateTableTemplate_")


def _unquote(name: str) -> str:
    text = name.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
        return text[1:-1]
    return text


def parse_tmdl(text: str) -> dict[str, Any]:
    """Best-effort TMDL subset: tables, columns, measures, relationships, roles."""
    tables: dict[str, dict[str, Any]] = {}
    relationships: list[dict[str, str]] = []
    roles: list[dict[str, Any]] = []

    current_table: str | None = None
    current_column: str | None = None
    current_rel: dict[str, str] | None = None
    current_role: dict[str, Any] | None = None

    for raw in text.splitlines():
        stripped = raw.split("//", 1)[0].rstrip()
        if not stripped.strip():
            continue
        line = stripped.strip()

        if line.startswith("table ") and not line.startswith("tablePermission"):
            current_table = _unquote(line[len("table ") :].split("=")[0])
            current_column = None
            current_rel = None
            current_role = None
            tables.setdefault(current_table, {"columns": {}, "measures": []})
            continue
        if line.startswith("column ") and current_table:
            current_column = _unquote(line[len("column ") :].split("=")[0])
            tables[current_table]["columns"].setdefault(current_column, "string")
            continue
        if line.startswith("dataType:") and current_table and current_column:
            tables[current_table]["columns"][current_column] = line.split(":", 1)[1].strip()
            continue
        if line.startswith("measure ") and current_table:
            rest = line[len("measure ") :]
            name_part, _, expr = rest.partition("=")
            tables[current_table]["measures"].append(
                {
                    "name": _unquote(name_part.strip()),
                    "formula": expr.strip(),
                    "aggregation": "unknown",
                }
            )
            current_column = None
            continue
        if line.startswith("relationship "):
            current_rel = {"name": _unquote(line[len("relationship ") :])}
            current_table = None
            current_column = None
            current_role = None
            continue
        if line.startswith("fromColumn:") and current_rel is not None:
            current_rel["fromColumn"] = line.split(":", 1)[1].strip()
            continue
        if line.startswith("toColumn:") and current_rel is not None:
            current_rel["toColumn"] = line.split(":", 1)[1].strip()
            if "fromColumn" in current_rel:
                relationships.append(dict(current_rel))
            continue
        if line.startswith("role "):
            current_role = {
                "name": _unquote(line[len("role ") :]),
                "permissions": [],
            }
            roles.append(current_role)
            current_table = None
            current_column = None
            current_rel = None
            continue
        if line.startswith("tablePermission ") and current_role is not None:
            rest = line[len("tablePermission ") :]
            table_name, _, expr = rest.partition("=")
            current_role["permissions"].append(
                {
                    "table": _unquote(table_name.strip()),
                    "expression": expr.strip(),
                }
            )
            continue

    return {
        "tables": tables,
        "relationships": relationships,
        "roles": roles,
    }


def is_hidden_date_table(name: str) -> bool:
    return name.startswith(_HIDDEN_DATE_PREFIXES)


def compact_m(expr: str, *, limit: int = 180) -> str:
    """Short label for a Power Query M expression (SQL / Excel / inline)."""
    if not expr:
        return ""
    match = _SQL_DB.search(expr)
    if match:
        return match.group(0)
    match = _FILE_CONTENTS.search(expr)
    if match:
        return f"Excel {match.group(1)}"
    if "Table.FromRows" in expr:
        return "inline table"
    one = " ".join(expr.split())
    return one[:limit] + ("…" if len(one) > limit else "")


def _from_pbixray(path: Path) -> dict[str, Any]:
    """Primary model extract: tables, DAX, relationships, M, RLS via pbixray."""
    from pbixray import PBIXRay

    ray = PBIXRay(str(path))
    tables: dict[str, dict[str, Any]] = {}

    def _ensure(name: str) -> dict[str, Any] | None:
        if is_hidden_date_table(name):
            return None
        return tables.setdefault(name, {"columns": {}, "measures": [], "source": ""})

    schema = getattr(ray, "schema", None)
    if schema is not None and len(schema):
        for row in schema.itertuples(index=False):
            table = _ensure(str(row.TableName))
            if table is None:
                continue
            table["columns"][str(row.ColumnName)] = str(
                getattr(row, "PandasDataType", None) or "string"
            )

    measures = getattr(ray, "dax_measures", None)
    if measures is not None and len(measures):
        for row in measures.itertuples(index=False):
            table = _ensure(str(row.TableName))
            if table is None:
                continue
            formula = str(getattr(row, "Expression", "") or "").strip()
            name = str(getattr(row, "Name", "") or "").strip()
            if name and formula:
                table["measures"].append(
                    {"name": name, "formula": formula, "aggregation": "unknown"}
                )

    power_query = getattr(ray, "power_query", None)
    if power_query is not None and len(power_query):
        for row in power_query.itertuples(index=False):
            table = _ensure(str(row.TableName))
            if table is None:
                continue
            table["source"] = str(getattr(row, "Expression", "") or "").strip()

    relationships: list[dict[str, str]] = []
    rels = getattr(ray, "relationships", None)
    if rels is not None and len(rels):
        for row in rels.itertuples(index=False):
            ft = str(row.FromTableName)
            tt = str(row.ToTableName)
            if is_hidden_date_table(ft) or is_hidden_date_table(tt):
                continue
            relationships.append(
                {
                    "fromColumn": f"{ft}.{row.FromColumnName}",
                    "toColumn": f"{tt}.{row.ToColumnName}",
                }
            )

    roles: list[dict[str, Any]] = []
    rls = getattr(ray, "rls", None)
    if rls is not None and len(rls):
        grouped: dict[str, list[dict[str, str]]] = {}
        for row in rls.itertuples(index=False):
            data = row._asdict() if hasattr(row, "_asdict") else {}
            role_name = str(
                data.get("Role") or data.get("Name") or data.get("role") or "role"
            )
            table_name = str(data.get("Table") or data.get("TableName") or "")
            expr = str(
                data.get("Filter")
                or data.get("Expression")
                or data.get("filterExpression")
                or ""
            )
            grouped.setdefault(role_name, []).append(
                {"table": table_name, "expression": expr.strip()}
            )
        roles = [{"name": name, "permissions": perms} for name, perms in grouped.items()]

    return {"tables": tables, "relationships": relationships, "roles": roles}


def _split_col_ref(ref: str) -> tuple[str, str]:
    if "." in ref:
        table, _, col = ref.partition(".")
        return table.strip(), col.strip()
    return "", ref.strip()


_SKIP_VISUALS = frozenset(
    {
        "textbox",
        "image",
        "slicer",
        "shape",
        "basicshape",
        "actionbutton",
        "bookmarknavigator",
        "pagenavigator",
        "textboxvisual",
    }
)
_KPI_VISUALS = frozenset(
    {"card", "kpi", "multirowcard", "gauge", "cardvisual", "multicard"}
)
_LINE_VISUALS = frozenset(
    {
        "linechart",
        "areachart",
        "stackedareachart",
        "lineclusteredcolumncombochart",
        "linestackedcolumncombochart",
    }
)
_TABLE_VISUALS = frozenset({"table", "matrix", "pivottable"})
_SLICER_VISUALS = frozenset({"slicer", "slicervisual"})


def _json_obj(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _field_label(ref: str) -> str:
    text = str(ref or "").strip().strip("'\"")
    if "." in text:
        text = text.rsplit(".", 1)[-1]
    return text.replace("_", " ").strip() or text


def _kind_from_visual_type(vtype: str) -> str | None:
    t = vtype.lower()
    if t in _SKIP_VISUALS:
        return None
    if t in _KPI_VISUALS:
        return "kpi"
    if t in _LINE_VISUALS or "line" in t or t.endswith("area"):
        return "line"
    if t in _TABLE_VISUALS:
        return "table"
    if t == "scatterchart":
        return "scatter"
    return "bar"


def _visual_title(single: dict[str, Any], vtype: str, index: int) -> str:
    objs = single.get("vcObjects") if isinstance(single.get("vcObjects"), dict) else {}
    titles = objs.get("title") if isinstance(objs, dict) else None
    if isinstance(titles, list) and titles and isinstance(titles[0], dict):
        props = titles[0].get("properties") or {}
        expr = ((props.get("text") or {}).get("expr") or {}) if isinstance(props, dict) else {}
        lit = ((expr.get("Literal") or {}).get("Value") if isinstance(expr, dict) else None)
        if isinstance(lit, str) and lit.strip():
            return lit.strip().strip("'\"")
    for bucket in (single.get("projections") or {}).values():
        if not isinstance(bucket, list):
            continue
        for item in bucket:
            if not isinstance(item, dict):
                continue
            ref = item.get("queryRef") or item.get("nativeQueryRef")
            if ref:
                return _field_label(str(ref))
    for sel in (single.get("prototypeQuery") or {}).get("Select") or []:
        if isinstance(sel, dict):
            name = sel.get("NativeReferenceName") or sel.get("Name")
            if name:
                return _field_label(str(name))
    pretty = "".join(
        f" {ch.lower()}" if ch.isupper() else ch for ch in vtype
    ).strip().title()
    return pretty or f"Visual {index}"


def _is_tooltip_page(name: str) -> bool:
    n = name.strip().lower()
    return n == "tooltip" or n.startswith("tooltip")


def _compose_page_visuals(items: list[dict[str, str]]) -> list[dict[str, str]]:
    kpis = [v for v in items if v.get("kind") == "kpi"][:4]
    charts = [v for v in items if v.get("kind") in {"bar", "line", "scatter"}][:4]
    tables = [v for v in items if v.get("kind") == "table"][:1]
    if not kpis and not charts and not tables:
        return [
            {"name": "Trend", "kind": "line"},
            {"name": "Breakdown", "kind": "bar"},
            {"name": "Detail", "kind": "table"},
        ]
    if not tables:
        tables = [{"name": "Detail", "kind": "table"}]
    return kpis + charts + tables


def _slicer_entry(single: dict[str, Any]) -> dict[str, str] | None:
    vtype = str(single.get("visualType") or "").lower()
    if vtype not in _SLICER_VISUALS and "slicer" not in vtype:
        return None
    title = _visual_title(single, vtype, 0)
    if not title or title.lower() in {"slicer", "visual"}:
        return None
    return {"name": title, "field": title, "kind": "slicer"}


def filters_from_report(data: Any) -> dict[str, list[dict[str, str]]]:
    """Page display name → slicers (Power BI filter well)."""
    if not isinstance(data, dict):
        return {}
    out: dict[str, list[dict[str, str]]] = {}
    sections = data.get("sections")
    if isinstance(sections, list):
        for section in sections:
            if not isinstance(section, dict):
                continue
            page = str(section.get("displayName") or section.get("name") or "Page")
            if _is_tooltip_page(page):
                continue
            found: list[dict[str, str]] = []
            seen: set[str] = set()
            for raw in section.get("visualContainers") or []:
                if not isinstance(raw, dict):
                    continue
                cfg = _json_obj(raw.get("config"))
                if not isinstance(cfg, dict):
                    continue
                single = cfg.get("singleVisual")
                if not isinstance(single, dict):
                    continue
                entry = _slicer_entry(single)
                if not entry or entry["field"] in seen:
                    continue
                seen.add(entry["field"])
                found.append(entry)
            out[page] = found
        return out
    pages = data.get("pages")
    if isinstance(pages, list):
        for page in pages:
            if not isinstance(page, dict):
                continue
            name = str(page.get("name") or "Page")
            if _is_tooltip_page(name):
                continue
            found = []
            seen: set[str] = set()
            for vis in page.get("visuals") or []:
                if not isinstance(vis, dict):
                    continue
                vtype = str(vis.get("type") or vis.get("visualType") or "")
                if "slicer" not in vtype.lower():
                    continue
                title = str(vis.get("title") or vis.get("name") or "").strip()
                if title and title not in seen:
                    seen.add(title)
                    found.append({"name": title, "field": title, "kind": "slicer"})
            out[name] = found
    return out


def visuals_from_report(data: Any) -> dict[str, list[dict[str, str]]]:
    """Page display name → composed visuals (title + kind), chrome skipped."""
    if not isinstance(data, dict):
        return {}
    out: dict[str, list[dict[str, str]]] = {}
    sections = data.get("sections")
    if isinstance(sections, list):
        for section in sections:
            if not isinstance(section, dict):
                continue
            page = str(section.get("displayName") or section.get("name") or "Page")
            items: list[dict[str, str]] = []
            seen: set[str] = set()
            for i, raw in enumerate(section.get("visualContainers") or [], start=1):
                if not isinstance(raw, dict):
                    continue
                cfg = _json_obj(raw.get("config"))
                if not isinstance(cfg, dict):
                    continue
                single = cfg.get("singleVisual")
                if not isinstance(single, dict):
                    continue
                vtype = str(single.get("visualType") or "")
                kind = _kind_from_visual_type(vtype)
                if kind is None:
                    continue
                title = _visual_title(single, vtype, i)
                base = title
                n = 2
                while title in seen:
                    title = f"{base} ({n})"
                    n += 1
                seen.add(title)
                items.append({"name": title, "kind": kind})
            if _is_tooltip_page(page):
                continue
            out[page] = _compose_page_visuals(items) if items else []
        return out
    pages = data.get("pages")
    if isinstance(pages, list):
        for page in pages:
            if not isinstance(page, dict):
                continue
            name = str(page.get("name") or "Page")
            items = []
            for i, vis in enumerate(page.get("visuals") or [], start=1):
                if not isinstance(vis, dict):
                    continue
                vtype = str(vis.get("type") or vis.get("visualType") or "table")
                kind = _kind_from_visual_type(vtype)
                if kind is None:
                    continue
                title = str(vis.get("title") or vis.get("name") or f"Visual {i}")
                items.append({"name": title, "kind": kind})
            if _is_tooltip_page(name):
                continue
            out[name] = _compose_page_visuals(items) if items else []
    return out


def parse_report_json(data: Any) -> tuple[int, int, list[str]]:
    """Return ``(pages, visuals, page_names)`` from fixture JSON or pbix Layout."""
    if not isinstance(data, dict):
        return 0, 0, []
    if isinstance(data.get("pages"), list):
        pages = [p for p in data["pages"] if isinstance(p, dict)]
        names = [str(p.get("name") or "Page") for p in pages]
        visuals = sum(len(p.get("visuals") or []) for p in pages)
        return len(pages), visuals, names
    sections = data.get("sections")
    if isinstance(sections, list):
        names = [
            str(s.get("displayName") or s.get("name") or "Page")
            for s in sections
            if isinstance(s, dict)
        ]
        visuals = 0
        for section in sections:
            if isinstance(section, dict):
                visuals += len(section.get("visualContainers") or [])
        return len(sections), visuals, names
    return 0, 0, []


def _from_model_json(model: dict[str, Any]) -> dict[str, Any]:
    tables: dict[str, dict[str, Any]] = {}
    for table in model.get("tables") or []:
        if not isinstance(table, dict) or not table.get("name"):
            continue
        name = str(table["name"])
        cols: dict[str, str] = {}
        for col in table.get("columns") or []:
            if isinstance(col, dict) and col.get("name"):
                cols[str(col["name"])] = str(col.get("dataType") or "string")
        measures: list[dict[str, str]] = []
        for meas in table.get("measures") or []:
            if not isinstance(meas, dict) or not meas.get("name"):
                continue
            expr = meas.get("expression")
            if isinstance(expr, list):
                formula = "\n".join(str(p) for p in expr)
            else:
                formula = str(expr or "")
            measures.append(
                {
                    "name": str(meas["name"]),
                    "formula": formula.strip(),
                    "aggregation": "unknown",
                }
            )
        tables[name] = {"columns": cols, "measures": measures}

    relationships: list[dict[str, str]] = []
    for rel in model.get("relationships") or []:
        if not isinstance(rel, dict):
            continue
        if rel.get("fromTable") and rel.get("toTable"):
            relationships.append(
                {
                    "fromColumn": f"{rel.get('fromTable')}.{rel.get('fromColumn')}",
                    "toColumn": f"{rel.get('toTable')}.{rel.get('toColumn')}",
                }
            )

    roles: list[dict[str, Any]] = []
    for role in model.get("roles") or []:
        if not isinstance(role, dict) or not role.get("name"):
            continue
        perms = []
        for perm in role.get("tablePermissions") or []:
            if not isinstance(perm, dict):
                continue
            expr = perm.get("filterExpression")
            if isinstance(expr, list):
                expression = "\n".join(str(p) for p in expr)
            else:
                expression = str(expr or "")
            perms.append(
                {
                    "table": str(perm.get("name") or ""),
                    "expression": expression.strip(),
                }
            )
        roles.append({"name": str(role["name"]), "permissions": perms})

    return {"tables": tables, "relationships": relationships, "roles": roles}


def _read_json_bytes(raw: bytes) -> Any:
    # pbix Report/Layout is often UTF-16LE without a BOM (`{\x00"\x00…`).
    if raw[:2] in {b"\xff\xfe", b"\xfe\xff"}:
        text = raw.decode("utf-16", errors="replace")
    elif len(raw) >= 4 and raw[1] == 0 and raw[0] != 0:
        text = raw.decode("utf-16-le", errors="replace")
    else:
        text = raw.decode("utf-8-sig", errors="replace").lstrip("\ufeff")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _model_from_schema_zip(path: Path) -> dict[str, Any]:
    """Fallback for ``.pbit`` templates that ship ``DataModelSchema`` JSON."""
    with zipfile.ZipFile(path) as zf:
        if "DataModelSchema" not in zf.namelist():
            return {"tables": {}, "relationships": [], "roles": []}
        parsed = _read_json_bytes(zf.read("DataModelSchema"))
    if not isinstance(parsed, dict):
        return {"tables": {}, "relationships": [], "roles": []}
    inner = parsed.get("model") if isinstance(parsed.get("model"), dict) else parsed
    return _from_model_json(inner if isinstance(inner, dict) else {})


def _layout_from_zip(
    path: Path,
) -> tuple[
    int,
    int,
    list[str],
    dict[str, list[dict[str, str]]],
    dict[str, list[dict[str, str]]],
]:
    with zipfile.ZipFile(path) as zf:
        if "Report/Layout" not in zf.namelist():
            return 0, 0, [], {}, {}
        parsed = _read_json_bytes(zf.read("Report/Layout"))
    pages, visuals, names = parse_report_json(parsed)
    return (
        pages,
        visuals,
        names,
        visuals_from_report(parsed),
        filters_from_report(parsed),
    )


def _extract_pbix(path: Path) -> dict[str, Any]:
    model: dict[str, Any] = {"tables": {}, "relationships": [], "roles": []}
    try:
        model = _from_pbixray(path)
    except Exception:  # noqa: BLE001
        model = {"tables": {}, "relationships": [], "roles": []}
    if not (model.get("tables") or {}):
        model = _model_from_schema_zip(path)
    pages, visuals, page_names, page_visuals, page_filters = _layout_from_zip(path)
    model["tables"] = {
        name: meta
        for name, meta in (model.get("tables") or {}).items()
        if not is_hidden_date_table(name)
    }
    return {
        "model": model,
        "pages": pages,
        "visuals": visuals,
        "page_names": page_names,
        "page_visuals": page_visuals,
        "page_filters": page_filters,
    }


def _extract_folder(path: Path) -> dict[str, Any]:
    tmdl_path = path / "model.tmdl"
    if not tmdl_path.is_file():
        tmdls = sorted(path.glob("*.tmdl"))
        tmdl_path = tmdls[0] if tmdls else tmdl_path
    model: dict[str, Any] = {"tables": {}, "relationships": [], "roles": []}
    if tmdl_path.is_file():
        model = parse_tmdl(tmdl_path.read_text(encoding="utf-8"))
    pages = visuals = 0
    page_names: list[str] = []
    page_visuals: dict[str, list[dict[str, str]]] = {}
    page_filters: dict[str, list[dict[str, str]]] = {}
    report_path = path / "report.json"
    if report_path.is_file():
        parsed = _read_json_bytes(report_path.read_bytes())
        pages, visuals, page_names = parse_report_json(parsed)
        page_visuals = visuals_from_report(parsed)
        page_filters = filters_from_report(parsed)
    return {
        "model": model,
        "pages": pages,
        "visuals": visuals,
        "page_names": page_names,
        "page_visuals": page_visuals,
        "page_filters": page_filters,
    }


def extract_powerbi_source(path: Path) -> dict[str, Any]:
    if path.is_file() and path.suffix.lower() in {".pbix", ".pbit"}:
        payload = _extract_pbix(path)
    elif path.is_file() and path.suffix.lower() == ".tmdl":
        payload = {
            "model": parse_tmdl(path.read_text(encoding="utf-8")),
            "pages": 0,
            "visuals": 0,
            "page_names": [],
            "page_visuals": {},
            "page_filters": {},
        }
    else:
        payload = _extract_folder(path)
    payload["workbook"] = path.name
    return payload


def estate_part(path: Path) -> dict[str, Any]:
    extracted = extract_powerbi_source(path)
    model = extracted["model"]
    tables = sorted(
        name for name in (model.get("tables") or {}) if not is_hidden_date_table(name)
    )
    columns = {
        name: dict(sorted((meta.get("columns") or {}).items()))
        for name, meta in (model.get("tables") or {}).items()
        if not is_hidden_date_table(name)
    }
    sources = {
        name: compact_m(str(meta.get("source") or ""))
        for name, meta in (model.get("tables") or {}).items()
        if meta.get("source") and not is_hidden_date_table(name)
    }
    fks: list[tuple[str, str, str, str]] = []
    for rel in model.get("relationships") or []:
        lt, lc = _split_col_ref(str(rel.get("fromColumn") or ""))
        rt, rc = _split_col_ref(str(rel.get("toColumn") or ""))
        hidden = is_hidden_date_table(lt) or is_hidden_date_table(rt)
        if lt and lc and rt and rc and not hidden:
            fks.append((lt, lc, rt, rc))
    return {
        "workbook": extracted["workbook"],
        "tables": tables,
        "columns": columns,
        "sources": sources,
        "foreign_keys": fks,
        "worksheets": int(extracted.get("visuals") or 0),
        "dashboards": int(extracted.get("pages") or 0),
    }


def kpi_rows(path: Path) -> list[dict[str, Any]]:
    extracted = extract_powerbi_source(path)
    rows: list[dict[str, Any]] = []
    for table, meta in (extracted["model"].get("tables") or {}).items():
        for meas in meta.get("measures") or []:
            name = str(meas.get("name") or "").strip()
            formula = str(meas.get("formula") or "").strip()
            if not name or not formula:
                continue
            rows.append(
                {
                    "name": name,
                    "workbook": extracted["workbook"],
                    "formula": formula,
                    "aggregation": str(meas.get("aggregation") or "unknown"),
                    "datatype": "",
                    "role": "measure",
                    "table": table,
                }
            )
    return rows


def dashboard_rows(path: Path) -> list[dict[str, Any]]:
    extracted = extract_powerbi_source(path)
    names = list(extracted.get("page_names") or [])
    if not names:
        return []
    page_visuals = extracted.get("page_visuals") or {}
    page_filters = extracted.get("page_filters") or {}
    stem = path.stem if path.is_file() else path.name
    out: list[dict[str, Any]] = []
    for name in names:
        if _is_tooltip_page(name):
            continue
        dash_id = f"{stem}::{name}"
        if name in page_visuals:
            tiles = page_visuals[name]
        else:
            tiles = _compose_page_visuals([])
        if not tiles:
            continue
        out.append(
            {
                "id": dash_id,
                "workbook": extracted["workbook"],
                "name": name,
                "source": "powerbi",
                "filters": list(page_filters.get(name) or []),
                "worksheets": [
                    {
                        "name": tile["name"],
                        "kind": tile["kind"],
                        "key": f"{dash_id}::{tile['name']}",
                    }
                    for tile in tiles
                ],
            }
        )
    return out


def source_columns_from_dax(expr: str) -> list[str]:
    cols = [m.group(1) for m in _COL_REF.finditer(expr)]
    seen: set[str] = set()
    out: list[str] = []
    for col in cols:
        if col not in seen:
            seen.add(col)
            out.append(col)
    return out


def _rls_rule(extracted: dict[str, Any]) -> dict[str, Any] | None:
    roles = extracted["model"].get("roles") or []
    if not roles:
        return None
    branches: list[dict[str, Any]] = []
    for role in roles:
        name = str(role.get("name") or "").strip()
        perms = role.get("permissions") or []
        conds = [str(p.get("expression") or "").strip() for p in perms if p.get("expression")]
        condition = " AND ".join(conds) if conds else "(no table filter)"
        cols: list[str] = []
        for expr in conds:
            cols.extend(source_columns_from_dax(expr))
        branches.append(
            {
                "condition": condition,
                "grants_to": name or "role",
                "source_columns": list(dict.fromkeys(cols)),
            }
        )
    names = [str(r.get("name") or "") for r in roles]
    return {
        "workbook": extracted["workbook"],
        "branches": branches,
        "plain_english": (
            f"Power BI RLS roles on `{extracted['workbook']}`: "
            + ", ".join(f"`{n}`" for n in names)
            + "."
        ),
    }


def _model_contract_rule(extracted: dict[str, Any]) -> dict[str, Any] | None:
    """Screen 4 fallback: colliding table names / M sources (no public MIT RLS)."""
    branches: list[dict[str, Any]] = []
    for name, meta in sorted((extracted["model"].get("tables") or {}).items()):
        if is_hidden_date_table(name):
            continue
        cols = sorted(meta.get("columns") or {})
        origin = compact_m(str(meta.get("source") or "")) or "(no M source)"
        branches.append(
            {
                "condition": f"{len(cols)} columns · {origin}",
                "grants_to": name,
                "source_columns": cols[:16],
            }
        )
    if not branches:
        return None
    return {
        "workbook": extracted["workbook"],
        "branches": branches,
        "plain_english": (
            f"Table contracts in `{extracted['workbook']}` "
            "(no RLS in this file — comparing names, columns, and M sources)."
        ),
    }


def access_rule(path: Path) -> dict[str, Any] | None:
    extracted = extract_powerbi_source(path)
    return _rls_rule(extracted) or _model_contract_rule(extracted)


def peek_text(path: Path, *, limit: int = 1200) -> tuple[str, str]:
    """Return ``(language, snippet)`` for the Load-screen peek expander."""
    if path.is_dir():
        tmdl = path / "model.tmdl"
        if tmdl.is_file():
            text = tmdl.read_text(encoding="utf-8", errors="replace")
            return "text", text[:limit] + ("\n…" if len(text) > limit else "")
        report = path / "report.json"
        if report.is_file():
            text = report.read_text(encoding="utf-8", errors="replace")
            return "json", text[:limit] + ("\n…" if len(text) > limit else "")
    if path.is_file() and path.suffix.lower() == ".tmdl":
        text = path.read_text(encoding="utf-8", errors="replace")
        return "text", text[:limit] + ("\n…" if len(text) > limit else "")
    if path.is_file() and path.suffix.lower() in {".pbix", ".pbit"}:
        extracted = extract_powerbi_source(path)
        chunks: list[str] = []
        for table, meta in (extracted["model"].get("tables") or {}).items():
            origin = compact_m(str(meta.get("source") or ""))
            if origin:
                chunks.append(f"// {table} ← {origin}")
            for meas in (meta.get("measures") or [])[:3]:
                formula = str(meas.get("formula") or "").strip()
                if formula:
                    chunks.append(f"{table}.{meas.get('name')} = {formula}")
            if len(chunks) >= 8:
                break
        if chunks:
            text = "\n\n".join(chunks)
            return "dax", text[:limit] + ("\n…" if len(text) > limit else "")
        try:
            with zipfile.ZipFile(path) as zf:
                listing = "\n".join(zf.namelist()[:40])
            return "text", listing
        except zipfile.BadZipFile:
            return "text", "(not a valid Power BI ZIP)"
    return "text", ""
