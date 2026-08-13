"""Screen 3 — KPI inventory (deterministic calculated-field parse → table)."""

from __future__ import annotations

import streamlit as st
from engine import state
from engine.extract import load_schema, validate_payload
from engine.kpi_parse import build_kpi_inventory
from engine.persist import render_step_actions
from engine.ui_common import require_cwd_files


def _render_metrics(payload: dict) -> None:
    metrics = list(payload.get("metrics") or [])
    metrics.sort(key=lambda m: (not bool(m.get("is_conflicting")), str(m.get("name") or "")))
    conflicts = sum(1 for m in metrics if m.get("is_conflicting"))
    shared = sum(1 for m in metrics if len(m.get("workbooks") or []) > 1)
    st.markdown(
        f"**{len(metrics)}** calculated fields · **{shared}** in more than one workbook · "
        f"**{conflicts}** with conflicting formulas. Conflicts sort first."
    )

    rows = [
        {
            "name": m.get("name"),
            "conflicting": bool(m.get("is_conflicting")),
            "workbooks": ", ".join(m.get("workbooks") or []),
            "plain_english": m.get("plain_english"),
            "definitions": len(m.get("definitions") or []),
        }
        for m in metrics
    ]
    st.dataframe(rows, width="stretch", hide_index=True)

    for m in metrics:
        if not m.get("is_conflicting") and len(m.get("workbooks") or []) < 2:
            continue
        title = str(m.get("name") or "metric")
        flag = " · conflict" if m.get("is_conflicting") else ""
        with st.expander(f"{title}{flag}", expanded=bool(m.get("is_conflicting"))):
            st.write(m.get("plain_english") or "")
            for d in m.get("definitions") or []:
                st.markdown(f"**{d.get('workbook')}** · aggregation `{d.get('aggregation')}`")
                st.code(str(d.get("formula") or ""), language="text")


def run() -> None:
    st.markdown(
        "Every calculated field, grouped by caption, with conflicts surfaced — "
        "**parsed from the `.twb` XML** (no agent). `plain_english` is a short "
        "deterministic note; arbitration still decides the canonical formula."
    )

    files = require_cwd_files()
    if not files:
        return

    payload = state.get_metrics()
    run_clicked = render_step_actions(
        run_label="Inventory KPIs",
        run_key="tts_map_kpi",
        step="kpi",
        payload=payload,
    )
    st.caption("Workspace · " + ", ".join(f"`{p.name}`" for p in files))

    if run_clicked:
        new_payload = build_kpi_inventory(files)
        errors = validate_payload(new_payload, load_schema("kpi_inventory.schema.json"))
        if errors:
            st.error("Deterministic extract failed schema validation:")
            for err in errors[:12]:
                st.caption(f"- {err}")
            with st.expander("Raw payload"):
                st.json(new_payload)
        else:
            state.set_metrics(new_payload)
            n = len(new_payload.get("metrics") or [])
            conflicts = sum(1 for m in new_payload["metrics"] if m.get("is_conflicting"))
            st.toast(f"Inventoried {n} fields · {conflicts} conflicts")
            st.rerun()

    payload = state.get_metrics()
    if payload:
        st.divider()
        st.subheader("KPI inventory")
        _render_metrics(payload)
    else:
        st.caption("Click **Inventory KPIs** to parse calculated fields.")


run()
