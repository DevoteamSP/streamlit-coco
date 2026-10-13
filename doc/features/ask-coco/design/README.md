# Ask CoCo design canvas

The design reference delivered with Ask CoCo: 86 numbered frames and two views of the window in the Spec-First Cockpit.
The host page illustrates an integration; the reusable window is implemented in `streamlit_coco/static/coco/`.

## Open the boards

Open [`index.html`](index.html) in a browser, then select a board. GitHub displays the HTML source; download or clone
this repository to view the rendered boards. No Streamlit server or Snowflake connection is needed.

| Board | Content |
| --- | --- |
| [CoCo22](canvas/project/CoCo22.dc.html) | Frames 1?37: launcher and window states |
| [CoCo22Waiting](canvas/project/CoCo22Waiting.dc.html) | Frames 38?61: questions, plans and standing permission |
| [CoCo22Data](canvas/project/CoCo22Data.dc.html) | Frames 62?86: data, files, page requests, display and session |
| [CoCo22OnPage](canvas/project/CoCo22OnPage.dc.html) | Window on a 1440 ? 900 host page |
| [CoCo22OnPage1366](canvas/project/CoCo22OnPage1366.dc.html) | Window on a 1366 ? 768 host page |

## Provenance

Copied on 2026-10-13 from `ui-rebuild/coco-board/canvas/project/`, the canvas supplied for this delivery.
All nine source files are preserved byte for byte in [`canvas/project/`](canvas/project/), including
[`canvas.json`](canvas/project/canvas.json), its board positions, titles and order, and the three CSS files.
The manifest's `v: 3` is retained as supplied. The consultation index and this README are additions.

The original boards reference `support.js`, an editor resource absent from the supplied canvas.
Their markup and CSS display as static HTML without it; a browser may report that missing script.
The `text/x-dc` scripts are editor metadata, not application code. Host-page links target Cockpit mockups
outside this canvas, and controls are design examples. Montserrat loads from Google Fonts;
offline viewing uses the CSS system-font fallback.

## Delivery

This folder is public feature documentation: it is included in the repository and source distribution (sdist).
The Python wheel contains the runtime package and its own assets; it does not embed these design boards.
No runtime asset is replaced by the canvas CSS.

Behaviour and migration: [Ask CoCo](../ask-coco.md). Verification: [test checklist](../test-checklist.md).
