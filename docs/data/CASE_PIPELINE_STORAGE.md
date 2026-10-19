# Case pipeline persistence

**18 October 2026 · Final schema contract v1 (D18); U8/D16 processing retained.**
Additive [integration changes](../team/INTEGRATION.md) advance head to
`0007_frontend_lifecycle`: 0006 adds restricted case-scope provisioning/private
runtime RLS, and 0007 adds independent case hold/outcome fields and action notes.
Optional [own-case memory](CASE_MEMORY.md) adds 0009; [manual plans and PPTX](RICH_OUTPUTS.md)
advance source head to `0010_rich_outputs`. Shared 0008 remains supported while disabled. Historical migrations stay frozen; the shared host has not been migrated here.
One `navigator` database retains `corpus`, `taxonomy`, `retrieval`, `cases`, `ops`.
LangGraph and Langfuse retain their own databases/stores. No three application
DBs or cross-database foreign keys are introduced.

| Table | Identity / links / responsibility |
| --- | --- |
| `cases.interpretations` | Immutable interpretation ID → run/input; typed output and pinned taxonomy |
| `cases.web_research` | Research ID → run; query, mode, state, failures and budgets |
| `cases.web_sources` | Discovery ID → research; normalized source, case document version or duplicate corpus version, outcome |
| `cases.claim_assessments` | Assessment ID → run/claim; supported/unsupported/contradicted, evidence IDs and validator identity |
| `cases.draft_reasons` | Reason row ID, stable reason key → result; content/support hash and typed payload |
| `cases.reason_claims` | Reason row → validated corpus claim IDs |
| `cases.reason_selections` | One current editorial selection per reason row; kept/rejected/none; reviewer/time |
| `cases.action_items` | Action ID → case; question, ask role, open/asked/done and optional answer note |
| `cases.reviews` | Exact result and immutable selection hash; approval is not truth validation |
| `cases.exports` | Existing export lineage plus format; reviewed PDF or provisioned PPTX |

Reuse existing entities/claims for organizations, institutes, companies, people,
units, projects, facilities and services. Relations are supported predicates, not
a separate graph database. Public companies are distinct from private case history.
Input revisions, dialogue, runs, questions/answers, manifests/items, packs/items/claims
and result revisions remain. Plans/round observations live in durable stage outputs;
entity matches live in the frozen pack. Removed match selections have no mapping
to reason cards; populated old tables are preserved only in the maintainer archive.

Pack membership is exactly pinned snapshot support plus a sealed, case-owned
manifest. Live evidence is stored in case scopes and never mutates the snapshot.
All pack claims require an explicit supported assessment in that run and all
support IDs must be members. Source `unreviewed` is independent of claim support.
An empty supported-claim list is valid only with an explicit partial/no-match
limitation. No semantic validator is implemented by storage.

Draft persistence requires a supported `DraftAssessment` of the exact draft hash;
the stored result includes that validator assertion. Model-backed semantic adapters
are now integrated; their quality is not established by persistence tests.
Reason revisions link claims to existing frontend cards. Carry editorial choices
only for identical content/support hashes; changed cards reset to none. Every
card must be reviewed and at least one kept before an accepted review/export.
Review hashes include the selection set; selection changes stale old exports.
Readers recheck access/revocation even for historical packs and artifacts.

Migration `0004_case_pipeline` added this workflow; `0005_finalize_schema` retires
the duplicate older workflow and finalizes active tables. Fresh and upgraded
databases expose the same [exact application schema](SCHEMA_REFERENCE.md).
Historical migrations use frozen metadata. Old untyped packs/results remain
readable for audit but cannot gain a new accepted approval/export without
validated v2 content. See [upgrade rules](RELATIONAL_SCHEMA.md#removed-structures-and-upgrade-behavior).
