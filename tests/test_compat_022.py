"""Code written for 0.2.2 keeps working: nothing it could call, import or pass has gone.

``tests/fixtures/api_0.2.2.json`` describes the 0.2.2 release (the last one before the managed
agent), taken from the source of the ``v0.2.2`` tag with ``cortex-code-agent-sdk`` 1.0.7 installed,
as an application of that release had it. It holds what 0.2.0 to 0.2.2 added to the 0.1.9 API
(``ask_coco``, ``get_window``, ``Features``, ``Attachments``, ``on_layout``, ``split``, ...), which
``test_compat_019.py`` does not see. The rules are the same: a name, module, class member, enum
member or parameter may not disappear, move, become required or change its default, and a new
parameter must have a default.
"""

from __future__ import annotations

import json
from pathlib import Path

from api_snapshot import compat_errors

SNAPSHOT = Path(__file__).parent / "fixtures" / "api_0.2.2.json"


def _snapshot() -> dict:
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))


def test_the_0_2_2_api_is_still_accepted() -> None:
    errors = compat_errors(_snapshot())
    assert not errors, "\n".join(errors)


def test_a_default_that_is_the_machines_platform_is_not_compared() -> None:
    """The snapshot was taken on macOS ('darwin'); Linux CI reads 'linux': same API."""
    import sys

    from api_snapshot import _default

    assert _default(sys.platform) == "<object>"
    assert _default("another") == "'another'"


def test_the_snapshot_holds_what_0_2_x_added() -> None:
    """The fixture is not an empty or a 0.1.9 one: the window's names are in it."""
    top = _snapshot()["top"]
    for name in ("ask_coco", "get_window", "Features", "Attachments", "FolderPolicy"):
        assert name in top or name in _snapshot()["modules"].get("streamlit_coco.policy", {}), name
    ask = {row[0]: row for row in top["ask_coco"]["params"]}
    assert {"policy", "features", "labels", "agent", "on_layout", "split"} <= set(ask)
    assert ask["split"][1] == "KEYWORD_ONLY"


def test_a_parameter_that_0_2_2_accepted_is_not_dropped_unnoticed() -> None:
    """The comparison itself, on the window's call: a removed keyword is reported."""
    old = _snapshot()
    broken = json.loads(json.dumps(old))
    broken["top"]["ask_coco"]["params"].append(["gone_param", "KEYWORD_ONLY", "False"])
    assert any("`gone_param` is gone" in e for e in compat_errors(broken))
