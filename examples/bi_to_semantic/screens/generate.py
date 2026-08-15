"""Screen 6 — Generate semantic view + RAP, then a Streamlit consumer app."""

from __future__ import annotations

from collections import Counter

import streamlit as st
from engine import state
from engine.bi_sources import list_bi_files
from engine.coco_jobs import (
    is_connected,
    open_copilot_for_job,
    queue_generate,
    queue_streamlit_app,
    set_preview_open,
)
from engine.dashboard_parse import list_dashboards
from engine.generate import (
    build_row_access_policy_sql,
    build_semantic_sql,
    build_semantic_yaml,
)
from engine.paths import OUT_DIR, WORKSPACE_DIR
from engine.streamlit_app_gen import (
    APP_DIRNAME_COCO,
    brief_is_saved,
    build_coco_prompt,
    build_spec,
    generated_app_exists,
    list_coco_markdown,
    load_brief,
    load_coco_markdown,
    prepare_coco_app,
    save_coco_markdown,
    semantic_view_sql,
    write_streamlit_app,
)

BRIEF_REFRESH_KEY = "tts_refresh_coco_brief"
CONNECT_HINT_KEY = "tts_coco_connect_hint"
MD_PILL_KEY = "tts_coco_md_file"
PREVIEW_VARIANT_KEY = "tts_preview_variant"
STEP_KEY = "tts_generate_step"
MODE_KEY = "tts_build_mode"
DASH_KEY = "tts_migrate_dash_pills"


def _store_key(base: str) -> str:
    return f"{base}__persist"


def _seed_widget(base: str, default):
    """Restore a stable widget key from persist (source of truth).

    Opening Copilot remounts Generate inside columns. persist_state keeps the
    widget, and persist wins if a remount still drops the value.
    """
    store = _store_key(base)
    if store not in st.session_state:
        for legacy in (f"{base}__rail", f"{base}__full", base):
            value = st.session_state.get(legacy)
            if value not in (None, ""):
                st.session_state[store] = value
                break
        else:
            st.session_state[store] = default
    st.session_state[base] = st.session_state[store]
    return base


def _md_body_key(name: str) -> str:
    return f"tts_coco_md_body__{name}"


def _selected_markdown(names: list[str]) -> str:
    current = st.session_state.get(MD_PILL_KEY)
    if current in names:
        return str(current)
    return "BRIEF.md" if "BRIEF.md" in names else names[0]


def _persist_on_change(base: str, widget_key: str):
    def _cb() -> None:
        st.session_state[_store_key(base)] = st.session_state.get(widget_key)

    return _cb


def _rap_target_table(estate: dict | None) -> str:
    names = [str(t.get("name")) for t in (estate or {}).get("tables") or [] if t.get("name")]
    for candidate in ("historical_events", "content", "users"):
        if candidate in names:
            return candidate
    return names[0] if names else "historical_events"


def _build_artifacts() -> dict[str, str]:
    estate = state.get_estate()
    metrics = state.metric_decisions()
    access = state.access_decisions()
    all_dec = state.get_decisions()
    yaml_body = build_semantic_yaml(estate, metrics, all_decisions=all_dec)
    return {
        "semantic_view.yaml": yaml_body,
        "semantic_view.sql": build_semantic_sql(yaml_body, decisions=all_dec),
        "row_access_policy.sql": build_row_access_policy_sql(
            access,
            all_decisions=all_dec,
            target_table=_rap_target_table(estate),
        ),
    }


def _write_prompt(artifacts: dict[str, str]) -> str:
    names = ", ".join(artifacts.keys())
    return f"""\
Write the generated Snowflake artifacts into the working directory.

Drafts are already under `_drafts/`. For each of: {names}
1. Read `_drafts/<filename>`
2. Write the exact same contents to `<filename>` at the cwd root (not under _drafts).

Do not invent new SQL. Do not skip the row access policy. Use the Write tool for each file.
After writing, Glob `*.sql` and `*.yaml` to confirm.
"""


def _go_streamlit() -> None:
    st.session_state[_store_key(STEP_KEY)] = "streamlit"
    st.rerun()


def _dash_labels(dashboards: list[dict]) -> dict[str, dict]:
    counts = Counter(str(d.get("name") or "") for d in dashboards)
    out: dict[str, dict] = {}
    for dash in dashboards:
        name = str(dash.get("name") or dash.get("id"))
        label = f"{name} · {dash.get('workbook')}" if counts[name] > 1 else name
        out[label] = dash
    return out


def _app_exists(variant: str) -> bool:
    return generated_app_exists(OUT_DIR, variant=variant)


