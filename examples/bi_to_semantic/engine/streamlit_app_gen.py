"""Generate a Streamlit dashboard bound to the semantic view.

The generated app never queries base tables — live mode uses ``SEMANTIC_VIEW(...)``.
Disconnected mode serves sample frames shaped like that view so the app runs
without a warehouse.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from engine.paths import warehouse_ids

SEMANTIC_VIEW_NAME = "BI_OPS_METRICS"
APP_DIRNAME = "streamlit_dash"
APP_DIRNAME_COCO = "streamlit_dash_coco"

_AUTHORS = [
    "Kim Lee",
    "Alex Rivera",
    "Sam Okonkwo",
    "Jordan Hale",
    "Priya Shah",
    "Chris Nguyen",
]
_ROLES = ["Viewer", "Explorer", "Creator", "Site admin", "Server admin"]
_SITES = ["Default", "Analytics", "Finance"]
_FILTER_PRESETS: dict[str, list[str]] = {
    "sales region": ["Americas", "EMEA", "APAC"],
    "region": ["North", "South", "East", "West", "Central"],
    "state": ["California", "Texas", "New York", "Washington", "Illinois"],
    "name": list(_AUTHORS),
    "product": ["Alpha", "Bravo", "Charlie", "Delta", "Echo"],
    "industry": ["Finance", "Healthcare", "Retail", "Energy", "Manufacturing"],
    "month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"],
    "period": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"],
    "site": list(_SITES),
    "country": ["United States", "United Kingdom", "Germany", "France", "Japan"],
    "type": ["Workbook", "View", "Datasource", "Flow"],
    "business area": ["IT", "Finance", "Operations", "Sales"],
}


def app_dir(out_dir: Path, *, variant: str = "deterministic") -> Path:
    name = APP_DIRNAME_COCO if variant == "coco" else APP_DIRNAME
    return out_dir / name


def generated_app_exists(out_dir: Path, *, variant: str) -> bool:
    return (app_dir(out_dir, variant=variant) / "streamlit_app.py").is_file()


def load_app_spec(out_dir: Path, *, variant: str) -> dict[str, Any] | None:
    path = app_dir(out_dir, variant=variant) / "spec.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def list_generated_files(dest: Path) -> list[str]:
    if not dest.is_dir():
        return []
    names: list[str] = []
    for path in sorted(dest.rglob("*")):
        if path.is_file() and path.name not in {".preview.pid", ".preview.log"}:
            names.append(str(path.relative_to(dest)))
    return names


def _worksheet_kind(name: str) -> str:
    n = name.lower()
    if any(w in n for w in ("top ", "leader", "author", "publisher", "viewer")):
        return "bar"
    if "role" in n:
        return "bar"
    if any(w in n for w in ("trend", "active", "summary", "count")):
        return "kpi"
    if any(w in n for w in ("detail", "content", "not ", "list")):
        return "table"
    return "table"


def _visual_entry(ws: Any) -> tuple[str, str, str]:
    """Return ``(display_name, kind, table_key)`` for a worksheet or Power BI tile."""
    if isinstance(ws, dict):
        name = str(ws.get("name") or "Visual")
        kind = str(ws.get("kind") or _worksheet_kind(name))
        key = str(ws.get("key") or name)
        return name, kind, key
    name = str(ws)
    return name, _worksheet_kind(name), name


def _ws_icon(kind: str) -> str:
    if kind == "bar":
        return ":material/bar_chart:"
    if kind == "line":
        return ":material/show_chart:"
    if kind == "scatter":
        return ":material/scatter_plot:"
    if kind == "kpi":
        return ":material/speed:"
    return ":material/table_rows:"


def build_spec(
    *,
    dashboards: list[dict[str, Any]],
    metric_decisions: list[dict[str, Any]],
    all_decisions: list[dict[str, Any]],
    estate: dict[str, Any] | None,
) -> dict[str, Any]:
    database, schema = warehouse_ids()
    metrics = []
    for dec in metric_decisions:
        if dec.get("action") == "drop":
            continue
        metrics.append(
            {
                "name": str(dec.get("metric_name") or dec.get("subject") or "metric"),
                "plain_english": str(dec.get("plain_english") or ""),
                "decision_id": str(dec.get("id") or ""),
            }
        )
    if not metrics:
        metrics = [
            {"name": "active_users", "plain_english": "Count of users.", "decision_id": ""},
            {
                "name": "published_items",
                "plain_english": "Count of published content.",
                "decision_id": "",
            },
        ]
    decision_ids = [str(d.get("id")) for d in all_decisions if d.get("id")]
    return {
        "semantic_view": f"{database}.{schema}.{SEMANTIC_VIEW_NAME}",
        "database": database,
        "schema": schema,
        "view_name": SEMANTIC_VIEW_NAME,
        "decision_ids": decision_ids,
        "metrics": metrics,
        "dashboards": dashboards,
        "shared_tables": [
            t.get("name") for t in ((estate or {}).get("tables") or []) if t.get("name")
        ][:8],
    }


def _sample_rows(ws: str, kind: str | None = None) -> list[dict[str, Any]]:
    n = ws.lower()
    kind = kind or _worksheet_kind(ws)
    seed = sum(ord(c) for c in ws) % 17
    if "role" in n:
        return [
            {"label": role, "value": val}
            for role, val in zip(_ROLES, [210, 48, 22, 4, 2], strict=True)
        ]
    if "author" in n or "publisher" in n:
        return [{"label": person, "value": 92 - i * 11} for i, person in enumerate(_AUTHORS)]
    if "viewer" in n:
        return [
            {"label": person, "value": 38 + i * 9} for i, person in enumerate(reversed(_AUTHORS))
        ]
    if "not logging" in n:
        return [
            {"name": person, "site": _SITES[i % 3], "days_idle": 14 + i * 3}
            for i, person in enumerate(_AUTHORS)
        ]
    if "not accessing" in n:
        return [
            {"name": person, "site": _SITES[i % 3], "views": 0}
            for i, person in enumerate(_AUTHORS[:4])
        ]
    if kind == "kpi":
        return [{"label": "period", "value": 40 + seed + i * 4} for i in range(7)]
    if kind == "line":
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"]
        return [
            {"label": month, "value": 50 + seed + i * 7} for i, month in enumerate(months)
        ]
    if kind == "bar":
        cats = ["North", "South", "East", "West", "Central"]
        return [{"label": cat, "value": 20 + seed + i * 9} for i, cat in enumerate(cats)]
    if kind == "scatter":
        return [
            {
                "x": 10 + i * 3,
                "y": 15 + seed + i * 2,
                "label": _AUTHORS[i % len(_AUTHORS)],
            }
            for i in range(8)
        ]
    return [
        {
            "name": f"{ws} #{i}",
            "site": _SITES[i % 3],
            "owner": _AUTHORS[i % len(_AUTHORS)],
            "count": 12 + i * 3,
        }
        for i in range(1, 9)
    ]


def _values_for(field: str) -> list[str]:
    key = field.lower().strip()
    for needle, vals in _FILTER_PRESETS.items():
        if needle in key:
            return list(vals)
    return [f"{field} {i}" for i in range(1, 5)]


def _dash_filter_fields(spec: dict[str, Any]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for dash in spec.get("dashboards") or []:
        for item in dash.get("filters") or []:
            name = str(item.get("field") or item.get("name") or "").strip()
            if name and name not in seen:
                seen.add(name)
                out.append(name)
    return out


def _stamp_filters(rows: list[dict[str, Any]], fields: list[str]) -> list[dict[str, Any]]:
    if not fields:
        return rows
    stamped: list[dict[str, Any]] = []
    for i, row in enumerate(rows):
        extra = dict(row)
        for field in fields:
            vals = _values_for(field)
            extra.setdefault(field, vals[i % len(vals)])
        stamped.append(extra)
    return stamped


def _build_facts(spec: dict[str, Any]) -> list[dict[str, Any]]:
    fields = _dash_filter_fields(spec) or ["Region", "Month"]
    months = _FILTER_PRESETS["month"]
    rows: list[dict[str, Any]] = []
    for i in range(24):
        row: dict[str, Any] = {
            "period": months[i % len(months)],
            "value": 40 + (i * 7) % 80,
        }
        for field in fields:
            vals = _values_for(field)
            row[field] = vals[i % len(vals)]
        rows.append(row)
    return rows


def build_disconnected_data(spec: dict[str, Any]) -> dict[str, Any]:
    """Sample frames that mimic SEMANTIC_VIEW output — not warehouse data."""
    kpis: dict[str, Any] = {}
    series: dict[str, list[int]] = {}
    seed = [42, 51, 48, 63, 70, 66, 81]
    for i, m in enumerate(spec.get("metrics") or []):
        name = str(m.get("name"))
        base = 800 + i * 137
        kpis[name] = {"value": base, "delta": f"+{(i + 3)}%"}
        series[name] = [base - 80 + 11 * x for x in seed]

    fields = _dash_filter_fields(spec)
    tables: dict[str, list[dict[str, Any]]] = {}
    for dash in spec.get("dashboards") or []:
        page_fields = [
            str(item.get("field") or item.get("name") or "").strip()
            for item in (dash.get("filters") or [])
            if item.get("field") or item.get("name")
        ] or fields
        for ws in dash.get("worksheets") or []:
            name, kind, key = _visual_entry(ws)
            tables[key] = _stamp_filters(_sample_rows(name, kind), page_fields)
    catalog = {field: _values_for(field) for field in fields}
    return {
        "kpis": kpis,
        "series": series,
        "tables": tables,
        "filters": catalog,
        "facts": _build_facts(spec),
        "mode": "disconnected",
    }


def semantic_view_sql(spec: dict[str, Any], *, metrics: list[str], dimensions: list[str]) -> str:
    fqn = spec["semantic_view"]
    met = ", ".join(metrics) if metrics else "1 AS measure"
    dim = ", ".join(dimensions) if dimensions else ""
    dim_clause = f"\n  DIMENSIONS {dim}" if dim else ""
    return f"SELECT * FROM SEMANTIC_VIEW(\n  {fqn}\n  METRICS {met}{dim_clause}\n)"


def write_contract(
    dest: Path,
    *,
    spec: dict[str, Any],
    yaml_body: str,
) -> None:
    """Write the semantic-view contract files the app must consume."""
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "data").mkdir(exist_ok=True)
    data = build_disconnected_data(spec)
    (dest / "spec.json").write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    (dest / "data" / "disconnected.json").write_text(
        json.dumps(data, indent=2) + "\n", encoding="utf-8"
    )
    (dest / "semantic_view.yaml").write_text(yaml_body, encoding="utf-8")


def write_streamlit_app(
    out_dir: Path,
    *,
    spec: dict[str, Any],
    yaml_body: str,
) -> Path:
    """Write the deterministic Streamlit app under ``out/streamlit_dash/``."""
    dest = app_dir(out_dir, variant="deterministic")
    write_contract(dest, spec=spec, yaml_body=yaml_body)
    (dest / ".streamlit").mkdir(exist_ok=True)
    (dest / ".streamlit" / "config.toml").write_text(_THEME, encoding="utf-8")
    (dest / "sv.py").write_text(_SV_PY, encoding="utf-8")
    (dest / "streamlit_app.py").write_text(_APP_PY, encoding="utf-8")
    (dest / "README.md").write_text(_readme(spec), encoding="utf-8")
    return dest


def list_coco_markdown(out_dir: Path) -> list[str]:
    """Markdown files in the CoCo app tree (BRIEF.md first)."""
    dest = app_dir(out_dir, variant="coco")
    if not dest.is_dir():
        return []
    names = sorted(path.name for path in dest.glob("*.md") if path.is_file())
    if "BRIEF.md" in names:
        names.remove("BRIEF.md")
        names.insert(0, "BRIEF.md")
    return names


def load_coco_markdown(out_dir: Path, name: str) -> str | None:
    dest = app_dir(out_dir, variant="coco")
    path = dest / Path(name).name
    if path.suffix.lower() != ".md" or not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    return text if text.strip() else None


def save_coco_markdown(out_dir: Path, name: str, body: str) -> Path:
    dest = app_dir(out_dir, variant="coco")
    dest.mkdir(parents=True, exist_ok=True)
    safe = Path(name).name
    if not safe.endswith(".md"):
        raise ValueError(f"Not a markdown file: {name}")
    path = dest / safe
    text = body if body.endswith("\n") else f"{body}\n"
    path.write_text(text, encoding="utf-8")
    return path


def brief_path(out_dir: Path) -> Path:
    return app_dir(out_dir, variant="coco") / "BRIEF.md"


def load_brief(out_dir: Path) -> str | None:
    return load_coco_markdown(out_dir, "BRIEF.md")


def save_brief(out_dir: Path, body: str) -> Path:
    return save_coco_markdown(out_dir, "BRIEF.md", body)


def brief_is_saved(out_dir: Path, editor: str) -> bool:
    disk = load_brief(out_dir)
    if disk is None:
        return False
    return disk.strip() == (editor or "").strip()


def prepare_coco_app(
    out_dir: Path,
    *,
    spec: dict[str, Any],
    yaml_body: str,
) -> Path:
    """Drop the contract under ``out/streamlit_dash_coco/`` for CoCo to author."""
    dest = app_dir(out_dir, variant="coco")
    write_contract(dest, spec=spec, yaml_body=yaml_body)
    return dest


def _brief_dashboard_block(spec: dict[str, Any]) -> str:
    """Readable per-workbook summary — never a comma wall of tile names."""
    by_wb: dict[str, list[dict[str, Any]]] = {}
    for dash in spec.get("dashboards") or []:
        by_wb.setdefault(str(dash.get("workbook") or "Workbook"), []).append(dash)
    if not by_wb:
        return "(none selected)"
    parts: list[str] = []
    for workbook, dashes in by_wb.items():
        source = str(dashes[0].get("source") or "")
        label = "Power BI" if source == "powerbi" else "Tableau" if source == "tableau" else "BI"
        parts.append(f"### {workbook} ({label})")
        for dash in dashes:
            kpis: list[str] = []
            charts: list[str] = []
            tables: list[str] = []
            for ws in dash.get("worksheets") or []:
                name, kind, _key = _visual_entry(ws)
                if kind == "kpi":
                    kpis.append(name)
                elif kind == "table":
                    tables.append(name)
                else:
                    charts.append(f"{name} ({kind})")
            slicers = [
                str(item.get("name") or item.get("field"))
                for item in (dash.get("filters") or [])
                if item.get("name") or item.get("field")
            ]
            parts.append(f"- **{dash.get('name')}**")
            if slicers:
                parts.append(f"  - Slicers: {', '.join(slicers)}")
            else:
                parts.append("  - Slicers: none parsed — still add Region + period filters")
            if kpis:
                parts.append(f"  - Cards: {', '.join(kpis)}")
            if charts:
                parts.append(f"  - Charts: {', '.join(charts)}")
            if tables:
                parts.append("  - Detail matrix")
        parts.append("")
    return "\n".join(parts).rstrip()


def _brief_sources(spec: dict[str, Any]) -> set[str]:
    return {str(d.get("source") or "") for d in (spec.get("dashboards") or [])}


def build_coco_prompt(spec: dict[str, Any], *, dest_name: str) -> str:
    view = spec.get("semantic_view")
    metrics = [str(m.get("name")) for m in (spec.get("metrics") or []) if m.get("name")]
    dashes = _brief_dashboard_block(spec)
    met_lines = "\n".join(f"- `{name}`" for name in metrics) or "- (none)"
    sources = _brief_sources(spec)
    if sources == {"powerbi"}:
        accent = (
            "Power BI look: primary `#F2C811`, dark text `#1C1C1C`, white cards, "
            "soft gray canvas `#F3F2F1`. Page tabs feel like a report."
        )
    elif sources == {"tableau"}:
        accent = (
            "Tableau look: primary `#E97627`, navy text `#1B1B1B`, white worksheets, "
            "cool gray canvas `#F5F5F5`. Filter shelf on the left or top."
        )
    else:
        accent = (
            "Mixed estate: charcoal primary `#1C2429`, gold highlight `#C9A227`, "
            "white cards, canvas `#F6F7F9`. Do not copy the Python teal `#0F6E8C`."
        )
    return f"""\
