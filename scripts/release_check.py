#!/usr/bin/env python3
"""What to look at before `make sync-release` and the tag (`make release-check`).

Five checks, each PASS, WARN, FAIL or SKIP (a network or a tool is missing: it says so):

1. version   the version of pyproject.toml is not on PyPI, not a tag of the public repository
             (remote and local clone), matches `__version__`, and has a CHANGELOG heading.
2. public    the public clone has no release that this CHANGELOG does not know (0.2.1 was
             published from a branch that never reached main).
3. audit     pip-audit of the root environment and of every other uv.lock.
4. alerts    open Dependabot alerts of the dev repository, by manifest (a warning: GitHub
             rescans after a push, so the list can lag behind a fix).
5. sync      the dry run of `scripts/sync_release.sh`: what changes in the public tree, what
             it deletes, generated `out/` files that would go public, dev-only files that leak.

Exit status: 1 when a check FAILS. Settings are the sync script's: RELEASE_REPO (default
../streamlit-coco) and RELEASE_REMOTE (default https://github.com/lletourmy/streamlit-coco.git).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE_REPO = Path(os.environ.get("RELEASE_REPO") or ROOT.parent / "streamlit-coco")
RELEASE_REMOTE = (
    os.environ.get("RELEASE_REMOTE") or "https://github.com/lletourmy/streamlit-coco.git"
)
PACKAGE = "streamlit-coco"
# Paths the sync script excludes: if one shows in its output, something leaks.
LEAK_PREFIXES = ("doc-dev/", "apps/", ".claude", ".agents", ".cursor")
LEAK_NAMES = (".env", "secrets.toml")

PASS, WARN, FAIL, SKIP = "PASS", "WARN", "FAIL", "SKIP"


# ---- pure parsing (tests/test_release_check.py)
def changelog_headings(text: str) -> list[str]:
    """The `## [X.Y.Z]` headings of a changelog (Unreleased included)."""
    return re.findall(r"^## \[([^\]]+)\]", text, re.M)


def unknown_releases(public: str, dev: str) -> list[str]:
    """Versions the public changelog has and the dev one lacks."""
    known = set(changelog_headings(dev))
    return [h for h in changelog_headings(public) if h != "Unreleased" and h not in known]


def project_version(pyproject: str) -> str | None:
    found = re.search(r'^version = "([^"]+)"', pyproject, re.M)
    return found.group(1) if found else None


def module_version(init: str) -> str | None:
    found = re.search(r'^__version__ = "([^"]+)"', init, re.M)
    return found.group(1) if found else None


def parse_sync_dry_run(output: str) -> dict[str, list[str]]:
    """Sort the itemized lines of `rsync -i --dry-run` (the sync script prints them).

    content: files whose content changes (size, checksum or new); times only are ignored.
    deleted: files the public tree would lose. out: generated `out/` files that change or are
    new. leaks: paths the sync script excludes and that show anyway.
    """
    content: list[str] = []
    deleted: list[str] = []
    for line in output.splitlines():
        if line.startswith("*deleting"):
            deleted.append(line.split(None, 1)[1].strip())
            continue
        parts = line.split(None, 1)
        if len(parts) != 2 or not re.fullmatch(r"[<>c.*][fdLDS][.+a-z?]*", parts[0]):
            continue
        code, path = parts[0], parts[1].strip()
        if code[1] != "f":  # directories and links: not content
            continue
        if "+" in code or (len(code) > 2 and code[2] == "c") or (len(code) > 3 and code[3] == "s"):
            content.append(path)
    changed = content + deleted
    return {
        "content": content,
        "deleted": deleted,
        "out": [p for p in content if "/out/" in p or p.startswith("out/")],
        "leaks": [p for p in changed if p.startswith(LEAK_PREFIXES) or Path(p).name in LEAK_NAMES],
    }


def alerts_by_manifest(tsv: str) -> Counter[str]:
    """Count `manifest<TAB>package<TAB>severity` lines by manifest."""
    return Counter(line.split("\t")[0] for line in tsv.splitlines() if line.strip())


# ---- helpers
def run(cmd: list[str], timeout: int = 120, **kwargs) -> subprocess.CompletedProcess:
    """Run a command in the repository; a command that hangs (no network) ends as status 124."""
    try:
        return subprocess.run(
            cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout, **kwargs
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(cmd, 124, "", f"timed out after {timeout}s")


def pypi_versions() -> set[str] | None:
    url = f"https://pypi.org/pypi/{PACKAGE}/json"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return set(json.load(r)["releases"])
    except Exception:  # noqa: BLE001 - certificates, proxy, offline: try curl before giving up
        done = run(["curl", "-fsS", "--max-time", "20", url], timeout=30)
        try:
            return set(json.loads(done.stdout)["releases"]) if done.returncode == 0 else None
        except (ValueError, KeyError):
            return None


def remote_tags() -> set[str] | None:
    done = run(["git", "ls-remote", "--tags", RELEASE_REMOTE], timeout=30)
    if done.returncode != 0:
        return None
    return {
        line.split("refs/tags/")[1].rstrip("^{}")
        for line in done.stdout.splitlines()
        if "refs/tags/" in line
    }


def report(name: str, status: str, lines: list[str]) -> str:
    print(f"\n[{status}] {name}")
    for line in lines:
        print(f"    {line}")
    return status


# ---- the checks
def check_version() -> str:
    pyproject = (ROOT / "pyproject.toml").read_text()
    version = project_version(pyproject)
    problems: list[str] = []
    notes: list[str] = []
    if not version:
        return report("version", FAIL, ["no version in pyproject.toml"])
    notes.append(f"pyproject.toml: {version}")
    if module_version((ROOT / "streamlit_coco" / "__init__.py").read_text()) != version:
        problems.append("streamlit_coco.__version__ differs from pyproject.toml")
    if version not in changelog_headings((ROOT / "CHANGELOG.md").read_text()):
        problems.append(f"CHANGELOG.md has no `## [{version}]` heading")
    if not (ROOT / "doc" / "releases" / version / "CHECKLIST.md").is_file():
        problems.append(f"doc/releases/{version}/CHECKLIST.md is missing")
    published = pypi_versions()
    if published is None:
        notes.append("PyPI: not reached (skipped)")
    elif version in published:
        problems.append(f"{version} is already on PyPI: a published version cannot be replaced")
    else:
        notes.append(f"PyPI: {version} is free (latest: {max(published, key=_key)})")
    tags = remote_tags()
    if tags is None:
        notes.append(f"public tags: {RELEASE_REMOTE} not reached (skipped)")
    elif f"v{version}" in tags:
        problems.append(f"the tag v{version} already exists on the public repository")
    else:
        notes.append(f"public tags: v{version} is free")
    if (RELEASE_REPO / ".git").is_dir():
        local = run(["git", "-C", str(RELEASE_REPO), "tag", "-l", f"v{version}"]).stdout.strip()
        if local:
            problems.append(f"the tag v{version} exists in the local public clone")
    return report("version", FAIL if problems else PASS, problems + notes)


def _key(version: str) -> tuple:
    return tuple(int(p) if p.isdigit() else 0 for p in re.split(r"[.]", version))


def check_public() -> str:
    if not (RELEASE_REPO / ".git").is_dir():
        return report("public", SKIP, [f"no public clone at {RELEASE_REPO}"])
    run(["git", "-C", str(RELEASE_REPO), "fetch", "--quiet"], timeout=30)
    shown = run(["git", "-C", str(RELEASE_REPO), "show", "origin/main:CHANGELOG.md"])
    if shown.returncode != 0:
        return report("public", SKIP, ["origin/main of the public clone has no CHANGELOG.md"])
    missing = unknown_releases(shown.stdout, (ROOT / "CHANGELOG.md").read_text())
    if missing:
        return report(
            "public",
            FAIL,
            [
                "the public repository has releases this CHANGELOG does not know: "
                + ", ".join(missing),
                "merge the branch that holds them before the sync (the sync would overwrite them)",
            ],
        )
    return report("public", PASS, ["every release of the public CHANGELOG is in this one"])


def check_audit() -> str:
    lines: list[str] = []
    status = PASS
    root = run([sys.executable, "-m", "pip_audit", "--skip-editable"])
    text = (root.stdout + root.stderr).strip().splitlines()
    if root.returncode == 0:
        lines.append("uv.lock (root environment): clean")
    else:
        status = FAIL
        lines.append("uv.lock (root environment):")
        lines += [f"  {line}" for line in text[:25]]
    others = run([sys.executable, str(ROOT / "scripts" / "audit_locks.py")])
    lines += others.stdout.strip().splitlines()
    if others.returncode:
        status = FAIL
    return report("audit", status, lines)


def check_alerts() -> str:
    origin = run(["git", "remote", "get-url", "origin"]).stdout.strip()
    repo = re.search(r"github\.com[:/]([^/]+/[^/.]+)", origin)
    if not repo:
        return report("alerts", SKIP, ["origin is not a GitHub repository"])
    done = run(
        [
            "gh",
            "api",
            f"repos/{repo.group(1)}/dependabot/alerts?state=open&per_page=100",
            "--paginate",
            "--jq",
            ".[] | [.dependency.manifest_path, .dependency.package.name,"
            " .security_advisory.severity] | @tsv",
        ]
    )
    if done.returncode != 0:
        return report(
            "alerts", SKIP, ["gh is missing, not signed in, or the alerts are not readable"]
        )
    counts = alerts_by_manifest(done.stdout)
    if not counts:
        return report("alerts", PASS, ["no open Dependabot alert"])
    severities = Counter(line.split("\t")[2] for line in done.stdout.splitlines() if line.strip())
    lines = [f"{n:4d}  {manifest}" for manifest, n in counts.most_common()]
    lines.append("by severity: " + ", ".join(f"{k} {v}" for k, v in severities.most_common()))
    lines.append("GitHub rescans after a push: re-run after the fix is on the default branch")
    return report("alerts", WARN, lines)


def check_sync() -> str:
    script = ROOT / "scripts" / "sync_release.sh"
    env = {**os.environ, "RELEASE_REPO": str(RELEASE_REPO), "RELEASE_REMOTE": RELEASE_REMOTE}
    done = run(["bash", str(script), "--dry-run"], env=env)
    if done.returncode != 0:
        return report("sync", FAIL, ["the dry run failed:", *done.stderr.strip().splitlines()[-5:]])
    found = parse_sync_dry_run(done.stdout)
    lines = [
        f"{len(found['content'])} files change in the public tree",
        f"{len(found['deleted'])} deleted: " + (", ".join(found["deleted"][:8]) or "none"),
    ]
    problems = False
    if found["out"]:
        problems = True
        lines.append(f"{len(found['out'])} generated out/ files would go public (the sync copies")
        lines.append("    ignored folders too): restore them from the public clone or delete them")
        lines += [f"    {p}" for p in found["out"][:12]]
    else:
        lines.append("no generated out/ file changes")
    if found["leaks"]:
        problems = True
        lines.append("dev-only files in the sync output: " + ", ".join(found["leaks"][:10]))
    else:
        lines.append("no dev-only file in the sync output")
    return report("sync", FAIL if problems else (WARN if found["deleted"] else PASS), lines)


def main() -> int:
    print(f"release-check · {ROOT.name} · public clone {RELEASE_REPO}")
    results = [
        check_version(),
        check_public(),
        check_audit(),
        check_alerts(),
        check_sync(),
    ]
    summary = Counter(results)
    print("\n" + " · ".join(f"{summary[s]} {s}" for s in (PASS, WARN, FAIL, SKIP) if summary[s]))
    if summary[FAIL]:
        print("Do not sync or tag yet.")
        return 1
    print("Read the warnings, then follow doc/deployment/publish.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
