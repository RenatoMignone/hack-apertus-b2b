# Optional runtime container wiring

For Mac preparation, run `python -m backend.deploy.check_runtime --env-file .env`
from repo root in the backend virtualenv. It checks configuration and local assets
without network access; `--network` adds read-only DB/checkpoint/S3 probes after
the SSH tunnel is open. It does not migrate, start a worker, write objects or call
models. Missing checks return exit code 1; exception details/secrets are omitted.
See the [live setup checkpoint](../../../docs/data/LIVE_SETUP.md#5-connect-and-verify)
for remaining access inputs and the limits of these probes.

API and durable worker also run with the Python commands in the
[runtime handoff](../../../docs/team/runtime/HANDOFF.md). The existing data/
LangGraph/Langfuse stack stays independently owned and is not started by runtime.

`Dockerfile.runtime` copies backend source/dependencies and the supplied unchanged
English logo, injects its path, installs the locked
requirements, and runs as UID 10001. Supply an operator-verified digest-pinned
`PYTHON_RUNTIME_IMAGE`; there is no guessed default digest. `runtime.compose.yaml`
starts API/worker on a pre-existing private navigator network, API published only
on localhost. Operator configuration must use Docker-internal DB/storage/model
addresses, not the host SSH tunnel addresses in the developer env example.
Compose sets `RUNTIME_PDF_LOGO_PATH=/app/assets/Logo_SF_BE_EN.png` explicitly so a
repo-relative path in the env file cannot override it. For direct Docker commands,
use that container path too. Install/package optional local-model/web extras for the actual target
platform and mount verified configurations/assets explicitly. The core Dockerfile
does not include model weights or certify an operational offline deployment.

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

For Windows-mounted shell entrypoints, root `.gitattributes` now enforces LF.
Existing host checkouts may need a one-time rewrite; [host instructions](../../../docs/data/WINDOWS_SHELL_FIX.md)
explain when the temporary migration override can be retired. Hosted embeddings
need the supplemental lock plus tokenizer/config mounts; they remain connected-only.
