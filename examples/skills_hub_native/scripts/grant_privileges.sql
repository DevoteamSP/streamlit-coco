-- Grants the application needs so that the managed coding agent can run as it.
-- Run as ACCOUNTADMIN after the first `snow app run` (they are lost on teardown). They give the
-- application, and nothing else, access to Cortex; read them before you run them.
--
-- Replace coco_skills_shop if you installed the application under another name.

GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO APPLICATION coco_skills_shop;
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_AGENT_USER TO APPLICATION coco_skills_shop;
