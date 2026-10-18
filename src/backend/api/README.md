# HTTP transport

Own future routes, request validation, response projections, error/status mapping
and request correlation. Delegate to application use cases; no SQL, model prompts
or workflow stages inside route handlers. No endpoints are implemented yet.

Follow [HTTP handoff](../../../docs/plans/FRONTEND_BACKEND_API.md). Inputs are
versioned requests and trusted caller context; outputs are authorized views or
accepted durable operation IDs. Authentication transport/framework, OpenAPI
schemas, size limits and pagination still need implementation-time agreement.
