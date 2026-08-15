"""Screen 1 — Load Tableau and/or Power BI sources into the agent cwd."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

import streamlit as st
from engine import state
from engine.bi_sources import list_bi_files, source_kind
from engine.paths import (
    MIT_WORKBOOKS,
    POWERBI_FIXTURES_DIR,
    POWERBI_OPTIONAL,
    POWERBI_PACK,
    TABLEAU_FIXTURES_DIR,
    WORKSPACE_DIR,
)
from engine.powerbi_parse import peek_text as peek_powerbi
from engine.ui_common import optional_secret

import streamlit_coco as st_coco

_KIND_UI = {
    "tableau": {
        "icon": "https://api.iconify.design/simple-icons:tableau.svg?color=%23E97627",
        "label": "Tableau",
        "color": "blue",
    },
    "powerbi": {
        "icon": "https://api.iconify.design/simple-icons:powerbi.svg?color=%23F2C811",
        "label": "Power BI",
        "color": "orange",
    },
}

_PACK_BLURBS = {
    "ts_content.twb": "Project-leader User Filter present.",
    "ts_users.twb": "Project-leader branch dropped.",
    "Customer Profitability Sample (auto).pbix": "Fact / Scenario / Date — one contract.",
    "Corporate Spend.pbix": "Same table names; columns do not agree.",
    "Human Resources Sample PBIX.pbix": "Optional MIT sample (fetched locally).",
    "Employee Hiring and History.pbix": "Optional MIT sample (fetched locally).",
}


def _copy_tableau_pack() -> tuple[list[str], list[str]]:
    copied: list[str] = []
    missing: list[str] = []
    for stale in WORKSPACE_DIR.glob("ts_*.twb"):
        if stale.name not in MIT_WORKBOOKS:
            stale.unlink(missing_ok=True)
    for name in MIT_WORKBOOKS:
        src = TABLEAU_FIXTURES_DIR / name
        if not src.is_file():
            missing.append(name)
            continue
        dest = WORKSPACE_DIR / name
        shutil.copy2(src, dest)
        copied.append(name)
    return copied, missing


def _copy_powerbi_pack() -> tuple[list[str], list[str]]:
    copied: list[str] = []
    missing: list[str] = []
    names = list(POWERBI_PACK)
    for extra in POWERBI_OPTIONAL:
        if (POWERBI_FIXTURES_DIR / extra).is_file():
            names.append(extra)
    for stale in WORKSPACE_DIR.glob("*.pbix"):
        if stale.name not in names:
            stale.unlink(missing_ok=True)
    for child in list(WORKSPACE_DIR.iterdir()) if WORKSPACE_DIR.is_dir() else []:
        if child.is_dir() and child.name.startswith("ops_"):
            shutil.rmtree(child)
    for name in names:
        src = POWERBI_FIXTURES_DIR / name
        if not src.is_file():
            missing.append(name)
            continue
        dest = WORKSPACE_DIR / name
        shutil.copy2(src, dest)
        copied.append(name)
    return copied, missing


def _tableau_pack_paths() -> list[Path]:
    return [TABLEAU_FIXTURES_DIR / name for name in MIT_WORKBOOKS]


def _powerbi_pack_paths() -> list[Path]:
    names = list(POWERBI_PACK)
    for extra in POWERBI_OPTIONAL:
        if (POWERBI_FIXTURES_DIR / extra).is_file():
            names.append(extra)
    return [POWERBI_FIXTURES_DIR / name for name in names]


def _copy_pack(copy_fn) -> None:
    copied, missing = copy_fn()
    if copied:
        state.set_cwd_ready(True)
        st.toast("Copied · " + ", ".join(copied))
    if missing:
        st.error("Missing fixtures · " + ", ".join(f"`{n}`" for n in missing))
    if copied:
        st.rerun()


def _pack_file_card(path: Path) -> None:
    kind = source_kind(path) or (
        "tableau" if path.suffix.lower() in {".twb", ".twbx"} else "powerbi"
    )
    ui = _KIND_UI.get(kind, _KIND_UI["tableau"])
    with st.container(border=True):
        st.image(ui["icon"], width=28)
        st.markdown(f"**{path.stem}**")
        with st.container(horizontal=True, gap="small"):
            st.badge(ui["label"], color=ui["color"])
            st.badge(path.suffix.lstrip(".").upper() or "FILE", color="gray")
        if path.is_file():
            st.caption(_human_size(path.stat().st_size))
            blurb = _PACK_BLURBS.get(path.name)
            if blurb:
                st.caption(blurb)
        else:
            st.badge("Missing", color="red")


def _mit_pack_popover(
    *,
    label: str,
    key: str,
    paths: list[Path],
    copy_fn,
) -> None:
    with st.popover(
        label,
        icon=":material/download:",
        type="primary",
        width="stretch",
        key=key,
    ):
        st.caption("These files will be copied into the workspace.")
        for start in range(0, len(paths), 2):
            chunk = paths[start : start + 2]
            cols = st.columns(len(chunk), gap="small")
            for col, path in zip(cols, chunk):
                with col:
                    _pack_file_card(path)
        if st.button(
            "Copy into workspace",
            type="primary",
            icon=":material/download:",
            width="stretch",
            key=f"{key}_copy",
        ):
            _copy_pack(copy_fn)


def _human_size(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n / (1024 * 1024):.1f} MB"


def _source_bytes(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    if path.is_dir():
        return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    return 0


def _remove_source(path: Path) -> None:
    root = WORKSPACE_DIR.resolve()
    resolved = path.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"refusing to delete outside workspace: {path}")
    if resolved.is_dir():
        shutil.rmtree(resolved)
    elif resolved.is_file():
        resolved.unlink(missing_ok=True)


def _source_card(path: Path) -> None:
    kind = source_kind(path) or "tableau"
    ui = _KIND_UI.get(kind, _KIND_UI["tableau"])
    size = _source_bytes(path)
    mtime = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    rel = path.relative_to(WORKSPACE_DIR)
    title = path.stem if path.is_file() else path.name
    with st.container(border=True, height="stretch"):
        with st.container(horizontal=True, vertical_alignment="center"):
            st.image(ui["icon"], width=36)
            st.markdown(f"**{title}**")
        with st.container(horizontal=True, gap="small"):
            st.badge(ui["label"], color=ui["color"])
            if path.is_file():
                st.badge(path.suffix.lstrip(".").upper(), color="gray")
            else:
                st.badge("PBIP folder", color="gray")
        bits = [_human_size(size), f"updated {mtime}"]
        if path.is_dir():
            n_tmdl = sum(1 for _ in path.rglob("*.tmdl"))
            bits.append(f"{n_tmdl} TMDL")
        st.caption(" · ".join(bits))
        st.caption(f"`{rel}`")
        with st.popover(
            "Remove",
            icon=":material/delete:",
            width="stretch",
            key=f"bts_rm_{rel.as_posix()}",
        ):
            st.caption(
                f"Remove **{path.name}** from the workspace? "
                "The original fixture is unchanged."
            )
            if st.button(
                "Confirm remove",
                type="primary",
                icon=":material/delete:",
                width="stretch",
                key=f"bts_rm_ok_{rel.as_posix()}",
            ):
                _remove_source(path)
                if not list_bi_files(WORKSPACE_DIR):
                    state.set_cwd_ready(False)
                st.toast(f"Removed · {path.name}")
                st.rerun()


def run() -> None:
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    files = list_bi_files(WORKSPACE_DIR)
    state.set_cwd_ready(bool(files))
    if st.button(
        "Next: Map the estate",
        type="primary",
        icon=":material/navigate_next:",
        key="bts_load_next",
        disabled=not files,
        help=None if files else "Load a pack or upload a file first",
    ):
        st.switch_page("screens/estate_map.py")

    st.subheader("Add sources")
    st.caption(
        "Drop Tableau (`.twb` / `.twbx`) or Power BI (`.pbix` / `.pbit`) files, "
        "or load a bundled pack. Files land in the agent's working directory. "
        "Open **Copilot** (header) once to connect — later screens reuse that "
        "same streamed session."
    )

    connection = optional_secret("snowflake_connection")

    opts = st_coco.CocoOptions(
        connection=connection,
        cwd=str(WORKSPACE_DIR),
        allowed_tools=["Read", "Glob", "Grep"],
    )

    up_col, tab_col, pbi_col = st.columns(3, gap="medium", border=True)
    with up_col:
        st.markdown("**Upload your own**")
        st.caption(
            "Bring Tableau (`.twb` / `.twbx`) or Power BI (`.pbix` / `.pbit` / TMDL). "
            "Files are copied into `_uploads/` in the agent workspace so Copilot can "
            "read them. 200 MB per file."
        )
        st.space("stretch")
        saved = st_coco.cwd_uploader(
            opts,
            label="Upload",
            overwrite="replace",
            file_type=["twb", "twbx", "xml", "pbix", "pbit", "tmdl", "json"],
            key="bts_cwd_uploader",
            show_inventory=False,
        )
        if saved:
            state.set_cwd_ready(True)
            st.rerun()
    with tab_col:
        with st.container(horizontal=True, vertical_alignment="center"):
            st.image(_KIND_UI["tableau"]["icon"], width=24)
            st.markdown("**MIT Tableau pack**")
        st.caption(
            "Copies `ts_content.twb` + `ts_users.twb` from Tableau Server Insights. "
            "Same ops estate; the project-leader User Filter is on content and "
            "dropped on users — that is the access-rule demo."
        )
        st.caption(
            "MIT © Tableau · "
            "[community-tableau-server-insights]"
            "(https://github.com/tableau/community-tableau-server-insights). "
            "Full set of four stays in `examples/tableau_legacy/`."
        )
        st.space("stretch")
        _mit_pack_popover(
            label="Use MIT Tableau",
            key="bts_load_mit",
            paths=_tableau_pack_paths(),
            copy_fn=_copy_tableau_pack,
        )
    with pbi_col:
        with st.container(horizontal=True, vertical_alignment="center"):
            st.image(_KIND_UI["powerbi"]["icon"], width=24)
            st.markdown("**MIT Power BI pack**")
        st.caption(
            "Copies `Customer Profitability Sample (auto).pbix` + "
            "`Corporate Spend.pbix` from Microsoft's Obvience `IP` samples. "
            "They share `Fact` / `Scenario` / `Date` names; the columns do not agree."
        )
        st.caption(
            "MIT © Microsoft · no public RLS in these samples. "
            "See `examples/powerbi_legacy/`."
        )
        st.space("stretch")
        _mit_pack_popover(
            label="Use MIT Power BI",
            key="bts_load_pbi",
            paths=_powerbi_pack_paths(),
            copy_fn=_copy_powerbi_pack,
        )

    files = list_bi_files(WORKSPACE_DIR)
    state.set_cwd_ready(bool(files))

    st.subheader("Sources")
    st.caption(f"`{WORKSPACE_DIR}`")
    if not files:
        st.caption("No BI sources loaded yet.")
        return

    for start in range(0, len(files), 4):
        chunk = files[start : start + 4]
        cols = st.columns(4, gap="medium")
        for col, path in zip(cols, chunk):
            with col:
                _source_card(path)

    sample = files[0]
    kind = source_kind(sample)
    if kind == "tableau" and sample.is_file():
        with st.expander("Peek at raw XML (first Tableau workbook)", expanded=False):
            text = sample.read_text(encoding="utf-8", errors="replace")
            st.code(text[:1200] + ("\n…" if len(text) > 1200 else ""), language="xml")
            st.caption(f"`{sample.name}` — this is what nobody opens.")
    elif kind == "powerbi":
        lang, snippet = peek_powerbi(sample)
        with st.expander("Peek at the model (first Power BI source)", expanded=False):
            st.code(snippet, language=lang)
            st.caption(f"`{sample.name}` — DAX / M from the model, not a semantic view.")


run()
