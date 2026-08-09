"""Smoke tests for the Product Backlog Desk example data layer."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "examples" / "backlog_desk"
sys.path.insert(0, str(APP))

from utils.backlog import filter_tickets, load_backlog  # noqa: E402
from utils.skills import SKILLS, skill_prompt  # noqa: E402


def test_load_backlog_seed_data() -> None:
    backlog = load_backlog()
    assert len(backlog.epics) >= 3
    assert len(backlog.tickets) >= 8
    assert backlog.release("0.2.0") is not None
    kpis = backlog.kpis()
    assert kpis["blocked"] >= 1
    assert kpis["open"] >= 1


def test_filter_and_skills() -> None:
    backlog = load_backlog()
    blocked = filter_tickets(backlog, status="blocked")
    assert any(t.id == "T-045" for t in blocked)
    skill = next(s for s in SKILLS if s.name == "check-dod")
    prompt = skill_prompt(skill, ticket_id="T-042")
    assert "T-042" in prompt
    assert "dod.md" in prompt
