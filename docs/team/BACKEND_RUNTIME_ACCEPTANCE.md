# Backend runtime acceptance — Renato

**Current status:** this is a historical acceptance record. See the [19 October
checklist](RUNTIME_CHECKLIST.md) for 224 isolated tests, working live access, keyless
web research and the remaining real-provider case-to-PDF acceptance.

18 October 2026. **Partial acceptance; live operation remains blocked.** Tested
integrated main `091b87fa90be23a7dd84c7e6e9692febb3787537` on branch
`codex/backend-runtime-acceptance`. This report records this run, not historical
Mac/lane results. No shared database writes, migrations, ingestion, checkpoint
setup or shared worker deployment occurred.

## Checkout and environment

- Fresh worktree `navigator-backend-runtime-acceptance`; the original checkout's
  user-edited deployment example was preserved byte for byte.
- Shell GitHub DNS failed. The connected GitHub API supplied the three upstream
  commits and missing objects; every imported Git object matched its SHA before
  creating the worktree at the exact remote revision. Main was checked again and
  still pointed to the revision above.
- Linux x86_64, CPython **3.13.15**. A new ignored `.venv` contains the editable
  backend and all **94 core-lock packages**, installed from an isolated copy of
  the existing package cache. `pip check` passed. Build tools are pip 26.2.1 and
  setuptools 84.0.0.
- Relevant installed versions: FastAPI 0.146.0, LangGraph 1.2.16, LangChain 1.4.6,
  psycopg 3.3.6, SQLAlchemy 2.1.5, ReportLab 5.0.1, pytest 9.1.1.
- The **hosted lock did not install completely**: PyPI DNS is unavailable, and
  filelock 4.2.2, fsspec 2026.9.0, hf-xet 1.7.0, huggingface-hub 2.2.0 and
  tokenizers 0.23.3 were not cached. No substitute tokenizer/version was selected.
- Docker daemon access is denied in this execution sandbox. Only PostgreSQL client
  binaries are installed locally; no disposable pgvector server could be started.
  Therefore no local PostgreSQL/pgvector server version is claimed for this run.

## Private configuration

The user's deployment example was copied to ignored `src/backend/deploy/.env`,
with mode 0600, in both checkouts. The acceptance copy was supplemented with
integrated runtime defaults. Original copied infrastructure values remain private
and separate; they were not selected as application credentials.

- Application: user-confirmed `dev_ren`, database `navigator`, SSH-forwarded
  `127.0.0.1:15432`. The provided password is stored only privately. The copied
  `navigator_migrator` DSN is retained separately, never used for the app/tests.
- Storage: forwarded `127.0.0.1:19000`; existing private S3 values preserved.
  Checkpoint DSN uses the PostgreSQL tunnel; no setup/write delegation was assumed.
- Connected Apertus **`apertus-v1-5-70b`**, existing Keera key and HF token retained.
  No stale exported overrides matched the copied configuration keys.
- A new private browser token and SHA-256 digest were generated under ignored
  `.local/runtime-acceptance/`, without printing either. `RUNTIME_AUTH_BINDINGS`
  remains `[]`: actual principal/namespace must come from authorized DB reads.
  No Elia token, fabricated identity or fixture profile was substituted.
- Local embedding JSON matches the configuration verified in
  [the HF handoff](../data/HOSTED_EMBEDDINGS.md), hash
  `b9846ffee5c2cc11a371a47be00d1cab898d6ca5b88ba6f08ae4e7e9339e131c`.
  This reuses the documented verification; it is not new server attestation.
  The pinned tokenizer is absent, and was not downloaded by runtime or replaced.
- Published profile remains unset pending real pins/access. Optional web/reranker
  remain disabled. Logo path resolves to the supplied unchanged challenge asset.

## Actual checks and results

