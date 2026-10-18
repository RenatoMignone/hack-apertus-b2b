# Application use cases

Live ingestion development uses `RUNTIME_CORPUS_MODE=live` after migration
`0008_live_corpus`. New runs capture complete authorized chunks in immutable
case-owned live snapshots, without shared publication. See
[live runtime](../../../docs/data/LIVE_CORPUS_RUNTIME.md) for configuration,
narrow user provisioning and acceptance checks.

Own case/input/run operations, authorization, revision checks, reviews, selections
and export requests. Inputs: validated commands plus trusted caller identity.
Outputs: durable resource IDs/views. Use narrow repository/workflow ports;
HTTP response construction belongs to api, workflow ordering to workflows.

Read [case state](../../../docs/data/CASE_STATE_AND_LINEAGE.md) and
[API handoff](../../../docs/plans/FRONTEND_BACKEND_API.md). Persist stage outputs
idempotently; do not hold SQL transactions open during model/network calls.
`service.py` is the async use-case facade; `persistence/` composes existing
repositories in short authorized transactions without changing the schema.
Its small modules separate commands, reads, queue leases, stage outputs,
editorial decisions and export authorization. Mutation idempotency and queue
records use existing outbox/stage-attempt tables; they are not a second fact store.

`bootstrap.py` builds per-identity applications with injected B/C factories from
`adapters.py`. Missing adapters fail as unavailable. Production never imports test
fixtures. `worker.py` executes jobs with heartbeat, run locks and checkpoints;
`cli.py` starts independent API/worker processes and explicit checkpoint setup.

Read the [runtime handoff](../../../docs/team/runtime/HANDOFF.md) for factory
signatures and original restart guarantees; [live setup](../../../docs/data/LIVE_SETUP.md)
owns current startup/deployment prerequisites.
The [integration handoff](../../../docs/team/INTEGRATION.md) supersedes its original
missing-factory list: `factories.py` composes the actual A/B/C adapters. Migration
0006 provisions a case scope through an owner-checked DB function and restricts
private stage/command reads; 0007 persists independent UI flags/action notes.
Runtime integration tests live in `tests/runtime/`; follow the current module
assignment for changes and preserve other contributors' work.

## Parallel feature routing

[Module handoffs](../../../docs/plans/MODULE_HANDOFFS.md) lists this module's
focused read path, outputs and acceptance checks. [Active questions](../../../docs/project/OPEN_QUESTIONS.md)
own unresolved inputs. Implement scoped behavior against agreed contracts and
fixtures; coordinate shared schema/config changes. Leave `src/frontend/` untouched.
