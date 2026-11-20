# Skills shop: deploy the Native App (development, same account)

Everything below runs in your own account, with the role of your profile (`ACCOUNTADMIN` in the author's). It creates: the application package `coco_skills_shop_pkg`, the application `coco_skills_shop` (with its compute pool `COCO_SKILLS_SHOP_COMPUTE_POOL`, an XS pool that suspends after 5 minutes, and its service) and one image `coco-skills-shop:dev` in an image repository you own.

Needs Docker running, the Snowflake CLI (`snow`) and a profile in `~/.snowflake/connections.toml`.

First time? [`COCO_PROMPT.md`](COCO_PROMPT.md) is a prompt for Cortex Code (CoCo) that asks you for the parameters, checks your account and runs the steps below, asking before each one that creates, costs or grants.

First name your image repository: `manifest.yml` and `containers/service_spec.yaml` say `/my_db/my_schema/my_repo/coco-skills-shop:dev`. Create the repository (`CREATE IMAGE REPOSITORY my_db.my_schema.my_repo`) and put its lower-case path in both files (the build script reads it from the spec):

```bash
sed -i.bak 's#/my_db/my_schema/my_repo/#/<db>/<schema>/<repo>/#' examples/skills_hub_native/manifest.yml examples/skills_hub_native/containers/service_spec.yaml
```

```bash
# 1. image (from the repository root)
examples/skills_hub_native/containers/build_and_push.sh snowflake   # the argument is the connection (profile)

# 2. package and application (snow app run)
(cd examples/skills_hub_native && snow app run --connection snowflake)

# 3. what the application needs for Cortex (read examples/skills_hub_native/scripts/grant_privileges.sql first)
snow sql -f examples/skills_hub_native/scripts/grant_privileges.sql --connection snowflake

# 4. restart the service so it starts with the grants, then look at it
snow sql -q "CALL coco_skills_shop.app_schema.suspend_service()" --connection snowflake
snow sql -q "CALL coco_skills_shop.app_schema.resume_service()" --connection snowflake
snow sql -q "CALL coco_skills_shop.app_schema.get_service_status()" --connection snowflake
snow sql -q "CALL coco_skills_shop.app_schema.get_service_logs('0', 'streamlit')" --connection snowflake
snow sql -q "SHOW ENDPOINTS IN SERVICE coco_skills_shop.services.shop_service" --connection snowflake   # ingress_url
```

Open `https://<ingress_url>` (you log in with your Snowflake user). The service publishes the bundled skills to `coco_skills_shop.data.skills_stage` when it starts (a schema that is not versioned, so the skills survive an upgrade; a version already on the stage is never replaced).

## Check the Agent API from inside the service

The page needs a login, so the service can also check itself: set `SKILLS_HUB_PROBE: "1"` in `containers/service_spec.yaml`, run the deploy and the restart of the steps above, then read the logs (`get_service_logs`). The probe lists the skills, verifies one, runs one agent turn with it (every request that asks is declined) and prints `probe: OK` or what failed. Set it back to `"0"`: each start makes one model call.

## What it costs while it runs

The service keeps `COCO_SKILLS_SHOP_COMPUTE_POOL` (CPU_X64_XS) active. Stop it when you do not use the app: `snow sql -q "CALL coco_skills_shop.app_schema.suspend_service()"` (the pool then suspends after 5 minutes), and `resume_service()` (the restart of step 4) to start it again.

## Teardown

```bash
(cd examples/skills_hub_native && snow app teardown --connection snowflake --force --cascade)   # the application, its service and pool, the package
```

The image stays in the repository; drop it with `DROP IMAGE ...` or leave it.