Author a **BI-grade** Streamlit consumer for migrated Tableau / Power BI pages.

This is **not** a restyle of `{APP_DIRNAME}/`. That tree is a thin deterministic
scaffold (KPI row + two native charts + one dataframe). Clone it and you fail
the brief. Build a report that a Tableau or Power BI user would recognize.

Working directory is the generate `out/` folder. Read `{dest_name}/BRIEF.md`,
`{dest_name}/spec.json`, and `{dest_name}/data/disconnected.json`.
Do **not** modify `{APP_DIRNAME}/`.

## Hard constraints

1. Live SQL is only `SELECT * FROM SEMANTIC_VIEW(...)` against `{view}`.
2. Never `SELECT` from base tables (`USERS`, `HISTORICAL_EVENTS`, etc.).
3. Default mode is **disconnected**: load `{dest_name}/data/disconnected.json`.
   Honour env `TTS_DATA_MODE` (`disconnected` | `live`).
4. Live mode: `st.connection("snowflake")` + `semantic_sql()`. If live fails,
   say so and fall back to sample frames — do not query tables.
5. Streamlit ≥1.57: `width="stretch"` (never `use_container_width`), Material
   icons (`:material/...:`), sentence case. No `st.divider`.
6. Provenance decision ids from spec.json go in a caption, not a hero banner.

