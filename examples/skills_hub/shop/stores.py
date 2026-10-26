"""Where the skills are kept: a folder on this computer (development, tests) or a Snowflake stage.

Both have the layout the managed agent reads from a stage:

    skills/index.json                          written only by `publish`
    skills/<id>/<version>/SKILL.md             one immutable folder per published version
    skills/<id>/<version>/references|assets|scripts/...

The stage is the source of truth: there is no table. A store only reads and writes; whether a
folder may be published is `skill.validate_folder`'s say, and who may write to the stage is the
stage's grants.
"""

from __future__ import annotations

import json
import re
import shutil
import tempfile
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from shop.skill import Report, Skill, semver_key

STAGE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*(?:\.[A-Za-z_][A-Za-z0-9_$]*){2}$")
INDEX = "skills/index.json"


class PublishError(Exception):
    """A skill that cannot be published (a version that exists, a report with errors, ...)."""


class NotOnAStage(Exception):
    """The store has no stage: the managed agent cannot read its skills."""


class SkillStore(Protocol):
    label: str
    is_stage: bool

    def index(self) -> list[Skill]: ...

    def read_skill_md(self, skill: Skill) -> str: ...

    def list_files(self, skill: Skill) -> list[str]: ...

    def fetch(self, skill: Skill, dest: Path) -> None: ...

    def publish(self, folder: Path, report: Report, *, force: bool = False) -> Skill: ...

    def skill_path(self, skill: Skill) -> str: ...


def _entries(skills: list[Skill], new: Skill) -> list[Skill]:
    """The index with `new` in it (replacing the same id and version), in order."""
    kept = [s for s in skills if (s.id, s.version) != (new.id, new.version)]
    return sorted([*kept, new], key=lambda s: (s.id, semver_key(s.version)))


def _index_text(skills: list[Skill]) -> str:
    body = {"schema": 1, "skills": [s.to_json() for s in skills]}
    return json.dumps(body, indent=2, sort_keys=True) + "\n"


def _parse_index(text: str) -> list[Skill]:
    try:
        data = json.loads(text)
        return [Skill.from_json(item) for item in data["skills"]]
    except (ValueError, KeyError, TypeError) as error:
        raise PublishError(f"skills/index.json is not readable: {error}") from error


def _stamped(report: Report, now: datetime | None) -> Skill:
    if not report.ok:
        raise PublishError("; ".join(report.errors) or "nothing to publish")
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return replace(report.skill, published_at=stamp)


