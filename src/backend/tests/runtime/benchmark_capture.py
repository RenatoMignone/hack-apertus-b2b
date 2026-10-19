"""Opt-in synthetic old/new capture benchmark on a disposable local test DB.

Requires explicit NAVIGATOR_TEST_ADMIN_DSN. Never loads deployment .env settings.
Run: python -m backend.tests.runtime.benchmark_capture --documents 200
"""
import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
from uuid import UUID, uuid4

import psycopg
from psycopg import sql
from sqlalchemy import select, text
from sqlalchemy.engine import make_url

from backend.application.persistence.session import BoundEngine
from backend.application.persistence.store import RuntimeStore
from backend.config.runtime import RuntimeSettings
from backend.contracts.data import AccessContext, Span
from backend.data import schema as t
from backend.data.artifacts.store import FilesystemArtifactStore
from backend.data.database import engine_for, migrate
from backend.data.fixtures import FIXTURE_MODEL, load_fixture
from backend.data.repositories.corpus import CorpusRepository
from backend.tests.run import require_test_admin_dsn


def seed(engine, artifacts, fixture, documents):
    access = AccessContext(principal_id=UUID(fixture['principal_id']), namespace=fixture['namespace'])
    body = 'Synthetic glucose monitoring capability.\n' * 100
    with engine.connect() as c:
        source = c.execute(select(t.sources.c.source_id).where(t.sources.c.scope_id == UUID(fixture['scope_id']))).scalars().first()
    template = CorpusRepository(engine, artifacts).stage_document(access, scope_id=UUID(fixture['scope_id']),
        source_id=source, url='https://fixture.invalid/performance-template', title='Synthetic benchmark',
        language='en', body=body, raw=body.encode(), spans=[Span(char_start=0,char_end=len(body),text=body)], parser_hash='benchmark-template')
    with engine.begin() as c:
        c.execute(text('''WITH docs AS (
          INSERT INTO corpus.documents(document_id,source_id,scope_id,canonical_url)
          SELECT gen_random_uuid(),:source,:scope,'https://fixture.invalid/benchmark/'||gen_random_uuid()
          FROM generate_series(1,:documents) RETURNING document_id)
          INSERT INTO corpus.document_versions(document_version_id,document_id,scope_id,raw_artifact_id,
            body_artifact_id,body_hash,body_text,parser_hash,language,title,status)
          SELECT gen_random_uuid(),d.document_id,v.scope_id,v.raw_artifact_id,v.body_artifact_id,v.body_hash,
            v.body_text,'benchmark-members','en','Synthetic benchmark','accepted'
          FROM docs d CROSS JOIN corpus.document_versions v WHERE v.document_version_id=:template'''),
          {'source':source,'scope':UUID(fixture['scope_id']),'documents':documents,'template':template})
        c.execute(text('''INSERT INTO retrieval.chunks(chunk_id,document_version_id,scope_id,char_start,char_end,
            literal_text,title,heading_path,language,chunker_hash)
          SELECT gen_random_uuid(),v.document_version_id,v.scope_id,g*40,(g+1)*40,
            substring(v.body_text FROM g*40+1 FOR 40),'Synthetic benchmark','[]'::jsonb,'en','benchmark-members'
          FROM corpus.document_versions v CROSS JOIN generate_series(0,99) g
          WHERE v.parser_hash='benchmark-members' '''))
        c.execute(text('''INSERT INTO corpus.evidence_spans(evidence_id,document_version_id,scope_id,char_start,
            char_end,literal_text,heading_path,extraction_method)
          SELECT gen_random_uuid(),document_version_id,scope_id,char_start,char_end,literal_text,'[]'::jsonb,'synthetic-benchmark'
          FROM retrieval.chunks WHERE chunker_hash='benchmark-members' '''))
        c.execute(text('''INSERT INTO retrieval.chunk_evidence(chunk_id,evidence_id)
          SELECT c.chunk_id,e.evidence_id FROM retrieval.chunks c JOIN corpus.evidence_spans e
            ON e.document_version_id=c.document_version_id AND e.char_start=c.char_start AND e.char_end=c.char_end
          WHERE c.chunker_hash='benchmark-members' '''))
        c.execute(text('''INSERT INTO retrieval.embeddings(embedding_id,chunk_id,config_id,input_hash,input_text,vector)
          SELECT gen_random_uuid(),c.chunk_id,ec.config_id,encode(sha256(convert_to(c.literal_text,'UTF8')),'hex'),
            c.literal_text,'[1,0.1,0.1]'::public.vector
          FROM retrieval.chunks c CROSS JOIN retrieval.embedding_configs ec
          WHERE c.chunker_hash='benchmark-members' AND ec.config_hash=:hash'''), {'hash':FIXTURE_MODEL.config_hash})
        c.execute(text('''INSERT INTO retrieval.search_documents(projection_id,chunk_id,search_config_hash,language_config,terms)
          SELECT gen_random_uuid(),c.chunk_id,b.search_config_hash,'english',to_tsvector('english',c.literal_text)
          FROM retrieval.chunks c CROSS JOIN retrieval.index_builds b
          JOIN corpus.snapshots s ON s.build_id=b.build_id
          WHERE c.chunker_hash='benchmark-members' AND s.snapshot_id=:snapshot'''), {'snapshot':UUID(fixture['snapshot_id'])})
        for table in ['retrieval.chunks','retrieval.embeddings','retrieval.chunk_evidence','retrieval.search_documents',
                      'corpus.documents','corpus.document_versions','corpus.evidence_spans']:
            c.execute(text('ANALYZE '+table))
    return access


