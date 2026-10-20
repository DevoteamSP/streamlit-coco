"""Display a pack HTML companion inside an iframe (never as a Streamlit route)."""

from __future__ import annotations

import streamlit as st

# The companion pages are full-width, not A4. The frame is about a screen tall;
# the document scrolls inside it, so previous / next stay within reach below.
FRAME_HEIGHT_PX = 900

_FRAME = st.components.v2.component(
    "training_html_frame",
    html="<div class='frame-root'></div>",
    css=f"""
.frame-root {{ width: 100%; height: {FRAME_HEIGHT_PX}px; }}
.frame-root iframe {{
  width: 100%;
  height: 100%;
  border: 1px solid #E2E4EA;
  border-radius: 12px;
  background: #fff;
}}
""",
    js="""
export default function (component) {
  const { data, parentElement } = component
  const root = parentElement.querySelector(".frame-root")
  if (!root) return

  let iframe = root.querySelector("iframe")
  if (!iframe) {
    iframe = document.createElement("iframe")
    iframe.setAttribute("title", "Document")
    root.appendChild(iframe)
  }

  const stamp = (data && data.source) || ""
  const html = (data && data.html) || ""
  if (iframe.dataset.stamp !== stamp) {
    iframe.dataset.stamp = stamp
    iframe.srcdoc = html
  }
}
""",
)


def render_html_frame(html_text: str, *, source: str) -> None:
    _FRAME(
        data={"html": html_text, "source": source},
        key="pack_html_frame",
        width="stretch",
        height=FRAME_HEIGHT_PX,
    )
