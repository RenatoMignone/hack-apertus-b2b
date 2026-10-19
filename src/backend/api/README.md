# HTTP transport

`app.py:create_app` builds the FastAPI application. `routes.py` exposes `/api/v1`;
`schemas.py` defines validated inputs and frontend projections. OpenAPI is served
at `/openapi.json`. Routes delegate to application use cases: no SQL, model prompts
or workflow stages belong here. Inference runs in the separate durable worker.

`security.py` maps bearer-token digests to server-configured identities and requires
idempotency keys for mutations. `middleware.py` limits bodies and correlates requests;
`errors.py` maps failures without echoing prompts, credentials or provider responses.
List endpoints have bounded pagination; CORS requires explicit origins.

Read the implemented [HTTP handoff](../../../docs/team/runtime/HTTP.md) and
[runtime setup](../../../docs/team/runtime/HANDOFF.md) before extending endpoints.
Keep the separately owned frontend unchanged; propose client updates in that handoff.

## Parallel feature routing

[Module handoffs](../../../docs/plans/MODULE_HANDOFFS.md) lists this module's
focused read path, outputs and acceptance checks. [Active questions](../../../docs/project/OPEN_QUESTIONS.md)
own unresolved inputs. Implement scoped behavior against agreed contracts and
fixtures; coordinate shared schema/config changes. Leave `src/frontend/` untouched.

19 October integration: reason categories include actual facility/service subjects
as `infrastructure`. The current [HTTP contract](../../../docs/plans/FRONTEND_BACKEND_API.md)
and [frontend audit](../../../docs/team/FRONTEND_RUNTIME_AUDIT.md) describe the
authorized clarification/retry/history and reviewed-export client integration.
