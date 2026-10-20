# Release checklist — 0.2.0

**Owner:** streamlit-coco maintainers
**Target tag date:** 2026-10-20  
**GitHub Release (publisher):** https://github.com/lletourmy/streamlit-coco/releases/tag/v0.2.0  
**GitHub Release (org mirror):** https://github.com/DevoteamSP/streamlit-coco/releases/tag/v0.2.0  
**PyPI:** https://pypi.org/project/streamlit-coco/0.2.0/

Do not run `make sync-release` or tag `v0.2.0` until Product docs + QA are done.

Outreach drafts: [`../../../doc-dev/releases/0.2.0/`](../../../doc-dev/releases/0.2.0/) (dev-only, not public sync).

---

## 1. Product docs (required)

- [x] **`pyproject.toml`** — `version = "0.2.0"` (and `streamlit_coco.__version__`)
- [x] **`CHANGELOG.md`** — `[Unreleased]` → `## [0.2.0] — 2026-10-14`; fresh `[Unreleased]` left at top
- [x] **`CHANGELOG.md`** at tag time: heading date `2026-10-20`; the "Prepared locally" sentence is gone (the GitHub Release body is this section)
- [x] **`doc/roadmap.md`** — Status / Last updated; `0.2.0` shipped section; **Now** is API mode
- [ ] **Public GitHub issues** — not touched. This cut is not published. No new issues filed.
- [x] **`doc/prd.md`** — status matches the cut; the chat family is not described as removed
- [x] **`doc/api.md`** — version line matches `0.2.0`; window and chat family both documented
- [x] Feature narrative: [`features/ask-coco/ask-coco.md`](../../features/ask-coco/ask-coco.md)
- [x] Streamlit floor **1.55** (`copilot_rail` needs `st.popover(key=)`): `pyproject.toml`, the window's check, README, API reference, deployment, training pack, one-pager (`tests/test_streamlit_floor.py` keeps them equal)
- [x] Public kit: `doc/releases/0.2.0/`
- [x] Outreach kit: `doc-dev/releases/0.2.0/` (drafts only)

## 2. Quality gates (required)

- [x] `make check` — ruff, 637 passed, 1 skipped, 742 subtests (2026-10-20)
- [x] `make test-all` — the above, 8 browser tests (the window, and the 0.1.9 chat helpers on their own harness), `pip-audit`: no known vulnerabilities (2026-10-20, Streamlit 1.60.0)
- [x] **0.1.9 compatibility** — `tests/test_compat_019.py` holds the public API to `tests/fixtures/api_0.1.9.json`; the 0.1.9 tests of the chat family are kept (2026-10-20)
- [x] Locked packages bumped for the 23 open Dependabot alerts (`gitpython`, `mcp` kept on 1.x, `pyjwt`, `snowflake-connector-python`, `urllib3`); the alerts close once this is on `main`
- [ ] Manual feature checklists — [`features/ask-coco/`](../../features/ask-coco/)
- [ ] Live CoCo smoke (`make modern-chat`, `make simple-chat`)

## 3. Visuals (required for community posts)

- [x] Screenshots captured per [`screenshots/README.md`](screenshots/README.md) (2026-10-20, scripted agent)
- [x] At least one **hero** image suitable for LinkedIn / GitHub Release: `screenshots/hero.png`; LinkedIn visual [`visual-linkedin.png`](../../../doc-dev/releases/0.2.0/visual-linkedin.png) (dev-only)
- [ ] Optional: 15–30s screen recording (Both → Minimize → Restore)

## 4. GitHub + PyPI (required before this is public)

Follow [`doc/deployment/publish.md`](../../deployment/publish.md). Done 2026-10-20.

- [x] Merge to `-dev` `main` ([#17](https://github.com/DevoteamSP/streamlit-coco-dev/pull/17); #16, the same lock bumps, closed as superseded)
- [x] `COMMIT=1 PUSH=1 MESSAGE="Release 0.2.0" make sync-release` to `lletourmy/streamlit-coco` and to `DevoteamSP/streamlit-coco` (identical trees)
- [x] Tag `v0.2.0` on public `streamlit-coco` and push (also mirrored on `DevoteamSP/streamlit-coco`)
- [x] Confirm GitHub Release + PyPI wheel; SBOM attached to both Releases. A clean `pip install "streamlit-coco[sdk]==0.2.0"` gives 0.2.0 and the 0.1.9 API guard passes against it
- [x] GitHub Release body: the CHANGELOG `[0.2.0]` section (written by the workflow). Screenshots are in the repository, not in the body

## 5. Narrative & outreach (strongly recommended — `doc-dev`)

- [x] LinkedIn draft — [`linkedin.md`](../../../doc-dev/releases/0.2.0/linkedin.md) (not posted)
- [x] Medium draft — [`medium.md`](../../../doc-dev/releases/0.2.0/medium.md) (not posted)
- [x] Community pass — [`COMMUNITY.md`](../../../doc-dev/releases/0.2.0/COMMUNITY.md) (not posted)
- [ ] Refresh [`doc/marketing/one-pager.md`](../../marketing/one-pager.md) if positioning changed
- [x] Paste published URLs below

### Published URLs

| Channel | URL | Date |
| --- | --- | --- |
| GitHub Release (lletourmy) | https://github.com/lletourmy/streamlit-coco/releases/tag/v0.2.0 | 2026-10-20 |
| GitHub Release (DevoteamSP) | https://github.com/DevoteamSP/streamlit-coco/releases/tag/v0.2.0 | 2026-10-20 |
| PyPI | https://pypi.org/project/streamlit-coco/0.2.0/ | 2026-10-20 |
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
