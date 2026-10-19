import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Barrier, Event, Lock
from time import monotonic, sleep
from types import SimpleNamespace
from uuid import uuid4

import pytest

from backend.contracts.data import content_hash
from backend.contracts.pipeline import FetchedSource
from backend.contracts.services import BudgetExceeded
from backend.ingestion.web import PublicWebTools, SafeHTTP


def context(budget=10):
    return SimpleNamespace(mode='connected', access=SimpleNamespace(principal_id=uuid4()),
        run_id=uuid4(), request_id='parallel-test', max_tool_calls=budget,
        deadline_at=datetime.now(timezone.utc)+timedelta(seconds=5))


def source(url):
    return FetchedSource(title='Fixture', url=url, canonical_url=url, content='Fixture text',
        content_hash=content_hash(b'Fixture text'), fetched_at=datetime.now(timezone.utc))


@pytest.mark.asyncio
async def test_pages_overlap_with_limit_three_and_keep_discovery_order():
    guard, barrier = Lock(), Barrier(3)
    active, peak = 0, 0
    def fetch(url):
        nonlocal active, peak
        with guard:
            active += 1
            peak = max(peak, active)
        try:
            barrier.wait(timeout=2)
            sleep((5-int(url.rsplit('/', 1)[1]))*.002)
            return source(url)
        finally:
            with guard:
                active -= 1
    urls = [f'https://fixture.invalid/{i}' for i in range(6)]
    tools = PublicWebTools(fetcher=SimpleNamespace(fetch=fetch))
    result = await tools.fetch(urls, context())
    assert peak == 3
    assert [s.url for s in result.sources] == urls


@pytest.mark.asyncio
async def test_failed_and_duplicate_pages_do_not_lose_successful_results():
    attempted = []
    def fetch(url):
        attempted.append(url)
        if url.endswith('/bad'):
            raise ValueError('policy denied')
        return source(url)
    tools = PublicWebTools(fetcher=SimpleNamespace(fetch=fetch))
    urls = ['https://fixture.invalid/good', 'https://fixture.invalid/bad']
    result = await tools.fetch([*urls, urls[0]], context())
    assert result.status == 'completed'
    assert [s.url for s in result.sources] == [urls[0]]
    assert sorted(attempted) == sorted(urls)
    assert result.limitations == ['source_fetch_failed_or_policy_denied']


@pytest.mark.asyncio
async def test_concurrent_attempts_cannot_exceed_run_budget():
    attempted = []
    def fetch(url):
        attempted.append(url)
        return source(url)
    tools = PublicWebTools(fetcher=SimpleNamespace(fetch=fetch))
    ctx = context(budget=2)
    with pytest.raises(BudgetExceeded):
        await tools.fetch([f'https://fixture.invalid/{i}' for i in range(6)], ctx)
    assert len(attempted) <= 2
    assert next(iter(tools.calls.values())) == 2
    with pytest.raises(BudgetExceeded):
        await tools.fetch(['https://fixture.invalid/later'], ctx)


def test_transport_serializes_same_host_including_redirect_requests():
    class Transport(SafeHTTP):
        active = 0
        peak = 0
        def _serialized_request(self, url, deadline):
            self.active += 1
            self.peak = max(self.peak, self.active)
            try:
                sleep(.01)
                return url
            finally:
                self.active -= 1
    transport = Transport(user_agent='Fixture')
    with ThreadPoolExecutor(max_workers=3) as pool:
        values = list(pool.map(lambda i: transport._request(
            f'https://fixture.invalid/{i}', monotonic()+2), range(6)))
    assert len(values) == 6 and transport.peak == 1


def test_transport_wait_for_host_lock_respects_deadline():
    transport = SafeHTTP(user_agent='Fixture')
    lock = transport.request_locks[hash('fixture.invalid') % len(transport.request_locks)]
    with lock:
        with pytest.raises(TimeoutError):
            transport._request('https://fixture.invalid/', monotonic())


@pytest.mark.asyncio
async def test_cancellation_does_not_admit_waiting_pages():
    release, started, guard = Event(), Event(), Lock()
    attempted = []
    def fetch(url):
        with guard:
            attempted.append(url)
            if len(attempted) == 3:
                started.set()
        release.wait(timeout=2)
        return source(url)
    tools = PublicWebTools(fetcher=SimpleNamespace(fetch=fetch))
    task = asyncio.create_task(tools.fetch(
        [f'https://fixture.invalid/{i}' for i in range(10)], context()))
    try:
        assert await asyncio.to_thread(started.wait, 2)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert len(attempted) == 3
    finally:
        release.set()
        if not task.done():
            task.cancel()
        await asyncio.gather(task, return_exceptions=True)
