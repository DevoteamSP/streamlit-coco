# Release checklist — 0.1.5

**Owner:** streamlit-coco maintainers  
**Target tag date:** 2026-08-09  
**GitHub Release (publisher):** https://github.com/lletourmy/streamlit-coco/releases/tag/v0.1.5  
**GitHub Release (org mirror):** https://github.com/DevoteamSP/streamlit-coco/releases/tag/v0.1.5  
**PyPI:** https://pypi.org/project/streamlit-coco/0.1.5/

Do not run `make sync-release` / tag `v0.1.5` until Product docs + QA are done. Marketing can ship the same day or within 48h.

Outreach drafts: [`../../../doc-dev/releases/0.1.5/`](../../../doc-dev/releases/0.1.5/) (dev-only, not public sync).

---

## 1. Product docs (required)

- [x] **`pyproject.toml`** — `version = "0.1.5"`
- [x] **`CHANGELOG.md`** — `[Unreleased]` → `## [0.1.5] — 2026-08-09`; empty subsections removed; fresh `[Unreleased]` left at top
- [x] **`doc/roadmap.md`** — Status → `0.1.5` shipped; clear **Now** table of cwd-upload / UX / SBOM / e2e items
- [x] **`doc/prd.md`** — Status / Phase 4 notes; NG7 upload + FR-S6/S7/ST4 reflected if not already
- [x] **`doc/api.md`** — `upload_to_cwd`, `cwd_uploader`, `UploadedPath`, `max_messages` / `show_copy` documented
- [x] Feature docs: `file-upload/`, panel checklist UX section, `doc/testing.md`
- [x] Public kit: `doc/releases/0.1.5/`
- [x] Outreach kit: `doc-dev/releases/0.1.5/`

## 2. Quality gates (required)

- [x] `make test-all` (lint + unit + Playwright e2e + audit) — [`doc/testing.md`](../../testing.md)
- [ ] Manual checklists: file-upload, panel (incl. copy / highlight / windowing), tools-display as needed
- [ ] Live smoke: `make cwd-upload`, `make chat`

## 3. Visuals (required for community posts)

- [x] Screenshots per [`screenshots/README.md`](screenshots/README.md)
- [x] Hero image for LinkedIn / GitHub Release
- [ ] Optional: short GIF — upload → ask → SQL card / Copy

## 4. GitHub + PyPI (required)

Follow [`doc/deployment/publish.md`](../../deployment/publish.md):

- [x] Merge `feature/cwd_upload` → `-dev` `main`
- [x] `COMMIT=1 PUSH=1 MESSAGE="Release 0.1.5" make sync-release` (lletourmy + DevoteamSP)
- [x] Tag `v0.1.5` on public `lletourmy/streamlit-coco` and push
- [x] Confirm GitHub Release + PyPI + SBOM asset (SBOM under `sbom/` so PyPI only gets wheel/sdist)
- [x] Release body: CHANGELOG excerpt + screenshots

## 5. Narrative & outreach (strongly recommended — `doc-dev`)

- [x] LinkedIn — posted 2026-08-09: [activity 7492226931485028352](https://www.linkedin.com/feed/update/urn:li:activity:7492226931485028352/) (copy + visual: [`linkedin.md`](../../../doc-dev/releases/0.1.5/linkedin.md))
- [x] Medium — published 2026-08-09: [Upload a CSV, ask CoCo](https://medium.com/@laurent.letourmy_61132/upload-a-csv-ask-coco-in-a-streamlit-app-8523fdd671ce) (draft: [`medium-article.md`](../../../doc-dev/releases/0.1.5/medium-article.md))
- [ ] Community pass — [`COMMUNITY.md`](../../../doc-dev/releases/0.1.5/COMMUNITY.md)
- [ ] Refresh [`doc/marketing/one-pager.md`](../../marketing/one-pager.md) (mention upload + safer transcript UX)
- [ ] Paste published URLs below

### Published URLs

| Channel | URL | Date |
| --- | --- | --- |
| GitHub Release (lletourmy) | https://github.com/lletourmy/streamlit-coco/releases/tag/v0.1.5 | 2026-08-09 |
| GitHub Release (DevoteamSP) | https://github.com/DevoteamSP/streamlit-coco/releases/tag/v0.1.5 | 2026-08-09 |
| PyPI | https://pypi.org/project/streamlit-coco/0.1.5/ | 2026-08-09 |
| LinkedIn | https://www.linkedin.com/feed/update/urn:li:activity:7492226931485028352/ | 2026-08-09 |
| Medium | https://medium.com/@laurent.letourmy_61132/upload-a-csv-ask-coco-in-a-streamlit-app-8523fdd671ce | 2026-08-09 |
| Streamlit Forum | | |
| Snowflake Community | | |
| Other | | |

## 6. Sign-off

| Role | Name | Date |
| --- | --- | --- |
| Engineering | | |
| Docs / product | | |
| Marketing / community | | |
