# Release kits (public)

Each cut gets `doc/releases/X.Y.Z/` for **ship hygiene** (docs, QA, screenshots).

**Community posts and articles** live under **`doc-dev/releases/X.Y.Z/`** (never synced to public `streamlit-coco`).

## Create kits for the next version

```bash
VER=0.1.6   # bump
mkdir -p "doc/releases/${VER}/screenshots" "doc-dev/releases/${VER}"
cp -R doc/releases/_template/. "doc/releases/${VER}/"
cp -R doc-dev/releases/_template/. "doc-dev/releases/${VER}/"
```

## What lives where

| Public (`doc/releases/X.Y.Z/`) | Dev-only (`doc-dev/releases/X.Y.Z/`) | Canonical sources |
| --- | --- | --- |
| Pre-tag checklist + sign-off | LinkedIn + Medium drafts | `CHANGELOG.md`, `doc/roadmap.md`, `doc/prd.md` |
| Screenshot brief + assets | Community / visibility checklist | Published URLs pasted into checklist |
| `NOTES.md` (themes / learnings) | | Ongoing series: `doc-dev/marketing/` |

**Do not tag** until the public checklist (docs + QA) is complete.

Ship mechanics: [`../deployment/publish.md`](../deployment/publish.md) · QA: [`../testing.md`](../testing.md) · Outreach: [`../../doc-dev/releases/`](../../doc-dev/releases/README.md).
