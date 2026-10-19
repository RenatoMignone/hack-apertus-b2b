from uuid import UUID, uuid4
import pytest
from sqlalchemy import select, update, insert
from backend.contracts.data import AccessContext
from backend.data import schema as t
from backend.data.repositories.corpus import CorpusRepository
from backend.ingestion.review import CorpusReview, ReviewManifest

pytestmark=pytest.mark.integration


def pending(database,corpus):
    fixture,artifacts=corpus
    access=AccessContext(principal_id=fixture['principal_id'],namespace=fixture['namespace'])
    scope=UUID(fixture['scope_id'])
    with database.connect() as c:
        span=c.execute(select(t.spans).where(t.spans.c.scope_id==scope).order_by(t.spans.c.evidence_id)).mappings().first()
    label=span['literal_text'].split(':')[0]
    repo=CorpusRepository(database,artifacts)
    entity=repo.record_entity(access,scope_id=scope,entity_type='unit',display_label=label)
    claim=repo.record_claim(access,scope_id=scope,subject_id=entity,predicate='capability',
        evidence_ids=[span['evidence_id']],typed_literal={'type':'text','value':span['literal_text']})
    return access,scope,entity,claim,span


def manifest_for(repository,access,scope,entity,claim):
    candidates=repository.candidates(access,scope)['candidates']
    decisions=[{k:row[k] for k in ('kind','record_id','expected_hash')}|{
        'decision':'accepted','justification':'Independent synthetic fixture review.', 'semantic_support_confirmed':True}
        for row in candidates if row['record_id'] in {str(entity),str(claim)}]
    return {'scope_id':str(scope),'reviewer':'fixture-reviewer','decisions':decisions}


def test_review_dry_run_atomic_apply_and_idempotency(database,corpus):
    access,scope,entity,claim,_=pending(database,corpus);repo=CorpusReview(database)
    manifest=manifest_for(repo,access,scope,entity,claim)
    assert repo.review(access,manifest)['applied'] is False
    with database.connect() as c:assert c.execute(select(t.claims.c.status).where(t.claims.c.claim_id==claim)).scalar_one()=='needs_review'
    assert repo.review(access,manifest,apply=True)['records']==2
    assert len(repo.review(access,manifest,apply=True)['already_applied'])==2
    with database.connect() as c:
        assert c.execute(select(t.entities.c.status).where(t.entities.c.entity_id==entity)).scalar_one()=='accepted'
        assert c.execute(select(t.claims.c.status).where(t.claims.c.claim_id==claim)).scalar_one()=='needs_review'
        assert c.execute(select(t.claims.c.status).where(t.claims.c.supersedes_id==claim)).scalar_one()=='accepted'


def test_stale_source_name_and_unreviewed_semantics_are_rejected(database,corpus):
    access,scope,entity,claim,_=pending(database,corpus);repo=CorpusReview(database)
    manifest=manifest_for(repo,access,scope,entity,claim)
    manifest['decisions'][0]['semantic_support_confirmed']=False
    with pytest.raises(ValueError,match='semantic'):repo.review(access,manifest,apply=True)
    manifest=manifest_for(repo,access,scope,entity,claim)
    with database.begin() as c:c.execute(update(t.entities).where(t.entities.c.entity_id==entity).values(display_label='Invented team'))
    with pytest.raises(ValueError,match='stale'):repo.review(access,manifest,apply=True)
    updated=manifest_for(repo,access,scope,entity,claim)
    with pytest.raises(ValueError,match='literally'):repo.review(access,updated,apply=True)


def test_tagging_pins_existing_source_concept_and_records_review(database,corpus):
    access,scope,_,_,span=pending(database,corpus);repo=CorpusReview(database)
    concept=uuid4()
    with database.begin() as c:
        c.execute(insert(t.concepts).values(concept_id=concept,taxonomy_version_id=UUID(corpus[0]['taxonomy_version_id']),
            code='fixture-topic',definition='Synthetic reviewed topic',facet='topic',notes={}))
    manifest={'scope_id':str(scope),'reviewer':'fixture-reviewer','tags':[{
        'concept_id':str(concept),'evidence_id':str(span['evidence_id']),'justification':'Reviewed fixture topic.',
        'semantic_support_confirmed':True}]}
    assert repo.review(access,manifest)['tags']==1
    assert repo.review(access,manifest,apply=True)['tags']==1
    assert repo.review(access,manifest,apply=True)['tags']==1
    with database.connect() as c:
        rows=c.execute(select(t.assignments).where(t.assignments.c.document_version_id==span['document_version_id'])).mappings().all()
        assert len(rows)==1 and rows[0]['status']=='accepted'
