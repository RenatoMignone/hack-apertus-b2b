# Logging and tracing

Console logs provide timestamped safe execution events from API and worker:
HTTP latency/request ID, run/case/stage, model request/usage/validation, retrieval
branches/candidates, web fetch attempts and safe failure types. Waiting events
make long work visible. Run polling exposes actual concurrent activity from
`ops.stage_attempts` diagnostic records; committed stage outputs remain separate.

Optional **self-hosted Langfuse** receives allowlisted identifiers, counts,
versions and timing through `SafeTracer`. Payloads, prompts, passages, company
plans, tokens, credentials and raw provider exceptions are excluded. Automatic
external LangSmith/full model callbacks are not part of runtime tracing.

Configure local Langfuse endpoint/project credentials privately and start the
optional Compose observability profile through [deployment](DEPLOYMENT.md).
Langfuse uses its own PostgreSQL/ClickHouse/Redis/blob storage and migrations,
separate from application evidence and checkpoints. Trace outages or a full
bounded trace queue must not block case execution. Traces are diagnostic, never
a fact store or approval authority.

Follow a run ID across stage/model/search events to distinguish provider latency,
DB queries, source registration and queue waits. Do not infer stalled inference
from generic HTTP polling alone. Review [performance](CAPTURE_PERFORMANCE.md)
for phase measurements and [operations](../plans/OPERATIONS_PLAN.md) for leases.

Retention and access must be set by the deployment owner for application records,
artifacts, checkpoints, logs and traces separately. Backups include sensitive data
and credentials and remain private. Verify restore/revocation behavior on the
actual deployment before making recovery guarantees.
