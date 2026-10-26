"""Code written for 0.3.0 keeps working: nothing it could call, import or pass has gone.

``tests/fixtures/api_0.3.0.json`` describes the 0.3.0 release, taken from the source tree the
``v0.3.0`` tag points at, with ``snowflake-cortex-agent-sdk`` 0.0.3 installed. It holds what 0.3.0
added to the 0.2.2 API (``ManagedOptions``, ``managed_agent``, ``options_from_connection``,
``AuditLog``, ``ask_coco(audit=)``, ``FolderPolicy(where=)``, ``check_environment(managed=)``, ...).
The rules are those of ``test_compat_019.py``.
"""

from __future__ import annotations

import json
from pathlib import Path

from api_snapshot import compat_errors

SNAPSHOT = Path(__file__).parent / "fixtures" / "api_0.3.0.json"


def _snapshot() -> dict:
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))


def test_the_0_3_0_api_is_still_accepted() -> None:
    errors = compat_errors(_snapshot())
    assert not errors, "\n".join(errors)


def test_the_snapshot_holds_what_0_3_0_added() -> None:
    top = _snapshot()["top"]
    for name in ("AuditLog", "ManagedOptions", "managed_agent", "options_from_connection"):
        assert name in top, name
    assert "upload_stage" in top["ManagedOptions"]["fields"]
    assert "audit" in {row[0] for row in top["ask_coco"]["params"]}
    check = {row[0]: row for row in top["check_environment"]["params"]}
    assert check["managed"][1] == "KEYWORD_ONLY"
