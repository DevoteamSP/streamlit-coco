"""Load and filter the file-backed product backlog."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from utils.paths import EPICS_DIR, RELEASES_DIR, TICKETS_DIR

STATUSES = ("backlog", "ready", "in_progress", "blocked", "done")
PRIORITIES = ("critical", "high", "medium", "low")
TYPES = ("feature", "bug", "chore", "spike")

STATUS_BADGE = {
    "backlog": ("gray", "Backlog"),
    "ready": ("blue", "Ready"),
    "in_progress": ("orange", "In progress"),
    "blocked": ("red", "Blocked"),
    "done": ("green", "Done"),
}

PRIORITY_BADGE = {
    "critical": ("red", "Critical"),
    "high": ("orange", "High"),
    "medium": ("blue", "Medium"),
    "low": ("gray", "Low"),
}


@dataclass(frozen=True)
class Epic:
    id: str
    title: str
    status: str
    owner: str
    target_release: str
    summary: str
    path: Path

    @classmethod
    def from_dict(cls, data: dict[str, Any], path: Path) -> Epic:
        return cls(
            id=str(data["id"]),
            title=str(data.get("title") or data["id"]),
            status=str(data.get("status") or "backlog"),
            owner=str(data.get("owner") or "unassigned"),
            target_release=str(data.get("target_release") or ""),
            summary=str(data.get("summary") or ""),
            path=path,
        )


@dataclass(frozen=True)
class Ticket:
    id: str
    epic_id: str
    title: str
    type: str
    priority: str
    status: str
    points: int
    owner: str
    description: str
    path: Path

    @classmethod
    def from_dict(cls, data: dict[str, Any], path: Path) -> Ticket:
        return cls(
            id=str(data["id"]),
            epic_id=str(data.get("epic_id") or ""),
            title=str(data.get("title") or data["id"]),
            type=str(data.get("type") or "feature"),
            priority=str(data.get("priority") or "medium"),
            status=str(data.get("status") or "backlog"),
            points=int(data.get("points") or 0),
            owner=str(data.get("owner") or "unassigned"),
            description=str(data.get("description") or ""),
            path=path,
        )


@dataclass(frozen=True)
class Release:
    version: str
    title: str
    status: str
    date: str
    ticket_ids: tuple[str, ...]
    body: str
    path: Path


@dataclass(frozen=True)
class Backlog:
    epics: tuple[Epic, ...]
    tickets: tuple[Ticket, ...]
    releases: tuple[Release, ...]

    def epic(self, epic_id: str) -> Epic | None:
        return next((e for e in self.epics if e.id == epic_id), None)

    def ticket(self, ticket_id: str) -> Ticket | None:
        return next((t for t in self.tickets if t.id == ticket_id), None)

    def release(self, version: str) -> Release | None:
        return next((r for r in self.releases if r.version == version), None)

    def tickets_for_epic(self, epic_id: str) -> list[Ticket]:
        return [t for t in self.tickets if t.epic_id == epic_id]

    def tickets_for_release(self, version: str) -> list[Ticket]:
        rel = self.release(version)
        if not rel:
            return []
        by_id = {t.id: t for t in self.tickets}
        return [by_id[i] for i in rel.ticket_ids if i in by_id]

    def kpis(self) -> dict[str, int]:
        counts = {s: 0 for s in STATUSES}
        for t in self.tickets:
            counts[t.status] = counts.get(t.status, 0) + 1
        return {
            "open": counts["backlog"]
            + counts["ready"]
            + counts["in_progress"]
            + counts["blocked"],
            "in_progress": counts["in_progress"],
            "blocked": counts["blocked"],
            "done": counts["done"],
            "points_open": sum(t.points for t in self.tickets if t.status != "done"),
        }


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected object in {path}")
    return data


def _parse_front_matter(text: str) -> tuple[dict[str, Any], str]:
    """Minimal YAML-ish front matter: `key: value` and `tickets: [a, b]`."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta: dict[str, Any] = {}
    for line in parts[1].strip().splitlines():
        if ":" not in line:
            continue
        key, raw = line.split(":", 1)
        key = key.strip()
        raw = raw.strip()
        if raw.startswith("[") and raw.endswith("]"):
            inner = raw[1:-1].strip()
            meta[key] = [p.strip().strip("\"'") for p in inner.split(",") if p.strip()]
        else:
            meta[key] = raw.strip("\"'")
    return meta, parts[2].lstrip("\n")


def _parse_release(path: Path) -> Release:
    meta, body = _parse_front_matter(path.read_text(encoding="utf-8"))
    version = str(meta.get("version") or path.stem)
    tickets = meta.get("tickets") or []
    if not isinstance(tickets, list):
        tickets = re.findall(r"T-\d+", str(tickets))
    return Release(
        version=version,
        title=str(meta.get("title") or version),
        status=str(meta.get("status") or "draft"),
        date=str(meta.get("date") or ""),
        ticket_ids=tuple(str(t) for t in tickets),
        body=body,
        path=path,
    )


def load_backlog() -> Backlog:
    epics = tuple(
        sorted(
            (Epic.from_dict(_load_json(p), p) for p in EPICS_DIR.glob("*.json")),
            key=lambda e: e.id,
        )
    )
    tickets = tuple(
        sorted(
            (Ticket.from_dict(_load_json(p), p) for p in TICKETS_DIR.glob("*.json")),
            key=lambda t: t.id,
        )
    )
    releases = tuple(
        sorted(
            (_parse_release(p) for p in RELEASES_DIR.glob("*.md")),
            key=lambda r: r.version,
            reverse=True,
        )
    )
    return Backlog(epics=epics, tickets=tickets, releases=releases)


def backlog_mtime_key() -> tuple[float, ...]:
    paths = [
        *EPICS_DIR.glob("*.json"),
        *TICKETS_DIR.glob("*.json"),
        *RELEASES_DIR.glob("*.md"),
    ]
    return tuple(sorted(p.stat().st_mtime for p in paths)) if paths else (0.0,)


def filter_tickets(
    backlog: Backlog,
    *,
    status: str | None = None,
    priority: str | None = None,
    epic_id: str | None = None,
    query: str = "",
) -> list[Ticket]:
    q = query.strip().lower()
    out: list[Ticket] = []
    for t in backlog.tickets:
        if status and status != "all" and t.status != status:
            continue
        if priority and priority != "all" and t.priority != priority:
            continue
        if epic_id and epic_id != "all" and t.epic_id != epic_id:
            continue
        if q and q not in t.title.lower() and q not in t.id.lower():
            continue
        out.append(t)
    return out


def tickets_as_rows(tickets: list[Ticket]) -> list[dict[str, Any]]:
    return [
        {
            "id": t.id,
            "title": t.title,
            "epic": t.epic_id,
            "type": t.type,
            "priority": t.priority,
            "status": t.status,
            "points": t.points,
            "owner": t.owner,
        }
        for t in tickets
    ]
