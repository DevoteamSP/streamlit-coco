#!/usr/bin/env python3
"""pip-audit every uv.lock of the repository, not only the root one.

usage: python scripts/audit_locks.py [lock ...]      (default: every tracked uv.lock but the root)

`make audit` audits the root environment (`pip-audit --skip-editable`); this script covers the
examples that have a lock of their own (examples/app_builder/uv.lock), which the root audit
cannot see and which Dependabot reports separately. Each lock is exported without hashes and
without the project itself, then audited with the pip-audit of the current environment.

Exit status: 0 when every lock is clean, 1 when one has a known vulnerability, 2 when a lock
could not be exported or audited (the audit did not run).
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def tracked_locks() -> list[Path]:
    """Every uv.lock under version control except the root one (`make audit` has it)."""
    out = subprocess.run(
        ["git", "ls-files", "*uv.lock"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.split()
    return [ROOT / p for p in out if p != "uv.lock"]


def audit_lock(lock: Path) -> tuple[int, str]:
    """(status, report) for one lock: 0 clean, 1 vulnerable, 2 could not run."""
    with tempfile.TemporaryDirectory() as tmp:
        requirements = Path(tmp) / "requirements.txt"
        export = subprocess.run(
            [
                "uv",
                "export",
                "--frozen",
                "--no-emit-project",
                "--no-emit-package",
                "streamlit-coco",
                "--no-hashes",
                "--directory",
                str(lock.parent),
                "-o",
                str(requirements),
            ],
            capture_output=True,
            text=True,
        )
        if export.returncode != 0:
            return 2, f"uv export failed: {export.stderr.strip()[-300:]}"
        audit = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip_audit",
                "--no-deps",
                "--disable-pip",
                "-r",
                str(requirements),
            ],
            capture_output=True,
            text=True,
        )
    body = "\n".join(
        line
        for line in (audit.stdout + audit.stderr).splitlines()
        if not line.startswith("WARNING:pip_audit")
    )
    if audit.returncode == 0:
        return 0, body.strip()
    if "known vulnerabilit" in body:
        return 1, body.strip()
    return 2, body.strip()[-400:]


def main(argv: list[str]) -> int:
    locks = [Path(a).resolve() for a in argv] or tracked_locks()
    if not locks:
        print("No other uv.lock to audit.")
        return 0
    worst = 0
    for lock in locks:
        status, report = audit_lock(lock)
        rel = lock.relative_to(ROOT) if lock.is_relative_to(ROOT) else lock
        label = {0: "clean", 1: "VULNERABLE", 2: "NOT AUDITED"}[status]
        print(f"{rel}: {label}")
        if status:
            print("\n".join(f"    {line}" for line in report.splitlines()[:40]))
        worst = max(worst, status)
    return worst


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
