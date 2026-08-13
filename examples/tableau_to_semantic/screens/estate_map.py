"""Screen 2 — Estate map (deterministic ``.twb`` parse → Graphviz)."""

from __future__ import annotations

import streamlit as st
from engine import state
from engine.estate_parse import build_estate_map
from engine.extract import load_schema, validate_payload
from engine.persist import render_step_actions
from engine.ui_common import require_cwd_files


def _shared_tables(estate: dict) -> set[str]:
    counts: dict[str, int] = {}
    for row in estate.get("workbook_usage") or []:
        for t in row.get("tables") or []:
            counts[str(t)] = counts.get(str(t), 0) + 1
    return {name for name, n in counts.items() if n >= 2}


def _to_dot(estate: dict) -> str:
    shared = _shared_tables(estate)
    lines = [
        "digraph estate {",
        "  rankdir=LR;",
        '  node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=10];',
        '  edge [fontname="Helvetica", fontsize=8];',
        '  graph [bgcolor="transparent"];',
    ]
    table_names = {str(t.get("name")) for t in (estate.get("tables") or []) if t.get("name")}
    for join in estate.get("joins") or []:
        table_names.add(str(join.get("left_table") or ""))
        table_names.add(str(join.get("right_table") or ""))
    table_names.discard("")

    for name in sorted(table_names):
        safe = name.replace('"', "")
        if name in shared:
            lines.append(
                f'  "{safe}" [fillcolor="#FFE08A", color="#B45309", penwidth=2, '
                f'label="{safe}\\n(shared)"];'
            )
        else:
            lines.append(f'  "{safe}" [fillcolor="#E8EEF5", color="#64748B"];')

    seen_edges: set[tuple[str, str]] = set()
    for join in estate.get("joins") or []:
        left = str(join.get("left_table") or "")
        right = str(join.get("right_table") or "")
        if not left or not right:
            continue
        edge = (left, right)
        if edge in seen_edges:
            continue
        seen_edges.add(edge)
        lc = str(join.get("left_column") or "")
        rc = str(join.get("right_column") or "")
        lines.append(f'  "{left}" -> "{right}" [label="{lc}={rc}", color="#94A3B8"];')

    lines.append("}")
    return "\n".join(lines)


def _render_estate(estate: dict) -> None:
    shared = _shared_tables(estate)
    st.markdown(
        f"**{len(estate.get('tables') or [])}** tables · "
        f"**{len(estate.get('joins') or [])}** joins · "
        f"**{len(shared)}** tables touched by more than one workbook "
        "(highlighted — that overlap is what a shared semantic view is for)."
    )

    left, right = st.columns([1.4, 1], gap="large")
    with left:
        try:
            st.graphviz_chart(_to_dot(estate), width="stretch")
        except Exception as exc:  # noqa: BLE001
            st.warning(f"Graphviz render failed ({exc}). Showing join table instead.")
            st.dataframe(estate.get("joins") or [], width="stretch", hide_index=True)
    with right:
        st.markdown("##### Workbook usage")
        usage = estate.get("workbook_usage") or []
        st.dataframe(
            [
                {
                    "workbook": u.get("workbook"),
                    "tables": len(u.get("tables") or []),
                    "worksheets": u.get("worksheets"),
                    "dashboards": u.get("dashboards"),
                }
                for u in usage
            ],
            width="stretch",
            hide_index=True,
        )
        if shared:
            st.markdown("##### Shared tables")
            st.write(", ".join(f"`{t}`" for t in sorted(shared)))


def run() -> None:
    st.markdown(
        "Map entities, joins, and which workbook touches what — "
        "**parsed from the `.twb` XML** (no agent). Shared tables are highlighted."
    )

    files = require_cwd_files()
    if not files:
        return

    estate = state.get_estate()
    run_clicked = render_step_actions(
        run_label="Map the estate",
        run_key="tts_map_estate",
        step="estate",
        payload=estate,
    )
    st.caption("Workspace · " + ", ".join(f"`{p.name}`" for p in files))

    if run_clicked:
        payload = build_estate_map(files)
        errors = validate_payload(payload, load_schema("estate_map.schema.json"))
        if errors:
            st.error("Deterministic extract failed schema validation:")
            for err in errors[:12]:
                st.caption(f"- {err}")
            with st.expander("Raw payload"):
                st.json(payload)
        else:
            state.set_estate(payload)
            st.toast(
                f"Mapped {len(payload.get('tables') or [])} tables · "
                f"{len(payload.get('joins') or [])} joins"
            )
            st.rerun()

    estate = state.get_estate()
    if estate:
        st.divider()
        st.subheader("Estate map")
        _render_estate(estate)
    else:
        st.caption("Click **Map the estate** to parse the workbooks.")


run()
