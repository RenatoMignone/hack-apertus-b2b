# Backbone validation results

> **Historical lane record — completed and merged, 18 October 2026.**
> Original instructions/results below describe that lane before integration.
> Its pending integration requests and ownership freezes are superseded by the
> [merged baseline](../INTEGRATION.md) and [current status](../../project/STATUS.md). Do not rerun this as a new task.

Measured 18 October 2026; branch `backend/backbone` plus A's exact `77bf4f8`
contracts-only commit. No application-schema DDL was added or altered.

## Tests

**69 passed in 25.13 seconds**, including all preserved backend tests and the
owned backbone suite, on disposable PostgreSQL 17/pgvector databases. The test
fixture creates and removes only its uniquely named databases. Shared `navigator`
was not migrated or populated by the test run.

From the original checkout on this host (not from the isolated worktree):

```powershell
$env:PYTHONUTF8 = '1'
$env:PYTHONPATH = "$PWD\.local\worktrees\backbone\src"
.\.venv\Scripts\python.exe -m backend.tests.run
```

The existing runner reads the ignored original host environment privately. In a
different lane environment, set NAVIGATOR_TEST_ADMIN_DSN to an authorized server
and run pytest on src/backend/tests. Never paste credentials into tracked files.

Coverage includes immutable versions/Unicode spans, original-content input
templates, finite/nonzero vectors, reranker bounds, independent lexical/vector
retrieval, RRF, access/revocation, leases/checkpoints, publication failure, supported
graph endpoints, whole-snapshot URL aliases, exact shared claim reuse, idempotent
pending case extraction and public-evidence mirrors, source flags, offline behavior,
MeSH-only two-level structure, Tier-3 subject/attribute evidence, three-topic
multilabel caps (including accumulated imports), model over-tagging rejection,
SSRF/private/mixed DNS targets, and reviewed-entity recall calculation mechanics.

Additional checks: compileall succeeded; git diff --check passed; ingestion CLI
help loads; actual NLM artifact parsing produced 16 categories/115 subcategories.
An earlier existing schema-reference assertion failed under Windows default text
encoding; enabling PYTHONUTF8=1 resolves it without modifying protected docs/tests.

## Actual collection and deployment

- Three pilot pages were fetched with robots/DNS/redirect/byte/time checks. The
  source manifest records hashes/dates/omissions. Raw originals remain private local
  working artifacts, not committed data. No model-quality conclusion follows.
- Model repository revisions were inspected without downloading weights. No real
  embedding/reranking/Apertus runtime was executed; no production snapshot/build
  IDs, hardware-throughput numbers or reviewed Recall@10 are available.
- Shared host revision was checked read-only: 0004_case_pipeline. The new lane
  targets finalized 0005; its maintainer must explicitly schedule that migration.
- Windows SSH keys for ren and elia were installed in their own standard-user
  profiles. Explicit file owners and protected user/SYSTEM/Administrators ACLs
  were verified, both public-key fingerprints validated and sshd -t passed in an
  administrator process. The running server presented its ED25519 host key on
  loopback. Key options restrict forwarding to host-loopback ports 5432 and 9000.
  No private keys were supplied or copied. A real peer's key authentication/WLAN
  reachability is not tested from this computer; DHCP firewall addresses still
  need to match each teammate. Mo's key is intentionally pending.

Remaining rollout gates and shared-contract requests are in HANDOFF.md.

The user explicitly chose to run actual ingestion later, after the changes are
ready. No production ingestion worker is running or scheduled by this task.
