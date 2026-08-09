"""Tests for cwd upload helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from streamlit_coco.errors import CwdUploadError
from streamlit_coco.options import CocoOptions
from streamlit_coco.upload import (
    format_upload_prompt,
    list_cwd_uploads,
    sanitize_upload_name,
    upload_to_cwd,
)


def test_sanitize_strips_path_components() -> None:
    assert sanitize_upload_name("../etc/passwd.csv") == "passwd.csv"
    assert sanitize_upload_name(r"..\secret\report.csv") == "report.csv"
    assert sanitize_upload_name("my report (1).csv") == "my_report_1_.csv"


def test_sanitize_rejects_empty() -> None:
    with pytest.raises(CwdUploadError):
        sanitize_upload_name("")
    with pytest.raises(CwdUploadError):
        sanitize_upload_name("..")


def test_upload_to_cwd_writes_under_uploads(tmp_path: Path) -> None:
    saved = upload_to_cwd(tmp_path, [("notes.csv", b"a,b\n1,2\n")])
    assert len(saved) == 1
    assert saved[0].relative == "_uploads/notes.csv"
    assert saved[0].path.read_bytes() == b"a,b\n1,2\n"
    assert saved[0].path.parent == tmp_path / "_uploads"


def test_upload_to_cwd_accepts_options(tmp_path: Path) -> None:
    opts = CocoOptions(cwd=str(tmp_path))
    saved = upload_to_cwd(opts, [("a.txt", b"hi")])
    assert saved[0].path.exists()


def test_upload_rejects_extension(tmp_path: Path) -> None:
    with pytest.raises(CwdUploadError, match="Disallowed"):
        upload_to_cwd(tmp_path, [("evil.exe", b"MZ")])


def test_upload_rejects_oversize(tmp_path: Path) -> None:
    with pytest.raises(CwdUploadError, match="bytes"):
        upload_to_cwd(tmp_path, [("big.csv", b"x" * 100)], max_bytes=10)


def test_upload_overwrite_policies(tmp_path: Path) -> None:
    upload_to_cwd(tmp_path, [("dup.csv", b"one")])
    with pytest.raises(CwdUploadError, match="already exists"):
        upload_to_cwd(tmp_path, [("dup.csv", b"two")], overwrite="error")

    skipped = upload_to_cwd(tmp_path, [("dup.csv", b"two")], overwrite="skip")
    assert skipped[0].skipped is True
    assert (tmp_path / "_uploads" / "dup.csv").read_bytes() == b"one"

    replaced = upload_to_cwd(tmp_path, [("dup.csv", b"two")], overwrite="replace")
    assert replaced[0].overwritten is True
    assert (tmp_path / "_uploads" / "dup.csv").read_bytes() == b"two"


def test_upload_rejects_subdir_escape(tmp_path: Path) -> None:
    with pytest.raises(CwdUploadError, match="subdir"):
        upload_to_cwd(tmp_path, [("a.csv", b"x")], subdir="../outside")


def test_list_and_prompt(tmp_path: Path) -> None:
    saved = upload_to_cwd(tmp_path, [("a.csv", b"1"), ("b.md", b"# hi")])
    listed = list_cwd_uploads(tmp_path)
    assert {p.name for p in listed} == {"a.csv", "b.md"}
    prompt = format_upload_prompt(saved, user_text="Summarize them")
    assert "`_uploads/a.csv`" in prompt
    assert "Summarize them" in prompt


def test_empty_files_allowed(tmp_path: Path) -> None:
    saved = upload_to_cwd(tmp_path, [("empty.csv", b"")])
    assert saved[0].bytes_written == 0
    assert saved[0].path.exists()
