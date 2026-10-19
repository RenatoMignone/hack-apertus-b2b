# Durable execution and runtime operations

The API validates commands and stores owned inputs/runs; the separate worker
claims queue work and drives LangGraph. Run status is queued, running,
waiting_for_input, succeeded, failed, cancelled or superseded. Browser disconnects
stop observation, not execution. Explicit cancellation is a separate command.

## Execution and recovery

`workflows/graph.py` compiles stages. Node services use typed injected ports.
`execution.py` enforces deadlines, cached committed outputs and safe tracing.
PostgreSQL application records are the durable business authority; LangGraph's
separate saver resumes control flow through server-created thread IDs and
`interrupt` / `Command(resume=...)`. Setup of saver tables is explicit.

Queue leases prevent simultaneous active workers; renewal verifies the worker,
run ownership and expiry without taking the long case mutation lock. Pure case
reads do not lock mutations. Source writes and input changes retain their required
locks. Runtime-only connections cap lock waits at five seconds and idle-in-
transaction waits at sixty seconds, preserving stricter server settings.

Idempotency keys bind repeated commands to the same body. Expected revisions and
hashes reject stale edits/reviews/exports. Completed outputs are reused only under
compatible input/evidence/configuration pins. Failed draft recovery can reuse the
pack; changed focus requires new research. Revoked evidence access remains enforced.

## Budgets and failures

Time, output tokens, tool calls and research rounds are separately bounded in
runtime settings and `RunContext`. At most three research rounds are supported.
A further gap round requires novel queries and sufficient time for observed prior
cost plus a 120-second finalization reserve. Otherwise finalize supported partial
work with a limitation. Source preparation has its own capture timeout (default
30 seconds), separate from model research. See [performance](../data/CAPTURE_PERFORMANCE.md).

Web defaults allow ten page attempts per round; discovery plus attempted fetches
share the per-run tool budget (eleven by default). Failed calls consume budget.
Apertus task validation has bounded repair; no silent model fallback or infinite
retries. Infrastructure/provider errors remain distinct from valid no-match output.

The initial research deadline includes queue time after run creation. Once the pack
is frozen, `RUNTIME_DRAFT_DEADLINE_SECONDS` (default 300, range 0–1800) guarantees
a bounded writing/repair/assessment allowance: the later of the research deadline
and pack creation plus allowance, capped at research deadline plus allowance.
Zero keeps the original single deadline. The allowance is pinned at run creation;
the derived deadline is saved atomically with `pack.persist` and carried in the
graph checkpoint context. Retries/restarts reuse that same timestamp rather than
extending it. Research cannot use the additional drafting time. Existing saved
outputs without the new deadline retain their old behavior.

SQL statement timeout and output-token limits are separate. Stage deadline failures
retain the actual failed stage for recovery/UI diagnostics. When a frozen pack
exists for unchanged input, retry the report: the API creates a new run with a fresh
configured deadline and revalidates existing support without repeating discovery,
retrieval or extraction. Changing settings cannot extend an already-persisted run.

## Progress and logs

Timestamped console events include run/case/stage IDs, elapsed milliseconds,
model requests/completions/usage, retrieval branches/candidate counts, web page
attempts and safe failure types. Waiting events show activity about every ten
seconds. Durable `runtime.progress.*` records expose actual concurrent stages in
run polling; these diagnostics do not replace committed outputs/checkpoints.
Successful routine polling is quiet; meaningful progress and slow requests remain
visible. Payloads, tokens, prompts and provider bodies are excluded.

Use [Make](../data/LIVE_SETUP.md) for foreground logs or background processes;
[Langfuse](../data/OBSERVABILITY.md) is optional masked diagnostics. Slow phase
logs identify a bottleneck but cannot alone establish hardware or query cause.
Inspect locks/query plans and provider latency separately. Suspended terminal
processes can hold transactions: stop owned services with Ctrl+C or `make destroy`.

## Acceptance

Disposable tests cover retries, ownership, leases, pause/resume, revocation,
exact review/export and process recovery. Actual target-host restart/resume,
combined real database/web report quality and load acceptance remain separately
recorded in [verification](../judges/VERIFICATION.md). Startup never migrates,
ingests, publishes, installs dependencies or downloads weights.

Independent extraction batches execute at most two concurrent model tasks and are
consumed in deterministic source order. Six-batch and entity/claim caps, per-call
repair and deadline checks remain. A schema-invalid batch cannot supply accepted
claims. Model-expanded optional operator leads are omitted unless literal in the
original input; the complete original request remains the retrieval intent.
