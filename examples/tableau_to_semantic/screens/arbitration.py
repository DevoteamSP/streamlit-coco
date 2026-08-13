"""Screen 5 — Arbitration (request_input judgement calls + provenance log)."""

from __future__ import annotations

import re

import streamlit as st
from engine import state
from engine.persist import render_save_then_next

import streamlit_coco as st_coco


def _safe_key(prefix: str, subject: str) -> str:
    slug = re.sub(r"[^\w]+", "_", subject.strip())[:48].strip("_") or "item"
    return f"{prefix}_{slug}"


def _next_metric() -> dict | None:
    payload = state.get_metrics()
    if not payload:
        return None
    decided = state.decided_metric_names()
    metrics = list(payload.get("metrics") or [])
    # Prefer conflicts first
    metrics.sort(key=lambda m: (not bool(m.get("is_conflicting")), str(m.get("name") or "")))
    for m in metrics:
        name = str(m.get("name") or "")
        if not name or name in decided:
            continue
        if m.get("is_conflicting") or len(m.get("workbooks") or []) > 1:
            return m
    return None


def _next_divergence() -> dict | None:
    payload = state.get_access()
    if not payload:
        return None
    decided = state.decided_access_subjects()
    for d in payload.get("divergences") or []:
        subject = str(d.get("branch") or "")
        if subject and subject not in decided:
            return d
    return None


def _render_decision_log() -> None:
    decisions = state.get_decisions()
    st.subheader("Decision log")
    if not decisions:
        st.caption("No decisions yet. Downstream artifacts will cite ids from this list.")
        return
    st.dataframe(
        [
            {
                "id": d.get("id"),
                "kind": d.get("kind"),
                "subject": d.get("subject"),
                "action": d.get("action"),
                "metric_name": d.get("metric_name"),
                "rationale": (d.get("rationale") or "")[:80],
            }
            for d in decisions
        ],
        width="stretch",
        hide_index=True,
    )
    if st.button("Clear all decisions", key="tts_clear_decisions"):
        state.clear_decisions()
        st.rerun()


def _arbitrate_metric(metric: dict) -> None:
    name = str(metric.get("name") or "metric")
    defs = metric.get("definitions") or []
    options = []
    for d in defs:
        wb = d.get("workbook")
        formula = str(d.get("formula") or "")
        options.append(f"{wb} :: {formula[:120]}")
    options.append("custom")

    st.markdown(f"### Metric · `{name}`")
    if metric.get("is_conflicting"):
        st.warning("Conflicting formulas across workbooks — pick the canonical one.")
    st.write(metric.get("plain_english") or "")

    for d in defs:
        st.markdown(f"**{d.get('workbook')}**")
        st.code(str(d.get("formula") or ""), language="text")

    decision = st_coco.request_input(
        "Arbitrate this metric — choose a canonical formula, name it, confirm the definition.",
        key=_safe_key("tts_metric", name),
        schema=[
            {
                "name": "formula_choice",
                "label": "Canonical formula source",
                "type": "select",
                "options": options or ["custom"],
            },
            {
                "name": "canonical_formula",
                "label": "Formula (edit if custom / refine)",
                "type": "textarea",
                "default": str((defs[0] or {}).get("formula") or "") if defs else "",
            },
            {
                "name": "metric_name",
                "label": "Canonical metric name",
                "type": "text",
                "default": name,
            },
            {
                "name": "plain_english",
                "label": "Plain-English definition",
                "type": "textarea",
                "default": str(metric.get("plain_english") or ""),
            },
            {
                "name": "action",
                "label": "Action",
                "type": "select",
                "options": ["keep", "drop"],
            },
            {
                "name": "rationale",
                "label": "Why",
                "type": "textarea",
                "required": False,
            },
        ],
        submit_label="Record decision",
    )
    if decision and isinstance(decision, dict):
        formula = str(decision.get("canonical_formula") or "")
        choice = str(decision.get("formula_choice") or "")
        if choice != "custom" and " :: " in choice and not formula.strip():
            formula = choice.split(" :: ", 1)[1]
        state.add_decision(
            "metric",
            name,
            {
                "action": decision.get("action") or "keep",
                "metric_name": decision.get("metric_name") or name,
                "canonical_formula": formula or choice,
                "plain_english": decision.get("plain_english") or "",
                "rationale": decision.get("rationale") or "",
                "formula_choice": choice,
            },
        )
        st.success(f"Recorded metric decision for `{name}`.")
        st.rerun()


def _arbitrate_access(div: dict) -> None:
    branch = str(div.get("branch") or "branch")
    st.markdown(f"### Access branch · `{branch}`")
    st.write(div.get("consequence") or "")
    present = ", ".join(div.get("present_in") or [])
    absent = ", ".join(div.get("absent_from") or [])
    st.caption(f"Present in: {present} · Absent from: {absent}")

    decision = st_coco.request_input(
        "Keep, drop, or merge this access branch — and say why.",
        key=_safe_key("tts_access", branch),
        schema=[
            {
                "name": "action",
                "label": "Action",
                "type": "select",
                "options": ["keep", "drop", "merge"],
            },
            {
                "name": "grants_to",
                "label": "Grants to (role / persona)",
                "type": "text",
                "default": branch,
            },
            {
                "name": "rationale",
                "label": "Why",
                "type": "textarea",
            },
        ],
        submit_label="Record decision",
    )
    if decision and isinstance(decision, dict):
        state.add_decision(
            "access_branch",
            branch,
            {
                "action": decision.get("action") or "keep",
                "grants_to": decision.get("grants_to") or branch,
                "rationale": decision.get("rationale") or "",
                "consequence": div.get("consequence") or "",
                "present_in": div.get("present_in") or [],
                "absent_from": div.get("absent_from") or [],
            },
        )
        st.success(f"Recorded access decision for `{branch}`.")
        st.rerun()


def run() -> None:
    st.markdown(
        "The human decides. One metric at a time, one access branch at a time. "
        "Every downstream artifact traces back to a decision recorded here."
    )

    if not state.get_metrics() and not state.get_access():
        st.warning("Run KPI inventory and access comparator first.")
        _render_decision_log()
        return

    decisions = state.get_decisions()
    left, right = st.columns(2, gap="small")
    with left:
        st.caption("Record decisions below, then save.")
    with right:
        # Always show Save — grayed until at least one decision exists.
        render_save_then_next("decisions", decisions or [])
    st.divider()

    tab_m, tab_a = st.tabs(["Metrics", "Access branches"])

    with tab_m:
        metric = _next_metric()
        if metric is None:
            if not state.get_metrics():
                st.info("No KPI inventory yet.")
            else:
                st.success("All conflicting / shared metrics have a decision.")
        else:
            _arbitrate_metric(metric)

    with tab_a:
        div = _next_divergence()
        if div is None:
            if not state.get_access():
                st.info("No access comparison yet.")
            else:
                st.success("All divergences have a decision.")
        else:
            _arbitrate_access(div)

    st.divider()
    _render_decision_log()


run()
