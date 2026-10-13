"""Filesystem locations for the App Builder example."""

from __future__ import annotations

import os
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = APP_ROOT.parents[1]
TYPES_DIR = APP_ROOT / "types"
FIXTURES_DIR = APP_ROOT / "fixtures"
# APP_BUILDER_HOME moves both folders the app writes to (a scratch run, a test).
_HOME = os.environ.get("APP_BUILDER_HOME")
_WORKSPACES = REPO_ROOT / "examples" / "workspaces" / "app_builder"
WORKSPACE_DIR = Path(_HOME) / "workspace" if _HOME else _WORKSPACES
OUT_DIR = Path(_HOME) / "out" if _HOME else APP_ROOT / "out"

PREVIEW_PORT = 8513
