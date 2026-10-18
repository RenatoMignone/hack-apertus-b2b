"""Real PostgreSQL checks for the research → pack → reason review boundary."""
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import insert, select, text
from sqlalchemy.exc import DBAPIError

from backend.contracts.data import Span, content_hash, configuration_hash
from backend.contracts.pipeline import ClaimAssessment, DraftAssessment, DraftReason, DraftRevision, FetchedSource, ReportEvidencePack, SupportedClaim
from backend.data import schema as t
from backend.data.admin import grant_scope, revoke_scope
from backend.data.repositories.corpus import CorpusRepository
from backend.data.repositories.drafts import DraftRepository
from backend.data.repositories.evidence import EvidenceRepository
from backend.data.repositories.research import ResearchRepository
from backend.tests.test_database import context, make_run
from backend.tests.test_pipeline_contracts import interpretation

pytestmark = pytest.mark.integration


def checked(draft):
    return DraftAssessment(draft_hash=configuration_hash(draft.model_dump(mode="json")), status="supported",
        validator="fixture-draft-check-v1", explanation="Synthetic test assertion; no live model validation")


def local_evidence(database, fixture, artifacts, case_id, *, url="https://new.example.org/research"):
    scope, source = uuid4(), uuid4()
    with database.begin() as c:
        c.execute(insert(t.scopes).values(scope_id=scope, kind="case", case_id=case_id, access_policy_id="case"))
        c.execute(insert(t.sources).values(source_id=source, scope_id=scope, canonical_origin="https://new.example.org", registry_ref="case-research"))
    grant_scope(database, UUID(fixture["principal_id"]), scope, write=True)
    body = "The research group develops closed-loop algorithms."
    corpus = CorpusRepository(database, artifacts)
    version = corpus.stage_document(context(fixture), scope_id=scope, source_id=source, url=url,
        title="Research group", language="en", raw=body.encode(), body=body, parser_hash="fixture-v1",
        spans=[Span(char_start=0, char_end=len(body), text=body)])
    with database.connect() as c:
        evidence_id = c.execute(select(t.spans.c.evidence_id).where(t.spans.c.document_version_id == version)).scalar_one()
    entity = corpus.record_entity(context(fixture), scope_id=scope, entity_type="unit", display_label="Research group")
    claim = corpus.record_claim(context(fixture), scope_id=scope, subject_id=entity, predicate="capability",
        typed_literal={"type": "text", "value": body}, evidence_ids=[evidence_id])
    return scope, version, evidence_id, claim, body


def prepared(database, corpus):
    fixture, artifacts = corpus
    access = context(fixture)
    cases, case_id, _, run_id, _ = make_run(database, fixture)
    evidence = EvidenceRepository(database)
    evidence.interpret(access, run_id, interpretation())
    scope, version, evidence_id, claim_id, body = local_evidence(database, fixture, artifacts, case_id)
    research = ResearchRepository(database)
    research_id = research.start(access, run_id, "public closed-loop research")
    page = FetchedSource(title="Research group", url="https://new.example.org/research", canonical_url="https://new.example.org/research",
        content=body, content_hash=content_hash(body.encode()), fetched_at=datetime.now(timezone.utc))
    assert research.record_source(access, research_id, page, version_id=version)["review_status"] == "unreviewed"
    manifest = evidence.manifest(access, run_id, [evidence_id])
    assessment = ClaimAssessment(claim_id=claim_id, evidence_ids=[evidence_id], statement=body, status="supported",
        validator="fixture-semantic-validator-v1", explanation="Synthetic test assessment, not measured model output")
    evidence.assess(access, run_id, assessment)
    claim = SupportedClaim(claim_id=claim_id, text=body, evidence_ids=[evidence_id])
    pack = ReportEvidencePack(interpretation=interpretation(), claims=[claim], outcome="complete")
    pack_id = evidence.freeze(access, run_id, pack, manifest_id=manifest)
    draft = DraftRevision(reasons=[DraftReason(id="why-1", headline="Relevant algorithms", text=body, claim_ids=[claim_id])])
    drafts = DraftRepository(database)
    result_id = drafts.create(access, case_id, pack_id, draft, expected_revision=0, assessment=checked(draft))
    return locals()


