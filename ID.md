# Asset Identity Sheet

| Field | Value |
|-------|-------|
| **Name** | `streamlit-coco` |
| **Display name** | streamlit-coco |
| **Snow Builders level** | N0 (working toward N1) |
| **Status** | active |
| **Asset Owner** |  Laurent Letourmy |
| **Contributors** | DevoteamSP / streamlit-coco contributors |
| **Created** | 2026-07 |
| **Last updated** | 2026-08-13 |
| **Confidentiality** | Public |

---

## Domain & Technology

**Domain**: ai_ml / streamlit / analytics

**Snowflake features**: cortex (CoCo / Cortex Code Agent SDK), Streamlit

**Other tech**: Python, uv, hatchling, pytest, ruff

**Industry**: cross_industry

---

## Maturity Justification

**Current level**: N0 → closing alpha toward N1

- Clients where used: 0 (alpha)
- Consultants trained: —
- Demo available: yes (`make chat`, `make backlog`, `make tableau-semantic`, `doc/training/`)
- Snowflake Alliance pre-alignment: —

**Next milestone**: N1 — conditions needed:

- [x] Feature golden-path checklists under `doc/features/`
- [x] CI + PR template
- [x] Consultant enablement pack (`doc/training/`) + workshop W01 (`0.1.6`)
- [ ] Fill owner / KPIs on this sheet
- [ ] Run and sign off UI checklists on a live CoCo + Snowflake connection
- [ ] Security threat model + audit pack (`doc/security/`)
- [x] Marketing one-pager (`doc/marketing/one-pager.md`) — refreshed for `0.1.6`

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
- Threat model: started (`doc/security/threat-model.md`)
- Last security scan: GitHub Actions Security workflow (Gitleaks CLI, CodeQL, pip-audit)
