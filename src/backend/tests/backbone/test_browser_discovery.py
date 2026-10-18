import asyncio
from types import SimpleNamespace

import pytest

from backend.contracts.services import ServiceUnavailable
from backend.ingestion.browser_discovery import BrowserDiscovery
from backend.ingestion.browser_results import parse_results


def test_search_links_are_leads_only_and_tracking_wrappers_are_not_fetched():
    html = '''<a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fwww.unibe.ch%2Fresearch%23team">Bern</a>
        <a class="result__a" href="https://www.unibe.ch/research">Duplicate</a>
        <a class="result__a" href="https://www.artorg.unibe.ch/research">ARTORG</a>
        <a class="result__a" href="http://127.0.0.1/private">Private</a>
        <a class="result__a" href="https://user:password@example.com">Credential</a>
        <a class="result__a" href="javascript:alert(1)">Script</a>
        <a class="result__a" href="http://[malformed">Malformed URL</a>
        <a href="https://example.com/navigation">Navigation</a>'''
    assert parse_results(html, 5) == ["https://www.unibe.ch/research", "https://www.artorg.unibe.ch/research"]
    assert parse_results(html, 1) == ["https://www.unibe.ch/research"]


@pytest.mark.parametrize("html", ["<html>Changed markup</html>",
    '<form id="challenge-form"></form><a class="result__a" href="https://example.org">Fake</a>',
    '<a class="result__a" href="https://duckduckgo.com/y.js?ad=1">Ad</a>'])
def test_blocks_and_unrecognized_pages_are_unavailable_not_no_match(html):
    with pytest.raises(ServiceUnavailable):
        parse_results(html, 3)
    assert parse_results('<div class="no-results">No results</div>', 3) == []


def test_browser_can_only_render_fixed_search_origin_top_level_get():
    frame = object()
    page = SimpleNamespace(main_frame=frame)
    def request(**changes):
        return SimpleNamespace(**dict(url="https://html.duckduckgo.com/html/?q=glucose",
            method="GET", frame=frame, is_navigation_request=lambda: True) | changes)
    assert BrowserDiscovery.permits(request(), page)
    for change in [{"url": "http://127.0.0.1/"}, {"url": "https://html.duckduckgo.com.attacker.org/html/"},
                   {"url": "https://html.duckduckgo.com:444/html/"}, {"method": "POST"},
                   {"frame": object()}, {"is_navigation_request": lambda: False},
                   {"url": "https://html.duckduckgo.com/other"}]:
        assert not BrowserDiscovery.permits(request(**change), page)


@pytest.mark.asyncio
async def test_provider_failures_are_redacted_and_cancelled_runs_stay_cancelled(monkeypatch):
    discovery = BrowserDiscovery(user_agent="NavigatorTest", timeout=1)
    async def unavailable(*args):
        raise RuntimeError("private query or browser diagnostic")
    monkeypatch.setattr(discovery, "_search", unavailable)
    with pytest.raises(ServiceUnavailable) as error:
        await discovery.discover("glucose", limit=3)
    assert "private" not in str(error.value)
    async def cancelled(*args):
        raise asyncio.CancelledError()
    monkeypatch.setattr(discovery, "_search", cancelled)
    with pytest.raises(asyncio.CancelledError):
        await discovery.discover("glucose", limit=3)
    async def slow(*args):
        await asyncio.sleep(10)
    monkeypatch.setattr(discovery, "_search", slow)
    with pytest.raises(ServiceUnavailable):
        await discovery.discover("glucose", limit=3)


@pytest.mark.asyncio
async def test_invalid_queries_never_start_browser(monkeypatch):
    discovery = BrowserDiscovery(user_agent="NavigatorTest")
    async def forbidden(*args):
        pytest.fail("invalid input must not launch a browser")
    monkeypatch.setattr(discovery, "_search", forbidden)
    for query, limit in [("", 1), ("x" * 501, 1), ("glucose", 0), ("glucose", 11)]:
        with pytest.raises(ValueError):
            await discovery.discover(query, limit=limit)


def test_factory_uses_explicit_browser_or_api_provider_without_fallback():
    from backend.application.factories import web
    from backend.config.runtime import RuntimeSettings
    from backend.ingestion.web import BraveDiscovery
    assert isinstance(web(settings=RuntimeSettings(web_discovery_provider="browser", web_user_agent="NavigatorTest"),
        engine=None, artifacts=None).discovery, BrowserDiscovery)
    assert isinstance(web(settings=RuntimeSettings(web_discovery_provider="brave", brave_api_key="synthetic"),
        engine=None, artifacts=None).discovery, BraveDiscovery)
    assert web(settings=RuntimeSettings(web_discovery_provider="brave"), engine=None, artifacts=None).discovery is None
    with pytest.raises(ValueError):
        RuntimeSettings(web_discovery_provider="other")


def test_browser_settings_are_loaded_from_environment(monkeypatch):
    from backend.config.runtime import RuntimeSettings
    monkeypatch.setenv("WEB_DISCOVERY_PROVIDER", "browser")
    monkeypatch.setenv("WEB_BROWSER_EXECUTABLE", "/opt/chrome/chrome")
    monkeypatch.setenv("WEB_BROWSER_TIMEOUT_SECONDS", "15")
    settings = RuntimeSettings.from_env()
    assert settings.web_browser_executable == "/opt/chrome/chrome"
    assert settings.web_browser_timeout_seconds == 15