## UX you must ship (Tableau / Power BI)

### Report chrome
- `st.set_page_config(..., layout="wide")` and a report title + source badge
  (Power BI / Tableau) on one horizontal row.
- **Page navigator** — one control for every dashboard below (`st.pills` or
  `st.tabs`). This is the Power BI page strip / Tableau dashboard tabs.
- Sidebar holds **global slicers only** (plus data mode). No charts in the sidebar.

### Slicers and cross-filter (required)
- Render every field in `dashboards[].filters` (and `disconnected.json.filters`).
  ≤5 values → `st.pills` / `st.segmented_control`. More → `st.multiselect`.
  Dates/periods → `st.segmented_control` or a period pill row.
- **Reset slicers** button (Power BI "clear all").
- Filters apply to **every** KPI, chart, and matrix on the open page.
  In disconnected mode, filter `facts` and each tile frame in pandas
  (`disconnected.json.facts` is the shared grain).
- **Cross-highlight:** `st.bar_chart` / `st.line_chart` / `st.scatter_chart`
  / `st.altair_chart` with `on_select="rerun"`. A click sets the matching
  slicer (category → filter), like Tableau highlight / Power BI cross-filter.
- Live mode: pass active slicer fields as `DIMENSIONS` to `semantic_sql()`.

### Visuals (do not use the Python scaffold)
- **Cards** — Power BI card strip: bordered `st.metric` with large value,
  delta, and `chart_data` sparkline. One card per KPI listed for the page.