class LocalFolderStore:
    """`root/skills/...` on this computer."""

    is_stage = False

    def __init__(self, root: str | Path, *, now: datetime | None = None) -> None:
        self.root, self._now = Path(root), now
        self.label = f"folder {self.root}"

    def index(self) -> list[Skill]:
        path = self.root / INDEX
        return _parse_index(path.read_text(encoding="utf-8")) if path.is_file() else []

    def read_skill_md(self, skill: Skill) -> str:
        return (self.root / skill.folder / "SKILL.md").read_text(encoding="utf-8")

    def list_files(self, skill: Skill) -> list[str]:
        root = self.root / skill.folder
        return sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())

    def fetch(self, skill: Skill, dest: Path) -> None:
        for rel in skill.files:
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.root / skill.folder / rel, target)

    def skill_path(self, skill: Skill) -> str:
        raise NotOnAStage("A skill in a local folder cannot be given to the managed agent.")

    def publish(self, folder: Path, report: Report, *, force: bool = False) -> Skill:
        skill = _stamped(report, self._now)
        target = self.root / skill.folder
        if target.exists():
            if not force:
                raise PublishError(f"{skill.id} {skill.version} is published; bump the version.")
            shutil.rmtree(target)
        for rel in skill.files:
            (target / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(folder / rel, target / rel)
        index = self.root / INDEX
        index.parent.mkdir(parents=True, exist_ok=True)
        scratch = index.with_suffix(".tmp")
        scratch.write_text(_index_text(_entries(self.index(), skill)), encoding="utf-8")
        scratch.replace(index)
        return skill


class CachedStore:
    """Another store's index, kept for `ttl` seconds: a Streamlit page reruns on every click and the
    stage is a network call. `refresh()` drops it; a publish through this store does too."""

    def __init__(self, store: Any, ttl: float = 60.0, *, clock=None) -> None:
        import time

        self._store, self._ttl, self._clock = store, ttl, clock or time.monotonic
        self._cached: tuple[float, list[Skill]] | None = None
        self.label, self.is_stage = store.label, store.is_stage

    def refresh(self) -> None:
        self._cached = None

    def index(self) -> list[Skill]:
        now = self._clock()
        if self._cached is None or now - self._cached[0] > self._ttl:
            self._cached = (now, self._store.index())
        return list(self._cached[1])

    def publish(self, folder: Path, report: Report, *, force: bool = False) -> Skill:
        self.refresh()
        return self._store.publish(folder, report, force=force)

    def __getattr__(self, name: str) -> Any:  # read_skill_md, fetch, skill_path
        return getattr(self._store, name)


class StageStore:
    """`@DB.SCHEMA.STAGE/skills/...` through a Snowflake connector connection.

    The stage must be a fully qualified, unquoted name: it goes into statements (and into the path
    the managed agent mounts), so it is checked against STAGE_RE and nothing else is interpolated
    except validated ids, versions and file names. The connection is the caller's: this class does
    not close it."""

    is_stage = True

    def __init__(self, connection: Any, stage: str, *, now: datetime | None = None) -> None:
        stage = stage.strip().lstrip("@")
        if not STAGE_RE.match(stage):
            raise ValueError("The stage must be DATABASE.SCHEMA.STAGE (letters, digits, _ and $).")
        self.conn, self.stage, self._now = connection, stage, now
        self.label = f"stage @{stage}"

    # ------------------------------------------------------------------ statements

    def _run(self, sql: str) -> list[tuple]:
        cursor = self.conn.cursor()
        try:
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()

    @staticmethod
    def _url(path: Path | str, *, directory: bool = False) -> str:
        text = str(path)
        if "'" in text or "\n" in text:
            raise ValueError(f"A path with a quote or a line break cannot be used: {text!r}")
        return f"'file://{text}{'/' if directory and not text.endswith('/') else ''}'"

    def _exists(self, prefix: str) -> bool:
        return bool(self._run(f"list @{self.stage}/{prefix}"))

    def _get(self, remote: str, dest_dir: Path) -> None:
        dest_dir.mkdir(parents=True, exist_ok=True)
        self._run(f"get @{self.stage}/{remote} {self._url(dest_dir, directory=True)}")

    def _put(self, local: Path, remote_dir: str, *, overwrite: bool) -> None:
        self._run(
            f"put {self._url(local)} @{self.stage}/{remote_dir.rstrip('/')}/ "
            f"auto_compress=false overwrite={'true' if overwrite else 'false'}"
        )

    # ------------------------------------------------------------------ the store

    def skill_path(self, skill: Skill) -> str:
        return f"@{self.stage}/{skill.folder}"

    def index(self) -> list[Skill]:
        if not self._exists(INDEX):
            return []
        with tempfile.TemporaryDirectory() as scratch:
            self._get(INDEX, Path(scratch))
            return _parse_index((Path(scratch) / "index.json").read_text(encoding="utf-8"))

    def read_skill_md(self, skill: Skill) -> str:
        with tempfile.TemporaryDirectory() as scratch:
            self._get(f"{skill.folder}/SKILL.md", Path(scratch))
            return (Path(scratch) / "SKILL.md").read_text(encoding="utf-8")

    def list_files(self, skill: Skill) -> list[str]:
        """Every file of the version's folder on the stage, as a path from the folder: the agent
        mounts the whole folder, so a file that is not in the index must be seen."""
        marker = f"/{skill.folder}/"
        names = (str(row[0]) for row in self._run(f"list @{self.stage}/{skill.folder}/"))
        return sorted(name.split(marker, 1)[1] for name in names if marker in name)

    def fetch(self, skill: Skill, dest: Path) -> None:
        for rel in skill.files:
            parent = Path(rel).parent.as_posix()
            self._get(f"{skill.folder}/{rel}", dest / parent if parent != "." else dest)

    def publish(self, folder: Path, report: Report, *, force: bool = False) -> Skill:
        skill = _stamped(report, self._now)
        if self._exists(f"{skill.folder}/") and not force:
            raise PublishError(f"{skill.id} {skill.version} is published; bump the version.")
        for rel in skill.files:
            parent = Path(rel).parent.as_posix()
            remote = skill.folder if parent == "." else f"{skill.folder}/{parent}"
            self._put(folder / rel, remote, overwrite=force)
        with tempfile.TemporaryDirectory() as scratch:
            index = Path(scratch) / "index.json"
            index.write_text(_index_text(_entries(self.index(), skill)), encoding="utf-8")
            self._put(index, "skills", overwrite=True)
        return skill
