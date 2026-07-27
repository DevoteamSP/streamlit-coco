# Asset Identity Sheet

| Field | Value |
|-------|-------|
| **Name** | `streamlit-coco` |
| **Display name** | streamlit-coco |
| **Snow Builders level** | N0 (working toward N1) |
| **Status** | active |
| **Asset Owner** | TBD — update before N1 gate |
| **Contributors** | DevoteamSP / streamlit-coco contributors |
| **Created** | 2026-07 |
| **Last updated** | 2026-07 |
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
- Demo available: yes (`make chat`, examples/)
- Snowflake Alliance pre-alignment: —

**Next milestone**: N1 — conditions needed:

- [x] Feature golden-path checklists under `docs/features/`
- [x] CI + PR template
- [ ] Fill owner / KPIs on this sheet
- [ ] Run and sign off UI checklists on a live CoCo + Snowflake connection
- [ ] Security threat model + audit pack (`docs/security/`)
- [ ] Marketing one-pager (`docs/marketing/`)

---

## Repository

| Role | URL |
| --- | --- |
| **Public / PyPI source** | [github.com/DevoteamSP/streamlit-coco](https://github.com/DevoteamSP/streamlit-coco) |
| **Development** | [github.com/DevoteamSP/streamlit-coco-dev](https://github.com/DevoteamSP/streamlit-coco-dev) |

Publish procedure: [`docs/deployment/publish.md`](docs/deployment/publish.md)

---

## Security

- IP review done: no
- Threat model: not yet (`docs/security/` TBD)
- Last security scan: GitHub Actions Security workflow (Gitleaks CLI, CodeQL, pip-audit)