- **Charts** — Altair for area, combo, legend, and rich tooltips. Native
  charts only when you need `on_select`. Maps (State / Region / Country):
  ranked bar or Altair if no lat/lon — do not dump a dataframe.
- **Focus** — `st.popover` or `@st.dialog` "Focus" on at least one chart
  (Power BI focus mode).
- **Detail** — one matrix, not a grid of dataframes. `column_config` with
  `NumberColumn` and `ProgressColumn` or `BarChartColumn`. `hide_index=True`.
- Optional: `st.toggle` for show labels / show data table under a chart.

### Theme
- {accent}
- Set `[theme]` in config.toml including `chartCategoricalColors`.
  `gatherUsageStats = false`.

## Pages to migrate

{dashes}

## Metrics on the view

{met_lines}

Disconnected extras you must use: `filters` (value lists) and `facts`
(filterable grain). Tile frames already carry the slicer columns.

Write (use the Write tool; the human will approve each file):
- `{dest_name}/sv.py` — loaders + `semantic_sql()` + `live_query()` + a
  `apply_filters(df, selections)` helper
- `{dest_name}/streamlit_app.py` — the report UI described above
- `{dest_name}/.streamlit/config.toml` — the BI theme (not the Python teal)
- `{dest_name}/README.md` — disconnected vs live

