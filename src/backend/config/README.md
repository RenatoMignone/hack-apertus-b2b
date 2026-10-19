# Server configuration

`settings.py` and `runtime.py` validate DSNs, identity bindings, factories, profile,
models, budgets and optional features. Root .env.example documents placeholders.
Credentials remain backend-only. Local access needs one existing loopback identity;
shared access retains bearer auth. Domain profile vocabulary is not factual evidence.

Read the [focused specification](../../../docs/data/LIVE_SETUP.md) and [module map](../../../docs/plans/MODULE_HANDOFFS.md).
Coordinate shared DTO/schema/configuration changes with their consumers and run
relevant boundary checks against isolated infrastructure.
