"""Optional streamlit-coco window: answers from this pack's Markdown."""

from __future__ import annotations

import streamlit as st
from i18n import LANG_NAME, t
from pack import pack_dir


def _example_questions(
    lang: str,
    *,
    source: str | None,
    track: str | None,
) -> list[dict[str, str]]:
    spoken = LANG_NAME.get(lang, "English")
    if source:
        return [
            {
                "title": t(lang, "coco_q_explain"),
                "text": t(lang, "coco_q_explain_q").format(source=source, lang=spoken),
            },
            {
                "title": t(lang, "coco_q_next"),
                "text": t(lang, "coco_q_next_q").format(source=source, lang=spoken),
            },
        ]
    if track:
        return [
            {
                "title": t(lang, "coco_q_track"),
                "text": t(lang, "coco_q_track_q").format(track=track, lang=spoken),
            },
            {
                "title": t(lang, "coco_q_start"),
                "text": t(lang, "coco_q_start_q").format(lang=spoken),
            },
        ]
    return [
        {
            "title": t(lang, "coco_q_start"),
            "text": t(lang, "coco_q_start_q").format(lang=spoken),
        },
        {
            "title": t(lang, "coco_q_path"),
            "text": t(lang, "coco_q_path_q").format(lang=spoken),
        },
    ]


def _labels(lang: str) -> dict[str, str]:
    labels = {}
    labels["window.launcher.label"] = t(lang, "coco_ask")
    labels["window.field.placeholder"] = t(lang, "coco_placeholder")
    return labels


def render_window(
    lang: str,
    *,
    source: str | None,
    track: str | None,
) -> None:
    try:
        import streamlit_coco as st_coco
    except ImportError:
        st.caption(f"{t(lang, 'coco_missing')} {t(lang, 'coco_install')}")
        st.code(
            "uv run --with streamlit --with pyyaml --with 'streamlit-coco[sdk]' "
            "streamlit run streamlit_app.py"
        )
        return

    # Default FolderPolicy: Read/Glob/Grep free inside the pack, every other call asks.
    st_coco.ask_coco(
        pack_dir(),
        key="training_coco",  # one conversation: a language switch keeps it, the labels follow
        prompts=_example_questions(lang, source=source, track=track),
        labels=_labels(lang),
    )
