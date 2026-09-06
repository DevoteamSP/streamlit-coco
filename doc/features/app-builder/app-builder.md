# App Builder

Guided Streamlit app generation for **business users**, with CoCo **guidelines skills** —
and a form that already knows the answer before it asks.

**Status:** Shipped in **`0.1.8`**. Example: `examples/app_builder` (`make app-builder`).
**Surfaces:** `examples/app_builder` composing `copilot_rail()` + `app_viewer()`; per-type
skills under `types/` (rules + a reference app + a self-check checklist; shared pack in `types/shared/`).
**Users / use cases / flows:** [`UX.md`](UX.md).
**Design rationale / build order:** [`../../../doc-dev/briefs/app-builder-v2.md`](../../../doc-dev/briefs/app-builder-v2.md) (dev-only).
**Related RFC:** [Napkin to App #9](https://github.com/DevoteamSP/streamlit-coco/issues/9) (photo start is **out of scope**).

---

## What

A sample app where a non-developer picks an app type, drops the data it
needs, and reviews **what CoCo found** before anything is written — instead
of typing column names and metric lists into a blank form. CoCo scaffolds the
app under approval gates, following packaged **guidelines skills** (layout,
theming, Snowflake patterns, a reference app to imitate) instead of
unconstrained generation. Preview and **Fix with CoCo** reuse the `0.1.6` /
`0.1.7` primitives; a self-check now runs once automatically before the
human ever sees a red Preview.

Some types need no Snowflake account at all: a folder of documents to
compare, a handful of URLs to watch for changes. Those exist specifically so
a room with no warehouse open can still see the product work.

This is the third first-party community example after Backlog Desk (`0.1.0`)
and BI → Semantic (`0.1.6` / `0.1.7`).

## Why

- Copilot rail + App Viewer already let a *developer* generate and preview an
  app (BI → Semantic). Business users still start from a blank file or a
  specialist.
- A blank form asking someone to type what's already in their file is the
  same mistake a bad onboarding wizard makes — and it produces exactly the
  generic, uninspiring output you'd expect from generic, uninspiring input.
- Unconstrained generation ignores Streamlit / Snowflake conventions
  (widgets, semantic views, HITL). Skills encode that — and a reference app
  teaches craft that prose rules cannot.
- Every type needing a Snowflake account narrows the audience to people who
  already have one open. Document- and URL-grounded types widen it to anyone
  with a laptop.
- Completes the ≥ 3 community-examples success check on the
  [roadmap](../../roadmap.md).

## How (intent)

Five pages in the menu: **Welcome · Library · Brief · Studio · Admin**.
Studio opens **Open Preview** \| **Open Copilot**. Admin is catalog CRUD.

The product is a **catalog of app types**. A Library card is **icon + name +
users + grounding kind + screenshot** (if any). Opening a type shows its
**brief**: context, what it enables, what it does not, and a place to drop
data. The brief's form is **pre-filled by a profile step** — deterministic
(pandas) for tabular data and named semantic views, agent-run only where no
parser could propose an answer (a pile of dissimilar documents, a set of
URLs). Answers plus **user sketches** (schema / wireframe they upload)
complete it. Type `screenshot` is only the Library card — sketches are not
on the type.

| Area | Intent |
| --- | --- |
| **UX** | See [`UX.md`](UX.md). Not a library `app_builder()`. |
| **Types** | Versioned YAML/JSON in the example; adding a type ≠ a new host app. Each declares a `grounding_kind` (`tabular` / `semantic_view` / `documents` / `urls`) that decides whether profiling is a parser or a CoCo job. |
| **Profiling** | Parser-first: "if a parser can answer it, a model should not be asked" (same rule as BI → Semantic). The form shows *findings*, editable, not blanks. Only the two questions no data can answer — who uses this, what must never happen — are always typed by a person. |
| **Skills** | Shared rules + per-type guidelines, restructured as **rules + a reference app the agent Reads + a checklist it verifies itself against.** No invented objects. |
| **HITL** | Write summary from brief answers; diff optional. No **Always allow** on first Write. AskUser never "Always allow". A self-check pass runs automatically after Write, before Preview reaches the human — it does not skip approval, it skips the human having to notice the app crashed. |
| **Grounding kinds without Snowflake** | Documents and URLs are fetched/extracted by the **host**, never by the CoCo session — no network tool is granted for this feature. CoCo only ever Reads local snapshots under `sources/`. |
| **Preview** | `app_viewer()` on `out/<slug>/` — never the host app. |
| **Rollout** | `examples/app_builder` + `make app-builder`. **Locked** live set for `0.1.8`: KPI presentation, Data quality, Call transcription, Meeting recap, Prompt library, CSV explorer. Document comparison and every `urls` type are later — see [`UX.md`](UX.md) §5.3. |

## Limitations / out of scope (this slice)

- Napkin / whiteboard photo as the **only** start ([#9](https://github.com/DevoteamSP/streamlit-coco/issues/9)); user sketches on a type brief are in scope
- API mode / SiS / Native App hosting of the child process (`0.2.0`+)
- Pixel-perfect clones of Tableau / Power BI (that is BI → Semantic)
- Live network access from inside a CoCo session (host fetches; agent Reads local files only)
- **Replacing the confirm-the-profile step with a full agent-run interview** — deliberately deferred, not rejected. It becomes the right shape once `documents`/`urls` types are live and users want to correct a proposed schema by talking instead of through the form. See [`UX.md`](UX.md) §11 for what has to be true first.
- `ships_copilot` (a generated app carrying its own Copilot rail) — designed in [`UX.md`](UX.md) §5.5, scoped to one type once the base catalogue is solid, not part of this slice's critical path

## Open questions (implementation)

Product questions in [`UX.md`](UX.md) §8 are **proposed locked**. Still open,
tracked in [`UX.md`](UX.md) §10:

- `0.1.8` live type set — locked in [`UX.md`](UX.md) §5.3
- `engine/profile.py` output schema
- PDF extraction library; URL fetch policy — later, with `doc-compare` / `urls`
- Skill pack migration to the three-file layout (`SKILL.md` + `reference/` + `CHECKLIST.md`)
- New public GitHub issue (do not file until confirmed)

## Related

- Users / flows / rationale for every design decision above: [`UX.md`](UX.md)
- Design brief this doc was rewritten from: [`../../../doc-dev/briefs/app-builder-v2.md`](../../../doc-dev/briefs/app-builder-v2.md)
- Checklist: [`test-checklist.md`](test-checklist.md)
- Roadmap: [`../../roadmap.md`](../../roadmap.md) (`0.1.8`)
- Primitives: [`../copilot-rail/`](../copilot-rail/) · [`../app-viewer/`](../app-viewer/)
