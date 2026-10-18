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
