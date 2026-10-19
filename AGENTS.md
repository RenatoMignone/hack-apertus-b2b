# B to Bern: agent entry point

Work in `hack-apertus-submission`. Preserve the root submission layout, original
partner materials and transcripts. Leave the historical sibling repository unchanged.

## Read only what the task needs

Start at [documentation](docs/README.md). The current implementation is described
by [architecture](docs/plans/ARCHITECTURE.md) and the
[execution graph](docs/plans/EXECUTION_GRAPH.md). [Delivery status](docs/project/STATUS.md)
separates implemented capabilities, measured verification and outstanding acceptance.

| Task | Read |
| --- | --- |
| Product or jury review | [Judge guide](docs/judges/README.md), [report](technical_report.md) |
| Setup, credentials, startup | [Local runbook](docs/data/LIVE_SETUP.md), [deployment](docs/data/DEPLOYMENT.md), [.env.example](.env.example), [Makefile](Makefile) |
| Module implementation | [Module map](docs/plans/MODULE_HANDOFFS.md), nearest source README |
| HTTP / frontend | [HTTP contract](docs/plans/FRONTEND_BACKEND_API.md), [UI behavior](docs/plans/FRONTEND_PLAN.md) |
| LangGraph / recovery / budgets | [Operations](docs/plans/OPERATIONS_PLAN.md), [service ports](docs/plans/SERVICE_CONTRACTS.md) |
| Evidence / report / review | [Processing boundaries](docs/plans/REPORT_PROCESSING_BOUNDARIES.md), [output](docs/plans/OUTPUT_REPORT_STRUCTURE.md) |
| Ingestion / taxonomy | [Ingestion](docs/data/ingestion/INGESTION_SPEC.md), [profiles](docs/data/DOMAIN_PROFILES.md), [review](docs/data/CORPUS_REVIEW.md) |
| SQL / retrieval | [Data layer](docs/data/DATA_LAYER.md), [schema](docs/data/RELATIONAL_SCHEMA.md), [generated columns](docs/data/SCHEMA_REFERENCE.md), [retrieval](docs/data/RETRIEVAL_SPEC.md) |
| Models / tools | [Apertus](docs/data/INFERENCE_CONFIGURATION.md), [embeddings](docs/data/HOSTED_EMBEDDINGS.md), [reranking](docs/data/RERANKING.md), [web](docs/data/WEB_RESEARCH.md) |
| Tests / quality | [Verification](docs/judges/VERIFICATION.md), [evaluation](docs/challenge/EVALUATION.md) |

## Implementation rules

- Inspect the working tree and actual contracts before edits. Preserve others'
  work; coordinate shared contracts, migration numbers and frontend changes with
  the active task owner. Module boundaries describe responsibilities, not permanent
  engineer ownership. Use focused files and acyclic imports.
- `contracts/` owns typed interfaces; `data/schema.py` and forward migrations own
  database structure; `/openapi.json` owns HTTP fields. Never infer fields from
  retired plans or use `legacy` / migration-baseline tables in application code.
- Keep SQL in data adapters, authorization/transactions in application services,
  agentic coordination in LangGraph/LangChain, model semantics in injected services
  and rendering deterministic. Frozen `ReportEvidencePack` is the drafting gate.
- Public facts require exact authorized passages plus semantic support assessment.
  Similarity, reranking, valid JSON and editorial keep decisions cannot establish
  truth. Missing roles/contacts stay unknown; adjacent matches retain caveats.
- Preserve full intent, negation and uncertainty. Taxonomy guides interpretation;
  topic/keyword hits cannot exclude otherwise eligible vector matches.
- Web findings stay flagged and case-scoped; canonical duplicates prefer pinned
  corpus versions. User edits/reports never automatically publish shared knowledge.
- Confidential plans stay outside the application and every model. Operator input
  is attributed context. Keep credentials and case data out of git, logs and
  `VITE_*`; retain `LLM_NAME`, `LLM_BASE_URL`, `LLM_API_KEY`.
- Shared servers use bearer bindings. Optional tokenless access is loopback-only
  with one existing identity. Never weaken RLS or migrate the shared host implicitly.
- All cards reviewed, at least one kept and exact result/selection/support hashes
  gate export. Wording edits reuse evidence; focus/identity edits research anew.
- Hosted providers/web require connected mode. Offline requires packaged local
  assets and disabled egress; the connected development path proves no air-gap.
- Run relevant checks. Full database tests require an explicitly disposable
  `NAVIGATOR_TEST_ADMIN_DSN`; never use shared infrastructure. Do not claim live
  quality, deployment or tests not actually verified.
- Update focused docs and the nearest README when behavior changes. Keep this
  file a router. Commit/push only within the user's authorization.
