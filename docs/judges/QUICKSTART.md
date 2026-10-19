# Run B2B

Run from the repository root unless a block changes directory. Choose a route:
seeded UI without credentials; real local application with fixture providers;
or live research using provisioned services. No route silently falls back.

## 1. Seeded UI demo: no services or credentials

Requires **Node 22.18+**, npm and an initial network connection to install packages.
The browser shows scripted examples. It does not call Apertus, crawl sources or
demonstrate retrieval quality. Sample state is saved in browser localStorage;
use a fresh browser profile for a clean tour.

PowerShell:

```powershell
cd src/frontend
npm ci
$env:VITE_API_MODE = 'mock'
npm run dev -- --host 127.0.0.1
```

Bash (macOS/Linux):

```bash
cd src/frontend
npm ci
VITE_API_MODE=mock npm run dev -- --host 127.0.0.1
```

Open the URL Vite prints, normally `http://127.0.0.1:5173`. Use a seeded board
case and follow the [walkthrough](DEMO.md). Browser PDF/PPTX exports are demo
outputs. Scripted examples are not verified live institutional facts.

Stop with Ctrl+C. Before switching to a backend, set `VITE_API_MODE=http` in
your shell and restart Vite. Process variables override Vite env files;
check an ignored `src/frontend/.env.local` if the mode is unexpected.

## 2. Local synthetic API and worker

This exercises real application, retrieval, review and export code with
synthetic model/embedding responses. Requires **Python 3.12–3.14**, Node 22.18+
and an **isolated local PostgreSQL installation with pgvector available**.
Use Python 3.13 where available. This is an integration demo, not offline Apertus.

Install from root. PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r src/backend/requirements.lock
.\.venv\Scripts\python.exe -m pip install --no-deps -e src/backend
```

Bash:

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r src/backend/requirements.lock
.venv/bin/python -m pip install --no-deps -e src/backend
```

The private test administrator DSN must point to an isolated cluster whose admin
can create databases/roles and enable the vector extension. Create
`navigator_app` once in **that disposable cluster** if absent:

```sql
CREATE ROLE navigator_app NOLOGIN;
```

The harness creates a uniquely named database, migrates it, loads fixture evidence
and starts API plus worker. It removes its database/role and temporary artifacts
on normal shutdown. Do not use the shared database or deployment credentials:
this harness creates and drops databases.

PowerShell (replace the example with your disposable local credentials):

```powershell
$env:NAVIGATOR_TEST_ADMIN_DSN = 'postgresql://TEST_ADMIN:TEST_PASSWORD@127.0.0.1:5432/postgres'
.\.venv\Scripts\python.exe -m backend.tests.runtime.smoke --clarify
```

Bash:

```bash
export NAVIGATOR_TEST_ADMIN_DSN='postgresql://TEST_ADMIN:TEST_PASSWORD@127.0.0.1:5432/postgres'
.venv/bin/python -m backend.tests.runtime.smoke --clarify
```

In a second terminal start the frontend. PowerShell:

```powershell
cd src/frontend
npm ci
$env:VITE_API_MODE = 'http'
npm run dev -- --host 127.0.0.1
```

Bash:

```bash
cd src/frontend
npm ci
VITE_API_MODE=http npm run dev -- --host 127.0.0.1
```

Connect with **`synthetic-browser-smoke`**, the public test-only token.
Create a fictional glucose-sensor case and answer the clarification. Fixture
responses are scripted, not arbitrary research. Source links/quotes are fixtures.
The harness uses in-memory checkpoints; it does not prove PostgreSQL checkpoint
recovery. Optional `--rich-outputs` also exercises manual-plan/PPTX controls.
Keep fictional cases out of comparison memory. Stop terminals with Ctrl+C.

## 3. Provisioned live application

A clean clone excludes DB contents, credentials, weights and tokenizer assets.
Obtain a private judge/operator configuration from the team. Do not replace an
existing developer `.env` with the example. Provider calls may incur costs.

The maintainer supplies:

- Application-role DB access, principal/namespace binding and authorized profile.
- Matching corpus capture/release, taxonomy and verified embedding configuration.
- Separate PostgreSQL checkpoint access with framework tables provisioned.
- S3-compatible source/export storage credentials and access.
- Keera access: `LLM_NAME=apertus-v1-5-70b`,
  `LLM_BASE_URL=https://gateway.keera.ch/api/v1`, private `LLM_API_KEY`.
- For connected HF encoding: endpoint token, pinned local tokenizer and shared
  configuration; install `requirements.hosted.lock` in the backend environment.
  Local encoding instead requires its documented dependencies and model assets.
- A raw operator bearer token for Connect; the backend stores its SHA-256 binding.
  This token differs from provider keys and DB credentials.

Use root [.env.example](../../.env.example) as the settings inventory. Follow
[HF setup](../data/HOSTED_EMBEDDINGS.md),
[inference setup](../data/INFERENCE_CONFIGURATION.md) and
[live provisioning](../data/LIVE_SETUP.md). Older runbook head numbers are dated:
confirm the selected host's revision with the maintainer and
[migration receipts](../team/MIGRATION_STATUS.md). Do not migrate the shared host
during a judge walkthrough.

After the core install above, activate the environment in every backend terminal.
PowerShell: `.\.venv\Scripts\Activate.ps1`; Bash: `source .venv/bin/activate`.
If activation is restricted, use full virtualenv executable paths.
From root:

```text
python -m backend.deploy.check_runtime --env-file .env
python -m backend.deploy.check_runtime --env-file .env --network
navigator-runtime --env-file .env serve --host 127.0.0.1 --port 8000
```

Default readiness inspects local configuration/assets; `--network` adds read-only
DB/checkpoint/storage probes. Neither proves provider quality or every runtime
write permission. Open an authorized tunnel first if required. In another terminal
using the same environment:

```text
navigator-runtime --env-file .env worker
```

Start Vite in `http` mode as above and enter the private operator token. Its dev
proxy sends `/api` to localhost:8000. Reload requires reconnection because tokens
stay in memory; background jobs continue. A hosted frontend needs an explicit API
origin/CORS configuration or reverse proxy; static preview alone is insufficient.

Startup does not migrate, download weights, populate the corpus or configure
checkpoint tables. Optional web uses [SearXNG/Crawl4AI](../data/WEB_RESEARCH.md);
optional reranking needs [assets](../data/RERANKING.md). PPTX/manual plans and
case memory need [activation](../team/OPTIONAL_FEATURE_ACTIVATION.md).
Only use formats the backend advertises.

## Troubleshooting

- **Connect fails:** confirm HTTP mode, API port/proxy and operator token.
  Provider keys are not browser login tokens.
- **Queued indefinitely:** start the worker with matching bindings/environment and
  checkpoint access; inspect persisted failure/stage details.
- **Slow creation/unavailable:** live capture precedes queueing and has a separate
  timeout. Consult [capture measurements](../data/CAPTURE_PERFORMANCE.md).
  Do not disable evidence checks or truncate the corpus to hide latency.
- **Profile/encoder unavailable:** compare grants, pins and local tokenizer assets.
  Do not relabel incompatible vectors.
- **Export blocked:** use the current revision, review every reason, keep one and
  approve the exact selection again after edits.
- **PPTX absent:** the backend has not advertised provisioned support.
- **No matches/web failure:** read gaps and coverage; a provider failure does not
  prove no expertise exists. HTTP failure never enables mocks.

For help, record mode, commit, failed stage and safe error code. Keep tokens,
private env files, full case prompts and source artifacts out of public issues.
