-- Synthetic data for the reconstructed workgroup model.
-- Referential integrity is preserved: parents are loaded before children,
-- and every foreign key draws from its parent's actual id range.

USE SCHEMA TABLEAU_LEGACY.PUBLIC;

INSERT INTO "asset_lists" ("created_timestamp", "description", "id", "list_type", "luid", "name", "owner_id", "site_id", "site_luid", "sync_token", "updated_at", "visibility")
SELECT
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "created_timestamp",
  'Synthetic asset_lists record ' || (SEQ4() + 1)::VARCHAR AS "description",
  SEQ4() + 1 AS "id",
  ARRAY_CONSTRUCT('create','update','delete','publish','refresh','access')[UNIFORM(0, 5, RANDOM())]::VARCHAR AS "list_type",
  UUID_STRING() AS "luid",
  'asset_lists_' || (SEQ4() + 1)::VARCHAR AS "name",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "owner_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "site_id",
  UUID_STRING() AS "site_luid",
  'asset_lists.sync_token.' || (SEQ4() + 1)::VARCHAR AS "sync_token",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "updated_at",
  'asset_lists.visibility.' || (SEQ4() + 1)::VARCHAR AS "visibility"
FROM TABLE(GENERATOR(ROWCOUNT => 15));

INSERT INTO "datasources" ("ask_data_curator_feedback", "ask_data_indexing", "ask_data_indexing_new", "ask_data_setting", "asset_key_id", "certification_note", "certifier_details", "certifier_user_id", "connectable", "content_version", "created_at", "data_engine_extracts", "data_id", "db_class", "db_name", "description", "document_version", "embedded", "extract_creation_pending", "extract_encryption_state", "extract_storage_format", "extracts_incremented_at", "extracts_refreshed_at", "first_published_at", "hidden_name", "id", "incrementable_extracts", "is_certified", "is_hierarchical", "last_published_at", "lock_version", "luid", "modified_by_user_id", "name", "nlp_setting", "nlp_setting_new", "owner_id", "parent_type", "parent_workbook_id", "project_id", "reduced_data_id", "refreshable_extracts", "remote_query_agent_id", "repository_data_id", "repository_extract_data_id", "repository_url", "revision", "separated_data_id", "separated_reduced_data_id", "site_id", "size", "state", "table_name", "tds_luid", "updated_at", "using_remote_query_agent")
SELECT
  'datasources.ask_data_curator_feedback.' || (SEQ4() + 1)::VARCHAR AS "ask_data_curator_feedback",
  'datasources.ask_data_indexing.' || (SEQ4() + 1)::VARCHAR AS "ask_data_indexing",
  'datasources.ask_data_indexing_new.' || (SEQ4() + 1)::VARCHAR AS "ask_data_indexing_new",
  'datasources.ask_data_setting.' || (SEQ4() + 1)::VARCHAR AS "ask_data_setting",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "asset_key_id",
  'datasources.certification_note.' || (SEQ4() + 1)::VARCHAR AS "certification_note",
  'datasources.certifier_details.' || (SEQ4() + 1)::VARCHAR AS "certifier_details",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "certifier_user_id",
  UNIFORM(0, 1, RANDOM()) = 1 AS "connectable",
  UNIFORM(0, 100, RANDOM()) AS "content_version",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "created_at",
  UNIFORM(0, 1, RANDOM()) = 1 AS "data_engine_extracts",
  'datasources.data_id.' || (SEQ4() + 1)::VARCHAR AS "data_id",
  'datasources.db_class.' || (SEQ4() + 1)::VARCHAR AS "db_class",
  'datasources.db_name.' || (SEQ4() + 1)::VARCHAR AS "db_name",
  'Synthetic datasources record ' || (SEQ4() + 1)::VARCHAR AS "description",
  ARRAY_CONSTRUCT('01.02','02.02','03.01','04.02')[UNIFORM(0, 3, RANDOM())]::VARCHAR AS "document_version",
  'datasources.embedded.' || (SEQ4() + 1)::VARCHAR AS "embedded",
  UNIFORM(0, 100, RANDOM()) AS "extract_creation_pending",
  UNIFORM(0, 100, RANDOM()) AS "extract_encryption_state",
  UNIFORM(0, 100, RANDOM()) AS "extract_storage_format",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "extracts_incremented_at",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "extracts_refreshed_at",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "first_published_at",
  'datasources.hidden_name.' || (SEQ4() + 1)::VARCHAR AS "hidden_name",
  SEQ4() + 1 AS "id",
  UNIFORM(0, 1, RANDOM()) = 1 AS "incrementable_extracts",
  UNIFORM(0, 1, RANDOM()) = 1 AS "is_certified",
  UNIFORM(0, 1, RANDOM()) = 1 AS "is_hierarchical",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "last_published_at",
  UNIFORM(0, 100, RANDOM()) AS "lock_version",
  UUID_STRING() AS "luid",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "modified_by_user_id",
  'datasources_' || (SEQ4() + 1)::VARCHAR AS "name",
  'datasources.nlp_setting.' || (SEQ4() + 1)::VARCHAR AS "nlp_setting",
  'datasources.nlp_setting_new.' || (SEQ4() + 1)::VARCHAR AS "nlp_setting_new",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "owner_id",
  ARRAY_CONSTRUCT('create','update','delete','publish','refresh','access')[UNIFORM(0, 5, RANDOM())]::VARCHAR AS "parent_type",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "parent_workbook_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "project_id",
  'datasources.reduced_data_id.' || (SEQ4() + 1)::VARCHAR AS "reduced_data_id",
  UNIFORM(0, 1, RANDOM()) = 1 AS "refreshable_extracts",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "remote_query_agent_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "repository_data_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "repository_extract_data_id",
  '/datasources/' || (SEQ4() + 1)::VARCHAR AS "repository_url",
  'datasources.revision.' || (SEQ4() + 1)::VARCHAR AS "revision",
  'datasources.separated_data_id.' || (SEQ4() + 1)::VARCHAR AS "separated_data_id",
  'datasources.separated_reduced_data_id.' || (SEQ4() + 1)::VARCHAR AS "separated_reduced_data_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "site_id",
  UNIFORM(0, 50000, RANDOM()) AS "size",
  ARRAY_CONSTRUCT('create','update','delete','publish','refresh','access')[UNIFORM(0, 5, RANDOM())]::VARCHAR AS "state",
  'datasources.table_name.' || (SEQ4() + 1)::VARCHAR AS "table_name",
  UUID_STRING() AS "tds_luid",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "updated_at",
  UNIFORM(0, 1, RANDOM()) = 1 AS "using_remote_query_agent"
