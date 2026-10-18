import asyncio
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import insert, select

from backend.contracts.data import Span, content_hash
from backend.contracts.pipeline import FetchedSource
from backend.contracts.services import (BackboneServices, EntityCandidate, ClaimCandidate, ExtractionBatch,
    EvidenceRejected, RunContext, WebResearchResult)
from backend.data import schema as tables
from backend.data.admin import grant_scope, revoke_scope
from backend.data.backbone import create_backbone
from backend.data.fixtures import FIXTURE_MODEL, FixtureEmbedder
from backend.data.repositories.corpus import CorpusRepository
from backend.data.repositories.snapshots import SnapshotRepository
from backend.ingestion.mesh import MeSHTagger, category_tags, mesh_vocabulary
from backend.ingestion.classification import SpecificSubject, SubjectAttribute
from backend.ingestion.normalize import normalize
from backend.ingestion.pipeline import CorpusBuilder
from backend.ingestion.registry import RegistryImporter
from backend.ingestion.web import FetchObservation
from backend.tests.test_database import context, make_run, plan_for

pytestmark = pytest.mark.integration


def setup_service(database, corpus):
    fixture, artifacts = corpus
    access = context(fixture)
    _, case_id, input_id, run_id, _ = make_run(database, fixture)
    scope_id = uuid4()
    with database.begin() as connection:
        connection.execute(insert(tables.scopes).values(scope_id=scope_id, kind="case", case_id=case_id, access_policy_id="case-test"))
    grant_scope(database, access.principal_id, scope_id, write=True)
    plan = plan_for(database, fixture)
    run_context = RunContext(access=access, case_id=case_id, input_id=input_id, run_id=run_id,
        snapshot_id=plan.snapshot_id, profile_id=plan.profile_id, taxonomy_version_id=plan.taxonomy_version_id,
        build_id=plan.build_id, embedding_config_hash=plan.embedding_config_hash, mode="connected",
        deadline_at=datetime.now(timezone.utc) + timedelta(minutes=5), request_id="test-backbone")
    service = create_backbone(database, artifacts, FixtureEmbedder())
    return fixture, scope_id, plan, run_context, service


def test_service_projects_real_records_and_checks_pins(database, corpus):
    fixture, scope, plan, run_context, service = setup_service(database, corpus)
    assert isinstance(service, BackboneServices)
    result = asyncio.run(service.retrieve(plan, run_context))
    assert len(result.evidence) == 4
    assert all(item.origin == "corpus" and item.review_status == "curated" for item in result.evidence)
    assert all(item.published_at is None for item in result.evidence)
    assert "reranker_unavailable" in result.limitations
    with pytest.raises(EvidenceRejected):
        asyncio.run(service.retrieve(plan.model_copy(update={"build_id": uuid4()}), run_context))
    revoke_scope(database, UUID(fixture["scope_id"]))
    with pytest.raises(EvidenceRejected):
        asyncio.run(service.read_evidence([result.evidence[0].evidence_id], run_context))


def test_new_extraction_mirrors_shared_evidence_and_preserves_origin(database, corpus):
    fixture, scope, plan, run_context, service = setup_service(database, corpus)
    result = asyncio.run(service.retrieve(plan, run_context))
    original = result.evidence[0]
    label = original.literal_text.split()[0]
    batch = ExtractionBatch(entities=[EntityCandidate(key="unit", entity_type="unit", display_label=label,
        evidence_ids=[original.evidence_id])], claims=[ClaimCandidate(key="capability", subject_key="unit",
            predicate="capability", typed_literal={"type": "text", "value": original.literal_text},
            statement=original.literal_text, evidence_ids=[original.evidence_id])])
    persisted = asyncio.run(service.persist_extraction(batch, run_context))
    repeated = asyncio.run(service.persist_extraction(batch, run_context))
    assert persisted == repeated
    claim = persisted.claims[0]
    assert claim.evidence_ids != [original.evidence_id]
    mirror = asyncio.run(service.read_evidence(claim.evidence_ids, run_context))[0]
    assert mirror.scope_id == scope
    assert mirror.origin == "corpus" and mirror.review_status == "curated"
    assert mirror.literal_text == original.literal_text and mirror.body_hash == original.body_hash
    with database.connect() as connection:
        stored = connection.execute(select(tables.claims).where(tables.claims.c.claim_id == claim.claim_id)).mappings().one()
        assert stored["status"] == "needs_review"
        assert connection.execute(select(tables.claim_evidence.c.review_decision).where(
            tables.claim_evidence.c.claim_id == claim.claim_id)).scalar_one() == "needs_review"
    revoke_scope(database, UUID(fixture["scope_id"]))
    with pytest.raises(EvidenceRejected):
        asyncio.run(service.read_evidence(claim.evidence_ids, run_context))


