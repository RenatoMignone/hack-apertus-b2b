# Submission readiness audit

19 October 2026. Read-only repository inspection before the README refresh.
Source documentation commit: `f53c4bc`; live remote inspection found
`main=072f099` and `codex/b2b-delivery-docs=f53c4bc`.
No deployment, tests, migration or submission was performed by this audit.

## Required delivery gaps

1. **Final technical-report PDF is absent.** No root `Stregoni_Report.pdf`
   exists. Finish the Markdown, export/render it and check the six-page limit
   excluding references. The required root files and code license already exist.
2. **Demo video URL is absent.** `technical_report.md` still says “Pending video
   URL.” The `demo/` folder and `demo.zip` are untracked scenario inputs, not a
   video. Record/upload a video of at most two minutes and insert its accessible URL.
3. **Delivery documentation is not on remote main.** It was pushed on
   `codex/b2b-delivery-docs`; integrate it into the actual submission branch.
   The subsequent README/Docker guide/audit changes also need deliberate release.
4. **Clean-checkout end-to-end judge run remains unverified.** The no-credential
   UI is scripted. Real research needs private identity/profile/corpus,
   checkpoints, storage, encoder assets and providers. Supply a permitted
   provisioning path or stable supervised/hosted judge access and verify it.
5. **The required deployment-target statement is not backed by acceptance.**
   The report selects an air-gapped target but explicitly says it is unverified.
   Demonstrate the selected target or agree a truthful alternative supported by
   the template/challenge. Connected providers do not prove Swiss residency.
6. **Public visibility/template ancestry and official submission are unverified.**
   Authenticated Git access does not establish anonymous access. The anonymous
   metadata check was unavailable. Confirm access and current form rules, then
   retain the submission receipt. Additional pitch/ZIP rules remain unconfirmed.

## Technical report still needs release-specific evidence

The Markdown already contains the product, architecture, model roles, data
boundaries, limitations and run instructions. It is not an empty template.
Its remaining gaps are:

- Replace draft/source-baseline language with the final release identity.
- Add the selected environment/hardware and actual model/configuration/corpus pins.
- Freeze a dated source inventory and per-family counts, exclusions and coverage.
- Provide reviewed quality results where available; otherwise retain the explicit
  statement that expert Recall@10 and factual-support percentages are unmeasured.
- Document measured latency and cost/resource basis, or bounded estimates with
  assumptions. No demonstrated cost per case or time-saving figure currently exists.
- Add the actual demo link and deployability acceptance outcome.
- Make the PDF self-contained: internal source-document links alone should not
  carry details essential to assess architecture, results and dependencies.

## Repository and product gaps

7. **Working host code is not fully versioned.** Many ingestion, enrichment,
   source-scope, transfer and configuration files are staged/untracked locally.
   Select and integrate intended changes, run their checks and leave unrelated
   work intact. A clean clone cannot reproduce uncommitted host behavior.
8. **Structured expert/unit results remain incomplete.** The local
   ingestion audit (`docs/data/ingestion/DELIVERABLES_AUDIT.md`, currently
   untracked) reports incomplete
   canonical identity resolution, cross-page relationship context and full
   field-level HTTP profiles. Reason cards alone do not demonstrate every required
   contact/role/affiliation/expertise/project/service field.
9. **Reviewed knowledge and retrieval evaluation remain incomplete.** The local
   web comparison (`docs/evaluation/web-reference-20261019/README.md`, currently
   untracked) is exploratory,
   not human-reviewed gold. Acquisition coverage does not establish accepted
   entities or semantic correctness. Review/map canonical identities and measure
   the challenge's 80% top-10 goal and wording variants independently.
10. **Docker delivery is partial.** Data and optional runtime Compose files exist,
    but no frontend service exists. The base runtime image lacks hosted-encoder
    supplemental dependencies and asset mounts. Model/corpus/identity
    provisioning is separate. See [Docker setup](DOCKER.md).
11. **Current-state documentation conflicts.** For example, `docs/README.md`
    calls head 0007, `src/backend/README.md` records 0008, status records later
    activation, and local capture receipts record 0011. Distinguish historical
    receipts from one authoritative release state and refresh entry points.
12. **Final regression/live acceptance receipt is missing for the chosen release.**
    Existing receipts cover different commits/environments. Repeat appropriate
    checks at the selected release and verify actual query → evidence → review →
    export, plus optional features if shown. Do not sum historical test counts.

The local ingestion audit also records a failed ARTORG PDF indexing and extraction
rejection/reference issues. These need explicit disposition and coverage caveats;
do not remove validation checks to claim completeness.

## Useful improvements, not extra organizer requirements

A redistributable sample output, screenshots and public-safe release manifest
would help judges. Automated CI would improve repeatability; no
`.github/workflows/` directory was present. Neither these additions nor external
database hosting is itself an explicit requirement in the local README.
A working, documented, accessible end-to-end path is the requirement.

Preserve supplied material/transcripts and review only intended public additions
for secrets and redistribution rights. This audit did not scan private secrets,
certify legal compliance or establish live provider quality.
