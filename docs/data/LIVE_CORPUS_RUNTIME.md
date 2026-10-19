# Live captures and published releases

`RUNTIME_CORPUS_MODE=live` lets new cases use ready authorized chunks while
collection/enrichment continues. The application creates immutable case-owned
snapshot/build membership, pinning source versions, profile/taxonomy and the
compatible embedding configuration. It does not mutate the shared active release.
New runs can see later ingestion; resume and wording edits keep their capture.
Incomplete coverage is explicit as `live_corpus_incomplete_coverage`.

`RUNTIME_CORPUS_MODE=published` resolves the reviewed active release. Publication
checks source-family coverage, support and compatibility before atomically moving
the active pointer. A completed release is optional for live development, but a
real accessible profile, taxonomy, compatible vectors and scope grants are required
in both modes. An empty authorized view is not proof the whole database is empty.

`navigator_runtime` provides corpus reads and owned case writes; corpus writers
retain separate privileges. Case-scope provisioning is owner-checked. Neither a
profile UUID nor runtime flag bypasses RLS. Source revocation still affects reads,
exports and downloads. Historical packs retain lineage without republishing facts.

Migrations 0008, 0011 and 0012 supply live capture, capture-performance and
membership-policy changes. API startup never applies them. See
[deployment](DEPLOYMENT.md), [performance](CAPTURE_PERFORMANCE.md) and
[case lineage](CASE_STATE_AND_LINEAGE.md).
