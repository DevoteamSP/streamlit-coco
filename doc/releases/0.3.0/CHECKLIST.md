# Release checklist — 0.3.0

**Owner:** streamlit-coco maintainers
**Tag date:** 2026-10-26 (`v0.3.0`, annotated, on `lletourmy/streamlit-coco` at `3b2bab9`). **Published.** What is left: the public issue comments, the LinkedIn visual and posts, and optionally the Native App page behind its ingress.
**GitHub Release / PyPI:** see *Published URLs* below (filled in after the tag)


Outreach drafts: [`../../../doc-dev/releases/0.3.0/`](../../../doc-dev/releases/0.3.0/) (dev-only, not public sync).

---

## 1. Product docs (required)

- [x] **`pyproject.toml`** — `version = "0.3.0"` (and `streamlit_coco.__version__`, `uv.lock`, `examples/app_builder/uv.lock`)
- [x] **`CHANGELOG.md`** — `[Unreleased]` → `## [0.3.0] — 2026-10-26`; fresh `[Unreleased]` left at top. **Re-date at the tag.**
- [x] **`doc/roadmap.md`** — Status / Last updated / Last cut; the `0.3.0` section
- [ ] **Public GitHub issues** — drafts in [`doc-dev/releases/0.3.0/ISSUES.md`](../../../doc-dev/releases/0.3.0/ISSUES.md), **nothing posted**: close public #15 and dev #4; comment on public #12, #8, #14. Post after the tag, with the release URL
- [x] **`doc/prd.md`** — status line, deployment table, decisions 14.8 and 14.9
- [x] **`doc/api.md`** — the managed agent (uploads, `SANDBOX_WHERE`), `ask_coco(audit=)`, `AuditLog`, `FolderPolicy(where=)`, `check_environment(managed=)`
- [x] Feature narrative: [`features/ask-coco/ask-coco.md`](../../features/ask-coco/ask-coco.md) section 8
- [x] Security: [`security/threat-model.md`](../../security/threat-model.md) (SEC-01 and SEC-02 closed, the managed agent and the Native App)
- [x] Streamlit floor unchanged (**1.55**); `tests/test_streamlit_floor.py` passes
- [x] Public kit: `doc/releases/0.3.0/`
- [x] Outreach kit: `doc-dev/releases/0.3.0/` (drafts only)
- [x] **SDK pin.** `snowflake-cortex-agent-sdk` is a public preview (`0.0.x`) and can break between versions: the `sdk` and `dev` extras say `>=0.0.3,<0.1` (the lock holds `0.0.3`). Re-check the newest `0.0.x` against the live checklist before the tag

## 2. Quality gates (required)

- [x] `make test-all` — lint, 775 passed and 1 skipped (a Windows-only 8.3 names test), 20 browser tests, `pip-audit`: no known vulnerabilities (2026-10-26, Streamlit 1.66.1)
- [x] Browser tests include `tests/e2e/test_managed_window.py` (the managed window on a scripted stream)
- [x] `make audit` — no known vulnerabilities, root lock and `examples/app_builder/uv.lock` (2026-10-26)
- [x] `make release-check` — 5 PASS: version free on PyPI and the public tags, the public CHANGELOG known, locks audited, no open Dependabot alert, sync dry run clean (2026-10-26)
- [x] **Compatibility with released versions** — `tests/test_compat_019.py`, `test_compat_022.py` and the new `test_compat_030.py` (`tests/fixtures/api_0.1.9.json`, `api_0.2.2.json`, `api_0.3.0.json`); every new parameter is keyword-only, last, with a default. Also checked once by hand: the current package accepts the public API of **all 10 tags** (v0.1.0 to v0.2.2), 0 incompatibilities, with the old SDK installed for the snapshots
- [x] **Wheel and sdist** — built (`uv build`): wheel 0.5 MB, 78 files, `Version: 0.3.0`, the SDK extra `>=0.0.3,<0.1`, the static assets, `audit.py`, `managed.py` and `backend.py` inside, no `doc-dev`; installed with the `sdk` extra in a clean Python 3.11 environment: imports, `check_environment(managed=True).ready`, and `ask_coco` on the scripted agent runs with no exception
- [x] Manual feature checklist — [`features/ask-coco/test-checklist.md`](../../features/ask-coco/test-checklist.md): rows 2 to 5 and 21 to 31 run on 2026-10-26 on the real agents through the window's conversation (Cortex Code 1.2.18; `snowflake-cortex-agent-sdk` 0.0.3 on a Snowflake test account), results in the table. **Not run:** rows 1, 6 to 20 (not repeated: nothing they test changed except the gate's audit hook), row 33's page behind the ingress (needs a login)
- [x] The managed window **in a browser on a real account** (`make managed`, 2026-10-26): logged in with a profile and role `PUBLIC`; the first screen said "It works in a Snowflake sandbox, not on this computer"; "Write a file" asked **"Allow CoCo to run a command in the Snowflake sandbox?"** with **Where: The Snowflake sandbox** and the exact command behind **Show command**; Allow ran it and the answer came back; no console error, no warning in the server log
- [ ] Token renewal over many hours, sandbox SQL under caller's rights, two skills in one conversation: not tested (stated in the feature file)

