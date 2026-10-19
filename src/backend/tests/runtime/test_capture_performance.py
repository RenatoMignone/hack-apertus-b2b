"""Performance changes preserve corpus membership, permissions and transaction bounds."""
from dataclasses import replace
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError

from backend.application.persistence.session import BoundEngine
from backend.application.persistence.store import RuntimeStore
from backend.contracts.services import ServiceUnavailable
from backend.data import schema as t
from backend.data.database import transaction
from backend.data.fixtures import FixtureEmbedder
from backend.data.retrieval.hybrid import HybridSearch
from backend.tests.runtime.test_live_corpus import live_users, start

pytestmark = pytest.mark.integration
SQL_ROOT = Path(__file__).resolve().parents[2] / 'data/migrations/versions'


def install(engine, name):
    statement = (SQL_ROOT/name).read_text().replace('CREATE FUNCTION ops.capture_live_corpus',
        'CREATE OR REPLACE FUNCTION ops.capture_live_corpus', 1)
    with engine.begin() as c:
        c.execute(text(statement))


def membership(engine, snapshot):
    with engine.connect() as c:
        return {table.fullname: {tuple(row) for row in c.execute(select(*[
            column for column in table.c if column.name!='snapshot_id']).where(table.c.snapshot_id==snapshot))}
            for table in (t.snapshot_chunks,t.snapshot_documents,t.snapshot_entities,t.snapshot_claims)}


def test_optimized_capture_keeps_exact_membership(harness, live_users):
    store, access = live_users[0]
    from backend.data.repositories.corpus import CorpusRepository
    repository=CorpusRepository(harness.store.engine,harness.store.artifacts)
    with harness.store.engine.connect() as c:
        evidence=c.execute(select(t.spans.c.evidence_id).where(t.spans.c.scope_id==UUID(harness.fixture['scope_id']))).scalars().first()
    entity=repository.record_entity(harness.access,scope_id=UUID(harness.fixture['scope_id']),
        entity_type='unit',display_label='Synthetic example')
    claim=repository.record_claim(harness.access,scope_id=UUID(harness.fixture['scope_id']),subject_id=entity,
        predicate='capability',typed_literal={'type':'text','value':'Synthetic glucose research'},
        evidence_ids=[evidence],accepted=True)
    try:
        install(harness.store.engine,'live_capture.sql')
        before, _ = start(store, access, 'baseline')
    finally:
        install(harness.store.engine,'live_capture_fast.sql')
    after, _ = start(store, access, 'optimized')
    assert membership(harness.store.engine,before.snapshot_id)==membership(harness.store.engine,after.snapshot_id)
    assert before.snapshot_id!=after.snapshot_id
    assert membership(harness.store.engine,after.snapshot_id)[t.snapshot_claims.fullname]=={(claim,)}


def test_capture_restores_existing_statement_timeout_and_can_repeat_in_transaction(live_users):
    store, access = live_users[0]
    with transaction(store.engine,access) as c:
        c.execute(text("SET LOCAL statement_timeout='25s'"))
        bound=RuntimeStore(BoundEngine(c),store.settings,store.artifacts)
        for key in ['first','second']:
            bound.create(access,key,{'prompt':'Synthetic public research'},'test')
            assert c.execute(text('SHOW statement_timeout')).scalar_one()=='25s'
            assert c.execute(text("SELECT to_regclass('pg_temp.navigator_live_capture_members')")).scalar_one() is None


def test_caller_cannot_supply_capture_temp_members(live_users):
    store, access = live_users[0]
    with pytest.raises(DBAPIError):
        with transaction(store.engine,access) as c:
            c.execute(text('CREATE TEMP TABLE navigator_live_capture_members(fake text) ON COMMIT DROP'))
            RuntimeStore(BoundEngine(c),store.settings,store.artifacts).create(
                access,'must-reject',{'prompt':'Synthetic public research'},'test')


