"""Manual input revision → freeze → review → PDF/PPTX, on disposable storage."""
from dataclasses import replace
from io import BytesIO
from uuid import UUID
from zipfile import ZipFile

import httpx
import pytest
from sqlalchemy import select
from backend.data import schema as t
from backend.reports.rendering.pptx import TemplatePptxRenderer, MIME
from backend.tests.runtime.test_case_memory import reviewed

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_manual_plans_and_both_reviewed_exports(harness):
    h = harness
    h.store.settings = replace(h.settings, rich_outputs_enabled=True)
    h.services.pptx = TemplatePptxRenderer()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=h.app), base_url='http://test', headers=h.headers) as client:
        url, detail, _ = await reviewed(client, h, 'rich')
        assert detail['exportFormats'] == ['pdf', 'pptx']
        response = await client.put(url+'/business-context', headers={'Idempotency-Key':'plans'}, json={
            'expected_revision':detail['revision'], 'permitted_context_confirmed':True,
            'values':{'planned_jobs':5, 'investment_amount':'100000.00','investment_currency':'CHF','timeline':'2027, tentative'}})
        assert response.status_code == 202, response.text
        assert await h.worker.run_once(h.access)
        updated = (await client.get(url)).json()
        assert updated['revision'] > detail['revision'] and updated['inputId'] != detail['inputId'] and updated['businessContext']['planned_jobs'] == 5
        result = updated['revisions'][-1]
        with h.store.engine.connect() as c:
            pack = c.execute(select(t.packs.c.payload).where(t.packs.c.pack_id == UUID(result['packId']))).scalar_one()
            assert pack['coverage']['operator_business_context']['investment_currency'] == 'CHF'
        report_url = f"{url}/reports/{result['id']}"
        selected = await client.put(report_url+'/reasons/reason1/selection', headers={'Idempotency-Key':'richkeep'},
            json={'selection':'kept','expected_result_hash':result['resultHash']})
        review = await client.post(report_url+'/reviews', headers={'Idempotency-Key':'richreview'}, json={
            'decision':'accepted', 'expected_result_hash':result['resultHash'], 'expected_selection_hash': selected.json()['selection_hash']})
        assert review.status_code == 201, review.text
        downloads = []
        for format in ['pdf','pptx']:
            queued = await client.post(url+'/exports', headers={'Idempotency-Key':format}, json={
                'result_id':result['id'], 'review_id':review.json()['review_id'], 'expected_result_hash':result['resultHash'],
                'expected_selection_hash':selected.json()['selection_hash'], 'format':format})
            assert queued.status_code == 202, queued.text
            assert await h.worker.run_once(h.access)
            operation = (await client.get(queued.json()['status_url'])).json()
            assert operation['status'] == 'committed', operation
            downloaded = await client.get(operation['download_url'])
            assert downloaded.status_code == 200, downloaded.text
            if format == 'pptx':
                assert downloaded.headers['content-type'] == MIME
                assert ZipFile(BytesIO(downloaded.content)).testzip() is None
            else:
                assert downloaded.content.startswith(b'%PDF') and h.pdf.report.business_context.planned_jobs == 5
            downloads.append(operation['download_url'])
        assert len(set(downloads)) == 2  # PDF cannot satisfy the PPTX cache key
        stale = await client.put(url+'/business-context', headers={'Idempotency-Key':'staleplans'}, json={
            'expected_revision':detail['revision'], 'permitted_context_confirmed':True,'values':{}})
        assert stale.status_code == 409
        edit = await client.post(url+'/messages', headers={'Idempotency-Key':'focuswithplans'}, json={
            'expected_revision':updated['revision'], 'kind':'focus','text':'Prioritize sensor research'})
        assert edit.status_code == 202, edit.text
        assert (await client.get(url)).json()['businessContext']['planned_jobs'] == 5
        for download in downloads:
            assert (await client.get(download)).status_code == 409


async def test_disabled_rich_outputs_are_explicitly_unavailable(harness):
    h = harness
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=h.app), base_url='http://test', headers=h.headers) as client:
        created = (await client.post('/api/v1/cases',json={'prompt':'Synthetic research', 'run':False})).json()
        url = '/api/v1/cases/'+created['case_id']
        detail = (await client.get(url)).json()
        assert detail['exportFormats'] == ['pdf'] and not detail['businessContextAvailable']
        response = await client.put(url+'/business-context',json={'expected_revision':0, 'permitted_context_confirmed':True,'values':{'planned_jobs':5}})
        assert response.status_code == 503, response.text