## 3. Visuals (required for community posts)

- [x] Screenshots (2026-10-26, scripted stream of the client, no login): `hero.png`, `01-first-screen.png`, `02-attach.png`, `03-audit.png`, `04-shop-library.png` — `.venv/bin/python scripts/capture_release_screens.py managed shop`; not captured: the Native App page (needs a login)
- [x] Intro motion piece: [`doc-dev/releases/0.3.0/intro-video.html`](../../../doc-dev/releases/0.3.0/intro-video.html) (20 s, self-contained HTML, dev-only)
- [ ] LinkedIn visual `visual-linkedin-0.3.0.png` (dev-only), super title `streamlit-coco 0.3.0` — not made (the post can go with `hero.png`)
- [ ] Optional: 15–30s screen recording (attach a CSV → ask → Allow → answer)

## 4. GitHub + PyPI (required before this is public)

**Before the tag, the public repository's CI and Security workflows must be green on the pushed commit** (the public tree has no `uv.lock`, so CI resolves fresh with the newest uv; run its steps on a copy of the synced tree first). On 2026-10-26 the first sync failed both and was fixed before the tag (CHANGELOG, Fixed). Three things the dev repo's own gates had not shown, all fixed before the tag: (1) a fresh `uv sync` on the public tree failed on the newest uv (0.13.5) because `[tool.uv] environments` made it resolve for Pyodide, where `playwright` has no wheel; (2) gitleaks flagged the fake credentials the audit and skills-shop tests use on purpose (`.gitleaks.toml` allowlist); (3) the 0.2.2 and 0.3.0 API snapshots, taken on macOS, failed on Linux because `Command.platform` defaults to the machine's platform. Lesson: run the public CI's steps on a copy of the synced tree (no lock, newest uv) before the first push.

Follow [`doc/deployment/publish.md`](../../deployment/publish.md).

- [x] Merge `dev/0.3.0-remote-api` to `-dev` `main` (merge commit `596aa44`, then the fixes below on `main`)
- [x] Public sync to `lletourmy/streamlit-coco`, three commits: `51145b6` "Release 0.3.0" (CI and Security **failed**: see below), `268c272` (CI fixes), `3b2bab9` (compat tests no longer depend on the platform): **CI and Security green on `3b2bab9`**
- [x] Tag `v0.3.0` on public `streamlit-coco`, annotated, pushed (on `3b2bab9`)
- [x] Confirm GitHub Release + PyPI: the Release workflow succeeded; the GitHub Release has the wheel, the sdist and the CycloneDX SBOM; PyPI lists `streamlit_coco-0.3.0-py3-none-any.whl` and `streamlit_coco-0.3.0.tar.gz`; `pip install "streamlit-coco[sdk]==0.3.0"` in a clean Python 3.11 environment imports, reports `0.3.0` with `snowflake-cortex-agent-sdk` 0.0.3, and runs `ask_coco` on the scripted agent
- [ ] GitHub Release body: the CHANGELOG excerpt is there (generated); `hero.png` is not in it yet
- [ ] Mirror the commit and the tag on `DevoteamSP/streamlit-coco` (optional)

## 5. Narrative & outreach (strongly recommended — `doc-dev`)

- [x] LinkedIn draft — [`linkedin.md`](../../../doc-dev/releases/0.3.0/linkedin.md) (not posted)
- [x] Medium draft — [`medium.md`](../../../doc-dev/releases/0.3.0/medium.md) (a brief, not posted)
- [x] Community pass — [`COMMUNITY.md`](../../../doc-dev/releases/0.3.0/COMMUNITY.md) (not posted)
- [ ] Refresh [`doc/marketing/one-pager.md`](../../marketing/one-pager.md) if positioning changed
- [ ] Paste published URLs below

### Published URLs

| Channel | URL | Date |
| --- | --- | --- |
| GitHub Release | https://github.com/lletourmy/streamlit-coco/releases/tag/v0.3.0 | 2026-10-26 |
| PyPI | https://pypi.org/project/streamlit-coco/0.3.0/ | 2026-10-26 |
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
