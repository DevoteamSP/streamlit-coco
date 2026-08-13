"""Screen 4 — Access-rule comparator (queue job → shared Copilot → grid)."""

from __future__ import annotations

import streamlit as st
from engine import state
from engine.coco_jobs import is_connected, queue_access_rules
from engine.persist import render_step_actions
from engine.ui_common import require_cwd_files

_CSS = """
<style>
.tts-access-grid { display: grid; gap: 0.75rem; margin: 0.5rem 0 1rem; }
.tts-access-grid.cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.tts-access-grid.cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.tts-access-grid.cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.tts-access-col-title {
  font-weight: 600; font-size: 0.95rem; margin-bottom: 0.35rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}
.tts-branch {
  border: 1px solid #CBD5E1; border-radius: 6px; padding: 0.55rem 0.65rem;
  margin-bottom: 0.45rem; font-size: 0.82rem; line-height: 1.35;
  background: #F8FAFC; color: #334155;
}
.tts-branch.common {
  opacity: 0.55; background: #F1F5F9; border-color: #E2E8F0; color: #64748B;
}
.tts-branch.divergent {
  border-color: #DC2626; background: #FEF2F2; color: #7F1D1D; opacity: 1;
}
.tts-branch .grants { font-weight: 600; display: block; margin-bottom: 0.15rem; }
.tts-consequence {
  border-left: 3px solid #DC2626; padding: 0.4rem 0.75rem; margin: 0.35rem 0;
  background: #FFF7ED; color: #9A3412;
}
</style>
"""


def _normalize_branch_key(branch: dict) -> str:
    return str(branch.get("grants_to") or branch.get("condition") or "").strip().lower()


def _render_access(payload: dict) -> None:
    st.markdown(_CSS, unsafe_allow_html=True)

    rules = list(payload.get("access_rules") or [])
    divergences = list(payload.get("divergences") or [])

    all_keys: list[set[str]] = []
    for rule in rules:
        keys = {_normalize_branch_key(b) for b in (rule.get("branches") or [])}
        keys.discard("")
        all_keys.append(keys)
    common: set[str] = set.intersection(*all_keys) if all_keys else set()

    n = max(len(rules), 1)
    cols_class = f"cols-{min(n, 4)}"
    parts = [f'<div class="tts-access-grid {cols_class}">']
    for rule in rules:
        wb = str(rule.get("workbook") or "?")
        parts.append("<div>")
        parts.append(f'<div class="tts-access-col-title">{wb}</div>')
        for branch in rule.get("branches") or []:
            key = _normalize_branch_key(branch)
            klass = "common" if key in common and len(rules) > 1 else "divergent"
            if key in common:
                klass = "common"
            elif len(rules) > 1:
                klass = "divergent"
            grants = str(branch.get("grants_to") or "")
            cond = str(branch.get("condition") or "")
            cols = ", ".join(branch.get("source_columns") or [])
            parts.append(
                f'<div class="tts-branch {klass}">'
                f'<span class="grants">{grants}</span>'
                f"<div>{cond}</div>"
                f"<div style='opacity:0.75;margin-top:0.2rem'><code>{cols}</code></div>"
                f"</div>"
            )
        plain = str(rule.get("plain_english") or "")
        if plain:
            parts.append(f"<p style='font-size:0.8rem;color:#64748B'>{plain}</p>")
        parts.append("</div>")
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)

    st.subheader("Divergences")
    if not divergences:
        st.warning("No divergences in the payload — re-run comparison.")
        return
    for d in divergences:
        present = ", ".join(d.get("present_in") or [])
        absent = ", ".join(d.get("absent_from") or [])
        st.markdown(f"**{d.get('branch')}** — present in `{present}` · absent from `{absent}`")
        st.markdown(
            f'<div class="tts-consequence">{d.get("consequence") or ""}</div>',
            unsafe_allow_html=True,
        )


def run() -> None:
    st.markdown(
        "Two dashboards. Two different answers to *who can see this row* — "
        "`ts_content` keeps the project-leader branch; `ts_users` dropped it. "
        "CoCo streams in the Copilot rail; this pane shows the comparator."
    )

    files = require_cwd_files()
    if not files:
        return

    payload = state.get_access()
    disabled = not is_connected()
    run_clicked = render_step_actions(
        run_label="Compare access rules",
        run_key="tts_queue_access",
        step="access",
        payload=payload,
        run_disabled=disabled,
    )
    if disabled:
        st.caption("Open **Copilot** → **Connection** → **Connect**, then compare.")

    if run_clicked:
        queue_access_rules()
        st.rerun()

    payload = state.get_access()
    if payload:
        st.divider()
        st.subheader("User Filter — side by side")
        _render_access(payload)
    else:
        st.caption("Results appear here after **Compare access rules** finishes in Copilot.")


run()
