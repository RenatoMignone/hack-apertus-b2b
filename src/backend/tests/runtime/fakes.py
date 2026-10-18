"""Explicit synthetic service fixtures. Never imported by production bootstrap."""
from collections import Counter
from uuid import uuid4

from sqlalchemy import insert, select

from backend.contracts.data import Span, configuration_hash
from backend.contracts.pipeline import (CaseInterpretation, ClaimAssessment, DraftAssessment, DraftReason,
    DraftRevision, ReportEvidencePack, SupportedClaim)
from backend.contracts.services import (ClaimCandidate, EntityCandidate, EvidenceAssessment, EvidenceRecord,
    ExtractionBatch, PersistedClaims, RegisteredResearch, ResearchBundle, WebResearchResult)
from backend.data import schema as t
from backend.data.admin import grant_scope
from backend.data.repositories.corpus import CorpusRepository


class FixtureReasoning:
    def __init__(self):
        self.calls = Counter()
        self.block = False
        self.bad_draft = False
        self.empty = False
        self.unsupported = False

    async def interpret(self, message, taxonomy_context, context):
        self.calls["interpret"] += 1
        return CaseInterpretation(company_name="Synthetic Company", company_summary="A synthetic sensor developer.",
            activity_label="glucose sensors", bern_intents=["Research in Bern"], needs=["sensor research"],
            search_terms=["glucose monitoring"], blocking_questions=["Which sensor application?"]
                if self.block and "Clarification:" not in message else [])

    async def extract(self, interpretation, research, context):
        self.calls["extract"] += 1
        if self.empty or not research.evidence:
            return ExtractionBatch(gaps=["No supported evidence"])
        record = research.evidence[0]
        return ExtractionBatch(entities=[EntityCandidate(key="unit", entity_type="unit", display_label="Synthetic unit",
            evidence_ids=[record.evidence_id])], claims=[ClaimCandidate(key="capability", subject_key="unit", predicate="capability",
            typed_literal={"type": "text", "value": record.literal_text}, statement=record.literal_text,
            evidence_ids=[record.evidence_id])])

    async def assess(self, claims, evidence, context):
        self.calls["assess"] += 1
        return EvidenceAssessment(assessments=[ClaimAssessment(claim_id=claim.claim_id, statement=claim.text,
            evidence_ids=claim.evidence_ids, status="unsupported" if self.unsupported else "supported",
            validator="synthetic-test", explanation="Synthetic fixture assertion, not a model benchmark") for claim in claims.claims])

    async def propose_pack(self, interpretation, claims, assessment, research, context):
        self.calls["pack"] += 1
        supported = {a.claim_id for a in assessment.assessments if a.status == "supported"}
        accepted = [claim for claim in claims.claims if claim.claim_id in supported]
        return ReportEvidencePack(interpretation=interpretation, claims=accepted,
            outcome="complete" if accepted else "no_match", gaps=[] if accepted else ["No supported match"])

    async def draft(self, pack, instruction, context):
        self.calls["draft"] += 1
        return DraftRevision(reasons=[DraftReason(id="reason1", headline="Synthetic research capability",
            text="Unverified invented wording" if self.bad_draft else pack.claims[0].text,
            claim_ids=[pack.claims[0].claim_id])] if pack.claims else [], change_note=instruction or "Initial draft")

    async def assess_draft(self, draft, pack, context):
        return DraftAssessment(draft_hash=configuration_hash(draft.model_dump(mode="json")),
            status="unsupported" if self.bad_draft else "supported", validator="synthetic-test",
            explanation="Synthetic fixture assessment, not semantic model validation")


