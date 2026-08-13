# Release checklist — 0.1.6

**Owner:** streamlit-coco maintainers  
**Target tag date:** 2026-08-13  
**GitHub Release (publisher):** _(fill after)_ https://github.com/lletourmy/streamlit-coco/releases/tag/v0.1.6  
**GitHub Release (org mirror):** _(fill after)_ https://github.com/DevoteamSP/streamlit-coco/releases/tag/v0.1.6  
**PyPI:** https://pypi.org/project/streamlit-coco/0.1.6/

Do not run `make sync-release` / tag `v0.1.6` until Product docs + QA are done. Marketing can ship the same day or within 48h.

Outreach drafts: [`../../../doc-dev/releases/0.1.6/`](../../../doc-dev/releases/0.1.6/) (dev-only, not public sync).

---

## 1. Product docs (required)

- [x] **`pyproject.toml`** — `version = "0.1.6"`
- [x] **`CHANGELOG.md`** — `[Unreleased]` → `## [0.1.6] — 2026-08-13`; empty subsections removed; fresh `[Unreleased]` left at top
- [x] **`doc/roadmap.md`** — Status → `0.1.6`; Copilot rail, training pack, Tableau example off **Now** / Later
- [x] **`doc/prd.md`** — Status / last-updated; `copilot_rail()` as exec UX; `rail.py` in layout; FR-P8
- [x] **`doc/api.md`** — `copilot_rail`, `transcript_view_pills`, `preview_chars`, `on_job_finished`
- [x] Feature docs: `copilot-rail/`; training pack `doc/training/`; Tableau example README/PRD
- [x] Public kit: `doc/releases/0.1.6/`
- [x] Outreach kit: `doc-dev/releases/0.1.6/`

## 2. Quality gates (required)

- [ ] `make test-all` (lint + unit + Playwright e2e + audit) — [`doc/testing.md`](../../testing.md)
- [ ] Manual checklists: [`copilot-rail/test-checklist.md`](../../features/copilot-rail/test-checklist.md); panel / approvals as needed
- [ ] Live smoke: `make tableau-semantic`, `make chat`

## 3. Visuals (required for community posts)

- [ ] Screenshots per [`screenshots/README.md`](screenshots/README.md)
- [ ] Hero image for LinkedIn / GitHub Release (Tableau + Copilot rail)
- [ ] Optional: short GIF — queue a Generate job → Working badge → Preview

## 4. GitHub + PyPI (required)

Follow [`doc/deployment/publish.md`](../../deployment/publish.md):

- [ ] Merge `feature/tableau_demo` → `-dev` `main`
- [ ] `COMMIT=1 PUSH=1 MESSAGE="Release 0.1.6" make sync-release` (lletourmy + DevoteamSP)
- [ ] Tag `v0.1.6` on public `lletourmy/streamlit-coco` and push
- [ ] Confirm GitHub Release + PyPI + SBOM asset
- [ ] Release body: CHANGELOG excerpt + screenshots

## 5. Narrative & outreach (strongly recommended — `doc-dev`)

- [ ] LinkedIn — [`linkedin.md`](../../../doc-dev/releases/0.1.6/linkedin.md)
- [ ] Medium — [`medium.md`](../../../doc-dev/releases/0.1.6/medium.md)
- [ ] Community pass — [`COMMUNITY.md`](../../../doc-dev/releases/0.1.6/COMMUNITY.md)
- [x] Refresh [`doc/marketing/one-pager.md`](../../marketing/one-pager.md) (`copilot_rail` + Tableau)
- [ ] Paste published URLs below

### Published URLs

| Channel | URL | Date |
| --- | --- | --- |
| GitHub Release (lletourmy) | | |
| GitHub Release (DevoteamSP) | | |
| PyPI | | |
| LinkedIn | | |
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
