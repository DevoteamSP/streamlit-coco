# Limits

Known limitations, stated as facts.

## Alpha status

`pyproject.toml` classifies the package as `Development Status :: 3 -
Alpha`. The public API surface (`CocoOptions`, `panel()`, `copilot_rail()`,
`app_viewer()`, and the rest of `streamlit_coco.__init__`) may still change
between minor versions; check `CHANGELOG.md` when upgrading.

## Streamlit in Snowflake, Community Cloud, and SPCS are not supported

The CoCo CLI is spawned as a local subprocess by the SDK. That needs a host
that can run subprocesses and reach a Snowflake connection config on disk.
Streamlit Community Cloud does not offer that. Streamlit in Snowflake (SiS)
and SPCS are considered in the threat model as deployment contexts, but no
install path, no code path, and no configuration surface for either exists
in this repo today — see [install](install.html) and
[architecture](architecture.html).

## No persisted approval audit log

The transcript, including which tool calls were approved, denied, or
"always allowed," lives only in Streamlit session state. Nothing records
who approved what, when, once the browser session ends. This is open item
**SEC-01** (see [security](security.html)); no target date has shipped.

## No dedicated least-privilege role recommendation document

[security](security.html) gives interim least-privilege guidance for the
connected Snowflake role (do not use `ACCOUNTADMIN`), but that guidance is
not a separate deliverable — there is no standalone document that
enumerates a recommended grant set for a streamlit-coco deployment. This is
open item **SEC-02**.

## One `app_viewer()` preview process per `app_dir`

`app_viewer()` tracks a single child `streamlit run` process per `app_dir`
via `.preview.pid` / `.preview.port` inside that directory. Pointing two
`app_viewer()` calls at the same `app_dir` at once is not supported, and
`app_dir` must never be pointed at the host app itself.

## The child preview app is a different origin — Fix-with-CoCo cannot read its DOM

The previewed Streamlit app runs on its own port (`127.0.0.1:8511`–`:8520`)
and is embedded in an iframe. The parent page cannot read the traceback
rendered in that iframe's DOM (cross-origin). **Fix with CoCo** works by
scraping `.preview.log` for `Uncaught app exception` /
`Traceback (most recent call last):` markers, not by inspecting what the
browser rendered. A later timestamped log line is treated as "error
cleared," which can miss a fix that did not actually resolve the traceback,
or clear an expander for an unrelated reason; **Fix with CoCo** still sends
the log tail even when the parse misses (see
[help.html#preview-log-parse-miss](../help.html#preview-log-parse-miss)).

## CodeQL is not running in CI

`.github/workflows/security.yml` does not include a CodeQL job — a private
GitHub organization needs a GHAS license to upload CodeQL results, which
this org does not have. Only Gitleaks (secrets) and `pip-audit`
(dependencies) run today. See [security](security.html) and
[testing-and-ci](testing-and-ci.html).
