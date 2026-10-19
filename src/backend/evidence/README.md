# Evidence preparation

`create_reasoning_services(settings, *, model=None, transport=None, receipt=None,
token_counter=None)` implements A's `ReasoningServices` v1. See the
[lane handoff](../../../docs/team/intelligence/HANDOFF.md).

- `interpret`: full permitted message + reviewed taxonomy (`concepts` with
  `concept_id` or `id`) → typed interpretation and targeted blocking questions.
- `extract`: supplied passages → local-key entity/atomic claim proposals; no
  invented canonical IDs, unsupported labels or unresolved batch references.
- `assess`: canonical pending claims + C's remapped evidence → separate semantic
  support/contradiction decisions. Code copies exact statements/support IDs.
- `propose_pack`: include only exact supported assessments with complete supplied
  evidence; bounded need-fit reasoning produces matched arguments/conditions.
  Unsupported/irrelevant material is excluded; partial/no-match is explicit.
- `draft` / `assess_draft`: delegate to the owned report services, using the frozen
  pack only and assessing exact wording/hash separately.

No SQL, fetching, tool execution, shared-memory publication or authoritative pack
freeze. A must persist extraction through C, refresh remapped evidence, record
assessments, seal manifests and freeze via the existing repositories. Source origin
and review status are copied from C and never promoted by semantic support.

Public source text is untrusted data. The services reject unresolved blocking
questions, duplicate canonical IDs, mismatched assessment statements/support,
unknown evidence and incompatible draft references. A supplies authorization,
profile/snapshot/model pins and budgets. Semantic model decisions remain fallible;
the synthetic tests and small live probe do not establish production quality.

`taxonomy_context.py` prepares interpretation input without changing stored
taxonomy or database retrieval. Model selections use short unique concept codes;
code validates these and maps them to canonical IDs before persistence. Every
concept, alias/ambiguity and directed broader/related relationship is retained.
Labels and edges use explicit column legends; UUID repetition, row timestamps
and repeated reviewer bookkeeping stay out of the prompt. It does not shortlist
by keywords, truncate meaning or increase model input limits.

`interpretation_response.py` accepts model display labels as strings/arrays.
Overlong wording is retained in search terms with a neutral short display fallback;
factual/reference validation is unchanged. `research_questions` are non-blocking
source questions; ambiguity in operator intent still requires clarification.

`extraction_batches.py` bounds source context and output cardinality, retains exact
literal records and distinct batch-local keys, and makes exclusions explicit.
Failed batches supply no claims; all-invalid batches still fail. Title metadata is
not a substitute for literal entity-name support. `query_planning.py` proposes
novel gap-driven queries; the workflow owns budgets, persistence and execution.

Need-fit payloads include only accepted claims and their canonical support; unrelated
retrieval text remains in coverage and cannot exhaust the fit model context.

Domain vocabulary is read from the pinned profile's `configuration.domain`; see
[profile onboarding](../../../docs/data/DOMAIN_PROFILES.md). Company fields use its
codes (unknown allowed), independent of topic/vector eligibility. Institutions in
draft entries are generic bounded source-supported names, not fixed pilot enums.
