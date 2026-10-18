# Backbone implementation handoff

18 October 2026. Lane C, isolated `backend/backbone` worktree. Integrated A's exact
contracts-only commit `77bf4f8`. No frontend, shared DTO, environment/lock,
submission-template, historical migration or finalized-schema changes.

## Implemented entry points

- `backend.data.backbone.create_backbone(engine, artifacts, embedder,
  reranker=None, observations=None)` implements `BackboneServices` v1, in process.
  Supply an authenticated application engine, not the maintainer/superuser DSN.
- `taxonomy(context)` returns the reviewed pinned version, concepts, labels,
  relations and profile. `retrieve(plan, context)` validates run and build pins,
  runs existing independent FTS/cosine/RRF search and bounded PostgreSQL claim
  expansion, returning actual `ResearchBundle`/`EvidenceRecord` DTOs.
- `register_research(result, context)` checks the whole snapshot and aliases,
  prefers pinned versions, otherwise stages case-owned text/artifacts and flags
  it web/unreviewed. Pass the fetcher's observation cache to retain original HTML.
- `persist_extraction(batch, context)` validates batch-local identities, literal
  source support, pinned existing IDs and case ownership. Exact supported shared
  literal claims may be reused. Other proposals mirror original artifacts/text,
  source spans and identities into the case scope. Claim/subject/evidence lineage
  is recorded in existing derivations. New claims remain `needs_review`.
- `read_evidence(ids, context)` projects authorized exact Unicode spans, original
  hashes, nullable publication dates and observed dates. A mirrored public source
  stays corpus/curated, not web merely because its scope is a case. Reads also
  reauthorize original shared support, so revocation cannot be bypassed by a copy.
- `backend.ingestion.web.create_web_tools(discovery=None, user_agent=None,
  allowed_hosts=())` implements `WebResearchTools`. Unconfigured/offline tools
  are explicitly unavailable. `BraveDiscovery(api_key)` is an opt-in discovery
  implementation, never enabled implicitly and never called in the measured run.

Adapters run complete synchronous repository calls in worker threads, without
sharing live SQL connections between threads. Cancellation propagates; deadline,
source, graph, label and embedding budgets are explicit. Errors crossing the
service boundary use the shared safe errors. A still owns graph execution,
idempotent durable stage envelopes, authentication and the composition root.

## Three-tier MeSH and label limits

This incorporates the user's later clarification: MeSH structural categories and
subcategories, plus dynamic concrete subjects. There is no custom diabetes topic
tree, additional graph database, device table or new medical entity type.

- Tier 1: official MeSH category, e.g. `C` Diseases.
- Tier 2: official immediate MeSH subcategory, e.g. `C19` Endocrine System Diseases.
  Deeper tree numbers may be rolled up for navigation, but cannot be stored as tags.
- Tier 3: up to five named source subjects with at most four literal attributes
  apiece (e.g. device name/material/prototype status). These are document-linked,
  evidence-backed extraction derivations, not additional MeSH branches. Exact
  evidence IDs support every name/attribute. They are not clinical conclusions.
- **At most three distinct topic labels per document version and taxonomy**,
  strongest first. Parent domains are derived and deduplicated, with at most three
  domains. Thus three topic families can produce at most six structural tags,
  not six independent topics. Accumulated imports cannot evade the cap. One or
  two meaningful labels are preferable to filling the quota. Unknown is allowed.
- Model suggestions are pending review; literal JSON/slice validation is not
  semantic certification. Human/approved semantic review is recorded separately.
  Classify meaning, negation and attribution, not isolated keywords. Navigation,
  references and incidental mentions must not generate positive labels.
- This labels **individual page/document versions**, not an entire institution or
  web domain. Inferred tags remain hints; neither retrieval branch is hard-filtered
  by them. Only explicit, reliable application constraints affect eligibility.

`config/profiles/mesh-2026.json` pins the NLM release artifact and tag policy.
`mesh.mesh_vocabulary` loads only the first two structural levels. The inspected
2026 tree contains **16 categories and 115 immediate subcategories**; these are
the real MeSH counts, rather than an invented 5–15/60–100 grouping. The `unknown`
sentinel is explicitly system metadata, not an invented NLM category.
English labels come from NLM; no unverified multilingual translations are presented
as official aliases. Source text is preserved in its original language.

`MeSHClassifier(model)` accepts an injected LangChain structured-output model.
`analyze(document, vocabulary)` returns validated tags and specific subjects.
`MeSHTagger.assign(...)` stores them on the existing tables with exact evidence,
primary priority and version pins. Classification creates no autonomous agent.
The model context/token budget must be checked by A/B's configured model wrapper;
the adapter also rejects oversized documents rather than silently truncating them.

`BackboneRepository.subject_mentions(version_ids, context)` reads authorized
document subject projections. A should add an agreed subject-mention field to the
shared bundle in a subsequent additive contract change if the runtime needs it
separately. C has **not** disguised medical subjects as person/unit/entity rows or
forked `ResearchBundle` to add an unagreed field. Original evidence remains available
to B through the existing v1 contract.

## Ingestion, models and publication

**User decision, 18 October 2026:** defer actual corpus ingestion until the code
changes are completed/integrated and deployment prerequisites are ready. Ingestion
is an explicit later operator command, not a startup hook or background task.
Do not populate the shared corpus or publish an index as part of this feature run.

- `RegistryImporter` imports source families (including overlapping UniBE/ARTORG),
  content-hashed immutable profiles/taxonomies and reviewed multilingual labels
  when actually provided. Conflicting immutable versions fail explicitly.
