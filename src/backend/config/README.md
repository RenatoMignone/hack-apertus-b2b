# Server settings and domain profiles

`settings.py` currently reads database/checkpoint/artifact settings. Root
[.env.example](../../../.env.example) and the backend example contain public Keera
settings and a team-key placeholder. LLM and proposed `EMBEDDING_*`/deployment keys
are handoff configuration, not yet consumed by `Settings` or a live adapter.

Read [provider settings](../../../docs/data/INFERENCE_CONFIGURATION.md),
[model/build configuration](../../../docs/data/BUILD_AND_OPERATIONS.md) and
[profiles](../../../docs/plans/ARCHITECTURE.md#data-independent-core-and-configurable-domain-profile).
Pin model/taxonomy/profile versions; do not copy source registries or secrets
into graph nodes. The config integrator coordinates new parsed keys and bootstrap
wiring; each feature documents what it requires. All credentials stay backend-only.