FROM TABLE(GENERATOR(ROWCOUNT => 300));

INSERT INTO "domains" ("active", "family", "id", "name", "short_name")
SELECT
  UNIFORM(0, 1, RANDOM()) = 1 AS "active",
  'domains.family.' || (SEQ4() + 1)::VARCHAR AS "family",
  SEQ4() + 1 AS "id",
  'domains_' || (SEQ4() + 1)::VARCHAR AS "name",
  'domains.short_name.' || (SEQ4() + 1)::VARCHAR AS "short_name"
FROM TABLE(GENERATOR(ROWCOUNT => 3));

INSERT INTO "flows" ("asset_key_id", "content_version", "created_at", "data_engine_extracts", "data_id", "description", "document_version", "embedded", "encryption_key_id", "extract_encryption_state", "file_type", "graph_image_id", "hidden", "id", "is_deleted", "kind", "last_published_at", "lock_version", "luid", "name", "owner_id", "project_id", "reduced_data_id", "site_id", "size", "thumbnail_id", "updated_at")
SELECT
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "asset_key_id",
  UNIFORM(0, 100, RANDOM()) AS "content_version",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "created_at",
  UNIFORM(0, 1, RANDOM()) = 1 AS "data_engine_extracts",
  'flows.data_id.' || (SEQ4() + 1)::VARCHAR AS "data_id",
  'Synthetic flows record ' || (SEQ4() + 1)::VARCHAR AS "description",
  ARRAY_CONSTRUCT('01.02','02.02','03.01','04.02')[UNIFORM(0, 3, RANDOM())]::VARCHAR AS "document_version",
  'flows.embedded.' || (SEQ4() + 1)::VARCHAR AS "embedded",
  'flows.encryption_key_id.' || (SEQ4() + 1)::VARCHAR AS "encryption_key_id",
  UNIFORM(0, 100, RANDOM()) AS "extract_encryption_state",
  ARRAY_CONSTRUCT('create','update','delete','publish','refresh','access')[UNIFORM(0, 5, RANDOM())]::VARCHAR AS "file_type",
  'flows.graph_image_id.' || (SEQ4() + 1)::VARCHAR AS "graph_image_id",
  UNIFORM(0, 1, RANDOM()) = 1 AS "hidden",
  SEQ4() + 1 AS "id",
  UNIFORM(0, 1, RANDOM()) = 1 AS "is_deleted",
  'flows.kind.' || (SEQ4() + 1)::VARCHAR AS "kind",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "last_published_at",
  UNIFORM(0, 100, RANDOM()) AS "lock_version",
  UUID_STRING() AS "luid",
  'flows_' || (SEQ4() + 1)::VARCHAR AS "name",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "owner_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "project_id",
  'flows.reduced_data_id.' || (SEQ4() + 1)::VARCHAR AS "reduced_data_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "site_id",
  UNIFORM(0, 50000, RANDOM()) AS "size",
  'flows.thumbnail_id.' || (SEQ4() + 1)::VARCHAR AS "thumbnail_id",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "updated_at"
FROM TABLE(GENERATOR(ROWCOUNT => 40));

INSERT INTO "hist_collections" ("collection_luid", "id", "name")
SELECT
  UUID_STRING() AS "collection_luid",
  SEQ4() + 1 AS "id",
  'hist_collections_' || (SEQ4() + 1)::VARCHAR AS "name"
FROM TABLE(GENERATOR(ROWCOUNT => 30));

INSERT INTO "hist_projects" ("id", "name", "project_id")
SELECT
  SEQ4() + 1 AS "id",
  'hist_projects_' || (SEQ4() + 1)::VARCHAR AS "name",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "project_id"
FROM TABLE(GENERATOR(ROWCOUNT => 120));

INSERT INTO "hist_schedules" ("day_of_month_mask", "day_of_week_mask", "end_at_minute", "end_schedule_at", "id", "is_serial", "minute_interval", "name", "priority", "schedule_id", "schedule_type", "scheduled_action", "start_at_minute")
SELECT
  UNIFORM(0, 100, RANDOM()) AS "day_of_month_mask",
  UNIFORM(0, 100, RANDOM()) AS "day_of_week_mask",
  UNIFORM(0, 100, RANDOM()) AS "end_at_minute",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "end_schedule_at",
  SEQ4() + 1 AS "id",
  UNIFORM(0, 1, RANDOM()) = 1 AS "is_serial",
  UNIFORM(0, 100, RANDOM()) AS "minute_interval",
  'hist_schedules_' || (SEQ4() + 1)::VARCHAR AS "name",
  UNIFORM(0, 100, RANDOM()) AS "priority",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "schedule_id",
  UNIFORM(0, 100, RANDOM()) AS "schedule_type",
  UNIFORM(0, 100, RANDOM()) AS "scheduled_action",
  UNIFORM(0, 100, RANDOM()) AS "start_at_minute"
FROM TABLE(GENERATOR(ROWCOUNT => 25));

INSERT INTO "historical_event_types" ("action_type", "name", "type_id")
SELECT
  ARRAY_CONSTRUCT('create','update','delete','publish','refresh','access')[UNIFORM(0, 5, RANDOM())]::VARCHAR AS "action_type",
  'historical_event_types_' || (SEQ4() + 1)::VARCHAR AS "name",
  SEQ4() + 1 AS "type_id"
FROM TABLE(GENERATOR(ROWCOUNT => 40));