def _render_objects(artifacts: dict[str, str]) -> None:
    st.markdown(
        "One definition. One policy. Below the BI layer — every consumer sees the same rule."
    )
    tab_yaml, tab_sv, tab_rap = st.tabs(
        ["semantic_view.yaml", "semantic_view.sql", "row_access_policy.sql"]
    )
    with tab_yaml:
        st.code(artifacts["semantic_view.yaml"], language="yaml")
    with tab_sv:
        st.code(artifacts["semantic_view.sql"], language="sql")
    with tab_rap:
        st.code(artifacts["row_access_policy.sql"], language="sql")

    disabled = not is_connected()
    with st.container(horizontal=True):
        if st.button(
            "Write with Copilot",
            type="primary",
            icon=":material/approval:",
            key="tts_queue_generate",
            disabled=disabled,
        ):
            drafts = OUT_DIR / "_drafts"
            drafts.mkdir(parents=True, exist_ok=True)
            for name, body in artifacts.items():
                (drafts / name).write_text(body, encoding="utf-8")
            queue_generate(_write_prompt(artifacts))
            st.rerun()
        if st.button(
            "Continue to Streamlit",
            icon=":material/web:",
            key="tts_to_streamlit",
        ):
            _go_streamlit()
    if disabled:
        st.caption("Open Copilot → Connection → Connect, then write.")

    written = sorted(OUT_DIR.glob("*.sql")) + sorted(OUT_DIR.glob("*.yaml"))
    if written:
        st.caption("On disk · " + ", ".join(f"`{p.name}`" for p in written))


def _render_python_builder(*, chosen: list, spec: dict, yaml_body: str) -> None:
    st.markdown("### Python")
    st.caption("Faster mode. Instant, known-good consumer of the view.")
    if st.button(
        "Build with python",
        type="primary",
        icon=":material/code:",
        key="tts_gen_streamlit",
        disabled=not chosen,
        width="stretch",
    ):
        path = write_streamlit_app(OUT_DIR, spec=spec, yaml_body=yaml_body)
        st.session_state[PREVIEW_VARIANT_KEY] = "deterministic"
        set_preview_open(True)
        st.toast(f"Wrote `{path.name}/`")
        st.rerun()
    if _app_exists("deterministic"):
        st.badge("Ready", icon=":material/check_circle:", color="green")


def _render_coco_builder(
    *,
    chosen: list,
    spec: dict,
    yaml_body: str,
    prompt: str,
) -> None:
    st.markdown("### Build with CoCo")
    st.caption("Enhanced mode. CoCo authors a different UI. Edit the brief, save, then generate.")
    if st.button(
        "Prepare brief",
        icon=":material/description:",
        key="tts_prepare_brief",
        disabled=not chosen,
    ):
        prepare_coco_app(OUT_DIR, spec=spec, yaml_body=yaml_body)
        save_coco_markdown(OUT_DIR, "BRIEF.md", prompt)
        st.session_state[BRIEF_REFRESH_KEY] = True
        st.toast("Brief refreshed from the selected dashboards")
        st.rerun()

    md_names = list_coco_markdown(OUT_DIR)
    if not md_names:
        md_names = ["BRIEF.md"]
    if MD_PILL_KEY not in st.session_state or st.session_state[MD_PILL_KEY] not in md_names:
        st.session_state[MD_PILL_KEY] = "BRIEF.md" if "BRIEF.md" in md_names else md_names[0]
    if len(md_names) > 1:
        st.pills(
            "Markdown",
            md_names,
            key=MD_PILL_KEY,
            persist_state="session",
            label_visibility="collapsed",
        )
    selected = _selected_markdown(md_names)
    body_key = _md_body_key(selected)
    disk = load_coco_markdown(OUT_DIR, selected)
    refresh = st.session_state.pop(BRIEF_REFRESH_KEY, False)
    current = str(st.session_state.get(body_key) or "")
    stale_wall = selected == "BRIEF.md" and (
        "visual, visual" in current
        or (disk or "").count("visual,") >= 3
        or (
            "2-column chart grid" in current
            and "slicer" not in current.lower()
        )
    )
    if stale_wall:
        st.session_state[body_key] = prompt
    elif selected == "BRIEF.md" and refresh:
        st.session_state[body_key] = disk or prompt
    elif not current.strip():
        st.session_state[body_key] = disk or (prompt if selected == "BRIEF.md" else "")
    st.text_area(
        selected,
        height=420,
        key=body_key,
        help="Save before generating. BRIEF.md is the CoCo prompt.",
        label_visibility="collapsed",
    )
    editor = str(st.session_state.get(body_key) or "")
    file_saved = bool(disk) and disk.strip() == editor.strip()
    brief_editor = editor if selected == "BRIEF.md" else (load_brief(OUT_DIR) or "")
    brief_saved = brief_is_saved(OUT_DIR, brief_editor)
    save_label = "Save Brief" if selected == "BRIEF.md" else f"Save {selected}"
    if st.button(
        save_label,
        type="primary" if editor.strip() and not file_saved else "secondary",
        icon=":material/save:",
        key="tts_save_brief",
        disabled=not chosen or not editor.strip(),
        width="stretch",
    ):
        prepare_coco_app(OUT_DIR, spec=spec, yaml_body=yaml_body)
        path = save_coco_markdown(OUT_DIR, selected, editor)
        st.toast(f"Saved `{path.parent.name}/{path.name}`")
        st.rerun()
    coco_disabled = (not chosen) or (not brief_saved)
    if st.button(
        "Generate with CoCo",
        type="primary",
        icon=":material/psychology:",
        key="tts_gen_streamlit_coco",
        disabled=coco_disabled,
        width="stretch",
    ):
        open_copilot_for_job()
        if not is_connected():
            st.session_state[CONNECT_HINT_KEY] = True
            st.rerun()
        prepare_coco_app(OUT_DIR, spec=spec, yaml_body=yaml_body)
        if selected == "BRIEF.md":
            save_coco_markdown(OUT_DIR, "BRIEF.md", editor)
            queued = editor
        else:
            queued = load_brief(OUT_DIR) or prompt
        queue_streamlit_app(queued)
        st.session_state.pop(CONNECT_HINT_KEY, None)
        st.session_state[PREVIEW_VARIANT_KEY] = "coco"
        st.toast(f"Queued · `{APP_DIRNAME_COCO}/`")
        st.rerun()
    if st.session_state.get(CONNECT_HINT_KEY) and not is_connected():
        st.warning(
            "Connect Copilot in the right rail, then click **Generate with CoCo** again.",
            icon=":material/link:",
        )
    elif not is_connected():
        st.caption("Generate opens Copilot — connect there to run the job.")
    elif not brief_saved:
        st.caption("Save BRIEF.md to enable Generate with CoCo.")
    else:
        st.caption(f"Saved · `{APP_DIRNAME_COCO}/{selected}`")
    if _app_exists("coco"):
        st.badge("Ready", icon=":material/psychology:", color="green")


