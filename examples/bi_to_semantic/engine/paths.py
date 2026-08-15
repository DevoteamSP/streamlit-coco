"""Filesystem locations for the bi_to_semantic example."""

from __future__ import annotations

from pathlib import Path

from engine.bi_sources import has_powerbi, has_tableau, list_bi_files, source_kind

APP_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = APP_ROOT.parents[1]
TABLEAU_FIXTURES_DIR = REPO_ROOT / "examples" / "tableau_legacy" / "workbooks"
POWERBI_FIXTURES_DIR = REPO_ROOT / "examples" / "powerbi_legacy"
WORKSPACE_DIR = REPO_ROOT / "examples" / "workspaces" / "bi_to_semantic"
OUT_DIR = APP_ROOT / "out"
CONTRACTS_DIR = APP_ROOT / "contracts"

# Back-compat alias used by older comments / imports.
FIXTURES_DIR = TABLEAU_FIXTURES_DIR

# Demo pack: two workbooks that carry the access-rule punchline
# (project leader present in content, absent in users). Full MIT set of four
# remains under examples/tableau_legacy/workbooks/.
MIT_WORKBOOKS = (
    "ts_content.twb",
    "ts_users.twb",
)

POWERBI_PACK = (
    "Customer Profitability Sample (auto).pbix",
    "Corporate Spend.pbix",
)
POWERBI_OPTIONAL = (
    "Human Resources Sample PBIX.pbix",
    "Employee Hiring and History.pbix",
)

DATABASE_TABLEAU = "TABLEAU_LEGACY"
DATABASE_POWERBI = "POWERBI_LEGACY"
DATABASE_MIXED = "BI_ESTATE"
SCHEMA = "PUBLIC"
# Default until workspace sources are known (Tableau MIT pack).
DATABASE = DATABASE_TABLEAU


def warehouse_ids(paths: list[Path] | None = None) -> tuple[str, str]:
    """Database + schema for generated SQL, based on loaded sources."""
    files = paths if paths is not None else list_bi_files(WORKSPACE_DIR)
    tab, pbi = has_tableau(files), has_powerbi(files)
    if tab and pbi:
        return DATABASE_MIXED, SCHEMA
    if pbi:
        return DATABASE_POWERBI, SCHEMA
    return DATABASE_TABLEAU, SCHEMA


def source_kinds_in_workspace() -> set[str]:
    kinds: set[str] = set()
    for path in list_bi_files(WORKSPACE_DIR):
        kind = source_kind(path)
        if kind:
            kinds.add(kind)
    return kinds
