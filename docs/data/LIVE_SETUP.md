# First live run: your Mac and Eric's host

19 October 2026 · Runbook for the integrated application. No commands in this
file have been executed on the shared host by this documentation audit.
[Current status](../project/STATUS.md) separates implementation from rollout.

**You can operate the backend from your Mac.** PostgreSQL access alone is
insufficient: configure [hosted HF embeddings](HOSTED_EMBEDDINGS.md) with a pinned
local tokenizer (no model weights), or choose local model assets explicitly.
The worker also needs the separate LangGraph database. A host-run backend is
another option, requiring an agreed application entry point/tunnel. Pick one
worker placement for the first run. Eric's [migration](../team/MIGRATION_STATUS.md)
is complete; do not repeat it. Sections 1–2 remain recovery/inspection guidance.

## 1. Confirm what actually exists (read-only)

Eric reports shared head **0008_live_corpus** and verified per-user runtime
bindings. [Live corpus mode](LIVE_CORPUS_RUNTIME.md) starts cases while ingestion
continues; no completed publication is required. Ready chunks and matching vectors
are captured immutably for each run. Published mode remains available for releases.

With your existing developer `.env`, activated backend environment and SSH tunnel,
this optional check reads only database identity/revision, without printing passwords:

```bash
python - <<'PY'
from sqlalchemy import text
from backend.data.cli import load_environment
from backend.config.settings import Settings
from backend.data.database import engine_for
load_environment('.env')
engine = engine_for(Settings.from_env().database_url)
try:
    with engine.begin() as connection:
        connection.execute(text('SET TRANSACTION READ ONLY'))
        print('Database / role:', connection.execute(
            text('SELECT current_database(), current_user')).one())
        print('Migration:', connection.execute(
            text('SELECT version_num FROM alembic_version')).scalars().all())
except Exception as error:
    raise SystemExit('Read-only check failed: ' + type(error).__name__)
finally:
    engine.dispose()
PY
```

Existing exported environment variables override env-file entries. Use a fresh
terminal with the intended environment; do not mix test, migrator and app DSNs.
This check does not verify corpus coverage, model availability or object access.

## 2. Upgrade only if behind (Eric or his delegated operator)

