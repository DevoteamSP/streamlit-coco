# Release notes bank — 0.3.0

Freeform. Feed LinkedIn / Medium / GitHub Release when this cut is published.

## Headline (one line)

> Ask CoCo runs in Snowflake's sandbox now: no CLI to install, and every Allow is on the record.

## Top 3 user-visible wins

1. **The managed agent in the same window** — `ask_coco(agent=managed_agent(options_from_connection("my_profile", role="PUBLIC")))`. Same Allow and Decline, same standing permissions; the request says the command runs in the Snowflake sandbox. The run is always created with `always_ask` and only a one-call "Allow this command" is ever sent.
2. **An audit log** — `ask_coco(audit=AuditLog("coco-audit.jsonl", who=...))`: who allowed which exact command, when. Works with the CLI agent too.
3. **Attach a file, the sandbox reads it** — a file attached before the first message goes to a stage mounted in the sandbox; no copy stays on the app's disk.

## Use cases to feature

1. A Skills shop: skills (a `SKILL.md` folder) kept on a stage, a chat with one chosen skill on the managed agent (`make skills-hub`)
2. The same shop as a Snowflake Native App on SPCS (`examples/skills_hub_native`): the agent runs as the application

## Learnings (candid)

- The server decides what it asks about. `echo hello` ran without a request; a write asked. The app's gate sees only what the server shows it, so the least-privilege role matters more than for the CLI agent.
- Snowflake's own "Allow all bash for this session" is a standing grant we never choose: the standing permission is the user's, through the gate.
- A first draft handed the managed agent our Cortex Code prompt, and it answered with the developer's local folder. It has its own prompt now.
- A regular stage mounts as a snapshot read when the first message is sent. A file put after that is invisible, so a late attachment is refused with a sentence, not accepted and lost.
- The package never saw the person who answers. `AuditLog(who=...)` takes it from the host.
- A Native App's versioned schema is recreated on every upgrade, which wiped the stage that held the skills: state lives in a schema that is not versioned.

## Quotes / soundbites

- “No CLI to install. The same window, the same Allow.”
- “The sandbox decides what is risky. You decide what runs.”

## Explicit non-goals this cut

- `CocoOptions.mode="api"`: the managed agent is a separate backend, not a mode.
- Mapping the app's working folder into the sandbox: nothing local is visible to it.
- Streamlit in Snowflake (`0.3.5`) and a versioned, published Native App (`0.4.0`).
