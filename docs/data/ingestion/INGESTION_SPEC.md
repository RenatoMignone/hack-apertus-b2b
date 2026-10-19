# Public-source ingestion and corpus builds

Bulk ingestion prepares reusable public knowledge independently of case-time
research. `src/backend/ingestion/` owns controlled acquisition, faithful normalization,
source registration, vocabulary import, reviewed enrichment and explicit builds.
The source registry [sources.yaml](sources.yaml) and supplied workbook are discovery
leads; actual fetched scope and coverage must be recorded.

## Pipeline

1. Register source origins/families, canonical URLs and approved scope.
2. Fetch public HTML or research PDF through robots-aware bounded HTTP. Record
   redirects/status/fetch date and raw bytes/hash. Scanned PDFs without text fail;
   OCR is not part of current normalization.
3. Normalize faithful text, headings/pages and exact Unicode spans. Preserve
   unknown publication dates and language. Create immutable document versions.
4. Import reviewed versioned MeSH/profile vocabulary; tag supported categories,
   specific subjects and attributes with exact passages. Model suggestions remain
   pending review; preserve unknowns and broader/related distinctions.
5. Chunk original text with chunk-to-evidence maps. Encode exact document-template
   strings using the shared [embedding configuration](../HOSTED_EMBEDDINGS.md),
   reusing unchanged compatible inputs. Store vectors/config/input text.
6. Prepare full-text projections and index builds. Make ready evidence available
   to authorized live captures, or explicitly publish a checked reviewed snapshot.

## CLI and manifests

```bash
.venv/bin/python -m backend.ingestion --help
.venv/bin/python -m backend.ingestion.review_cli --help
```

Commands include `collect`, `mesh-import`, `benchmark`, `build`. DB commands check
schema and never migrate. Hosted encoding removes the need for local model weights;
local mode requires provisioned assets. Runtime startup downloads nothing.

`build --sources` reads a JSON list of observation-file path, origin, families,
registry reference and optional reviewed claims/MeSH tags/specific subjects.
Claims contain supported entity identity/type/label, predicate, reviewer, exact
span and exactly one typed literal or object identity. Relationship targets must
resolve within scope. Tags and subject attributes carry exact support.
`--publish` is explicit and requires reviewed support and required source families;
a one-source sample build is not a complete pilot release. Inspect CLI help for
required access/profile/configuration manifests rather than inventing fields.

## Identity, review and publication

Use person/unit/organization/project/facility/service entity types. Labels are not
global identity keys. Canonical aliases deduplicate pages; same names do not merge
people. Every claim has literal support and derivation. Review inserts immutable
claim successors, with optimistic hashes; see [curation](../CORPUS_REVIEW.md).
Publication freezes membership and atomically moves the active pointer after
validation. Shared claims never learn automatically from case edits or exports.

Ingestion and query encoders must match weights/revision, tokenizer, templates,
dimension and normalization. Changed encoding creates a new build; do not relabel
vectors. Case web discovery/fetch uses [separate bounded tools](../WEB_RESEARCH.md)
and stores unreviewed case evidence. Neither path accepts confidential company plans.
Exact SQL fields are in [schema](../RELATIONAL_SCHEMA.md); shared DTOs are in
`contracts/data.py`, `pipeline.py` and `services.py`.