The required revision is **`0008_live_corpus`**, already applied by Eric. Do not
repeat it from a developer checkout. If another host is behind, its authorized
maintainer must follow [live migration instructions](LIVE_CORPUS_RUNTIME.md#maintainer-deployment)
and [backup/recovery](DEPLOYMENT.md#backup-and-restore). Application startup never
migrates. Keep migration-owner credentials out of API/worker environments.

## 3. Get the corpus/model handoff

The corpus owner must supply these real, mutually compatible items:

| Item | Runtime use |
| --- | --- |
| DB principal ID, namespace, application-role DSN and public scope grants | Server-side identity/access; shared profile must be visible in this namespace |
| Profile UUID, reviewed taxonomy and matching embedding config | `RUNTIME_PROFILE_ID` selects the profile; `RUNTIME_CORPUS_MODE=live` creates a ready-evidence capture, while `published` uses the active release |
| Verified shared `ModelConfiguration` JSON and selected encoder setup | HF endpoint/token + pinned tokenizer, or local assets; model, tokenizer, templates and dimension must match the index |
| Artifact endpoint/bucket and backend application credentials | Reads source artifacts and writes reports; SSH forwarding does not grant object permissions |
| Checkpoint database access and agreed worker location | `LANGGRAPH_DATABASE_URL`; use a plain psycopg `postgresql://...` DSN for the saver |
| Coverage/failures and reviewed example query | Establish that sources/claims are usable, not merely that tables contain rows |

In live mode, ingestion may continue and coverage stays explicitly incomplete.
A new run sees newly indexed data; existing runs and formatting edits retain their
capture. Do not publish synthetic fixtures into the real namespace.

## 4. Configure and run the backend on your Mac

1. Reinstall the merged core lock and editable backend using the [backend README](../../src/backend/README.md),
   even if the older lane environment already passed tests. Missing
   `navigator-runtime` or `langgraph.types` indicates an outdated environment.
   For hosted embeddings install `src/backend/requirements.hosted.lock` and provision
   the pinned tokenizer; see [HF setup](HOSTED_EMBEDDINGS.md). Local mode instead
   needs optional `local-models` dependencies and full assets. Verify target-platform
   wheels before deployment; startup downloads neither tokenizer nor weights.
2. Keep your tunnel open, replacing the username with the account Eric supplied:

   ```text
   ssh -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -L 15432:127.0.0.1:5432 -L 19000:127.0.0.1:9000 YOUR_SSH_USER@192.168.10.230
   ```

   This is the previously supplied LAN host address; confirm it if DHCP/network
   changed. The reported SSH policy permits destination ports 5432 and 9000.
   Both navigator and langgraph databases use PostgreSQL port 5432, but each needs
   its own credentials. A tunnel to a host-run API on port 8000 requires Eric to
   explicitly extend that policy; do not assume it is allowed.
3. Copy root [.env.example](../../.env.example) to a private ignored file without
   replacing existing secrets. Set application DB/S3 credentials, permitted
   checkpoint DSN, profile UUID, verified embedding JSON and HF/tokenizer or local assets, current private
   Keera key and the integrated factories/PDF versions/logo path.
4. Generate a private random operator token; put only its SHA-256 digest in
   `RUNTIME_AUTH_BINDINGS`, with the real principal ID/namespace. Keep the raw
   token for the browser connection screen. API and worker use the same bindings;
   the digest authenticates the operator, not the LLM provider. See
   [runtime settings](../../src/backend/config/README.md).
5. The checkpoint owner explicitly runs this once where approved:

   ```text
   navigator-runtime --env-file .env checkpoints-setup
   ```

   Framework schema setup is separate from application migrations; do not share
   framework owner credentials casually just to make a local experiment start.
6. From repo root in separate terminals using the same private env:

   ```text
   navigator-runtime --env-file .env serve --host 127.0.0.1 --port 8000
   navigator-runtime --env-file .env worker
   ```

For private keyless SearXNG search plus isolated Crawl4AI, follow [web setup](WEB_RESEARCH.md)
on the worker host. No search API key or browser is needed with provider `searxng`;
the sidecar and crawler environment are separate from the core runtime. Authorized
profile/corpus requirements remain; live mode does not require publication. Start without optional web/reranker if not provisioned; web remains disabled when
`RUNTIME_WEB_FACTORY` is empty. Their absence must be visible, not replaced by
invented evidence. Connected Keera requires `DEPLOYMENT_MODE=connected`.

## 5. Connect and verify

Before starting processes, run the repeatable readiness check from repo root:

```bash
.venv/bin/python -m backend.deploy.check_runtime --env-file .env
# With the SSH tunnel open and credentials supplied:
.venv/bin/python -m backend.deploy.check_runtime --env-file .env --network
```

The default checks local configuration/tokenizer assets only; it makes no model,
DB or S3 calls. `--network` adds read-only application schema/identity, checkpoint
table reads and S3 bucket HEAD. It never migrates, runs jobs or writes artifacts.
Missing/failed checks return exit code 1 and omit exception messages/secrets.
These checks do not prove profile publication/scope access, checkpoint write
permissions, object read/write permissions or model quality. Verify those at
their acceptance steps. Existing shell variables override env-file values.

### Historical Mac preparation checkpoint — 18 October 2026

The Mac repository `.venv` was refreshed from `requirements.hosted.lock` and the
editable backend. Dependency consistency and CLI imports passed; **117 tests
passed, 58 integration tests deselected**. Local HF tokenizer/config validation
passed without contacting providers. Private operator token/hash binding and
developer DSN were prepared in ignored local files; no secret is recorded here.

At that earlier checkpoint the bundle used a fixture namespace. The new live
binding supersedes it; preserve historical fixture identities rather than
relabeling them. See the latest runtime access status for current peer checks.
API/worker on this Mac is the proposed first placement; no worker was started.

SSH to the user-confirmed account `elia@192.168.10.230` returned **No route to host**.
No peer-side database/storage check could complete from this Mac. Eric subsequently
reported protected per-developer bundles and successful host-local saver/S3 writes;
see [runtime access](../team/RUNTIME_ACCESS_STATUS.md). Transfer those bundles
privately, preserving each identity/token, before filling the remaining settings.
The original Mac preparation still needs these inputs:

- Reachable SSH host/network and verified host key; use the existing Bern key.
- Checkpoint DSN and confirmation that framework tables are provisioned; runtime
  read/write permissions must be agreed separately from setup ownership.
- MinIO application credentials for the `navigator` bucket.
- Accessible profile/taxonomy and compatible embedding configuration, with
  matching source access. Live captures do not need reviewed-release publication.

Eric's application migration is already complete. This preparation did not
change his host, ingest data, publish a snapshot or initialize checkpoint tables.

### Live acceptance

Start the [frontend](../../src/frontend/README.md) with Node 22.18+ and its default
HTTP mode, then enter your operator token. The Vite dev proxy targets localhost:8000.
Run one permitted public test case: verify actual progress or clarification,
source quotations and caveats, review every reason, keep at least one and download
PDF. Confirm an input edit creates a new researched revision and stale exports
are rejected. Record environment, corpus/model pins, outcome and failures.

A capabilities response reports configuration, not a full provider health check.
A synthetic browser smoke already passed; this live acceptance still needs real
assets/corpus/providers. Later evaluate research quality and target-host restart.
No shared tests, migration or model download happen automatically at startup.

### Current integration checkpoint — 19 October 2026

The private live binding is installed, existing credentials/operator token are
preserved, and an actual owned-case capture of 13,705 ready chunks passed in a
transaction that was rolled back. The combined backend passed 221 isolated tests.
Eric applied the missing SELECT grant on `public.alembic_version`. All network
readiness checks and actual production application bootstrap now pass; see
[runtime access status](../team/RUNTIME_ACCESS_STATUS.md). No shared schema or
grants were changed from this checkout. Restart both API and worker, then perform
full real-provider case-to-PDF acceptance.