INSERT INTO "metrics" ("asset_key_id", "connected_view_name", "connected_view_path", "created_at", "customized_view_id", "dataalert_id", "datasource_id", "description", "embedded", "id", "incomplete_refresh_attempts", "last_refreshed_at", "last_scheduled_at", "luid", "name", "owner_id", "project_id", "site_id", "suspend_state", "updated_at", "view_id", "workbook_id")
SELECT
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "asset_key_id",
  'metrics.connected_view_name.' || (SEQ4() + 1)::VARCHAR AS "connected_view_name",
  '/metrics/' || (SEQ4() + 1)::VARCHAR AS "connected_view_path",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "created_at",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "customized_view_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "dataalert_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "datasource_id",
  'Synthetic metrics record ' || (SEQ4() + 1)::VARCHAR AS "description",
  'metrics.embedded.' || (SEQ4() + 1)::VARCHAR AS "embedded",
  SEQ4() + 1 AS "id",
  UNIFORM(0, 100, RANDOM()) AS "incomplete_refresh_attempts",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "last_refreshed_at",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "last_scheduled_at",
  UUID_STRING() AS "luid",
  'metrics_' || (SEQ4() + 1)::VARCHAR AS "name",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "owner_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "project_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "site_id",
  UNIFORM(0, 100, RANDOM()) AS "suspend_state",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "updated_at",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "view_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "workbook_id"
FROM TABLE(GENERATOR(ROWCOUNT => 60));

INSERT INTO "projects" ("admin_insights_enabled", "controlled_permissions_enabled", "controlling_permissions_project_id", "created_at", "description", "id", "lower_name", "luid", "name", "nested_projects_permissions_included", "owner_id", "parent_project_id", "site_id", "special", "state", "updated_at")
SELECT
  UNIFORM(0, 1, RANDOM()) = 1 AS "admin_insights_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "controlled_permissions_enabled",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "controlling_permissions_project_id",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "created_at",
  'Synthetic projects record ' || (SEQ4() + 1)::VARCHAR AS "description",
  SEQ4() + 1 AS "id",
  'projects.lower_name.' || (SEQ4() + 1)::VARCHAR AS "lower_name",
  UUID_STRING() AS "luid",
  'projects_' || (SEQ4() + 1)::VARCHAR AS "name",
  UNIFORM(0, 1, RANDOM()) = 1 AS "nested_projects_permissions_included",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "owner_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "parent_project_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "site_id",
  UNIFORM(0, 100, RANDOM()) AS "special",
  ARRAY_CONSTRUCT('create','update','delete','publish','refresh','access')[UNIFORM(0, 5, RANDOM())]::VARCHAR AS "state",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "updated_at"
FROM TABLE(GENERATOR(ROWCOUNT => 120));

INSERT INTO "site_roles" ("display_name", "id", "licensing_rank", "name")
SELECT
  'site_roles.display_name.' || (SEQ4() + 1)::VARCHAR AS "display_name",
  SEQ4() + 1 AS "id",
  UNIFORM(0, 100, RANDOM()) AS "licensing_rank",
  'site_roles_' || (SEQ4() + 1)::VARCHAR AS "name"
FROM TABLE(GENERATOR(ROWCOUNT => 6));

