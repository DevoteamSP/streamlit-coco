"""Tests for rich markdown / transcript windowing helpers."""

from __future__ import annotations

from streamlit_coco.rich_text import (
    normalize_fence_language,
    split_markdown_fences,
    window_transcript,
)


def test_split_fenced_sql_and_prose() -> None:
    text = "Here is SQL:\n\n```sql\nSELECT 1;\n```\n\nDone."
    parts = split_markdown_fences(text)
    assert [p.kind for p in parts] == ["markdown", "code", "markdown"]
    assert parts[1].language == "sql"
    assert parts[1].text == "SELECT 1;"
    assert "Done." in parts[2].text


def test_language_aliases() -> None:
    assert normalize_fence_language("py") == "python"
    assert normalize_fence_language("yml") == "yaml"
    assert normalize_fence_language("") == "text"


def test_window_transcript_load_earlier() -> None:
    items = [{"id": i} for i in range(10)]
    visible, hidden = window_transcript(items, max_messages=3, extra=0)
    assert [x["id"] for x in visible] == [7, 8, 9]
    assert hidden == 7
    visible2, hidden2 = window_transcript(items, max_messages=3, extra=3)
    assert [x["id"] for x in visible2] == [4, 5, 6, 7, 8, 9]
    assert hidden2 == 4
    all_items, hidden3 = window_transcript(items, max_messages=None)
    assert hidden3 == 0
    assert len(all_items) == 10
