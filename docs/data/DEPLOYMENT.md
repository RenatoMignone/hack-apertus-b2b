# Data services, shared access and recovery

Application/API, worker, adapters, PDF and HTTP frontend are integrated.
Application head is **`0008_live_corpus`**. Start at the
[first live run checklist](LIVE_SETUP.md) for existing deployments and Mac-to-host
setup. A new data stack follows the commands below; do not reinitialize Eric's
existing secrets/volumes. The earlier [migration](../team/MIGRATION_STATUS.md) reached 0007;
the [live runtime rollout](../team/RUNTIME_ACCESS_STATUS.md) now records host 0008. Future shared
migrations still require a backup/window and migration-role access. Windows
checkouts should apply the [LF fix](WINDOWS_SHELL_FIX.md); hosted encoder setup
is in [HF configuration](HOSTED_EMBEDDINGS.md).

Commands below run from the repository root in PowerShell. Use
Python 3.12–3.14 and Docker Desktop with its WSL2 Linux engine enabled. Linux hosts
can use the same Compose file and Python commands with their virtualenv paths.

## First start

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r src/backend/requirements.lock
.\.venv\Scripts\python.exe -m pip install --no-deps -e src/backend
.\.venv\Scripts\navigator.exe host-init
docker compose -f src/backend/deploy/compose.yaml up -d postgres minio storage-init
.\.venv\Scripts\navigator.exe --env-file src/backend/deploy/.env db-migrate
.\.venv\Scripts\navigator.exe --env-file src/backend/deploy/.env checkpoint-setup
.\.venv\Scripts\navigator.exe --env-file src/backend/deploy/.env validate-config
```

`host-init` reads the committed container digest lock and generates random
credentials in the ignored `src/backend/deploy/.env`. It refuses to overwrite
existing secrets. Protect that file with Windows account permissions; Unix mode
bits alone do not configure Windows ACLs. The host environment is for the
maintainer, never a teammate application environment. PostgreSQL initialization
scripts run only against a new Docker volume. Changing environment passwords
does not rotate an initialized database's passwords.

Run `src/backend/deploy/preflight.ps1` to inspect memory, disk, WSL, Docker,
listening ports and SSH. Keep enough space for corpus objects, image downloads
and a separate backup. Models have a separate hardware budget. Avoid a second
Docker Engine installation inside WSL when using Docker Desktop's engine.

PostgreSQL 17 and pgvector 0.8.2 use a Docker volume. Its three databases have
separate owners: `navigator_migrator`, `langgraph` and `langfuse`. The application
roles have no login. New application users inherit `navigator_runtime` for corpus
reads and owned case writes; `navigator_app` remains the explicit ingestion role.
See [live runtime](LIVE_CORPUS_RUNTIME.md) for migration 0008 and changing an
existing developer login without replacing credentials.
The host maintainer or an explicitly delegated migration operator applies migrations. Startup calls `check_schema`, which
checks the Alembic head without migrating. Migrations use a PostgreSQL advisory
lock. Use additive migrations when branches must share the same database.

MinIO uses the Chainguard distribution referenced by Langfuse's official
deployment; the selected image includes the server and `mc`. The unavailable
`minio/minio` distribution is not required. Its digest is locked despite the
upstream `latest` tag. The `navigator` bucket and `langfuse` bucket have separate
users/policies. Application artifact credentials cannot read the trace bucket
or delete artifacts. Source keys are hashes, never machine-specific paths.

## Smoke test and tests

```powershell
New-Item -ItemType Directory -Force .local | Out-Null
.\.venv\Scripts\navigator.exe --env-file src/backend/deploy/.env fixture-load > .local/fixture.json
.\.venv\Scripts\navigator.exe --env-file src/backend/deploy/.env fixture-search .local/fixture.json 'glucose monitoring'
.\.venv\Scripts\python.exe -m backend.tests.run
```

Fixtures contain synthetic text in EN/DE/FR/IT and deliberately artificial
three-dimensional vectors. Source-family labels exercise coverage validation;
the `.invalid` URLs and fictional content are not evidence about those units.
Fixture builds can only publish within `test*` or `fixture*` namespaces. There
are no measured embedding/reranker quality results.

The test runner uses the private host environment to create and drop uniquely
named disposable databases. It does not truncate `navigator`. Tests include
four concurrent database roles, RLS, Unicode offsets, model compatibility,
publication conflicts, case revisions, worker leases, revocation and an actual
LangGraph checkpoint save/reload. Install test dependencies from the lock file.
Without a host environment, run unit tests with `pytest`; integration tests
require `NAVIGATOR_TEST_ADMIN_DSN` for a PostgreSQL server with pgvector installed.

Measured on 18 October 2026: 26 tests passed against Docker PostgreSQL/pgvector,
including four simultaneous database logins and actual checkpoint save/reload.
A cold backup restored onto an isolated Compose project and reproduced four
pinned fixture hits while verifying all eight stored artifact hashes. A second
restore included the Langfuse PostgreSQL, ClickHouse, Redis and blob volumes;
the restored local Langfuse returned HTTP 200 from `/api/public/health`. These are storage and
deployment checks, not a retrieval-quality benchmark or a real LAN SSH trial.

## Four developers on the same network

First check peer reachability. Network client isolation may prevent SSH even
when everyone uses the same Wi-Fi. Use a permitted team-controlled LAN if needed.
Database and object-store ports bind exclusively to `127.0.0.1`.

Create a distinct ordinary Windows account and public-key login for each
teammate. Follow Microsoft's Windows OpenSSH instructions for public-key file
locations and ACLs, especially when using an administrator account. Prefer
ordinary accounts. In an elevated host PowerShell, enable SSH for the exact
teammate IP addresses using the supplied script:

```powershell
.\src\backend\deploy\configure-ssh.ps1 -AllowedAddresses 192.168.1.21,192.168.1.22,192.168.1.23
```

Replace the sample addresses with the real addresses. This script installs and
starts OpenSSH and restricts its standard firewall rule. Audit any independently
created SSH firewall rules as well. Configure key-only authentication after
testing the supplied keys. No SSH accounts, keys or firewall changes are made
automatically by `host-init`.

Provision one database account per developer, using the host environment:

```powershell
.\.venv\Scripts\navigator.exe --env-file src/backend/deploy/.env principal-create dev_alice alice --credentials-file .local/alice.json
.\.venv\Scripts\navigator.exe --env-file src/backend/deploy/.env scope-grant PRINCIPAL_UUID PUBLIC_SCOPE_UUID --write
```

The credential file contains the principal ID, namespace, role and password;
share it privately with that teammate. `principal-create` requires database
administrator rights, derived from the host environment or `ADMIN_DATABASE_URL`.
Create/review public sources and grant scopes deliberately. Developers use
their own namespace for profiles, runs, jobs and publication pointers. Shared
public source content can be granted to several principals. RLS verifies both
the database login and principal; passing a different principal UUID is rejected.
Use the same namespace for teammates who need the same published profile;
give experimental work a separate namespace and corresponding principal/role.

On each teammate computer, keep the tunnel running in the same OS environment
as the local backend:

```text
ssh -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -L 15432:127.0.0.1:5432 -L 19000:127.0.0.1:9000 WINDOWS_USER@HOST_LAN_IP
```

Set their private backend environment to:

```text
DATABASE_URL=postgresql+psycopg://DEV_ROLE:DEV_PASSWORD@127.0.0.1:15432/navigator
ARTIFACT_BACKEND=s3
S3_ENDPOINT_URL=http://127.0.0.1:19000
S3_BUCKET=navigator
S3_ACCESS_KEY_ID=<application artifact user>
S3_SECRET_ACCESS_KEY=<application artifact secret>
```

The artifact credential is a trusted backend/developer credential. Product end
users receive no database or object-store credentials; the implemented HTTP backend
authorizes artifact reads through scoped repository records. SSH keys and
database logins are individual. Framework database credentials stay with the
shared workflow host, rather than all teammates. No public IP or router port
forward is needed. The host must remain awake while others work.

## Optional local Langfuse

```powershell
docker compose -f src/backend/deploy/compose.yaml --profile observability up -d
```

Open `http://localhost:3000`, create the local organization/project and store its
keys only in the backend environment. A teammate can forward port 3000 through
SSH. ClickHouse and Redis have no published ports; the UI binds loopback.
The deployment disables Langfuse telemetry and in-app AI features. `SafeTracer`
allowlists identifiers/counts/timings before the SDK sees them, uses a bounded
queue, and degrades without stopping a case. Full model callbacks/payload capture
are deliberately not enabled. Do not point it at a hosted Langfuse service.

