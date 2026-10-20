# Technical Guide

This guide describes streamlit-coco 0.1.9.

streamlit-coco is a Python/Streamlit library that embeds Snowflake's Cortex
Code Agent SDK ("CoCo") into a Streamlit app: a right-rail or full-panel
Copilot, human-in-the-loop approval gates for destructive tools, a live
preview of an app CoCo just wrote, structured output into your own widgets,
and a headless `query()` / `CocoSession` API for scripts and CI. Package
status is alpha (`Development Status :: 3 - Alpha`).

This guide is for the people who run, maintain, and extend streamlit-coco
itself — not for someone building a Streamlit app on top of it (that reader
wants the [User Guide](../user-guide/index.html)).

## Who this is for

| Audience | Reads for | Start at |
|---|---|---|
| Operate | Install the library and the CoCo CLI on a host, configure a Snowflake connection, run the example apps, diagnose a broken session | [install](sections/install.html) → [configuration](sections/configuration.html) → [operations](sections/operations.html) → [help](help.html) |
| Maintain | Keep the repo releasable: tests, CI gates, security posture, cutting a release | [testing-and-ci](sections/testing-and-ci.html) → [security](sections/security.html) → [upgrade-and-release](sections/upgrade-and-release.html) |
| Extend | Add a text renderer, a tool-card family, an App Builder type, or a new example app | [architecture](sections/architecture.html) → [extending](sections/extending.html) → [data-and-contracts](sections/data-and-contracts.html) |

Every audience should read [architecture](sections/architecture.html) first;
it is the shared map the other chapters assume.

## Contents

**Understand**
- [architecture](sections/architecture.html) — components, repo map, data flow, invariants
- [data-and-contracts](sections/data-and-contracts.html) — `CocoEvent`, JSON Schema contracts, output artifacts, versioning
- [limits](sections/limits.html) — known limitations, stated plainly

**Run**
- [install](sections/install.html) — prerequisites and ordered install steps, local target only
- [configuration](sections/configuration.html) — every `CocoOptions` field, env var, and config file
- [operations](sections/operations.html) — run, schedule, monitor, cost/latency, cleanup
- [security](sections/security.html) — roles and grants, secrets, threat model, CI security posture

**Build**
- [testing-and-ci](sections/testing-and-ci.html) — test tree, gates, what CI checks
- [extending](sections/extending.html) — text renderer, tool-family dispatch, App Builder types, new example apps
- [upgrade-and-release](sections/upgrade-and-release.html) — versioning, the publish process, uninstall

**Answers**
- [help](help.html) — symptom-indexed troubleshooting

## Not covered

- **Skills module** — no `.cortex/skills/*/SKILL.md` at the repo root. App Builder's own `types/*/SKILL.md` files are in-example CoCo guideline skills, documented under [extending](sections/extending.html) instead of a `reference-skills`-style chapter.
- **Snowflake objects** — the library creates or owns no Snowflake DDL. All SQL execution happens through the agent's own SQL tool, approval-gated, using whatever the connected role can do; there is no `reference-procedures` chapter.
- **Native App** — no `manifest.yml` / `snowflake.yml` in this repo. Not shipped.
- **Deployment modes** — only one target ships today: local (Streamlit, the CoCo CLI, and the Snowflake config on the same host). Streamlit in Snowflake (SiS) and SPCS are threat-model and roadmap scope only; they are not implemented, so [install](sections/install.html) has one target, not a `modes` chapter.
- **Controls catalogue** — no rule files or scoring rubric in this repo.
- **Infrastructure as code** — no `*.tf` files in this repo.
