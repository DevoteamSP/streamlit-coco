# Upgrade and release

## Versions

streamlit-coco follows semver. The current version is **0.1.9** (alpha —
`Development Status :: 3 - Alpha` in `pyproject.toml`). There is no
migration-notes file separate from `CHANGELOG.md`; upgrade impact for a
given version is whatever that version's `CHANGELOG.md` entry states under
Added / Changed / Fixed / Security.

## Publish process

Two GitHub repositories are involved:

| Repo | Role |
|---|---|
| `DevoteamSP/streamlit-coco-dev` | Development (private, WIP, agents, experiments) |
| `lletourmy/streamlit-coco` | **Temporary** public release surface — tags pushed here trigger the PyPI publish |

The PyPI project name is always `streamlit-coco`, regardless of which
GitHub repo currently publishes it.

**Temporary publisher caveat:** `DevoteamSP` is not yet validated as a PyPI
Trusted Publisher, so `RELEASE_REMOTE`, the `release.yml` PyPI-upload gate
(`github.repository == 'lletourmy/streamlit-coco'`), and the package's
published URLs currently point at `lletourmy/streamlit-coco`. When
`DevoteamSP` is validated, all of these move to `DevoteamSP/streamlit-coco`
— this is a one-time cutover, not a per-release step.

### Release steps, in order

1. **Prepare in `-dev`.** Create the release kit for the version
   (`doc/releases/X.Y.Z/`, `doc-dev/releases/X.Y.Z/` from the `_template/`
   folders), then run `make test-all` and the manual UI checklists under
   `doc/features/`.
2. **Bump `version` in `pyproject.toml`.**
3. **Clean and update `CHANGELOG.md`** — move `[Unreleased]` to
   `## [X.Y.Z] — YYYY-MM-DD`, drop empty subsections, keep one clear
   Added/Changed/Fixed/Security block.
4. **Clean and update `doc/roadmap.md`** — status line, Now / Next, remove
   shipped items from the active plan.
5. **Update `doc/prd.md`** (and `doc/api.md` if the public API changed).
6. **Add screenshots** under `doc/releases/X.Y.Z/screenshots/`; write
   outreach drafts under `doc-dev/releases/X.Y.Z/` (never synced publicly).
7. **Merge to `main`** on `streamlit-coco-dev`.
8. **Sync the public tree:**
   ```bash
   DRY_RUN=1 make sync-release                       # preview
   COMMIT=1 PUSH=1 MESSAGE="Release X.Y.Z" make sync-release   # write + push
   ```
   Default target clone: `../streamlit-coco`. Default remote:
   `https://github.com/lletourmy/streamlit-coco.git`. Both are overridable
   with `RELEASE_REPO=` / `RELEASE_REMOTE=`. Excluded from the public sync
   tree: `.cursor/`, `.agents/`, `.claude/`, `doc-dev/`, `apps/`, local
   caches, `dist/`, and the sync script itself (also excluded from the
   sdist build via `pyproject.toml`'s
   `[tool.hatch.build.targets.sdist].exclude`).
9. **Tag on `lletourmy/streamlit-coco`, not on `-dev`:**
   ```bash
   cd ../streamlit-coco
   git tag -a vX.Y.Z -m "vX.Y.Z"
   git push origin vX.Y.Z
   ```
10. The GitHub Release workflow (`release.yml`) then:
    - creates a GitHub Release with notes extracted from `CHANGELOG.md`;
    - builds sdist + wheel (`uv build`);
    - generates a CycloneDX SBOM (`sbom-vX.Y.Z.cdx.json`) and attaches it
      to the Release;
    - publishes to PyPI — **skipped for `-rc` / `-beta` / `-alpha` tags.**
11. **Verify:**
    ```bash
    pip install "streamlit-coco[sdk]==X.Y.Z"
    ```

### Manual / local publish fallback

From a clean synced tree (or `-dev` if unavoidable):

```bash
make build      # uv build -> dist/
make publish    # uv publish — needs credentials if Trusted Publisher is unavailable
```

Prefer the tagged CI path on `lletourmy/streamlit-coco` over this fallback.

## Uninstall

streamlit-coco is a library, not a service — there is no separate teardown
procedure beyond removing the package:

```bash
pip uninstall streamlit-coco
# or
uv remove streamlit-coco
```

Removing the package does not touch anything it wrote at runtime (see
[operations](operations.html) Cleanup) — those artifacts are cleaned up
separately if needed.

## Release procedure

This is the same flow as **Publish process** above; there is no separate
release runbook to keep in sync. Cutting a release means completing the
numbered steps in that section in order.
