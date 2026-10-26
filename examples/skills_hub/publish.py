"""Publish a skill folder to the shop's stage: see shop/cli.py. Run it with `make publish-skill`."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from shop.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