INSERT INTO "sites" ("admin_insights_publish_frequency", "afe_enabled", "allow_live_query_sync", "allow_subscriptions_attach_pdf", "ask_data_mode", "attribute_capture_enabled", "authoring_disabled", "auto_suspend_refresh_enabled", "auto_suspend_refresh_inactivity_window", "backgrounder_governance_default_limit_enabled", "biometrics_mobile_enabled", "cache_warmup_enabled", "cache_warmup_threshold", "cataloging_enabled", "cmek_available", "collections_enabled", "commenting_enabled", "commenting_mentions_enabled", "content_admin_mode", "content_migration_tool_enabled", "content_version_limit", "created_at", "custom_subscription_email", "custom_subscription_footer", "data_alerts_enabled", "data_change_discovery_enabled", "data_orientation_enabled", "data_orientation_guest_users_enabled", "data_story_enabled", "derived_permissions_enabled", "domain_allowlist", "dqw_subscriptions_enabled", "eas_enabled", "einstein_in_flow_enabled", "explain_data_enabled", "extract_encryption_mode", "flow_auto_save_enabled", "flow_output_subscriptions_data_as_email_attachment_enabled", "flow_output_subscriptions_data_in_email_body_enabled", "flow_output_subscriptions_enabled", "flow_parameters_any_type_enabled", "flow_parameters_enabled", "flows_enabled", "guest_access_enabled", "iba_enabled", "id", "linked_tasks_enabled", "linked_tasks_run_now_enabled", "lock_version", "luid", "materialized_views_enabled", "materialized_views_mode", "metrics_enabled", "metrics_level", "metrics_snapshotting_enabled", "metrics_snapshotting_time_zone", "mfa_enforcement_exemption", "mfa_enforcement_legacy", "mfa_enforcement_status", "mixed_content_enabled", "name", "named_sharing_enabled", "notification_enabled", "notify_site_admins_on_throttle", "obfuscation_enabled", "personal_space_enabled", "personal_space_storage_quota", "protocol_cache_lifetime", "protocol_group_size_limit", "public_collections_enabled", "publish_to_salesforce_enabled", "query_limit", "refresh_token_setting", "request_access", "run_now_enabled", "sandbox_datasources_enabled", "sandbox_enabled", "sandbox_flows_enabled", "sandbox_storage_quota", "self_service_schedule_for_flow_enabled", "self_service_schedule_for_refresh_enabled", "self_service_schedules_enabled", "sheet_image_enabled", "site_invite_notification_enabled", "start_page_uri", "status", "status_reason", "storage_quota", "subscribe_others_enabled", "subscriptions_enabled", "support_access_enabled", "tag_limit", "tier_author_capacity", "tier_basic_user_capacity", "tier_interactor_capacity", "time_zone", "unrestricted_embedding_enabled", "updated_at", "url_namespace", "user_quota", "user_visibility", "version_history_enabled", "viz_in_tooltip_enabled", "viz_recs_enabled", "viz_recs_username_enabled", "web_editing_enabled", "web_extraction_enabled", "web_zone_content_enabled", "workflow_extension_enabled")
SELECT
  UNIFORM(0, 100, RANDOM()) AS "admin_insights_publish_frequency",
  UNIFORM(0, 1, RANDOM()) = 1 AS "afe_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "allow_live_query_sync",
  UNIFORM(0, 1, RANDOM()) = 1 AS "allow_subscriptions_attach_pdf",
  'sites.ask_data_mode.' || (SEQ4() + 1)::VARCHAR AS "ask_data_mode",
  UNIFORM(0, 1, RANDOM()) = 1 AS "attribute_capture_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "authoring_disabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "auto_suspend_refresh_enabled",
  UNIFORM(0, 100, RANDOM()) AS "auto_suspend_refresh_inactivity_window",
  UNIFORM(0, 1, RANDOM()) = 1 AS "backgrounder_governance_default_limit_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "biometrics_mobile_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "cache_warmup_enabled",
  UNIFORM(0, 100, RANDOM()) AS "cache_warmup_threshold",
  UNIFORM(0, 1, RANDOM()) = 1 AS "cataloging_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "cmek_available",
  UNIFORM(0, 1, RANDOM()) = 1 AS "collections_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "commenting_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "commenting_mentions_enabled",
  UNIFORM(0, 100, RANDOM()) AS "content_admin_mode",
  UNIFORM(0, 1, RANDOM()) = 1 AS "content_migration_tool_enabled",
  UNIFORM(0, 1000, RANDOM()) AS "content_version_limit",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "created_at",
  'user' || (SEQ4() + 1)::VARCHAR || '@example.com' AS "custom_subscription_email",
  'sites.custom_subscription_footer.' || (SEQ4() + 1)::VARCHAR AS "custom_subscription_footer",
  UNIFORM(0, 1, RANDOM()) = 1 AS "data_alerts_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "data_change_discovery_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "data_orientation_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "data_orientation_guest_users_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "data_story_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "derived_permissions_enabled",
  'sites.domain_allowlist.' || (SEQ4() + 1)::VARCHAR AS "domain_allowlist",
  UNIFORM(0, 1, RANDOM()) = 1 AS "dqw_subscriptions_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "eas_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "einstein_in_flow_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "explain_data_enabled",
  UNIFORM(0, 100, RANDOM()) AS "extract_encryption_mode",
  UNIFORM(0, 1, RANDOM()) = 1 AS "flow_auto_save_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "flow_output_subscriptions_data_as_email_attachment_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "flow_output_subscriptions_data_in_email_body_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "flow_output_subscriptions_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "flow_parameters_any_type_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "flow_parameters_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "flows_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "guest_access_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "iba_enabled",
  SEQ4() + 1 AS "id",
  UNIFORM(0, 1, RANDOM()) = 1 AS "linked_tasks_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "linked_tasks_run_now_enabled",
  UNIFORM(0, 100, RANDOM()) AS "lock_version",
  UUID_STRING() AS "luid",
  UNIFORM(0, 1, RANDOM()) = 1 AS "materialized_views_enabled",
  UNIFORM(0, 100, RANDOM()) AS "materialized_views_mode",
  UNIFORM(0, 1, RANDOM()) = 1 AS "metrics_enabled",
  UNIFORM(0, 100, RANDOM()) AS "metrics_level",
  UNIFORM(0, 1, RANDOM()) = 1 AS "metrics_snapshotting_enabled",
  'sites.metrics_snapshotting_time_zone.' || (SEQ4() + 1)::VARCHAR AS "metrics_snapshotting_time_zone",
  UNIFORM(0, 1, RANDOM()) = 1 AS "mfa_enforcement_exemption",
  UNIFORM(0, 1, RANDOM()) = 1 AS "mfa_enforcement_legacy",
  ARRAY_CONSTRUCT('create','update','delete','publish','refresh','access')[UNIFORM(0, 5, RANDOM())]::VARCHAR AS "mfa_enforcement_status",
  UNIFORM(0, 1, RANDOM()) = 1 AS "mixed_content_enabled",
  'sites_' || (SEQ4() + 1)::VARCHAR AS "name",
  UNIFORM(0, 1, RANDOM()) = 1 AS "named_sharing_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "notification_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "notify_site_admins_on_throttle",
  UNIFORM(0, 1, RANDOM()) = 1 AS "obfuscation_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "personal_space_enabled",
  UNIFORM(0, 100, RANDOM()) AS "personal_space_storage_quota",
  UNIFORM(0, 100, RANDOM()) AS "protocol_cache_lifetime",
  UNIFORM(0, 50000, RANDOM()) AS "protocol_group_size_limit",
  UNIFORM(0, 1, RANDOM()) = 1 AS "public_collections_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "publish_to_salesforce_enabled",
  UNIFORM(0, 1000, RANDOM()) AS "query_limit",
  UNIFORM(0, 100, RANDOM()) AS "refresh_token_setting",
  UNIFORM(0, 100, RANDOM()) AS "request_access",
  UNIFORM(0, 1, RANDOM()) = 1 AS "run_now_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "sandbox_datasources_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "sandbox_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "sandbox_flows_enabled",
  UNIFORM(0, 100, RANDOM()) AS "sandbox_storage_quota",
  UNIFORM(0, 1, RANDOM()) = 1 AS "self_service_schedule_for_flow_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "self_service_schedule_for_refresh_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "self_service_schedules_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "sheet_image_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "site_invite_notification_enabled",
  '/sites/' || (SEQ4() + 1)::VARCHAR AS "start_page_uri",
  ARRAY_CONSTRUCT('create','update','delete','publish','refresh','access')[UNIFORM(0, 5, RANDOM())]::VARCHAR AS "status",
  ARRAY_CONSTRUCT('create','update','delete','publish','refresh','access')[UNIFORM(0, 5, RANDOM())]::VARCHAR AS "status_reason",
  UNIFORM(0, 100, RANDOM()) AS "storage_quota",
  UNIFORM(0, 1, RANDOM()) = 1 AS "subscribe_others_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "subscriptions_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "support_access_enabled",
  UNIFORM(0, 1000, RANDOM()) AS "tag_limit",
  UNIFORM(0, 100, RANDOM()) AS "tier_author_capacity",
  UNIFORM(0, 100, RANDOM()) AS "tier_basic_user_capacity",
  UNIFORM(0, 100, RANDOM()) AS "tier_interactor_capacity",
  'sites.time_zone.' || (SEQ4() + 1)::VARCHAR AS "time_zone",
  UNIFORM(0, 1, RANDOM()) = 1 AS "unrestricted_embedding_enabled",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "updated_at",
  '/sites/' || (SEQ4() + 1)::VARCHAR AS "url_namespace",
  UNIFORM(0, 100, RANDOM()) AS "user_quota",
  UNIFORM(0, 100, RANDOM()) AS "user_visibility",
  UNIFORM(0, 1, RANDOM()) = 1 AS "version_history_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "viz_in_tooltip_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "viz_recs_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "viz_recs_username_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "web_editing_enabled",
  UNIFORM(0, 100, RANDOM()) AS "web_extraction_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "web_zone_content_enabled",
  UNIFORM(0, 1, RANDOM()) = 1 AS "workflow_extension_enabled"
