# Delivery Plan — streamlit-coco

Engagement pattern for delivering `streamlit-coco` on a client project. Written for a
Python/Streamlit-savvy client team building an internal AI-assisted app on Snowflake.
Typical duration: **1–2 weeks** for a focused pilot (Assess → Build), extending to
**3–4 weeks** if Migrate/Enable phases (replacing an existing chatbot, or training a
broader team) are in scope.

## Phase breakdown

### 1. Assess (0.5–1 day)

Scope the target app, confirm prerequisites, decide which interaction mode(s) fit
(interactive panel, structured output, headless, or a mix).

| Activity | Owner | Duration | Deliverable |
| --- | --- | --- | --- |
| Confirm Snowflake account has Cortex Code access | Client | — | Access confirmed |
| Identify target app + use case (dashboard copilot, pipeline step, internal tool) | Devoteam + Client | 2h | One-pager use-case brief |
| Decide interaction mode(s): panel / structured-output / headless | Devoteam | 1h | Mode decision recorded in brief |
| Confirm which tools need approval gates for this use case | Devoteam + Client | 1h | Approval policy draft |

### 2. Build (2–5 days)

Stand up the integration against the client's actual Snowflake account and app shell.

| Activity | Owner | Duration | Deliverable |
| --- | --- | --- | --- |
| Install + configure `streamlit-coco` in client repo/environment | Devoteam | 0.5d | Working local install |
| Build minimal app skeleton (`panel()` + `chat_input_bar()` or headless `query()`) | Devoteam | 1d | Skeleton app running against client data |
| Configure `allowed_tools` / `require_approval_for` per approval policy | Devoteam | 0.5d | Approval gates verified |
| Wire structured output into client's existing widgets (if applicable) | Devoteam | 1d | Widget(s) driven by agent output |
| Client review checkpoint | Devoteam + Client | 1h | Sign-off to proceed or adjust |

### 3. Migrate (1–5 days, optional — only if replacing an existing solution)

Move logic/prompts from a prior chatbot or manual workflow into the new integration.

| Activity | Owner | Duration | Deliverable |
| --- | --- | --- | --- |
| Inventory existing prompts / workflows to port | Client | 1d | Migration backlog |
| Port + adapt prompts/workflows | Devoteam | 2–3d | Ported workflows working end-to-end |
| Parallel-run old vs. new for validation | Devoteam + Client | 1d | Validation sign-off |

### 4. Enable (1–2 days)

Hand over to the client team; train at least one client-side consultant/developer.

| Activity | Owner | Duration | Deliverable |
| --- | --- | --- | --- |
| Run W01 workshop (setup, architecture, hands-on) | Devoteam | 0.5d | Workshop sign-off, ≥1 client dev trained |
| Deliver 10–12 min demo to stakeholders | Devoteam | 0.5h | Demo delivered, Q&A logged |
| Handover docs (README, deployment guide, troubleshooting) | Devoteam | 0.5d | Docs reviewed by client |
| Go-live support window (async, 1 week) | Devoteam | — | Issues triaged within 1 business day |

## Workshop map

| Workshop | Phase | Purpose |
| --- | --- | --- |
| W01 | Build → Enable | Setup, architecture walkthrough, hands-on build of a first app, approval-gate design |

Additional workshops (W02+) are not yet needed at this asset's maturity — add them if a
client engagement surfaces a repeatable need (e.g. a dedicated "headless/CI integration"
workshop, or a "structured output for BI dashboards" workshop).

## Dependencies

- **Assess → Build**: Snowflake Cortex Code access must be confirmed before Build starts — this is the most common blocker.
- **Build → Migrate**: skeleton app must be signed off before porting existing logic.
- **Migrate → Enable**: parallel-run validation must pass before handover/training.

## Suggested calendar (2-week pilot, Assess + Build + Enable, no Migrate)

| Week | Days | Focus |
| --- | --- | --- |
| 1 | Mon–Tue | Assess |
| 1 | Wed–Fri | Build (skeleton + approvals) |
| 2 | Mon–Tue | Build (structured output / polish) |
| 2 | Wed | W01 workshop + demo |
| 2 | Thu–Fri | Handover docs + go-live support window starts |
