# Release checklist — 0.2.2

**Owner:** streamlit-coco maintainers
**Target tag date:** 2026-10-25  
**GitHub Release / PyPI:** see *Published URLs* below (filled in after the tag)

Do not run `make sync-release` or tag `v0.2.2` until Product docs + QA are done.

Outreach drafts: [`../../../doc-dev/releases/0.2.2/`](../../../doc-dev/releases/0.2.2/) (dev-only, not public sync).

---

## 1. Product docs (required)

- [x] **`pyproject.toml`** — `version = "0.2.2"` (and `streamlit_coco.__version__`, `uv.lock`)
- [x] **`CHANGELOG.md`** — `[Unreleased]` → `## [0.2.2] — 2026-10-25`; fresh `[Unreleased]` left at top
- [x] **`CHANGELOG.md`** at tag time: heading date `2026-10-25` is the tag date (the GitHub Release body is this section)
- [x] **`doc/roadmap.md`** — Status / Last updated / Last cut; `v0.2.2` section; Now is still API mode (`0.3.0`)
- [ ] **Public GitHub issues** — not touched. Close resolved, comment on progressed, propose new ones from `doc/roadmap.md`
- [x] **`doc/prd.md`** — status line
- [x] **`doc/api.md`** — version line; `Features(dock, full_page)`; `ask_coco(on_layout, split)`
- [x] Feature narrative: [`features/ask-coco/ask-coco.md`](../../features/ask-coco/ask-coco.md) (window places, callback, split, hints, title-bar click)
- [x] Streamlit floor unchanged (**1.55**); `tests/test_streamlit_floor.py` passes
- [x] Public kit: `doc/releases/0.2.2/`
- [x] Outreach kit: `doc-dev/releases/0.2.2/` (drafts only)

## 2. Quality gates (required)

- [x] `make check` — ruff, 637 passed, 1 skipped, 742 subtests (2026-10-25, Streamlit 1.66.1)
- [x] `make e2e` — 15 browser tests (the window, and the 0.1.9 chat helpers on their own harness), including the new `tests/e2e/test_window_layout.py` (2026-10-25, Streamlit 1.66.1)
- [x] `make test-all` — the above and `pip-audit`: **no known vulnerabilities** (2026-10-25). The first run found 41 in the development lock (`pillow 12.3.0`: 37, fixed in 13.0.0; `filelock 3.32.0`: 3, fixed in 4.2.1; `certifi 2026.7.22`: 1, fixed in 2026.10.19). Fixed by `uv lock --upgrade-package certifi --upgrade-package filelock --upgrade-package pillow --upgrade-package streamlit`: Streamlit 1.60.0 → 1.66.1 (it capped `pillow<13`), `pillow` 13.0.0, `certifi` 2026.10.23; and a `[tool.uv] override-dependencies` for `filelock>=4.2.1` on Python 3.11+ (4.2.4 locked), because `snowflake-connector-python` (via `cortex-code-agent-sdk 1.0.7`) still says `filelock<4` but only uses `FileLock`, `BaseFileLock` and `Timeout`. The override is in the development lock only, not in the wheel; Python 3.10 keeps `filelock` 3.x. The package floor stays Streamlit 1.55; the screenshots were captured on 1.66.1 (the locked version)
- [x] **0.1.9 compatibility** — `tests/test_compat_019.py` holds the public API to `tests/fixtures/api_0.1.9.json`; every new parameter is keyword-only, last, with a default (2026-10-25)
- [x] Manual feature checklists — [`features/ask-coco/`](../../features/ask-coco/) (rows 17–20 are new). Run by the maintainer on 2026-10-25 against a real agent; the Result column of the table is not filled in
- [x] Live CoCo smoke (`make modern-chat`, `make app-builder`, `make bi-semantic` without `STREAMLIT_COCO_AGENT=mock`). Run by the maintainer on 2026-10-25; the outcome of each step is not written down here
- [x] Flaky once, passes alone and in the full runs: `test_attached_file_lands_in_the_folder` (a slow machine)

## 3. Visuals (required for community posts)

- [x] Screenshots captured per [`screenshots/README.md`](screenshots/README.md) (2026-10-25, scripted agent): `hero.png`, `01-full-page.png`, `02-hint.png`
- [x] LinkedIn visual [`visual-linkedin-0.2.2.png`](../../../doc-dev/releases/0.2.2/visual-linkedin-0.2.2.png) (dev-only), super title `streamlit-coco 0.2.2`
- [ ] Optional: 15–30s screen recording (float → attach right → full page → back)

## 4. GitHub + PyPI (required before this is public)

Follow [`doc/deployment/publish.md`](../../deployment/publish.md). Published on 2026-10-25.

- [ ] Merge to `-dev` `main` (`release/0.2.2` is not merged or pushed yet)
- [x] Public sync: commit `f6520a7` "Release 0.2.2" on `lletourmy/streamlit-coco` `main` (`MESSAGE="Release 0.2.2" make sync-release`, pushed 2026-10-25). Before it: the unmerged `docs/0.2.0-publish-urls` branch (the published 0.2.1) was merged into this branch, and the generated `out/` files were cleaned
- [x] Tag `v0.2.2` on public `streamlit-coco`, annotated, pushed
- [x] Confirm GitHub Release + PyPI wheel: Release, CI and Security workflows succeeded; PyPI lists `streamlit_coco-0.2.2-py3-none-any.whl` and `streamlit_coco-0.2.2.tar.gz`; the GitHub Release has the wheel, the sdist and the CycloneDX SBOM
- [ ] GitHub Release body: CHANGELOG excerpt is there (generated from the `0.2.2` section); `hero.png` is not in it yet
- [ ] Mirror the commit and the tag on `DevoteamSP/streamlit-coco` (optional, see publish.md)

## 5. Narrative & outreach (strongly recommended — `doc-dev`)

- [x] LinkedIn draft — [`linkedin.md`](../../../doc-dev/releases/0.2.2/linkedin.md) (not posted)
- [x] Medium draft — [`medium.md`](../../../doc-dev/releases/0.2.2/medium.md) (not posted)
- [x] Community pass — [`COMMUNITY.md`](../../../doc-dev/releases/0.2.2/COMMUNITY.md) (not posted)
- [ ] Refresh [`doc/marketing/one-pager.md`](../../marketing/one-pager.md) if positioning changed
- [ ] Paste published URLs below

### Published URLs

| Channel | URL | Date |
| --- | --- | --- |
| GitHub Release (lletourmy) | https://github.com/lletourmy/streamlit-coco/releases/tag/v0.2.2 | 2026-10-25 |
| PyPI | https://pypi.org/project/streamlit-coco/0.2.2/ | 2026-10-25 |
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
