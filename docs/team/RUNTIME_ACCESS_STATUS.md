# Runtime access status

18 October 2026. Eric authorized work against ongoing ingestion. Publication is
no longer a prerequisite for development cases. See the
[live runtime instructions](../data/LIVE_CORPUS_RUNTIME.md).

`RUNTIME_CORPUS_MODE=live` captures ready readable chunks for each owned case
without a published snapshot or active pointer. Profile, taxonomy, full embedding
configuration and exact evidence stay pinned per run; coverage remains explicitly
incomplete. Later runs can use newly indexed documents.

Verified development identifiers: namespace `artorg_trial_20261018`,
profile `2f062878-4650-5a0e-a8b8-2b5cc713f0ef`, taxonomy
`701b18e8-e80a-5437-a4b0-7ed58ac41021`, public scope
`3e2f422f-2c27-44dc-be95-922968ad5926`, embedding configuration hash
`b9846ffee5c2cc11a371a47be00d1cab898d6ca5b88ba6f08ae4e7e9339e131c`
(768 dimensions). These are development identifiers, not published production
pins. Snapshot/build IDs are generated per live run.

The maintainer `runtime-access` command binds each human DB login to its own
principal in that namespace, grants public reads and optionally patches the private
bundle. Passwords, token digests, checkpoints, MinIO and model credentials remain.
Historical fixture data/identities remain. Ordinary application credentials can
provision and write owned cases. New users receive the narrow runtime role.

## Applied on the shared host

Migration `0008_live_corpus` is applied after a validated private backup
(57,680,099 bytes; archive SHA-256
`f2c9ac92cc0cca15f924a1ba7e53a363f93e1af48edff4217f96d2df7e5e6f95`).
The existing login passwords, checkpoint, MinIO and provider credentials remain.
Both private bundles have the new bindings, profile and `RUNTIME_CORPUS_MODE=live`.

- Renato: DB login `dev_ren`, principal `802d003e-1585-4e74-8262-50703a36887f`.
- Elia: DB login `dev_elia`, principal `af5e3bf3-a43f-42ed-a866-94de438e6747`.
- Both: namespace `artorg_trial_20261018`, read access to the public scope above,
  owned-case writes through `navigator_runtime`; no administrator/shared-corpus
  write privileges. Historical fixture principals/data are retained.

Verification used each person's actual application DB credentials and the
supported `RuntimeStore`, case-scope function and authorized live retrieval joins.
Both created/cancelled an owned case, captured 180 ready versions / 13,705 chunks,
returned 30 hybrid lexical/vector hits for `diabetes`, and read an authorized real source artifact
through MinIO with its recorded hash verified. Public-scope writes were denied.
Verification cases/captures were rolled back; the test never published a snapshot.
The changing corpus grew during this work; ingestion was not stopped or replaced.

`ops.scope_grants` intentionally returns zero rows under its SELECT policy;
`ops.can_access` and corpus/application RLS use the hidden grants successfully.
The previous profile invisibility came from the fixture namespace mismatch.

Checked hybrid source example: `https://www.dcberne.com/en/project_category/applied-clinical-diabetes-research/`.
Checked source artifact SHA-256:
`102692db08cda4f236cbe421960bcc03fd314bd111281dd84a5e0b1c3bc867de`.
Relevance scores/keyword hits do not establish factual support.

The isolated PostgreSQL 17 / pgvector suite passed **51 tests**, including ongoing
ingestion visibility, immutable captures, ownership, broad-role removal, and actual
API → reasoning/retrieval adapters → review → PDF in both live/published modes.
Provider responses/embeddings were synthetic in those tests. One pytest loop-policy
deprecation warning remains. Windows worker/checkpoint commands now use Psycopg's
compatible selector loop.

## Remaining handoff steps

Deploy the backend patch/revision in each user's checkout, apply their private
binding/configuration and restart API + worker. Keep the operator's actual token
digest; do not replace it with an older bundle token. Individual private receipts
are in each bundle. Their peer-side tunnel and process/queue placement remain to be
confirmed; queue claims are restricted by principal, and ingestion has a separate
job path. No services were started/restarted on Renato's device from this session.

After Eric resumed HF, the configured real adapter returned a valid 768-dimensional
query vector. Hybrid retrieval and a real MinIO source/hash check passed under both
ordinary application identities, using the exact stored embedding configuration.
The endpoint/configuration/credentials remain unchanged. A complete real-provider
case-to-PDF run remains an acceptance step after the peer-side API/worker starts;
the complete execution path passed with synthetic providers in isolated tests.
Published release pins remain pending and are optional for live development.

## Renato peer integration — 19 October 2026

Renato fetched `eafed67` and retained Eric's live ingestion, migration and runtime
access implementation. Local SearXNG/Crawl4AI research and the ten-page default
remain integrated. The private deployment binding was patched using the supported
helper, preserving the existing operator token digest and all provider, database,
checkpoint and storage credentials. No shared migration or grant change was run.

Earlier peer checks independently passed checkpoint write/read with rollback,
synthetic S3 integrity and HF query/document encoding (HTTP 200, two 768d unit
vectors). Prior fixture-namespace and publication blockers are historical; live
development uses the new principal and ready-evidence captures described above.
Combined real-provider case-to-PDF acceptance remains separate from engineering tests.

Peer integration verification: **221 backend tests passed** on disposable
PostgreSQL 17/pgvector, including Eric's live/published capture/access cases and
our keyless research adapters. One existing pytest asyncio-policy deprecation
warning remains. Shared-host application identity and a real owned-case capture
passed: **13,705 ready chunks**, correct profile and status `live`. The entire
probe transaction was rolled back; no verification case/capture was retained.

**Earlier startup blocker, now resolved:** the narrow runtime role cannot
read `public.alembic_version` (SQLSTATE 42501). The API's schema check therefore
fails before service composition, despite case/capture access working. An
authorized maintainer must apply this read-only metadata grant on `navigator`:

```sql
GRANT SELECT ON TABLE public.alembic_version TO navigator_runtime;
```

This grants no migration, corpus-write or administrator capability. No shared
grant was changed in this integration. Rerun readiness and restart API/worker
after the owner applies it; do not bypass schema verification.

Latest peer recheck after Eric applied the metadata grant: all network readiness
checks pass, `public.alembic_version` reads `0008_live_corpus`, and the actual
production `Registry.application` bootstrap succeeds with corpus mode `live`.
No credentials, grants or schema were changed by this recheck. Restart existing
API/worker processes to load the updated code and private binding; combined
real-provider case-to-PDF acceptance remains to be run.
