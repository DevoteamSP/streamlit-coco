"""Load App Builder type documents from ``types/*/type.json``."""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from engine.paths import TYPES_DIR
from engine.skills import SHARED_SKILL_ID

_TYPE_ID = re.compile(r"^[a-z][a-z0-9-]{0,62}$")
GROUNDING_KINDS = ("tabular", "semantic_view", "documents", "urls")


@dataclass(frozen=True)
class Question:
    id: str
    prompt: str
    kind: str
    required: bool = False
    options: tuple[str, ...] = ()
    help: str = ""
    infer: str | None = None


@dataclass(frozen=True)
class AppType:
    id: str
    icon: str
    name: str
    users: tuple[str, ...]
    needs: tuple[str, ...]
    brief_context: str
    enables: tuple[str, ...]
    does_not: tuple[str, ...]
    questions: tuple[Question, ...]
    topics: tuple[str, ...] = ()
    needs_snowflake: bool = False
    screenshot: Path | None = None
    demo_fixture: str | None = None
    coming_soon: bool = False
    guidelines_skill: str | None = None
    grounding_kind: str = "tabular"
    ships_copilot: bool = False
    version: str = "1"
    path: Path = field(default_factory=Path)

    @property
    def material_icon(self) -> str:
        name = self.icon.strip(":") or "apps"
        if name.startswith("material/"):
            name = name.split("/", 1)[1]
        return f":material/{name}:"

    @property
    def grounding_label(self) -> str:
        return {
            "tabular": "Files",
            "semantic_view": "Semantic view",
            "documents": "Documents",
            "urls": "URLs",
        }.get(self.grounding_kind, self.grounding_kind.replace("_", " ").title())


def _as_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    return tuple(str(item) for item in value)


def _parse_question(raw: dict[str, Any]) -> Question:
    options = raw.get("options") or []
    return Question(
        id=str(raw["id"]),
        prompt=str(raw["prompt"]),
        kind=str(raw.get("kind") or "text"),
        required=bool(raw.get("required")),
        options=tuple(str(item) for item in options),
        help=str(raw.get("help") or ""),
        infer=(str(raw["infer"]) if raw.get("infer") else None),
    )


def load_type(path: Path) -> AppType:
    data = json.loads(path.read_text(encoding="utf-8"))
    folder = path.parent
    shot_name = data.get("screenshot")
    shot: Path | None = None
    if shot_name:
        shot = (folder / str(shot_name)).resolve()
        if not shot.is_file():
            shot = None
    brief = data.get("brief") or {}
    questions = tuple(_parse_question(q) for q in (brief.get("questions") or []))
    return AppType(
        id=str(data["id"]),
        icon=str(data.get("icon") or "apps"),
        name=str(data["name"]),
        users=_as_tuple(data.get("users")),
        needs=_as_tuple(data.get("needs")),
        brief_context=str(brief.get("context") or "").strip(),
        enables=_as_tuple(brief.get("enables")),
        does_not=_as_tuple(brief.get("does_not")),
        questions=questions,
        topics=_as_tuple(data.get("topics")),
        needs_snowflake=bool(data.get("needs_snowflake")),
        screenshot=shot,
        demo_fixture=data.get("demo_fixture") or None,
        coming_soon=bool(data.get("coming_soon")),
        guidelines_skill=data.get("guidelines_skill") or None,
        grounding_kind=str(data.get("grounding_kind") or "tabular"),
        ships_copilot=bool(data.get("ships_copilot")),
        version=str(data.get("version") or "1"),
        path=folder,
    )


def load_catalog(types_dir: Path | None = None) -> list[AppType]:
    root = types_dir or TYPES_DIR
    types: list[AppType] = []
    if not root.is_dir():
        return types
    for type_file in sorted(root.glob("*/type.json")):
        types.append(load_type(type_file))
    return types


def get_type(type_id: str, types_dir: Path | None = None) -> AppType | None:
    for item in load_catalog(types_dir):
        if item.id == type_id:
            return item
    return None


def catalog_topics(types: list[AppType] | None = None) -> list[str]:
    items = types if types is not None else load_catalog()
    found: set[str] = set()
    for app_type in items:
        found.update(app_type.topics)
    return sorted(found)


def filter_by_topics(
    types: list[AppType],
    selected: list[str] | tuple[str, ...] | None,
) -> list[AppType]:
    if not selected:
        return list(types)
    wanted = set(selected)
    return [item for item in types if wanted.intersection(item.topics)]


def type_dir(type_id: str, types_dir: Path | None = None) -> Path:
    return (types_dir or TYPES_DIR) / type_id


def load_type_raw(type_id: str, types_dir: Path | None = None) -> dict[str, Any]:
    path = type_dir(type_id, types_dir) / "type.json"
    if not path.is_file():
        raise FileNotFoundError(f"No type.json for `{type_id}`")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"type.json for `{type_id}` is not an object")
    return data


def new_type_template(type_id: str) -> dict[str, Any]:
    return {
        "id": type_id,
        "version": "1",
        "icon": "apps",
        "name": "New app type",
        "users": ["Domain owner"],
        "screenshot": None,
        "needs": [],
        "needs_snowflake": False,
        "topics": ["Local"],
        "demo_fixture": None,
        "coming_soon": False,
        "guidelines_skill": None,
        "grounding_kind": "tabular",
        "ships_copilot": False,
        "brief": {
            "context": "",
            "enables": [],
            "does_not": [],
            "questions": [
                {
                    "id": "source",
                    "prompt": "What should this app use?",
                    "kind": "text",
                    "required": True,
                }
            ],
        },
    }


def save_type_raw(
    data: dict[str, Any],
    types_dir: Path | None = None,
    *,
    previous_id: str | None = None,
) -> Path:
    type_id = str(data.get("id") or "").strip()
    if type_id == SHARED_SKILL_ID:
        raise ValueError(
            f"`{SHARED_SKILL_ID}` is reserved for the shared skill under types/{SHARED_SKILL_ID}/."
        )
    if not _TYPE_ID.match(type_id):
        raise ValueError(
            "Type id must start with a letter and use only lowercase letters, numbers, and hyphens."
        )
    kind = str(data.get("grounding_kind") or "tabular")
    if kind not in GROUNDING_KINDS:
        raise ValueError(f"grounding_kind must be one of: {', '.join(GROUNDING_KINDS)}")
    data["id"] = type_id
    data["grounding_kind"] = kind
    root = types_dir or TYPES_DIR
    dest = root / type_id
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / "type.json"
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    load_type(path)
    if previous_id and previous_id != type_id:
        old = root / previous_id
        if old.is_dir() and old.resolve() != dest.resolve():
            shutil.rmtree(old)
    return path


def delete_type(type_id: str, types_dir: Path | None = None) -> None:
    if type_id == SHARED_SKILL_ID:
        raise ValueError(
            f"`{SHARED_SKILL_ID}` is reserved for the shared skill and cannot be deleted as a type."
        )
    folder = type_dir(type_id, types_dir)
    if not folder.is_dir():
        raise FileNotFoundError(f"No type folder `{type_id}`")
    shutil.rmtree(folder)
