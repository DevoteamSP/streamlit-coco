"""Skill prompts for Product Backlog Desk (injected into CoCo)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Skill:
    name: str
    label: str
    description: str


SKILLS: tuple[Skill, ...] = (
    Skill(
        "summarize-sprint",
        "Summarize sprint",
        "Count open / in-progress / blocked tickets and list highlights + risks.",
    ),
    Skill(
        "draft-release-notes",
        "Draft release notes",
        "Write or update release notes markdown from tickets in a target release.",
    ),
    Skill(
        "propose-ticket-update",
        "Propose ticket update",
        "Suggest a JSON status/priority patch for a ticket (Edit requires approval).",
    ),
    Skill(
        "check-dod",
        "Check definition of done",
        "Compare a ticket against data/policies/dod.md and list gaps.",
    ),
)


def skill_by_name(name: str) -> Skill | None:
    return next((s for s in SKILLS if s.name == name), None)


def skill_prompt(
    skill: Skill,
    *,
    ticket_id: str | None = None,
    epic_id: str | None = None,
    release: str | None = None,
) -> str:
    ctx_lines = [
        "You are assisting with a file-backed product backlog under `data/`.",
        "Use Read / Glob / Grep to inspect `data/epics`, `data/tickets`, `data/releases`, "
        "and `data/policies`. Prefer citing file paths.",
        "Tickets and epics are JSON files. Releases are Markdown with YAML-ish front matter.",
        "Do not invent tickets that are not on disk.",
        "Edit and Write require human approval — propose changes clearly.",
    ]
    if ticket_id:
        ctx_lines.append(f"Focus ticket: `{ticket_id}` (file `data/tickets/{ticket_id}.json`).")
    if epic_id:
        ctx_lines.append(f"Focus epic: `{epic_id}` (file `data/epics/{epic_id}.json`).")
    if release:
        ctx_lines.append(f"Focus release: `{release}` (file `data/releases/{release}.md`).")

    if skill.name == "summarize-sprint":
        task = (
            "Summarize the current sprint from all tickets under `data/tickets/`.\n"
            "Return:\n"
            "1. Counts: backlog, ready, in_progress, blocked, done\n"
            "2. Top highlights (3 bullets)\n"
            "3. Risks / blockers (bullet list with ticket ids)\n"
            "4. Suggested focus for the next day\n"
            "Keep it concise for a standup."
        )
    elif skill.name == "draft-release-notes":
        target = release or "0.2.0"
        task = (
            f"Draft release notes for version `{target}`.\n"
            f"Read `data/releases/{target}.md` if it exists and the ticket JSON files "
            "listed in its front matter (or infer from epic target_release).\n"
            f"Write updated notes to `data/releases/{target}.md` using Write/Edit.\n"
            "Include: title, highlights, ticket list with one-line summaries, known gaps.\n"
            "Preserve front matter keys: version, title, status, date, tickets."
        )
    elif skill.name == "propose-ticket-update":
        tid = ticket_id or "T-042"
        task = (
            f"Inspect `data/tickets/{tid}.json` and propose a small, justified update "
            "(status and/or priority only unless clearly needed).\n"
            "Explain the rationale, then apply the Edit. Wait for approval."
        )
    elif skill.name == "check-dod":
        tid = ticket_id or "T-042"
        task = (
            f"Read `data/policies/dod.md` and `data/tickets/{tid}.json`.\n"
            "List each DoD criterion as PASS / FAIL / UNKNOWN with a one-line reason.\n"
            "End with a short recommendation (ready to ship? what is missing?)."
        )
    else:
        task = skill.description

    return "\n".join([*ctx_lines, "", f"## Task: {skill.label}", task])
