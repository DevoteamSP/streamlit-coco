# Release checklist — 0.3.1

**Owner:** streamlit-coco maintainers
**Target tag date:** 2026-11-20 (`v0.3.1`, annotated, on `lletourmy/streamlit-coco`). **Not tagged yet.**
**GitHub Release / PyPI:** see *Published URLs* below (filled in after the tag)

Patch cut of [`0.3.0`](../0.3.0/CHECKLIST.md): one opt-in option and fixes. Outreach drafts: [`../../../doc-dev/releases/0.3.1/`](../../../doc-dev/releases/0.3.1/) (dev-only).

---

## 1. Product docs

- [x] **`pyproject.toml`**: `version = "0.3.1"` (and `streamlit_coco.__version__`, `uv.lock`, `examples/app_builder/uv.lock`: only the `streamlit-coco` version line of each lock changed)
- [x] **`CHANGELOG.md`**: `[Unreleased]` to `## [0.3.1] — 2026-11-20`; fresh `[Unreleased]` at top. **Re-date at the tag if it slips.**
- [x] **`doc/roadmap.md`**, **`doc/prd.md`**, **`README.md`**, **`doc/releases/README.md`**, **`doc/api.md`**: version and status (`settings_file` was already in `doc/api.md`)
- [x] Feature: [`features/settings-file/feature.md`](../../features/settings-file/feature.md) and [`features/ask-coco/ask-coco.md`](../../features/ask-coco/ask-coco.md) (the "settings file of its own" section)
- [x] Public kit `doc/releases/0.3.1/`; outreach kit `doc-dev/releases/0.3.1/` (drafts only)
- [ ] **Public GitHub issues**: nothing to close for 0.3.1; the 0.3.0 comments are still unposted ([`doc-dev/releases/0.3.0/ISSUES.md`](../../../doc-dev/releases/0.3.0/ISSUES.md))

## 2. Quality gates

- [x] the full gate (`doc/testing.md`), 2026-11-20: lint clean (the first run found 16 E501 in code of the last two commits: fixed by `ruff format` of five files and two hand edits, no behaviour change); 798 passed and 1 skipped; 20 browser tests; `pip-audit` clean after `msgpack` 1.2.1 to 1.2.4 in the root lock (CVE-2026-114613, a dev-only transitive of `pip-audit`; only that package block changed, `uv lock` on uv 0.13.6 would have rewritten the whole file); `audit_locks`: clean
- [x] **Compatibility with released versions**: new `tests/fixtures/api_0.3.1.json` and `tests/test_compat_031.py` (the only difference from the 0.3.0 snapshot is `CocoOptions.settings_file`, last, default `None`); `test_compat_019`, `_022` and `_030` unchanged
- [ ] `uv run --extra dev python scripts/release_check.py`: version free (PyPI latest 0.3.0, tag free), audit clean; **sync step fails**: 44 generated files of `examples/app_builder/out/` would go public (restore them from the public clone or delete them), and the public clone `../streamlit-coco` does not exist yet; one Dependabot alert (high, `uv.lock`) is open until the lock fix is pushed
- [x] Wheel and sdist built (`uv build`): `0.3.1`, no `doc-dev`, no `out/`. [ ] installed in a clean environment
- [ ] **Live checklist rows 34 to 36** ([`features/ask-coco/test-checklist.md`](../../features/ask-coco/test-checklist.md): a plugin whose hook writes a file, with and without `settings_file`, and a missing file) on a real Cortex Code: **not run**. Unit-tested only (`tests/test_cortex.py`, `tests/test_options.py`). Needs a Cortex Code with `--config` (1.2.45 has it)

## 3. GitHub + PyPI

Follow [`doc/deployment/publish.md`](../../deployment/publish.md). The public CI runs on a tree with no lock and the newest uv: run its steps on a copy of the synced tree before the tag (see the 0.3.0 checklist).

- [ ] Merge `feat/0.3.1` into `-dev` `main`
- [ ] Public sync to `lletourmy/streamlit-coco` (`COMMIT=1 PUSH=1 MESSAGE="Release 0.3.1" bash scripts/sync_release.sh`); CI and Security green on the pushed commit
- [ ] Tag `v0.3.1` (annotated) on public `streamlit-coco`; the Release workflow succeeds
- [ ] Confirm the GitHub Release (wheel, sdist, SBOM) and PyPI; `pip install "streamlit-coco[sdk]==0.3.1"` in a clean environment imports and reports `0.3.1`
- [ ] Mirror on `DevoteamSP/streamlit-coco` (same tree, annotated tag; no PyPI upload by design)

## 4. Outreach (optional for a patch)

- [x] LinkedIn / Medium / community drafts in `doc-dev/releases/0.3.1/` (not posted)

### Published URLs

| Channel | URL | Date |
| --- | --- | --- |
| GitHub Release | | |
| PyPI | | |
| GitHub Release (DevoteamSP mirror) | | |
| LinkedIn | | |

## 5. Sign-off

| Role | Name | Date |
| --- | --- | --- |
| Engineering | | |
| Docs / product | | |