def test_case_local_pack_review_pdf_and_editorial_rejection(database, corpus):
    x = prepared(database, corpus)
    cases, drafts, access = x["cases"], x["drafts"], x["access"]
    result = cases.read_result(access, x["result_id"])
    sources = x["evidence"].read(access, x["run_id"], [x["evidence_id"]], pack_id=x["pack_id"])
    assert sources[0]["review_status"] == "unreviewed"
    assert sources[0]["literal_text"] == x["body"]
    with pytest.raises(ValueError, match="review all"):
        cases.review(access, x["result_id"], expected_hash=result["result_hash"], decision="accepted")
    selections = drafts.select(access, x["result_id"], "why-1", "kept", expected_hash=result["result_hash"])
    with pytest.raises(ValueError, match="selection hash"):
        cases.review(access, x["result_id"], expected_hash=result["result_hash"], decision="accepted", expected_selection_hash="stale")
    review = cases.review(access, x["result_id"], expected_hash=result["result_hash"], decision="accepted", expected_selection_hash=selections)
    reference = x["artifacts"].put(b"%PDF-1.4\nsynthetic fixture", "application/pdf")
    export = cases.record_export(access, x["result_id"], review, reference, artifacts=x["artifacts"], template_version="fixture", renderer_version="fixture")
    drafts.select(access, x["result_id"], "why-1", "rejected", expected_hash=result["result_hash"])
    with database.connect() as c:
        assert c.execute(select(t.exports.c.status).where(t.exports.c.export_id == export)).scalar_one() == "stale"
        assert c.execute(select(t.assessments.c.status).where(t.assessments.c.claim_id == x["claim_id"])).scalar_one() == "supported"
    with pytest.raises(ValueError):
        cases.record_export(access, x["result_id"], review, reference, artifacts=x["artifacts"], template_version="fixture", renderer_version="fixture")
    revoke_scope(database, x["scope"])
    with database.connect() as c:
        assert c.execute(select(t.exports.c.status).where(t.exports.c.export_id == export)).scalar_one() == "revoked"
    with pytest.raises(PermissionError):
        cases.read_result(access, x["result_id"])
    with pytest.raises(PermissionError):
        x["evidence"].read(access, x["run_id"], [x["evidence_id"]], pack_id=x["pack_id"])


def test_selection_carry_and_changed_reason_reset(database, corpus):
    x = prepared(database, corpus)
    result = x["cases"].read_result(x["access"], x["result_id"])
    x["drafts"].select(x["access"], x["result_id"], "why-1", "kept", expected_hash=result["result_hash"])
    unchanged = x["drafts"].create(x["access"], x["case_id"], x["pack_id"], x["draft"], expected_revision=1, assessment=checked(x["draft"]), parent_id=x["result_id"])
    changed = x["draft"].model_copy(update={"reasons": [x["draft"].reasons[0].model_copy(update={"text": "Shorter wording"})]})
    changed_id = x["drafts"].create(x["access"], x["case_id"], x["pack_id"], changed, expected_revision=2, assessment=checked(changed), parent_id=unchanged)
    with database.connect() as c:
        def selection(result_id):
            return c.execute(select(t.reason_selections.c.selection).join(t.reasons).where(t.reasons.c.result_id == result_id)).scalar_one()
        assert selection(unchanged) == "kept"
        assert selection(changed_id) == "none"
    with pytest.raises(ValueError, match="stale"):
        x["drafts"].create(x["access"], x["case_id"], x["pack_id"], changed, expected_revision=1, assessment=checked(changed))


