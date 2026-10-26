# Deploy the Skills shop with CoCo: a prompt that asks, then builds

For someone who has not deployed this Native App before. Open Cortex Code (CoCo) in a clone of this repository, at its root, and paste everything under **The prompt**. CoCo asks for the parameters, checks your account, then builds the image, installs the application and shows you its address. It asks before every step that creates something, costs credits or grants a right.

What you end up with (development install, in your own account): the application package `coco_skills_shop_pkg`, the application `coco_skills_shop` with its XS compute pool and its Streamlit service, one image in an image repository you name, and a stage of skills inside the application. Manual version of the same steps: [`DEPLOY.md`](DEPLOY.md).

You need: Docker running, the Snowflake CLI (`snow`), a profile in `~/.snowflake/connections.toml`, and an account where Snowpark Container Services and the Cortex Agent API are available. The author ran it as `ACCOUNTADMIN`; other roles are untested.

---

## The prompt

````text
You are helping me deploy the "Skills shop" Snowflake Native App of this repository to my own Snowflake
account. Work from the repository root. The files that matter are all in examples/skills_hub_native/
(read DEPLOY.md, snowflake.yml, snowflake.local.yml.example, manifest.yml, containers/service_spec.yaml,
containers/build_and_push.sh, scripts/setup_script.sql and scripts/grant_privileges.sql first) and in
the Makefile targets native-shop-*. Do not change anything under streamlit_coco/ or examples/skills_hub/.

HOW YOU WORK
- Ask me for the parameters below with your question tool, at most three questions at a time, and show
  the default you propose. Do not guess an answer and do not move on until I answered.
- Before every step that creates, changes or deletes something in Snowflake, builds or pushes an image,
  or grants a right: show me the exact command or SQL, say in one sentence what it does and what it
  costs, and wait for my "yes". Read-only checks need no question.
- Never print a password, token, private key or the contents of connections.toml. Never run
  `snow app teardown`, DROP, or anything on an object that is not named in this prompt. Do not touch
  other applications of the account.
- If a step fails, read the message, say what it means in plain words, propose one fix and ask before
  you try it. Do not retry in a loop.

PARAMETERS TO ASK (in this order)
1. Connection: run `snow connection list` and offer the profiles (never show secrets). Which one?
   Then run `snow connection test -c <profile>` and tell me the account, user and current role.