Model adapters consume the existing `LLM_NAME`, `LLM_BASE_URL`, `LLM_API_KEY`
configuration interface through implemented adapters. Authenticated synthetic
Apertus probes are recorded; EmbeddingGemma/BGE local runtime/assets still need
validation. Real index builds fail until verified configuration is supplied.
No weights are downloaded by this deployment.

## Backup and restore

Coordinate a maintenance window: stop all teammate backends, close their database
tunnels and pause workers. Stop external writers before invoking the command.
The command stops the Compose services, archives Docker volumes, records SHA-256
checksums and container digests, and restarts the previously running services.
This is a cold physical backup, including all three PostgreSQL databases, roles
and checkpoint tables, plus artifact bytes. Include tracing volumes when enabled.

```powershell
.\.venv\Scripts\navigator.exe --env-file src/backend/deploy/.env backup .local/backups/first
.\.venv\Scripts\navigator.exe --env-file src/backend/deploy/.env backup .local/backups/with-traces --include-traces
```

Backups contain `host.env` and source/case data. Keep them private and copy them
to encrypted storage outside this machine. Default policy: daily coordinated
backups, seven daily copies, one weekly restore drill; this targets an RPO of
24 hours, with RTO established by measured restores. The command never deletes
old backups automatically.

Restore onto an empty deployment with the same code and image digests. Prepare
the pinned images and host environment, then run:

```powershell
.\.venv\Scripts\navigator.exe --env-file src/backend/deploy/.env restore PRIVATE_BACKUP_DIRECTORY
```

Use `--include-traces` when the backup contains traces. Existing target Docker
volumes cause restore to refuse; never use it to overwrite a shared database.
For a rehearsal on the same computer, use a distinct `COMPOSE_PROJECT_NAME`,
`NAVIGATOR_HOST_ENV` and loopback port overrides `POSTGRES_PORT`, `S3_PORT`,
`S3_CONSOLE_PORT`. Validate schema, load the pinned fixture/case and verify object
hashes before declaring recovery. Keep compatible image exports for offline
recovery. PostgreSQL dump files alone do not back up artifacts or tracing stores.

## Local and LAN product hosting

The data services are portable to an independent Linux machine using the same
Compose file. The implemented API and React client can run on localhost. For LAN
hosting expose the authenticated application through a configured HTTPS entry
point; PostgreSQL and storage remain private. Current host placement, peer SSH
reachability, application port forwarding and user acceptance require confirmation.
The [runtime container notes](../../src/backend/deploy/README.runtime.md) describe
optional API/worker containers; no runtime image build is claimed by integration.

Preload locked Python wheels, images and verified model artifacts before an
offline deployment. Fixture retrieval needs no network calls, but passing these
tests does not establish a complete air-gapped product or model quality.

References: [Docker WSL2](https://docs.docker.com/desktop/features/wsl/),
[port publishing](https://docs.docker.com/engine/network/port-publishing/),
[Windows OpenSSH](https://learn.microsoft.com/en-us/windows-server/administration/openssh/openssh_install_firstuse),
[Langfuse deployment](https://langfuse.com/self-hosting/deployment/docker-compose).

## Schema upgrades and measured history

Always target the current Alembic head, now `0008_live_corpus`; the
[runbook](LIVE_SETUP.md#2-upgrade-only-if-behind-eric-or-his-delegated-operator)
explains migration credentials and sequencing. Migration 0005 archives populated
retired structures; 0006 adds restricted case-scope/runtime access; 0007 adds UI
lifecycle fields; 0008 adds immutable case-owned live captures and the narrow
runtime role. Existing case history remains; legacy results need a validated
v2 draft before new approval/export. Read [upgrade behavior](RELATIONAL_SCHEMA.md#removed-structures-and-upgrade-behavior).

Dated checks, all on 18 October 2026:

| Checkpoint | Environment / result | Scope |
| --- | --- | --- |
| Original data deployment | Docker PostgreSQL/pgvector: 26 tests and isolated backup/restore checks above | Storage/checkpoints/tracing, not product/model quality |
| Finalized schema 0005 | Disposable PostgreSQL 17 + pgvector: 42 tests | Fresh/upgrade/schema reference and owner-only legacy preservation |
| Integrated application 0007 | Disposable PostgreSQL 18.0 + pgvector 0.8.1: 153 backend tests; browser-to-PDF with synthetic inference/embeddings | Real module composition, restricted roles and actual PDF rendering |

See [integration verification](../team/INTEGRATION.md#verification) for exact
commands and limits. Do not combine historical counts as a new test total.
Eric subsequently migrated the shared host 0004 → 0007; see [the measured
rollout](../team/MIGRATION_STATUS.md). The integration's original tests remain dated.
No shared-host migration, real corpus publication or full live-model run was
performed by integration or this docs audit. Inference settings and optional
local-model/web provisioning are in [provider configuration](INFERENCE_CONFIGURATION.md)
and the [live runbook](LIVE_SETUP.md).
