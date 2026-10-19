"""Local access keeps server identity/RLS; progress reads never lock case rows."""
from dataclasses import replace
from datetime import datetime, timezone
import logging
from time import perf_counter
from uuid import UUID

import httpx
import pytest
from sqlalchemy import text

from backend.config.runtime import RuntimeSettings
from backend.observability.logging import PollFilter, activity, event
from backend.tests.runtime.test_live_corpus import live_users, start


def test_local_access_requires_single_binding(harness):
    with pytest.raises(ValueError):
        RuntimeSettings(local_access=True)
    with pytest.raises(ValueError):
        replace(harness.settings, local_access=True, bindings=(harness.binding, harness.binding))


@pytest.mark.asyncio
@pytest.mark.integration
async def test_local_access_auto_connects_only_on_loopback_and_valid_token_still_required_elsewhere(harness):
    h = harness
    h.app.state.registry.settings = replace(h.settings, local_access=True)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=h.app, client=('127.0.0.1', 1234)), base_url='http://127.0.0.1') as c:
        result = await c.get('/api/v1/capabilities')
        assert result.status_code == 200 and result.json()['access_mode'] == 'local'
        for headers in ({'Origin': 'https://evil.invalid'}, {'Host':'evil.invalid'}, {'X-Forwarded-For':'127.0.0.1'}, {'Forwarded':'for=127.0.0.1'}):
            assert (await c.get('/api/v1/capabilities',headers=headers)).status_code == 403
        assert (await c.get('/api/v1/capabilities', headers={'Authorization':'Bearer wrong'})).status_code == 401
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=h.app, client=('192.0.2.2', 1234)), base_url='http://127.0.0.1') as c:
        assert (await c.get('/api/v1/capabilities')).status_code == 403
        assert (await c.get('/api/v1/capabilities',headers=h.headers)).status_code == 200


@pytest.mark.integration
def test_progress_read_does_not_wait_for_case_write_lock(harness, live_users):
    store, access = live_users[0]
    context, _ = start(store, access, 'progress')
    store.mark_run(access, context.run_id, 'running')
    store.start_activity(access, context.run_id, 'retrieve.1')
    store.start_activity(access, context.run_id, 'fetch.1')
    with harness.store.engine.begin() as c:
        c.execute(text('SELECT case_id FROM cases.cases WHERE case_id=:id FOR UPDATE'), {'id':context.case_id})
        with store.engine.connect() as connection:
            connection.execute(text("SET statement_timeout='1s'")); connection.commit()
        # The store's pooled connection uses the bounded statement timeout.
        view = store.run_view(access, context.case_id, context.run_id)
        rows = store.case_rows(access, context.case_id)
        assert rows[0]['case']['case_id'] == context.case_id
    assert {a['step'] for a in view['activity']} == {'retrieve.1','fetch.1'}
    assert view['stage'] == 'searching'
    store.finish_activity(access,context.run_id,'retrieve.1')
    assert [a['step'] for a in store.run_view(access,context.case_id,context.run_id)['activity']] == ['fetch.1']
    store.finish_activity(access,context.run_id,'fetch.1',failed=True)
    assert store.run_view(access,context.case_id,context.run_id)['activity'] == []


def test_poll_filter_keeps_errors_and_mutations():
    def record(method, path, status):
        return logging.LogRecord('uvicorn.access',logging.INFO,'',0,'%s %s %s %s %s',('local',method,path,'1.1',status),None)
    f = PollFilter()
    assert not f.filter(record('GET','/api/v1/cases/c/runs/r',200))
    assert f.filter(record('GET','/api/v1/cases/c/runs/r',503))
    assert f.filter(record('POST','/api/v1/cases',201))


@pytest.mark.asyncio
async def test_diagnostics_include_model_activity_without_payload_or_exception_text(caplog):
    with caplog.at_level(logging.INFO, logger='backend.runtime'):
        with pytest.raises(ValueError):
            async with activity('model', task='extract', model='apertus-v1-5-70b'):
                event('test.event', prompt='SECRET_PROMPT', api_key='SECRET_KEY', error_code='invalid')
                raise ValueError('SECRET_BODY')
    assert 'model.started' in caplog.text and 'model.failed' in caplog.text
    assert 'model=apertus-v1-5-70b' in caplog.text
    assert 'SECRET' not in caplog.text


@pytest.mark.asyncio
@pytest.mark.integration
async def test_diagnostic_progress_failure_does_not_block_stage(harness, live_users, monkeypatch):
    from backend.workflows.execution import Execution
    store, access = live_users[0]
    context, _ = start(store, access, 'progress-unavailable')
    def unavailable(*args):
        raise RuntimeError('Private diagnostics unavailable')
    monkeypatch.setattr(store,'start_activity',unavailable)
    async def task():
        return {'ok': True}
    assert await Execution(store,context).call('diagnostic_probe',{},task) == {'ok':True}


