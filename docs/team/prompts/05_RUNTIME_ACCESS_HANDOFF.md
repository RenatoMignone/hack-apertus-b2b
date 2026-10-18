# Eric — provide backend runtime access while ingestion continues

Read `AGENTS.md`, `docs/plans/MODULE_HANDOFFS.md`, the execution graph and
processing boundaries, then `docs/data/LIVE_SETUP.md`, `DEPLOYMENT.md`,
`HOSTED_EMBEDDINGS.md` and `docs/team/MIGRATION_STATUS.md`. Inspect current code
and local changes. Use current main; preserve ingestion work and private overrides.

## Objective and boundaries

Prepare everything Elia and Renato need to run separate local API/worker
processes against the existing services. Application migration 0007 is complete:
do not rerun migrations, rebuild/reset volumes, restart ingestion, republish an
incomplete corpus or change the embedding configuration during its build.
No frontend changes. Work on a fresh `codex/runtime-access-handoff` branch.

1. **Network:** confirm the host's current reachable LAN address, port 22,
   expected SSH host-key fingerprints, individual accounts and allowed source IPs.
   Elia's account is `elia`; his last connection to 192.168.10.230 failed with
   `No route to host`. Inspect Windows firewall/OpenSSH and network isolation;
   identify the cause before changing rules. Preserve key-only access and
   loopback-only PostgreSQL/MinIO. Supply exact tunnel commands for ports
   5432 and 9000. Confirm Renato's own SSH account rather than sharing Elia's.
2. **Application identities:** verify each developer's DB role/principal/namespace
   and active scope grants. Elia's supplied role is `dev_elia`, principal
   `3e5962b0-7aed-4a22-85a3-1f87a6ba31b6`, namespace `fixture_179c1e989fc4`.
   Determine how each can access the published pilot profile and public sources.
   Do not rename this identity or relabel fixtures as pilot data. Use supported,
   narrowly scoped provisioning/grants if needed; preserve existing ownership.
   Keep ordinary app credentials separate from administrative/migration roles.
3. **Checkpoints:** inspect the separate langgraph database and saver tables.
   Confirm whether framework setup has already completed. As its authorized
   owner, provision missing framework tables only if necessary, coordinating
   concurrent use. Supply runtime credentials with the required checkpoint
   read/write permissions, without distributing owner credentials. Explain the
   existing shared-checkpoint isolation model and any unresolved limitation.
   Give each developer a plain `postgresql://...` DSN via their local tunnel.
4. **Artifacts:** supply application S3 endpoint, bucket, region and scoped
   credentials. Verify an existing authorized source object's integrity and a
   small synthetic content-addressed put/read using the actual artifact adapter.
   Record the test key/hash; do not delete shared objects or distribute MinIO
   root/tracing credentials. Keep this separate from ingestion transactions.
5. **Corpus handoff:** report publication status honestly. If ready, provide
   profile UUID/namespace, active published snapshot, build, taxonomy version,
   embedding configuration/hash, coverage/exclusions and one checked example
   query. Verify each developer can resolve the published profile and support
   under their own DB login. If still ingesting, mark these pending and deliver
   access credentials now; do not publish early just to satisfy this task.
   Use the identical full verified HF JSON for builds and queries; see the HF
   handoff. Do not reuse synthetic/local vectors under the hosted config hash.
6. **Verification:** run the read-only readiness checker with the appropriate
   host-local/private settings. Separate configured, reachable, authorized,
   write-tested and published status. Bucket HEAD/table reads alone do not prove
   artifact/checkpoint writes. Report host-side checks separately from actual
   developer-side SSH checks; do not claim their LAN access was tested remotely.

## Deliverables

- Separate ignored private bundles for Elia and Renato, with exact env keys from
  `.env.example`, DSNs, IDs, S3 credentials and any approved provider credentials.
  Use secure file permissions; transfer privately. Never print secrets in logs,
  chat, tracked docs, commands or Git. Do not include the host admin env.
- A non-secret `docs/team/RUNTIME_ACCESS_STATUS.md`: actual environment, checks,
  dates, safe identifiers, pending inputs, network resolution and exact next steps.
  State who owns checkpoint setup and the first live acceptance run.
- Run whitespace/link checks and inspect the staged diff for secrets. Commit and
  push only non-secret handoff/focused fixes on your feature branch; provide its
  commit and private bundle locations. Do not merge unrelated ingestion changes.
