# Security Findings Report — Streamlit CoCo

**Date**: 2026-07-28  
**Version audited**: 0.1.0  
**Scanned by**: Laurent Letourmy  
**Repository**: `~/dev2/streamlit-coco-dev` (11 commits)

---

## Summary

| Scanner | Scope | Findings | Status |
|---------|-------|----------|--------|
| pip-audit | Python dependencies | 0 vulnerabilities | **Clean** |
| Gitleaks | Git history (secrets) | 0 leaks | **Clean** |
| CodeQL | Static analysis (Python) | — | *CI-only (GitHub Actions)* |

**Overall**: No known vulnerabilities or secrets detected.

---

## 1. Dependency Audit (pip-audit)

**Tool**: `pip-audit` via `uv run pip-audit`  
**Environment**: Python 3.11, uv-managed virtualenv

```
No known vulnerabilities found

Name           Skip Reason
-------------- ---------------------------------------------------------------
streamlit-coco Dependency not found on PyPI and could not be audited (0.1.0)
```

**Notes**:
- `streamlit-coco` itself is skipped because it's not yet published to PyPI — this is expected for pre-release packages.
- All transitive dependencies (streamlit, cortex-code-agent-sdk, etc.) passed with no known CVEs.

---

## 2. Secrets Scan (Gitleaks)

**Tool**: `gitleaks detect --source .`  
**Scope**: 11 commits, ~498 KB scanned

```
7:41AM INF 11 commits scanned.
7:41AM INF scanned ~497837 bytes (497.84 KB) in 1.05s
7:41AM INF no leaks found
```

**Notes**:
- No hardcoded secrets, tokens, or API keys found in git history.
- `.gitignore` covers `.env`, `*.secret`, `*.key`, `client_*.yaml`.

---

## 3. Static Analysis (CodeQL)

**Tool**: GitHub CodeQL (`.github/workflows/security.yml`)  
**Status**: Runs on PR and weekly schedule in CI. Not run locally.

**Last CI run**: Check [GitHub Security tab](https://github.com/DevoteamSP/streamlit-coco-dev/security) for latest results.

---

## 4. Manual Review Observations

| Check | Result |
|-------|--------|
| `shell=True` in source | Not found |
| Hardcoded credentials | Not found |
| `eval()` / `exec()` usage | Not found |
| User input passed to SQL without parameterization | N/A — SQL execution delegated to CoCo agent (approval-gated) |
| Dependencies with known supply-chain risk | None identified |

---

## 5. Remediation Tracker

| ID | Finding | Severity | Status | Resolution |
|----|---------|----------|--------|------------|
| — | No findings | — | — | — |

---

## 6. Next Steps

- [ ] Publish to PyPI so pip-audit can verify the package itself
- [ ] Commit `uv.lock` for reproducible dep resolution
- [x] Add SBOM generation to release workflow (CycloneDX or SPDX)
- [ ] Review CodeQL results after first full CI run on `main`

---

*Report generated manually using local scans. For continuous monitoring, see `.github/workflows/security.yml`.*
