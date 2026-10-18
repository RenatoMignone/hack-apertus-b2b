"""Bounded keyless discovery through an explicitly configured private SearXNG."""
import asyncio
from collections import OrderedDict
from dataclasses import dataclass
from hashlib import sha256
import json
from time import monotonic
from urllib.parse import urlsplit

import httpx

from backend.contracts.services import ServiceUnavailable
from backend.ingestion.browser_results import result_url


@dataclass(frozen=True)
class DiscoveryResult:
    urls: list[str]
    limitations: list[str]


def search_endpoint(value):
    parsed = urlsplit(value)
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment or parsed.path not in {"", "/", "/search"}
            or (parsed.scheme == "http" and parsed.hostname not in {"127.0.0.1", "localhost", "::1", "searxng"})):
        raise ValueError("SearXNG requires an explicit private loopback/service HTTP or HTTPS endpoint")
    return value.rstrip("/") if parsed.path == "/search" else value.rstrip("/") + "/search"


class SearXNGDiscovery:
    def __init__(self, endpoint, *, engines=("duckduckgo", "yahoo"), timeout=12, transport=None):
        if not engines or len(engines) > 5 or any(not name.replace("_", "").isalnum() for name in engines):
            raise ValueError("configure one to five explicit search engines")
        self.endpoint, self.engines = search_endpoint(endpoint), tuple(dict.fromkeys(engines))
        self.timeout, self.transport = timeout, transport
        self.cache = OrderedDict()
        self.lock = asyncio.Lock()

    async def discover_with_diagnostics(self, query, *, limit):
        if not query.strip() or len(query) > 500 or not 1 <= limit <= 10:
            raise ValueError("bounded query and 1–10 results required")
        key = (sha256(query.encode()).hexdigest(), limit)
        async with asyncio.timeout(self.timeout):
            async with self.lock:
                cached = self.cache.get(key)
                if cached and monotonic() < cached[0]:
                    value = cached[1]
                    return DiscoveryResult(list(value.urls), list(value.limitations))
                value = await self._request(query, limit)
                # Cache URL leads only; actual source text is fetched again.
                self.cache[key] = (monotonic() + (30 if value.limitations else 300), value)
                self.cache.move_to_end(key)
                while len(self.cache) > 128:
                    self.cache.popitem(last=False)
                return DiscoveryResult(list(value.urls), list(value.limitations))

    async def _request(self, query, limit):
        try:
            async with asyncio.timeout(self.timeout):
                async with httpx.AsyncClient(transport=self.transport, trust_env=False, follow_redirects=False,
                        timeout=httpx.Timeout(self.timeout, connect=3)) as client:
                    async with client.stream("POST", self.endpoint, data={"q": query, "format": "json",
                            "engines": ",".join(self.engines), "language": "en", "safesearch": "1"}) as response:
                        if response.status_code != 200:
                            raise ServiceUnavailable()
                        body = bytearray()
                        async for chunk in response.aiter_bytes():
                            body.extend(chunk)
                            if len(body) > 2_000_000:
                                raise ServiceUnavailable()
                data = json.loads(body)
                rows, errors = data["results"], data.get("unresponsive_engines", [])
                if not isinstance(rows, list) or not isinstance(errors, list):
                    raise ValueError()
                urls = []
                for row in rows[:100]:
                    # Reject unexpected provider routing and unsafe URL leads.
                    if not isinstance(row, dict) or not isinstance(row.get("url"), str):
                        raise ValueError()
                    origins = row.get("engines", [row.get("engine")])
                    if not isinstance(origins, list) or not origins or not set(origins) <= set(self.engines):
                        raise ValueError()
                    url = result_url(row["url"])
                    if url and url not in urls:
                        urls.append(url)
                if not urls and (errors or rows):
                    raise ServiceUnavailable()
                return DiscoveryResult(urls[:limit], ["web_search_partial_engines"] if errors else [])
        except asyncio.CancelledError:
            raise
        except (httpx.HTTPError, ValueError, KeyError, TypeError, TimeoutError):
            raise ServiceUnavailable() from None

    async def discover(self, query, *, limit):
        try:
            return (await self.discover_with_diagnostics(query, limit=limit)).urls
        except TimeoutError:
            raise ServiceUnavailable() from None
