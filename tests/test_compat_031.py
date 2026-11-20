"""Code written for 0.3.1 keeps working: nothing it could call, import or pass has gone.

``tests/fixtures/api_0.3.1.json`` describes the 0.3.1 release, taken from the source tree of the
cut, with ``snowflake-cortex-agent-sdk`` 0.0.3 installed. It holds what 0.3.1 added to the 0.3.0
API: ``CocoOptions.settings_file``. The rules are those of ``test_compat_019.py``.
"""

from __future__ import annotations

import json
from pathlib import Path

from api_snapshot import compat_errors

SNAPSHOT = Path(__file__).parent / "fixtures" / "api_0.3.1.json"


def _snapshot() -> dict:
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))


def test_the_0_3_1_api_is_still_accepted() -> None:
    errors = compat_errors(_snapshot())
    assert not errors, "\n".join(errors)


def test_the_snapshot_holds_what_0_3_1_added() -> None:
    options = _snapshot()["top"]["CocoOptions"]
    assert "settings_file" in options["fields"]
    params = {row[0]: row for row in options["init"]}
    assert params["settings_file"][2] == "None"
