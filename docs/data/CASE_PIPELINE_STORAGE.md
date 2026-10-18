# Case pipeline persistence additions

**18 October 2026 · U8/D16; supplements the physical schema and lineage specs.**
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
| `cases.action_items` | Action ID → case; question, ask role, open/asked/done |
| `cases.reviews` | Exact result and immutable selection hash; approval is not truth validation |
| `cases.exports` | Existing export lineage plus format; PDF first, PPTX later |

Reuse existing entities/claims for organizations, institutes, companies, people,
units, projects, facilities and services. Relations are supported predicates, not
a separate graph database. Public companies are distinct from private case history.
Existing input revisions, dialogue, runs, questions/answers, plans/rounds/hits,
matches/support, manifests/items, packs/items/claims and result revisions remain.
Old match selections are retained as legacy data; never guess reason mappings.

Pack membership is exactly pinned snapshot support plus a sealed, case-owned
manifest. Live evidence is stored in case scopes and never mutates the snapshot.
All pack claims require an explicit supported assessment in that run and all
support IDs must be members. Source `unreviewed` is independent of claim support.
An empty supported-claim list is valid only with an explicit partial/no-match
limitation. No semantic validator is implemented by storage.

Draft persistence requires a supported `DraftAssessment` of the exact draft hash;
the stored result includes that validator assertion. Live semantic validation is
not supplied by this change. Reason revisions link claims to existing frontend cards. Carry editorial choices
only for identical content/support hashes; changed cards reset to none. Every
card must be reviewed and at least one kept before an accepted review/export.
Review hashes include the selection set; selection changes stale old exports.
Readers recheck access/revocation even for historical packs and artifacts.

Forward migration `0004_case_pipeline` preserves existing data and installs new
RLS/immutable guards and app-role grants. Migration 0001 must create only its
original tables (exclude U8 tables), because it currently imports live metadata;
0004 adds new tables/columns for both fresh and existing databases. Old untyped
packs/results remain readable for audit but cannot gain a new accepted approval
or export through the v2 reason workflow without validated content.
