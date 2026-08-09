# Streamlit CoCo — One-Pager

> Embed Snowflake's AI coding agent directly into your Streamlit apps — with streaming UI, human-in-the-loop approval gates, and headless pipelines.

---

## The Problem

Teams building Streamlit apps on Snowflake need AI-assisted data exploration, code generation, and automated workflows. Today, integrating Snowflake's Cortex Code agent into a custom app requires building session management, streaming rendering, tool-card display, and safety gates from scratch — weeks of work with no reusable foundation.

---

## The Solution

**streamlit-coco** is a Python library that wraps the Cortex Code Agent SDK into production-ready Streamlit components:

| Capability | What it does |
|-----------|--------------|
| `panel()` | Streaming agent transcript with tool cards (SQL, Read, Write, Grep) |
| Approval gates | Human-in-the-loop pause before destructive tools execute |
| `chat_input_bar()` | App-integrated chat input with session management |
| `query()` | Headless async API for scripts and CI — no UI needed |
| Structured output | Route agent responses into your own Streamlit widgets |

---

## Key Differentiators

- **5 minutes to first working app** — `pip install streamlit-coco[sdk]` + 10 lines of code
- **Safety by default** — Edit, Write, Bash, and SQL tools require explicit user approval
- **Dual mode** — interactive UI for analysts, headless API for pipelines
- **Pure Python** — no JavaScript build step, works with SiS and local Streamlit

---

## Who Is This For?

| Persona | Use case |
|---------|----------|
| Data engineers | Agentic pipelines with human oversight |
| Analytics teams | AI-powered data exploration dashboards |
| Platform teams | Internal tools with embedded code generation |
| Consultants | Rapid prototyping of AI-first Snowflake apps |

---

## Technical Requirements

- Python 3.10+
- Streamlit >= 1.53
- Snowflake account with Cortex Code access
- `cortex-code-agent-sdk >= 1.0.7`

---

## Getting Started

```bash
pip install streamlit-coco[sdk]
```

```python
import streamlit as st
import streamlit_coco as coco

session = coco.get_or_create_session()
coco.panel(session)
coco.chat_input_bar(session)
```

```bash
streamlit run app.py
```

---

## Maturity & Support

| | |
|---|---|
| **Level** | N0 (Alpha) — targeting N1 |
| **License** | Apache-2.0 |
| **Owner** | Laurent Letourmy — Devoteam Snowflake Partner |
| **Repo** | [github.com/DevoteamSP/streamlit-coco](https://github.com/DevoteamSP/streamlit-coco) |

---

*Devoteam Snow Builders — Accelerating AI-first Snowflake delivery*
