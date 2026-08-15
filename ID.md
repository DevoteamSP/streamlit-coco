# Asset Identity Sheet

| Field | Value |
|-------|-------|
| **Name** | `streamlit-coco` |
| **Display name** | streamlit-coco |
| **Snow Builders level** | N0 (working toward N1) |
| **Status** | active |
| **Asset Owner** | Laurent Letourmy — laurent.letourmy@devoteam.com |
| **Contributors** | DevoteamSP / streamlit-coco contributors |
| **Created** | 2026-07 |
| **Last updated** | 2026-08-15 |
| **Confidentiality** | Public |

---

## Domain & Technology

**Domain**: ai_ml / streamlit / analytics

**Snowflake features**: cortex (CoCo / Cortex Code Agent SDK), Streamlit

**Other tech**: Python, uv, hatchling, pytest, ruff

**Industry**: cross_industry

---

## Maturity Justification

**Current level**: N0 → closing alpha toward N1 (PyPI `0.1.7`)

- Clients where used: 0 (alpha). Internal: Data Product Studio.
- Consultants trained: 0 additional. Enablement pack + workshop W01 shipped in `0.1.6`; registry `consultants_enabled: 1` is the asset owner.
- Demo available: yes (`make chat`, `make backlog`, `make bi-semantic`, [`doc/training/`](doc/training/training-overview.md))
- Snowflake Alliance pre-alignment: no

**Next milestone**: N1 — conditions needed:

- [x] Feature golden-path checklists under `doc/features/`
- [x] CI + PR template
- [x] Consultant enablement pack (`doc/training/`) + workshop W01 (`0.1.6`)
- [x] Owner + KPIs on this sheet
- [x] Security threat model + audit pack (`doc/security/`) — SEC-01 / SEC-02 still open for v0.2
- [x] Marketing one-pager (`doc/marketing/one-pager.md`) — refreshed for `0.1.7`
- [ ] 1 additional consultant trained via W01 (pack exists; count still 0 beyond owner)
- [ ] Remaining live UI checklists — core panel / approvals / tools / structured / CCv2 signed off; copilot-rail still pending
- [ ] 2+ client usages

Last audit: **22.5/26** (2026-08-12). This refresh closes the stale-`ID.md` P1 from that report.

---

## KPIs

| KPI | Value |
|-----|-------|
| Estimated time gain | not measured (one-pager: ~5 min to first working app vs hand-rolled CoCo plumbing) |
| Total reuse count | 0 client missions |
| Revenue influenced | not tracked |
| Consultants enabled | 1 (asset owner) |
| Last audit score | 22.5/26 (2026-08-12) |
| PyPI downloads | 319 last month (snapshot 2026-08-14) |
| GitHub stars | 2 ([DevoteamSP/streamlit-coco](https://github.com/DevoteamSP/streamlit-coco)) |

Public adoption targets (90 days post-launch): 500+ PyPI downloads / month, 50+ GitHub stars, ≥ 3 community examples. See [`doc/roadmap.md`](doc/roadmap.md).

---

## Repository

| Role | URL |
| --- | --- |
| **Public / PyPI source** | [github.com/lletourmy/streamlit-coco](https://github.com/lletourmy/streamlit-coco) *(temporary until DevoteamSP is PyPI-validated)* |
| **Development** | [github.com/DevoteamSP/streamlit-coco-dev](https://github.com/DevoteamSP/streamlit-coco-dev) |

Publish procedure: [`doc/deployment/publish.md`](doc/deployment/publish.md)

---

## Security

- IP review done: no
- Threat model: yes — [`doc/security/threat-model.md`](doc/security/threat-model.md) (open: SEC-01 approval audit log, SEC-02 least-privilege role docs)
- Findings: [`doc/security/findings-report.md`](doc/security/findings-report.md) (2026-07-28; 0 pip-audit / Gitleaks findings)
- Last security scan: GitHub Actions [`security.yml`](.github/workflows/security.yml) on every PR / push to `main` + weekly Monday — Gitleaks CLI + pip-audit. CodeQL omitted (private org needs GHAS).
