# Submission package

**B to Bern (B2B), Team Stregoni.** Verification is recorded in
[verification](VERIFICATION.md).

| Item | Requirement / location |
| --- | --- |
| Repository | Public template-based repository with a release commit identifying the submitted version |
| Technical report | [Source](../../technical_report.md); root `Stregoni_Report.pdf`, at most six pages excluding references |
| Demo video | Accessible URL in the report; at most two minutes |
| Application access | Provisioned live deployment or supervised demonstration with its run mode identified |
| Submission | Official team submission and confirmation |

A live deployment requires API, worker, PostgreSQL/pgvector, checkpoints, artifact
storage and configured model/search services. Shared access uses an authenticated
HTTPS application; database and storage remain private. A supervised team computer
requires the host and its service connections to remain available.

Connected Keera/HF operation and an air-gapped deployment are separate modes.
The latter requires packaged local dependencies and disabled egress. Deployment
and backup/restore procedures are in [deployment](../data/DEPLOYMENT.md) and
[Docker setup](DOCKER.md).
