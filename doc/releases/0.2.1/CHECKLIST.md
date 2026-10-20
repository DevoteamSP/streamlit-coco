# Release checklist — 0.2.1

**Owner:** streamlit-coco maintainers  
**Target tag date:** 2026-10-20  
**GitHub Release (publisher):** see *Published URLs* below (filled in after the tag)  
**GitHub Release (org mirror):** see *Published URLs* below  
**PyPI:** see *Published URLs* below

README patch of [`0.2.0`](../0.2.0/CHECKLIST.md). No outreach: nothing user-visible changed.

---

## 1. Product docs

- [x] **`pyproject.toml`** and `streamlit_coco.__version__`: `0.2.1`
- [x] **`CHANGELOG.md`**: `## [0.2.1] — 2026-10-20` (the GitHub Release body is this section)
- [x] **`doc/roadmap.md`**, **`doc/prd.md`**, **`doc/releases/README.md`**, **`README.md`**, **`doc/api.md`**: version and status
- [x] Locked dependencies unchanged (only the `streamlit-coco` entry of the two `uv.lock` files)

## 2. Quality gates

- [x] `make check`: see the sign-off below
- [x] Built wheel and sdist pass `twine check`

## 3. GitHub + PyPI

Follow [`doc/deployment/publish.md`](../../deployment/publish.md).

- [ ] `COMMIT=1 PUSH=1 MESSAGE="Release 0.2.1" make sync-release` to `lletourmy/streamlit-coco` and `DevoteamSP/streamlit-coco`
- [ ] Tag `v0.2.1` on both and push
- [ ] Confirm the GitHub Releases and the PyPI files; the PyPI page shows the new README

### Published URLs

| Channel | URL | Date |
| --- | --- | --- |
| GitHub Release (lletourmy) | | |
| GitHub Release (DevoteamSP) | | |
| PyPI | | |
