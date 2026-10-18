# HTTP transport

Own future routes, request validation, response projections, error/status mapping
and request correlation. Delegate to application use cases; no SQL, model prompts
or workflow stages inside route handlers. No endpoints are implemented yet.

Follow [HTTP handoff](../../../docs/plans/FRONTEND_BACKEND_API.md). Inputs are
versioned requests and trusted caller context; outputs are authorized views or
accepted durable operation IDs. Authentication transport/framework, OpenAPI
schemas, size limits and pagination still need implementation-time agreement.

## Parallel feature routing

[Module handoffs](../../../docs/plans/MODULE_HANDOFFS.md) lists this module's
focused read path, outputs and acceptance checks. [Active questions](../../../docs/project/OPEN_QUESTIONS.md)
own unresolved inputs. Implement scoped behavior against agreed contracts and
fixtures; coordinate shared schema/config changes. Leave `src/frontend/` untouched.
