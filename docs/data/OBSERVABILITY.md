# Langfuse tracing and evaluation specification

**18 October 2026 · Selected tracing platform; not deployed or instrumented.**
LangGraph controls execution; Langfuse observes it. Application evidence and case
history remain in PostgreSQL/artifact storage. Read [data layer](DATA_LAYER.md)
and [case lineage](CASE_STATE_AND_LINEAGE.md) before implementing instrumentation.

## Integration and trace contract

Use the supported Langfuse LangChain/LangGraph callback integration for compatible
model/retriever calls, with explicit observations for custom SQL retrieval,
normalization, validation, publication and rendering. Do not assume callbacks
automatically instrument every custom function or plain HTTP Apertus adapter.
Propagate trace context explicitly and avoid duplicate automatic/manual spans.

| Item | Required values |
| --- | --- |
| Correlation | Trace/run ID, opaque case/session/thread IDs where applicable, input/result revision IDs, ingestion job ID for collection |
| Reproducibility | Profile/taxonomy/schema/snapshot/index build, model role/config hash, prompt/ranking version |
| Span types | Interpretation, expansion, company research, lexical/vector search, fusion, reranking, support validation, pack freeze, drafting, export |
| Retrieval metadata | Filters without private content, query-variant IDs, candidate/accepted counts, evidence/chunk IDs, separate ranks/scores, gap/stop reasons |
| Model observation | Resolved model config ID, duration, status, retries, input/output token counts if reported or reliably counted, permitted masked payload |
| Quality event | Support failures, citation coverage, missing fields, no-match/partial status, reviewer judgment and exact evaluated revision |

One trace per case run; ingestion jobs have separate traces linked through their
job/snapshot IDs. Store the resulting trace correlation in `cases.runs`, but do
not require a live Langfuse lookup to reconstruct or resume an answer.

Model cost is recorded only from a verified price/configuration or measured
resource accounting. Missing usage/pricing is `unknown`; local inference is not
automatically free. Similarity, evidence strength, human feedback and evaluation
scores are different quantities. Langfuse hosting does not create gold labels.

## Payload policy

Default to allowlisted IDs, configuration hashes, stage timings, counts and error
codes. Full prompts, retrieved bodies and outputs are **off by default**; enable
only eligible data under an explicit trace payload/retention configuration. Mask
before the SDK/callback receives or exports data, including custom metadata,
exceptions and model request bodies. Disable automatic payload capture unless
the selected integration's masking behavior has been verified.

Never trace confidential business plans/one-pagers, credentials or forbidden
content. Case messages may contain personal/contextual material even though
permitted for the application; tracing is a separate copy with its own access
and retention boundary. Do not use human names/emails as trace identifiers.
Trace IDs cannot be dereferenced to unauthorized evidence through the UI/API.

## Self-hosted topology

```text
Application / LangGraph → local Langfuse ingestion endpoint
                           ├→ Langfuse web + worker
                           ├→ PostgreSQL: Langfuse transactional database
                           ├→ ClickHouse: traces, observations, scores
                           ├→ Redis/Valkey: queue/cache
                           └→ S3-compatible blob service: ingestion events/assets
```

These are documented platform dependencies, not optional replacements for one
PostgreSQL database. Use separate DB users/buckets from `navigator`, private
service networking and persistent volumes. Choose actual versions/resource
budgets during implementation. Application artifact storage may share the blob
service with isolated buckets, but framework data stays framework-owned.

Air-gapped mode runs all tracing services inside the independent boundary or
explicitly disables tracing; it never falls back to hosted Langfuse. Disable
telemetry/update checks/external evaluators and package assets/dependencies.
Prefer locally versioned prompt/config artifacts so cold start does not require
a trace service or hosted prompt registry. Independent cloud mode must account
for every service's location and egress before making a sovereignty claim.

## Failure behavior and retention

Tracing is asynchronous with bounded delivery time/queue/retries. On outage,
continue the case workflow, expose tracing as degraded, and keep a minimal local
sanitized diagnostic record. Never accumulate unbounded payloads or block model
calls waiting for tracing. Apply a configurable drain deadline at shutdown.

Define coordinated retention/deletion for application, checkpoint and trace
copies. A case deletion/revocation enqueues cleanup in each system and invalidates
lookup/cached access immediately; track retries and residual backups honestly.
Retention durations and backup policies are deployment inputs, not invented
legal guarantees. Observability failure does not erase application audit lineage.

## Acceptance checks and references

Verify parent-child spans, case/run isolation, custom SQL timings, no duplicate
model events, absent-token handling, payload masking, outage behavior, bounded
flush and deletion propagation. Test network-disabled execution against the
local endpoint; traces are not proof of factual correctness.

References inspected during this session on 18 October 2026:
[Langfuse integration](https://langfuse.com/integrations/frameworks/langchain),
[self-hosted components](https://langfuse.com/self-hosting),
[LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence).
Pin actual SDK/framework compatibility when implementing.
