# Corpus review and tagging

19 October 2026. `python -m backend.ingestion.review_cli --help` exports pending
entity/claim candidates with literal sources, hashes and URLs. It is read-only
unless `--apply` is explicitly supplied with a reviewed manifest. A public-scope
writer is required to apply; runtime developer credentials do not gain privileges.

```text
python -m backend.ingestion.review_cli --env-file PRIVATE_INGESTION_ENV --principal PRINCIPAL_UUID --namespace NAMESPACE --scope SCOPE_UUID --output .local/review-candidates.json
python -m backend.ingestion.review_cli --env-file PRIVATE_INGESTION_ENV --principal PRINCIPAL_UUID --namespace NAMESPACE --scope SCOPE_UUID --manifest .local/reviewed-decisions.json
# Same reviewed command plus --apply writes the checked batch atomically.
```

Build the manifest explicitly; export does not propose acceptance:

```json
{
  "schema_version": 1,
  "scope_id": "SCOPE_UUID",
  "reviewer": "Actual reviewer identifier",
  "decisions": [{
    "kind": "claim",
    "record_id": "EXPORTED_UUID",
    "expected_hash": "EXPORTED_SHA256",
    "decision": "accepted",
    "justification": "Explain semantic support after checking all supplied passages.",
    "semantic_support_confirmed": true
  }],
  "tags": [{
    "concept_id": "REVIEWED_CONCEPT_UUID",
    "evidence_id": "EXACT_SUPPORT_UUID",
    "mapping_kind": "direct",
    "justification": "Why this passage supports the topic.",
    "semantic_support_confirmed": true
  }]
}
```

Entities must have literally supported names. Accepted claims need accepted
subject/object identities, either already accepted or reviewed in the same batch.
Source body hashes, exact offsets, scope membership and optimistic record hashes
are checked in both dry-run/apply. Contradictory support cannot be bulk accepted.
A source-integrity pass does not establish semantic truth: the reviewer must
confirm that the complete relationship/value is supported.

Claims/support links are immutable: review inserts a successor with `supersedes_id`
and provenance, never changes old claim bytes or frozen memberships. Reapplying
an identical review is idempotent. A different review of an already superseded
claim is rejected. Entity status can advance while its identity remains unchanged.
Tags resolve existing reviewed concepts and exact source passages; topic budgets
are bounded, and no vocabulary branch is invented.

This does not publish or rebuild snapshots, edit documents, merge identities or
accept an entire extraction batch automatically. Eric coordinates real-corpus
application and subsequent capture/publication. Test fixtures alone are not a
review of his 6,069 pending claims. No shared-host command was applied here.
