from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest

from backend.contracts.services import ServiceUnavailable
from backend.ingestion.searxng_discovery import SearXNGDiscovery, search_endpoint
from backend.ingestion.web import PublicWebTools


@pytest.mark.asyncio
async def test_explicit_engines_post_query_deduplicate_and_filter_leads():
    def handler(request):
        assert request.method == "POST" and request.url.path == "/search"
        assert "q=glucose" in request.content.decode() and "engines=duckduckgo%2Cyahoo" in request.content.decode()
        return httpx.Response(200, json={"results": [
            {"url": "https://www.unibe.ch/research#team", "engines": ["yahoo"]},
            {"url": "https://www.unibe.ch/research", "engines": ["duckduckgo"]},
            {"url": "http://127.0.0.1/private", "engines": ["yahoo"]}], "unresponsive_engines": []})
    adapter = SearXNGDiscovery("http://127.0.0.1:18888", transport=httpx.MockTransport(handler))
    assert await adapter.discover("glucose", limit=5) == ["https://www.unibe.ch/research"]


@pytest.mark.asyncio
async def test_repeated_queries_cache_only_url_leads_and_do_not_leak_mutations():
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(200, json={"results": [{"url": "https://www.unibe.ch/", "engines": ["yahoo"]}]})
    adapter = SearXNGDiscovery("http://localhost:18888", transport=httpx.MockTransport(handler))
    one = await adapter.discover("glucose", limit=3)
    one.append("https://unexpected.example/")
    assert await adapter.discover("glucose", limit=3) == ["https://www.unibe.ch/"]
    assert len(calls) == 1


@pytest.mark.parametrize("status,body", [(403, {}), (429, {}), (503, {}), (302, {}),
    (200, {"results": [], "unresponsive_engines": [["yahoo", "CAPTCHA"]]}),
    (200, {"results": [{"url": "https://example.org", "engines": ["unexpected"]}]}),
    (200, {"results": "wrong"}), (200, {})])
@pytest.mark.asyncio
async def test_blocks_and_protocol_failures_are_not_no_match(status, body):
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(status, json=body, headers={"Location": "https://other.example"})
    adapter = SearXNGDiscovery("http://localhost:18888", transport=httpx.MockTransport(handler))
    with pytest.raises(ServiceUnavailable):
        await adapter.discover("glucose", limit=3)
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_real_no_match_and_partial_diagnostics_are_distinct():
    adapter = SearXNGDiscovery("http://searxng:8080", transport=httpx.MockTransport(
        lambda request: httpx.Response(200, json={"results": [], "unresponsive_engines": []})))
    assert await adapter.discover("glucose", limit=3) == []
    adapter.transport = httpx.MockTransport(lambda request: httpx.Response(200, json={
        "results": [{"url": "https://www.unibe.ch/", "engines": ["yahoo"]}],
        "unresponsive_engines": [["duckduckgo", "too many requests"]]}))
    tools = PublicWebTools(discovery=adapter, fetcher=SimpleNamespace(fetch=lambda url: (_ for _ in ()).throw(ValueError())))
    context = SimpleNamespace(mode="connected", access=SimpleNamespace(principal_id=uuid4()), run_id=uuid4(),
        request_id="test", max_tool_calls=6, deadline_at=datetime.now(timezone.utc) + timedelta(seconds=10))
    urls = await tools.discover("glucose", context)
    result = await tools.fetch(urls, context)
    assert "web_search_partial_engines" in result.limitations
    assert "source_fetch_failed_or_policy_denied" in result.limitations


@pytest.mark.parametrize("url", ["file:///tmp/socket", "http://192.168.1.1", "https://user:secret@example.org",
    "https://example.org/search?token=secret", "https://example.org/other"])
def test_search_endpoint_is_fixed_server_configuration(url):
    with pytest.raises(ValueError):
        search_endpoint(url)


def test_runtime_factory_selects_searxng_without_key(monkeypatch):
    from backend.application.factories import web
    from backend.config.runtime import RuntimeSettings
    monkeypatch.setenv("WEB_DISCOVERY_PROVIDER", "searxng")
    monkeypatch.setenv("WEB_SEARCH_URL", "http://127.0.0.1:18888")
    monkeypatch.setenv("WEB_SEARCH_ENGINES", "duckduckgo,yahoo")
    settings = RuntimeSettings.from_env()
    assert isinstance(web(settings=settings, engine=None, artifacts=None).discovery, SearXNGDiscovery)


@pytest.mark.asyncio
async def test_ten_pages_share_run_budget_including_failed_fetches():
    from backend.config.runtime import RuntimeSettings
    from backend.contracts.services import BudgetExceeded

    adapter = SearXNGDiscovery("http://localhost:18888", transport=httpx.MockTransport(
        lambda request: httpx.Response(200, json={"results": [
            {"url": f"https://www.unibe.ch/page/{i}", "engines": ["yahoo"]}
            for i in range(20)]})))
    attempted = []
    def failed_fetch(url):
        attempted.append(url)
        raise ValueError("unavailable page")
    tools = PublicWebTools(discovery=adapter, fetcher=SimpleNamespace(fetch=failed_fetch))
    context = SimpleNamespace(mode="connected", access=SimpleNamespace(principal_id=uuid4()),
        run_id=uuid4(), request_id="ten-page-budget", max_tool_calls=RuntimeSettings().max_tool_calls,
        deadline_at=datetime.now(timezone.utc) + timedelta(seconds=10))
    urls = await tools.discover("glucose", context)
    assert len(urls) == 10
    result = await tools.fetch(urls, context)
    assert len(attempted) == 10
    assert result.status == "failed"
    with pytest.raises(BudgetExceeded):
        await tools.discover("follow-up query", context)