def test_foreign_evidence_and_unsubstantiated_entity_labels_rejected(database, corpus):
    _, _, plan, run_context, service = setup_service(database, corpus)
    records = asyncio.run(service.retrieve(plan, run_context)).evidence
    with pytest.raises(EvidenceRejected):
        asyncio.run(service.read_evidence([uuid4()], run_context))
    batch = ExtractionBatch(entities=[EntityCandidate(key="bad", entity_type="person", display_label="Invented Person",
        evidence_ids=[records[0].evidence_id])])
    with pytest.raises(EvidenceRejected):
        asyncio.run(service.persist_extraction(batch, run_context))


def test_registration_whole_snapshot_alias_preference_and_web_flags(database, corpus):
    _, scope, plan, run_context, service = setup_service(database, corpus)
    records = asyncio.run(service.retrieve(plan, run_context)).evidence
    original = records[-1]
    alias = "https://fixture.invalid/an-alias-not-used-in-retrieval"
    with database.begin() as connection:
        document_id = connection.execute(select(tables.versions.c.document_id).where(
            tables.versions.c.document_version_id == original.document_version_id)).scalar_one()
        connection.execute(insert(tables.aliases).values(alias_id=uuid4(), document_id=document_id, url=alias))
    page = FetchedSource(title="Live changed page", url=alias, canonical_url=alias, content="Changed live text",
        content_hash=content_hash(b"Changed live text"), fetched_at=datetime.now(timezone.utc))
    registered = asyncio.run(service.register_research(WebResearchResult(status="completed", sources=[page, page]), run_context))
    assert registered.evidence[0].document_version_id == original.document_version_id
    assert "duplicate_research_source_deduplicated" in registered.limitations
    assert registered.evidence[0].literal_text == original.literal_text
    fresh = page.model_copy(update={"url": "https://new.example.org/page", "canonical_url": "https://new.example.org/page"})
    registered = asyncio.run(service.register_research(WebResearchResult(status="completed", sources=[fresh]), run_context))
    assert registered.evidence[0].scope_id == scope
    assert registered.evidence[0].origin == "web" and registered.evidence[0].review_status == "unreviewed"
    with pytest.raises(EvidenceRejected):
        asyncio.run(service.register_research(WebResearchResult(status="completed", sources=[fresh]),
            run_context.model_copy(update={"mode": "offline"})))


class BuildEmbedder(FixtureEmbedder):
    def accepts_document(self, text, title="none", headings=""):
        return len(text) <= 2400

    def document_input(self, text, title="none", headings=""):
        return FIXTURE_MODEL.document_template.format(text=text, title=title, headings=headings)

    def embed_documents(self, inputs):
        return [self.embed_query(value) for value in inputs]


def test_registry_ingestion_and_versions_are_idempotent(database, corpus):
    fixture, artifacts = corpus
    access, scope = context(fixture), UUID(fixture["scope_id"])
    registry = RegistryImporter(database)
    source = registry.source(access, scope, "https://example.org", ["UniBE", "ARTORG"], "test-registry")
    assert source == registry.source(access, scope, "https://example.org", ["UniBE", "ARTORG"], "test-registry")
    observation = FetchObservation("https://example.org/old", "https://example.org/lab", b'<html lang="en"><title>Lab</title><p>Lab develops glucose technology.</p></html>',
        "text/html", 200, datetime.now(timezone.utc))
    builder = CorpusBuilder(database, artifacts, BuildEmbedder(), FIXTURE_MODEL)
    first = builder.ingest(access, scope_id=scope, source_id=source, observation=observation)
    second = builder.ingest(access, scope_id=scope, source_id=source, observation=observation)
    assert first["version_id"] == second["version_id"] and first["chunk_ids"] == second["chunk_ids"]
    assert first["published_at"] is None
    with pytest.raises(ValueError, match="reviewed"):
        builder.publish(access, [first], profile_id=UUID(fixture["profile_id"]), taxonomy_version_id=UUID(fixture["taxonomy_version_id"]))


def small_mesh():
    labels = {"C": "Diseases", "E": "Techniques"}
    raw = b"Endocrine System Diseases;C19\nDiabetes Mellitus;C19.246\nEquipment and Supplies;E07\n"
    return raw, {"name": "mesh-category-subcategory", "version": "test-" + uuid4().hex, "release": "2026",
        "source_url": "https://nlmpubs.nlm.nih.gov/mesh-test", "source_sha256": content_hash(raw), "category_labels": labels}


