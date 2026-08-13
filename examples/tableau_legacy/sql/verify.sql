USE SCHEMA TABLEAU_LEGACY.PUBLIC;
SELECT '_users.system_user_id -> system_users.id' AS fk,
  COUNT(*) AS orphelins
FROM "_users" ch LEFT JOIN "system_users" pa ON ch."system_user_id" = pa."id"
WHERE ch."system_user_id" IS NOT NULL AND pa."id" IS NULL
UNION ALL
SELECT 'hist_datasources.datasource_id -> datasources.id' AS fk,
  COUNT(*) AS orphelins
FROM "hist_datasources" ch LEFT JOIN "datasources" pa ON ch."datasource_id" = pa."id"
WHERE ch."datasource_id" IS NOT NULL AND pa."id" IS NULL
UNION ALL
SELECT 'hist_flows.flow_id -> flows.id' AS fk,
  COUNT(*) AS orphelins
FROM "hist_flows" ch LEFT JOIN "flows" pa ON ch."flow_id" = pa."id"
WHERE ch."flow_id" IS NOT NULL AND pa."id" IS NULL
UNION ALL
SELECT 'hist_metrics.metric_id -> metrics.id' AS fk,
  COUNT(*) AS orphelins
FROM "hist_metrics" ch LEFT JOIN "metrics" pa ON ch."metric_id" = pa."id"
WHERE ch."metric_id" IS NOT NULL AND pa."id" IS NULL
UNION ALL
SELECT 'hist_sites.site_id -> sites.id' AS fk,
  COUNT(*) AS orphelins
FROM "hist_sites" ch LEFT JOIN "sites" pa ON ch."site_id" = pa."id"
WHERE ch."site_id" IS NOT NULL AND pa."id" IS NULL
UNION ALL
SELECT 'hist_tasks.task_id -> tasks.id' AS fk,
  COUNT(*) AS orphelins
FROM "hist_tasks" ch LEFT JOIN "tasks" pa ON ch."task_id" = pa."id"
WHERE ch."task_id" IS NOT NULL AND pa."id" IS NULL
UNION ALL
SELECT 'hist_users.site_role_id -> site_roles.id' AS fk,
  COUNT(*) AS orphelins
FROM "hist_users" ch LEFT JOIN "site_roles" pa ON ch."site_role_id" = pa."id"
WHERE ch."site_role_id" IS NOT NULL AND pa."id" IS NULL
UNION ALL
SELECT 'hist_views.view_id -> views.id' AS fk,
  COUNT(*) AS orphelins
FROM "hist_views" ch LEFT JOIN "views" pa ON ch."view_id" = pa."id"
WHERE ch."view_id" IS NOT NULL AND pa."id" IS NULL
UNION ALL
SELECT 'hist_workbooks.workbook_id -> workbooks.id' AS fk,
  COUNT(*) AS orphelins
FROM "hist_workbooks" ch LEFT JOIN "workbooks" pa ON ch."workbook_id" = pa."id"
WHERE ch."workbook_id" IS NOT NULL AND pa."id" IS NULL
UNION ALL
SELECT 'historical_events.hist_actor_user_id -> hist_users.id' AS fk,
  COUNT(*) AS orphelins
FROM "historical_events" ch LEFT JOIN "hist_users" pa ON ch."hist_actor_user_id" = pa."id"
WHERE ch."hist_actor_user_id" IS NOT NULL AND pa."id" IS NULL
UNION ALL
SELECT 'historical_events.hist_collection_id -> hist_collections.id' AS fk,
  COUNT(*) AS orphelins
FROM "historical_events" ch LEFT JOIN "hist_collections" pa ON ch."hist_collection_id" = pa."id"
WHERE ch."hist_collection_id" IS NOT NULL AND pa."id" IS NULL
UNION ALL
SELECT 'historical_events.hist_datasource_id -> hist_datasources.id' AS fk,
  COUNT(*) AS orphelins
FROM "historical_events" ch LEFT JOIN "hist_datasources" pa ON ch."hist_datasource_id" = pa."id"
WHERE ch."hist_datasource_id" IS NOT NULL AND pa."id" IS NULL
UNION ALL
SELECT 'historical_events.hist_flow_id -> hist_flows.id' AS fk,
  COUNT(*) AS orphelins
FROM "historical_events" ch LEFT JOIN "hist_flows" pa ON ch."hist_flow_id" = pa."id"
WHERE ch."hist_flow_id" IS NOT NULL AND pa."id" IS NULL
UNION ALL
SELECT 'historical_events.hist_metric_id -> hist_metrics.id' AS fk,
  COUNT(*) AS orphelins