FROM TABLE(GENERATOR(ROWCOUNT => 5));

INSERT INTO "tasks" ("active", "args", "consecutive_failure_count", "created_at", "creator_id", "historical_queue_time", "historical_run_time", "id", "last_success_completed_at", "luid", "obj_id", "obj_type", "priority", "run_count", "schedule_id", "site_id", "state", "subtitle", "title", "type", "updated_at")
SELECT
  UNIFORM(0, 1, RANDOM()) = 1 AS "active",
  'tasks.args.' || (SEQ4() + 1)::VARCHAR AS "args",
  UNIFORM(0, 50000, RANDOM()) AS "consecutive_failure_count",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "created_at",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "creator_id",
  UNIFORM(0, 100, RANDOM()) AS "historical_queue_time",
  UNIFORM(0, 100, RANDOM()) AS "historical_run_time",
  SEQ4() + 1 AS "id",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "last_success_completed_at",
  UUID_STRING() AS "luid",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "obj_id",
  ARRAY_CONSTRUCT('create','update','delete','publish','refresh','access')[UNIFORM(0, 5, RANDOM())]::VARCHAR AS "obj_type",
  UNIFORM(0, 100, RANDOM()) AS "priority",
  UNIFORM(0, 50000, RANDOM()) AS "run_count",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "schedule_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "site_id",
  UNIFORM(0, 100, RANDOM()) AS "state",
  'tasks.subtitle.' || (SEQ4() + 1)::VARCHAR AS "subtitle",
  'tasks_' || (SEQ4() + 1)::VARCHAR AS "title",
  ARRAY_CONSTRUCT('create','update','delete','publish','refresh','access')[UNIFORM(0, 5, RANDOM())]::VARCHAR AS "type",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "updated_at"
FROM TABLE(GENERATOR(ROWCOUNT => 200));

INSERT INTO "views" ("caption", "created_at", "datasource_id", "description", "edit_count", "fields", "first_published_at", "for_cache_updated_at", "id", "index", "is_deleted", "locked", "luid", "name", "owner_id", "published", "read_count", "repository_data_id", "repository_url", "revision", "sheet_id", "sheettype", "site_id", "state", "thumbnail_id", "title", "updated_at", "workbook_id")
SELECT
  'views_' || (SEQ4() + 1)::VARCHAR AS "caption",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "created_at",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "datasource_id",
  'Synthetic views record ' || (SEQ4() + 1)::VARCHAR AS "description",
  UNIFORM(0, 50000, RANDOM()) AS "edit_count",
  'views.fields.' || (SEQ4() + 1)::VARCHAR AS "fields",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "first_published_at",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "for_cache_updated_at",
  SEQ4() + 1 AS "id",
  UNIFORM(0, 100, RANDOM()) AS "index",
  UNIFORM(0, 1, RANDOM()) = 1 AS "is_deleted",
  UNIFORM(0, 1, RANDOM()) = 1 AS "locked",
  UUID_STRING() AS "luid",
  'views_' || (SEQ4() + 1)::VARCHAR AS "name",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "owner_id",
  UNIFORM(0, 1, RANDOM()) = 1 AS "published",
  UNIFORM(0, 50000, RANDOM()) AS "read_count",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "repository_data_id",
  '/views/' || (SEQ4() + 1)::VARCHAR AS "repository_url",
  'views.revision.' || (SEQ4() + 1)::VARCHAR AS "revision",
  'views.sheet_id.' || (SEQ4() + 1)::VARCHAR AS "sheet_id",
  ARRAY_CONSTRUCT('create','update','delete','publish','refresh','access')[UNIFORM(0, 5, RANDOM())]::VARCHAR AS "sheettype",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "site_id",
  ARRAY_CONSTRUCT('create','update','delete','publish','refresh','access')[UNIFORM(0, 5, RANDOM())]::VARCHAR AS "state",
  'views.thumbnail_id.' || (SEQ4() + 1)::VARCHAR AS "thumbnail_id",
  'views_' || (SEQ4() + 1)::VARCHAR AS "title",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "updated_at",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "workbook_id"
FROM TABLE(GENERATOR(ROWCOUNT => 4000));

