# Data adapters

Migration `0008_live_corpus` supports case-owned captures of ready chunks while
ingestion continues. Runtime users receive `navigator_runtime` for corpus reads
and owned case writes. Publication remains separate; see
[live runtime](../../../docs/data/LIVE_CORPUS_RUNTIME.md).

Implemented adapters for canonical records, scoped evidence, snapshots and search.
Use [data-layer router](../../../docs/data/DATA_LAYER.md) and its focused specs.

- `repositories/`: parameterized PostgreSQL access and transaction boundaries.
- `migrations/`: application-owned navigator schema migrations only.
- `retrieval/`: independent lexical/vector branches, RRF and reranker integration.
- `artifacts/`: controlled original/normalized/pack/export byte storage adapters.

Inputs: typed IDs/queries plus snapshot/scope/access context. Outputs: versioned
records/hits/artifact references. No model-generated SQL. Retrieval uses injected
model ports. See [deployment](../../../docs/data/DEPLOYMENT.md) for services,
CLI, migrations and tests. LangGraph and
Langfuse retain their own migration tools and framework-owned tables.

## U8 persistence implementation

U8 adds interpretations, case web research, supported claim assessments, case manifests, typed packs, draft reasons, editorial selections and PDF export lineage. Current source head is `0012_membership_lookup` (including restricted case-scope/runtime
RLS and independent UI flags/action notes). Use focused case repositories; populated retired workflow tables are owner-only history outside the application schema.

## Parallel feature routing

[Module handoffs](../../../docs/plans/MODULE_HANDOFFS.md) lists this module's
focused read path, outputs and acceptance checks. [Active questions](../../../docs/project/OPEN_QUESTIONS.md)
own unresolved inputs. Implement scoped behavior against agreed contracts and
fixtures; coordinate shared schema/config changes. Leave `src/frontend/` untouched.

## Final schema and corpus/retrieval task

Start with the [ingestion/retrieval handoff](../../../docs/data/INGESTION_RETRIEVAL_HANDOFF.md).
`schema.py` defines final tables; [exact fields](../../../docs/data/SCHEMA_REFERENCE.md)
are generated from it with `PYTHONPATH=src python -m backend.data.schema_docs`
(from repository root). Add `--check` for drift checking. Never import
`migrations/baseline_schema.py` in runtime code: it freezes old migration behavior.
No new code reads `legacy` or recreates removed match/selection/plan/hit/frontier tables.

Live capture performance and the required maintainer-only rollout are documented
in [capture performance](../../../docs/data/CAPTURE_PERFORMANCE.md). Shared 0010
remains compatible; startup never applies the function migration. Snapshot
authorization/context reads must use the small projection rather than fetching
whole membership manifests.

Migration 0012 optimizes snapshot-membership RLS without changing tables or grants. Shared host rollout remains maintainer-owned; see [runtime feedback](../../../docs/team/RUNTIME_FEEDBACK_AND_SEARCH.md).

## Runtime connection safeguards

`engine_for(..., runtime=True)` is used only by API/worker composition. It caps
lock waits at five seconds and idle-in-transaction at sixty seconds, preserving
stricter server policy. Ingestion/migrations retain their own connection settings.
Pure source duplicate checks use one document/alias query and do not take case
write locks; source registration still authorizes/locks its active run.
