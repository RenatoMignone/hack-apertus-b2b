# Repeatable isolated runtime acceptance

19 October 2026. Use a disposable PostgreSQL/pgvector admin DSN, **never** an
application/ingestion DSN or Eric's shared database:

```sh
NAVIGATOR_TEST_ADMIN_DSN=postgresql://postgres@127.0.0.1:25432/postgres \
  .venv/bin/python -m pytest src/backend/tests/runtime/test_recovery.py \
  src/backend/tests/runtime/test_combined_research.py -q
```

The fixture creates/drops a uniquely named database. The process helper refuses
any database without its `navigator_test_` prefix. Checkpointer setup, deliberate
lease expiration and crash injection operate only on that disposable database.

Measured checks:

- Real subprocess exits immediately after claim-persistence stage commit, before
  LangGraph saves that node's next checkpoint. Another process takes over the
  expired lease, resumes via PostgreSQL checkpoints, reuses extraction output,
  completes one result and creates no duplicate claim. No provider is contacted.
- Existing clarification/restart, deadline, concurrent-worker, stale-answer and
  model-configuration pin checks remain covered.
- Combined LangGraph DB/web run uses actual SafeHTTP target/robots policy,
  public-PDF normalization, tool budgets, registration and PostgreSQL provenance.
  Transport responses, DNS, discovery, model decisions and embeddings are explicit
  synthetic fixtures. Duplicate pinned URLs retain corpus text/version/review;
  one new source remains unreviewed and case-scoped. Shared corpus is unchanged.

This is repeatable failure/provenance verification, not a live SearXNG/Crawl4AI
or Keera quality benchmark. Renato still needs the combined real-provider case,
upstream availability checks and a controlled deployment-host restart exercise.
