"""Example with custom structured-output renderer."""

from __future__ import annotations

import streamlit as st

import streamlit_coco as st_coco

st.set_page_config(page_title="CoCo Structured Output", layout="wide")
st.title("CoCo with custom output panel")

left, right = st.columns([2, 1])

with right:
    pipeline = st.empty()
    pipeline.markdown("##### Pipeline output")
    pipeline.caption("Waiting for structured result…")

# JSON Schema forces structured_output on the result (checklist steps 3–5).
PACKAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "version": {"type": "string"},
        "requires_python": {"type": "string"},
        "dependencies": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["name", "version", "requires_python", "dependencies"],
    "additionalProperties": False,
}

opts = st_coco.CocoOptions(
    cwd=".",
    allowed_tools=["Read", "Glob", "Grep"],
    output_schema=PACKAGE_SCHEMA,
)
session = st_coco.get_or_create_session(opts, key="structured_demo")
if not session.is_ready and not session.is_connecting:
    session.start()


def render_output(data: dict, result: st_coco.CocoChatResult) -> None:
    with pipeline.container():
        st.subheader("Pipeline output")
        if "selected_features" in data:
            st.metric("Selected features", len(data["selected_features"]))
            st.dataframe(data["selected_features"])
        elif "name" in data and "version" in data:
            st.metric("Package", str(data.get("name")))
            st.metric("Version", str(data.get("version")))
            st.caption(f"requires-python: {data.get('requires_python', '—')}")
            deps = data.get("dependencies") or []
            st.write(f"{len(deps)} dependencies")
            if deps:
                st.dataframe({"dependency": deps})
        else:
            st.json(data)


with left:
    st.caption(
        "Ask CoCo to Read `pyproject.toml` and return name/version/"
        "requires_python/dependencies as structured JSON."
    )
    st_coco.chat(
        session=session,
        key="coco_chat",
        on_structured_output=render_output,
        use_fragment=False,
    )
