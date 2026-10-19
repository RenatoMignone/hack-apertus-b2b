# Stregoni delivery checklist

**Product:** B to Bern (B2B).
**Team:** Renato Mignone, Elia Innocenti, Eric Ruiz Giménez, Mohamed Kechiche.
Prepared 19 October 2026. This is release preparation, not a submission receipt.

## Prepared in this documentation pass

- [x] Product/team overview in the root README, keeping organizer sections.
- [x] Judge entry point, setup routes and a practical walkthrough.
- [x] Architecture, model roles, evidence/review boundaries and source map.
- [x] Technical-report draft in the required root location.
- [x] Explicit verification scope, current limitations and hosting decision guide.

## Finish before submission

- [ ] Select and record the final release commit after integrating intended work.
  The documentation started at `072f099`; local ingestion/runtime edits are
  separate work and must be deliberately included or excluded.
- [ ] From a clean checkout, run the seeded UI route and the selected backend
  acceptance route. Record platform and passed/failed/skipped checks.
- [ ] Choose supervised local demo versus stable independent judge access; record
  the actual URL, availability window, login handoff and operator.
- [ ] Complete a permitted live case through quotations, review and PDF; record
  actual corpus/model pins, limitations and measured latency.
- [ ] If shown, verify PPTX/manual plans/own-case features on the actual deployment.
  Do not infer activation from source availability or old receipts.
- [ ] Verify the claimed target architecture. Until then retain the report's
  explicit statement that the air-gapped target is a design, not a demonstrated mode.
- [ ] Record a video of at most two minutes; verify access from a signed-out
  browser and place its URL in the top Demo field of the technical report.
- [ ] Export the final report as **`Stregoni_Report.pdf`** at repository root,
  render/inspect every page and verify the template's six-page limit excluding
  references. The current Markdown is a draft; pagination is not verified.
- [ ] Check current organizer form requirements, including any pitch PDF/ZIP rules.
  Historical instructions differ; use [submission provenance](../project/EVENT_AND_SUBMISSION.md).
- [ ] Confirm public repository access/template ancestry and review public
  contents for secrets and rights. Preserve supplied assets/transcript contents;
  code licensing does not grant redistribution rights for all third-party data.
- [ ] Submit through the official team flow and retain confirmation.

No final PDF, video, hosted URL, public-visibility change, commit or submission
is implied by this checklist. These actions need actual artifacts or receipts.

## Hosting decision

**Current fact, supplied by the team on 19 October:** PostgreSQL runs on a
member's computer. Stable external hosting has not been selected or provisioned.

For a supervised demonstration, the existing computer is usable if it stays awake,
the database/storage remain available and the API/worker have verified access.
Test the complete path from the demonstration device and retain the seeded UI
and video as clearly labeled fallbacks. A laptop-backed service is not an
independently available judge environment.

For judges to explore later without the team present, the recommendation is an
independent host for **API, background worker, PostgreSQL/pgvector, checkpoint DB
and artifact storage**, or an equivalent split across compatible services.
Keep database/storage connectivity private; expose the authenticated application
over HTTPS. Hosting only the frontend or only PostgreSQL does not deploy B2B.

Before choosing a managed database, verify required PostgreSQL/pgvector support,
extensions, role/RLS behavior, function/migration ownership and separate
checkpoint access. The current implementation cannot be assumed compatible with
every managed offering. Confirm storage API support and backup/restore as well.
PostgreSQL's [official authentication documentation](https://www.postgresql.org/docs/current/auth-pg-hba-conf.html)
explains host/database/user restrictions and TLS-only connection rules.
The private-service topology is a delivery recommendation, not a measured deployment.

The maintainer's migration path must preserve a validated database backup,
artifact package, IDs, grants, configuration pins and existing case/checkpoint
history. Stage the restore on the new target, verify exact source/artifact hashes,
owner isolation, case-to-export and restart/resume, then coordinate cutover.
Do not change the running ingestion host implicitly.

Any Swiss sovereign-cloud claim also needs verified operator, jurisdiction,
residency and runtime dependencies. Connected Keera/HF calls do not establish
that claim. Use [deployment](../data/DEPLOYMENT.md) and
[architecture target requirements](../plans/ARCHITECTURE.md#target-architecture-mandatory)
as acceptance references. No provider purchase, migration or infrastructure
change is authorized or performed by this preparation document.
