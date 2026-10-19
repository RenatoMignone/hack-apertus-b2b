"""Opt-in history over real disposable PostgreSQL; synthetic providers only."""
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import select

from backend.application.case_memory import CaseMemory, profile
from backend.contracts.pipeline import CaseInterpretation
from backend.data import schema as t
from backend.data.fixtures import FixtureEmbedder

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def reviewed(client, h, key):
    created = (await client.post('/api/v1/cases', headers={'Idempotency-Key': key},
        json={'prompt': 'Explicit synthetic glucose fixture'})).json()
    assert await h.worker.run_once(h.access)
    url = f"/api/v1/cases/{created['case_id']}"
    detail = (await client.get(url)).json()
    result = detail['revisions'][0]
    selected = await client.put(f"{url}/reports/{result['id']}/reasons/reason1/selection",
        headers={'Idempotency-Key': key+'keep'}, json={'selection': 'kept', 'expected_result_hash': result['resultHash']})
    assert selected.status_code == 200, selected.text
    response = await client.post(f"{url}/reports/{result['id']}/reviews", headers={'Idempotency-Key': key+'review'},
        json={'decision': 'accepted', 'expected_result_hash': result['resultHash'],
              'expected_selection_hash': selected.json()['selection_hash']})
    assert response.status_code == 201, response.text
    return url, detail, result


async def test_reviewed_opt_in_matches_and_revocation(harness):
    h = harness
    class Counting(FixtureEmbedder):
        calls = 0
        def embed_query(self, value):
            self.calls += 1
            return super().embed_query(value)
    encoder = Counting()
    h.services.memory = CaseMemory(h.store, encoder, minimum_score=0)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=h.app), base_url='http://test', headers=h.headers) as client:
        url, detail, result = await reviewed(client, h, 'first')
        body = {'eligible': True, 'synthetic': False, 'permitted_context_confirmed': True,
                'expected_revision': detail['revision'], 'expected_result_hash': result['resultHash']}
        # Explicit attestations are required; this fixture deliberately exercises
        # the trusted operator declaration, not a claim of genuine pilot history.
        response = await client.post(url+'/memory', headers={'Idempotency-Key': 'synthetic-denied'}, json={**body, 'synthetic': True})
        assert response.status_code == 409, response.text
        response = await client.post(url+'/memory', headers={'Idempotency-Key': 'index'}, json=body)
        assert response.status_code == 200, response.text
        calls = encoder.calls
        assert (await client.post(url+'/memory', headers={'Idempotency-Key': 'reindex'}, json=body)).status_code == 200
        assert encoder.calls == calls  # stored vector reused, not re-embedded
        lifecycle = await client.patch(url, headers={'Idempotency-Key': 'closed-outcome'}, json={
            'expected_revision': detail['revision'], 'status':'closed', 'outcome':'visit'})
        assert lifecycle.status_code == 200, lifecycle.text
        detail = (await client.get(url)).json()
        url2, detail2, _ = await reviewed(client, h, 'second')
        match = detail2['revisions'][0]['similarCases'][0]
        assert match['caseId'] == detail['case']['id'] and match['score'] == 100
        assert match['method'] == 'symmetric-needs-cosine-v1'
        assert match['shared'] == ['sensor research']
        assert match['status'] == 'closed' and match['outcome'] == 'visit'
        foreign = h.access.model_copy(update={'principal_id': uuid4()})
        with pytest.raises(PermissionError):
            h.services.memory._search(foreign, UUID(detail2['case']['id']), {}, [1., .1, .1], 5)
        response = await client.post(url+'/memory', headers={'Idempotency-Key': 'disable'},
            json={'eligible': False, 'expected_revision': detail['revision']})
        assert response.status_code == 200, response.text
        assert not (await client.get(url2)).json()['revisions'][0]['similarCases']
        with h.store.engine.connect() as c:
            assert len(c.execute(select(t.case_memory)).all()) == 1


async def test_index_requires_exact_review_and_current_revision(harness):
    h = harness
    h.services.memory = CaseMemory(h.store, FixtureEmbedder())
    created = h.store.create(h.access, 'new', {'prompt': 'Synthetic glucose'}, 'request')
    assert await h.worker.run_once(h.access)
    detail = await h.application.detail(h.access, UUID(created['case_id']))
    body = {'eligible': True, 'synthetic': False, 'permitted_context_confirmed': True,
        'expected_revision': detail['revision'], 'expected_result_hash': detail['revisions'][0]['resultHash']}
    with pytest.raises(ValueError):
        await h.services.memory.set(h.access, UUID(created['case_id']), 'unreviewed', body)
    value, semantic = profile(CaseInterpretation(company_name='Secret label', company_summary='Permitted context', activity_label='sensors', bern_intents=['Research in Bern'], needs=['No clinical approval assumed']))
    assert 'Secret label' not in semantic and 'No clinical approval assumed' in semantic
