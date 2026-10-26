"""A skill of the shop: a folder with a SKILL.md, published as skills/<id>/<version>/.

Pure Python: no Streamlit, no Snowflake. `validate_folder` is the gate of `make publish-skill`: a
folder that does not pass is never uploaded. A skill is instructions (and sometimes code) the agent
follows in its sandbox, so what may be published is narrow on purpose: safe names, a short list of
file types, size limits, no links, no obvious credentials.
"""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
SEGMENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
ALLOWED_SUFFIXES = frozenset(
    {".md", ".txt", ".py", ".sh", ".sql", ".json", ".yaml", ".yml", ".csv", ".html", ".css"}
    | {".js", ".png", ".jpg", ".jpeg", ".svg"}
)
BINARY_SUFFIXES = frozenset({".png", ".jpg", ".jpeg"})
MAX_FILES, MAX_FILE_BYTES, MAX_TOTAL_BYTES, MAX_DEPTH = 50, 1_000_000, 5_000_000, 4
MAX_DESCRIPTION = 400

# Obvious secrets only: a net, not a guarantee. A reviewer still reads the folder.
SECRET_PATTERNS = (
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "a private key"),
    (
        re.compile(
            r"(?i)\b(api[_-]?key|secret|token|password|passwd)\b\s*[:=]\s*['\"]?[A-Za-z0-9/+_.-]{16,}"
        ),
        "a credential-like value",
    ),
)


@dataclass(frozen=True)
class Skill:
    """One published version of a skill, as the index of the stage lists it."""

    id: str
    version: str
    title: str
    description: str
    pack: str = ""
    icon: str = ""
    run_prompt: str = ""
    sha256: str = ""
    has_scripts: bool = False
    files: tuple[str, ...] = field(default_factory=tuple)
    published_at: str = ""

    def to_json(self) -> dict:
        return {**asdict(self), "files": list(self.files)}

    @classmethod
    def from_json(cls, data: dict) -> Skill:
        known = {f for f in cls.__dataclass_fields__}  # tolerate a newer index
        values = {k: v for k, v in data.items() if k in known}
        values["files"] = tuple(values.get("files") or ())
        return cls(**values)

    @property
    def folder(self) -> str:
        return f"skills/{self.id}/{self.version}"


@dataclass
class Report:
    """What `validate_folder` found. `skill` is set (without `published_at`) when there is no
    error."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    skill: Skill | None = None

    @property
    def ok(self) -> bool:
        return not self.errors and self.skill is not None


def semver_key(version: str) -> tuple[int, int, int]:
    major, minor, patch = (int(part) for part in version.split("."))
    return major, minor, patch


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    """The `key: value` lines between the two `---` lines, and the rest. Single-line values (a
    continuation line indented under a key is joined to it); quotes around a value are dropped."""
    match = re.match(r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|\Z)(.*)\Z", text, re.DOTALL)
    if not match:
        return {}, text
    meta: dict[str, str] = {}
    key = None
    for line in match.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[0] in " \t" and key:
            meta[key] = f"{meta[key]} {line.strip()}".strip()
            continue
        name, sep, value = line.partition(":")
        if not sep:
            continue
        key = name.strip().lower()
        meta[key] = value.strip().strip("'\"")
    return meta, match.group(2)


def folder_hash(root: Path, files: list[str] | tuple[str, ...]) -> str:
    """sha256 over the sorted (path, content hash) of the files: the same folder, the same hash."""
    digest = hashlib.sha256()
    for rel in sorted(files):
        content = hashlib.sha256((root / rel).read_bytes()).hexdigest()
        digest.update(f"{rel}\0{content}\n".encode())
    return digest.hexdigest()


def _walk(folder: Path, errors: list[str]) -> list[str]:
    """Relative paths of the files, in order; links and unsafe names are errors."""
    files: list[str] = []
    for dirpath, dirnames, filenames in os.walk(folder, followlinks=False):
        here = Path(dirpath)
        for name in [*dirnames, *filenames]:
            path = here / name
            rel = path.relative_to(folder).as_posix()
            if path.is_symlink():
                errors.append(f"{rel}: a link is not allowed.")
            elif not SEGMENT_RE.match(name):
                errors.append(f"{rel}: the name must be letters, digits, `.`, `_` or `-`.")
        dirnames[:] = sorted(d for d in dirnames if not (here / d).is_symlink())
        for name in sorted(filenames):
            path = here / name
            if not path.is_symlink():
                files.append(path.relative_to(folder).as_posix())
    return files


def validate_folder(folder: str | os.PathLike[str]) -> Report:
    folder = Path(folder)
    report = Report()
    if not folder.is_dir():
        report.errors.append(f"{folder}: not a folder.")
        return report
    files = _walk(folder, report.errors)
    if "SKILL.md" not in files:
        report.errors.append("SKILL.md is missing at the top of the folder.")
    if len(files) > MAX_FILES:
        report.errors.append(f"{len(files)} files: at most {MAX_FILES}.")
    total = 0
    for rel in files:
        path = folder / rel
        if len(Path(rel).parts) > MAX_DEPTH:
            report.errors.append(f"{rel}: more than {MAX_DEPTH} levels deep.")
        suffix = path.suffix.lower()
        if suffix not in ALLOWED_SUFFIXES:
            report.errors.append(f"{rel}: this type of file is not allowed ({suffix or 'none'}).")
            continue
        size = path.stat().st_size
        total += size
        if size > MAX_FILE_BYTES:
            report.errors.append(f"{rel}: {size} bytes, at most {MAX_FILE_BYTES}.")
        if suffix not in BINARY_SUFFIXES and size <= MAX_FILE_BYTES:
            text = path.read_text(encoding="utf-8", errors="replace")
            for pattern, what in SECRET_PATTERNS:
                if pattern.search(text):
                    report.errors.append(f"{rel}: looks like it holds {what}.")
    if total > MAX_TOTAL_BYTES:
        report.errors.append(f"{total} bytes in all: at most {MAX_TOTAL_BYTES}.")
    if report.errors:
        return report

    meta, _ = parse_front_matter((folder / "SKILL.md").read_text(encoding="utf-8"))
    skill_id, version = meta.get("name", ""), meta.get("version", "")
    description = meta.get("description", "")
    if not ID_RE.match(skill_id):
        report.errors.append(
            "front matter `name`: lowercase letters, digits and `-`, at most 63 characters."
        )
    if not VERSION_RE.match(version):
        report.errors.append("front matter `version`: three numbers, like 1.0.0.")
    if not description:
        report.errors.append("front matter `description` is missing.")
    elif len(description) > MAX_DESCRIPTION:
        report.errors.append(f"front matter `description`: at most {MAX_DESCRIPTION} characters.")
    if report.errors:
        return report

    scripts = [rel for rel in files if Path(rel).parts[0] == "scripts"]
    if scripts:
        report.warnings.append(
            "carries code that the agent may run (each run asks first): " + ", ".join(scripts)
        )
    report.skill = Skill(
        id=skill_id,
        version=version,
        title=meta.get("title") or skill_id,
        description=description,
        pack=meta.get("pack", ""),
        icon=meta.get("icon", ""),
        run_prompt=meta.get("run_prompt", ""),
        sha256=folder_hash(folder, files),
        has_scripts=bool(scripts),
        files=tuple(files),
    )
    return report
