"""Structured output: the page shows the result CoCo returns as data.

``CocoOptions(output_schema=...)`` makes the answer data. The button asks through ``coco.ask``,
the window shows the data block, and ``coco.result`` hands the same data to the page.
"""

from __future__ import annotations

import streamlit as st

import streamlit_coco as st_coco

st.set_page_config(page_title="CoCo Structured Output", layout="wide")
st.title("CoCo with a result on the page")

PACKAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "version": {"type": "string"},
        "requires_python": {"type": "string"},
        "dependencies": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["name", "version", "requires_python", "dependencies"],
    "additionalProperties": False,
}
KEY = "package"

coco = st_coco.ask_coco(
    ".",
    options=st_coco.CocoOptions(output_schema=PACKAGE_SCHEMA),
    policy=st_coco.policy.FolderPolicy("."),
)

left, right = st.columns([2, 1])
with left:
    st.caption("Ask CoCo to read `pyproject.toml` and return its package facts as data.")
    if st.button("Ask for the package facts", type="primary"):  # ask only behind a button
        coco.ask(
            "Package facts", "Read pyproject.toml and return the package facts as structured data."
        )

result = coco.result("Package facts")
if result is not None:
    st.session_state[KEY] = result
shown = st.session_state.get(KEY)
with right:
    st.subheader("Pipeline output")
    if shown is None:
        st.caption("Waiting for a structured result…")
    elif not isinstance(shown["data"], dict):
        st.write(shown["text"])
    elif "name" in shown["data"]:
        data = shown["data"]
        st.metric("Package", str(data["name"]))
        st.metric("Version", str(data.get("version")))
        st.write(f"{len(data.get('dependencies') or [])} dependencies")
    else:
        st.json(shown["data"])
