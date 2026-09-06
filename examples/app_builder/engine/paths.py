"""Filesystem locations for the App Builder example."""

from __future__ import annotations

from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = APP_ROOT.parents[1]
TYPES_DIR = APP_ROOT / "types"
FIXTURES_DIR = APP_ROOT / "fixtures"
WORKSPACE_DIR = REPO_ROOT / "examples" / "workspaces" / "app_builder"
OUT_DIR = APP_ROOT / "out"

PREVIEW_PORT = 8513
