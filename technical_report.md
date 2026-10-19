# Technical report — B to Bern (B2B), Team Stregoni

- **Challenge:** Bern Economic Development Agency — Research & Expertise Navigator
- **Event:** Hack Apertus, on-site Liebefeld
- **Team:** Stregoni — Renato Mignone, Elia Innocenti, Eric Ruiz Giménez, Mohamed Kechiche
- **Demo:** Pending video URL; [reproducible walkthrough](docs/judges/DEMO.md)
- **Status:** Delivery draft, 19 October 2026; final artifacts and acceptance are tracked in the [delivery checklist](docs/judges/DELIVERY.md)

## 1. Summary

B to Bern helps economic-development staff identify research capabilities relevant
to a company's plans. Operators describe permitted company context and Bern
objectives in everyday language. B2B searches public institutional evidence,
explains direct and adjacent matches, and produces a reviewed “Why Bern?” brief.
The diabetes-technology pilot treats UniBE, ARTORG and Diabetes Center Berne as
one ecosystem. Apertus v1.5 interprets needs, extracts and assesses evidence, and
drafts cited reasons; code controls provenance and export eligibility.
A real-provider partial report and reviewed PDF have been demonstrated. Actual-
Apertus isolated cases also passed clarification, evidence assessment, review and
export. Real-corpus retrieval and later SQL optimization have separate measured
receipts.
Independent expert Recall@10 remains to be measured.

## 2. Architecture

React/Vite communicates with an authenticated FastAPI service. A separate durable
LangGraph worker executes interpretation, clarification, research, evidence
preparation and drafting. PostgreSQL/pgvector stores authorized corpus evidence,
case revisions and results; a separate PostgreSQL database holds framework
checkpoints, with checkpoint row-level isolation and target-host access policy
remaining deployment-acceptance items. S3-compatible storage holds source and
export artifacts. Optional
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

### Target architectures (mandatory)

The application is designed to run in all three requested deployment settings:

- **On-premise:** all services can run on infrastructure administered by the
  organisation, whether on a remote Swiss server, an internal company server,
  or a controlled personal workstation/PC for development or small-scale use.
- **Air-gapped:** connected build stages prepare approved corpus snapshots,
  compatible indexes, Apertus weights and serving runtime, embedding/reranker
  assets, tokenizers, dependencies and report assets for transfer. Runtime uses
  local inference/encoding, disables web research and external egress, and
  performs intake, retrieval, review and export locally.
- **Sovereign Swiss cloud:** the same services can run on a Swiss-operated,
  Swiss-jurisdiction cloud with Swiss data residency and provider-controlled
  storage, backups, inference and monitoring.

These are supported deployment designs, not completed certifications. A cold
start, completed case and export with external networking disabled remain
acceptance requirements for the air-gapped target; Swiss jurisdiction,
residency, contractual controls and operations remain acceptance requirements
for a sovereign-cloud deployment.

The measured development path is **connected**: Keera reasoning, an HF embedding
endpoint, independently hosted PostgreSQL/MinIO and local API/worker/frontend.
Current development uses PostgreSQL hosted on team-controlled infrastructure.
This does not establish Swiss data residency, sovereign Swiss-cloud operation or
air-gap compliance. Build time requires package/model/image acquisition;
connected runtime additionally requires provider credentials and network access.
Offline runtime requires packaged assets and local services, with no hosted
fallback.

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
LangChain supplies model/task adapters. See the
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
as public evidence. Source copyright remains with institutions; Apache-2.0 code licensing does not
relicense source pages, personal data, recordings or model weights. Partner
branding is for this challenge only. Workshop recordings, transcripts and source
snapshots are retained as internal provenance where permitted, but are excluded
from the public submission unless their publication rights are separately
confirmed.

## 5. Limitations

The live-corpus report is partial. A fresh full case after the retrieval fix,
combined database/web quality and independently reviewed expert Recall@10 remain
acceptance tasks. Source coverage, freshness, multilingual quality, representative
latency/cost and load also need evaluation; English is the baseline.

Apertus is central to interpretation, evidence assessment and drafting, so model
quality directly affects the product. Context limits, reasoning errors,
structured-output failures, multilingual quality, inference latency,
memory/accelerator requirements, provider availability and model-version changes
remain material risks. Bounded prompts, typed contracts, validation, evidence
gates and human review reduce these risks but cannot remove the underlying model
trade-offs.

Source passages and model support checks make findings inspectable, while human
review handles unsupported implications and practical follow-up. Current roles,
availability and willingness to collaborate need confirmation. Users may download
the reviewed report as PDF and, where enabled, as PPTX; both outputs remain
dependent on the reviewed evidence and configured deployment.

The retrieval PoC is evidence of source traceability and retrieval mechanics only.
It does not establish complete corpus coverage, expert availability, semantic
matching quality or end-to-end report quality. A reachable source URL or matching
passage does not prove that every generated role, capability, relationship,
availability statement or business implication is correct.

The selected air-gapped runtime has not been demonstrated; current development is
connected. Target-host restart/recovery and checkpoint access isolation remain.
Representative cost and throughput are not yet measured. The main drivers are
70B inference, embedding generation, optional reranking, corpus storage,
crawling and concurrent workflow execution. Local sovereign operation may require
substantial accelerator memory, while hosted operation introduces provider cost,
quota and availability dependencies.
See [verification](docs/judges/VERIFICATION.md), the
[retrieval PoC](docs/proof-of-concept/README.md) and the
[delivery checklist](docs/judges/DELIVERY.md).

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
isolated disposable databases and fixture providers where applicable. Historical
validation and live receipts used different environments; no single
hardware/quality benchmark is claimed. Record the final commit, platform, pins,
active flags and live-case outcome for any reproduced result.

## License

Creative Commons Attribution 4.0 (CC-BY-4.0), following the report template.
Repository code uses [Apache-2.0](LICENSE); third-party material keeps its rights.

## References

1. [Supplied challenge and success criteria](docs/challenge/CHALLENGE_BRIEF.md).
2. [Architecture/deployment contract](docs/plans/ARCHITECTURE.md).
3. [Processing and evidence gates](docs/plans/REPORT_PROCESSING_BOUNDARIES.md).
4. [Apertus configuration](docs/data/INFERENCE_CONFIGURATION.md).
5. [Embedding protocol and pins](docs/data/HOSTED_EMBEDDINGS.md).
6. [Recorded live partial report and PDF](docs/judges/VERIFICATION.md).
7. [Capture-performance evidence](docs/data/CAPTURE_PERFORMANCE.md).
8. [Evaluation method](docs/challenge/EVALUATION.md).
9. [Retrieval proof-of-concept PDF](docs/proof-of-concept/Stregoni_Retrieval_Proof_of_Concept.pdf).
