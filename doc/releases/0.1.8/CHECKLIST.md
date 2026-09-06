# Release checklist — 0.1.8

**Owner:** streamlit-coco maintainers  
**Target tag date:** 2026-09-06 
**GitHub Release (publisher):** https://github.com/lletourmy/streamlit-coco/releases/tag/v0.1.8  
**GitHub Release (org mirror):** https://github.com/DevoteamSP/streamlit-coco/releases/tag/v0.1.8  
**PyPI:** https://pypi.org/project/streamlit-coco/0.1.8/

Do not run `make sync-release` / tag `v0.1.8` until Product docs + QA are done. Marketing can ship the same day or within 48h.

Outreach drafts: [`../../../doc-dev/releases/0.1.8/`](../../../doc-dev/releases/0.1.8/) (dev-only, not public sync).

---

## 1. Product docs (required)

- [x] **`pyproject.toml`** — `version = "0.1.8"`
- [x] **`CHANGELOG.md`** — `[Unreleased]` → `## [0.1.8] — 2026-09-06`; empty subsections removed; fresh `[Unreleased]` left at top
- [x] **`doc/roadmap.md`** — Status / Last updated; App Builder off **Now**; Later community-examples checkbox checked
- [x] **Public GitHub issues** — commented on [#9](https://github.com/DevoteamSP/streamlit-coco/issues/9) (sketches-on-brief in; photo-only still RFC). App Builder tracker **not filed** until confirmed
- [x] **`doc/prd.md`** — Status / phase notes match the cut; new capabilities reflected if they change the product story
- [x] **`doc/api.md`** — Public exports for new APIs documented (`example_questions`, `transcript_display_config()`)
- [x] Feature narratives / checklists: [`app-builder/`](../../features/app-builder/)
- [x] Public kit: `doc/releases/0.1.8/`
- [x] Outreach kit: `doc-dev/releases/0.1.8/`

## 2. Quality gates (required)

- [x] `make test-all` (lint + unit + Playwright e2e + audit) — see [`doc/testing.md`](../../testing.md) — 2026-09-06
- [ ] Manual feature checklists for touched areas — [`app-builder/test-checklist.md`](../../features/app-builder/test-checklist.md); re-run rail / viewer if composed (deferred; ship on automated gate)
- [ ] Live CoCo demos smoke (`make chat`, App Builder make target, …) as needed (deferred)

## 3. Visuals (required for community posts)

- [ ] Screenshots captured per [`screenshots/README.md`](screenshots/README.md)
- [ ] At least one **hero** image suitable for LinkedIn / GitHub Release
- [ ] Optional: 15–45s screen recording (prompt → generated app → Preview / Fix)

## 4. GitHub + PyPI (required)

Follow [`doc/deployment/publish.md`](../../deployment/publish.md):

- [x] Merge to `-dev` `main`
- [x] `COMMIT=1 PUSH=1 MESSAGE="Release 0.1.8" make sync-release`
- [x] Tag `v0.1.8` on public `streamlit-coco` and push
- [x] Confirm GitHub Release + PyPI wheel; SBOM asset if workflow attaches it
- [ ] GitHub Release body: CHANGELOG excerpt + 2–4 screenshots / GIF (notes from CHANGELOG; screenshots still outstanding)

## 5. Narrative & outreach (strongly recommended — `doc-dev`)

- [ ] LinkedIn — [`linkedin.md`](../../../doc-dev/releases/0.1.8/linkedin.md)
- [ ] Medium — [`medium.md`](../../../doc-dev/releases/0.1.8/medium.md)
- [ ] Community pass — [`COMMUNITY.md`](../../../doc-dev/releases/0.1.8/COMMUNITY.md) + [`community-posts.md`](../../../doc-dev/releases/0.1.8/community-posts.md)
- [ ] Refresh [`doc/marketing/one-pager.md`](../../marketing/one-pager.md) if positioning changed
- [ ] Paste published URLs below

### Published URLs

| Channel | URL | Date |
| --- | --- | --- |
| GitHub Release (lletourmy) | https://github.com/lletourmy/streamlit-coco/releases/tag/v0.1.8 | 2026-09-06 |
| GitHub Release (DevoteamSP) | https://github.com/DevoteamSP/streamlit-coco/releases/tag/v0.1.8 | 2026-09-06 |
| PyPI | https://pypi.org/project/streamlit-coco/0.1.8/ | 2026-09-06 |
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