class FixtureBackbone:
    def __init__(self, store, fixture):
        self.store, self.fixture = store, fixture
        self.calls = Counter()
        self.empty = False
        self.delay = 0

    async def taxonomy(self, context):
        return {"taxonomy_version_id": str(context.taxonomy_version_id), "concepts": []}

    async def retrieve(self, plan, context):
        import asyncio
        self.calls["retrieve"] += 1
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.empty:
            return ResearchBundle()
        with self.store.engine.connect() as c:
            ids = list(c.execute(select(t.spans.c.evidence_id).join(t.snapshot_documents,
                t.snapshot_documents.c.document_version_id == t.spans.c.document_version_id).where(
                t.snapshot_documents.c.snapshot_id == context.snapshot_id)).scalars())[:1]
        return ResearchBundle(evidence=await self.read_evidence(ids, context))

    async def register_research(self, result, context):
        self.calls["register"] += 1
        return RegisteredResearch()

    async def persist_extraction(self, batch, context):
        self.calls["persist"] += 1
        if not batch.claims:
            return PersistedClaims()
        scope, source = uuid4(), uuid4()
        with self.store.engine.begin() as c:
            c.execute(insert(t.scopes).values(scope_id=scope, kind="case", case_id=context.case_id, access_policy_id="test-only"))
            c.execute(insert(t.sources).values(source_id=source, scope_id=scope,
                canonical_origin="https://fixture.invalid", registry_ref="synthetic-copy-only"))
        grant_scope(self.store.engine, context.access.principal_id, scope, write=True)
        corpus = CorpusRepository(self.store.engine, self.store.artifacts)
        entities = {candidate.key: corpus.record_entity(context.access, scope_id=scope,
            entity_type=candidate.entity_type, display_label=candidate.display_label) for candidate in batch.entities}
        claims = []
        for candidate in batch.claims:
            records = await self.read_evidence(candidate.evidence_ids, context)
            record = records[0]
            body = record.literal_text
            version = corpus.stage_document(context.access, scope_id=scope, source_id=source, url=record.url,
                title=record.title, language=record.language, raw=body.encode(), body=body,
                spans=[Span(char_start=0, char_end=len(body), text=body)], parser_hash="synthetic-copy")
            with self.store.engine.connect() as c:
                evidence = c.execute(select(t.spans.c.evidence_id).where(t.spans.c.document_version_id == version)).scalar_one()
            claim = corpus.record_claim(context.access, scope_id=scope, subject_id=entities[candidate.subject_key],
                predicate=candidate.predicate, typed_literal=candidate.typed_literal,
                object_entity_id=entities.get(candidate.object_key), evidence_ids=[evidence])
            claims.append(SupportedClaim(claim_id=claim, text=candidate.statement, evidence_ids=[evidence]))
        return PersistedClaims(claims=claims, entity_ids=entities)

    async def read_evidence(self, evidence_ids, context):
        with self.store.engine.connect() as c:
            rows = c.execute(select(t.spans, t.versions.c.title, t.versions.c.body_hash, t.versions.c.language,
                t.documents.c.canonical_url, t.versions.c.source_date).select_from(
                t.spans.join(t.versions).join(t.documents)).where(t.spans.c.evidence_id.in_(evidence_ids))).mappings().all()
            return [EvidenceRecord(evidence_id=r["evidence_id"], document_version_id=r["document_version_id"], scope_id=r["scope_id"],
                title=r["title"], url=r["canonical_url"], language=r["language"], body_hash=r["body_hash"], char_start=r["char_start"],
                char_end=r["char_end"], literal_text=r["literal_text"], heading_path=r["heading_path"], page=r["page"],
                fetched_at=r["created_at"], published_at=r["source_date"], origin="corpus", review_status="curated") for r in rows]


class FixtureWeb:
    def __init__(self):
        self.calls = []
        self.delay = 0

    async def discover(self, query, context):
        import asyncio
        self.calls.append(query)
        if self.delay:
            await asyncio.sleep(self.delay)
        return []

    async def fetch(self, urls, context):
        return WebResearchResult(status="completed")


class FixturePdf:
    def __init__(self):
        self.report = None

    async def render(self, report):
        self.report = report
        assert report.claims and report.evidence
        return b"%PDF-1.4\nSynthetic registration fixture; renderer belongs to lane B."