def _render_streamlit(artifacts: dict[str, str]) -> None:
    files = list_bi_files(WORKSPACE_DIR)
    dashboards = list_dashboards(files)
    if not dashboards:
        st.warning("No dashboards / report pages found. Load sources on **1 · Load**.")
        return

    label_map = _dash_labels(dashboards)
    labels = list(label_map.keys())
    stored_dash = st.session_state.get(_store_key(DASH_KEY))
    if isinstance(stored_dash, (list, tuple)):
        dash_default = [name for name in stored_dash if name in labels] or labels
        st.session_state[_store_key(DASH_KEY)] = dash_default
    else:
        dash_default = labels
    dash_key = _seed_widget(DASH_KEY, dash_default)
    picked = st.pills(
        "Dashboards",
        labels,
        selection_mode="multi",
        key=dash_key,
        on_change=_persist_on_change(DASH_KEY, dash_key),
        persist_state="session",
        label_visibility="collapsed",
    )
    chosen = [label_map[name] for name in (picked or [])]
    spec = build_spec(
        dashboards=chosen,
        metric_decisions=state.metric_decisions(),
        all_decisions=state.get_decisions(),
        estate=state.get_estate(),
    )
    n_sheets = sum(len(d.get("worksheets") or []) for d in chosen)
    st.caption(f"{len(chosen)} dashboards · {n_sheets} tiles · `{spec.get('semantic_view')}`")

    yaml_body = artifacts["semantic_view.yaml"]
    prompt = build_coco_prompt(spec, dest_name=APP_DIRNAME_COCO)

    build_mode = st.session_state.get(MODE_KEY) or st.session_state.get(
        _store_key(MODE_KEY), "python"
    )

    with st.container(border=True):
        if build_mode == "coco":
            _render_coco_builder(
                chosen=chosen,
                spec=spec,
                yaml_body=yaml_body,
                prompt=prompt,
            )
        else:
            _render_python_builder(chosen=chosen, spec=spec, yaml_body=yaml_body)

    with st.expander("Semantic view contract", expanded=False):
        st.code(
            semantic_view_sql(
                spec,
                metrics=[m["name"] for m in spec.get("metrics") or []],
                dimensions=[],
            ),
            language="sql",
        )


def _generate_step_control(widget_key: str) -> str:
    value = st.segmented_control(
        "Generate",
        options=["objects", "streamlit"],
        format_func=lambda s: "1 · Semantic view + RAP" if s == "objects" else "2 · Streamlit app",
        key=widget_key,
        on_change=_persist_on_change(STEP_KEY, widget_key),
        persist_state="session",
        label_visibility="collapsed",
    )
    return value or st.session_state.get(_store_key(STEP_KEY), "objects")


def run() -> None:
    decisions = state.get_decisions()
    if not decisions:
        st.warning("No arbitration decisions yet — go to **Arbitration** first.")
        return

    artifacts = _build_artifacts()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    step_key = _seed_widget(STEP_KEY, "objects")
    mode_key = _seed_widget(MODE_KEY, "python")

    with st.container(horizontal=True, vertical_alignment="bottom"):
        step = _generate_step_control(step_key)
        if step == "streamlit":
            st.segmented_control(
                "How to build",
                options=["python", "coco"],
                format_func=lambda m: "Python · faster" if m == "python" else "CoCo · enhanced",
                key=mode_key,
                on_change=_persist_on_change(MODE_KEY, mode_key),
                persist_state="session",
                label_visibility="collapsed",
            )

    if step == "streamlit":
        _render_streamlit(artifacts)
    else:
        _render_objects(artifacts)


run()
