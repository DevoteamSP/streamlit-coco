# Release checklist — 0.1.9

**Owner:** streamlit-coco maintainers  
**Target tag date:** 2026-09-10  
**GitHub Release (publisher):** https://github.com/lletourmy/streamlit-coco/releases/tag/v0.1.9  
**GitHub Release (org mirror):** https://github.com/DevoteamSP/streamlit-coco/releases/tag/v0.1.9  
**PyPI:** https://pypi.org/project/streamlit-coco/0.1.9/

Do not run `make sync-release` / tag `v0.1.9` until Product docs + QA are done. Marketing can ship the same day or within 48h.

Outreach drafts: [`../../../doc-dev/releases/0.1.9/`](../../../doc-dev/releases/0.1.9/) (dev-only, not public sync).

---

## 1. Product docs (required)

- [x] **`pyproject.toml`** — `version = "0.1.9"`
- [x] **`CHANGELOG.md`** — `[Unreleased]` → `## [0.1.9] — 2026-09-10`; empty subsections removed; fresh `[Unreleased]` left at top
- [x] **`doc/roadmap.md`** — Status / Last updated; `0.1.9` shipped section; **Now** still API mode
- [x] **Public GitHub issues** — reviewed 2026-09-10: no open issue is Done-when for this cut. None progressed enough for a comment. No new tracker proposed (shipped API is documented on the rail feature + `doc/api.md`)
- [x] **`doc/prd.md`** — Status / FR-P8 match the cut
- [x] **`doc/api.md`** — `toml_file=` / `list_snowflake_connections()` documented
- [x] Feature narratives / checklists: [`copilot-rail/`](../../features/copilot-rail/)
- [x] Public kit: `doc/releases/0.1.9/`
- [x] Outreach kit: `doc-dev/releases/0.1.9/`

## 2. Quality gates (required)

- [x] `make test-all` (lint + unit + Playwright e2e + audit) — see [`doc/testing.md`](../../testing.md) — 2026-09-10 (147 unit + 3 e2e + pip-audit clean)
- [x] Manual feature checklist — [`copilot-rail/test-checklist.md`](../../features/copilot-rail/test-checklist.md) step **1a** on `make app-builder` (Connection popover: Config file + Connection selectboxes on one row) — 2026-09-10
- [ ] Live CoCo smoke as needed (`make app-builder`)

## 3. Visuals (required for community posts)

- [ ] Screenshots captured per [`screenshots/README.md`](screenshots/README.md)
- [ ] At least one **hero** image suitable for LinkedIn / GitHub Release
- [ ] Optional: 15–45s screen recording (open Connection → change Config file)

## 4. GitHub + PyPI (required)

Follow [`doc/deployment/publish.md`](../../deployment/publish.md):

- [x] Merge to `-dev` `main`
- [x] `COMMIT=1 PUSH=1 MESSAGE="Release 0.1.9" make sync-release`
- [x] Tag `v0.1.9` on public `streamlit-coco` and push
- [x] Confirm GitHub Release + PyPI wheel; SBOM asset if workflow attaches it
- [ ] GitHub Release body: CHANGELOG excerpt + screenshot if captured

## 5. Narrative & outreach (strongly recommended — `doc-dev`)

- [ ] LinkedIn — [`linkedin.md`](../../../doc-dev/releases/0.1.9/linkedin.md)
- [ ] Medium — [`medium.md`](../../../doc-dev/releases/0.1.9/medium.md) (short note; optional for this cut)
- [ ] Community pass — [`COMMUNITY.md`](../../../doc-dev/releases/0.1.9/COMMUNITY.md)
- [ ] Refresh [`doc/marketing/one-pager.md`](../../marketing/one-pager.md) if positioning changed — rail line updated
- [ ] Paste published URLs below

### Published URLs

| Channel | URL | Date |
| --- | --- | --- |
| GitHub Release (lletourmy) | https://github.com/lletourmy/streamlit-coco/releases/tag/v0.1.9 | 2026-09-10 |
| GitHub Release (DevoteamSP) | https://github.com/DevoteamSP/streamlit-coco/releases/tag/v0.1.9 | 2026-09-10 |
| PyPI | https://pypi.org/project/streamlit-coco/0.1.9/ | 2026-09-10 |
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
