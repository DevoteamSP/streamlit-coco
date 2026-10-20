"""Code written for 0.1.9 keeps working: nothing it could call, import or pass has gone.

``tests/fixtures/api_0.1.9.json`` describes the 0.1.9 release (the last one on PyPI). A name,
module, class member, enum member or parameter of it may not disappear, move, become required
or change its default, and a new parameter must have a default.
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path

from api_snapshot import compat_errors

SNAPSHOT = Path(__file__).parent / "fixtures" / "api_0.1.9.json"


def test_the_0_1_9_api_is_still_accepted() -> None:
    errors = compat_errors(json.loads(SNAPSHOT.read_text(encoding="utf-8")))
    assert not errors, "\n".join(errors)


def test_the_guard_notices_a_renamed_parameter() -> None:
    """The comparison itself: a keyword that was renamed is reported."""
    from api_snapshot import _param_errors

    old = [["session", "POSITIONAL_OR_KEYWORD", "<required>"], ["label", "KEYWORD_ONLY", "'x'"]]
    renamed = [["target", "POSITIONAL_OR_KEYWORD", "<required>"], ["label", "KEYWORD_ONLY", "'x'"]]
    assert any("`session` is gone" in e for e in _param_errors("f", old, renamed))
    appended = [*old, ["mini", "KEYWORD_ONLY", "False"]]
    assert _param_errors("f", old, appended) == []
    required = [*old, ["mini", "KEYWORD_ONLY", "<required>"]]
    assert any("no default" in e for e in _param_errors("f", old, required))


def test_render_output_field_keeps_its_0_1_9_keyword() -> None:
    from streamlit_coco.display import render_output_field

    names = list(inspect.signature(render_output_field).parameters)
    assert names[:2] == ["session", "container"]
