"""Filled brief persist — ``brief.json`` + rendered ``BRIEF.md``."""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from engine.catalog import AppType, Question
from engine.paths import OUT_DIR

BRIEF_JSON = "brief.json"
BRIEF_MD = "BRIEF.md"
SKETCH_DIR = "sketches"
APP_FILE = "streamlit_app.py"
USER_BRIEF_KEY = "user_brief"
GROUNDING_KINDS = frozenset({"semantic_view", "tables"})
_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(name: str) -> str:
    text = _SLUG_RE.sub("-", name.strip().lower()).strip("-")
    return text or "app"


def unique_slug(base: str, out_dir: Path | None = None) -> str:
    candidate = base or "app"
    n = 2
    while (slug_dir(candidate, out_dir) / BRIEF_JSON).is_file():
        candidate = f"{base}-{n}"
        n += 1
    return candidate


def filled_app_name(payload: dict[str, Any] | None, *, fallback: str) -> str:
    if payload:
        name = str(payload.get("app_name") or "").strip()
        if name:
            return name
    return fallback


def partition_questions(
    questions: tuple[Question, ...] | list[Question],
) -> tuple[list[Question], list[Question], list[Question]]:
    """Split type questions into data / inferred findings / still asked."""
    items = list(questions)
    grounding = [q for q in items if q.kind in GROUNDING_KINDS]
    rest = [q for q in items if q.kind not in GROUNDING_KINDS]
    if not grounding and rest:
        grounding = [rest[0]]
        rest = rest[1:]
    found = [q for q in rest if q.infer]
    asked = [q for q in rest if not q.infer]
    return grounding, found, asked


def slug_dir(slug: str, out_dir: Path | None = None) -> Path:
    return (out_dir or OUT_DIR) / slug


def list_saved_briefs(out_dir: Path | None = None) -> list[Path]:
    root = out_dir or OUT_DIR
    if not root.is_dir():
        return []
    found = [p.parent for p in root.glob(f"*/{BRIEF_JSON}")]
    return sorted(found, key=lambda p: p.stat().st_mtime, reverse=True)


def load_filled(slug: str, out_dir: Path | None = None) -> dict[str, Any] | None:
    path = slug_dir(slug, out_dir) / BRIEF_JSON
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else None


def answers_complete(app_type: AppType, answers: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for question in app_type.questions:
        if not question.required:
            continue
        if not _has_answer(question, answers.get(question.id)):
            missing.append(question.id)
    return missing


def _has_answer(question: Question, value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple)):
        return any(str(item).strip() for item in value)
    return bool(value)


def list_sketches(slug: str, out_dir: Path | None = None) -> list[Path]:
    folder = slug_dir(slug, out_dir) / SKETCH_DIR
    if not folder.is_dir():
        return []
    files: list[Path] = []
    for path in sorted(folder.iterdir()):
        if path.is_file() and not path.name.startswith("."):
            files.append(path)
    return files


def render_brief_md(
    app_type: AppType,
    answers: dict[str, Any],
    *,
    sketches: list[Path] | None = None,
    app_name: str | None = None,
) -> str:
    title = (app_name or "").strip() or app_type.name
    lines = [
        f"# {title}",
        "",
        f"Type: **{app_type.name}** · `{app_type.id}` · version `{app_type.version}`",
        f"Users: {', '.join(app_type.users) or '—'}",
        "",
        "## Context",
        "",
        app_type.brief_context or "_(none)_",
        "",
        "## What this allows",
        "",
    ]
    lines.extend(f"- {item}" for item in app_type.enables)
    if not app_type.enables:
        lines.append("- _(none)_")
    lines.extend(["", "## What this does not do", ""])
    lines.extend(f"- {item}" for item in app_type.does_not)
    if not app_type.does_not:
        lines.append("- _(none)_")
    owner = str(answers.get(USER_BRIEF_KEY) or "").strip()
    lines.extend(
        [
            "",
            "## What the owner wants",
            "",
            owner or "_(none)_",
            "",
            "## Answers",
            "",
        ]
    )
    for question in app_type.questions:
        value = answers.get(question.id)
        rendered = _format_answer(value)
        req = "required" if question.required else "optional"
        lines.append(f"### {question.prompt}")
        lines.append("")
        lines.append(f"_{req} · `{question.id}`_")
        lines.append("")
        lines.append(rendered)
        lines.append("")
    lines.extend(["## User sketches", ""])
    if sketches:
        for path in sketches:
            lines.append(f"- `{path.as_posix()}`")
    else:
        lines.append("- _(none)_")
    lines.append("")
    return "\n".join(lines)


def _format_answer(value: Any) -> str:
    if value is None or value == "":
        return "_(not answered)_"
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
        if not items:
            return "_(not answered)_"
        return "\n".join(f"- {item}" for item in items)
    return str(value).strip()


def save_filled(
    slug: str,
    app_type: AppType,
    answers: dict[str, Any],
    *,
    app_name: str | None = None,
    out_dir: Path | None = None,
) -> Path:
    dest = slug_dir(slug, out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    (dest / SKETCH_DIR).mkdir(parents=True, exist_ok=True)
    sketches = list_sketches(slug, out_dir)
    existing = load_filled(slug, out_dir) or {}
    name = filled_app_name(
        {"app_name": app_name} if app_name else existing,
        fallback=slug,
    )
    payload = {
        "type_id": app_type.id,
        "type_version": app_type.version,
        "app_name": name,
        "answers": answers,
        "sketches": [str(p.relative_to(dest)) for p in sketches],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    (dest / BRIEF_JSON).write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    (dest / BRIEF_MD).write_text(
        render_brief_md(app_type, answers, sketches=sketches, app_name=name),
        encoding="utf-8",
    )
    return dest


def app_exists(slug: str, out_dir: Path | None = None) -> bool:
    return (slug_dir(slug, out_dir) / APP_FILE).is_file()


def delete_filled(slug: str, out_dir: Path | None = None) -> Path:
    root = (out_dir or OUT_DIR).resolve()
    dest = slug_dir(slug, out_dir).resolve()
    if dest == root or not dest.is_relative_to(root):
        raise ValueError("Refusing to delete outside the apps folder.")
    if dest.is_dir():
        shutil.rmtree(dest)
    return dest
