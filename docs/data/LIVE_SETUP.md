# First live run: your Mac and Eric's host

18 October 2026 · Runbook for the integrated application. No commands in this
file have been executed on the shared host by this documentation audit.
[Current status](../project/STATUS.md) separates implementation from rollout.

**You can operate the backend from your Mac.** A successful PostgreSQL connection
alone does not establish readiness: the current factory loads the embedding
model in the local API/worker processes, and the worker also needs the separate
LangGraph database. Running the full backend on Eric's host is another option;
it keeps shared model assets/checkpoint credentials there, but needs an agreed
application entry point/tunnel. Pick one worker placement for the first run.

## 1. Confirm what actually exists (read-only)

Eric will perform the migration using the [complete rollout prompt](../team/prompts/04_SHARED_HOST_MIGRATION.md).
Ask him for the current schema revision and whether his ingestion/index build
has published a usable snapshot. The lane-C handoff last observed 0004; that is a
historical observation, not a fresh check. Do not assume either 0004 or 0007.

With your existing developer `.env`, activated backend environment and SSH tunnel,
this optional check reads only database identity/revision, without printing passwords:

```bash
python - <<'PY'
from sqlalchemy import text
from backend.data.cli import load_environment
from backend.config.settings import Settings
from backend.data.database import engine_for
load_environment('.env')
engine = engine_for(Settings.from_env().database_url)
try:
    with engine.begin() as connection:
        connection.execute(text('SET TRANSACTION READ ONLY'))
        print('Database / role:', connection.execute(
            text('SELECT current_database(), current_user')).one())
        print('Migration:', connection.execute(
            text('SELECT version_num FROM alembic_version')).scalars().all())
except Exception as error:
    raise SystemExit('Read-only check failed: ' + type(error).__name__)
finally:
    engine.dispose()
PY
```

Existing exported environment variables override env-file entries. Use a fresh
terminal with the intended environment; do not mix test, migrator and app DSNs.
This check does not verify corpus coverage, model availability or object access.

## 2. Upgrade only if behind (Eric or his delegated operator)

The required application revision in this checkout is **`0007_frontend_lifecycle`**.
If already there, do not repeat the rollout. If behind:

