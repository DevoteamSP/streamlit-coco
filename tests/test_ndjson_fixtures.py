"""Regression tests against recorded NDJSON stream fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from streamlit_coco.messages import parse_ndjson_stream

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "ndjson"
MANIFEST = FIXTURES_DIR / "manifest.json"


def _load_manifest() -> dict[str, dict]:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return payload["files"]


def _match_event(event, expected: dict) -> None:
    for key, value in expected.items():
        actual = getattr(event, key)
        if isinstance(value, dict):
            assert actual == value, f"field {key!r}: {actual!r} != {value!r}"
        else:
            assert actual == value, f"field {key!r}: {actual!r} != {value!r}"


@pytest.mark.parametrize(
    "filename,spec",
    list(_load_manifest().items()),
    ids=list(_load_manifest().keys()),
)
def test_ndjson_fixture_corpus(filename: str, spec: dict) -> None:
    text = (FIXTURES_DIR / filename).read_text(encoding="utf-8")
    events = parse_ndjson_stream(text)
    expected = spec["expect"]
    assert len(events) >= len(expected), (
        f"{filename}: expected at least {len(expected)} events, got {len(events)}"
    )
    for index, event_spec in enumerate(expected):
        _match_event(events[index], event_spec)
