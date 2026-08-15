# W01 — Setup, Architecture & First App

**Duration**: 3h
**Phase**: Build → Enable
**Series**: A (Platform)

---

## Purpose

Get the client team from zero to a working `streamlit-coco` integration: environment set
up and verified, the core architecture (session ownership, approval gates, tool cards)
understood, and at least one client-side developer able to build and demo a minimal app
independently. This workshop is what evidences the Snow Builders N0→N1 gate item "1
additional consultant trained" for client engagements, and de-risks the Build phase by
surfacing environment/access issues early.

---

## Participants

| Role | Devoteam | Client |
|------|----------|--------|
| Facilitator | Asset owner / trained consultant | — |
| Tech lead | Supporting engineer (optional) | Client Streamlit/Python developer |
| Decision maker | — | Engineering lead / product owner |
| Power user | — | Analyst or developer who will maintain the app post-handover |

---

## Pre-requisites

What must be ready **before** this session:

- [ ] Snowflake account with Cortex Code access provisioned for the client environment
- [ ] Client developer has Python 3.10+ and `uv` installed
- [ ] `~/.snowflake/connections.toml` (or equivalent) configured for the target account
- [ ] CoCo CLI (`cortex`) installable/reachable on the client's machine or shared dev box
- [ ] Assess-phase use-case brief shared (from `delivery_plan.md` Phase 1) so the hands-on
      exercise can target a realistic scenario
- [ ] Repo access to `streamlit-coco-dev` (or the client's fork/integration repo) granted

---

## Agenda

| Time | Block | Facilitator |
|------|-------|-------------|
| 0:00 | Context & goals (10 min) — why streamlit-coco, what "done" looks like today | Devoteam |
| 0:10 | Setup verification (20 min) — run through [`setup-guide.md`](../../training/setup-guide.md) checklist live; troubleshoot any environment issues on the spot | Devoteam + Client |
| 0:30 | Architecture walkthrough (30 min) — session ownership model, `panel()`/`chat_input_bar()`/`copilot_rail()`/`query()`, approval gates, tool cards; live in `examples/chat_app.py` | Devoteam |
| 1:00 | Demo / live walkthrough (25 min) — run the [demo script](../../training/demo-script.md) Steps 1–3 (first impression, approval gates, structured output) | Devoteam |
| 1:25 | Break (10 min) | — |
| 1:35 | Hands-on exercise (60 min) — client developer completes Hands-On Lab [Exercise 5](../../training/hands-on-lab.md#exercise-5--build-a-minimal-app-from-scratch): build a minimal app from the README alone, targeting the client's actual use case instead of the generic sample | Client (guided by Devoteam) |
| 2:35 | Q&A and approval-policy decisions (15 min) — finalize which tools are auto-run vs. approval-gated for the target app | Devoteam + Client |
| 2:50 | Next steps & homework (10 min) — assign quiz, agree on Build-phase milestones | Devoteam |

---

## Expected Outcomes

By the end of this session, participants will:

1. Understand the `streamlit-coco` architecture: session ownership, streaming render,
   approval gates, and the difference between interactive/structured/headless modes.
2. Have a working local environment verified against the [setup guide](../../training/setup-guide.md) checklist.
3. Have built (with guidance) a minimal working app targeting the client's real use case.
4. Have agreed on an initial `allowed_tools` / `require_approval_for` policy for the Build phase.

**Deliverable**: a running skeleton app in the client's repo/environment, plus a recorded
approval-policy decision to carry into the Build phase.

---

## Facilitator Notes

- **Common confusion point**: mixing up `allowed_tools` and `require_approval_for` — some
  attendees expect tools not listed in either to auto-run; clarify that unlisted tools
  default to requiring approval (safety-first design).
- **Common confusion point**: expecting Streamlit Community Cloud or SiS support — CoCo
  needs a subprocess + CLI on the same host as Streamlit; clarify this limitation early if
  the client's target deployment is cloud-hosted (see `doc/deployment/local.md` §8).
- **If the group is ahead of schedule**: show `make bi-semantic` (`copilot_rail()` in a
  product wizard) or extend the hands-on to structured output (Hands-On Lab Exercise 3).
- **If behind**: skip the headless-mode portion of the demo walkthrough (Step 4) — it's
  optional and not required for the core Build-phase outcome.
- **Key question to ask**: "Which of your existing destructive workflows (writes, table
  creation, deletes) absolutely must have a human in the loop before this goes live?" —
  this drives the approval-policy decision directly.
