# FAQ

## How do I install streamlit-coco?

`pip install streamlit-coco[sdk]`. Full steps, prerequisites and
verification are in Enablement [`setup.html`](../../enablement/setup.html).

## Is it production-ready?

No — the version this guide describes is alpha (see the [index](../index.html)
for which version that is).

## Does it need a Snowflake connection?

For any CoCo-backed feature, yes — the agent runs through the Cortex Code
CLI/SDK against a configured Snowflake connection. Some example-app screens
work without one: BI → Semantic's estate-map and KPI-inventory screens parse
workbooks deterministically, and the deterministic Streamlit consumer it
generates needs no warehouse to view.

## What LLM does it use?

Whichever model Cortex Code runs under the hood. No model configuration is
required beyond `CocoOptions.model` (leave it `None`, or set it to `"auto"`).

## Can I customize which tools need approval?

Yes — `CocoOptions.allowed_tools` and `CocoOptions.require_approval_for`.
`AskUserQuestion` and `ExitPlanMode` always require approval regardless of
either setting. See
[I want to configure tool approvals](task-configure-tool-approvals.html).

## What happens if I deny an approval?

The tool call does not execute. The agent's turn continues from there,
optionally with the reason passed to `deny_pending()`.

## Is there a persisted log of approval decisions?

No — approval decisions, including "Always allow", are held in the session
only and are not written to a persisted audit log.

## How is this different from using the CoCo CLI directly?

The library adds the Streamlit-specific plumbing the CLI does not provide on
its own: rerun-safe session state, streamed rendering, tool cards, and the
approval UI.

## Does file upload work?

Yes — `upload_to_cwd()` / `cwd_uploader()` / `chat_input_bar(accept_file=...)`
write into the agent's `cwd`. See
[I want to add file uploads](task-add-file-uploads.html).

## What is `copilot_rail()`?

A right-rail Copilot built around `panel()`, for embedding CoCo inside a
larger multipage app instead of as a full-page chat. See the Backlog Desk
and BI → Semantic entries in [Example apps reference](reference-examples.html).

## Does it work with Streamlit in Snowflake (SiS) or SPCS?

Not today. Local — Streamlit, the CoCo CLI and the Snowflake config on the
same machine — is the only deployment target this version ships.

## How do I see the raw tool request/response payloads?

Set `STREAMLIT_COCO_DEBUG=1` or `COCO_DEBUG=1` (or `st.session_state["coco_debug"] = True`).
If the payloads still don't show, see
[`help.html#debug-mode-not-showing-payloads`](../../technical-guide/help.html#debug-mode-not-showing-payloads).

## Session says "Starting CoCo…" and never connects — what do I check?

See
[`help.html#session-stuck-connecting`](../../technical-guide/help.html#session-stuck-connecting)
and, if the connection itself is the problem,
[`help.html#coco-connection-error`](../../technical-guide/help.html#coco-connection-error) /
[`help.html#snowflake-config-not-found`](../../technical-guide/help.html#snowflake-config-not-found).

## `make audit` fails right after I bump the version in `pyproject.toml` — is that real?

Usually not — see
[`help.html#pip-audit-editable-false-positive`](../../technical-guide/help.html#pip-audit-editable-false-positive).

## App Builder's Studio page seems to overwrite my brief edits on Save & regenerate

See
[`help.html#app-builder-brief-overwrite-race`](../../technical-guide/help.html#app-builder-brief-overwrite-race).

## Where do I find the current list of known gaps for this asset?

`dsp-assets/audits/streamlit-coco/` holds the latest gap report; this guide
does not restate its contents since they change between releases.