| Check | This run | Limit |
| --- | --- | --- |
| Core install, editable backend, `pip check`, CLI help, compileall | Passed | Hosted supplemental lock is incomplete |
| Local readiness CLI | Correctly exits 1 | Operator binding, profile and pinned tokenizer missing; checkpoint/key/S3 configuration and logo checks pass |
| Network readiness CLI / direct read-only app probe | Blocked | Sandbox rejects tunnel connections; checkpoint/S3 probes fail safely |
| Non-integration backend tests before the fixes | **117 passed, 58 deselected**, 1.33 s | Diagnostic asyncio polling shim described below |
| Final complete test selection, test DSN deliberately unset | **119 passed, 58 skipped**, 1.11 s | All PostgreSQL tests skipped; this is not a passed integration suite |
| In-process HTTP via ASGITransport | Passed | Health, OpenAPI (23 paths), unauthenticated cases → 401; no DB/model |
| PDF unit tests | Passed within the 119 | Synthetic records; kept-only rendering/citations and layout regressions, not a complete case |
| Disposable application smoke and PostgreSQL saver/restart | **Not run** | No permitted isolated pgvector server; shared server was never substituted |
| Existing frontend transport tests, direct Node invocation | **8 passed**, 38 ms test time | Synthetic fetch transport, no browser/server |
| Frontend build with copied existing dependencies | Passed, Vite build 1.35 s | Diagnostic only: installed dependencies differ from the current lock |
| Clean locked frontend install | Blocked (`ENOTCACHED`) | Registry inaccessible; Vite 8.3.4 not cached |
| Browser HTTP-to-PDF / real published corpus | **Not run** | Requires live access, complete assets/pins and agreed worker ownership |

### Sandbox-specific test limitation

The ordinary backend invocation stalled on the first PDF test. A minimal
`asyncio.run(asyncio.to_thread(lambda: ...))` also timed out independently of the
application. The worker thread had completed; the loop remained in `select`.
This is consistent with the sandbox denying socket-based cross-thread wakeups.

For independent tests only, an **ignored local `sitecustomize.py`** scheduled a
20 ms event-loop timer. The same minimal reproduction then completed, followed
by the results above. No production code, service response, evidence validator
or assertion was changed. These are diagnostic test passes under that shim;
rerun the ordinary commands on an unrestricted operator host before acceptance.
The shim and private environment are not committed.

The existing frontend dependency copy used Vite 5.4.11, React Router DOM 6.28.0
and plugin-react 4.3.4, all outside the new declared ranges. Its successful build
is not lockfile/deployment verification. `npm test` reported the test file as one
passing item in this sandbox; direct invocation exposed all eight actual subtests.
Frontend source, types, package manifest and lock were not modified.

## Provider and evidence observations

- A bounded actual Keera adapter attempt used fictional permitted glucose-sensor
  text, 70B, one transport attempt, five-second timeout and 128 output tokens.
  It returned safe `ServiceUnavailable` after **0.390 s**. With network denied,
  no authenticated success, token usage, structured repair, quota or served
  weight revision was observed. Mocked task/repair/error tests passed separately.
- The actual HF loader failed safely before inference in **0.001 s**, because
  pinned tokenizer assets are missing. JSON/config hash matches were verified;
  live query/document vectors, token parity and endpoint latency were not.
  Mocked formatting, usage, dimension, normalization and failure tests passed.
- User confirmed an SSH tunnel to Eric's host. Socket probes from **this session**
  to both forwarded ports returned `PermissionError` (EPERM); the application
  read-only SQL attempt returned `OperationalError`. This does not establish
  a bad password, broken tunnel or unavailable service outside this sandbox.
