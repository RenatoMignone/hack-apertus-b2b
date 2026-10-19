# Technical report — B to Bern (B2B), Team Stregoni

- **Challenge:** Bern Economic Development Agency — Research & Expertise Navigator
- **Event:** Hack Apertus, on-site Liebefeld
- **Team:** Stregoni — Renato Mignone, Elia Innocenti, Eric Ruiz Giménez, Mohamed Kechiche
- **Demo:** Pending video URL; [reproducible walkthrough](docs/judges/DEMO.md)
- **Status:** Delivery draft, 19 October 2026; integrated main, with final artifacts/acceptance tracked in the delivery checklist

## 1. Summary

B to Bern helps economic-development staff identify research capabilities relevant
to a company's plans. Operators describe permitted company context and Bern
objectives in everyday language. B2B searches public institutional evidence,
explains direct and adjacent matches, and produces a reviewed “Why Bern?” brief.
The diabetes-technology pilot treats UniBE, ARTORG and Diabetes Center Berne as
one ecosystem. Apertus v1.5 interprets needs, extracts and assesses evidence, and
drafts cited reasons; code controls provenance and export eligibility.
A real-provider partial report and reviewed PDF have been demonstrated. This
establishes a working narrow path, not comprehensive expert discovery or measured
retrieval quality. The challenge's 80% Recall@10 target remains unmeasured.

## 2. Architecture

React/Vite communicates with an authenticated FastAPI service. A separate durable
LangGraph worker executes interpretation, clarification, research, evidence
preparation and drafting. PostgreSQL/pgvector stores authorized corpus evidence,
case revisions and results; a separate PostgreSQL database holds framework
checkpoints. S3-compatible storage holds source and export artifacts. Optional
masked local Langfuse traces diagnose execution and do not supply facts.

Retrieval runs lexical and vector searches independently, fuses with reciprocal
rank fusion and optionally reranks using a provisioned multilingual CPU model.
Topic labels cannot exclude otherwise eligible vector matches. Optional connected
web research discovers URLs through private SearXNG and converts fetched
pages using isolated Crawl4AI. Search snippets are not evidence. New web evidence
remains flagged and case-local; it does not update the shared corpus automatically.

Evidence preparation combines literal passage checks with model-based semantic
support and need-fit assessment. Code freezes a `ReportEvidencePack` before
drafting. Each draft is assessed against its exact content hash. Operators review
every reason, keep at least one, and approve the exact result/selection hashes
before deterministic export. Editorial approval does not establish factual truth.
Wording edits reuse the pack; new facts or focus create a new research revision.
See the [judge architecture guide](docs/judges/ARCHITECTURE.md) and
[execution graph](docs/plans/EXECUTION_GRAPH.md).

### Target architecture (mandatory)

**Selected design target: b) air-gapped case runtime on independent infrastructure,
outside cantonal ICT. This target has not been demonstrated.** Connected build
stages must prepare approved corpus snapshots, compatible indexes, Apertus weights
and serving runtime, embedding/reranker assets, tokenizers, dependencies and report
assets for transfer. Runtime must use local inference/encoding and disable web
research and external egress. A cold start, completed case and export with external
networking disabled remain acceptance requirements.

The measured development path is **connected**: Keera reasoning, an HF embedding
endpoint, independently hosted PostgreSQL/MinIO and local API/worker/frontend.
The team currently hosts PostgreSQL on a member's computer. This does not
establish Swiss data residency, sovereign Swiss-cloud operation or air-gap
compliance. Build time requires package/model/image acquisition; connected runtime
additionally requires provider credentials and network access. Offline runtime
requires packaged assets and local services, with no hosted fallback.

## 3. Use of Apertus

- **Model:** gateway alias `apertus-v1-5-70b`, Apertus v1.5 70B; the immutable
  served weight revision is not established by the alias.
- **Use:** structured interpretation/query planning; atomic claim extraction;
  semantic support/fit assessment; draft synthesis and wording assessment.
- **Measured connection:** CSCS through Keera, `https://gateway.keera.ch/api/v1`,
  using Chat Completions and a private team key.

`LLM_NAME`, `LLM_BASE_URL` and `LLM_API_KEY` remain backend configuration. The
model is selected explicitly with no automatic fallback. Typed contracts and
bounded repair constrain task responses; valid JSON alone is insufficient to
accept a factual statement. LangGraph coordinates all agentic execution and
LangChain supplies model/task adapters. Thinking aliases are separate and cannot
be combined with tool calling. See the
[evidence services](src/backend/evidence/README.md) and
[model adapters](src/backend/models/README.md).

Embeddings are a separate role: the connected encoder is pinned EmbeddingGemma 2,
revision `914f7f89142e33e77833254d9c9b90c3cef7303b`, with 768-dimensional vectors
and a compatible local tokenizer. Ingestion and queries must use the same
verified configuration. The optional reranker has its own compatible tokenizer;
neither rank nor similarity is a factual-support score.