def test_mesh_import_keeps_only_two_levels_and_assigns_supported_tags(database, corpus):
    fixture, _ = corpus
    access = context(fixture)
    raw, manifest = small_mesh()
    vocabulary = mesh_vocabulary(raw, manifest)
    assert {item["code"] for item in vocabulary["concepts"]} == {"C", "C19", "E", "E07", "unknown"}
    assert category_tags(["C19.246.267", "E07"], vocabulary) == ["C", "C19", "E", "E07"]
    registry = RegistryImporter(database)
    imported = registry.profile(access, vocabulary, reviewer="test-reviewer")
    assert imported == registry.profile(access, vocabulary, reviewer="test-reviewer")
    altered = {**vocabulary, "tag_levels": ["deeper"]}
    with pytest.raises(ValueError, match="immutable"):
        registry.profile(access, altered, reviewer="test-reviewer")
    with database.connect() as connection:
        evidence = connection.execute(select(tables.spans).where(tables.spans.c.scope_id == UUID(fixture["scope_id"]))).mappings().first()
    tagger = MeSHTagger(database)
    proposals = [{"code": "C19", "span": Span(char_start=evidence["char_start"], char_end=evidence["char_end"], text=evidence["literal_text"])}]
    tags = tagger.assign(access, evidence["document_version_id"], imported["taxonomy_version_id"], proposals, reviewer="test-curator")
    assert len(tags) == 2
    assert tags == tagger.assign(access, evidence["document_version_id"], imported["taxonomy_version_id"], proposals, reviewer="test-curator")
    with pytest.raises(ValueError, match="only MeSH"):
        tagger.assign(access, evidence["document_version_id"], imported["taxonomy_version_id"],
            [{**proposals[0], "code": "C19.246"}])


def test_graph_relationships_have_complete_pinned_support(database, corpus):
    fixture, artifacts = corpus
    access = context(fixture)
    repository = CorpusRepository(database, artifacts)
    scope = UUID(fixture["scope_id"])
    with database.connect() as connection:
        evidence = connection.execute(select(tables.spans).where(tables.spans.c.scope_id == scope)).mappings().first()
    subject = repository.record_entity(access, scope_id=scope, entity_type="unit", display_label=evidence["literal_text"].split()[0])
    organization = repository.record_entity(access, scope_id=scope, entity_type="organization", display_label="Synthetic University")
    relationship = repository.record_claim(access, scope_id=scope, subject_id=subject, predicate="part_of",
        object_entity_id=organization, evidence_ids=[evidence["evidence_id"]], accepted=True)
    snapshots = SnapshotRepository(database)
    with database.connect() as connection:
        old = connection.execute(select(tables.snapshots).where(tables.snapshots.c.snapshot_id == UUID(fixture["snapshot_id"]))).mappings().one()
        build = connection.execute(select(tables.builds).where(tables.builds.c.build_id == old["build_id"])).mappings().one()
    with pytest.raises(ValueError, match="subject/object"):
        snapshots.stage(access, profile_id=old["profile_id"], taxonomy_version_id=old["taxonomy_version_id"], config_id=build["config_id"],
            chunk_ids=list(map(UUID, fixture["chunk_ids"])), chunker_hash=build["chunker_hash"], entity_ids=[subject], claim_ids=[relationship])
    snapshot_id = snapshots.stage(access, profile_id=old["profile_id"], taxonomy_version_id=old["taxonomy_version_id"], config_id=build["config_id"],
        chunk_ids=list(map(UUID, fixture["chunk_ids"])), chunker_hash=build["chunker_hash"], entity_ids=[subject, organization], claim_ids=[relationship])
    snapshots.publish(access, snapshot_id, expected_active=old["snapshot_id"])
    fixture["snapshot_id"] = str(snapshot_id)
    _, _, plan, run_context, service = setup_service(database, (fixture, artifacts))
    bundle = asyncio.run(service.retrieve(plan, run_context))
    assert {row["entity_id"] for row in bundle.existing_entities} == {subject, organization}
    assert all(row["claims"][0]["claim_id"] == relationship for row in bundle.existing_entities)
    with database.connect() as connection:
        excluded = connection.execute(select(tables.versions.c.document_id).where(
            tables.versions.c.document_version_id == evidence["document_version_id"])).scalar_one()
    bundle = asyncio.run(service.retrieve(plan.model_copy(update={"excluded_document_ids": [excluded]}), run_context))
    assert not bundle.existing_entities


