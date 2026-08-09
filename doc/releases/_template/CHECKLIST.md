# Release checklist — X.Y.Z

**Owner:**  
**Target tag date:**  
**GitHub Release:** _(fill after)_  
**PyPI:** https://pypi.org/project/streamlit-coco/X.Y.Z/

Do not run `make sync-release` / tag `vX.Y.Z` until Product docs + QA are done. Marketing can ship the same day or within 48h.

Outreach drafts (LinkedIn / Medium / community) live in **`doc-dev/releases/X.Y.Z/`** (not synced publicly).

---

## 1. Product docs (required)

- [ ] **`pyproject.toml`** — `version = "X.Y.Z"`
- [ ] **`CHANGELOG.md`** — `[Unreleased]` → `## [X.Y.Z] — YYYY-MM-DD`; empty subsections removed; fresh `[Unreleased]` left at top
- [ ] **`doc/roadmap.md`** — Status / Last updated; shipped items off **Now**; Later checkboxes updated
- [ ] **`doc/prd.md`** — Status / phase notes match the cut; new capabilities reflected if they change the product story
- [ ] **`doc/api.md`** — Public exports for new APIs documented
- [ ] Feature narratives / checklists under `doc/features/` for anything user-visible this cut
- [ ] Public kit: `doc/releases/X.Y.Z/`
- [ ] Outreach kit: `doc-dev/releases/X.Y.Z/`

## 2. Quality gates (required)

- [ ] `make test-all` (lint + unit + Playwright e2e + audit) — see [`doc/testing.md`](../../testing.md)
- [ ] Manual feature checklists for touched areas — [`doc/features/README.md`](../../features/README.md)
- [ ] Live CoCo demos smoke (`make chat`, `make cwd-upload`, …) as needed

## 3. Visuals (required for community posts)

- [ ] Screenshots captured per [`screenshots/README.md`](screenshots/README.md)
- [ ] At least one **hero** image suitable for LinkedIn / GitHub Release
- [ ] Optional: 15–45s screen recording (upload / copy / SQL highlight)

## 4. GitHub + PyPI (required)

Follow [`doc/deployment/publish.md`](../../deployment/publish.md):

- [ ] Merge to `-dev` `main`
- [ ] `COMMIT=1 PUSH=1 MESSAGE="Release X.Y.Z" make sync-release`
- [ ] Tag `vX.Y.Z` on public `streamlit-coco` and push
- [ ] Confirm GitHub Release + PyPI wheel; SBOM asset if workflow attaches it
- [ ] GitHub Release body: CHANGELOG excerpt + 2–4 screenshots / GIF

## 5. Narrative & outreach (strongly recommended — `doc-dev`)

- [ ] LinkedIn — `doc-dev/releases/X.Y.Z/linkedin.md`
- [ ] Medium — `doc-dev/releases/X.Y.Z/medium.md`
- [ ] Community pass — `doc-dev/releases/X.Y.Z/COMMUNITY.md`
- [ ] Refresh [`doc/marketing/one-pager.md`](../../marketing/one-pager.md) if positioning changed
- [ ] Paste published URLs below

### Published URLs

| Channel | URL | Date |
| --- | --- | --- |
| GitHub Release | | |
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