@pytest.mark.integration
def test_runtime_connections_bound_waits_preserve_stricter_policy_and_release_idle_locks(database, corpus):
    from time import sleep
    from sqlalchemy.exc import DBAPIError
    from backend.data.database import engine_for
    from backend.data.repositories.cases import CaseRepository
    from backend.contracts.data import AccessContext
    fixture, _ = corpus
    access = AccessContext(principal_id=UUID(fixture['principal_id']), namespace=fixture['namespace'])
    case_id, _ = CaseRepository(database).create(access, 'synthetic lock safety')
    bounded = engine_for(database.url.render_as_string(hide_password=False), runtime=True)
    stricter = engine_for(database.url.update_query_dict({'options':
        '-c lock_timeout=100 -c idle_in_transaction_session_timeout=1000'}).render_as_string(hide_password=False), runtime=True)
    try:
        with bounded.connect() as c:
            assert c.execute(text("SELECT setting FROM pg_settings WHERE name='lock_timeout'")).scalar_one() == '5000'
            assert c.execute(text("SELECT setting FROM pg_settings WHERE name='idle_in_transaction_session_timeout'")).scalar_one() == '60000'
        with database.begin() as holder:
            holder.execute(text('SELECT case_id FROM cases.cases WHERE case_id=:id FOR UPDATE'), {'id':case_id})
            with stricter.begin() as waiter:
                assert waiter.execute(text("SELECT setting FROM pg_settings WHERE name='lock_timeout'")).scalar_one() == '100'
                with pytest.raises(DBAPIError) as error:
                    waiter.execute(text('SELECT case_id FROM cases.cases WHERE case_id=:id FOR UPDATE'), {'id':case_id})
                assert error.value.orig.sqlstate == '55P03'
        idle = stricter.connect()
        try:
            idle.execute(text('SELECT case_id FROM cases.cases WHERE case_id=:id FOR UPDATE'), {'id':case_id})
            sleep(1.5)  # Simulate a suspended terminal; the server releases its locks.
            with database.begin() as c:
                c.execute(text("SET LOCAL lock_timeout='500ms'"))
                c.execute(text('SELECT case_id FROM cases.cases WHERE case_id=:id FOR UPDATE'), {'id':case_id})
            with pytest.raises(DBAPIError):
                idle.execute(text('SELECT 1'))
        finally:
            idle.close()
    finally:
        bounded.dispose(); stricter.dispose()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_board_summary_matches_detail_without_loading_historical_reports(harness, monkeypatch):
    from sqlalchemy import event as sql_event
    h = harness
    for i in range(5):
        h.store.create(h.access, f'board-{i}', {'prompt':f'Synthetic glucose company {i}'}, 'request')
    await h.worker.run_once(h.access)
    before = [row['case'] for row in [await h.application.detail(h.access, UUID(item['id']))
        for item in h.store.case_summaries(h.access)]]
    def forbidden(*args, **kwargs):
        raise AssertionError('Listing cases must not hydrate or validate full historical reports')
    monkeypatch.setattr(h.store, 'case_rows', forbidden)
    statements = []
    def record(_c, _cursor, statement, _params, _ctx, _many):
        statements.append(statement)
    sql_event.listen(h.store.engine, 'before_cursor_execute', record)
    try:
        result = await h.application.list_cases(h.access)
    finally:
        sql_event.remove(h.store.engine, 'before_cursor_execute', record)
    assert result == before
    assert len(statements) == 7  # Authentication/settings + four batched projections.
    assert await h.application.list_cases(h.access, limit=2, offset=1) == result[1:3]


@pytest.mark.integration
def test_web_duplicate_lookup_batches_aliases_without_case_write_lock(harness, live_users):
    from sqlalchemy import event as sql_event
    from backend.data.database import engine_for
    from backend.data.repositories.research import ResearchRepository
    store, access = live_users[0]
    context, _ = start(store, access, 'duplicate-batch')
    engine = engine_for(store.engine.url.update_query_dict({'options':'-c lock_timeout=100'})
        .render_as_string(hide_password=False), runtime=True)
    statements = []
    def record(_c, _cursor, statement, _params, _ctx, _many):
        statements.append(statement)
    sql_event.listen(engine, 'before_cursor_execute', record)
    try:
        with harness.store.engine.begin() as holder:
            holder.execute(text('SELECT case_id FROM cases.cases WHERE case_id=:id FOR UPDATE'), {'id':context.case_id})
            assert ResearchRepository(engine).corpus_duplicate(access, context.run_id,
                'https://fixture.invalid/unknown-batched-duplicate') is None
        assert len([s for s in statements if 'corpus.document_aliases' in s]) == 1
        assert not any('FOR UPDATE' in s for s in statements)
    finally:
        engine.dispose()


@pytest.mark.integration
def test_worker_lease_renews_during_case_write_and_stale_worker_cannot_renew(harness, live_users):
    from sqlalchemy import select
    from backend.data import schema as t
    from backend.contracts.services import StaleRevision
    store, access = live_users[0]
    context, _ = start(store, access, 'lease-with-registration')
    job = store.claim_job(access, 'synthetic-worker')
    assert job['run_id'] == context.run_id
    # A short SQL bound makes the old heartbeat's case-lock dependency fail
    # deterministically rather than hanging this regression test.
    with store.engine.connect() as c:
        c.execute(text("SET lock_timeout='100ms'")); c.commit()
    with harness.store.engine.begin() as holder:
        holder.execute(text('SELECT case_id FROM cases.cases WHERE case_id=:id FOR UPDATE'), {'id':context.case_id})
        store.heartbeat(access, job['attempt_id'], 'synthetic-worker')
    with store.session(access) as c:
        deadline = c.execute(select(t.attempts.c.lease_until).where(t.attempts.c.attempt_id == job['attempt_id'])).scalar_one()
    assert deadline >= job['lease_until']
    with pytest.raises(StaleRevision):
        store.heartbeat(access, job['attempt_id'], 'another-worker')
    store.cancel(access, 'cancel-lease-test', context.case_id, context.run_id)
    with pytest.raises(StaleRevision):
        store.heartbeat(access, job['attempt_id'], 'synthetic-worker')