Do not invent a different semantic view name. After writing, Glob `{dest_name}/**`.
"""


def render_inline_preview(spec: dict[str, Any], *, mode: str = "disconnected") -> None:
    """Render the generated dashboard inside the wizard (disconnected sample data)."""
    data = build_disconnected_data(spec)
    dashboards = spec.get("dashboards") or []
    if not dashboards:
        st.info("Select at least one dashboard / report page to migrate.")
        return

    with st.container(horizontal=True, vertical_alignment="center"):
        st.markdown("**Migrated dashboards**")
        if mode != "live":
            st.badge("Disconnected", icon=":material/cloud_off:", color="orange")
        else:
            st.badge("Live", icon=":material/cloud:", color="green")
        st.caption(f"`{spec.get('semantic_view')}`")

    if mode != "live":
        st.caption(
            "Sample frames shaped like `SEMANTIC_VIEW(...)` — no warehouse call. "
            "Live mode uses the generated semantic view only."
        )
    else:
        st.caption(
            f"Would query `{spec.get('semantic_view')}` — this studio still uses sample rows."
        )

    names = [str(d.get("name") or d.get("id")) for d in dashboards]
    picked = st.pills(
        "Dashboard",
        names,
        selection_mode="single",
        default=names[0],
        key="tts_inline_dash",
    )
    dash = next((d for d in dashboards if str(d.get("name")) == picked), dashboards[0])
    st.caption(f"From `{dash.get('workbook')}` · {len(dash.get('worksheets') or [])} tiles")

    _render_kpi_row(spec, data)
    _render_worksheets(spec, data, dash)


def _render_kpi_row(spec: dict[str, Any], data: dict[str, Any]) -> None:
    metrics = spec.get("metrics") or []
    if not metrics:
        return
    with st.container(horizontal=True):
        for m in metrics[:4]:
            name = str(m.get("name"))
            kpi = (data.get("kpis") or {}).get(name) or {"value": "—", "delta": None}
            st.metric(
                name.replace("_", " ").title(),
                kpi.get("value"),
                kpi.get("delta"),
                border=True,
                chart_data=(data.get("series") or {}).get(name),
                chart_type="line",
                help=str(m.get("plain_english") or ""),
            )


def _frame_for(data: dict[str, Any], key: str) -> pd.DataFrame:
    return pd.DataFrame((data.get("tables") or {}).get(key) or [])


def _render_chart(df: pd.DataFrame, kind: str) -> None:
    if df.empty:
        st.caption("No sample rows.")
        return
    if kind == "line" and "value" in df.columns:
        xcol = "label" if "label" in df.columns else df.columns[0]
        st.line_chart(df, x=xcol, y="value")
        return
    if kind == "scatter" and "x" in df.columns and "y" in df.columns:
        st.scatter_chart(df, x="x", y="y")
        return
    if kind == "bar" and "value" in df.columns:
        xcol = "label" if "label" in df.columns else df.columns[0]
        st.bar_chart(df, x=xcol, y="value")
        return
    st.dataframe(df, hide_index=True, width="stretch")


def _render_worksheets(
    spec: dict[str, Any],
    data: dict[str, Any],
    dash: dict[str, Any],
) -> None:
    entries = [_visual_entry(ws) for ws in (dash.get("worksheets") or [])]
    kpis = [e for e in entries if e[1] == "kpi"]
    charts = [e for e in entries if e[1] in {"bar", "line", "scatter"}]
    tables = [e for e in entries if e[1] == "table"]
    view = spec.get("view_name")

    if kpis:
        with st.container(horizontal=True):
            for name, _kind, key in kpis:
                df = _frame_for(data, key)
                series = df["value"].tolist() if not df.empty and "value" in df.columns else None
                last = series[-1] if series else "—"
                delta = f"{series[-1] - series[-2]:+}" if series and len(series) >= 2 else None
                st.metric(
                    name,
                    last,
                    delta,
                    border=True,
                    chart_data=series,
                    chart_type="line",
                    help=f"via `{view}`",
                )

    if charts:
        cols = st.columns(2, gap="medium")
        for i, (name, kind, key) in enumerate(charts):
            with cols[i % 2], st.container(border=True):
                st.markdown(f"{_ws_icon(kind)} **{name}**")
                st.caption(f"via `{view}`")
                _render_chart(_frame_for(data, key), kind)

    for name, kind, key in tables[:1]:
        with st.container(border=True):
            st.markdown(f"{_ws_icon(kind)} **{name}**")
            st.caption(f"via `{view}`")
            st.dataframe(_frame_for(data, key), hide_index=True, width="stretch")


def _readme(spec: dict[str, Any]) -> str:
    view = spec.get("semantic_view")
    return f"""# Generated Streamlit dashboard

