# Optional runtime container wiring

API and durable worker also run with the Python commands in the
[runtime handoff](../../../docs/team/runtime/HANDOFF.md). The existing data/
LangGraph/Langfuse stack stays independently owned and is not started by runtime.

`Dockerfile.runtime` copies only backend source/dependencies, installs the locked
requirements, and runs as UID 10001. Supply an operator-verified digest-pinned
`PYTHON_RUNTIME_IMAGE`; there is no guessed default digest. `runtime.compose.yaml`
starts API/worker on a pre-existing private navigator network, API published only
on localhost. Operator configuration must use Docker-internal DB/storage/model
addresses, not the host SSH tunnel addresses in the developer env example.

```bash
docker compose -f src/backend/deploy/runtime.compose.yaml config
# On the authorized target, after prerequisites and private settings are ready:
docker compose -f src/backend/deploy/runtime.compose.yaml up --build -d
```

Set `RUNTIME_ENV_FILE` to an ignored private env file, `NAVIGATOR_NETWORK` if the
base stack uses another network, `RUNTIME_PORT` for the host port. API/worker share
a runtime artifact volume when using filesystem storage; use the existing S3
adapter/config when sharing artifacts with ingestion. Do not auto-migrate the
team DB or download model assets at image startup. Create framework checkpoints
explicitly with the checkpoint owner before starting the worker.

For isolated local runs use a unique Compose project name and remove only that
project's resources. Do not run broad prune/stop commands or remove shared data
volumes. Container configuration is supplied for integration; no image was built,
registered or deployed in this task. Offline deployment additionally requires
local model/adapters/assets and host-enforced network isolation.
