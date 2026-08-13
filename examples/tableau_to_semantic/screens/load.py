"""Screen 1 — Load Tableau workbooks into the agent cwd."""

from __future__ import annotations

import shutil

import streamlit as st
from engine import state
from engine.extract import list_twb_files
from engine.paths import FIXTURES_DIR, MIT_WORKBOOKS, WORKSPACE_DIR
from engine.ui_common import optional_secret

import streamlit_coco as st_coco


def run() -> None:
    st.markdown(
        "Drop `.twb` / `.twbx` files, or load the bundled **MIT Tableau Server** pack. "
        "Files land in the agent's working directory. Open **Copilot** (header) once "
        "to connect — later screens reuse that same streamed session."
    )

    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    connection = optional_secret("snowflake_connection")

    # Lightweight options so cwd_uploader has a target even before CoCo starts.
    opts = st_coco.CocoOptions(
        connection=connection,
        cwd=str(WORKSPACE_DIR),
        allowed_tools=["Read", "Glob", "Grep"],
    )

    st.subheader("Bundled fixture pack")
    st.caption(
        "Demo pack: **`ts_content`** + **`ts_users`** (project-leader branch present "
        "vs dropped) from "
        "[tableau/community-tableau-server-insights]"
        "(https://github.com/tableau/community-tableau-server-insights) "
        "— **MIT © Tableau**. Full set of four remains in `examples/tableau_legacy/`."
    )

    if st.button("Use MIT Tableau Server pack", type="primary", key="tts_load_mit"):
        copied: list[str] = []
        missing: list[str] = []
        # Drop non-demo workbooks from a previous full-pack load.
        for stale in WORKSPACE_DIR.glob("ts_*.twb"):
            if stale.name not in MIT_WORKBOOKS:
                stale.unlink(missing_ok=True)
        for name in MIT_WORKBOOKS:
            src = FIXTURES_DIR / name
            if not src.is_file():
                missing.append(name)
                continue
            dest = WORKSPACE_DIR / name
            shutil.copy2(src, dest)
            copied.append(name)
        if copied:
            state.set_cwd_ready(True)
            st.success("Copied · " + ", ".join(f"`{n}`" for n in copied))
        if missing:
            st.error("Missing fixtures · " + ", ".join(f"`{n}`" for n in missing))

    st.subheader("Upload")
    st_coco.cwd_uploader(
        opts,
        label="Upload `.twb` / `.twbx` into the workspace",
        overwrite="replace",
        file_type=["twb", "twbx", "xml"],
        key="tts_cwd_uploader",
        show_inventory=True,
        # Put uploads at cwd root via empty-ish subdir — library defaults to `_uploads`.
        # Keep `_uploads` so inventory works; extract prompts Glob both.
    )

    files = list_twb_files(WORKSPACE_DIR)
    st.subheader("Workspace inventory")
    st.caption(f"`{WORKSPACE_DIR}`")
    if not files:
        st.info("No workbooks loaded yet.")
        state.set_cwd_ready(False)
        return

    state.set_cwd_ready(True)

    if st.button(
        "Next: Map the estate",
        type="primary",
        icon=":material/navigate_next:",
        key="tts_load_next",
    ):
        st.switch_page("screens/estate_map.py")
    st.divider()

    rows = [
        {
            "file": p.name,
            "bytes": p.stat().st_size,
            "path": str(p.relative_to(WORKSPACE_DIR)),
        }
        for p in files
    ]
    st.dataframe(rows, width="stretch", hide_index=True)

    # Peek: show a snippet of the first file as XML (demo beat 1)
    with st.expander("Peek at raw XML (first workbook)", expanded=False):
        sample = files[0]
        text = sample.read_text(encoding="utf-8", errors="replace")
        st.code(text[:1200] + ("\n…" if len(text) > 1200 else ""), language="xml")
        st.caption(f"`{sample.name}` — this is what nobody opens.")


run()
