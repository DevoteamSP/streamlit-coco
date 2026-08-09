# Threat Model — Streamlit CoCo

**Version**: 1.0  
**Date**: 2026-07-28  
**Author**: Laurent Letourmy  
**Deployment context**: local development / Streamlit in Snowflake (SiS) / SPCS

---

## 1. Deployment Topology

```
┌─────────────────────────────────────────────────────────────┐
│  Streamlit App (local or SiS)                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  streamlit-coco library                               │  │
│  │  ┌──────────┐  ┌──────────────┐  ┌───────────────┐   │  │
│  │  │  panel() │  │PermissionMgr │  │  query()      │   │  │
│  │  │  chat()  │  │(HITL gates)  │  │  (headless)   │   │  │
│  │  └────┬─────┘  └──────┬───────┘  └───────┬───────┘   │  │
│  │       │               │                   │           │  │
│  │       └───────────────┼───────────────────┘           │  │
│  │                       ▼                               │  │
│  │            cortex-code-agent-sdk                       │  │
│  └───────────────────────┼───────────────────────────────┘  │
│                          │ NDJSON streaming (local socket)   │
│                          ▼                                   │
│              CoCo CLI / Agent backend                        │
│                          │                                   │
│                          ▼                                   │
│              Snowflake Cortex (LLM + tools)                  │
└─────────────────────────────────────────────────────────────┘
```

Key surfaces:
- **Network exposure**: local only (dev) / internal Snowflake network (SiS)
- **Auth model**: Snowflake SSO / PAT / key-pair (delegated to CoCo CLI / SDK)
- **Data touched**: user prompts, agent transcripts (may contain SQL results), Snowflake credentials (in OS config, never in code)

---

## 2. Assets to Protect

| Asset | Sensitivity | Location |
|-------|-------------|----------|
| Snowflake credentials (PAT / key-pair) | High | OS keyring / `~/.snowflake/` — never in repo |
| User prompts & agent transcripts | Medium–High | Streamlit session state (in-memory) |
| SQL results rendered in UI | Medium–High | In-memory; may contain PII depending on query |
| CoCo session NDJSON stream | Medium | Local socket / SDK transport |
| Library source code | Low | Public GitHub repo |

---

## 3. Threat Actors

| Actor | Motivation | Access level |
|-------|-----------|-------------|
| Malware on developer machine | Credential theft, session hijack | Local filesystem + process |
| Malicious dependency (supply chain) | Code execution, data exfiltration | pip install, CI |
| Malicious PR contributor | Backdoor, secret exfiltration | Repo write (PR review required) |
| End user crafting adversarial prompts | Prompt injection → unintended tool execution | Streamlit UI input |
| Co-tenant in shared SiS environment | Session data leakage | Streamlit server process |

---

## 4. STRIDE Analysis

| Threat | Component | Severity | Status |
|--------|-----------|----------|--------|
| **S**poofing — impersonate Snowflake session | SDK auth delegation | Low | mitigated: auth handled by CoCo CLI, not this library |
| **T**ampering — modify agent response in transit | NDJSON stream parser | Low | mitigated: local socket, no network hop in dev; TLS in SiS |
| **T**ampering — malicious tool input bypasses approval | PermissionManager | Medium | mitigated: HITL gates block Edit/Write/Bash/SQL by default |
| **R**epudiation — no log of approved destructive actions | Approval flow | Medium | open: transcript in session state only, not persisted |
| **I**nformation disclosure — secrets in transcript/logs | display module | Medium | mitigated: library does not log credentials; SDK redacts |
| **I**nformation disclosure — SQL results with PII shown to unauthorized viewer | panel() UI | Medium | accepted: app developer responsibility (row-access policies) |
| **D**enial of service — infinite streaming from malformed NDJSON | message parser | Low | mitigated: SDK timeout; session can be stopped |
| **E**levation of privilege — "always allow" bypasses future approvals | PermissionManager | Medium | mitigated: always-allow is per-tool, per-session only, resets on restart |
| **E**levation of privilege — prompt injection triggers dangerous tools | CoCo agent | High | mitigated: approval gates intercept before execution; user must approve |

---

## 5. Attack Scenarios

### Scenario 1: Prompt injection bypasses approval gate

- **Path**: User crafts a prompt that tricks the agent into calling `snowflake_sql_execute` with a destructive statement (DROP, DELETE)
- **Impact**: Data loss in the connected Snowflake account
- **Mitigation**: 
  - Approval gates intercept all SQL/Write/Bash tools before execution (default `permission_mode`)
  - User sees the full SQL and must explicitly approve
  - Recommended: connect with a least-privilege role (not ACCOUNTADMIN)

### Scenario 2: Supply chain attack via compromised dependency

- **Path**: Attacker publishes malicious version of `cortex-code-agent-sdk` or transitive dep
- **Impact**: Arbitrary code execution in the Streamlit process
- **Mitigation**:
  - `pip-audit` in CI (`security.yml`) scans for known vulnerabilities
  - `uv.lock` pins exact versions (once committed)
  - Gitleaks prevents secrets from entering the repo

### Scenario 3: Session state leakage in shared SiS deployment

- **Path**: In a multi-user SiS app, one user's transcript (containing SQL results) is accidentally rendered to another user
- **Impact**: Unauthorized data exposure
- **Mitigation**:
  - `CocoSession` is keyed per Streamlit session (per-browser tab)
  - Streamlit's native session isolation prevents cross-user state bleed
  - App developers should not store transcripts in shared caches

### Scenario 4: "Always allow" escalation

- **Path**: User clicks "Always allow" for SQL tool; later a prompt-injected query runs without review
- **Impact**: Unreviewed destructive SQL execution
- **Mitigation**:
  - "Always allow" is scoped per-tool, per-session (clears on page refresh / restart)
  - Documentation warns against "Always allow" in production deployments
  - Future: add configurable deny-list patterns even when "always allow" is active

---

## 6. Out of Scope

By design, this library does NOT address:
- **Snowflake authentication** — delegated entirely to CoCo CLI / SDK and OS credential store
- **Encryption at rest** — data resides in Snowflake (encrypted by default) or in-memory
- **Network perimeter security** — SiS / SPCS networking managed by Snowflake
- **LLM safety / content filtering** — handled by Cortex backend
- **Multi-tenant app authorization** — app developer's responsibility to implement RBAC

---

## 7. Open Items

| ID | Description | Owner | Target |
|----|-------------|-------|--------|
| SEC-01 | Persist approval audit log (who approved what, when) | Laurent Letourmy | v0.2 |
| SEC-02 | Document least-privilege role recommendation for connected Snowflake account | Laurent Letourmy | v0.2 |
| SEC-03 | Commit `uv.lock` for reproducible builds (currently gitignored) | Laurent Letourmy | v0.1.1 |
| SEC-04 | Add SBOM generation to CI release workflow | Laurent Letourmy | ✅ `0.1.5` (CycloneDX on tag release) |
