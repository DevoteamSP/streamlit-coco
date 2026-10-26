"""The shop: what the screens ask. Pure Python: no Streamlit.

    shop = Shop(store)
    shop.skills(query="sql", pack="snowflake")     # the latest version of each skill
    shop.verify(skill)                             # the files on the store are the ones published
    shop.chat_options(base, skill)                 # ManagedOptions for a chat with that skill only

A chat has exactly one skill: the managed agent takes its skills when the conversation is
created, and a skill added to an existing thread was not picked up (spike, 2026-10-26), so
choosing another skill is a new conversation.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass, field, replace
from pathlib import Path

from shop.skill import Skill, folder_hash, parse_front_matter, semver_key
from shop.stores import SkillStore


@dataclass
class Verdict:
    ok: bool
    problems: list[str] = field(default_factory=list)


class Shop:
    def __init__(self, store: SkillStore) -> None:
        self.store = store

    # ------------------------------------------------------------------ the catalogue

    def all_versions(self) -> list[Skill]:
        return self.store.index()

    def skills(self, *, query: str = "", pack: str | None = None) -> list[Skill]:
        """The latest version of each skill, filtered by a text (id, title, description, pack) and a
        pack."""
        latest: dict[str, Skill] = {}
        for skill in self.store.index():
            best = latest.get(skill.id)
            if best is None or semver_key(skill.version) > semver_key(best.version):
                latest[skill.id] = skill
        words = query.lower().split()
        found = []
        for skill in latest.values():
            haystack = " ".join([skill.id, skill.title, skill.description, skill.pack]).lower()
            if (not pack or skill.pack == pack) and all(word in haystack for word in words):
                found.append(skill)
        return sorted(found, key=lambda s: (s.pack, s.title.lower()))

    def packs(self) -> list[str]:
        return sorted({s.pack for s in self.store.index() if s.pack})

    def versions(self, skill_id: str) -> list[Skill]:
        found = [s for s in self.store.index() if s.id == skill_id]
        return sorted(found, key=lambda s: semver_key(s.version), reverse=True)

    def get(self, skill_id: str, version: str | None = None) -> Skill:
        for skill in self.versions(skill_id):
            if version is None or skill.version == version:
                return skill
        raise KeyError(f"{skill_id} {version or ''}".strip())

    def about(self, skill: Skill) -> str:
        """The body of SKILL.md, without its front matter."""
        return parse_front_matter(self.store.read_skill_md(skill))[1].strip()

    # ------------------------------------------------------------------ before a chat

    def verify(self, skill: Skill) -> Verdict:
        """The folder on the store is what was published: the same list of files (the agent mounts
        the whole folder, so an added file counts), then the same content. A changed folder is not
        offered for a chat."""
        try:
            listed = sorted(self.store.list_files(skill))
        except Exception as error:  # noqa: BLE001 - an unreadable folder is a problem
            return Verdict(False, [f"Could not read the folder: {error}"])
        if listed != sorted(skill.files):
            added, missing = set(listed) - set(skill.files), set(skill.files) - set(listed)
            detail = "; ".join(
                f"{label}: {', '.join(sorted(names))}"
                for label, names in (("added", added), ("missing", missing))
                if names
            )
            return Verdict(False, [f"The files are not the ones that were published ({detail})."])
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            try:
                self.store.fetch(skill, root)
            except Exception as error:  # noqa: BLE001 - a missing or unreadable file is a problem
                return Verdict(False, [f"Could not read the files: {error}"])
            if folder_hash(root, list(skill.files)) != skill.sha256:
                return Verdict(False, ["The content changed since it was published."])
        return Verdict(True)

    def chat_options(self, base, skill: Skill):
        """`ManagedOptions` for a chat with this skill and no other. `base` carries the identity and
        the mounts; the connection stays with the shop (it is not closed with the chat)."""
        return replace(
            base,
            connection=None,
            stage_skills=[{"name": skill.id, "path": self.store.skill_path(skill)}],
        )
