# HTTP transport

Validates requests, invokes authorized application use cases and projects safe
responses. `schemas.py` and generated `/openapi.json` define exact transport fields.
Routes contain no SQL or model prompts. Shared bearer identity, loopback local
mode, idempotency and expected revision/hash checks retain server authority.

Read the [focused specification](../../../docs/plans/FRONTEND_BACKEND_API.md) and [module map](../../../docs/plans/MODULE_HANDOFFS.md).
Coordinate shared DTO/schema/configuration changes with their consumers and run
relevant boundary checks against isolated infrastructure.
