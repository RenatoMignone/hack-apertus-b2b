# Retrieval proof of concept

**What it shows:** a fictional glucose-sensor company can retrieve relevant
passages from real Bern institutional sources, with inspectable quotations,
rankings and source references.

[Read the three-page PDF](Stregoni_Retrieval_Proof_of_Concept.pdf)
· [Inspect the original result record](retrieval-results.json)

The experiment ran on **19 October 2026 at 09:22 UTC**. The PDF presentation was
revised later that day; its original measurements and JSON remain unchanged.

## Results

Four requests searched an authorized capture of **127,902 chunks** and returned
**120 passage occurrences across 52 documents**. All recorded exact-slice and
source-body hash checks passed.

| Request | Encoding + search | Hits |
| --- | --- | --- |
| Full fictional company brief | 24.824 s | 30 |
| Glucose sensors | 21.839 s | 30 |
| CGM | 18.119 s | 30 |
| Everyday biosensing wording | 17.542 s | 30 |

Queries contained no researcher names. Independent lexical/vector search and RRF
returned the candidates; examples were selected after inspecting the rankings.
The PDF highlights Lilian Witthauer's sensing research (2023 publication), José
García-Tirado's closed-loop systems context (2024), and Stavroula Mougiakakou's
historical diabetes algorithms work (2012), with original quotations and links.

## Scope

This is evidence of **retrieval and traceability**. No accepted structured entity
profiles were returned; the researcher mentions are publication-based leads.
Independent expert Recall@10 was not measured. Results include weak matches and
older publications, so relevance, current roles and availability need review.
The returned sources do not establish broad coverage beyond ARTORG/UniBE and DCB.
This experiment did not run Apertus drafting, web research, reranking or UI export.

## What has been verified since

| Separate evidence | Result |
| --- | --- |
| Actual-Apertus isolated pipeline | Fictional sources; match, clarification/resume and no-match; assessed drafts, review and PDF export with PostgreSQL checkpoints |
| Frontend/backend integration | Navigation, authentication, evidence review and export behavior; combined automated checks passed |
| Live retrieval optimization | SQL retrieval and RRF timing were measured on an authorized corpus; this remains separate from the PoC |

These are separate experiments with different inputs and timing boundaries.
A fresh complete case on the optimized live corpus, reviewed expert recall and
target deployment acceptance remain. Current status
tracks those tasks.

## Rebuild the PDF

From repository root, with the backend installed:

```sh
python -m backend.evaluation.render_proof_of_concept
```

This reads the committed JSON and writes only the PDF. Bundled Unicode fonts work
across platforms; optional `--font` and `--font-bold` select other TTF files.
Receipt consistency is checked locally; the renderer does not repeat source-body
verification or contact the database/model. Private raw results are not required.

To collect a **new** experiment, use an existing authorized run and matching
encoder/tokenizer configuration:

```sh
python -m backend.evaluation.proof_of_concept --env-file PRIVATE_ENV --run-id OWNED_RUN_ID
```

The collector calls the configured embedding service and database, permits temporary
retrieval tables and performs no persistent corpus/case writes. Raw output stays
in ignored `.local/proof-concept/`. New results require their own inspected receipt;
do not replace the historical record with unreviewed rankings.

## Original provenance

Schema `0012_membership_lookup`; snapshot `658224cd-9e05-4fa1-bbbb-bc7d309f7fdf`;
source `a35d70af7f65` plus local changes. Relevance was inspected by the assistant;
no independent human gold labels were collected. Full pins, queries, rankings,
selected quotes and offsets are preserved in the JSON.