INSERT INTO "workbooks" ("asset_key_id", "checksum", "content_version", "created_at", "data_engine_extracts", "data_id", "default_view_index", "description", "display_tabs", "document_version", "embedded", "extract_creation_pending", "extract_encryption_state", "extract_storage_format", "extracts_incremented_at", "extracts_refreshed_at", "first_published_at", "id", "incrementable_extracts", "is_deleted", "is_private", "last_published_at", "lock_version", "luid", "modified_by_user_id", "name", "owner_id", "parent_workbook_id", "primary_content_url", "project_id", "published_all_sheets", "reduced_data_id", "refreshable_extracts", "repository_data_id", "repository_extract_data_id", "repository_url", "revision", "share_description", "show_toolbar", "site_id", "size", "state", "thumb_user", "updated_at", "version", "view_count")
SELECT
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "asset_key_id",
  'workbooks.checksum.' || (SEQ4() + 1)::VARCHAR AS "checksum",
  UNIFORM(0, 100, RANDOM()) AS "content_version",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "created_at",
  UNIFORM(0, 1, RANDOM()) = 1 AS "data_engine_extracts",
  'workbooks.data_id.' || (SEQ4() + 1)::VARCHAR AS "data_id",
  UNIFORM(0, 100, RANDOM()) AS "default_view_index",
  'Synthetic workbooks record ' || (SEQ4() + 1)::VARCHAR AS "description",
  UNIFORM(0, 1, RANDOM()) = 1 AS "display_tabs",
  ARRAY_CONSTRUCT('01.02','02.02','03.01','04.02')[UNIFORM(0, 3, RANDOM())]::VARCHAR AS "document_version",
  'workbooks.embedded.' || (SEQ4() + 1)::VARCHAR AS "embedded",
  UNIFORM(0, 100, RANDOM()) AS "extract_creation_pending",
  UNIFORM(0, 100, RANDOM()) AS "extract_encryption_state",
  UNIFORM(0, 100, RANDOM()) AS "extract_storage_format",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "extracts_incremented_at",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "extracts_refreshed_at",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "first_published_at",
  SEQ4() + 1 AS "id",
  UNIFORM(0, 1, RANDOM()) = 1 AS "incrementable_extracts",
  UNIFORM(0, 1, RANDOM()) = 1 AS "is_deleted",
  UNIFORM(0, 1, RANDOM()) = 1 AS "is_private",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "last_published_at",
  UNIFORM(0, 100, RANDOM()) AS "lock_version",
  UUID_STRING() AS "luid",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "modified_by_user_id",
  'workbooks_' || (SEQ4() + 1)::VARCHAR AS "name",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "owner_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "parent_workbook_id",
  '/workbooks/' || (SEQ4() + 1)::VARCHAR AS "primary_content_url",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "project_id",
  UNIFORM(0, 1, RANDOM()) = 1 AS "published_all_sheets",
  'workbooks.reduced_data_id.' || (SEQ4() + 1)::VARCHAR AS "reduced_data_id",
  UNIFORM(0, 1, RANDOM()) = 1 AS "refreshable_extracts",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "repository_data_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "repository_extract_data_id",
  '/workbooks/' || (SEQ4() + 1)::VARCHAR AS "repository_url",
  'workbooks.revision.' || (SEQ4() + 1)::VARCHAR AS "revision",
  'Synthetic workbooks record ' || (SEQ4() + 1)::VARCHAR AS "share_description",
  UNIFORM(0, 1, RANDOM()) = 1 AS "show_toolbar",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "site_id",
  UNIFORM(0, 50000, RANDOM()) AS "size",
  ARRAY_CONSTRUCT('create','update','delete','publish','refresh','access')[UNIFORM(0, 5, RANDOM())]::VARCHAR AS "state",
  UNIFORM(0, 100, RANDOM()) AS "thumb_user",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "updated_at",
  ARRAY_CONSTRUCT('01.02','02.02','03.01','04.02')[UNIFORM(0, 3, RANDOM())]::VARCHAR AS "version",
  UNIFORM(0, 50000, RANDOM()) AS "view_count"
FROM TABLE(GENERATOR(ROWCOUNT => 800));

INSERT INTO "hist_datasources" ("certification_note", "datasource_id", "id", "is_certified", "name", "remote_query_agent_name", "repository_url", "revision", "size", "using_remote_query_agent")
SELECT
  'hist_datasources.certification_note.' || (SEQ4() + 1)::VARCHAR AS "certification_note",
  UNIFORM(1, 300, RANDOM()) AS "datasource_id",
  SEQ4() + 1 AS "id",
  UNIFORM(0, 1, RANDOM()) = 1 AS "is_certified",
  'hist_datasources_' || (SEQ4() + 1)::VARCHAR AS "name",
  'hist_datasources.remote_query_agent_name.' || (SEQ4() + 1)::VARCHAR AS "remote_query_agent_name",
  '/hist_datasources/' || (SEQ4() + 1)::VARCHAR AS "repository_url",
  'hist_datasources.revision.' || (SEQ4() + 1)::VARCHAR AS "revision",
  UNIFORM(0, 50000, RANDOM()) AS "size",
  UNIFORM(0, 1, RANDOM()) = 1 AS "using_remote_query_agent"
FROM TABLE(GENERATOR(ROWCOUNT => 300));

INSERT INTO "hist_flows" ("content_version", "flow_id", "id", "name", "size")
SELECT
  ARRAY_CONSTRUCT('01.02','02.02','03.01','04.02')[UNIFORM(0, 3, RANDOM())]::VARCHAR AS "content_version",
  UNIFORM(1, 40, RANDOM()) AS "flow_id",
  SEQ4() + 1 AS "id",
  'hist_flows_' || (SEQ4() + 1)::VARCHAR AS "name",
  UNIFORM(0, 50000, RANDOM()) AS "size"
FROM TABLE(GENERATOR(ROWCOUNT => 40));

INSERT INTO "hist_metrics" ("id", "metric_id", "name")
SELECT
  SEQ4() + 1 AS "id",
  UNIFORM(1, 60, RANDOM()) AS "metric_id",
  'hist_metrics_' || (SEQ4() + 1)::VARCHAR AS "name"
FROM TABLE(GENERATOR(ROWCOUNT => 60));