def measure(engine, settings, artifacts, access, *, profile=False):
    with engine.connect() as c:
        transaction = c.begin()
        started = perf_counter()
        try:
            c.execute(text("SET LOCAL statement_timeout='30s'"))
            plans=[]
            if profile:
                def notice(message):
                    value=getattr(message,'message_primary','')
                    if 'plan:' in value:
                        try:plans.append(json.loads(value.split('plan:',1)[1].strip()))
                        except ValueError:pass
                c.connection.driver_connection.add_notice_handler(notice)
                c.exec_driver_sql("LOAD 'auto_explain'")
                for key,value in [('auto_explain.log_min_duration','100ms'),('auto_explain.log_analyze','on'),
                        ('auto_explain.log_timing','off'),('auto_explain.log_buffers','on'),
                        ('auto_explain.log_format','json'),('auto_explain.log_nested_statements','on'),
                        ('client_min_messages','log')]:
                    c.execute(text('SELECT set_config(:key,:value,true)'),{'key':key,'value':value})
            store = RuntimeStore(BoundEngine(c), settings, artifacts)
            started = perf_counter()
            created = store.create(access, uuid4().hex, {'prompt':'Synthetic performance probe'}, 'benchmark')
            context = store.context(access, UUID(created['run_id']))
            digest, count = c.execute(text('''SELECT md5(string_agg(chunk_id::text||embedding_id::text,'' ORDER BY chunk_id)),count(*)
                FROM retrieval.snapshot_chunks WHERE snapshot_id=:snapshot'''), {'snapshot':context.snapshot_id}).one()
            elapsed=round(perf_counter()-started,3)
            for plan in plans:
                query=plan.get('Query Text','')
                if 'WITH ready AS' in query or 'WITH authorized_scopes AS' in query:
                    output=Path('.local/capture-performance');output.mkdir(parents=True,exist_ok=True)
                    label='before' if 'WITH ready AS' in query else 'after'
                    (output/(label+'-plan.json')).write_text(json.dumps(plan,indent=2))
                    def nodes(value):
                        yield value
                        for child in value.get('Plans',[]):yield from nodes(child)
                    details=[{k:n.get(k) for k in ['Node Type','Relation Name','Plan Rows','Actual Rows','Actual Loops','Rows Removed by Join Filter','Rows Removed by Filter']} for n in nodes(plan.get('Plan',{}))]
                    print(json.dumps({'query_plan':label,'nodes':details,'jit':plan.get('JIT')}),flush=True)
            return {'status':'passed','seconds':elapsed,'chunks':count,'membership_hash':digest}
        except Exception as error:
            return {'status':'failed','error_type':type(error).__name__,'seconds':round(perf_counter()-started,3)}
        finally:
            transaction.rollback()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--documents',type=int,default=200)
    parser.add_argument('--profile',action='store_true',help='Requires pg_stat_statements preload; record nested plans locally')
    args=parser.parse_args()
    if not 1<=args.documents<=2000:raise SystemExit('documents must be 1–2000')
    admin=require_test_admin_dsn()
    url=make_url(admin)
    if url.host not in {'127.0.0.1','localhost'} or url.port==15432:
        raise SystemExit('Use an isolated local disposable PostgreSQL endpoint, never the shared SSH tunnel')
    name='navigator_capture_bench_'+uuid4().hex
    engine=None
    with psycopg.connect(admin,autocommit=True) as c:
        c.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
    try:
        engine=engine_for(url.set(database=name).render_as_string(hide_password=False))
        migrate(engine)
        if args.profile:
            with engine.begin() as c:c.execute(text('CREATE EXTENSION IF NOT EXISTS pg_stat_statements'))
        with TemporaryDirectory(prefix='navigator-capture-benchmark-') as directory:
            artifacts=FilesystemArtifactStore(Path(directory))
            fixture=load_fixture(engine,artifacts)
            access=seed(engine,artifacts,fixture,args.documents)
            config=Path(directory)/'embedding.json';config.write_text(FIXTURE_MODEL.model_dump_json())
            settings=RuntimeSettings(default_profile_id=UUID(fixture['profile_id']),corpus_mode='live',
                embedding_configuration=str(config),live_taxonomy_version_id=UUID(fixture['taxonomy_version_id']),
                capture_timeout_seconds=30)
            root=Path(__file__).resolve().parents[2]/'data/migrations/versions'
            results={}
            for label,file in [('before','live_capture.sql'),('after','live_capture_fast.sql')]:
                source=(root/file).read_text().replace('CREATE FUNCTION ops.capture_live_corpus','CREATE OR REPLACE FUNCTION ops.capture_live_corpus',1)
                with engine.begin() as c:c.execute(text(source))
                if args.profile:
                    with engine.begin() as c:c.execute(text('SELECT pg_stat_statements_reset()'))
                results[label]=measure(engine,settings,artifacts,access,profile=args.profile)
                print(json.dumps({label:results[label]}),flush=True)
                if args.profile:
                    with engine.connect() as c:
                        rows=c.execute(text("SELECT calls,round(total_exec_time::numeric,1) AS milliseconds,rows,left(query,160) AS operation FROM pg_stat_statements WHERE dbid=(SELECT oid FROM pg_database WHERE datname=current_database()) ORDER BY total_exec_time DESC LIMIT 10")).mappings()
                        print(json.dumps({'profile':label,'statements':[dict(r) for r in rows]},default=str),flush=True)
            if all(r['status']=='passed' for r in results.values()):
                assert results['before']['membership_hash']==results['after']['membership_hash']
                print(json.dumps({'same_membership':True,'speedup':round(results['before']['seconds']/results['after']['seconds'],2)}),flush=True)
    finally:
        if engine:engine.dispose()
        with psycopg.connect(admin,autocommit=True) as c:
            c.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))


if __name__=='__main__':main()
