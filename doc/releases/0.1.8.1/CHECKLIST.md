# Release checklist — 0.1.8.1

**Owner:** streamlit-coco maintainers  
**Target tag date:** 2026-09-07  
**GitHub Release (publisher):** _(fill after)_  
**GitHub Release (org mirror):** _(fill after)_  
**PyPI:** https://pypi.org/project/streamlit-coco/0.1.8.1/

Do not run `make sync-release` / tag `v0.1.8.1` until Product docs + QA are done. Marketing can ship the same day or within 48h.

Outreach drafts: [`../../../doc-dev/releases/0.1.8.1/`](../../../doc-dev/releases/0.1.8.1/) (dev-only, not public sync).

---

## 1. Product docs (required)

- [x] **`pyproject.toml`** — `version = "0.1.8.1"`
- [x] **`CHANGELOG.md`** — `[Unreleased]` → `## [0.1.8.1] — 2026-09-07`; empty subsections removed; fresh `[Unreleased]` left at top
- [x] **`doc/roadmap.md`** — Status / Last updated; `0.1.8.1` shipped section; **Now** still API mode
- [x] **Public GitHub issues** — reviewed 2026-09-07: no open issue is Done-when for this patch. None progressed enough for a comment. No new tracker proposed (shipped API is documented on the rail feature + `doc/api.md`)
- [x] **`doc/prd.md`** — Status / FR-P8 match the cut
- [x] **`doc/api.md`** — `deferred=` on `copilot_rail()` documented
- [x] Feature narratives / checklists: [`copilot-rail/`](../../features/copilot-rail/)
- [x] Public kit: `doc/releases/0.1.8.1/`
- [x] Outreach kit: `doc-dev/releases/0.1.8.1/`

## 2. Quality gates (required)

- [x] `make test-all` (lint + unit + Playwright e2e + audit) — see [`doc/testing.md`](../../testing.md) — 2026-09-07 (135 unit + 3 e2e + pip-audit clean)
- [ ] Manual feature checklist — [`copilot-rail/test-checklist.md`](../../features/copilot-rail/test-checklist.md) step **2b-deferred** on `make bi-semantic` (Connect → click starter → input fills, no send)
- [ ] Live CoCo smoke as needed (`make bi-semantic`)

## 3. Visuals (required for community posts)

- [ ] Screenshots captured per [`screenshots/README.md`](screenshots/README.md)
- [ ] At least one **hero** image suitable for LinkedIn / GitHub Release
- [ ] Optional: 15–45s screen recording (click starter → input fills → submit)

## 4. GitHub + PyPI (required)

Follow [`doc/deployment/publish.md`](../../deployment/publish.md):

- [ ] Merge to `-dev` `main`
- [ ] `COMMIT=1 PUSH=1 MESSAGE="Release 0.1.8.1" make sync-release`
- [ ] Tag `v0.1.8.1` on public `streamlit-coco` and push
- [ ] Confirm GitHub Release + PyPI wheel; SBOM asset if workflow attaches it
- [ ] GitHub Release body: CHANGELOG excerpt + screenshot if captured

## 5. Narrative & outreach (strongly recommended — `doc-dev`)

- [ ] LinkedIn — [`linkedin.md`](../../../doc-dev/releases/0.1.8.1/linkedin.md)
- [ ] Medium — [`medium.md`](../../../doc-dev/releases/0.1.8.1/medium.md) (short patch note; optional for this cut)
- [ ] Community pass — [`COMMUNITY.md`](../../../doc-dev/releases/0.1.8.1/COMMUNITY.md)
- [ ] Refresh [`doc/marketing/one-pager.md`](../../marketing/one-pager.md) if positioning changed — rail line updated
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
