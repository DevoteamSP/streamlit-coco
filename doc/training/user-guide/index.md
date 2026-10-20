# User Guide — streamlit-coco

This guide describes streamlit-coco 0.1.9.

It documents the product as built: how to use it, what each part of its
public API does, and what each screen or command produces. It is not a
tutorial — for a guided first run, see Enablement
[`guided-tour.html`](../enablement/guided-tour.html) and
[`hands-on.html`](../enablement/hands-on.html).

## Who this is for

Anyone who writes Python against `streamlit-coco`: embedding a Copilot panel
or rail in a Streamlit app, running or adapting one of the example apps, or
calling the headless API from a script. It assumes working Python and basic
Streamlit knowledge; it does not assume prior exposure to the Cortex Code
Agent SDK.

## Reading paths

**Building an app.** Read [Concepts](sections/concepts.html), then
[Getting started](sections/getting-started.html), then
[I want to build a minimal CoCo app](sections/task-build-a-minimal-app.html).
Keep [API reference](sections/reference-api.html) open while you code.

**Evaluating the product.** Read [Concepts](sections/concepts.html), then
[I want to run the example apps](sections/task-run-the-example-apps.html) and
[Example apps reference](sections/reference-examples.html). Check
[FAQ](sections/faq.html) for the questions evaluators ask most.

**Extending or integrating deeper.** Read
[API reference](sections/reference-api.html) and
[Command reference](sections/reference-commands.html) end to end, then the
task pages for [tool approvals](sections/task-configure-tool-approvals.html),
[file uploads](sections/task-add-file-uploads.html),
[structured output](sections/task-use-structured-output.html) and
[headless use](sections/task-run-headless.html). The Technical Guide
`architecture.html` and `extending.html` cover what sits behind this API.

## Contents

### Start
- [Concepts](sections/concepts.html)
- [Getting started](sections/getting-started.html)

### Tasks
- [I want to build a minimal CoCo app](sections/task-build-a-minimal-app.html)
- [I want to run the example apps](sections/task-run-the-example-apps.html)
- [I want to configure tool approvals](sections/task-configure-tool-approvals.html)
- [I want to add file uploads](sections/task-add-file-uploads.html)
- [I want to use structured output](sections/task-use-structured-output.html)
- [I want to run CoCo headless](sections/task-run-headless.html)

### Reference
- [API reference](sections/reference-api.html)
- [Command reference](sections/reference-commands.html)
- [Example apps reference](sections/reference-examples.html)
- [Outputs](sections/outputs.html)

### Answers
- [FAQ](sections/faq.html)

## Not covered

- **Skills module** — there is no `.cortex/skills/*/SKILL.md` orchestration
  layer at the repo root. The App Builder example's own `types/<id>/SKILL.md`
  files are in-example CoCo guideline skills, documented under
  [Example apps reference](sections/reference-examples.html) → App Builder,
  not as a separate reference-skills chapter.
- **Snowflake objects** — this library does not create or own any Snowflake
  DDL. SQL execution happens only through the agent's own SQL tool, gated by
  approval, using whatever the connected role can already do.
- **Native App** — the repo has no `manifest.yml` or `snowflake.yml`. Native
  App packaging is not shipped.
- **Deployment modes beyond local** — only one target ships today: local
  (Streamlit, the CoCo CLI and the Snowflake config on the same machine).
  Streamlit in Snowflake and SPCS are discussed only as threat-model scope in
  the Technical Guide; they are not implemented.
- **Controls catalogue** — there is no rule-file or scoring-rubric layer in
  this repo.
- **Infrastructure as code** — there is no Terraform in this repo.
- **Example-app screens, page by page** — the three example apps each have
  their own screens, but this guide covers each app as one reference entry
  in [Example apps reference](sections/reference-examples.html) rather than
  one entry per Streamlit page. Each example ships its own README with a
  page-level walkthrough; duplicating that here would drift from it.
