"""Discover Tableau and Power BI sources in the BI → Semantic workspace."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

BiKind = Literal["tableau", "powerbi"]

TABLEAU_SUFFIXES = {".twb", ".twbx"}
POWERBI_FILE_SUFFIXES = {".pbix", ".pbit"}


def source_kind(path: Path) -> BiKind | None:
    if path.is_file():
        suffix = path.suffix.lower()
        if suffix in TABLEAU_SUFFIXES:
            return "tableau"
        if suffix in POWERBI_FILE_SUFFIXES or suffix == ".tmdl":
            return "powerbi"
        return None
    if path.is_dir() and _powerbi_dir(path):
        return "powerbi"
    return None


def _powerbi_dir(path: Path) -> bool:
    if (path / "model.tmdl").is_file():
        return True
    tmdls = list(path.glob("*.tmdl"))
    return bool(tmdls) and (path / "report.json").is_file()


def source_label(path: Path) -> str:
    return path.name


def list_bi_files(cwd: Path) -> list[Path]:
    """Tableau workbooks + Power BI files/folders at cwd (and ``_uploads/``)."""
    found: list[Path] = []
    patterns = (
        "*.twb",
        "*.twbx",
        "*.pbix",
        "*.pbit",
        "_uploads/*.twb",
        "_uploads/*.twbx",
        "_uploads/*.pbix",
        "_uploads/*.pbit",
    )
    for pattern in patterns:
        found.extend(cwd.glob(pattern))

    search_roots = [cwd, cwd / "_uploads"]
    for root in search_roots:
        if not root.is_dir():
            continue
        for child in sorted(root.iterdir()):
            if child.is_dir() and _powerbi_dir(child):
                found.append(child)
            elif child.is_file() and child.suffix.lower() == ".tmdl":
                found.append(child)

    by_key: dict[str, Path] = {}
    for path in found:
        if source_kind(path) is None:
            continue
        by_key[str(path.resolve())] = path
    return sorted(by_key.values(), key=lambda p: p.name.lower())


def partition_sources(paths: list[Path]) -> tuple[list[Path], list[Path]]:
    """Return ``(tableau, powerbi)``."""
    tableau: list[Path] = []
    powerbi: list[Path] = []
    for path in paths:
        kind = source_kind(path)
        if kind == "tableau":
            tableau.append(path)
        elif kind == "powerbi":
            powerbi.append(path)
    return tableau, powerbi


def has_tableau(paths: list[Path]) -> bool:
    return bool(partition_sources(paths)[0])


def has_powerbi(paths: list[Path]) -> bool:
    return bool(partition_sources(paths)[1])
