# Infrastructure and deployment

[Local setup](LIVE_SETUP.md) runs API, worker and frontend against provisioned
services. [Docker guide](../judges/DOCKER.md) describes a new isolated stack.
These are distinct from migrating an existing shared host.

## Topology and roles

`deploy/compose.yaml` supplies PostgreSQL/pgvector, MinIO and storage initialization;
its optional observability profile adds self-hosted Langfuse dependencies.
`runtime.compose.yaml` supplies API/worker on an existing private network.
`search.compose.yaml` supplies private SearXNG. Frontend runs separately.

The application database uses restricted authenticated runtime identities and
scope grants. Ingestion, migration owner, checkpoint saver and trace storage have
separate responsibilities. API/worker must never use a migration-owner DSN. Keep
DB/object storage private; expose the authenticated application over HTTPS for
shared access. Individual SSH tunnels are a development option, not authorization.

## New stack

Only on a new isolated deployment, install backend dependencies and run
`navigator host-init`, then the base Compose stack. Initialization refuses to
overwrite private secrets and database initialization scripts only run on fresh
volumes. Use exact commands in [Docker setup](../judges/DOCKER.md).
Never reinitialize an existing shared stack to resolve developer access.
Image digests are locked in `deploy/images.lock.json`.

## Migration and optional activation

Current source head: **`0012_membership_lookup`**. Inspect the installed host's
`alembic_version`; do not infer rollout from source. The authorized maintainer
backs up, coordinates writers and applies forward migrations:

```text
navigator --env-file PRIVATE_MAINTAINER_ENV db-migrate
```

Application startup checks schema and never migrates. Migration advisory locking
and bounded DDL waits do not replace a maintenance plan. Review RLS/owner grants
and verify restricted runtime behavior after rollout. Historical populated retired
tables remain owner-only legacy; runtime never queries them.

`0009_case_memory` and `0010_rich_outputs` add optional features. Enable
`CASE_MEMORY_ENABLED` / `RUNTIME_RICH_OUTPUTS_ENABLED` only with migrated tables,
compatible assets and accepted access; supply the unchanged PPTX template path.
Source 0011/0012 improve capture/membership paths; see [performance](CAPTURE_PERFORMANCE.md).
Checkpoint tables use the framework's explicit `navigator-runtime ... checkpoints-setup`
with authorized setup access; do not rerun setup from an ordinary worker account.

## Containers and platform

The runtime image runs non-root and requires a verified digest-pinned Python base
image. Package encoder/tokenizer/reranker/crawler assets and mount configurations;
core containers do not download them at startup. Docker-internal DB/storage/search
addresses differ from host SSH-forwarded loopback addresses. See
[runtime container notes](../../src/backend/deploy/README.runtime.md).

Windows Docker Desktop uses Linux containers/WSL2. Root `.gitattributes` enforces
LF for shell scripts. Existing Windows-mounted checkouts with CRLF entrypoints
must restore LF before running them; check the script with `/bin/sh -n` rather
than retaining temporary schema-bootstrap overrides.

## Backup and restore

Coordinate a maintenance window and stop writers before cold backups:

```text
navigator --env-file PRIVATE_MAINTAINER_ENV backup PRIVATE_BACKUP_DIRECTORY
navigator --env-file PRIVATE_MAINTAINER_ENV restore PRIVATE_BACKUP_DIRECTORY
```

`--include-traces` includes tracing volumes where enabled. Backups contain private
host configuration/credentials, application/checkpoint DB data and artifacts;
protect and copy them to encrypted independent storage. Restore only to empty
compatible volumes/digests, using a distinct Compose project/ports for rehearsals.
Verify schema, IDs, scope isolation and source/report hashes before declaring
recovery. A DB dump alone omits artifact/trace stores. Select retention/RPO/RTO
with the operator and measure restores on the target host.

## Acceptance

Agree worker placement/queue ownership and process supervision, apply private
settings, restart API/worker/frontend, run readiness then an actual case/review/
export. Test controlled restart/resume and backup restore separately. Hosted
Keera/HF and web are connected dependencies. Offline requires local models/assets,
disabled external egress and demonstrated cold-start/report completion.
[Delivery status](../project/STATUS.md) records outstanding acceptance.
