"""Persist assessments and freeze supported packs; never infer semantic truth here."""
from uuid import uuid4

from sqlalchemy import insert, select

from backend.contracts.data import configuration_hash
from backend.contracts.pipeline import CaseInterpretation, ClaimAssessment, ReportEvidencePack
from backend.data import schema as t
from backend.data.database import require_scope, transaction
from backend.data.repositories.cases import CaseRepository


def eligible_evidence(connection, run, evidence_ids, manifest_id=None):
    requested = set(evidence_ids)
    snapshot = set(connection.execute(select(t.spans.c.evidence_id).join(t.snapshot_documents,
        t.snapshot_documents.c.document_version_id == t.spans.c.document_version_id).where(
        t.snapshot_documents.c.snapshot_id == run["snapshot_id"], t.spans.c.evidence_id.in_(requested))).scalars())
    local = set()
    if manifest_id:
        manifest = connection.execute(select(t.manifests).where(t.manifests.c.manifest_id == manifest_id)).mappings().one()
        if manifest["case_id"] != run["case_id"]:
            raise PermissionError("foreign case manifest")
        rows = connection.execute(select(t.spans, t.scopes.c.case_id).join(t.manifest_items,
            t.manifest_items.c.evidence_id == t.spans.c.evidence_id).join(t.scopes).where(
            t.manifest_items.c.manifest_id == manifest_id)).mappings().all()
        if manifest["manifest_hash"] != manifest_hash(run["case_id"], [row["evidence_id"] for row in rows]):
            raise ValueError("case evidence manifest hash mismatch")
        for row in rows:
            if row["case_id"] != run["case_id"]:
                raise PermissionError("foreign case evidence")
            require_scope(connection, row["scope_id"])
            local.add(row["evidence_id"])
    if not requested <= snapshot | local:
        raise PermissionError("evidence must belong to pinned snapshot or own case manifest")
    rows = connection.execute(select(t.spans).where(t.spans.c.evidence_id.in_(requested))).mappings().all()
    if len(rows) != len(requested):
        raise PermissionError("evidence unavailable")
    for row in rows:
        require_scope(connection, row["scope_id"])
    return rows


def manifest_hash(case_id, evidence_ids):
    return configuration_hash({"case_id": str(case_id), "evidence": sorted(str(key) for key in set(evidence_ids))})


