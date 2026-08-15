"""App viewer helpers — exception parse and fix prompt (no Streamlit UI)."""

from __future__ import annotations

from pathlib import Path

import streamlit_coco as st_coco
from streamlit_coco.app_preview import (
    default_fix_prompt,
    last_preview_exception,
    preview_log_tail,
)


def test_app_viewer_exports() -> None:
    assert "app_viewer" in st_coco.__all__
    assert "default_fix_prompt" in st_coco.__all__
    assert "last_preview_exception" in st_coco.__all__
    assert "start_app_preview" in st_coco.__all__
    assert callable(st_coco.default_fix_prompt)
    assert callable(st_coco.last_preview_exception)


def test_app_viewer_export_not_shadowed_by_submodule() -> None:
    """``st_coco.app_viewer`` must stay the function after the impl module loads.

    A same-named ``app_viewer.py`` would bind the submodule on the package and
    make ``st_coco.app_viewer(...)`` raise TypeError on the next rerun.
    """
    import streamlit_coco.viewer as impl

    assert callable(st_coco.app_viewer)
    assert st_coco.app_viewer is impl.app_viewer
    assert callable(st_coco.app_viewer)


def test_last_preview_exception_reads_current_traceback(tmp_path: Path) -> None:
    log = tmp_path / ".preview.log"
    log.write_text(
        "2026-08-15 started\n"
        "Uncaught app exception\n"
        "Traceback (most recent call last):\n"
        '  File "streamlit_app.py", line 12, in <module>\n'
        "NameError: name 'foo' is not defined\n",
        encoding="utf-8",
    )
    err = last_preview_exception(tmp_path)
    assert err is not None
    assert "NameError" in err
    log.write_text(
        log.read_text(encoding="utf-8")
        + "\n" * 8
        + "2026-08-15 12:00:00.000 Executing script\n"
        + "2026-08-15 12:00:00.100 Session rerun ok\n",
        encoding="utf-8",
    )
    assert last_preview_exception(tmp_path) is None


def test_last_preview_exception_missing_log(tmp_path: Path) -> None:
    assert last_preview_exception(tmp_path) is None
    assert preview_log_tail(tmp_path) == ""


def test_preview_log_tail_last_n_lines(tmp_path: Path) -> None:
    (tmp_path / ".preview.log").write_text(
        "\n".join(f"line {i}" for i in range(10)),
        encoding="utf-8",
    )
    assert preview_log_tail(tmp_path, n=3) == "line 7\nline 8\nline 9"


def test_default_fix_prompt_includes_traceback_and_app_dir(tmp_path: Path) -> None:
    dest = tmp_path / "streamlit_dash"
    dest.mkdir()
    prompt = default_fix_prompt("NameError: name 'foo' is not defined", dest)
    assert "NameError" in prompt
    assert "streamlit_dash/streamlit_app.py" in prompt
    assert "Write / Edit" in prompt
    assert "tts_" not in prompt
    assert "Tableau" not in prompt


def test_default_fix_prompt_empty_traceback_is_inspect_stub(tmp_path: Path) -> None:
    dest = tmp_path / "my_app"
    dest.mkdir()
    prompt = default_fix_prompt("", dest)
    assert "no traceback" in prompt
    assert "my_app/streamlit_app.py" in prompt
