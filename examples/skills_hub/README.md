# Skills shop

Example for [streamlit-coco](https://github.com/DevoteamSP/streamlit-coco) (experimental): a **shop of skills** kept on a Snowflake stage, and a chat with **one chosen skill** on Snowflake's managed coding agent. Only developers publish; the app reads.

A skill is a folder with a `SKILL.md` (front matter, then instructions) and optional `references/`, `assets/` and `scripts/`. The managed agent loads it from the stage (`ManagedOptions(stage_skills=...)`), in its own sandbox, with the rights of the role you log in with.

## Run

```bash
make install
make skills-hub
```

- **Sample skills (no Snowflake)**: the shop shows three samples from `samples/` and the chat is the scripted agent. Also what `STREAMLIT_COCO_AGENT=mock` gives.
- **Stage in Snowflake**: pick a profile of `~/.snowflake`, a role and the stage (`DATABASE.SCHEMA.STAGE`), then **Connect**. The role must be able to read the stage and use Cortex Agents; give it the least rights that work (not `ACCOUNTADMIN`).

## Publish a skill (developers)

```bash
make publish-skill SKILL=examples/skills_hub/samples/csv-profile \
  ARGS="--stage DB.SCHEMA.SKILL_STAGE --profile snowflake --role MY_PUBLISHER_ROLE"
make publish-skill SKILL=examples/skills_hub/samples/csv-profile ARGS="--dry-run"
```

The command validates the folder first (safe names, a short list of file types, size limits, no links, no obvious credentials; `scripts/` are listed as a warning), then uploads it to `skills/<id>/<version>/` and updates `skills/index.json`. A published version never changes: publishing it again is refused. Give the shop's users **read** on the stage and keep **write** for the publishers' role.

Layout on the stage:

```
skills/index.json
skills/<skill_id>/<version>/SKILL.md
skills/<skill_id>/<version>/references|assets|scripts/...
```

## What to know

- **One skill per chat.** A skill added to an existing thread was not picked up in the spike, so choosing another skill starts a new conversation.
- **Before a chat**, the app checks the folder on the stage against what was published: the same list of files (the agent mounts the whole folder, so a file added by hand is caught) and the same content hash. A changed version is not offered.
- **Scripts ask first.** A skill's `scripts/` run in the sandbox only after you Allow the command in the window. Snowflake asks only about calls it rates risky, so the review of a skill's folder at publish time is the control that matters.
- The agent is not told anything about this computer (no working folder, no local rights): see `streamlit_coco.managed.build_prompt`.
- The same app runs as a Native App: `examples/skills_hub_native/` (`DEPLOY.md`). There it reads the application's own stage and the agent runs as the application.
- Brief and decisions (dev-only): `doc-dev/briefs/skills-hub-managed.md`.

## Code

| Path | What |
| --- | --- |
| `app.py` | the Streamlit pages: library, detail, chat |
| `shop/skill.py` | the model, `validate_folder` (the publish gate), hashing |
| `shop/stores.py` | `LocalFolderStore`, `StageStore`, `CachedStore`; publish |
| `shop/service.py` | `Shop`: search, versions, `verify`, `chat_options` |
| `shop/cli.py`, `publish.py` | `make publish-skill` |
| `shop/native.py`, `shop/bootstrap.py`, `shop/probe.py` | inside the Native App: the service's connection and stage, publishing the bundled skills at start, a one-turn probe |
| `samples/` | three sample skills (one carries a script) |

Tests: `tests/test_skills_hub.py` (a fake stage over a temporary folder, no Snowflake).
