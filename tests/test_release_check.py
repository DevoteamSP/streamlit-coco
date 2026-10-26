"""The parsing of scripts/release_check.py (the checks need the network and the clones)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "release_check", Path(__file__).resolve().parents[1] / "scripts" / "release_check.py"
)
rc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rc)

DRY_RUN = """\
sending incremental file list
.d..t.... doc/
>f.st.... CHANGELOG.md
>f..t.... README.md
>f+++++++ tests/e2e/test_window_layout.py
cd+++++++ doc/releases/0.2.2/
>f.st.... examples/app_builder/out/meeting-recap/brief.json
>f+++++++ doc-dev/releases/0.2.2/linkedin.md
*deleting examples/app_builder/engine/copilot_panel.py
Synced -> /somewhere/streamlit-coco
"""


def test_a_time_only_change_is_not_content() -> None:
    found = rc.parse_sync_dry_run(DRY_RUN)
    assert "README.md" not in found["content"]
    assert "CHANGELOG.md" in found["content"]
    assert "tests/e2e/test_window_layout.py" in found["content"]
    assert "doc/" not in found["content"] and "doc/releases/0.2.2/" not in found["content"]


def test_deletions_out_files_and_leaks_are_told_apart() -> None:
    found = rc.parse_sync_dry_run(DRY_RUN)
    assert found["deleted"] == ["examples/app_builder/engine/copilot_panel.py"]
    assert found["out"] == ["examples/app_builder/out/meeting-recap/brief.json"]
    assert found["leaks"] == ["doc-dev/releases/0.2.2/linkedin.md"]


def test_a_clean_dry_run_has_nothing_to_flag() -> None:
    found = rc.parse_sync_dry_run(">f.st.... streamlit_coco/window.py\n>f..t.... README.md\n")
    assert found["out"] == [] and found["leaks"] == [] and found["deleted"] == []


def test_the_public_changelog_may_not_know_more_than_the_dev_one() -> None:
    dev = "## [Unreleased]\n\n## [0.2.2] - x\n\n## [0.2.0] - x\n"
    public = "## [Unreleased]\n\n## [0.2.1] - x\n\n## [0.2.0] - x\n"
    assert rc.unknown_releases(public, dev) == ["0.2.1"]
    assert rc.unknown_releases(dev, dev) == []


def test_versions_are_read_from_pyproject_and_the_module() -> None:
    assert rc.project_version('[project]\nname = "x"\nversion = "1.2.3"\n') == "1.2.3"
    assert rc.module_version('"""d"""\n__version__ = "1.2.3"\n') == "1.2.3"


def test_alerts_are_counted_by_manifest() -> None:
    tsv = (
        "uv.lock\tpillow\thigh\n"
        "uv.lock\tcertifi\tcritical\n"
        "examples/app_builder/uv.lock\tpillow\thigh\n"
    )
    assert rc.alerts_by_manifest(tsv) == {"uv.lock": 2, "examples/app_builder/uv.lock": 1}