Bound to semantic view `{view}`.

```bash
TTS_DATA_MODE=disconnected streamlit run streamlit_app.py
```

- **Disconnected** (default) — sample frames, no Snowflake.
- **Live** — `SELECT * FROM SEMANTIC_VIEW(...)` only. Never queries base tables.

Provenance decision ids: {", ".join(spec.get("decision_ids") or []) or "(none)"}
"""


_THEME = """\
[theme]
base = "light"
primaryColor = "#0F6E8C"
backgroundColor = "#F6F7F9"
secondaryBackgroundColor = "#FFFFFF"
textColor = "#1C2429"
borderColor = "#D8DEE4"
font = "sans serif"

[browser]
gatherUsageStats = false
"""

_SV_PY = '''\
"""Query helper — semantic view only (live) or disconnected samples."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent


def load_spec() -> dict[str, Any]:
    return json.loads((ROOT / "spec.json").read_text(encoding="utf-8"))


def load_disconnected() -> dict[str, Any]:
    return json.loads((ROOT / "data" / "disconnected.json").read_text(encoding="utf-8"))


def default_mode() -> str:
    raw = (os.environ.get("TTS_DATA_MODE") or "disconnected").strip().lower()
    return "live" if raw == "live" else "disconnected"


def semantic_sql(spec: dict[str, Any], *, metrics: list[str], dimensions: list[str]) -> str:
    fqn = spec["semantic_view"]
    met = ", ".join(metrics) if metrics else spec["metrics"][0]["name"]
    dim_clause = f"\\n  DIMENSIONS {', '.join(dimensions)}" if dimensions else ""
    return (
        f"SELECT * FROM SEMANTIC_VIEW(\\n"
        f"  {fqn}\\n"
        f"  METRICS {met}"
        f"{dim_clause}\\n"
        f")"
    )


