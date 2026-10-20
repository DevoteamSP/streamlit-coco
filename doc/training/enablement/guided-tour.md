# Guided tour

A 20–30 minute walkthrough of the running product. This is not a demo script
(that is [`demo-guide.md`](demo-guide.html)) and it is not exercises (that is
[`hands-on.md`](hands-on.html)) — just what you will see when you run each
command, and what to pay attention to.

Complete the [setup checklist](setup.html) first.

## Part 1 — `make chat`, the preferred pattern (~15 min)

```bash
make chat
```

This runs `examples/chat_app.py`. It is the reference implementation of the
library's preferred pattern: **you own the page, CoCo owns the session.**

**What appears first:** a title ("CoCo for Streamlit"), an environment status
gate ("Start CoCo Chat"), and a sidebar. Before you click Start, the gate
shows the SDK / CLI / Snowflake probe results — this is `check_environment()`
rendered by `render_start_gate()`. Notice it never starts an agent process on
its own; it only starts once you click the button.

**Click Start CoCo Chat.** The main panel is empty at first, with a status
line. In the sidebar, open the **Settings** popover (`:material/tune:`
icon). Notice:

- An **Output mode** segmented control (`transcript` / `field`) — this maps
  directly to `panel(output_mode=...)`.
- A **CoCo debug mode** toggle — flips `STREAMLIT_COCO_DEBUG`-equivalent
  behavior via `st.session_state["coco_debug"]`, showing raw tool payloads
  once enabled.
- A **Plan mode** toggle — sets `permission_mode="plan"` so `ExitPlanMode`
  approvals can be exercised.
- **Auto-allowed** and **Requires approval** tool pills — these feed
  `CocoOptions.allowed_tools` and `require_approval_for` live, and a
  **Reset session** button restarts the worker when you change them (tool
  permissions are part of the session's options hash).

**Type a prompt** — for example *"What tables are available in
SNOWFLAKE_SAMPLE_DATA.TPCH_SF1?"*. Watch the transcript render
progressively, not all at once: this is the `@st.fragment` poll loop
(`run_every=0.25`) pulling from the background `CocoSession` worker, so the
rest of the page does not rerun while CoCo is thinking. A tool card appears
(likely Glob or SQL) — this is the readable card the library builds instead
of a raw JSON dump.

**Ask for something that writes** — for example *"Create a summary table
called TOP_CUSTOMERS in my schema."* An approval banner appears with
**Approve once**, **Always allow**, **Deny** (in that order). This is
`render_approvals()`, wired automatically inside `panel()` because
`show_approvals=True` is the default. This is the human-in-the-loop gate:
`Edit`, `Write`, and `Bash` are in `require_approval_for` by default in this
example.

**Sidebar test prompts:** toggle **Test prompts** to browse
`examples/testdata/prompts.json` by category and send one without typing —
useful later for repeatable demos.

## Part 2 — `make backlog`, a rail beside a real app (~5 min)

```bash
make backlog
```

This runs the Product Backlog Desk (`examples/backlog_desk/`), a multipage,
file-backed (no SQL) app: **Board**, **Epic**, **Ticket**, **Release** pages.
Notice Copilot is **not** a navigation page — it is a right-hand rail opened
from the header **Copilot** button, or from an action link such as "Check
DoD" on a ticket. Close it with **Close**; the Board/Epic/Ticket/Release
pages work without connecting Copilot at all. This is the shape
`copilot_rail()` is built for: the app owns the page, CoCo sits in a column
next to it, not instead of it.

## Part 3 — `make bi-semantic`, the rail in full (~8 min)

```bash
make bi-semantic
```

This runs BI → Semantic (`examples/bi_to_semantic/`), the fullest use of
`copilot_rail()`. On screen 1 (**Load**), load the bundled **MIT Tableau
Server pack** — no warehouse needed. Move to screen 4 or 6 and open Copilot
on the right.

Notice, on the rail's title row: **Copilot**, a **Connection** popover, and
an icon-only **Display config** popover (`:material/display_settings:`,
hover shows "Display config") beside it. Open Display config — it has two
sliders: **Last messages** (default 8, range 1–50) and **First n characters**
(default 200, range 40–1000), each with an on/off pill. Moving a slider
reruns the rail fragment only; the popover stays open and the transcript
updates live. This replaced an earlier pills-only look — as of this version,
transcript compactness is controlled entirely from this popover.

While CoCo is busy, watch the title row: a compact **Working · thinking…**
badge sits there — not a tall status card — and a **Cancel job** button
appears next to **Close**. After Connect, on an empty transcript, you may see
**example question** buttons; clicking one either sends it immediately or, if
marked deferred, copies it into the chat input for you to edit first.

## What to notice across all three

- The agent always runs server-side; the browser only renders Streamlit
  widgets — nothing about the agent process is exposed to the client.
- Approval gates are the same primitive everywhere (`render_approvals()`
  inside `panel()`), whether the app is a full-page chat or a rail.
- `panel()` is the common core; `copilot_rail()` is `panel()` plus
  connection chrome, job queuing, and transcript-compactness controls, built
  for embedding beside an existing app rather than replacing it.

Next: [`hands-on.md`](hands-on.html) to build and break things yourself.
