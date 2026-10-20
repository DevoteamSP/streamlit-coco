# Release checklist — 0.2.1

**Owner:** streamlit-coco maintainers  
**Target tag date:** 2026-10-20  
**GitHub Release (publisher):** https://github.com/lletourmy/streamlit-coco/releases/tag/v0.2.1  
**GitHub Release (org mirror):** https://github.com/DevoteamSP/streamlit-coco/releases/tag/v0.2.1  
**PyPI:** https://pypi.org/project/streamlit-coco/0.2.1/

README patch of [`0.2.0`](../0.2.0/CHECKLIST.md). No outreach: nothing user-visible changed.

---

## 1. Product docs

- [x] **`pyproject.toml`** and `streamlit_coco.__version__`: `0.2.1`
- [x] **`CHANGELOG.md`**: `## [0.2.1] — 2026-10-20` (the GitHub Release body is this section)
- [x] **`doc/roadmap.md`**, **`doc/prd.md`**, **`doc/releases/README.md`**, **`README.md`**, **`doc/api.md`**: version and status
- [x] Locked dependencies unchanged (only the `streamlit-coco` entry of the two `uv.lock` files)

## 2. Quality gates

- [x] `make check`: ruff, 637 passed, 1 skipped, 742 subtests (2026-10-20)
- [x] Built wheel and sdist pass `twine check`

## 3. GitHub + PyPI

Follow [`doc/deployment/publish.md`](../../deployment/publish.md).

- [x] `COMMIT=1 PUSH=1 MESSAGE="Release 0.2.1" make sync-release` to `lletourmy/streamlit-coco` and `DevoteamSP/streamlit-coco` (identical trees)
- [x] Tag `v0.2.1` on both and push
- [x] Confirm the GitHub Releases (wheel, sdist, SBOM) and the PyPI files; the PyPI page shows the new README, and a clean `pip install "streamlit-coco[sdk]==0.2.1"` gives 0.2.1 with the 0.1.9 API guard passing. PyPI's main listing served 0.2.0 for a few minutes after the upload (cache); the version page and the simple index had 0.2.1 at once

### Published URLs

| Channel | URL | Date |
| --- | --- | --- |
| GitHub Release (lletourmy) | https://github.com/lletourmy/streamlit-coco/releases/tag/v0.2.1 | 2026-10-20 |
| GitHub Release (DevoteamSP) | https://github.com/DevoteamSP/streamlit-coco/releases/tag/v0.2.1 | 2026-10-20 |
| PyPI | https://pypi.org/project/streamlit-coco/0.2.1/ | 2026-10-20 |
