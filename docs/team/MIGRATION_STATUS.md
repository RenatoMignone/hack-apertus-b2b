# Shared-host migration status

**Measured: 18 October 2026, 20:38 Europe/Madrid (18:38 UTC). Completed.**

## Authorization and code

- The host maintainer explicitly confirmed the maintenance window in this chat.
  External API/worker/ingestion writers were declared paused. Immediately before
  migration, PostgreSQL reported no other sessions connected to `navigator`.
- Fetched `origin/main`; it and local `main` matched
  `3d008019c0dfb50cd9bd01e6947fcf7ce0ec3fc2`. Expected migration head matched the
  rollout prompt: `0007_frontend_lifecycle`.
- Preserved the untracked `docs/team/runtime/mo/` directory in the original
  checkout. Used a clean feature worktree on `codex/shared-host-migration`.
  This status file is uncommitted in that worktree; nothing was committed/pushed.
- Installed the integrated core lock and editable backend in the host `.venv`;
  `pip check` passed. No models, optional model runtime or paid services installed.

## Database and preservation

- Compose project: `bern-navigator`; PostgreSQL **17.10**, pgvector **0.8.2**.
- Before: `0004_case_pipeline`. After: **`0007_frontend_lifecycle`**.
  Existing migrations 0005, 0006 and 0007 ran as `navigator_migrator`, without
  editing migration history or bypassing RLS. A second `db-migrate` was a no-op;
  `check_schema` and the requested `validate-config` command passed.
- Application tables reduced from 70 to the expected **63**. The seven retired
  tables were empty; no legacy archive was necessary. No chunks had additional
  retired encoding context. This is expected retirement, not lost populated data.
- Retained: four documents, four immutable versions, four chunks, four vectors,
  eight artifacts, one snapshot, one active pointer, three principals and three
  scope grants. Before/after counts and canonical row fingerprints matched for
  every retained table, including IDs, pins, grants and embedding configurations.
- There were no cases/results; lifecycle status conversion therefore had no
  existing rows to exercise. `cases.cases.on_hold`, `outcome`, and
  `cases.action_items.answer` were verified present.
- The sole active snapshot uses a **test-only synthetic embedding configuration**.
  **There is no production/reviewed real corpus snapshot.** Nothing was ingested,
  rebuilt, fixture-loaded or published during this rollout.

## Recovery verification

- Private recovery directory: host-local `.local/migration-20261018/`.
  Backup/reference contents are deliberately not committed or reproduced here.
- Cold backup includes the complete PostgreSQL volume (all three databases and
  database roles), artifact volume, ClickHouse data/logs and Redis data. The six
  file checksums, including the private host environment, passed; all five archive
  member streams were read successfully. Matching code revision, container image
  IDs, pinned image references and Compose hash were retained privately.
- Verified running images matched the configured backup images before stopping.
- Rehearsed extraction of all five archives into fresh, uniquely named Docker
  volumes, without overwriting shared volumes. Isolated PostgreSQL started at
  0004 and reproduced the four versions, snapshot, all framework databases and
  existing developer/application roles. Restored MinIO verified all eight artifact
  byte counts and SHA-256 hashes. The same eight live artifact hashes passed
  after migration. Trace archives were restored, but isolated trace services
  were not started; no end-to-end trace recovery claim is made.
- Rehearsal containers are stopped. Rehearsal volumes remain private for recovery
  inspection; no shared/test volume deletion was performed. Backup ACLs restrict
  access to the host user, SYSTEM and local Administrators.
