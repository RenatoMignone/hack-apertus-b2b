# Case persistence and lineage

The `cases` schema is business authority; LangGraph checkpoints resume execution
and Langfuse traces diagnose it. Neither framework store is the source of facts.

| Record group | Responsibility |
| --- | --- |
| Cases, inputs, dialogue | Owner/namespace, lifecycle, immutable permitted context and chat revisions |
| Runs, interpretations, questions/answers | Pinned research identity/configuration, durable clarification and execution status |
| Web research and manifests | Discovery outcomes, flagged case sources and sealed exact evidence membership |
| Assessments and evidence packs | Exact statement/support decisions, supported claims and frozen pack hash |
| Results, reasons and reason claims | Draft revisions and explicit claim/evidence relationships |
| Selections, reviews and exports | Editorial decisions, exact approval hashes, artifact identity and operation status |
| Action items | Operator follow-up questions/notes; no automatic outbound communication |

`input_revisions` and report revisions are immutable. Focus/identity edits create
new inputs and supersede active old runs. Formatting edits reuse an eligible pack.
Case board status is independent of run state; on-hold/outcome are lifecycle fields.
Historical reports remain readable but cannot silently replace current intent.

Every run pins a snapshot/build, taxonomy/profile, embedding configuration and
applicable model/prompt versions. New local evidence and extracted proposals stay
in owned case scope. Corpus mirrors retain original source/snapshot/evidence IDs
as derivation lineage. Literal slices must satisfy exact body offsets/hashes.

Application writes use expected revisions and transaction locks. Idempotency keys
bind command/body; queue leases bind worker and expiry. Pure reads/lease renewal
avoid the long mutation lock. Stage outputs commit before reuse; diagnostic progress
records do not authorize skipping stages. See [runtime operations](../plans/OPERATIONS_PLAN.md).

All reason cards reviewed plus at least one kept permits an accepted review bound
to exact result and selection hashes. Export rechecks current revision, approval,
claim/support access, renderer/template versions and artifact hashes; download
revalidates eligibility. A later edit or revoked source can invalidate access.
PDF input resolves claim IDs through canonical evidence links, never title guesses.

Optional [case memory](CASE_MEMORY.md) and [manual plans/PPTX](RICH_OUTPUTS.md)
have their own tables and explicit activation. Exact columns and constraints are
in the generated [schema reference](SCHEMA_REFERENCE.md).
