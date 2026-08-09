# Contributing to streamlit-coco

Thanks for looking. This project is built and maintained by the Devoteam Snowflake
Partner practice, and we use it on real client work.

## How this repository works

Development happens in an internal repository. **This repo is the published source** —
it is what ships to [PyPI](https://pypi.org/project/streamlit-coco/), and it is where
issues and pull requests are handled.

That means one thing worth knowing before you spend time: when we merge your pull
request, we replay it into the internal tree so it ships in the next release. We keep
your commit authorship when we do. When a port makes that impossible, we credit you by
name in [`CHANGELOG.md`](CHANGELOG.md). You will always be named.

If that model is a dealbreaker for you, tell us in an issue — we would rather know.

## Our commitment

**We reply to every issue and pull request within 5 business days.** Not always with a
merge — sometimes with a question, or with "no, and here is why." But you will not be
left waiting in silence.

## What we are looking for

Genuinely useful, roughly in order:

- **Bug reports with a reproduction.** A minimal script beats a long description.
- **New examples.** `examples/` is the fastest way in. Our roadmap lists use cases we
  have not built yet — an app builder, a FinOps cost explorer, a query-incident triage
  console, multi-persona workspaces. Pick one, build it small, open a PR.
- **Deployment recipes.** Docker, SPCS, Streamlit in Snowflake. If you got it running
  somewhere we have not documented, that is worth more than it sounds.
- **Documentation fixes.** Including "this paragraph is wrong" — especially that.
- **Issues labelled [`good first issue`](../../issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22).**

Please open an issue before starting anything large or architectural. We may already be
building it internally, and we would rather say so before you write the code.

## Getting set up

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/DevoteamSP/streamlit-coco
cd streamlit-coco
make install          # uv sync with dev dependencies
make check            # ruff + unit/smoke (excludes browser e2e)
make e2e-install      # optional: Playwright + Chromium
make e2e              # browser UX against the CoCo-free harness
```

See [`doc/testing.md`](doc/testing.md) for the full gate (unit → e2e → audit → manual checklists).

Running live demos needs the CoCo CLI on your `PATH` and a Snowflake connection
configured in `~/.snowflake/connections.toml`. See the [README](README.md) for details.

```bash
uv run streamlit run examples/chat_app.py
```

## Pull requests

- Branch from `main`, one concern per PR.
- `make check` passes (`make e2e` when touching transcript / upload UX). New behaviour comes with a test.
- Add a line to the `[Unreleased]` section of [`CHANGELOG.md`](CHANGELOG.md).
- Explain *why* in the PR description. The diff already says what.

Small and finished beats large and nearly there.

## Reporting a security issue

Do not open a public issue. Email <laurent.letourmy@devoteam.com> with the details and
we will come back to you within 5 business days.

This library runs an agent that can read files, write files, and execute SQL. Approval
gates exist for a reason — if you have found a way around one, we want to hear it first.

## Licence

Apache-2.0. By contributing, you agree that your contributions are licensed under the
same terms.

## One more thing

We are hiring people who build. If you enjoyed working on this, that is a stronger
signal to us than any CV — open a PR, then email <laurent.letourmy@devoteam.com> and
say so.