- Restore only onto fresh isolated deployment volumes, using the matching images
  and Compose revision, following [the recovery procedure](../data/DEPLOYMENT.md#backup-and-restore).
  The backup is pre-upgrade 0004, not an immediately runnable 0007 database.

## Windows startup issue and services

The backup's automatic restart initially failed because Windows CRLF in
`init-storage.sh` made `/bin/sh` reject `set -eu`. Backup creation/checksums had
already completed; migration had not begun. Recovered startup with the private
`.local/migration-20261018/windows-shell.override.yaml`, which strips carriage
returns at execution time. No bootstrap source/history/credentials were changed.
Retain this override for Compose operations on this checkout until shell-file
line endings are fixed in a separately reviewed change; a plain Compose startup
can recreate the failing bootstrap again.

From the original repository root, the verified startup form is:

```powershell
docker compose -f src/backend/deploy/compose.yaml -f .local/migration-20261018/windows-shell.override.yaml --env-file src/backend/deploy/.env --profile observability up -d postgres minio redis clickhouse langfuse-web langfuse-worker
```

All six previously running shared services were restored. PostgreSQL, Redis and
ClickHouse reported healthy; MinIO liveness and Langfuse public health returned
HTTP 200. Storage bootstrap exited successfully. PostgreSQL and artifact ports
remain bound to loopback; no public exposure was added. Bind mounts point back
to the original host checkout, not the temporary migration worktree.

## Security and actual checks

- `ops.ensure_case_scope(uuid)` exists as SECURITY DEFINER with fixed
  `search_path=pg_catalog`. EXECUTE is granted to `navigator_app`, not PUBLIC.
  The existing migration's owner/principal/namespace checks were inspected.
- Both `runtime_private` policies exist as RESTRICTIVE policies on
  `ops.stage_attempts` and `ops.outbox`.
- `navigator_app` remains NOLOGIN, non-superuser, without BYPASSRLS, CREATEDB
  or CREATEROLE. Existing Ren and Elia credentials successfully performed
  authenticated scoped reads: four versions, one fixture snapshot, zero cases.
- LangGraph database connectivity works with the private host configuration;
  checkpoint tables, blobs, writes and migration tables exist. This does not
  establish that the Mac operator has checkpoint credentials/access.
- No fixture-load, pytest, case creation, privilege/isolation write test or
  checkpoint write was run against shared data. Security behavior beyond the
  inspected function/policies and developer reads is not claimed as live-tested.

## Copyable Mac-operator handoff

```text
Eric's shared navigator DB is now at 0007_frontend_lifecycle.
Host code baseline: 3d008019c0dfb50cd9bd01e6947fcf7ce0ec3fc2.
PostgreSQL 17.10 / pgvector 0.8.2. Existing roles/grants/artifacts were preserved.
Use your existing individual SSH tunnel and private developer env, never the
maintainer DSN. Database/storage ports remain host-loopback-only.
The active snapshot is synthetic/test-only; no real corpus snapshot is ready.
Do not start a real case worker until reviewed profile/snapshot/build/config
pins, a compatible embedding adapter/configuration, permitted model access,
checkpoint credentials and runtime bearer-token bindings have been supplied.
No API/frontend was deployed and no external writers were restarted by this task.
Use only code compatible with 0007 before reconnecting application writers.
```

Private runtime token bindings, embedding configuration and model path are absent
from the host environment. S3 access was verified on the host, not independently
from a Mac. Real Apertus authentication/quotas, the proposed HF embedding endpoint
and its adapter, reviewed MeSH-tagged corpus publication, remote checkpoint access
and a combined provider-backed case remain gates. This database migration alone
does not prove the complete application is live. Teammate writers remain paused
pending their operators' compatibility/readiness checks; DBeaver may reconnect.

## Subsequent repository fixes

The LF checkout rule and host rewrite instructions are now in
[Windows shell fix](../data/WINDOWS_SHELL_FIX.md); normal bootstrap still needs
host-side verification before retiring the private override. The shared hosted
encoder is implemented and protocol/parity tested: [HF handoff](../data/HOSTED_EMBEDDINGS.md).
The recorded migration results above retain their original scope.

## Optional release prepared — 19 October 2026

### Shared-host activation — 19 October 2026, 07:44 Madrid

The operator confirmed Elia's application API/worker pause. Remaining ordinary
developer database connections were idle with no open transaction; they were
preserved. The existing `navigator_migrator` identity applied 0009 and 0010 using
the normal application `db-migrate` command against `navigator`, then repeated
it successfully as a no-op. LangGraph and infrastructure services were unchanged.

A fresh custom-format backup contains 561,838,357 bytes. SHA256:
`1bb10c9571d4ed86bbebdde675b15378068b85fa77fefc6bdd29a6ac3ddc1b14`.
Archive listing was validated; a full restore of this archive was not rehearsed.
The private operator receipt retains its location. Recovery requires restoring
that archive with `pg_restore` into a separately provisioned database and checking
it before an explicit cutover, never dropping the live ingestion database.
Feature rollback means disabling the two optional flags, not schema downgrade.

Measured before/after counts were identical: 225 sources, 2,149 documents and
versions, 7,703 claims, 4,197 artifacts. All existing IDs in those tables were
preserved, including case-local records; these are not public-only crawl counts.
The two new tables have owner RLS. `navigator_runtime` has SELECT/INSERT/UPDATE
on memory profiles, SELECT/INSERT on business contexts, and no DELETE on either.
The 768-dimension partial HNSW memory index exists. No grants were widened.

The focused isolated acceptance suite passed **21 tests** on Windows, including
real disposable PostgreSQL checkpoints, killed-process recovery, combined
controlled research, memory, manual plans and PDF/PPTX. The test subprocess
harness now uses a bounded thread-launched subprocess with an explicit source
path and Windows selector policy. One pytest loop-policy deprecation warning
remains. Models/web responses are synthetic; no fixtures entered the shared host.

Elia and Renato's private bundles now include a portable optional-settings helper
and the unchanged supplied PPTX template (SHA256
`a2f5e50ff7b986fe6a5a2f38654bf5459142ea9285e844e12aa9392f20f7a262`).
Prepared settings enable `CASE_MEMORY_ENABLED=true`, minimum score 50
(uncalibrated), `RUNTIME_RICH_OUTPUTS_ENABLED=true`, template version
`challenge-pptx-a2f5e50ff7b9`, renderer version `pdf-pptx-df0626b`. All personal
bindings, tokens, checkpoint/MinIO credentials, model settings and tunnel endpoints
were preserved. No existing case was opted in or indexed.

Both ordinary user identities passed read-only host-network readiness: schema,
identity, pinned encoder/local tokenizer, checkpoint reads and S3 bucket HEAD.
Authenticated ASGI composition on this host returned 200 with PDF/PPTX capabilities
and existing-case manual/history controls. These checks used actual ordinary
credentials and explicit host endpoint overrides in memory; they did not test
the peers' running Mac servers or their tunnels. Earlier artifact write/read
evidence is separate; this activation did not repeat those writes.

**Per-user activation remains:** apply the private helper to each existing local
env after pulling current main; restart that user's API/worker with matching code
and settings; rebuild/restart the frontend; run the supplied read-only readiness
command through the user's own tunnel. The permitted real-case plan revision,
review, PDF/PPTX download, old-revision checks, real-case opt-in/out and owner
isolation acceptance remain operator tasks. Combined real DB/web/Keera acceptance,
human relevance labels and similarity calibration remain separate open work.

### Historical preparation note (superseded by activation above)

Source now includes 0009_case_memory and 0010_rich_outputs. These were tested on
disposable PostgreSQL only; this task did not migrate the shared host. Current
runtime explicitly accepts 0008 core while both optional flags are false. Eric's
[activation prompt](OPTIONAL_FEATURE_ACTIVATION.md) owns backup/migration and
per-host feature enablement. The earlier host measurements above remain dated.
