#!/usr/bin/env python3
"""Collect daily adoption stats for streamlit-coco (PyPI + GitHub traffic).

Writes:
  doc-dev/metrics/snapshots/YYYY-MM-DD.json
  doc-dev/metrics/latest.json
  appends one line to doc-dev/metrics/history.jsonl

Requires: network, ``gh`` authenticated with push/admin on both traffic repos.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
METRICS_DIR = ROOT / "doc-dev" / "metrics"
SNAPSHOTS_DIR = METRICS_DIR / "snapshots"
HISTORY_PATH = METRICS_DIR / "history.jsonl"
LATEST_PATH = METRICS_DIR / "latest.json"
ROADMAP_PATH = ROOT / "doc" / "roadmap.md"

PACKAGE = "streamlit-coco"
REPOS = (
    "DevoteamSP/streamlit-coco",
    "lletourmy/streamlit-coco",
)
PYPISTATS_BASE = "https://pypistats.org/api/packages"


def _http_json(url: str, *, retries: int = 5) -> Any:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "streamlit-coco-adoption-stats/1.0"},
    )
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            last_exc = exc
            if exc.code not in (429, 500, 502, 503, 504) or attempt + 1 >= retries:
                raise
            # Respect Retry-After when present; otherwise exponential backoff.
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            try:
                delay = float(retry_after) if retry_after else 2.0**attempt
            except ValueError:
                delay = 2.0**attempt
            time.sleep(min(delay, 60.0))
        except urllib.error.URLError as exc:
            last_exc = exc
            if attempt + 1 >= retries:
                raise
            time.sleep(min(2.0**attempt, 60.0))
    assert last_exc is not None
    raise last_exc


def _gh_json(path: str) -> Any:
    proc = subprocess.run(
        ["gh", "api", path],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(f"gh api {path} failed: {err}")
    return json.loads(proc.stdout)


def collect_pypi() -> dict[str, Any]:
    recent = _http_json(f"{PYPISTATS_BASE}/{PACKAGE}/recent")
    out: dict[str, Any] = {
        "source": "pypistats.org",
        "package": PACKAGE,
        "recent": recent.get("data") or {},
        "url": f"https://pypistats.org/packages/{PACKAGE}",
    }
    # Overall series is optional; pypistats rate-limits aggressively.
    time.sleep(1.5)
    try:
        overall = _http_json(f"{PYPISTATS_BASE}/{PACKAGE}/overall?mirrors=false")
        days = overall.get("data") or []
        out["overall_without_mirrors"] = days
        out["overall_days"] = len(days)
    except (urllib.error.HTTPError, urllib.error.URLError) as exc:
        out["overall_without_mirrors"] = []
        out["overall_days"] = 0
        out["overall_error"] = str(exc)
    return out


def collect_repo(full_name: str) -> dict[str, Any]:
    meta = _gh_json(f"repos/{full_name}")
    out: dict[str, Any] = {
        "full_name": full_name,
        "html_url": meta.get("html_url"),
        "stargazers_count": meta.get("stargazers_count"),
        "forks_count": meta.get("forks_count"),
        "open_issues_count": meta.get("open_issues_count"),
        "subscribers_count": meta.get("subscribers_count"),
        "pushed_at": meta.get("pushed_at"),
    }
    for kind in ("views", "clones"):
        try:
            out[kind] = _gh_json(f"repos/{full_name}/traffic/{kind}")
        except RuntimeError as exc:
            out[kind] = {"error": str(exc)}
    for kind in ("paths", "referrers"):
        try:
            out[f"popular_{kind}"] = _gh_json(f"repos/{full_name}/traffic/popular/{kind}")
        except RuntimeError as exc:
            out[f"popular_{kind}"] = {"error": str(exc)}
    return out


def collect(as_of: date | None = None) -> dict[str, Any]:
    day = as_of or date.today()
    collected_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    pypi = collect_pypi()
    github = {name: collect_repo(name) for name in REPOS}
    devoteam = github.get("DevoteamSP/streamlit-coco") or {}
    return {
        "schema_version": 1,
        "date": day.isoformat(),
        "collected_at": collected_at,
        "pypi": pypi,
        "github": github,
        "summary": {
            "pypi_last_day": (pypi.get("recent") or {}).get("last_day"),
            "pypi_last_week": (pypi.get("recent") or {}).get("last_week"),
            "pypi_last_month": (pypi.get("recent") or {}).get("last_month"),
            "devoteam_stars": devoteam.get("stargazers_count"),
            "devoteam_views_14d": (devoteam.get("views") or {}).get("count"),
            "devoteam_views_uniques_14d": (devoteam.get("views") or {}).get("uniques"),
            "devoteam_clones_14d": (devoteam.get("clones") or {}).get("count"),
            "devoteam_clones_uniques_14d": (devoteam.get("clones") or {}).get("uniques"),
            "lletourmy_stars": (github.get("lletourmy/streamlit-coco") or {}).get(
                "stargazers_count"
            ),
            "lletourmy_views_14d": (
                (github.get("lletourmy/streamlit-coco") or {}).get("views") or {}
            ).get("count"),
            "lletourmy_clones_14d": (
                (github.get("lletourmy/streamlit-coco") or {}).get("clones") or {}
            ).get("count"),
        },
    }


def write_snapshot(payload: dict[str, Any], *, force: bool = False) -> Path:
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    path = SNAPSHOTS_DIR / f"{payload['date']}.json"
    if path.exists() and not force:
        raise FileExistsError(f"{path} already exists (pass --force to overwrite today's snapshot)")
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    LATEST_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    # Replace same-date line in history if force-rewriting.
    lines: list[str] = []
    if HISTORY_PATH.exists():
        for line in HISTORY_PATH.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                lines.append(line)
                continue
            if row.get("date") == payload["date"]:
                continue
            lines.append(line)
    slim = {
        "date": payload["date"],
        "collected_at": payload["collected_at"],
        **payload["summary"],
    }
    lines.append(json.dumps(slim, separators=(",", ":")))
    HISTORY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def format_summary(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    lines = [
        f"Adoption stats — {payload['date']} (UTC {payload['collected_at']})",
        "",
        "PyPI (pypistats.org/packages/streamlit-coco)",
        f"  last day / week / month: "
        f"{s.get('pypi_last_day')} / {s.get('pypi_last_week')} / {s.get('pypi_last_month')}",
        "",
        "GitHub traffic (~14d API window)",
        f"  DevoteamSP  stars={s.get('devoteam_stars')}  "
        f"views={s.get('devoteam_views_14d')} ({s.get('devoteam_views_uniques_14d')} uniq)  "
        f"clones={s.get('devoteam_clones_14d')} ({s.get('devoteam_clones_uniques_14d')} uniq)",
        f"  lletourmy   stars={s.get('lletourmy_stars')}  "
        f"views={s.get('lletourmy_views_14d')}  clones={s.get('lletourmy_clones_14d')}",
    ]
    for name, repo in (payload.get("github") or {}).items():
        refs = repo.get("popular_referrers")
        if isinstance(refs, list) and refs:
            top = ", ".join(f"{r.get('referrer')}={r.get('count')}" for r in refs[:5])
            lines.append(f"  referrers {name.split('/')[0]}: {top}")
    return "\n".join(lines)


def update_roadmap(payload: dict[str, Any]) -> bool:
    """Refresh the Success checks snapshot table Current column from latest stats."""
    if not ROADMAP_PATH.exists():
        raise FileNotFoundError(ROADMAP_PATH)
    text = ROADMAP_PATH.read_text(encoding="utf-8")
    s = payload["summary"]
    day = payload["date"]
    month = s.get("pypi_last_month")
    day_dl = s.get("pypi_last_day")
    week = s.get("pypi_last_week")
    stars = s.get("devoteam_stars")

    snapshot_line = (
        f"Snapshot **{day}** ([pypistats](https://pypistats.org/packages/streamlit-coco)): "
        f"**{month}** downloads last month · **{stars}** GitHub stars."
    )
    text2, n1 = re.subn(
        r"Snapshot \*\*\d{4}-\d{2}-\d{2}\*\*.*",
        snapshot_line,
        text,
        count=1,
    )
    row = (
        f"| PyPI downloads | 500+ / month | "
        f"{month} last month ({day_dl} last day · {week} last week) |"
    )
    text3, n2 = re.subn(
        r"\| PyPI downloads \| 500\+ / month \| .* \|",
        row,
        text2,
        count=1,
    )
    stars_row = (
        f"| GitHub stars | 50+ | {stars} "
        f"([DevoteamSP/streamlit-coco](https://github.com/DevoteamSP/streamlit-coco)) |"
    )
    text4, n3 = re.subn(
        r"\| GitHub stars \| 50\+ \| .* \|",
        stars_row,
        text3,
        count=1,
    )
    # Keep table header date in sync when present.
    text5, n4 = re.subn(
        r"\| Metric \| Target \| Current \(\d{4}-\d{2}-\d{2}\) \|",
        f"| Metric | Target | Current ({day}) |",
        text4,
        count=1,
    )
    if n1 + n2 + n3 + n4 == 0:
        return False
    ROADMAP_PATH.write_text(text5, encoding="utf-8")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite today's snapshot if it already exists",
    )
    parser.add_argument(
        "--update-roadmap",
        action="store_true",
        help="Also refresh Current values in doc/roadmap.md Success checks",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and print only; do not write files",
    )
    args = parser.parse_args(argv)

    try:
        payload = collect()
    except (urllib.error.URLError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(format_summary(payload))
    if args.dry_run:
        return 0

    try:
        path = write_snapshot(payload, force=args.force)
    except FileExistsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"\nwrote {path.relative_to(ROOT)}")
    print(f"wrote {LATEST_PATH.relative_to(ROOT)}")
    print(f"appended {HISTORY_PATH.relative_to(ROOT)}")

    if args.update_roadmap:
        if update_roadmap(payload):
            print(f"updated {ROADMAP_PATH.relative_to(ROOT)}")
        else:
            print(
                "warning: roadmap Success checks patterns not found; no edit",
                file=sys.stderr,
            )
            return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
