# Own-case similarity v1

19 October 2026. Optional backend feature; shared-host activation is Eric's task.
Core schema 0008 works with `CASE_MEMORY_ENABLED=false`. Maintainer migration
`0009_case_memory` adds immutable `cases.memory_profiles` and owner RLS. After
migration, configure the same pinned encoder used by this installation and set
`CASE_MEMORY_ENABLED=true`. No existing case is automatically indexed.

## Eligibility and API

`POST /api/v1/cases/{case_id}/memory` uses existing bearer authentication and an
Idempotency-Key. Enabling requires `eligible:true`, `synthetic:false`,
`permitted_context_confirmed:true`, `expected_revision` and the exact reviewed
`expected_result_hash`. All cards must already be reviewed, one kept, and an
accepted review must bind that result and selection hash. This is a trusted
operator declaration; it cannot establish source truth or detect fictional text.
Disabling requires `eligible:false` and the current `expected_revision`.

Case detail exposes `memory:{available,eligible}`. Frozen report revisions expose
`similarCases` with case/memory/input/result IDs, index date, score, method,
shared literal needs, current-case needs absent from that profile, and any known
outcome at indexing. A later input revision makes the old profile ineligible;
opt-out hides references on subsequent authorized reads. Previously downloaded
artifacts are not recalled. Reindex explicitly after new review/configuration.

## Comparison and limits

The encoder sees activity, fields, needs, Bern objectives, concepts and constraints
including negation. Company names, outcomes and generated pitches are excluded.
One vector per approved profile/configuration is reused. Queries filter owner,
namespace, current input, enabled status, configuration hash and dimensions before
returning up to five of fifty candidates. Current case is excluded. A 768-dimension
HNSW cosine index supports the current encoder; other dimensions use exact search
until an explicit dimension-specific index migration is provisioned.

`CASE_MEMORY_MIN_SCORE` defaults to 50/100. Clamped cosine similarity is a needs
similarity index, **not a success probability or validated relevance metric**.
Human-reviewed case pairs must calibrate threshold/recall before quality claims.
The method is `symmetric-needs-cosine-v1`; it uses the same query encoding for both
sides. Public source retrieval retains its separate document/query protocol.
Frozen matches are internal context, excluded from the model's public factual
claims. Agency-wide access, automatic learning, outcome prediction and exported
history sections are deferred. Optional history failure leaves a visible gap and
does not prevent a supported core report.

Verification: disposable PostgreSQL migration/schema, reviewed opt-in, vector reuse,
owner rejection, frozen matching, revocation and existing PDF pipeline tests.
No shared migration, indexing or grant was performed.