def test_capture_timeout_rolls_back_case_creation(harness, live_users):
    store, access = live_users[0]
    store.settings=replace(store.settings,capture_timeout_seconds=1)
    try:
        with harness.store.engine.begin() as c:
            c.execute(text('''CREATE OR REPLACE FUNCTION ops.capture_live_corpus(target_case uuid,target_profile uuid,
                target_taxonomy uuid,embedding_hash text) RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER
                SET search_path=pg_catalog AS $$ BEGIN PERFORM pg_sleep(2); RETURN target_case; END $$'''))
        with pytest.raises(ServiceUnavailable):
            start(store,access,'timeout')
        with transaction(store.engine,access) as c:
            assert c.execute(select(func.count()).select_from(t.cases).where(t.cases.c.owner_id==access.principal_id)).scalar_one()==0
    finally:
        install(harness.store.engine,'live_capture_fast.sql')


def test_query_batch_and_serial_embedding_have_identical_ranking(live_users):
    store, access = live_users[0]
    _, plan = start(store,access,'query-batch')
    plan=plan.model_copy(update={'variants':['glucose monitoring','biosensors']})
    class Batch(FixtureEmbedder):
        calls=0
        def embed_queries(self,texts):
            self.calls+=1
            return [super(Batch,self).embed_query(value) for value in texts]
    batched=Batch()
    serial=HybridSearch(store.engine,FixtureEmbedder()).search(access,plan)
    result=HybridSearch(store.engine,batched).search(access,plan)
    assert batched.calls==1
    assert [(h.chunk_id,h.fusion_score,h.lexical_rank,h.vector_rank) for h in result.hits]==[
        (h.chunk_id,h.fusion_score,h.lexical_rank,h.vector_rank) for h in serial.hits]
    assert [h.evidence_ids for h in result.hits]==[h.evidence_ids for h in serial.hits]


def test_newest_ready_version_replaces_only_its_document(harness,live_users):
    from backend.contracts.data import Span
    from backend.data.repositories.corpus import CorpusRepository
    store,access=live_users[0]
    first,_=start(store,access,'version-before')
    with harness.store.engine.connect() as c:
        old=c.execute(select(t.versions,t.documents.c.canonical_url,t.documents.c.source_id)
            .select_from(t.versions.join(t.documents)).where(t.versions.c.scope_id==UUID(harness.fixture['scope_id']))).mappings().first()
        config=c.execute(select(t.embedding_configs.c.config_id).where(t.embedding_configs.c.config_hash==first.embedding_config_hash)).scalar_one()
    body='Updated synthetic glucose monitoring capability.'
    repository=CorpusRepository(harness.store.engine,harness.store.artifacts)
    version=repository.stage_document(harness.access,scope_id=old['scope_id'],source_id=old['source_id'],
        url=old['canonical_url'],title='Updated synthetic source',language='en',body=body,raw=body.encode(),
        spans=[Span(char_start=0,char_end=len(body),text=body)],parser_hash='updated-ready-version')
    incomplete,_=start(store,access,'version-without-index')
    assert membership(harness.store.engine,first.snapshot_id)==membership(harness.store.engine,incomplete.snapshot_id)
    chunk=repository.stage_chunk(harness.access,version_id=version,span=Span(char_start=0,char_end=len(body),text=body),
        chunker_hash='updated-ready-version',config_id=config,vector=FixtureEmbedder().embed_query(body))
    after,_=start(store,access,'version-ready')
    members=membership(harness.store.engine,after.snapshot_id)
    assert (version,) in members[t.snapshot_documents.fullname]
    assert (old['document_version_id'],) not in members[t.snapshot_documents.fullname]
    assert chunk in {row[0] for row in members[t.snapshot_chunks.fullname]}
    assert (old['document_version_id'],) in membership(harness.store.engine,first.snapshot_id)[t.snapshot_documents.fullname]
