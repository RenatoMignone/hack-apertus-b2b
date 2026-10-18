# Eric — migrate and verify the shared database

Current task, 18 October 2026. Unlike prompts 01–03, this is a new rollout task.
Copy the prompt below into your agent on the database host.

```text
You are operating Eric's existing shared Bern Navigator PostgreSQL deployment.
The backend/runtime, backend/intelligence, backend/backbone and ui-polish branches
are integrated into main (integration baseline 4c6cfe2). I am the host maintainer
and authorize a coordinated backup, application-schema migration and verification.
Do not ingest/rebuild/publish the corpus, download models, provision paid services
or deploy the API/frontend as part of this task.

Read AGENTS.md, docs/team/INTEGRATION.md, docs/data/DEPLOYMENT.md,
docs/data/RELATIONAL_SCHEMA.md and the actual migration/database/recovery code.
If available, also read docs/project/STATUS.md and docs/data/LIVE_SETUP.md.
Completed lane prompts/ownership freezes are historical. Preserve local work,
private env files, existing accounts/grants and original materials. Do not reset
branches or overwrite credentials. Never print secrets or DSNs containing them.

1. Inspect first, without mutation.
   - Confirm the correct repository, git revision/status and current main.
     Fetch and fast-forward a clean checkout; if it is dirty, preserve it and
     use an appropriate separate checkout. Do not merge unfinished local work.
   - Identify the actual Compose project, running services, storage paths,
     PostgreSQL/pgvector versions, current Alembic revision and migration role.
     0004 was a historical observation; do not assume it is still current.
   - This baseline's expected head is 0007_frontend_lifecycle. If current main
     has a different head, report the difference before changing the shared DB.
     If already at 0007, verify readiness and skip the migration.
   - Record non-sensitive pre-upgrade counts/IDs for retained corpus entities,
     documents/versions, snapshots/active pointers and existing cases/results.
     Note populated structures 0005 will archive; distinguish those from loss.

2. Prepare recovery and an agreed maintenance window.
   - Coordinate with teammates and pause ingestion, API/worker and other writers;
     no migration while another task is filling/publishing this same database.
     If the window cannot be confirmed, stop before shared mutation and report it.
   - Use the existing host backup procedure, including database roles/framework
     databases and artifact bytes; include tracing stores if enabled. Inspect
     data/recovery.py before running it: the supplied cold backup stops/restarts
     its Compose services. Keep external writers paused after services return.
   - Use a new private backup destination. Verify manifest checksums and retain
     the matching code/Compose/image-digest revision and recovery instructions.
     Backups contain secrets; do not commit them. If recovery cannot be verified,
     stop before migration. An isolated restore rehearsal is preferred where
     existing resources allow; never restore onto existing shared volumes.

3. Apply the existing migrations, without altering their history.
   - Activate/install the integrated backend core lock and editable package in
     the appropriate host environment. Use a clean environment without stale
     exported DATABASE_URL overrides.
   - Use the private maintainer env whose DATABASE_URL is the migration owner
     (normally navigator_migrator), not an ordinary developer/application login.
     ADMIN_DATABASE_URL alone does not choose db-migrate's connection.
   - From repository root, with the correct env path if different, run:
       navigator --env-file src/backend/deploy/.env db-migrate
       navigator --env-file src/backend/deploy/.env validate-config
   - db-migrate upgrades every missing revision to head; starting at 0004 means
     0005_finalize_schema, 0006_runtime_access, 0007_frontend_lifecycle.
     0005 preserves populated retired data in owner-only legacy; 0006 adds
     restricted owner-checked case-scope provisioning and runtime RLS; 0007 adds
     on_hold/outcome and action answer fields and converts combined statuses.
   - Do not bypass constraints/RLS, edit alembic_version, rewrite migrations or
     use destructive downgrade. If an upgrade fails, capture a sanitized cause,
     check actual committed state and stop; do not invent a production repair.

4. Verify and hand off.
   - Confirm exactly 0007_frontend_lifecycle and successful check_schema.
   - Check retained records, IDs, snapshot pins, existing artifacts and expected
     legacy preservation against the pre-upgrade inventory. Verify 0007 fields
     and expected status conversion on existing rows where applicable.
   - Verify ops.ensure_case_scope(uuid), its restricted EXECUTE permissions and
     runtime_private RLS policies. Confirm navigator_app remains non-privileged;
     use real provisioned developer identities for scoped read checks.
   - Do not run fixture-load, corpus publication or pytest against shared data.
     Any write/isolation tests need disposable databases. Report separately what
     was actually tested versus only inspected.
   - Resume only the services/writers agreed for this window, checking that their
     code is compatible with the new head. If any writer must stay paused, say why.
   - Update a focused docs/team/MIGRATION_STATUS.md with timestamp, code revision,
     before/after DB head, DB/extension versions, backup verification (private
     reference only), checks performed, preservation findings and remaining gates.
     Do not include passwords, tokens, private env/backup contents or company data.
     Do not commit/push without a separate request.

Final response: migration completed or blocked; exact revision; recovery/check
results; services resumed/paused; and a copyable non-secret handoff for the Mac
backend operator. Include principal ID/namespace/profile/snapshot/build/config
identifiers only where already provisioned and appropriate to share. State whether
any real corpus snapshot exists. Identify missing embedding configuration/assets,
checkpoint access, storage access or runtime token setup without inventing values.
This migration alone does not prove the full application is live.
```
