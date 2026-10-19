# Delivery checklist

**B to Bern (B2B), Team Stregoni.** Current implementation and acceptance are in
[status](../project/STATUS.md); this page covers the final submission package.

- [ ] Select final main-branch release commit after intended integration.
- [ ] Verify clean-checkout UI setup and the chosen backend acceptance route.
- [ ] Confirm maintainer migration rollout, restart services and complete a fresh
  permitted case through source inspection, all-card review and PDF download.
- [ ] If demonstrated, verify actual PPTX/manual plans/own-case capabilities.
- [ ] Provide a stable supervised or independently hosted judge access route,
  with explicit availability and private credential handoff where needed.
- [ ] Demonstrate the selected deployment target or clearly retain its unverified
  status; connected Keera/HF does not establish air-gap or Swiss residency.
- [ ] Finalize [technical_report.md](../../technical_report.md), export root
  `Stregoni_Report.pdf`, inspect all pages and confirm six pages excluding references.
- [ ] Record an accessible video of at most two minutes; add URL to the report.
- [ ] Confirm current organizer form/pitch requirements, public repository access,
  template ancestry, secrets review and third-party material rights.
- [ ] Submit through the official team flow and retain confirmation.

The delivery documentation and My desk updates are merged locally into main;
final publication/release is a separate action. No missing video, PDF, hosted URL
or official submission is implied by a Markdown checklist.

For shared judge access, deploy API, worker, PostgreSQL/pgvector, checkpoints,
artifacts and required model/search dependencies together or through verified
private connectivity. Hosting only frontend or DB is insufficient. Keep storage/DB
private and expose the authenticated app over HTTPS. A team computer can support
a supervised demo if awake/reachable; it is not independently available hosting.

Infrastructure cutover requires a validated backup/restore preserving IDs, source
hashes, grants, pins and case/checkpoint history, followed by owner-isolation and
case/export/recovery checks. See [deployment](../data/DEPLOYMENT.md) and
[Docker setup](DOCKER.md). No infrastructure purchase or migration follows
implicitly from this checklist.