INSERT INTO "hist_sites" ("id", "name", "site_id", "url_namespace")
SELECT
  SEQ4() + 1 AS "id",
  'hist_sites_' || (SEQ4() + 1)::VARCHAR AS "name",
  UNIFORM(1, 5, RANDOM()) AS "site_id",
  '/hist_sites/' || (SEQ4() + 1)::VARCHAR AS "url_namespace"
FROM TABLE(GENERATOR(ROWCOUNT => 5));

INSERT INTO "hist_tasks" ("id", "priority", "state", "task_id", "type")
SELECT
  SEQ4() + 1 AS "id",
  UNIFORM(0, 100, RANDOM()) AS "priority",
  UNIFORM(0, 100, RANDOM()) AS "state",
  UNIFORM(1, 200, RANDOM()) AS "task_id",
  ARRAY_CONSTRUCT('create','update','delete','publish','refresh','access')[UNIFORM(0, 5, RANDOM())]::VARCHAR AS "type"
FROM TABLE(GENERATOR(ROWCOUNT => 200));

INSERT INTO "hist_users" ("domain_name", "email", "hist_licensing_role_id", "id", "name", "publisher_tristate", "site_admin_level", "site_role_id", "system_admin_level", "system_user_id", "user_id")
SELECT
  'hist_users.domain_name.' || (SEQ4() + 1)::VARCHAR AS "domain_name",
  'user' || (SEQ4() + 1)::VARCHAR || '@example.com' AS "email",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "hist_licensing_role_id",
  SEQ4() + 1 AS "id",
  'hist_users_' || (SEQ4() + 1)::VARCHAR AS "name",
  UNIFORM(0, 100, RANDOM()) AS "publisher_tristate",
  UNIFORM(0, 100, RANDOM()) AS "site_admin_level",
  UNIFORM(1, 6, RANDOM()) AS "site_role_id",
  UNIFORM(0, 100, RANDOM()) AS "system_admin_level",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "system_user_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "user_id"
FROM TABLE(GENERATOR(ROWCOUNT => 2400));

INSERT INTO "hist_views" ("id", "name", "repository_url", "revision", "view_id")
SELECT
  SEQ4() + 1 AS "id",
  'hist_views_' || (SEQ4() + 1)::VARCHAR AS "name",
  '/hist_views/' || (SEQ4() + 1)::VARCHAR AS "repository_url",
  'hist_views.revision.' || (SEQ4() + 1)::VARCHAR AS "revision",
  UNIFORM(1, 4000, RANDOM()) AS "view_id"
FROM TABLE(GENERATOR(ROWCOUNT => 4000));

INSERT INTO "hist_workbooks" ("id", "name", "repository_url", "revision", "size", "workbook_id")
SELECT
  SEQ4() + 1 AS "id",
  'hist_workbooks_' || (SEQ4() + 1)::VARCHAR AS "name",
  '/hist_workbooks/' || (SEQ4() + 1)::VARCHAR AS "repository_url",
  'hist_workbooks.revision.' || (SEQ4() + 1)::VARCHAR AS "revision",
  UNIFORM(0, 50000, RANDOM()) AS "size",
  UNIFORM(1, 800, RANDOM()) AS "workbook_id"
FROM TABLE(GENERATOR(ROWCOUNT => 800));

INSERT INTO "projects_contents" ("content_id", "content_type", "id", "project_id", "site_id")
SELECT
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "content_id",
  ARRAY_CONSTRUCT('create','update','delete','publish','refresh','access')[UNIFORM(0, 5, RANDOM())]::VARCHAR AS "content_type",
  SEQ4() + 1 AS "id",
  UNIFORM(1, 120, RANDOM()) AS "project_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "site_id"
FROM TABLE(GENERATOR(ROWCOUNT => 900));

INSERT INTO "system_users" ("activated_at", "activation_code", "admin_level", "asset_key_id", "auth_user_id", "created_at", "custom_display_name", "deleted_at", "domain_id", "email", "failed_login_attempts", "force_password_update", "friendly_name", "hashed_password", "id", "keychain", "last_failed_login", "last_password_update", "lock_version", "name", "protected_password", "protected_password_bad_format", "salt", "state", "sys", "updated_at")
SELECT
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "activated_at",
  'system_users.activation_code.' || (SEQ4() + 1)::VARCHAR AS "activation_code",
  UNIFORM(0, 100, RANDOM()) AS "admin_level",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "asset_key_id",
  'system_users.auth_user_id.' || (SEQ4() + 1)::VARCHAR AS "auth_user_id",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "created_at",
  UNIFORM(0, 1, RANDOM()) = 1 AS "custom_display_name",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "deleted_at",
  UNIFORM(1, 3, RANDOM()) AS "domain_id",
  'user' || (SEQ4() + 1)::VARCHAR || '@example.com' AS "email",
  UNIFORM(0, 100, RANDOM()) AS "failed_login_attempts",
  UNIFORM(0, 1, RANDOM()) = 1 AS "force_password_update",
  'system_users_' || (SEQ4() + 1)::VARCHAR AS "friendly_name",
  'system_users.hashed_password.' || (SEQ4() + 1)::VARCHAR AS "hashed_password",
  SEQ4() + 1 AS "id",
  'system_users.keychain.' || (SEQ4() + 1)::VARCHAR AS "keychain",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "last_failed_login",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "last_password_update",
  UNIFORM(0, 100, RANDOM()) AS "lock_version",
  'system_users_' || (SEQ4() + 1)::VARCHAR AS "name",
  'system_users.protected_password.' || (SEQ4() + 1)::VARCHAR AS "protected_password",
  UNIFORM(0, 1, RANDOM()) = 1 AS "protected_password_bad_format",
  'system_users.salt.' || (SEQ4() + 1)::VARCHAR AS "salt",
  ARRAY_CONSTRUCT('create','update','delete','publish','refresh','access')[UNIFORM(0, 5, RANDOM())]::VARCHAR AS "state",
  UNIFORM(0, 1, RANDOM()) = 1 AS "sys",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "updated_at"
FROM TABLE(GENERATOR(ROWCOUNT => 2000));