- [Eric's migration record](MIGRATION_STATUS.md) reports 0007, PostgreSQL 17.10 /
  pgvector 0.8.2 and a synthetic active snapshot. Those are owner-reported facts,
  not new measurements here. No newer runtime-access/publication handoff was
  present in the inspected main revision. The supplied personal DSN alone does
  not supply a reviewed profile/snapshot/build/taxonomy bundle.
- No real case or result IDs/hashes, pipeline stage timings, audited source
  passages, capability-fit judgments or measured no-match quality are available.
  No Recall@10, real extraction accuracy, durable recovery or deployment claim.

## Focused fix

`backend.tests.run` previously loaded deployment `.env` and constructed an
administrator DSN from `POSTGRES_PASSWORD`. It could silently replace an intended
isolated test target with deployment credentials. It now **requires an explicit
`NAVIGATOR_TEST_ADMIN_DSN`**, never reads deployment secrets or overwrites the
selected target. The browser smoke uses the same guard instead of an unhelpful
missing-key traceback. Two regressions verify that absent test configuration
cannot launch tests/smoke even when deployment credentials exist. The operator
must still ensure any explicitly supplied DSN points to a disposable server.

## Commands and remaining handoff

From this worktree, activate `.venv`. Normal target-host acceptance commands:

```bash
python -m pip install -r src/backend/requirements.hosted.lock
python -m pip install --no-deps -e src/backend
python -m pip check
python -m pytest src/backend/tests -m 'not integration' -q
python -m backend.deploy.check_runtime --env-file src/backend/deploy/.env
python -m backend.deploy.check_runtime --env-file src/backend/deploy/.env --network
# Only after provisioning an isolated local pgvector cluster and navigator_app:
NAVIGATOR_TEST_ADMIN_DSN='<isolated disposable administrator DSN>' python -m pytest src/backend/tests -q
NAVIGATOR_TEST_ADMIN_DSN='<same isolated DSN>' python -m backend.tests.runtime.smoke
node --experimental-strip-types src/frontend/tests/httpApi.test.ts
npm --prefix src/frontend ci
npm --prefix src/frontend test
npm --prefix src/frontend run build
```

Commands actually used for the diagnostic backend totals:

```bash
PYTHONPATH=.local/runtime-acceptance/asyncio-polling:src python -m pytest src/backend/tests -m 'not integration' -q
PYTHONPATH=.local/runtime-acceptance/asyncio-polling:src env -u NAVIGATOR_TEST_ADMIN_DSN python -m pytest src/backend/tests -q
```

Next operator steps:

1. Use an environment allowed to reach package registries, the SSH forwards and
   providers; install the exact hosted/frontend locks and pinned tokenizer through
   [documented provisioning](../data/HOSTED_EMBEDDINGS.md).
2. Read Ren's actual principal/namespace and confirm public scope grants. Bind
   the privately generated token hash; never invent IDs or reuse Elia's binding.
3. Obtain Eric's reviewed published profile/snapshot/build/taxonomy/config pins,
   coverage/failures and example query. Verify schema, nonprivileged role,
   source-object reads and encoder config compatibility read-only.
4. Agree checkpoint/artifact test writes and worker/queue ownership with Eric and
   Elia. Verify permissions with bounded synthetic writes; no checkpoint setup
   without delegation. Never run destructive pytest on the shared server.
5. Complete isolated full suite/smoke and PostgreSQL restart checks, then bounded
   live providers and a public real-corpus case through review/PDF. Record stage
   timings, exact evidence and IDs/hashes; test only your own run's interruption.
6. Mohamed: frontend sources/interfaces were unchanged; no new HTTP contract
   request. Repeat browser acceptance after the backend is ready. Remaining
   adaptive research/reranking/lineage work was not started by this task.

## Publication status

Remote main reads succeeded through the connected GitHub API. Publishing through
that connector was rejected with `MCP tool call requires approval, but approval
policy is never`; shell GitHub DNS is also unavailable. The focused changes are
committed locally for a normal push from an authorized network-capable terminal.
No remote branch, main merge or shared history rewrite was performed here.

### Subsequent integration note — 18 October 2026

The user subsequently pushed this commit to `origin/codex/backend-runtime-acceptance`;
it was fetched and integrated. The original publication block above describes the
sandbox session at the time. Eric’s later [host-local access report](RUNTIME_ACCESS_STATUS.md)
provides private bundle availability but does not prove peer-side connectivity.
A later unrestricted local run passed 177 backend tests including database tests;
see [integration](INTEGRATION.md). This does not retroactively change this report’s
partial acceptance or establish a published pilot corpus.
