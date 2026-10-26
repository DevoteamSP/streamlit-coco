-- Skills shop: setup script. Compute pool, the Streamlit service, the application's skills stage and
-- the lifecycle procedures. Skills are published to data.skills_stage by the service itself
-- (shop.bootstrap) when it starts.

CREATE APPLICATION ROLE IF NOT EXISTS app_public;

CREATE OR ALTER VERSIONED SCHEMA app_schema;
GRANT USAGE ON SCHEMA app_schema TO APPLICATION ROLE app_public;

-- Services cannot live in a versioned schema.
CREATE SCHEMA IF NOT EXISTS services;
GRANT USAGE ON SCHEMA services TO APPLICATION ROLE app_public;

-- The skills of the shop: skills/index.json and skills/<id>/<version>/... (owned by the application,
-- written by its service, read by the managed coding agent that runs as the application). In a
-- schema that is not versioned: objects of a versioned schema are recreated at every upgrade, which
-- would empty the stage each time.
CREATE SCHEMA IF NOT EXISTS data;
GRANT USAGE ON SCHEMA data TO APPLICATION ROLE app_public;
CREATE STAGE IF NOT EXISTS data.skills_stage;
GRANT READ ON STAGE data.skills_stage TO APPLICATION ROLE app_public;

LET pool_name := (SELECT CURRENT_DATABASE()) || '_compute_pool';

CREATE COMPUTE POOL IF NOT EXISTS IDENTIFIER(:pool_name)
  MIN_NODES = 1
  MAX_NODES = 1
  INSTANCE_FAMILY = CPU_X64_XS
  AUTO_RESUME = TRUE
  AUTO_SUSPEND_SECS = 300;

CREATE SERVICE IF NOT EXISTS services.shop_service
  IN COMPUTE POOL IDENTIFIER(:pool_name)
  FROM SPECIFICATION_FILE = '/containers/service_spec.yaml'
  MIN_INSTANCES = 1
  MAX_INSTANCES = 1;

GRANT SERVICE ROLE services.shop_service!streamlit_role TO APPLICATION ROLE app_public;

CREATE OR REPLACE PROCEDURE app_schema.version_init()
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
  ALTER SERVICE IF EXISTS services.shop_service FROM SPECIFICATION_FILE = '/containers/service_spec.yaml';
  CALL SYSTEM$WAIT_FOR_SERVICES(600, 'services.shop_service');
  RETURN 'Upgrade complete';
END;
$$;
GRANT USAGE ON PROCEDURE app_schema.version_init() TO APPLICATION ROLE app_public;

CREATE OR REPLACE PROCEDURE app_schema.suspend_service()
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
  ALTER SERVICE services.shop_service SUSPEND;
  RETURN 'Service suspended';
END;
$$;

CREATE OR REPLACE PROCEDURE app_schema.resume_service()
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
  ALTER SERVICE services.shop_service RESUME;
  RETURN 'Service resumed';
END;
$$;

CREATE OR REPLACE PROCEDURE app_schema.get_service_status()
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
  LET status STRING := (SELECT SYSTEM$GET_SERVICE_STATUS('services.shop_service'));
  RETURN :status;
END;
$$;

CREATE OR REPLACE PROCEDURE app_schema.get_service_logs(instance_id VARCHAR, container_name VARCHAR)
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
  LET logs STRING := (SELECT SYSTEM$GET_SERVICE_LOGS('services.shop_service', :instance_id, :container_name));
  RETURN :logs;
END;
$$;

GRANT USAGE ON PROCEDURE app_schema.suspend_service() TO APPLICATION ROLE app_public;
GRANT USAGE ON PROCEDURE app_schema.resume_service() TO APPLICATION ROLE app_public;
GRANT USAGE ON PROCEDURE app_schema.get_service_status() TO APPLICATION ROLE app_public;
GRANT USAGE ON PROCEDURE app_schema.get_service_logs(VARCHAR, VARCHAR) TO APPLICATION ROLE app_public;
