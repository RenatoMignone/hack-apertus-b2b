# Working while corpus ingestion continues

18 October 2026. Eric explicitly authorized use of the ingesting database without
waiting for a completed version or production publication. Publication remains an
optional workflow for reviewed releases.

## Capture performance update — 19 October 2026

Source migration `0011_capture_performance` removes a measured quadratic
newest-version sort while preserving exact ready membership and isolation.
[Performance details](CAPTURE_PERFORMANCE.md) and the
[maintainer rollout](../team/CAPTURE_PERFORMANCE_HANDOFF.md) distinguish local
benchmarks from the still-pending shared-host activation.

## Runtime behavior

Set `RUNTIME_CORPUS_MODE=live` in the private API and worker environment.
Keep `RUNTIME_PROFILE_ID` set to the existing domain profile in the application's
namespace and `EMBEDDING_CONFIGURATION` pointing to the complete matching JSON.
The profile supplies its reviewed taxonomy ID; `RUNTIME_LIVE_TAXONOMY_ID` is an
explicit alternative for profiles without that field. No active pointer,
published snapshot, finished ingestion job or complete source-family coverage is
required. Existing environments default to `published` until changed explicitly;
the root example enables `live` for new development environments.

At each new research run, `ops.capture_live_corpus` authenticates the actual
database login, principal, namespace and owned case. It captures readable public
chunks with accepted text, available source artifacts, exact evidence, matching
verified vectors and lexical projections. Text awaiting indexing is skipped;
other users' case evidence is excluded. It chooses the newest ready document
version and records the selected chunks, embeddings, documents and accepted
supported claims/entities. Multiple chunkers are recorded explicitly.

Captures/builds use status `live`, have no publication timestamp and never advance
`corpus.active_snapshots`. They are immutable and owned by that case. Retrieval
requires the corresponding authorized run. New runs see newly ready chunks;
existing runs, retries, clarification resumes, wording edits, review and PDF retain
their evidence. Start a new research run to include later ingestion. Retrieval
records `live_corpus_incomplete_coverage`. Support checks and review/export gates
still apply. Live access does not certify coverage or real model quality.

## Maintainer deployment

Apply migration `0008_live_corpus` with the approved maintainer connection. The
one-time operation needs permission to create the non-login `navigator_runtime`
role. It changes functions, policies and two allowed status values; it does not
rewrite source rows/vectors or active pointers. Its lock wait is limited to three
seconds: a busy migration fails atomically and can be retried after the conflicting
transaction ends. Application startup checks the schema and never migrates.

After migration, configure each existing human login with the supported CLI:

```powershell
$env:PYTHONPATH = 'src'
.venv/Scripts/python.exe -m backend.data.cli --env-file src/backend/deploy/.env runtime-access dev_ren artorg_trial_20261018 --scope 3e2f422f-2c27-44dc-be95-922968ad5926 --profile 2f062878-4650-5a0e-a8b8-2b5cc713f0ef --runtime-env-file .local/runtime-access/renato/.env
```

`runtime-access` uses `ADMIN_DATABASE_URL` or the private host's existing
`POSTGRES_PASSWORD`. It retains the login password and historical principals,
creates/reuses the namespace binding, grants only explicit public reads and
replaces `navigator_app` membership with `navigator_runtime`. It refuses residual
write privileges exceeding that role. The optional private-file patch preserves
existing tokens and all database/checkpoint/storage/model credentials, updating
only identity, profile and live mode. Repeat for Elia's actual login and private
bundle. Do not run this for ingestion/service accounts.

The namespace above is the existing development namespace, without a claim of
completed pilot coverage. Both applications need their own principal IDs in it.
New `principal-create` users receive `navigator_runtime` by default; the maintainer
must explicitly select `--ingestion` to create a shared-corpus writer.

Runtime users can read the shared corpus and write owned cases, flagged web
evidence, drafts, reviews and report artifact metadata. They cannot write shared
profiles/taxonomy, vectors, snapshots, active pointers or grants. Case-only insert
policies also reject public-corpus writes after an accidental writable public
grant. Direct `ops.scope_grants` rows remain hidden by design; verify with
`ops.can_access` and the application path.

Deploy this backend revision and restart both API and worker using the patched
private configuration. Transfer the updated private bundle to its user, preserving
their actual token. Keep working checkpoint/MinIO credentials. Existing tunnel
ports remain PostgreSQL `15432 → 5432` and MinIO `19000 → 9000`; HF/Keera need
outbound HTTPS. No production deployment is a prerequisite for this development mode.

## Workers and acceptance

Each teammate may run API and worker locally. Workers claim jobs only for their
configured principal's cases. Ingestion uses a separate job path. Two workers
bound to the same principal intentionally share that principal's leased queue;
use one worker owner unless sharing is intended. Peer-side placement and tunnel
reachability need confirmation from the person running those processes.

Acceptance: create a case during ingestion; retrieve from its live capture; read a
real artifact and verify SHA-256; persist case-local web evidence; draft with
citations; review every reason; export/download PDF. Verify another user cannot
use the capture or mutate the case. Index another document and confirm only a new
run sees it. Tests are `tests/runtime/test_live_corpus.py` and both modes of
`test_real_lanes_restricted_role_review_and_actual_pdf`. They use disposable
PostgreSQL, synthetic providers and an actual PDF renderer; they are not a model
quality benchmark.
