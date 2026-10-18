# Application use cases

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
signatures, restart guarantees, startup commands and remaining cross-lane work.
Add integration tests only in `tests/runtime/`; preserve data/ and B's modules.

## Parallel feature routing

[Module handoffs](../../../docs/plans/MODULE_HANDOFFS.md) lists this module's
focused read path, outputs and acceptance checks. [Active questions](../../../docs/project/OPEN_QUESTIONS.md)
own unresolved inputs. Implement scoped behavior against agreed contracts and
fixtures; coordinate shared schema/config changes. Leave `src/frontend/` untouched.
