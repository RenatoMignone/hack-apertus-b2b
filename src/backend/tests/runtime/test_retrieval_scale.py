"""Opt-in integration-scale probe; only the isolated test harness database."""
from time import perf_counter
import json
from sqlalchemy import text
import pytest

from backend.data.database import transaction
from backend.data.fixtures import FixtureEmbedder
from backend.data.retrieval.hybrid import HybridSearch
from backend.tests.runtime.benchmark_capture import seed
from backend.tests.runtime.test_live_corpus import live_users, start

pytestmark = pytest.mark.integration


def test_restricted_live_retrieval_at_twenty_thousand_chunks(harness, live_users):
    seed(harness.store.engine,harness.store.artifacts,harness.fixture,200)
    store, access=live_users[0]
    context, plan=start(store,access,'scale')
    with transaction(store.engine,access) as c:
        count=c.execute(text('SELECT count(*) FROM retrieval.snapshot_chunks WHERE snapshot_id=:id'), {'id':context.snapshot_id}).scalar_one()
        assert count==20004
        explain='\n'.join(c.execute(text('EXPLAIN SELECT chunk_id FROM retrieval.snapshot_chunks WHERE snapshot_id=:id'), {'id':context.snapshot_id}).scalars())
        assert 'hashed SubPlan' in explain
    started=perf_counter()
    result=HybridSearch(store.engine,FixtureEmbedder()).search(access,plan)
    assert len(result.hits)==30
    assert all(h.snapshot_id==context.snapshot_id for h in result.hits)
    print(json.dumps({'synthetic_restricted_chunks':count,'search_seconds':round(perf_counter()-started,3),'hits':len(result.hits)}))
