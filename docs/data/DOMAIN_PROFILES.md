# Domain-independent profiles

19 October 2026. The orchestration, evidence assessment and draft/export pipeline
use generic contracts. Medtech is the default vocabulary, not a hardcoded enum
on company fields or draft institutions. `CompanyField` remains a compatibility
constant for old callers; new processing fields accept profile-defined codes.

A corpus owner creates a **new immutable taxonomy profile version**, recalculating
its configuration hash, with this optional `configuration.domain` object:

```json
{"version":"materials-v1","fields":{"materials":"Materials science","manufacturing":"Manufacturing"},"institutions":{"Empa":"Empa"}}
```

The pinned profile is delivered with the reviewed taxonomy to interpretation.
Field outputs must belong to its vocabulary; `unknown`/`other` always remain valid.
Institution names in draft entries still require cited source support and separate
semantic assessment; configuration is not evidence of affiliation. New values do
not become vector prefilters. Taxonomy concepts/aliases/relations retain canonical
IDs, independent review, versioning and unknown/unmapped terms.

Onboarding another domain requires authorized sources, a reviewed taxonomy and
new profile/snapshot (or explicit live capture), then compatible embedding/index
builds. A different encoder requires re-embedding and rebuilding; labels alone do
not make an existing RAG corpus cover a new subject. No shared data is changed by
this feature. Default pilot configuration remains backward compatible.

Current HTTP badges remain UniBE/ARTORG/DCB/Other for frontend compatibility;
unknown institutions project to Other with the exact `institutionLabel` retained.
The frontend owner can adopt that optional label and a neutral badge. PDF/PPTX
render source-supported names directly. No frontend files changed.

Verification: a materials/manufacturing profile passes actual structured service
validation with synthetic model output; unsupplied field codes are rejected.
This checks portability, not new-domain corpus coverage or model quality.