class EvidenceRepository:
    def __init__(self, engine):
        self.engine = engine
        self.cases = CaseRepository(engine)

    def interpret(self, access, run_id, interpretation: CaseInterpretation):
        with transaction(self.engine, access) as connection:
            self.cases._run(connection, access, run_id)
            key = uuid4()
            connection.execute(insert(t.interpretations).values(interpretation_id=key, run_id=run_id,
                payload=interpretation.model_dump(mode="json")))
            return key

    def assess(self, access, run_id, assessment: ClaimAssessment):
        with transaction(self.engine, access) as connection:
            run = self.cases._run(connection, access, run_id)
            claim = connection.execute(select(t.claims).where(t.claims.c.claim_id == assessment.claim_id)).mappings().one()
            require_scope(connection, claim["scope_id"])
            scope = connection.execute(select(t.scopes).where(t.scopes.c.scope_id == claim["scope_id"])).mappings().one()
            if scope["kind"] == "case" and scope["case_id"] != run["case_id"]:
                raise PermissionError("foreign case claim")
            support = set(connection.execute(select(t.claim_evidence.c.evidence_id).where(
                t.claim_evidence.c.claim_id == assessment.claim_id, t.claim_evidence.c.relation == "supports")).scalars())
            if set(assessment.evidence_ids) != support:
                raise ValueError("assessment must cover exact claim support")
            key = uuid4()
            connection.execute(insert(t.assessments).values(assessment_id=key, run_id=run_id,
                claim_id=assessment.claim_id, status=assessment.status, payload=assessment.model_dump(mode="json")))
            return key

    def manifest(self, access, run_id, evidence_ids):
        with transaction(self.engine, access) as connection:
            run = self.cases._run(connection, access, run_id)
            rows = connection.execute(select(t.spans, t.scopes.c.case_id).join(t.scopes).where(
                t.spans.c.evidence_id.in_(evidence_ids))).mappings().all()
            if len(rows) != len(set(evidence_ids)) or any(row["case_id"] != run["case_id"] for row in rows):
                raise PermissionError("manifest requires own case evidence")
            for row in rows:
                require_scope(connection, row["scope_id"])
            key = uuid4()
            connection.execute(insert(t.manifests).values(manifest_id=key, case_id=run["case_id"],
                manifest_hash=manifest_hash(run["case_id"], evidence_ids)))
            for evidence_id in set(evidence_ids):
                connection.execute(insert(t.manifest_items).values(item_id=uuid4(), manifest_id=key, evidence_id=evidence_id))
            return key

    def freeze(self, access, run_id, pack: ReportEvidencePack, *, manifest_id=None):
        with transaction(self.engine, access) as connection:
            run = self.cases._run(connection, access, run_id)
            interpretation = connection.execute(select(t.interpretations.c.payload).where(
                t.interpretations.c.run_id == run_id)).scalar_one()
            if interpretation != pack.interpretation.model_dump(mode="json"):
                raise ValueError("pack interpretation differs from pinned run interpretation")
            evidence_ids = {key for claim in pack.claims for key in claim.evidence_ids}
            eligible_evidence(connection, run, evidence_ids, manifest_id)
            for claim in pack.claims:
                assessment = connection.execute(select(t.assessments).where(t.assessments.c.run_id == run_id,
                    t.assessments.c.claim_id == claim.claim_id)).mappings().one()
                if (assessment["status"] != "supported" or claim.text != assessment["payload"]["statement"]
                        or set(map(str, claim.evidence_ids)) != set(assessment["payload"]["evidence_ids"])):
                    raise ValueError("pack claim lacks supported assessment with exact evidence")
                # Shared claims must be part of the pinned snapshot; local claims stay local.
                scope = connection.execute(select(t.scopes).join(t.claims).where(
                    t.claims.c.claim_id == claim.claim_id)).mappings().one()
                if scope["kind"] == "case":
                    if scope["case_id"] != run["case_id"]:
                        raise PermissionError("foreign case claim")
                elif not connection.execute(select(t.snapshot_claims).where(
                    t.snapshot_claims.c.snapshot_id == run["snapshot_id"],
                    t.snapshot_claims.c.claim_id == claim.claim_id)).first():
                    raise PermissionError("claim absent from pinned snapshot")
            key = uuid4()
            body = pack.model_dump(mode="json")
            pins = {name: str(run[name]) for name in ("run_id", "input_id", "snapshot_id")}
            digest = configuration_hash({"payload": body, "pins": pins, "configuration": run["configuration"],
                "manifest_id": str(manifest_id) if manifest_id else None, "evidence": sorted(map(str, evidence_ids))})
            connection.execute(insert(t.packs).values(pack_id=key, run_id=run_id, input_id=run["input_id"],
                manifest_id=manifest_id, pack_hash=digest, payload=body))
            for evidence_id in evidence_ids:
                connection.execute(insert(t.pack_items).values(pack_id=key, evidence_id=evidence_id))
            for claim in pack.claims:
                connection.execute(insert(t.pack_claims).values(pack_id=key, claim_id=claim.claim_id))
            return key

    def read(self, access, run_id, evidence_ids, *, pack_id=None):
        """Authorized citation reads, including historical packs and case-local support."""
        with transaction(self.engine, access) as connection:
            run = connection.execute(select(t.runs).where(t.runs.c.run_id == run_id)).mappings().one()
            self.cases._case(connection, access, run["case_id"])
            manifest_id = None
            if pack_id:
                pack = connection.execute(select(t.packs).where(t.packs.c.pack_id == pack_id)).mappings().one()
                if pack["run_id"] != run_id:
                    raise PermissionError("pack belongs to another run")
                self.cases._validate_pack(connection, pack_id)
                membership = set(connection.execute(select(t.pack_items.c.evidence_id).where(
                    t.pack_items.c.pack_id == pack_id)).scalars())
                if not set(evidence_ids) <= membership:
                    raise PermissionError("citation absent from pack")
                manifest_id = pack["manifest_id"]
            rows = eligible_evidence(connection, run, evidence_ids, manifest_id)
            output = []
            for row in rows:
                version = connection.execute(select(t.versions, t.documents.c.canonical_url, t.scopes.c.kind)
                    .select_from(t.versions.join(t.documents).join(t.scopes, t.scopes.c.scope_id == t.versions.c.scope_id))
                    .where(t.versions.c.document_version_id == row["document_version_id"])).mappings().one()
                discovery = connection.execute(select(t.web_sources.c.payload).where(
                    t.web_sources.c.document_version_id == row["document_version_id"])).scalars().first()
                output.append({**dict(row), "title": version["title"], "url": version["canonical_url"],
                    "origin": "web" if version["kind"] == "case" else "corpus",
                    "review_status": "unreviewed" if version["kind"] == "case" else "curated",
                    "fetched_at": discovery["fetched_at"] if discovery else version["created_at"],
                    "published_at": discovery.get("published_at") if discovery else version["source_date"]})
            return output
