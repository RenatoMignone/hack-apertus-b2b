# Technical options and implementation handoff

**Status: proposal, not an architecture decision.** No implementation, language,
database, retrieval framework, endpoint or hosting arrangement has been selected.
The discussion explicitly leaves prefetching versus live tool access open.
[Recording evidence E18–E20](RECORDING_INSIGHTS.md)

## Logical responsibilities

The written brief requires a flow from public sources through extraction,
semantic enrichment and structured knowledge to source-backed search. A useful
division of responsibilities, independent of stack, is:

1. **Discovery/collection:** configured seeds and bounded public-page access;
   collect coverage and failure metadata.
2. **Extraction:** clean content and retain titles, structural context, links,
   dates and evidence locators.
3. **Enrichment:** identify entities/capabilities and terminology; distinguish
   source observations from inferred relationships.
4. **Retrieval:** search across the whole ecosystem, resolve duplicates and
   rank against the actual company need.
5. **Evidence validation:** check the support for every returned factual field.
6. **Presentation:** structured results, concise explanation, direct links and
   visible uncertainty; optional reviewed export later.
7. **Evaluation:** version the corpus, queries, expected matches and actual runs.

These need not be separate services. Do not introduce orchestration, a graph,
fine-tuning or infrastructure solely because the terms appeared in discussion.

## Architecture alternatives

| Option | Useful properties | Main trade-offs and required proof |
| --- | --- | --- |
| Prefetched corpus/index | Reproducible snapshot, inspectable evidence, predictable search cost; supports a disconnected runtime with local dependencies | Collection/refresh maintenance and extraction coverage; show that useful pages were actually captured and dated |
| Live model-assisted navigation | Can inspect current pages and reduce precollection needs | Network dependence, website failures, latency/cost, harder reproducibility and citation validation; this path alone cannot run air-gapped |
| Prefetched search with bounded connected refresh | Can separate reproducible baseline from source updates | More moving parts; make online/offline behavior explicit and do not silently fall back to an external service |

Connected independent cloud is permitted by B1. Live browsing therefore is not
automatically disallowed, but it cannot substantiate a claim of disconnected
operation. Choose one primary demonstrated target and document alternatives as
proposals. Never deploy into cantonal ICT or require an internal network.

## Candidate Apertus roles

| Role | Potential value | Validation needed |
| --- | --- | --- |
| Query understanding/term expansion | Bridge lay wording, abbreviations and institutional terminology | Same-intent expert recall; avoid expansion into unrelated medical topics |
| Evidence-bound entity/capability extraction | Normalize heterogeneous pages into structured result fields | Field accuracy, missing-value behavior and evidence for each relationship |
| Match explanation/plain-language description | Explain how a source-supported capability relates to the company need | Claim support and readability; label any adjacent-application hypothesis |
| Candidate reranking or guided navigation | Improve relevance or find missing pages | Compare with a simpler baseline; measure latency/cost and failure behavior |

Pick a justified subset using **Apertus v1.5 8B or 70B**. Do not assume Apertus
provides an embedding API, vision capability, guaranteed JSON conformance or
tool-calling behavior on an unverified endpoint. Auxiliary embedding/reranking
models are options whose license, runtime dependencies and sovereign deployment
must be documented; none has been selected.

Record actual model identifier/version, endpoint compatibility, prompts,
sampling/quantization settings, serving stack, hardware/quotas and observed
failures. Hosted development inference does not prove local portability.

## Retrieval and grounding options

A proposed low-complexity baseline is lexical keyword retrieval. Compare the
chosen semantic technique against that baseline on verified terminology variants.
Lexical/semantic hybrid retrieval, learned reranking, explicit concept mappings
and a knowledge graph are alternatives, not requirements.

Regardless of choice, retain evidence pointers through extraction and ranking.
Validate source IDs/URLs and supported claims before rendering results. Avoid
relying on model confidence scores as proof. A lower rank or unavailable field
is preferable to an unsupported role, contact or project. Use the proposed
contract in [DATA_AND_PROVENANCE.md](DATA_AND_PROVENANCE.md).

## Deployment and configuration obligations

- Keep `LLM_NAME`, `LLM_BASE_URL`, `LLM_API_KEY` as the model configuration names
  required by the template. Actual values are unknown; never commit a key.
- Endpoint URL, authentication scheme, exact model names, protocol, quotas and
  support arrangements must be verified before building an adapter. A prior
  organizer announcement about CSCS keys is context, not endpoint documentation.
- Distinguish connected acquisition, build/model download and search runtime.
  Inventory every external dependency, including embeddings, fonts, analytics,
  CDNs and browser assets if used.
- For a claimed air-gapped run, preload all required assets and actually test
  with network access disabled. For Swiss-cloud claims, verify operator,
  jurisdiction, location/residency and dependencies rather than inferring them
  from a Swiss-looking URL.
- Code goes in `src/`; architecture detail and run instructions eventually go
  in root `technical_report.md` without removing its mandatory sections.

## Suggested order after implementation is authorized

1. Obtain the missing source inventory, verify seeds and decide a feasible
   medical slice while retaining all three source families.
2. Agree on a small evidence-backed query/expected-match pilot and source
   snapshot before optimizing retrieval.
3. Choose the smallest architecture and Apertus role that can demonstrate the
   complete pipeline, evidence and deployment boundary.
4. Build one real end-to-end result, including missing-field/no-match behavior.
5. Expand coverage and terminology cases; evaluate and record failures.
6. Add optional export/shortlisting only if the core requirements work.

Log actual choices and evidence in
[DECISIONS_AND_OPEN_QUESTIONS.md](DECISIONS_AND_OPEN_QUESTIONS.md). None of these
steps has been executed or authorized as implementation by the current docs task.
