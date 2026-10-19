# Evidence preparation

Extract local entity/claim proposals, persist canonical support and assess exact
statements against actual passages. Code validates identity/scope/literal hashes;
model services assess semantics and fit. Only supported claims enter the frozen
ReportEvidencePack; adjacent opportunities retain uncertainty.

Interpretation repair identifies missing blocking questions explicitly. Unresolved
operator ambiguity is preserved; unknown public facts remain research questions.

Read the [focused specification](../../../docs/plans/REPORT_PROCESSING_BOUNDARIES.md) and [module map](../../../docs/plans/MODULE_HANDOFFS.md).
Coordinate shared DTO/schema/configuration changes with their consumers and run
relevant boundary checks against isolated infrastructure.

Extraction uses at most six batches of twelve passages / 18,000 characters, two
model calls concurrently. Document round-robin selection pairs retrieved passages
with literal identity context before spending more budget on the same document.
Skipped support stays explicit; batch gaps never imply corpus-wide absence.
Model-only support/claim aliases resolve to exact supplied canonical IDs in code;
unknown references, invented identities and unsupported statements remain rejected.
Fit assesses needs independently and retains narrow capabilities without inventing
missing people, specifications or availability. A no-match pack records supported
and matched claim counts, distinguishing unresolved fit from absent source facts.
