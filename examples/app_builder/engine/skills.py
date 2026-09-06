"""Guidelines skills on disk — shared + per-type packs CoCo Reads."""

from __future__ import annotations

import re
from pathlib import Path

from engine.paths import TYPES_DIR

SHARED_SKILL_ID = "shared"
_SKILL_ID = re.compile(r"^[a-z][a-z0-9-]{0,62}$")


def skill_dir(skill_id: str) -> Path:
    return (TYPES_DIR / skill_id).resolve()


def skill_md_path(skill_id: str) -> Path:
    return skill_dir(skill_id) / "SKILL.md"


def _ensure_under_types(path: Path) -> Path:
    root = TYPES_DIR.resolve()
    resolved = path.resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError("skill path must stay under types/")
    return resolved


def read_skill_md(skill_id: str) -> str:
    path = skill_md_path(skill_id)
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def write_skill_md(skill_id: str, body: str) -> Path:
    if skill_id != SHARED_SKILL_ID and not _SKILL_ID.match(skill_id):
        raise ValueError("skill folder must be a lowercase id (letters, digits, hyphen)")
    dest = _ensure_under_types(skill_md_path(skill_id))
    dest.parent.mkdir(parents=True, exist_ok=True)
    text = body if body.endswith("\n") else f"{body}\n"
    dest.write_text(text, encoding="utf-8")
    return dest


def skill_dirs_for(guidelines_skill: str | None) -> list[str]:
    """Directories to pass as CoCo ``add_dirs`` (shared first, then the type)."""
    dirs: list[str] = []
    shared = skill_dir(SHARED_SKILL_ID)
    if shared.is_dir():
        dirs.append(str(shared))
    if guidelines_skill and guidelines_skill != SHARED_SKILL_ID:
        typed = skill_dir(guidelines_skill)
        if typed.is_dir():
            dirs.append(str(typed))
    return dirs


def skill_md_files_for(guidelines_skill: str | None) -> list[Path]:
    """SKILL.md files CoCo must Read on Build (shared, then type)."""
    files: list[Path] = []
    shared = skill_md_path(SHARED_SKILL_ID)
    if shared.is_file():
        files.append(shared)
    if guidelines_skill and guidelines_skill != SHARED_SKILL_ID:
        typed = skill_md_path(guidelines_skill)
        if typed.is_file():
            files.append(typed)
    return files
