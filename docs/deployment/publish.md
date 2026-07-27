# Publish to streamlit-coco + PyPI

Two GitHub repos:

| Repo | Role |
| --- | --- |
| [`DevoteamSP/streamlit-coco-dev`](https://github.com/DevoteamSP/streamlit-coco-dev) | Development (WIP, agents, experiments) |
| [`DevoteamSP/streamlit-coco`](https://github.com/DevoteamSP/streamlit-coco) | Public release surface; **tags publish to PyPI** |

Package name on PyPI is always `streamlit-coco`.

---

## One-time setup

1. Public repo exists: https://github.com/DevoteamSP/streamlit-coco
2. On [PyPI Trusted Publishers](https://pypi.org/manage/account/publishing/) (or the project’s Publishing settings), register:

   | Field | Value |
   | --- | --- |
   | PyPI project | `streamlit-coco` |
   | Owner | `DevoteamSP` |
   | Repository | `streamlit-coco` |
   | Workflow | `release.yml` |
   | Environment | *(leave empty unless you add one)* |

3. Confirm `.github/workflows/release.yml` only uploads when  
   `github.repository == 'DevoteamSP/streamlit-coco'` (already gated).

---

## Cut a release

### 1. Prepare in `-dev`

```bash
make check
# Run manual UI checklists under docs/features/ before 0.x / 1.0 cuts
```

- Set `version` in `pyproject.toml`
- Move `CHANGELOG.md` `[Unreleased]` → `## [X.Y.Z] — YYYY-MM-DD`
- Merge to `main` on `-dev` (recommended before sync)

### 2. Sync the public tree

```bash
# Preview
DRY_RUN=1 make sync-release

# Write + commit + push to DevoteamSP/streamlit-coco
COMMIT=1 PUSH=1 MESSAGE="Release X.Y.Z" make sync-release
```

Default target clone: `../streamlit-coco` (override with `RELEASE_REPO=`).

Excluded from the public tree: `.cursor/`, `.agents/`, `.claude/`, local caches, `dist/`, and this sync script.

### 3. Tag on **streamlit-coco** (not `-dev`)

```bash
cd ../streamlit-coco
git tag -a vX.Y.Z -m "vX.Y.Z"
git push origin vX.Y.Z
```

The Release workflow then:

1. Creates a GitHub Release (notes from `CHANGELOG`)
2. Builds sdist + wheel (`uv build`)
3. Publishes to PyPI (skipped for `-rc` / `-beta` / `-alpha` tags)

### 4. Verify

```bash
pip install "streamlit-coco[sdk]==X.Y.Z"
# PyPI: https://pypi.org/project/streamlit-coco/
# Release: https://github.com/DevoteamSP/streamlit-coco/releases
```

---

## Manual / local publish (fallback)

From a clean synced tree (or `-dev` if you must):

```bash
make build
make publish   # uv publish — needs credentials if Trusted Publisher is unavailable
```

Prefer the tagged CI path on `streamlit-coco`.