1. Coordinate a window with Eric; pause ingestion, all API/worker processes and
   other writers. Take a consistent database + artifact backup; retain restore
   instructions. [Deployment/recovery](DEPLOYMENT.md#backup-and-restore) describes
   the supplied host-side cold backup for its Compose topology.
2. Update the host checkout/environment to integrated main. Use a private
   maintainer environment whose **`DATABASE_URL` is the migration owner**
   (`navigator_migrator` in the supplied host setup), never your ordinary app DSN.
3. On the host, from repo root with its virtualenv active:

   ```text
   navigator --env-file src/backend/deploy/.env db-migrate
   navigator --env-file src/backend/deploy/.env validate-config
   ```

4. Confirm revision 0007, storage configuration and one preserved record/citation,
   then proceed with corpus/runtime setup. `validate-config` checks schema and
   storage configuration construction; it is not a model or S3 connectivity test.

`db-migrate` upgrades **all unapplied migrations to head**, including 0005 when
starting at 0004. It uses `DATABASE_URL`; setting `ADMIN_DATABASE_URL` alone does
not select its connection. 0005 archives populated retired structures, 0006 adds
restricted scope/RLS support, and 0007 persists UI flags/action answers. Published
corpus/index data is a separate operation, not created by a schema migration.
Do not edit old migrations, change `alembic_version` by hand or use destructive downgrades.

**Can you do it?** Yes, if Eric delegates the migration role and backup/maintenance
window. Your SSH key/developer DB credentials do not by themselves provide that
role. Prefer Eric running these two host commands rather than distributing his
private infrastructure env. Ordinary application processes keep developer/app
credentials after the upgrade. This documentation audit does not execute a shared migration.

## 3. Get the corpus/model handoff

The corpus owner must supply these real, mutually compatible items:

| Item | Runtime use |
| --- | --- |
| DB principal ID, namespace, application-role DSN and public scope grants | Server-side identity/access; shared profile must be visible in this namespace |
| Published profile UUID, snapshot/build IDs, taxonomy version and config hash | `RUNTIME_PROFILE_ID` selects the profile; new runs pin its published snapshot |
| Verified `ModelConfiguration` JSON and local embedding asset directory | `EMBEDDING_CONFIGURATION` / `EMBEDDING_MODEL_PATH`; exact model, tokenizer, templates and dimension must match the index |
| Artifact endpoint/bucket and backend application credentials | Reads source artifacts and writes reports; SSH forwarding does not grant object permissions |
| Checkpoint database access and agreed worker location | `LANGGRAPH_DATABASE_URL`; use a plain psycopg `postgresql://...` DSN for the saver |
| Coverage/failures and reviewed example query | Establish that sources/claims are usable, not merely that tables contain rows |

A published snapshot is required; a partly filled DB or extracted text alone is
insufficient. Use the implemented [ingestion CLI](../../src/backend/ingestion/README.md)
and [publication contract](INGESTION_RETRIEVAL_HANDOFF.md) for explicit builds.
Do not publish synthetic fixtures into the real pilot namespace.

## 4. Configure and run the backend on your Mac

1. Reinstall the merged core lock and editable backend using the [backend README](../../src/backend/README.md),
   even if the older lane environment already passed tests. Missing
   `navigator-runtime` or `langgraph.types` indicates an outdated environment.
   Provision compatible optional `local-models` dependencies and verified assets
   for this Mac; the core lock alone does not include the heavy model runtime.
   Optional dependencies still need a target-platform lock before deployment.
2. Keep your tunnel open, replacing the username with the account Eric supplied:

   ```text
   ssh -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -L 15432:127.0.0.1:5432 -L 19000:127.0.0.1:9000 YOUR_SSH_USER@192.168.10.230
   ```

   This is the previously supplied LAN host address; confirm it if DHCP/network
   changed. The reported SSH policy permits destination ports 5432 and 9000.
   Both navigator and langgraph databases use PostgreSQL port 5432, but each needs
   its own credentials. A tunnel to a host-run API on port 8000 requires Eric to
   explicitly extend that policy; do not assume it is allowed.
3. Copy root [.env.example](../../.env.example) to a private ignored file without
   replacing existing secrets. Set application DB/S3 credentials, permitted
   checkpoint DSN, profile UUID, verified embedding JSON/assets, current private
   Keera key and the integrated factories/PDF versions/logo path.
4. Generate a private random operator token; put only its SHA-256 digest in
   `RUNTIME_AUTH_BINDINGS`, with the real principal ID/namespace. Keep the raw
   token for the browser connection screen. API and worker use the same bindings;
   the digest authenticates the operator, not the LLM provider. See
   [runtime settings](../../src/backend/config/README.md).
5. The checkpoint owner explicitly runs this once where approved:

   ```text
   navigator-runtime --env-file .env checkpoints-setup
   ```

   Framework schema setup is separate from application migrations; do not share
   framework owner credentials casually just to make a local experiment start.
6. From repo root in separate terminals using the same private env:

   ```text
   navigator-runtime --env-file .env serve --host 127.0.0.1 --port 8000
   navigator-runtime --env-file .env worker
   ```

Start without optional web/reranker if not provisioned; web remains disabled when
`RUNTIME_WEB_FACTORY` is empty. Their absence must be visible, not replaced by
invented evidence. Connected Keera requires `DEPLOYMENT_MODE=connected`.

## 5. Connect and verify

Start the [frontend](../../src/frontend/README.md) with Node 22.18+ and its default
HTTP mode, then enter your operator token. The Vite dev proxy targets localhost:8000.
Run one permitted public test case: verify actual progress or clarification,
source quotations and caveats, review every reason, keep at least one and download
PDF. Confirm an input edit creates a new researched revision and stale exports
are rejected. Record environment, corpus/model pins, outcome and failures.

A capabilities response reports configuration, not a full provider health check.
A synthetic browser smoke already passed; this live acceptance still needs real
assets/corpus/providers. Later evaluate research quality and target-host restart.
No shared tests, migration or model download happen automatically at startup.
