"""Persist step payloads under ``out/`` and navigate to the next screen."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st

from engine.paths import OUT_DIR

# step id → (filename, next page path, button label)
STEP_NEXT: dict[str, tuple[str, str, str]] = {
    "estate": (
        "estate_map.json",
        "screens/kpi_inventory.py",
        "Save then Inventory KPIs",
    ),
    "kpi": (
        "kpi_inventory.json",
        "screens/access_rules.py",
        "Save then Compare access rules",
    ),
    "access": (
        "access_rules.json",
        "screens/arbitration.py",
        "Save then Arbitrate",
    ),
    "decisions": (
        "decisions.json",
        "screens/generate.py",
        "Save then Generate",
    ),
}


def artifact_path(step: str) -> Path:
    filename, _, _ = STEP_NEXT[step]
    return OUT_DIR / filename


def save_payload(step: str, payload: Any) -> Path:
    """Write JSON under ``out/``; returns the path written."""
    if step not in STEP_NEXT:
        raise KeyError(f"Unknown step: {step}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = artifact_path(step)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def load_payload(step: str) -> Any | None:
    path = artifact_path(step)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def step_has_output(step: str, payload: Any) -> bool:
    """True when this step has been executed and produced usable output."""
    if payload is None:
        return False
    if step == "estate":
        return bool(isinstance(payload, dict) and (payload.get("tables") or payload.get("joins")))
    if step == "kpi":
        return bool(isinstance(payload, dict) and payload.get("metrics"))
    if step == "access":
        return bool(isinstance(payload, dict) and payload.get("access_rules"))
    if step == "decisions":
        return isinstance(payload, list) and len(payload) > 0
    return bool(payload)


def render_save_then_next(step: str, payload: Any, *, key: str | None = None) -> None:
    """Persist this step's output, then switch page (single button; grayed if not ready)."""
    if step not in STEP_NEXT:
        return
    _, next_page, label = STEP_NEXT[step]
    btn_key = key or f"tts_save_then_{step}"
    path = artifact_path(step)
    ready = step_has_output(step, payload)
    exists = path.is_file()
    with st.container(horizontal=True, vertical_alignment="center"):
        clicked = st.button(
            label,
            type="primary" if ready else "secondary",
            icon=":material/navigate_next:",
            key=btn_key,
            disabled=not ready,
            help=None if ready else "Execute this step first",
        )
        if clicked and ready:
            written = save_payload(step, payload)
            st.toast(f"Saved `{written.name}`")
            st.switch_page(next_page)
        if ready:
            st.caption(f"`out/{path.name}`" + (" · saved" if exists else " · not saved yet"))
        else:
            st.caption("Save disabled · run the step first")


def render_step_actions(
    *,
    run_label: str,
    run_key: str,
    step: str,
    payload: Any | None,
    run_disabled: bool = False,
) -> bool:
    """Top bar: run | Save then next — side by side. Returns True if run clicked."""
    _, next_page, save_label = STEP_NEXT[step]
    path = artifact_path(step)
    ready = step_has_output(step, payload)
    left, right = st.columns(2, gap="small")
    with left:
        run_clicked = st.button(
            run_label,
            type="primary" if not ready else "secondary",
            key=run_key,
            disabled=run_disabled,
            width="stretch",
        )
    with right:
        save_clicked = st.button(
            save_label,
            type="primary" if ready else "secondary",
            icon=":material/navigate_next:",
            key=f"tts_save_then_{step}",
            disabled=not ready,
            width="stretch",
            help=None if ready else "Execute this step first",
        )
        if ready:
            exists = path.is_file()
            st.caption(f"`out/{path.name}`" + (" · saved" if exists else " · not saved yet"))
        else:
            st.caption("Save disabled · run the step first")
        if save_clicked and ready:
            written = save_payload(step, payload)
            st.toast(f"Saved `{written.name}`")
            st.switch_page(next_page)
    return run_clicked
