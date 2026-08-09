"""Resolve paths for the Product Backlog Desk demo."""

from __future__ import annotations

from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = APP_ROOT / "data"
EPICS_DIR = DATA_DIR / "epics"
TICKETS_DIR = DATA_DIR / "tickets"
RELEASES_DIR = DATA_DIR / "releases"
POLICIES_DIR = DATA_DIR / "policies"
DOD_PATH = POLICIES_DIR / "dod.md"
