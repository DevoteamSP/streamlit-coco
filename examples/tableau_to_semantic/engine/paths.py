"""Filesystem locations for the tableau_to_semantic example."""

from __future__ import annotations

from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = APP_ROOT.parents[1]
FIXTURES_DIR = REPO_ROOT / "examples" / "tableau_legacy" / "workbooks"
WORKSPACE_DIR = REPO_ROOT / "examples" / "workspaces" / "tableau_to_semantic"
OUT_DIR = APP_ROOT / "out"
CONTRACTS_DIR = APP_ROOT / "contracts"

# Demo pack: two workbooks that carry the access-rule punchline
# (project leader present in content, absent in users). Full MIT set of four
# remains under examples/tableau_legacy/workbooks/.
MIT_WORKBOOKS = (
    "ts_content.twb",
    "ts_users.twb",
)

DATABASE = "TABLEAU_LEGACY"
SCHEMA = "PUBLIC"
