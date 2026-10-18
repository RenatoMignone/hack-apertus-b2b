"""Keyless search in an isolated Playwright browser; no arbitrary shell tools.

Only DuckDuckGo HTML search documents are rendered. Existing SafeHTTP performs
robots-aware, DNS-pinned, byte-limited acquisition. The browser is offline and
all other requests are aborted; source pages use the separate existing fetcher.
"""
import asyncio
import os
from pathlib import Path
from urllib.parse import urlencode, urlsplit

from backend.contracts.services import ServiceUnavailable
from backend.ingestion.browser_results import SEARCH_ORIGIN, parse_results
from backend.ingestion.web import SafeHTTP


class BrowserDiscovery:
    def __init__(self, *, user_agent, executable_path="", timeout=25, transport=None):
        if not user_agent.strip() or not 1 <= timeout <= 60:
            raise ValueError("browser discovery requires a user agent and 1–60 second timeout")
        if executable_path and not Path(executable_path).is_absolute():
            raise ValueError("browser executable must be an absolute server-configured path")
        self.user_agent, self.executable_path, self.timeout = user_agent, executable_path, timeout
        self.transport = transport or SafeHTTP(user_agent=user_agent, max_bytes=2_000_000,
            timeout=min(timeout, 15), allowed_hosts=("html.duckduckgo.com",))
        self.lock = asyncio.Lock()

    @staticmethod
    def permits(request, page):
        parts = urlsplit(request.url)
        return (request.method == "GET" and request.is_navigation_request()
            and request.frame == page.main_frame and parts.scheme == "https"
            and parts.hostname == "html.duckduckgo.com" and parts.port in {None, 443}
            and not parts.username and not parts.password and parts.path == "/html/")

    async def _search(self, query, limit):
        from playwright.async_api import async_playwright
        async with async_playwright() as playwright:
            # Do not pass provider/DB secrets, proxy variables or personal profiles.
            environment = {key: os.environ[key] for key in
                ("PATH", "HOME", "TMPDIR", "LANG", "XDG_RUNTIME_DIR") if key in os.environ}
            options = dict(headless=True, chromium_sandbox=True, env=environment)
            if self.executable_path:
                options["executable_path"] = self.executable_path
            browser = await playwright.chromium.launch(**options)
            try:
                context = await browser.new_context(offline=True, java_script_enabled=False,
                    service_workers="block", accept_downloads=False, permissions=[], user_agent=self.user_agent)
                page = await context.new_page()
                failures = []

                async def acquire(route):
                    if not self.permits(route.request, page):
                        await route.abort()
                        return
                    try:
                        observation = await asyncio.to_thread(self.transport.fetch, route.request.url)
                        if observation.mime.split(";")[0] not in {"text/html", "application/xhtml+xml"}:
                            raise ValueError("search response must be HTML")
                        await route.fulfill(status=200, body=observation.raw, headers={
                            "Content-Type": "text/html; charset=utf-8",
                            "Content-Security-Policy": "default-src 'none'; form-action 'none'"})
                    except (OSError, ValueError, TimeoutError, ServiceUnavailable):
                        failures.append(True)
                        await route.abort()

                await context.route("**/*", acquire)
                await page.goto(SEARCH_ORIGIN + "/html/?" + urlencode({"q": query}),
                    wait_until="domcontentloaded", timeout=int(self.timeout * 1000))
                if failures:
                    raise ServiceUnavailable()
                return parse_results(await page.content(), limit)
            finally:
                await browser.close()

    async def discover(self, query, *, limit):
        if not isinstance(query, str) or not query.strip() or len(query) > 500 or not 1 <= limit <= 10:
            raise ValueError("bounded query and 1–10 results required")
        try:
            async with asyncio.timeout(self.timeout):
                async with self.lock:
                    return await self._search(query, limit)
        except asyncio.CancelledError:
            raise
        except Exception:
            # Playwright errors can include queries, HTML or launch environment.
            # Missing assets, HTTP blocks and timeouts all fail without fallback.
            raise ServiceUnavailable() from None