def kpi_frame(spec: dict[str, Any], data: dict[str, Any], name: str) -> dict[str, Any]:
    return (data.get("kpis") or {}).get(name) or {"value": "—", "delta": None}


def worksheet_frame(data: dict[str, Any], worksheet: str) -> pd.DataFrame:
    return pd.DataFrame((data.get("tables") or {}).get(worksheet) or [])


def infer_kind(name: str) -> str:
    n = name.lower()
    if any(w in n for w in ("top ", "leader", "author", "publisher", "viewer", "role")):
        return "bar"
    if any(w in n for w in ("trend", "active", "summary", "count")):
        return "kpi"
    return "table"


def visual_entries(dash: dict[str, Any]) -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for ws in dash.get("worksheets") or []:
        if isinstance(ws, dict):
            name = str(ws.get("name") or "Visual")
            kind = str(ws.get("kind") or infer_kind(name))
            key = str(ws.get("key") or name)
            out.append((name, kind, key))
        else:
            name = str(ws)
            out.append((name, infer_kind(name), name))
    return out


def icon_for(kind: str) -> str:
    return {
        "bar": ":material/bar_chart:",
        "line": ":material/show_chart:",
        "scatter": ":material/scatter_plot:",
        "kpi": ":material/speed:",
    }.get(kind, ":material/table_rows:")


def render_chart(df: pd.DataFrame, kind: str) -> None:
    if df.empty:
        st.caption("No sample rows.")
        return
    if kind == "line" and "value" in df.columns:
        xcol = "label" if "label" in df.columns else df.columns[0]
        st.line_chart(df, x=xcol, y="value")
        return
    if kind == "scatter" and "x" in df.columns and "y" in df.columns:
        st.scatter_chart(df, x="x", y="y")
        return
    if kind == "bar" and "value" in df.columns:
        xcol = "label" if "label" in df.columns else df.columns[0]
        st.bar_chart(df, x=xcol, y="value")
        return
    st.dataframe(df, hide_index=True, width="stretch")


def live_query(sql: str) -> pd.DataFrame:
    conn = st.connection("snowflake")
    return conn.query(sql)
'''

_APP_PY = '''\
"""BI dashboard → Streamlit, bound to the generated semantic view."""

from __future__ import annotations

import streamlit as st

import sv

st.set_page_config(
    page_title="Migrated dashboards",
    page_icon=":material/dashboard:",
    layout="wide",
    initial_sidebar_state="expanded",
)

SPEC = sv.load_spec()
DATA = sv.load_disconnected()

with st.sidebar:
    st.markdown("### :material/database: Data")
    mode = st.segmented_control(
        "Mode",
        options=["disconnected", "live"],
        default=sv.default_mode(),
        format_func=lambda m: (
            "Disconnected · no data" if m == "disconnected" else "Live · semantic view"
        ),
        key="tts_gen_mode",
    )
    st.caption(f"Semantic view `{SPEC['semantic_view']}`")
    if mode == "disconnected":
        st.badge("No warehouse", icon=":material/cloud_off:", color="orange")
        st.caption("Sample frames with the same shape as SEMANTIC_VIEW output.")
    else:
        st.badge("Live", icon=":material/cloud:", color="green")
        st.caption("Queries the semantic view only — never base tables.")
    sql_preview = sv.semantic_sql(
        SPEC,
        metrics=[m["name"] for m in SPEC.get("metrics") or []],
        dimensions=[],
    )
    with st.expander("SEMANTIC_VIEW SQL"):
        st.code(sql_preview, language="sql")
    ids = SPEC.get("decision_ids") or []
    if ids:
        st.caption("Provenance · " + ", ".join(f"`{i}`" for i in ids[:6]))