- `CorpusBuilder` stages faithful HTML/public-PDF text, original bytes, headings,
  page/Unicode spans, known aliases, actual fetch observations and optional reviewed
  entity/relationship claims. Unknown publication dates stay null. Unchanged chunks
  reuse their exact input/config embeddings. No confidential business-plan intake.
- `CorpusBuilder.publish` requires reviewed claim-bearing records; existing
  snapshot checks require all three families and full pinned subject/object/support
  membership. Shared snapshots now also reject case-scoped documents and unreviewed
  taxonomies. Failed publication does not replace the active snapshot.
- `models.embeddings.local.load_embeddinggemma(configuration, local_path)` is
  local-files-only. It requires the actual package-version identity, model commit,
  tokenizer identity, float32, real token budget and verified configuration. Exact
  manually formatted query/document inputs are encoded without double prefixes.
  Finite nonzero shape-compatible vectors are L2-normalized. No implicit download,
  hosted fallback or use of Apertus token IDs.
- `models.reranking.local.load_reranker(...)` implements the existing finite-score
  port with explicit pair-token budgets and local artifacts. Missing rerankers are
  reported, and an unavailable reranker does not erase valid hybrid hits. Scores
  are always labelled relevance, never calibrated factual confidence.
- Web targets undergo public-address/DNS checks, IP-pinned connections with TLS
  hostname validation, redirect rechecks, robots policy, rate/byte/time limits.
  Browser JavaScript/subresource execution is deliberately absent: SafeHTTP acquires
  controlled bytes; Crawl4AI generates Markdown from sanitized extracted content.
  Search snippets are leads only. Failed/blocked pages produce explicit limitations.

Optional packages are proposals in `ingestion/requirements.in`; A resolves the
shared lock. None were installed into the team's existing venv. No service was
started/stopped and no hosted provider/paid service or model download was provisioned.

## Commands

From an activated lane environment with `PYTHONPATH=src` and `PYTHONUTF8=1`:

```powershell
python -m backend.ingestion --help
python -m backend.ingestion collect https://www.dcberne.com/en/projects/ --user-agent 'YOUR-IDENTIFIED-USER-AGENT' --output .local/dcb-observation.json
python -m backend.ingestion --env-file .local/application.env mesh-import --trees .local/mtrees2026.bin --manifest src/backend/config/profiles/mesh-2026.json --access .local/access.json --reviewer REVIEWER --output .local/mesh-pins.json
python -m backend.ingestion benchmark --configuration .local/verified-embedding.json --model-path .local/models/embeddinggemma --inputs .local/formatted-inputs.json --output .local/embedding-benchmark.json
python -m backend.ingestion --env-file .local/application.env build --access .local/access.json --scope PUBLIC_SCOPE_UUID --sources .local/sources.json --mesh-pins .local/mesh-pins.json --configuration .local/verified-embedding.json --model-path .local/models/embeddinggemma --confirm-public-sources --output .local/build.json
```

`build --publish` is explicit; use `--expected-active SNAPSHOT_UUID` when replacing
an existing publication. These commands never migrate. Output files are exclusive,
so immutable manifests are not overwritten. The source-list schema is documented
in this lane's ingestion README. Application credentials must match AccessContext;
IDs do not confer permission.

## Measured and remaining gates

The preserved backend suite plus owned tests pass in disposable PostgreSQL/pgvector
databases. UTF-8 must be enabled on Windows: without it an existing schema-reference
test fails on platform-default decoding of an em dash. No canonical doc/test bootstrap
was altered to hide this. Final exact test count/command is in RESULTS.md.

Public collection succeeded for one UniBE/DBMR, one ARTORG and one DCB page;
see SOURCE_MANIFEST.json. Raw bytes/text remain ignored/local, not committed or
redistributed. This is a tiny source slice, not exhaustive ecosystem/expert coverage.
No real index/snapshot was published and no real-model Recall@10 is claimed.

**Shared host is still `0004_case_pipeline` (read-only check).** This lane targets
the finalized `0005_finalize_schema` and cannot run on that host until its maintainer
schedules backup/migration separately. No shared-host migration was performed.

**Case-scope provisioning is a runtime integration blocker:** schema-0005 requires
an existing writable case scope/grant, but ordinary app roles cannot create their
own grant (RLS denies it), and CaseRepository.create does not provision one. Tests
explicitly provision isolated scopes through their fixture owner. A/maintainer
must agree a secure provisioning mechanism; no privileged worker connection or
uncoordinated DDL was added to bypass the finalized access contract.

EmbeddingGemma and BGE weights/runtime, verified package combination, real hardware
benchmark, authenticated Apertus classification, discovery key/provider approval,
PDF dependency/browser-free Crawl4AI runtime smoke test, partner-reviewed expert/unit
gold labels and meaningful EN/DE/FR/IT quality checks remain deployment gates.
`ingestion.evaluation.recall_at_10` requires reviewed labels and aggregates by intent;
synthetic fixtures are never reported as a model-quality metric.

## References checked

- [NLM MeSH tree structure](https://www.nlm.nih.gov/mesh/intro_trees.html),
  [official category labels](https://meshb.nlm.nih.gov/treeView),
  [2026 tree artifact](https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/newterms/mtrees2026.bin).
- [EmbeddingGemma model card](https://huggingface.co/google/embeddinggemma-2),
  [BGE reranker](https://huggingface.co/BAAI/bge-reranker-v2-m3).
- [Crawl4AI Markdown generation](https://docs.crawl4ai.com/core/markdown-generation/),
  [Brave discovery API](https://api-dashboard.search.brave.com/api-reference/web/search/get).

Model repository metadata was inspected without downloading weights:
EmbeddingGemma `914f7f89142e33e77833254d9c9b90c3cef7303b`,
BGE `953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e`. These metadata observations do not
verify a local runtime, tokenizer loading, latency, dimensions or quality.
