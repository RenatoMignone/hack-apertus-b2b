# Runtime access handoff — reported host results

18 October 2026 · Source: Eric’s handoff supplied by the user in this chat.
His commit `300c677` was not published: automatic approval review rejected the
push of operational metadata to an unverified remote. This is a reduced summary,
not a claim that his branch was fetched or his checks were repeated here.
Private bundles must be transferred privately, never committed.

| Area | Eric reports | Still needed |
| --- | --- | --- |
| Developer bundles | Separate protected bundles with DB/checkpoint credentials, tokens, pinned SSH key, HF JSON and tokenizer | Transfer each bundle to its intended developer; preserve individual identity/token |
| DB access | Both developer roles authenticate; own public scope is readable | Both remain in the fixture namespace with empty source scopes; pilot profile visibility/grants are pending |
| Checkpoints | Existing saver tables; separate non-owner runtime roles; synthetic saver writes/reads passed | Peer-side access; shared tables lack row isolation for direct DB credential holders |
| Artifacts | Bucket HEAD and actual synthetic content-addressed put/read passed; no delete permission | Read/integrity-check a real authorized source once available |
| Network | Host-local SSH self-check and pinned fingerprint match | Neither developer’s peer-side SSH is established by this report; Elia’s route failure remains unresolved |
| SSH policy | Bundle clients enforce keys and pin the host | Server still allows passwords and broad forwarding; administrator must validate keys before tightening policy |
| Corpus | Reviewed taxonomy and an in-progress unpublished trial profile exist | No published pilot snapshot/index build; no usable runtime profile pins |

No application migration, ingestion, corpus publication, restart or frontend change
was performed by Eric’s access task. He reports a narrow schema-revision read
grant, two retained synthetic checkpoint records and a synthetic artifact probe.
These are owner-reported host changes, not changes made by this integration.
Provider keys/quotas and real retrieval quality were not verified by that task.

## Next actions

1. Transfer private bundles and verify peer-side SSH from an approved network.
   A host self-check does not resolve another computer’s route or Wi-Fi isolation.
2. If Renato can connect from his terminal, let him lead live acceptance; his
   earlier Codex session was sandbox-blocked and did not establish working access.
3. Eric/admin validates server key-only/forwarding policy without interrupting
   working keys or ingestion. Confirm the intended shared-checkpoint trust model;
   application authorization does not isolate direct SQL credentials.
4. Corpus owner completes and reviews publication, then supplies exact profile,
   snapshot/build/taxonomy/config pins, source grants, coverage and a checked query.
   Do not relabel fixture identities or publish incomplete data to unblock tests.
5. Developers run the [readiness check](../data/LIVE_SETUP.md), verify a real source
   artifact, and run their own public case through review/PDF with agreed queue
   ownership. Checkpoint setup is already complete; do not rerun it.

The readiness checker’s SELECT on `alembic_version` depends on the reported host
grant; reproducible restricted-role deployment privileges should be reconciled by
the schema/configuration owner. No new migration is allocated here.