INSERT INTO "_users" ("domain_id", "domain_name", "domain_short_name", "friendly_name", "id", "licensing_role_id", "licensing_role_name", "login_at", "name", "site_id", "system_user_id")
SELECT
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "domain_id",
  '_users.domain_name.' || (SEQ4() + 1)::VARCHAR AS "domain_name",
  '_users.domain_short_name.' || (SEQ4() + 1)::VARCHAR AS "domain_short_name",
  '_users_' || (SEQ4() + 1)::VARCHAR AS "friendly_name",
  SEQ4() + 1 AS "id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "licensing_role_id",
  '_users.licensing_role_name.' || (SEQ4() + 1)::VARCHAR AS "licensing_role_name",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "login_at",
  '_users_' || (SEQ4() + 1)::VARCHAR AS "name",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "site_id",
  UNIFORM(1, 2000, RANDOM()) AS "system_user_id"
FROM TABLE(GENERATOR(ROWCOUNT => 2000));

INSERT INTO "historical_events" ("created_at", "details", "duration_in_ms", "hist_actor_site_id", "hist_actor_user_id", "hist_capability_id", "hist_collection_id", "hist_column_id", "hist_comment_id", "hist_config_id", "hist_data_connection_id", "hist_data_quality_indicator_id", "hist_data_role_id", "hist_database_id", "hist_datasource_id", "hist_flow_draft_id", "hist_flow_id", "hist_group_id", "hist_licensing_role_id", "hist_metric_id", "hist_project_id", "hist_published_connection_id", "hist_remote_agent_id", "hist_schedule_id", "hist_table_id", "hist_tag_id", "hist_target_site_id", "hist_target_user_id", "hist_task_id", "hist_view_id", "hist_workbook_id", "historical_event_type_id", "id", "is_failure", "worker")
SELECT
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "created_at",
  'historical_events.details.' || (SEQ4() + 1)::VARCHAR AS "details",
  UNIFORM(0, 100, RANDOM()) AS "duration_in_ms",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "hist_actor_site_id",
  IFF(UNIFORM(1, 7, RANDOM()) = 1, UNIFORM(1, 2400, RANDOM()), NULL) AS "hist_actor_user_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "hist_capability_id",
  IFF(UNIFORM(1, 7, RANDOM()) = 1, UNIFORM(1, 30, RANDOM()), NULL) AS "hist_collection_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "hist_column_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "hist_comment_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "hist_config_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "hist_data_connection_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "hist_data_quality_indicator_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "hist_data_role_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "hist_database_id",
  IFF(UNIFORM(1, 7, RANDOM()) = 1, UNIFORM(1, 300, RANDOM()), NULL) AS "hist_datasource_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "hist_flow_draft_id",
  IFF(UNIFORM(1, 7, RANDOM()) = 1, UNIFORM(1, 40, RANDOM()), NULL) AS "hist_flow_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "hist_group_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "hist_licensing_role_id",
  IFF(UNIFORM(1, 7, RANDOM()) = 1, UNIFORM(1, 60, RANDOM()), NULL) AS "hist_metric_id",
  IFF(UNIFORM(1, 7, RANDOM()) = 1, UNIFORM(1, 120, RANDOM()), NULL) AS "hist_project_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "hist_published_connection_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "hist_remote_agent_id",
  IFF(UNIFORM(1, 7, RANDOM()) = 1, UNIFORM(1, 25, RANDOM()), NULL) AS "hist_schedule_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "hist_table_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "hist_tag_id",
  IFF(UNIFORM(1, 7, RANDOM()) = 1, UNIFORM(1, 5, RANDOM()), NULL) AS "hist_target_site_id",
  IFF(UNIFORM(1, 20, RANDOM()) = 1, UNIFORM(1, 500, RANDOM()), NULL) AS "hist_target_user_id",
  IFF(UNIFORM(1, 7, RANDOM()) = 1, UNIFORM(1, 200, RANDOM()), NULL) AS "hist_task_id",
  IFF(UNIFORM(1, 7, RANDOM()) = 1, UNIFORM(1, 4000, RANDOM()), NULL) AS "hist_view_id",
  IFF(UNIFORM(1, 7, RANDOM()) = 1, UNIFORM(1, 800, RANDOM()), NULL) AS "hist_workbook_id",
  IFF(UNIFORM(1, 7, RANDOM()) = 1, UNIFORM(1, 40, RANDOM()), NULL) AS "historical_event_type_id",
  SEQ4() + 1 AS "id",
  UNIFORM(0, 1, RANDOM()) = 1 AS "is_failure",
  'historical_events.worker.' || (SEQ4() + 1)::VARCHAR AS "worker"
FROM TABLE(GENERATOR(ROWCOUNT => 200000));

INSERT INTO "users" ("created_at", "extracts_required", "id", "lock_version", "login_at", "luid", "nonce", "raw_data_suppressor_tristate", "row_limit", "site_id", "site_role_id", "storage_limit", "system_admin_auto", "system_user_id", "updated_at")
SELECT
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "created_at",
  UNIFORM(0, 1, RANDOM()) = 1 AS "extracts_required",
  SEQ4() + 1 AS "id",
  UNIFORM(0, 100, RANDOM()) AS "lock_version",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "login_at",
  UUID_STRING() AS "luid",
  'users.nonce.' || (SEQ4() + 1)::VARCHAR AS "nonce",
  UNIFORM(0, 100, RANDOM()) AS "raw_data_suppressor_tristate",
  UNIFORM(0, 1000, RANDOM()) AS "row_limit",
  UNIFORM(1, 5, RANDOM()) AS "site_id",
  UNIFORM(1, 6, RANDOM()) AS "site_role_id",
  UNIFORM(0, 1000, RANDOM()) AS "storage_limit",
  UNIFORM(0, 1, RANDOM()) = 1 AS "system_admin_auto",
  UNIFORM(1, 2000, RANDOM()) AS "system_user_id",
  DATEADD(second, -UNIFORM(0, 63072000, RANDOM()), CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS "updated_at"
FROM TABLE(GENERATOR(ROWCOUNT => 2400));