FROM "historical_events" ch LEFT JOIN "hist_metrics" pa ON ch."hist_metric_id" = pa."id"
WHERE ch."hist_metric_id" IS NOT NULL AND pa."id" IS NULL
UNION ALL
SELECT 'historical_events.hist_project_id -> hist_projects.id' AS fk,
  COUNT(*) AS orphelins
FROM "historical_events" ch LEFT JOIN "hist_projects" pa ON ch."hist_project_id" = pa."id"
WHERE ch."hist_project_id" IS NOT NULL AND pa."id" IS NULL
UNION ALL
SELECT 'historical_events.hist_schedule_id -> hist_schedules.id' AS fk,
  COUNT(*) AS orphelins
FROM "historical_events" ch LEFT JOIN "hist_schedules" pa ON ch."hist_schedule_id" = pa."id"
WHERE ch."hist_schedule_id" IS NOT NULL AND pa."id" IS NULL
UNION ALL
SELECT 'historical_events.hist_target_site_id -> hist_sites.id' AS fk,
  COUNT(*) AS orphelins
FROM "historical_events" ch LEFT JOIN "hist_sites" pa ON ch."hist_target_site_id" = pa."id"
WHERE ch."hist_target_site_id" IS NOT NULL AND pa."id" IS NULL
UNION ALL
SELECT 'historical_events.hist_task_id -> hist_tasks.id' AS fk,
  COUNT(*) AS orphelins
FROM "historical_events" ch LEFT JOIN "hist_tasks" pa ON ch."hist_task_id" = pa."id"
WHERE ch."hist_task_id" IS NOT NULL AND pa."id" IS NULL
UNION ALL
SELECT 'historical_events.hist_view_id -> hist_views.id' AS fk,
  COUNT(*) AS orphelins
FROM "historical_events" ch LEFT JOIN "hist_views" pa ON ch."hist_view_id" = pa."id"
WHERE ch."hist_view_id" IS NOT NULL AND pa."id" IS NULL
UNION ALL
SELECT 'historical_events.hist_workbook_id -> hist_workbooks.id' AS fk,
  COUNT(*) AS orphelins
FROM "historical_events" ch LEFT JOIN "hist_workbooks" pa ON ch."hist_workbook_id" = pa."id"
WHERE ch."hist_workbook_id" IS NOT NULL AND pa."id" IS NULL
UNION ALL
SELECT 'historical_events.historical_event_type_id -> historical_event_types.type_id' AS fk,
  COUNT(*) AS orphelins
FROM "historical_events" ch LEFT JOIN "historical_event_types" pa ON ch."historical_event_type_id" = pa."type_id"
WHERE ch."historical_event_type_id" IS NOT NULL AND pa."type_id" IS NULL
UNION ALL
SELECT 'projects_contents.project_id -> projects.id' AS fk,
  COUNT(*) AS orphelins
FROM "projects_contents" ch LEFT JOIN "projects" pa ON ch."project_id" = pa."id"
WHERE ch."project_id" IS NOT NULL AND pa."id" IS NULL
UNION ALL
SELECT 'system_users.domain_id -> domains.id' AS fk,
  COUNT(*) AS orphelins
FROM "system_users" ch LEFT JOIN "domains" pa ON ch."domain_id" = pa."id"
WHERE ch."domain_id" IS NOT NULL AND pa."id" IS NULL
UNION ALL
SELECT 'users.site_id -> sites.id' AS fk,
  COUNT(*) AS orphelins
FROM "users" ch LEFT JOIN "sites" pa ON ch."site_id" = pa."id"
WHERE ch."site_id" IS NOT NULL AND pa."id" IS NULL
UNION ALL
SELECT 'users.site_role_id -> site_roles.id' AS fk,
  COUNT(*) AS orphelins
FROM "users" ch LEFT JOIN "site_roles" pa ON ch."site_role_id" = pa."id"
WHERE ch."site_role_id" IS NOT NULL AND pa."id" IS NULL
UNION ALL
SELECT 'users.system_user_id -> system_users.id' AS fk,
  COUNT(*) AS orphelins
FROM "users" ch LEFT JOIN "system_users" pa ON ch."system_user_id" = pa."id"
WHERE ch."system_user_id" IS NOT NULL AND pa."id" IS NULL
ORDER BY orphelins DESC, fk;
