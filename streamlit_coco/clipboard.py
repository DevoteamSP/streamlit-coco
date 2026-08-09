"""Browser clipboard copy control (CCv2 inline)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import streamlit as st

_COPY_HTML = """
<button type="button" class="coco-copy-btn"
  aria-label="Copy to clipboard" title="Copy to clipboard">
  <span class="coco-copy-icon" aria-hidden="true">content_copy</span>
</button>
<span class="coco-copy-status" aria-live="polite"></span>
"""

_COPY_CSS = """
:host, .coco-copy-wrap { display: inline-flex; align-items: center; gap: 0.35rem; }
.coco-copy-btn {
  appearance: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.75rem;
  height: 1.75rem;
  padding: 0;
  border: 1px solid var(--st-secondary-text-color, #8884);
  background: var(--st-background-color, transparent);
  color: var(--st-text-color, inherit);
  border-radius: 0.35rem;
  cursor: pointer;
  line-height: 1;
}
.coco-copy-btn:hover { border-color: var(--st-primary-color, #ff4b4b); }
.coco-copy-icon {
  font-family: "Material Symbols Rounded";
  font-weight: 400;
  font-style: normal;
  font-size: 1.125rem;
  line-height: 1;
  user-select: none;
  font-variation-settings: "FILL" 0, "wght" 400, "GRAD" 0, "opsz" 20;
  -webkit-font-smoothing: antialiased;
}
.coco-copy-status {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
"""

_COPY_JS = """
export default function ({ data, parentElement }) {
  const btn = parentElement.querySelector(".coco-copy-btn");
  const icon = parentElement.querySelector(".coco-copy-icon");
  const status = parentElement.querySelector(".coco-copy-status");
  if (!btn || !icon || !status) return;
  const label = (data && data.label) || "Copy to clipboard";
  const text = (data && data.text) != null ? String(data.text) : "";
  btn.setAttribute("aria-label", label);
  btn.setAttribute("title", label);
  icon.textContent = "content_copy";
  btn.onclick = async () => {
    try {
      await navigator.clipboard.writeText(text);
      icon.textContent = "check";
      status.textContent = "Copied";
      setTimeout(() => {
        icon.textContent = "content_copy";
        status.textContent = "";
      }, 1600);
    } catch (_err) {
      status.textContent = "Failed";
      setTimeout(() => { status.textContent = ""; }, 2000);
    }
  };
}
"""


@lru_cache(maxsize=1)
def _get_copy_component() -> Any:
    if not hasattr(st.components, "v2"):
        raise RuntimeError(
            "Copy button requires Streamlit >= 1.53 with Custom Components v2. "
            f"Installed version: {st.__version__}"
        )
    return st.components.v2.component(
        "streamlit_coco_copy",
        html=_COPY_HTML,
        css=_COPY_CSS,
        js=_COPY_JS,
        isolate_styles=True,
    )


def render_copy_button(
    text: str,
    *,
    key: str,
    label: str = "Copy to clipboard",
    height: int = 32,
) -> None:
    """Mount a one-click browser clipboard button for ``text``.

    ``label`` is used for ``aria-label`` / tooltip only (icon-only button).
    """
    if not text:
        return
    try:
        component = _get_copy_component()
    except RuntimeError:
        # Extremely old Streamlit — skip silently; st.code still has native copy.
        return
    component(
        data={"text": text, "label": label},
        key=key,
        height=height,
        width="content",
    )
