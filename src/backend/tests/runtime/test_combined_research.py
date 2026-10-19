"""Controlled public fetch + real DB/web merge; no external-network quality claim."""
import socket
from uuid import UUID

import httpx
import pytest
from sqlalchemy import select

from backend.application.adapters import Services
from backend.application.service import RuntimeApplication
from backend.application.worker import Worker
from backend.data import schema as t
from backend.data.backbone import create_backbone
from backend.data.fixtures import FixtureEmbedder
from backend.evidence import create_reasoning_services
from backend.ingestion.web import Crawl4AIFetcher, PublicWebTools, SafeHTTP
from backend.models.reasoning import ModelSettings
from backend.tests.runtime.test_integrated_lanes import synthetic_transport

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_combined_fetch_dedup_provenance_and_graph_completion(harness):
    h = harness
    with h.store.engine.connect() as c:
        original = c.execute(select(t.documents.c.canonical_url, t.versions.c.document_version_id,
            t.versions.c.body_text).select_from(t.documents.join(t.versions).join(t.snapshot_documents)).where(
            t.snapshot_documents.c.snapshot_id == UUID(h.fixture['snapshot_id']))).mappings().first()
    fresh = 'https://public.example.org/synthetic-sensor-research.pdf'
    from io import BytesIO
    from reportlab.pdfgen.canvas import Canvas
    buffer = BytesIO()
    page = Canvas(buffer, invariant=1)
    page.drawString(40, 800, 'Synthetic example develops glucose sensor prototypes.')
    page.save()
    pdf = buffer.getvalue()
    class Discovery:
        async def discover(self, query, limit):
            assert 'Synthetic Company' not in query
            return [original['canonical_url'], fresh, fresh]
    class ControlledHTTP(SafeHTTP):
        def _request(self, url, deadline):
            normalized, _, _ = self.target(url)  # keep actual target policy active
            if url.endswith('/robots.txt'):
                return normalized, 404, {}, b''
            return normalized, 200, {'content-type': 'application/pdf'}, pdf
    transport = ControlledHTTP(user_agent='Navigator synthetic integration fixture', min_interval=0,
        resolver=lambda host, port, **kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', port))])
    fetcher = Crawl4AIFetcher(transport)
    web = PublicWebTools(discovery=Discovery(), fetcher=fetcher)
    services = Services(reasoning=create_reasoning_services(ModelSettings(api_key='fixture-only'),
        transport=httpx.MockTransport(synthetic_transport)),
        backbone=create_backbone(h.store.engine, h.store.artifacts, FixtureEmbedder(), observations=fetcher.observations),
        web=web, pdf=h.pdf)
    created = h.store.create(h.access, 'combined', {'prompt': 'Public glucose sensor research'}, 'request')
    assert await Worker(RuntimeApplication(h.store, services), checkpoint_factory=h.checkpoint).run_once(h.access)
    run_id, case_id = UUID(created['run_id']), UUID(created['case_id'])
    assert h.store.run_view(h.access, case_id, run_id)['state'] == 'completed'
    with h.store.engine.connect() as c:
        research = c.execute(select(t.attempts.c.outputs).where(t.attempts.c.run_id == run_id,
            t.attempts.c.stage == 'runtime.node.register.1')).scalar_one()['value']
        rows = research['evidence']
        old = [row for row in rows if row['url'] == original['canonical_url']]
        new = [row for row in rows if row['url'] == fresh]
        assert len(old) == 1 and old[0]['document_version_id'] == str(original['document_version_id'])
        assert old[0]['origin'] == 'corpus' and old[0]['review_status'] == 'curated'
        assert old[0]['literal_text'] == original['body_text']
        assert len(new) == 1 and new[0]['origin'] == 'web' and new[0]['review_status'] == 'unreviewed'
        scope = c.execute(select(t.scopes).where(t.scopes.c.scope_id == UUID(new[0]['scope_id']))).mappings().one()
        assert scope['kind'] == 'case' and scope['case_id'] == case_id
        assert 'pinned_corpus_version_preferred_over_live_duplicate' in research['limitations']
        assert c.execute(select(t.versions.c.body_text).where(
            t.versions.c.document_version_id == original['document_version_id'])).scalar_one() == original['body_text']
