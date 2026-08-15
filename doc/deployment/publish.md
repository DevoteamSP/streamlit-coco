# Publish to streamlit-coco + PyPI

Two GitHub repos:

| Repo | Role |
| --- | --- |
| [`DevoteamSP/streamlit-coco-dev`](https://github.com/DevoteamSP/streamlit-coco-dev) | Development (WIP, agents, experiments) |
| [`lletourmy/streamlit-coco`](https://github.com/lletourmy/streamlit-coco) | **Temporary** public release surface; **tags publish to PyPI** |

Package name on PyPI is always `streamlit-coco`.

> **Temporary publisher (2026-08):** DevoteamSP is not yet validated on PyPI, so
> Trusted Publishing and `make sync-release` target
> [`lletourmy/streamlit-coco`](https://github.com/lletourmy/streamlit-coco).
> When the org is validated, switch `RELEASE_REMOTE`, `release.yml` gate,
> package URLs, and the PyPI Trusted Publisher back to
> [`DevoteamSP/streamlit-coco`](https://github.com/DevoteamSP/streamlit-coco).

---

## One-time setup

1. Public release repo exists: https://github.com/lletourmy/streamlit-coco
2. On [PyPI Trusted Publishers](https://pypi.org/manage/account/publishing/) (or the project’s Publishing settings), register:

   | Field | Value |
   | --- | --- |
   | PyPI project | `streamlit-coco` |
   | Owner | `lletourmy` |
   | Repository | `streamlit-coco` |
   | Workflow | `release.yml` |
   | Environment | *(leave empty unless you add one)* |

3. Confirm `.github/workflows/release.yml` only uploads when  
   `github.repository == 'lletourmy/streamlit-coco'` (already gated).

---

## Cut a release

### 1. Prepare in `-dev`

Create (or complete) release kits for the version:

```bash
VER=X.Y.Z
mkdir -p "doc/releases/${VER}/screenshots" "doc-dev/releases/${VER}"
cp -R doc/releases/_template/. "doc/releases/${VER}/"
cp -R doc-dev/releases/_template/. "doc-dev/releases/${VER}/"
```

- Public checklist: [`doc/releases/`](../releases/README.md) → `doc/releases/X.Y.Z/CHECKLIST.md`  
  (current: [`doc/releases/0.1.7/`](../releases/0.1.7/))
- Outreach (LinkedIn / Medium / community): [`doc-dev/releases/`](../../doc-dev/releases/README.md)  
  (current: [`doc-dev/releases/0.1.7/`](../../doc-dev/releases/0.1.7/)) — **never synced** to the public repo

```bash
make test-all
# Manual UI checklists under doc/features/ before 0.x / 1.0 cuts
```

**Required before tagging (do not skip):**

1. Bump `version` in `pyproject.toml`
2. **Clean + update `CHANGELOG.md`:** move `[Unreleased]` → `## [X.Y.Z] — YYYY-MM-DD`, drop empty subsections, keep one clear Added/Changed/Fixed/Security block
3. **Clean + update `doc/roadmap.md`:** status line, **Now** / **Next**, remove shipped items from the active plan
4. **Update `doc/prd.md`** (and `doc/api.md` if APIs changed)
5. **Screenshots** in `doc/releases/X.Y.Z/screenshots/`; **LinkedIn / Medium / community** drafts in `doc-dev/releases/X.Y.Z/`
6. Merge to `main` on `-dev` (recommended before sync)

### 2. Sync the public tree

```bash
# Preview
DRY_RUN=1 make sync-release

# Write + commit + push to lletourmy/streamlit-coco (PyPI Trusted Publisher)
COMMIT=1 PUSH=1 MESSAGE="Release X.Y.Z" make sync-release

# Also mirror to the org public repo (same tree; PyPI still gates on lletourmy until validated)
COMMIT=1 PUSH=1 MESSAGE="Release X.Y.Z" \
  RELEASE_REPO="$PWD/../streamlit-coco-org" \
  RELEASE_REMOTE="https://github.com/DevoteamSP/streamlit-coco.git" \
  make sync-release
```

Default target clone: `../streamlit-coco` (override with `RELEASE_REPO=`).
Default remote: `https://github.com/lletourmy/streamlit-coco.git` (override with `RELEASE_REMOTE=`).

Excluded from the public tree: `.cursor/`, `.agents/`, `.claude/`, `doc-dev/`,
`apps/`, local caches, `dist/`, and this sync script.

### 3. Tag on **lletourmy/streamlit-coco** (PyPI publisher; not `-dev`)

```bash
cd ../streamlit-coco
git tag -a vX.Y.Z -m "vX.Y.Z"
git push origin vX.Y.Z
```

Optionally mirror the same annotated tag on `DevoteamSP/streamlit-coco` for discoverability
(PyPI upload still only runs when `github.repository == 'lletourmy/streamlit-coco'`).

The Release workflow then:

1. Creates a GitHub Release (notes from `CHANGELOG`)
2. Builds sdist + wheel (`uv build`)
3. Publishes to PyPI (skipped for `-rc` / `-beta` / `-alpha` tags)

### 4. Verify

```bash
pip install "streamlit-coco[sdk]==X.Y.Z"
# PyPI: https://pypi.org/project/streamlit-coco/
# Release: https://github.com/lletourmy/streamlit-coco/releases
```

---

## Manual / local publish (fallback)

From a clean synced tree (or `-dev` if you must):

```bash
make build
make publish   # uv publish — needs credentials if Trusted Publisher is unavailable
```

Prefer the tagged CI path on `streamlit-coco`.