## 4. Data

The pilot sources are public UniBE, ARTORG and Diabetes Center Berne pages and
public research PDFs. The supplied UniBE workbook is a discovery map, not proof
of complete acquisition. Corpus versions retain exact text, hashes, locators,
retrieval configuration and access scope. Published snapshots or immutable
case-owned live captures pin each run's evidence while ingestion can continue.
Counts change during collection; no fixed release count or three-source
completeness is claimed here.

Operators read confidential company documents outside the application and type
only permitted context. Confidential uploads to any model are forbidden under
the current boundary. Operator assertions remain attributed rather than treated
as public evidence. Source copyright remains with institutions; Apache-2.0 code
licensing does not relicense source pages, personal data, recordings or model
weights. Partner branding is for this challenge only. Original materials and
the explicitly publication-authorized transcript are preserved; no additional
redistribution rights are assumed.

## 5. Limitations

The strongest recorded live result is a partial report, not an expert-search
benchmark. Named-person/facility coverage, direct versus adjacent fit, combined
real DB/web quality, freshness and bias need review. No independently judged
Recall@10, factual-accuracy percentage, time-saving figure, cost per case,
load capacity or DE/FR/IT quality result is claimed. English is the baseline.

Model assessment can miss unsupported implications even when quotations are
correct. B2B exposes source passages, missing information and caveats and can
return partial/no-match output. It cannot establish expert availability,
willingness to collaborate or clinical suitability. Context limits, provider
quotas, search failures and capture latency can interrupt research. Checkpoint
tests do not certify target-host recovery or full credential isolation.
Optional PPTX, manual plans and own-case memory require activation and assets;
synthetic tests do not certify their live use.

The [verification guide](docs/judges/VERIFICATION.md) records evidence provenance.
Deployment acceptance and delivery artifacts remain open in the
[release checklist](docs/judges/DELIVERY.md).

## 6. Reproducibility

Use [judge setup](docs/judges/QUICKSTART.md) for exact PowerShell/Bash commands.
The credential-free route requires Node 22.18+, `npm ci` in `src/frontend`, then
`VITE_API_MODE=mock npm run dev` in Bash (PowerShell syntax is in the guide).
This scripted UI route makes no live research-quality claim.

For the backend, use Python 3.12–3.14 (3.13 is the documented starting point),
install `src/backend/requirements.lock` and the editable backend, then configure
an ignored environment from `.env.example`. Provision application/checkpoint DB
access, authorized corpus/profile pins, source/export storage, matching encoder
configuration/tokenizer and provider access. Hosted embeddings additionally use
`requirements.hosted.lock`. Run from root in the activated environment:

```text
python -m backend.deploy.check_runtime --env-file .env
python -m backend.deploy.check_runtime --env-file .env --network
navigator-runtime --env-file .env serve --host 127.0.0.1 --port 8000
```

In a separate terminal with the same environment run
`navigator-runtime --env-file .env worker`. Start Vite in HTTP mode; shared access uses the privately provisioned operator
token, while configured single-identity loopback testing auto-connects. Follow the walkthrough through
source inspection, review and PDF download. Startup does not migrate, populate
data or download weights. A clean clone is not a pre-provisioned live installation.

The guide also supplies a synthetic API/worker route using disposable local
PostgreSQL/pgvector and fixture providers. Backend checks use
`python -m pytest src/backend/tests -m "not integration" -q`; the full suite
requires an isolated `NAVIGATOR_TEST_ADMIN_DSN` and creates/drops test databases.
Frontend checks are `npm test` and `npm run build`. Record the final commit,
platform, pins, active flags, test counts and live-case outcome at release.
Historical tests and live receipts used different environments; no single
hardware/quality benchmark is claimed. Final release SHA and report PDF/page
count remain pending.

## License

Creative Commons Attribution 4.0 (CC-BY-4.0), following the report template.
Repository code uses [Apache-2.0](LICENSE); third-party material keeps its rights.

## References

1. [Supplied challenge and success criteria](docs/challenge/CHALLENGE_BRIEF.md).
2. [Architecture/deployment contract](docs/plans/ARCHITECTURE.md).
3. [Processing and evidence gates](docs/plans/REPORT_PROCESSING_BOUNDARIES.md).
4. [Apertus configuration](docs/data/INFERENCE_CONFIGURATION.md).
5. [Embedding protocol and pins](docs/data/HOSTED_EMBEDDINGS.md).
6. [Recorded live partial report and PDF](docs/project/STATUS.md).
7. [Capture-performance evidence](docs/data/CAPTURE_PERFORMANCE.md).
8. [Evaluation method](docs/challenge/EVALUATION.md).
