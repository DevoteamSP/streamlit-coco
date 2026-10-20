"""The Streamlit minimum is one number: pyproject.toml, the window's check and the README agree."""

from __future__ import annotations

import re
from pathlib import Path

from streamlit_coco.window import STREAMLIT_FLOOR

ROOT = Path(__file__).resolve().parents[1]
FLOOR = ".".join(map(str, STREAMLIT_FLOOR))


def test_pyproject_declares_the_floor_the_window_checks() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert re.search(rf'"streamlit>={re.escape(FLOOR)}"', text), FLOOR


def test_the_readme_says_the_same_floor() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"Streamlit {FLOOR} or later" in readme