def test_exact_shared_claim_reuse_preserves_canonical_identity(database, corpus):
    fixture, artifacts = corpus
    access = context(fixture)
    repository = CorpusRepository(database, artifacts)
    scope = UUID(fixture["scope_id"])
    with database.connect() as connection:
        evidence = connection.execute(select(tables.spans).where(tables.spans.c.scope_id == scope)).mappings().first()
        old = connection.execute(select(tables.snapshots).where(tables.snapshots.c.snapshot_id == UUID(fixture["snapshot_id"]))).mappings().one()
        build = connection.execute(select(tables.builds).where(tables.builds.c.build_id == old["build_id"])).mappings().one()
    subject = repository.record_entity(access, scope_id=scope, entity_type="unit", display_label=evidence["literal_text"].split()[0])
    literal = {"type": "text", "value": evidence["literal_text"]}
    claim_id = repository.record_claim(access, scope_id=scope, subject_id=subject, predicate="capability", typed_literal=literal,
        evidence_ids=[evidence["evidence_id"]], accepted=True)
    snapshots = SnapshotRepository(database)
    snapshot_id = snapshots.stage(access, profile_id=old["profile_id"], taxonomy_version_id=old["taxonomy_version_id"], config_id=build["config_id"],
        chunk_ids=list(map(UUID, fixture["chunk_ids"])), chunker_hash=build["chunker_hash"], entity_ids=[subject], claim_ids=[claim_id])
    snapshots.publish(access, snapshot_id, expected_active=old["snapshot_id"])
    fixture["snapshot_id"] = str(snapshot_id)
    _, _, _, run_context, service = setup_service(database, (fixture, artifacts))
    batch = ExtractionBatch(entities=[EntityCandidate(key="unit", entity_type="unit", display_label=evidence["literal_text"].split()[0],
        existing_entity_id=subject, evidence_ids=[evidence["evidence_id"]])], claims=[ClaimCandidate(key="exact", subject_key="unit", predicate="capability",
            typed_literal=literal, statement=evidence["literal_text"], evidence_ids=[evidence["evidence_id"]])])
    saved = asyncio.run(service.persist_extraction(batch, run_context))
    assert saved.claims[0].claim_id == claim_id
    assert saved.claims[0].evidence_ids == [evidence["evidence_id"]]


def test_multilabel_budget_and_tier_three_subjects_are_source_backed(database, corpus):
    fixture, _ = corpus
    access = context(fixture)
    raw, manifest = small_mesh()
    raw += b"Cardiovascular Diseases;C14\nNeoplasms;C04\nBacterial Infections;C01\n"
    manifest["source_sha256"] = content_hash(raw)
    vocabulary = mesh_vocabulary(raw, manifest)
    pins = RegistryImporter(database).profile(access, vocabulary, reviewer="fixture-curator")
    with database.connect() as connection:
        evidence = connection.execute(select(tables.spans).where(tables.spans.c.scope_id == UUID(fixture["scope_id"]))).mappings().first()
    span = Span(char_start=evidence["char_start"], char_end=evidence["char_end"], text=evidence["literal_text"])
    tagger = MeSHTagger(database)
    subject = SpecificSubject(name=span.text.split()[0], kind="research subject", span=span,
        attributes=[SubjectAttribute(name="explicit phrase", value=span.text, span=span)])
    tags = tagger.assign(access, evidence["document_version_id"], pins["taxonomy_version_id"],
        [{"code": code, "span": span} for code in ["C19", "C14", "E07"]], subjects=[subject])
    assert len(tags) == 5
    with database.connect() as connection:
        assert set(connection.execute(select(tables.assignments.c.status).where(tables.assignments.c.assignment_id.in_(tags))).scalars()) == {"needs_review"}
        stored = connection.execute(select(tables.derivations.c.inputs).where(tables.derivations.c.inputs["kind"].astext == "specific_subject",
            tables.derivations.c.inputs["version_id"].astext == str(evidence["document_version_id"]))).scalars().one()
        assert stored["name"] == subject.name and stored["subject_kind"] == subject.kind
        assert stored["evidence_id"] and stored["attributes"][0]["evidence_id"]
    with pytest.raises(ValueError, match="accumulated"):
        tagger.assign(access, evidence["document_version_id"], pins["taxonomy_version_id"], [{"code": "C04", "span": span}])
    with pytest.raises(ValueError, match="budget"):
        tagger.assign(access, evidence["document_version_id"], pins["taxonomy_version_id"],
            [{"code": code, "span": span} for code in ["C19", "C14", "E07", "C04"]])
    bad = subject.model_copy(update={"name": "Fabricated CT prototype"})
    with pytest.raises(ValueError, match="source support"):
        tagger.assign(access, evidence["document_version_id"], pins["taxonomy_version_id"], [], subjects=[bad])
