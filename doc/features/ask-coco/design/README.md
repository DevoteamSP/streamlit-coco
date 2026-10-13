# Ask CoCo design canvas

The design reference delivered with Ask CoCo: 86 numbered frames and two views of the window in the Spec-First Cockpit.
The host page illustrates an integration; the reusable window is implemented in `streamlit_coco/static/coco/`.

## Open the boards

Open [`index.html`](index.html) in a browser, then select a board. GitHub displays the HTML source; download or clone
this repository to view the rendered boards. No Streamlit server or Snowflake connection is needed.

| Board | Content |
| --- | --- |
| [CoCo22](preview/CoCo22.dc.html) | Frames 1-37: launcher and window states |
| [CoCo22Waiting](preview/CoCo22Waiting.dc.html) | Frames 38-61: questions, plans and standing permission |
| [CoCo22Data](preview/CoCo22Data.dc.html) | Frames 62-86: data, files, page requests, display and session |
| [CoCo22OnPage](preview/CoCo22OnPage.dc.html) | Window on a 1440 x 900 host page |
| [CoCo22OnPage1366](preview/CoCo22OnPage1366.dc.html) | Window on a 1366 x 768 host page |

## Provenance

Copied on 2026-10-13 from `ui-rebuild/coco-board/canvas/project/`, the canvas supplied for this delivery.
All nine source files are preserved byte for byte in [`canvas/project/`](canvas/project/), including
[`canvas.json`](canvas/project/canvas.json), its board positions, titles and order, and the three CSS files.
The manifest's `v: 3` is retained as supplied. The consultation index, this README and the finished consultation pages are additions.

The original boards reference `support.js`, an editor resource absent from the supplied canvas.
The consultation pages in `preview/` omit that reference and the `text/x-dc` editor metadata,
load the original CSS, and disable links to Cockpit mockups outside this canvas. Controls remain
static design examples. The finished pages are committed with the documentation; opening them requires no build step.

The original sources remain unchanged in `canvas/project/`. Montserrat loads from Google Fonts;
offline viewing uses the CSS system-font fallback.

## Delivery

This folder is public feature documentation: it is included in the repository and source distribution (sdist).
The Python wheel contains the runtime package and its own assets; it does not embed these design boards.
No runtime asset is replaced by the canvas CSS.

Behaviour and migration: [Ask CoCo](../ask-coco.md). Verification: [test checklist](../test-checklist.md).