2. Role: the role used to build and install (default: the profile's role). The author used ACCOUNTADMIN;
   say plainly that another role needs the privileges to create an application package and an
   application, and access to the image repository, and that it is untested.
3. Warehouse: an existing warehouse for `snow app run` (list them with SHOW WAREHOUSES; propose a small one).
4. Image repository: database, schema and repository name (default: a database I own, schema PUBLIC,
   repository COCO_IMAGES). Check whether it exists (SHOW IMAGE REPOSITORIES IN SCHEMA ...). If not, offer
   to create it (CREATE IMAGE REPOSITORY ...).
5. Names: keep the defaults coco_skills_shop (application), coco_skills_shop_pkg (package) and
   COCO_SKILLS_SHOP_COMPUTE_POOL. Strongly recommend keeping them: the Makefile targets and the SQL of
   scripts/grant_privileges.sql use these names. If I want others, list every file you would have to
   change and ask again.
6. Start-up check: run the in-service probe once (one model call: it proves the Agent API answers from
   inside the service) — yes or no? Default yes for a first install.

BEFORE ANYTHING IS CREATED (read-only)
- `snow --version`, and `docker info` (Docker must be running: if not, tell me to start it, do not
  start it yourself).
- With my profile and role: SELECT CURRENT_ACCOUNT(), CURRENT_ROLE(); SHOW COMPUTE POOLS (this proves
  Snowpark Container Services is available); SHOW APPLICATIONS LIKE 'COCO_SKILLS_SHOP';
  SHOW APPLICATION PACKAGES LIKE 'COCO_SKILLS_SHOP_PKG'; SHOW COMPUTE POOLS LIKE 'COCO_SKILLS_SHOP%'.
  If any of them already exists, stop and ask me: reuse (upgrade), or choose other names. Never replace
  it silently.
- Say whether Cortex looks available to the role (SHOW GRANTS TO ROLE or a SNOWFLAKE.CORTEX database
  role in the account). If you cannot tell, say so: the probe at the end will.
- Summarise what will be created and what will cost credits (a CPU_X64_XS compute pool that stays active
  while the service runs, and model calls when I chat), then ask for my "yes" to go on.

THE STEPS (each one after my "yes")
1. Configure, in files that are gitignored or that I approve:
   - Copy examples/skills_hub_native/snowflake.local.yml.example to snowflake.local.yml (gitignored) and
     set role and warehouse for both entities. Show me the file.
   - In examples/skills_hub_native/manifest.yml and containers/service_spec.yaml replace
     /my_db/my_schema/my_repo/ by /<database>/<schema>/<repository>/ (lower case) — show me the diff.
     Do not commit these two edits.
   - If I chose a probe: set SKILLS_HUB_PROBE to "1" in containers/service_spec.yaml (show the diff).
2. Image repository: CREATE IMAGE REPOSITORY if it does not exist (show the SQL first).
3. Image: `make native-shop-image SNOW_CONNECTION=<profile>`. It logs in to the registry, builds linux/amd64
   and pushes <registry host>/<db>/<schema>/<repo>/coco-skills-shop:dev. Tell me it takes a few minutes.
   Check the image is there: SHOW IMAGES IN IMAGE REPOSITORY <db>.<schema>.<repo>.
4. Package and application: `make native-shop-deploy SNOW_CONNECTION=<profile>` (it is `snow app run`:
   it uploads the files, creates the package and the application, which creates the compute pool and
   the service). If it says the image is not accessible to the package, show me the grants of the
   Snowflake Native App container tutorial (USAGE on the database and the schema, READ on the image
   repository, to the application package) and ask before you run them. (Not needed in the author's own
   install, as ACCOUNTADMIN.)
5. Grants for Cortex — the one place I want a full stop. Show me examples/skills_hub_native/scripts/
   grant_privileges.sql line by line. Explain: it gives the APPLICATION, and nothing else, the database
   roles SNOWFLAKE.CORTEX_USER and SNOWFLAKE.CORTEX_AGENT_USER, so the agent running as the application
   may call Cortex; it needs ACCOUNTADMIN; the grants are lost if the application is torn down. Run it
   only after I answer yes to this exact question.
6. Restart so the service starts with the grants: `make native-shop-restart`, then wait and poll
   `make native-shop-status` (at most ~5 minutes, every 20 seconds) until the service is READY. If it is
   not, read `make native-shop-logs` and tell me what it says.
7. The address: `SHOW ENDPOINTS IN SERVICE coco_skills_shop.services.shop_service` and give me
   `https://<ingress_url>`. Say that I open it in my browser and log in with my Snowflake user; you cannot.
8. If I chose the probe: read `make native-shop-logs` and report whether it ends with `probe: OK`; if not,
   what failed. Then set SKILLS_HUB_PROBE back to "0" in containers/service_spec.yaml and ask whether to
   run `make native-shop-deploy` and `make native-shop-restart` again so the service stops making a
   model call at every start.

AT THE END, report in this order
- Done / not done, one line per step.
- What now exists in my account (application, package, compute pool, service, stage
  coco_skills_shop.data.skills_stage with the bundled skills, the image, the grants) and the address.
- What runs up costs and how to stop it: `snow sql -q "CALL coco_skills_shop.app_schema.suspend_service()"
  --connection <profile>` (the pool suspends five minutes later); `make native-shop-restart` starts it again.
- How to remove everything: `make native-shop-teardown` (do not run it), and that the image stays in the
  repository.
- What I did not check: that the page works for my user behind the ingress, that chat answers as my
  role (it runs as the application, with the application's rights), and how long the session lasts.
- The files you changed in the repository (git status), and a reminder that snowflake.local.yml is
  gitignored while the two image-path edits are not meant to be committed.
````

---

## Notes for whoever maintains this prompt

- It follows [`DEPLOY.md`](DEPLOY.md) and the `native-shop-*` targets of the Makefile; change them together.
- The default names are kept on purpose: `coco_skills_shop` is written in the Makefile, in `scripts/grant_privileges.sql` and in the procedures of `scripts/setup_script.sql`.
- The container-tutorial grants in step 4 were **not needed** in the author's run (`ACCOUNTADMIN`, the repository in the same account); they are offered for a role that is not the owner of the repository, and are untested here.
- Nothing in the prompt runs a grant, a creation or a push without an explicit yes. That is the contract to keep when editing it.