with st.container(horizontal=True, vertical_alignment="center"):
    st.title("Migrated dashboards")
    if mode == "disconnected":
        st.badge("Disconnected", icon=":material/cloud_off:", color="orange")
    else:
        st.badge("Live semantic view", icon=":material/cloud:", color="green")

st.caption(
    "BI worksheets / visuals, now a Streamlit consumer of one semantic view "
    "and one row access policy."
)

if mode == "live":
    st.caption(
        "Live mode runs `SELECT * FROM SEMANTIC_VIEW(...)`. "
        'Configure st.connection("snowflake") in secrets to hit the warehouse.'
    )

dashboards = SPEC.get("dashboards") or []
if not dashboards:
    st.warning("No dashboards in spec.json.")
    st.stop()

labels = [d["name"] for d in dashboards]
chosen = st.pills("Dashboard", labels, selection_mode="single", default=labels[0])
dash = next(d for d in dashboards if d["name"] == chosen)
st.caption(f"From `{dash['workbook']}` · {len(dash.get('worksheets') or [])} tiles")

metrics = SPEC.get("metrics") or []
if metrics:
    with st.container(horizontal=True):
        for m in metrics[:4]:
            name = m["name"]
            live_failed = False
            if mode == "live":
                try:
                    df = sv.live_query(
                        sv.semantic_sql(SPEC, metrics=[name], dimensions=[])
                    )
                    value = df.iloc[0, 0] if not df.empty else "—"
                    st.metric(
                        name.replace("_", " "),
                        value,
                        border=True,
                        help=m.get("plain_english") or "",
                    )
                    continue
                except Exception as exc:  # noqa: BLE001
                    live_failed = True
                    st.caption(f"Live query failed · {exc}")
            kpi = sv.kpi_frame(SPEC, DATA, name)
            st.metric(
                name.replace("_", " "),
                kpi.get("value"),
                kpi.get("delta"),
                border=True,
                chart_data=DATA.get("series", {}).get(name),
                chart_type="line",
                help=(
                    ("Sample fallback · " if live_failed else "")
                    + (m.get("plain_english") or "")
                ),
            )

entries = sv.visual_entries(dash)
kpis = [e for e in entries if e[1] == "kpi"]
charts = [e for e in entries if e[1] in {"bar", "line", "scatter"}]
tables = [e for e in entries if e[1] == "table"]

if kpis:
    with st.container(horizontal=True):
        for name, _kind, key in kpis:
            df = sv.worksheet_frame(DATA, key)
            series = df["value"].tolist() if not df.empty and "value" in df.columns else None
            last = series[-1] if series else "—"
            delta = f"{series[-1] - series[-2]:+}" if series and len(series) >= 2 else None
            st.metric(name, last, delta, border=True, chart_data=series, chart_type="line")

if charts:
    cols = st.columns(2, gap="medium")
    for i, (name, kind, key) in enumerate(charts):
        with cols[i % 2], st.container(border=True):
            st.markdown(f"{sv.icon_for(kind)} **{name}**")
            st.caption("via SEMANTIC_VIEW")
            df = sv.worksheet_frame(DATA, key)
            if mode == "live":
                try:
                    df = sv.live_query(
                        sv.semantic_sql(
                            SPEC,
                            metrics=[metrics[0]["name"]] if metrics else ["1"],
                            dimensions=[],
                        )
                    )
                except Exception as exc:  # noqa: BLE001
                    st.caption(f"Live query failed · {exc}")
                    st.badge("Sample fallback", color="orange")
            sv.render_chart(df, kind)

for name, kind, key in tables[:1]:
    with st.container(border=True):
        st.markdown(f"{sv.icon_for(kind)} **{name}**")
        st.caption("via SEMANTIC_VIEW")
        df = sv.worksheet_frame(DATA, key)
        if mode == "live":
            try:
                df = sv.live_query(
                    sv.semantic_sql(
                        SPEC,
                        metrics=[metrics[0]["name"]] if metrics else ["1"],
                        dimensions=[],
                    )
                )
            except Exception as exc:  # noqa: BLE001
                st.caption(f"Live query failed · {exc}")
                st.badge("Sample fallback", color="orange")
        st.dataframe(df, hide_index=True, width="stretch")
'''