def test_foreign_manifest_and_unassessed_claim_rejected(database, corpus):
    x = prepared(database, corpus)
    _, other_case, _, other_run, _ = make_run(database, x["fixture"])
    x["evidence"].interpret(x["access"], other_run, interpretation())
    with pytest.raises(PermissionError, match="own case"):
        x["evidence"].manifest(x["access"], other_run, [x["evidence_id"]])
    with pytest.raises(PermissionError, match="foreign case"):
        x["evidence"].freeze(x["access"], other_run, x["pack"], manifest_id=x["manifest"])
    changed = x["pack"].model_copy(update={"claims": [x["claim"].model_copy(update={"text": "An invented stronger statement"})]})
    with pytest.raises(ValueError, match="assessment"):
        x["evidence"].freeze(x["access"], x["run_id"], changed, manifest_id=x["manifest"])
    with pytest.raises(DBAPIError, match="cannot change"):
        with database.begin() as c:
            c.execute(insert(t.manifest_items).values(item_id=uuid4(), manifest_id=x["manifest"], evidence_id=x["evidence_id"]))


def test_empty_pack_offline_and_duplicate_preference(database, corpus):
    fixture, artifacts = corpus
    cases, case_id, _, run_id, _ = make_run(database, fixture)
    access = context(fixture)
    evidence = EvidenceRepository(database)
    evidence.interpret(access, run_id, interpretation())
    pack_id = evidence.freeze(access, run_id, ReportEvidencePack(interpretation=interpretation(), outcome="no_match", gaps=["No verified match"]))
    result = DraftRepository(database).create(access, case_id, pack_id, DraftRevision(reasons=[]), expected_revision=0, assessment=checked(DraftRevision(reasons=[])))
    assert cases.read_result(access, result)
    research = ResearchRepository(database)
    offline = research.start(access, run_id, "public query", mode="offline")
    with database.connect() as c:
        assert c.execute(select(t.web_research.c.status).where(t.web_research.c.research_id == offline)).scalar_one() == "unavailable"
        url, version = c.execute(select(t.documents.c.canonical_url, t.versions.c.document_version_id).select_from(t.documents.join(t.versions).join(t.snapshot_documents)).where(
            t.snapshot_documents.c.snapshot_id == UUID(fixture["snapshot_id"]))).first()
    assert research.corpus_duplicate(access, run_id, url + "#fragment") == version
    assert research.corpus_duplicate(access, run_id, "https://unknown.example.org") is None


def test_draft_assessment_gate_and_action_status(database, corpus):
    x = prepared(database, corpus)
    check = checked(x["draft"]).model_copy(update={"status": "unsupported"})
    with pytest.raises(ValueError, match="assessment"):
        x["drafts"].create(x["access"], x["case_id"], x["pack_id"], x["draft"], expected_revision=1, assessment=check)
    action = x["drafts"].action(x["access"], x["case_id"], "Is the group available?", "Research liaison")
    x["drafts"].set_action_status(x["access"], action, "asked")
    with database.connect() as c:
        assert c.execute(select(t.action_items.c.status).where(t.action_items.c.action_id == action)).scalar_one() == "asked"
    with pytest.raises(ValueError, match="action status"):
        x["drafts"].set_action_status(x["access"], action, "invented")


def test_historical_citations_survive_edit_and_frozen_membership_is_checked(database, corpus):
    x = prepared(database, corpus)
    x["cases"].edit(x["access"], x["case_id"], expected_revision=1, instruction="Focus on sensors", kind="focus")
    assert x["evidence"].read(x["access"], x["run_id"], [x["evidence_id"]], pack_id=x["pack_id"])
    with pytest.raises(ValueError, match="current revision"):
        x["drafts"].select(x["access"], x["result_id"], "why-1", "kept",
            expected_hash=x["cases"].read_result(x["access"], x["result_id"])["result_hash"])
    with database.begin() as c:
        extra = c.execute(select(t.spans.c.evidence_id).where(t.spans.c.scope_id == UUID(x["fixture"]["scope_id"]))).scalars().first()
        c.execute(insert(t.pack_items).values(pack_id=x["pack_id"], evidence_id=extra))
    with pytest.raises(PermissionError, match="frozen pack"):
        x["cases"].read_result(x["access"], x["result_id"])
    with pytest.raises(PermissionError, match="frozen pack"):
        x["evidence"].read(x["access"], x["run_id"], [extra], pack_id=x["pack_id"])
