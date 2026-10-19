# Prompt for Eric: activate optional case history and rich outputs

Run this on the shared host with the host owner's existing private environment.
No credentials or confidential company documents belong in the response or git.

> Read AGENTS.md, docs/project/STATUS.md, docs/team/COMPLETION_ROADMAP.md,
> docs/data/CASE_MEMORY.md and docs/data/RICH_OUTPUTS.md. Integrate current main
> without discarding any ingestion changes; use a clean worktree if needed.
> You own this shared-host migration/activation. Keep ingestion work and corpus
> publication separate; do not fabricate reviewed entities/tags or publish early.
>
> 1. Inspect current application Alembic revision and running services using the
>    existing private host configuration. Confirm the target is the intended
>    navigator DB, not the separate LangGraph DB. Record only non-secret status.
>    Capture a restorable database backup and confirm its restore procedure.
> 2. Review 0009_case_memory and 0010_rich_outputs. 0009 adds owner-isolated,
>    immutable, opt-in case vectors plus a 768-dimension HNSW index. 0010 adds
>    owner-isolated immutable manual business contexts bound to input revisions.
>    Existing corpus/ingestion tables/data are untouched. New exports reuse the
>    existing format column; no LangGraph/framework migration is needed.
> 3. Coordinate a brief application-worker pause, then apply the normal existing
>    application `navigator --env-file PRIVATE_HOST_ENV db-migrate` command using
>    the authorized maintainer identity. Do not use developer/admin fallback
>    credentials. Verify the resulting head is 0010_rich_outputs, repeated
>    migration is a no-op, existing source/claim/artifact counts are preserved,
>    and runtime roles inherit only the intended new table privileges/RLS.
>    If the lock timeout or any check fails, stop and report; do not widen grants
>    or disable triggers. Do not run this command on Elia/Renato's Mac.
> 4. Confirm the pinned encoder/configuration and tokenizer are provisioned on
>    each worker host. Use CASE_MEMORY_ENABLED=true and CASE_MEMORY_MIN_SCORE=50
>    only where ready. The threshold is uncalibrated, not a success probability.
>    Other vector dimensions need a separately reviewed index for large histories.
>    No existing case is automatically eligible. Do not index fictional Helvetic,
>    synthetic fixtures or generated pitches. Agency-wide sharing is deferred.
> 5. Provision the unchanged docs/provided_material/powerpoint_template.pptx
>    on each API/worker host (container path /app/assets/powerpoint_template.pptx).
>    Set RUNTIME_PPTX_TEMPLATE_PATH to it, RUNTIME_RICH_OUTPUTS_ENABLED=true,
>    and explicit updated RUNTIME_TEMPLATE_VERSION/RUNTIME_RENDERER_VERSION
>    identifying this template/export release. Preserve personal bindings, tokens,
>    checkpoint/MinIO credentials and other services. No secret in .env.example.
> 6. Restart API/workers on the same code/configuration. Restart/rebuild frontend.
>    Run check_runtime.py --env-file PRIVATE_RUNTIME_ENV --network for each
>    developer: it is read-only. Check authenticated capabilities and case detail
>    advertise the provisioned formats/manual/history controls. On an isolated
>    disposable test DB run the focused tests listed in LOCAL_ACCEPTANCE.md and
>    test_rich_outputs.py/test_case_memory.py. Do not use the shared host as the
>    disposable-test admin target or mix fixtures into its corpus/history.
> 7. Have each operator verify permitted manual plans on an authorized case,
>    new revision/review, PDF and PPTX download, exact citations and unchanged
>    old revisions. Opt in only a real reviewed permitted case; check owner
>    isolation and opt-out. No sensitive contents in the handoff. A real public
>    DB/web/Keera case and human retrieval labels remain separate acceptance work.
> 8. Update MIGRATION_STATUS.md and STATUS.md with measured revision, feature
>    flags, role/RLS checks, backup reference (no private path/credentials), tests
>    actually run and remaining gaps. Commit/push only non-secret documentation
>    and explicitly requested fixes. If rollback is needed, disable the two new
>    feature flags and run this compatible release's core workflow; do not
>    downgrade/delete immutable history. Report any failed migration/check before
>    changing infrastructure. Return concise per-user readiness and remaining work.

Until this completes, leave both optional flags false. Current code/readiness
accepts core head 0008 or additive 0009/0010; enabled features require their tables.
