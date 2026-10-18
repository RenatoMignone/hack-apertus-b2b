# Renato — prepare and verify the integrated backend end to end

Read `AGENTS.md`, `docs/plans/MODULE_HANDOFFS.md`, the execution graph,
processing boundaries and open questions. Then read `docs/data/LIVE_SETUP.md`,
`HOSTED_EMBEDDINGS.md`, backend/config/workflow READMEs and Eric's runtime access
handoff when available. Inspect current main and local changes; preserve them.
Create a fresh `codex/backend-runtime-acceptance` branch.

## Scope

Set up your own environment and test the existing pipeline. Make focused fixes
for observed backend failures; do not rewrite the architecture or independently
start adaptive research, reranking or lineage features. Leave `src/frontend/`
unchanged. Coordinate shared contracts/config/migrations with Elia; do not
allocate migrations or modify Eric's ingestion/shared corpus. Continue independent
tests while access or published data is missing; label blocked checks honestly.

## Execute in order

1. Create/refresh a Python 3.12–3.14 virtualenv. Install
   `src/backend/requirements.hosted.lock`, then the editable backend with
   `--no-deps`. Run `pip check`, CLI/import checks and:
   `python -m pytest src/backend/tests -m "not integration" -q`.
2. Prepare your ignored private environment from the example and Eric's bundle.
   Use your own DB principal/namespace and a new browser bearer token; store only
   its SHA-256 digest in `RUNTIME_AUTH_BINDINGS`. Never reuse Elia's token/identity.
   Preserve existing secrets and check for stale exported env overrides. Configure
   connected Apertus 70B, the verified HF JSON and pinned local tokenizer. Download
   tokenizer assets only through the documented provisioning process; no runtime
   download or hidden model/fixture fallback. Missing credentials remain missing.
3. Run `python -m backend.deploy.check_runtime --env-file .env`, then, with your
   SSH tunnel open, add `--network`. Validate DB role/schema, profile/snapshot and
   config-hash compatibility, source access, artifact read/write and checkpoint
   read/write. Coordinate synthetic writes with the owner; never use a migrator
   DSN for the app. Do not run checkpoint setup without its owner's delegation.
4. **Full integration suite:** provision an isolated local disposable PostgreSQL
   cluster with pgvector and required roles, following the test fixtures/README.
   Set `NAVIGATOR_TEST_ADMIN_DSN` only to that isolated server and run
   `python -m pytest src/backend/tests -q`. These tests create/drop databases and
   roles: never point them at Eric's shared server. Use a dedicated Compose
   project/volume if needed; no broad prune/stop commands. Report actual versions,
   counts/skips and failures; do not reuse historical test totals as your result.
5. **Synthetic application smoke:** use the documented
   `python -m backend.tests.runtime.smoke` with that isolated test-admin DSN.
   Exercise real HTTP intake, clarification, progress, cited draft, all-card
   review/one-kept gate and actual PDF download. Check wording-only pack reuse,
   changed-focus research, stale approvals, duplicate commands, cancellation and
   cross-owner isolation. Use existing tests where they cover these behaviors;
   add focused regression tests for genuine fixes. The smoke uses memory
   checkpoints, so test PostgreSQL saver/restart recovery separately with the
   isolated runtime tests; do not claim durable recovery from this smoke alone.
6. **Live providers:** make small bounded calls through the actual adapters using
   synthetic/permitted public text. Verify HF query/document config and token
   accounting, Keera structured tasks/repair and safe failures. Do not send
   confidential plans/one-pagers. Record latency, observed usage and failures;
   leave unobserved quota/weight provenance facts unknown.
7. **Real published corpus:** once Eric delivers valid pins/access, start your
   local API and an agreed worker. Coordinate queue ownership with Elia: workers
   sharing a principal/namespace may consume each other's jobs. Run a public test
   case through interpretation → retrieval → extraction → support assessment →
   frozen pack → draft → separate draft assessment → review → PDF. Audit exact
   source passages, need/capability fit, direct/adjacent wording, gaps and no-match.
   Capture IDs/hashes and measured timings without secrets/full private prompts.
   Verify checkpoint resume on controlled interruption of your own run only.
8. **Frontend consumer:** run existing frontend transport tests and build using
   its README; browser smoke in HTTP mode if available. Do not change frontend
   source, types or locks. Send any required interface change as a written
   handoff for Mohamed; report browser checks as blocked if tools are unavailable.

Optional web/reranker may stay disabled for the first case; limitations must be
visible. Test their configured/unconfigured behavior; do not claim live quality
without provisioning. If the real corpus is pending, finish steps 1–6 and report
step 7 pending instead of substituting fixtures as real evidence.

## Deliverables

Write `docs/team/BACKEND_RUNTIME_ACCEPTANCE.md`: environment/commit, exact commands,
actual results/skips, live versus synthetic checks, failures/fixes, remaining
access inputs, stage timings and evidence-quality observations. Separate working
plumbing from measured research quality; a few cases do not establish Recall@10.
Update focused owner docs for any fixes. No secrets, raw tokens or private case
content in tracked evidence. Run diff/secret checks, commit and push your focused
feature branch; provide the commit and a concise handoff. Do not merge main,
deploy shared processes or change Eric's ingestion as part of this task.
