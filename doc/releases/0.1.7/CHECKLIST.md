# Release checklist — 0.1.7

**Owner:** streamlit-coco maintainers  
**Target tag date:** 2026-08-15  
**GitHub Release (publisher):** _(fill after)_ https://github.com/lletourmy/streamlit-coco/releases/tag/v0.1.7  
**GitHub Release (org mirror):** _(fill after)_ https://github.com/DevoteamSP/streamlit-coco/releases/tag/v0.1.7  
**PyPI:** https://pypi.org/project/streamlit-coco/0.1.7/

Do not run `make sync-release` / tag `v0.1.7` until Product docs + QA are done. Marketing can ship the same day or within 48h.

Outreach drafts: [`../../../doc-dev/releases/0.1.7/`](../../../doc-dev/releases/0.1.7/) (dev-only, not public sync).

---

## 1. Product docs (required)

- [x] **`pyproject.toml`** — `version = "0.1.7"`
- [x] **`CHANGELOG.md`** — `[Unreleased]` → `## [0.1.7] — 2026-08-15`; empty subsections removed; fresh `[Unreleased]` left at top
- [x] **`doc/roadmap.md`** — Status → `0.1.7`; App Builder moved to **`0.1.8`**; BI + App Viewer off **Now**
- [x] **Public GitHub issues** — reviewed 2026-08-16: none fully closed; progress comments on [#10](https://github.com/DevoteamSP/streamlit-coco/issues/10), [#8](https://github.com/DevoteamSP/streamlit-coco/issues/8), [#11](https://github.com/DevoteamSP/streamlit-coco/issues/11), [#9](https://github.com/DevoteamSP/streamlit-coco/issues/9); App Builder (`0.1.8`) still needs a tracker
- [x] **`doc/prd.md`** — Status / last-updated; `app_viewer()` in exec summary; FR-P9
- [x] **`doc/api.md`** — `app_viewer`, preview helpers, `default_fix_prompt`, `title_extra`
- [x] Feature docs: `app-viewer/`; BI example README/PRD
- [x] Public kit: `doc/releases/0.1.7/`
- [x] Outreach kit: `doc-dev/releases/0.1.7/`

## 2. Quality gates (required)

- [ ] `make test-all` (lint + unit + Playwright e2e + audit) — [`doc/testing.md`](../../testing.md)
- [ ] Manual checklists: [`app-viewer/test-checklist.md`](../../features/app-viewer/test-checklist.md); [`copilot-rail/test-checklist.md`](../../features/copilot-rail/test-checklist.md)
- [ ] Live smoke: `make bi-semantic`, `make chat`

## 3. Visuals (required for community posts)

- [x] Screenshots per [`screenshots/README.md`](screenshots/README.md)
- [x] Hero image for LinkedIn / GitHub Release (`streamlit_app_generation.png`)
- [ ] Optional: short GIF — Run preview → exception → **Fix with CoCo** → rail job

## 4. GitHub + PyPI (required)

Follow [`doc/deployment/publish.md`](../../deployment/publish.md):

- [ ] Merge feature branch → `-dev` `main`
- [ ] `COMMIT=1 PUSH=1 MESSAGE="Release 0.1.7" make sync-release` (lletourmy + DevoteamSP)
- [ ] Tag `v0.1.7` on public `lletourmy/streamlit-coco` and push
- [ ] Confirm GitHub Release + PyPI + SBOM asset
- [ ] Release body: CHANGELOG excerpt + screenshots

## 5. Narrative & outreach (strongly recommended — `doc-dev`)

- [ ] LinkedIn — [`linkedin.md`](../../../doc-dev/releases/0.1.7/linkedin.md)
- [ ] Medium — [`medium.md`](../../../doc-dev/releases/0.1.7/medium.md)
- [ ] Community pass — [`COMMUNITY.md`](../../../doc-dev/releases/0.1.7/COMMUNITY.md)
- [x] Refresh [`doc/marketing/one-pager.md`](../../marketing/one-pager.md) (`app_viewer` + BI)
- [ ] Paste published URLs below

### Published URLs

| Channel | URL | Date |
| --- | --- | --- |
| GitHub Release (lletourmy) | | 2026-08-15 |
| GitHub Release (DevoteamSP) | | 2026-08-15 |
| PyPI | | 2026-08-15 |
| LinkedIn | https://www.linkedin.com/feed/update/urn:li:activity:7500896297399287808/ | 09-02-2026|
| Medium | | |
| Streamlit Forum | | |
| Snowflake Community | | |
| Other | | |

## 6. Sign-off

| Role | Name | Date |
| --- | --- | --- |
| Engineering | | |
| Docs / product | | |
| Marketing / community | | |
