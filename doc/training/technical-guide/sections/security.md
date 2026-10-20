# Security

Source: `doc/security/threat-model.md` (v1.0, 2026-07-28), `doc/security/findings-report.md`
(2026-07-28, version audited 0.1.0), `.github/workflows/security.yml`.

## Roles and grants

streamlit-coco does not manage Snowflake grants and ships no recommended
role definition. What it actually does with the connected role:

- The library delegates all Snowflake authentication to the CoCo CLI / SDK
  and the OS-level Snowflake connection config. It never evaluates or
  restricts what the connected role can do.
- Every SQL statement the agent runs goes through the agent's own SQL tool,
  gated by the approval flow described below. The **effective SQL
  permissions in a session are exactly the connected role's grants** — the
  approval gate controls whether a statement runs, not what it is allowed to
  touch once approved.
- **Recommendation (least privilege): connect with a role scoped to the
  schemas and warehouse the session actually needs, not `ACCOUNTADMIN`.**
  A role with `ACCOUNTADMIN` or an equivalent broad grant such as
  `MANAGE WAREHOUSES` (which can modify and operate every warehouse in the
  account, not only the one a demo uses) means an approved `DROP` or
  `DELETE` in one session can reach objects outside the intended scope. This
  guide does not name a specific role or grant set because none is checked
  into the repo — connect the demo/example apps with a role that owns only
  the database, schema, and warehouse the example needs.

A dedicated least-privilege role recommendation document does not exist yet
(tracked as SEC-02, open — see below and [limits](limits.html)).

## Secrets handling

- Snowflake credentials (PAT, key-pair, or SSO) live in the OS-level
  Snowflake config (`~/.snowflake/connections.toml` or legacy
  `config.toml`) or in an OS keyring, never in this library's code or in
  Streamlit session state.
- The library never logs or stores credentials itself; authentication is
  delegated entirely to the CoCo CLI / SDK.
- `.gitignore` covers `.env`, `*.secret`, `*.key`, and `client_*.yaml`.
- Do not commit a Snowflake connections file or any of the patterns above to
  the repo. There is no in-repo secrets store to configure.

## Data handled

| Data | Sensitivity | Where it lives |
|---|---|---|
| User prompts and agent transcripts | Medium–High | Streamlit session state, in-memory |
| SQL results rendered in the UI | Medium–High | In-memory; may contain PII depending on the query the agent ran |
| Snowflake credentials | High | OS keyring / `~/.snowflake/` — never in the repo or in library state |
| CoCo session NDJSON stream | Medium | Local socket / SDK transport (local deployment target: no network hop) |

Whether SQL results shown to a given viewer contain data that viewer should
not see is the connected app's responsibility (row-access policies, or not
sharing a session across users) — the library does not filter query results.

## Threat-model summary

From `doc/security/threat-model.md` §4:

- **Prompt injection triggers dangerous tools — High severity.** Mitigated
  by approval gates: `PermissionManager` intercepts before execution, and
  the user must explicitly approve. The threat model additionally
  recommends connecting with a least-privilege role, not `ACCOUNTADMIN`
  (see Roles and grants above).
- **"Always allow" escalation — Medium severity.** Mitigated by scope:
  "always allow" is per-tool, per-session only, held in
  `PermissionManager.always_allowed_tools`, and clears on session reset or
  process restart (see Revocation below). `AskUserQuestion` and
  `ExitPlanMode` never expose an "Always allow" option.
- **Repudiation — no persisted log of approved destructive actions —
  Medium severity, open.** The transcript exists only in Streamlit session
  state; nothing is written to durable storage. Tracked as **SEC-01**
  (open, target v0.2) — see [limits](limits.html).
- **Information disclosure via secrets in transcript/logs — Medium
  severity.** Mitigated: the library does not log credentials, and the SDK
  redacts them from its output.
- **Elevation of privilege via a compromised dependency — supply chain.**
  Mitigated by `pip-audit` in CI and Gitleaks scanning the repo (see CI
  security posture below); `uv.lock` is committed for reproducible builds.

## Revocation

"Always allow" for a tool is scoped to the running `CocoSession` instance.
It clears automatically on:

- `session.reset()`
- `session.close()` (and process restart)

There is no persistent "always allow" policy store, and no UI action to
revoke a single tool's "always allow" without resetting the whole session.

## CI security posture (current)

CI runs two scanners, not three:

- **Gitleaks** (CLI binary, not `gitleaks-action@v2`) — secret scanning on
  every pull request, every push to `main`, and weekly (Monday 06:00 UTC).
- **`pip-audit --skip-editable`** — dependency vulnerability scanning on
  the same triggers.

**CodeQL is not running.** `doc/security/findings-report.md` still lists
CodeQL as "CI-only (GitHub Actions)," but `.github/workflows/security.yml`
was changed in `0.1.5` to drop the CodeQL job — a private GitHub
organization needs a GitHub Advanced Security (GHAS) license to upload
CodeQL results, which this org does not have, so the analyze step would
fail as a configuration error. The workflow file's own comment states this
explicitly. Treat CodeQL as **not active** in this repo today; do not cite
the findings-report table as current.

Both `security.yml` jobs are also mirrored in `ci.yml` as
`continue-on-error: true` steps on the `test` job (non-blocking until a
clean baseline is established there too).

## Open and resolved items (`threat-model.md` §7)

| ID | Description | Status |
|---|---|---|
| SEC-01 | Persist an approval audit log (who approved what, when) | **Open**, target v0.2 |
| SEC-02 | Document a least-privilege role recommendation for the connected Snowflake account, as a dedicated deliverable | **Open**, target v0.2 (this page's Roles and grants section is interim guidance, not that deliverable) |
| SEC-03 | Commit `uv.lock` for reproducible builds | **Resolved** — the lockfile is committed today |
| SEC-04 | Add SBOM generation to the release workflow | **Resolved**, shipped `0.1.5` — `release.yml` generates a CycloneDX SBOM (`sbom-vX.Y.Z.cdx.json`) attached to the GitHub Release on every tag |

## Manual review findings (`findings-report.md`, version audited 0.1.0)

- `pip-audit`: 0 known vulnerabilities.
- Gitleaks: 0 leaks across 11 commits scanned.
- Manual review: no `shell=True`, no hardcoded credentials, no `eval()` /
  `exec()` found in the source.
