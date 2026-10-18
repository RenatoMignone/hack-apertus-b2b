# Keera comparison — 18 October 2026

**Measured, deliberately small diagnostic; not a model/retrieval benchmark.**
Used the supplied team key privately with the exact Keera aliases. No secret,
business plan, one-pager, database record or real company document was sent.
Fixtures are fictional laboratory text at `.invalid`, with deterministic IDs.

## Method

70B first, then 8B; identical synthetic ambiguity, extraction, three-statement
support/contradiction and pack-only writing inputs. Temperature 0, non-streaming,
1,800 output tokens/call, one repair/task, no model fallback, 90-second transport
timeout and no transient transport retry in the comparison. A known supported
claim, contradicted clinical-approval claim and unsupported collaboration claim
are assessed independently of extraction output so failures remain attributable.
Draft checks use the same fixed synthetic pack, not a claimed complete pipeline.

Initial probes exposed type-name wrappers and invalid local entity/object
references. The task now states root keys, gives a format-only extraction example
and supplies sanitized repair diagnostics. Validators were not weakened. The
last paired run below includes those changes and stricter lead/trace checks.

## Last paired run

| Task | 70B | 8B |
| --- | --- | --- |
| Ambiguity | Valid, blocking question; 2.640 s | Valid, blocking question; 1.324 s |
| Extraction | Valid JSON but **empty claims/entities**, missing an explicit capability; 1.240 s | Extracted the stated laboratory/capability; 1.747 s |
| Three claim statuses | All matched expected supported/contradicted/unsupported; 3.659 s | All matched expected statuses; 1.559 s |
| Draft | Valid references/schema; 2.621 s | Failed bounded structural/reference checks after repair; 2.909 s |
| Separate draft assessment | Rejected its draft's implied collaboration opportunity; 1.897 s | Not run because draft failed |
| Sequential task time | 12.057 s | 7.539 s (different number of completed stages) |
| Reported prompt/completion tokens | 5,004 / 739 | 5,689 / 1,127, including repairs |

Earlier probes produced different verdicts for similar wording. Some ambiguity
responses inferred medtech detail from a vague request; operator review and broader
interpretation evaluation remain needed. Valid schema is not extraction recall or
factual support. No price, sustained quota, concurrency, immutable weight revision,
native JSON Schema or statistically meaningful model accuracy was established.

## Tool proposal probe

One harmless `lookup_public_expertise(query)` proposal per non-thinking alias;
no tool executed. 8B returned a valid allowlisted proposal. 70B returned no tool
proposal. Both requests completed; this does not establish reliable 70B tool
selection. Thinking aliases are prevented from receiving tools locally and covered
by fixtures; no live thinking/tool combination was attempted.

## Recommendation and reproduction

**No overall winner or automatic default change.** 70B was more usable for these
draft/assessment calls but missed an obvious extraction fact. 8B was faster and
extracted useful content, but its draft did not satisfy the contract. Keep explicit
`LLM_NAME`; A can evaluate task-specific 70B routing after broader independently
reviewed cases. Neither model completed a verified full case in this diagnostic.

```bash
PYTHONPATH=src python -m backend.tests.intelligence.benchmark \
  --env-file /absolute/path/to/private.env \
  --output .local/intelligence/model-comparison.json
```

This opt-in script captures **synthetic output only** for debugging, never prompts,
keys or provider error bodies. Keep generated JSON local; do not reuse this recorder
for private cases. Production receipts expose only task/model, usage and timing.
Prompt/config changes require a newly labeled comparison, not silently replacing
reported results.
