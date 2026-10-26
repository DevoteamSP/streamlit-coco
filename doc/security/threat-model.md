# Threat Model — Streamlit CoCo

**Version**: 1.1  
**Date**: 2026-10-26 (1.0: 2026-07-28)  
**Author**: Laurent Letourmy  
**Deployment context**: local development / Streamlit in Snowflake (SiS) / SPCS; the managed agent (`0.3.0`, experimental) runs in Snowflake's sandbox

---

## 1. Deployment Topology

```
┌─────────────────────────────────────────────────────────────┐
│  Streamlit App (local or SiS)                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  streamlit-coco library                               │  │
│  │  ┌──────────┐  ┌──────────────┐  ┌───────────────┐   │  │
│  │  │  window  │  │ Gate+Policy  │  │  query()      │   │  │
│  │  │ (ask_coco)│ │(Allow/Decline)│ │  (headless)   │   │  │
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
- **Auth model**: Snowflake SSO / PAT / key-pair (delegated to CoCo CLI / SDK). Managed agent: the session token of a connector login (`options_from_connection`), a PAT, or the service token of a Native App; the agent works with the rights of that role, or of the application
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
| **R**epudiation — no log of approved destructive actions | Approval flow | Medium | mitigated in `0.3.0`: `AuditLog` (`ask_coco(audit=)`) writes one line per decision (who, what the user was shown, when); off by default, not tamper-proof; the exact input is redacted for what looks like a credential and each allowed call gets an `outcome` line (SEC-01) |
| **I**nformation disclosure — secrets in transcript/logs | display module | Medium | mitigated: library does not log credentials; SDK redacts |
| **I**nformation disclosure — SQL results with PII shown to unauthorized viewer | the window | Medium | accepted: app developer responsibility (row-access policies) |
| **D**enial of service — infinite streaming from malformed NDJSON | message parser | Low | mitigated: SDK timeout; session can be stopped |
| **E**levation of privilege — "always allow" bypasses future approvals | PermissionManager | Medium | mitigated: always-allow is per-tool, per-session only, resets on restart |
| **E**levation of privilege — prompt injection triggers dangerous tools | CoCo agent | High | mitigated: approval gates intercept before execution; user must approve |
| **E**levation of privilege — the managed agent's own "Allow all bash for this session" | Managed agent | High | mitigated: the run is always `always_ask`; only "Allow this command" (one call) is ever sent, never the session-wide option; no one-call option means decline |
| **E**levation of privilege — a call the server rates "no risk" runs without a request | Managed agent | Medium | accepted, documented: the server decides what it asks about (`echo hello` ran unasked; a write asked). The sandbox, and the role of the session, are the limit. Use the least role (section 8) |
| **I**nformation disclosure — a credential in a command ends up in the audit file | Audit log | Medium | mitigated in part: `redact_secrets` rewrites what looks like a credential (named values, bearer tokens, key blocks, URL passwords, common token shapes) before the write; it does **not** catch a secret that looks like nothing (a plain `-p hunter2` argument, a secret inside a written file, an encoded one) nor personal data in SQL: the file is sensitive, owner-readable only |
| **I**nformation disclosure — a file the user attached stays on a stage | Managed upload | Medium | mitigated: a folder of the conversation, removed when it ends (best effort, a failed `REMOVE` is logged); no copy stays in the working folder. Use a stage no one else reads |
| **I**nformation disclosure — the agent is told the developer's folder | Managed agent | Low | mitigated: its own prompt names nothing of this computer (found live in `0.3.0` development) |

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

### Scenario 4: standing permission escalation

- **Path**: User ticks "Do not ask again for SQL statements"; later a prompt-injected statement runs without review
- **Impact**: Unreviewed destructive SQL execution
- **Mitigation**:
  - A standing permission exists only when the host sets `FolderPolicy(standing=True)`; the default offers none
  - It covers one family (commands; changes in this folder; queries that only read; SQL statements; one tool; reading elsewhere) until the conversation ends (New conversation, Disconnect, a changed folder), and the menu lists it with "Ask again"
  - It never covers the `.git` folder, a secret-named file or a place the policy flags; those ask each time
  - A grant for queries does not cover a statement that changes; a grant for statements says nobody will read each call
  - The call is judged again each time, and a call the app cannot read is still refused

---

### Scenario 5: the managed agent runs a command the user did not expect

- **Path**: a prompt-injected file the agent reads in the sandbox makes it run a command that writes, or that reaches out
- **Impact**: bounded by the sandbox and by the role of the session (a SQL call runs with that role's rights, restricted)
- **Mitigation**:
  - The command the server rates risky pauses the run and reaches the policy and the gate: the user reads the exact command and answers; the request says it runs in the Snowflake sandbox
  - Only the one-call allow is sent; the server's session-wide allow never is
  - The `AuditLog` keeps who allowed which command
  - Connect with a role that has the least rights that work (section 8)

### Scenario 6: a Native App's chat acts with the application's rights

- **Path**: a user chats with a skill in a Native App on SPCS; the agent runs as the **application**, not as the user
- **Impact**: the user can have the agent do whatever the application's role may do (`examples/skills_hub_native` grants it `SNOWFLAKE.CORTEX_USER` and `SNOWFLAKE.CORTEX_AGENT_USER`, and its own stage, nothing else)
- **Mitigation**: grant the application only what its job needs; the consumer approves each grant; sandbox SQL under the caller's rights is **not tested** (the earlier hub needed `GRANT CALLER ... TO APPLICATION`); do not offer such an app where users must be told apart by their rights

---

## 6. Out of Scope

By design, this library does NOT address:
- **Snowflake authentication** — delegated entirely to CoCo CLI / SDK and OS credential store (the managed agent: the SDK's authenticators)
- **The sandbox itself** — Snowflake's service; this library only decides what it asks the user
- **Encryption at rest** — data resides in Snowflake (encrypted by default) or in-memory
- **Network perimeter security** — SiS / SPCS networking managed by Snowflake
- **LLM safety / content filtering** — handled by Cortex backend
- **Multi-tenant app authorization** — app developer's responsibility to implement RBAC

---

## 7. Open Items

| ID | Description | Owner | Target |
|----|-------------|-------|--------|
| SEC-01 | Persist approval audit log (who approved what, when) | Laurent Letourmy | ✅ `0.3.0` (`AuditLog`, `ask_coco(audit=)`: pluggable sink, off by default, a failing write never stops the session, every decision, the outcome of an allowed call, secrets redacted); shipping the file to storage the app cannot rewrite is the host's |
| SEC-02 | Document least-privilege role recommendation for connected Snowflake account | Laurent Letourmy | ✅ `0.3.0` (section 8) |
| SEC-03 | Commit `uv.lock` for reproducible builds (currently gitignored) | Laurent Letourmy | v0.1.1 |
| SEC-04 | Add SBOM generation to CI release workflow | Laurent Letourmy | ✅ `0.1.5` (CycloneDX on tag release) |

---

## 8. Least-privilege role (SEC-02)

The agent works with the rights of the role it connects with: Cortex Code through the profile's role,
the managed agent through the role of `options_from_connection(profile, role=...)` (or the
application, in a Native App). A prompt-injected agent can do what that role can do, so give it the
least that works. Never `ACCOUNTADMIN` or `SYSADMIN` for a chat.

What was checked live (a Snowflake test account, 2026-10-26):

- **`PUBLIC` alone was enough** to run the managed agent (the Cortex access reaches it through `PUBLIC`
  on that account): connect, answer, run a command in the sandbox, load a stage skill.
- A scratch role with `USAGE` on one database and `CREATE SCHEMA` on it, nothing else, put the skills
  of the shop and an upload on a stage it created, and the agent read them.

A role for a chat that reads one schema and nothing more (the shape; adapt the names; not every
line was run, the account may differ):

```sql
CREATE ROLE COCO_CHAT;
GRANT USAGE ON DATABASE SALES TO ROLE COCO_CHAT;
GRANT USAGE ON SCHEMA SALES.MART TO ROLE COCO_CHAT;
GRANT SELECT ON ALL TABLES IN SCHEMA SALES.MART TO ROLE COCO_CHAT;      -- reads only
GRANT USAGE ON WAREHOUSE COCO_WH TO ROLE COCO_CHAT;                      -- a small one
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE COCO_CHAT;            -- if PUBLIC does not carry it
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_AGENT_USER TO ROLE COCO_CHAT;      -- the Agent API
-- uploads from the window (ManagedOptions(upload_stage=...)): write on that one stage only
GRANT READ, WRITE ON STAGE SALES.TMP.COCO_UPLOADS TO ROLE COCO_CHAT;
```

Rules of thumb: no `CREATE`/`DROP`/`OWNERSHIP` for a read-only chat; one warehouse with a resource
monitor; a stage of its own for uploads and skills (readable by the role, not by everyone); for a
Native App, only the grants `scripts/grant_privileges.sql` lists. Pair the role with the policy:
`FolderPolicy(sql=True)` shows each statement, and a standing permission for statements says nobody
reads each call, so offer none to a role that can change data.
