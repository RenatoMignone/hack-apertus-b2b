import asyncio
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
import http.client
import ipaddress
import socket
import ssl
import json
from time import monotonic
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.parse import urlencode
from urllib.robotparser import RobotFileParser

from backend.contracts.data import content_hash
from backend.contracts.pipeline import FetchedSource, canonical_url
from backend.contracts.services import BudgetExceeded, ServiceUnavailable, WebResearchResult
from backend.ingestion.normalize import normalize


@dataclass(frozen=True)
class FetchObservation:
    requested_url: str
    final_url: str
    raw: bytes
    mime: str
    status: int
    fetched_at: datetime
    redirects: tuple[str, ...] = ()


class SafeHTTP:
    def __init__(self, *, user_agent, max_bytes=8_000_000, timeout=15, max_redirects=4,
                 allowed_hosts=(), resolver=socket.getaddrinfo, min_interval=1.0):
        if not user_agent.strip() or max_bytes < 1 or timeout <= 0 or max_redirects < 0 or min_interval < 0:
            raise ValueError("explicit user agent and positive network budgets required")
        self.user_agent, self.max_bytes, self.timeout = user_agent, max_bytes, timeout
        self.max_redirects, self.allowed_hosts, self.resolver = max_redirects, set(allowed_hosts), resolver
        self.min_interval = min_interval
        self.last_request = {}

    def target(self, url):
        normalized = canonical_url(url)
        parts = urlsplit(normalized)
        if parts.port not in {None, 80, 443} or (self.allowed_hosts and parts.hostname not in self.allowed_hosts):
            raise ValueError("source is outside the permitted network policy")
        addresses = self.resolver(parts.hostname, parts.port or (443 if parts.scheme == "https" else 80), type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global
                or ipaddress.ip_address(item[4][0]).is_multicast for item in addresses):
            raise ValueError("private, local, special or unresolved network target denied")
        return normalized, parts, addresses[0][4][0]

    def _request(self, url, deadline):
        normalized, parts, address = self.target(url)
        remaining = deadline - monotonic()
        if remaining <= 0:
            raise TimeoutError("network deadline exceeded")
        wait = self.min_interval - (monotonic() - self.last_request.get(parts.hostname, 0))
        if wait > 0:
            if wait >= remaining:
                raise TimeoutError("network politeness budget exceeded")
            import time
            time.sleep(wait)
        remaining = deadline - monotonic()
        port = parts.port or (443 if parts.scheme == "https" else 80)
        connection = (http.client.HTTPSConnection(parts.hostname, port, timeout=min(self.timeout, remaining),
            context=ssl.create_default_context()) if parts.scheme == "https" else
            http.client.HTTPConnection(parts.hostname, port, timeout=min(self.timeout, remaining)))
        connection._create_connection = lambda target, timeout, source_address=None: socket.create_connection(
            (address, port), timeout, source_address)
        try:
            self.last_request[parts.hostname] = monotonic()
            path = urlunsplit(("", "", parts.path or "/", parts.query, ""))
            connection.request("GET", path, headers={"User-Agent": self.user_agent, "Accept-Encoding": "identity"})
            response = connection.getresponse()
            headers = dict(response.getheaders())
            payload = bytearray()
            while True:
                if monotonic() >= deadline:
                    raise TimeoutError("network deadline exceeded")
                data = response.read(min(65536, self.max_bytes + 1 - len(payload)))
                if not data:
                    break
                payload.extend(data)
                if len(payload) > self.max_bytes:
                    raise ValueError("source byte budget exceeded")
            return normalized, response.status, {key.lower(): value for key, value in headers.items()}, bytes(payload)
        finally:
            connection.close()

    def _redirected(self, url, deadline, *, check_robots):
        requested, redirects = canonical_url(url), []
        current = requested
        for index in range(self.max_redirects + 1):
            self.target(current)
            if check_robots:
                parts = urlsplit(current)
                robots_url = urlunsplit((parts.scheme, parts.netloc, "/robots.txt", "", ""))
                _, status, _, body, _ = self._redirected(robots_url, deadline, check_robots=False)
                if status != 404:
                    if status != 200:
                        raise ValueError("robots policy unavailable or denied")
                    policy = RobotFileParser()
                    policy.parse(body.decode("utf-8", errors="replace").splitlines())
                    if not policy.can_fetch(self.user_agent, current):
                        raise ValueError("robots policy denies this source")
                    delay = policy.crawl_delay(self.user_agent) or policy.crawl_delay("*")
                    if delay and delay > self.min_interval:
                        raise ValueError("source crawl-delay exceeds configured fetch policy")
            final, status, headers, raw = self._request(current, deadline)
            if status not in {301, 302, 303, 307, 308}:
                return final, status, headers, raw, tuple(redirects)
            if index == self.max_redirects or not headers.get("location"):
                raise ValueError("source redirect budget exceeded")
            current = canonical_url(urljoin(final, headers["location"]))
            redirects.append(current)
        raise ValueError("source redirect failed")

    def fetch(self, url):
        final, status, headers, raw, redirects = self._redirected(url, monotonic() + self.timeout, check_robots=True)
        if status != 200 or headers.get("content-encoding", "identity") != "identity":
            raise ValueError("source returned an unsupported HTTP response")
        return FetchObservation(canonical_url(url), final, raw, headers.get("content-type", ""), status,
            datetime.now(timezone.utc), redirects)


class Crawl4AIFetcher:
    def __init__(self, transport: SafeHTTP):
        self.transport = transport
        self.observations = OrderedDict()

    def fetch(self, url):
        try:
            from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
        except ImportError as error:
            raise ServiceUnavailable() from error
        observation = self.transport.fetch(url)
        document = normalize(observation.raw, observation.mime, fallback_title=observation.final_url)
        if observation.mime.split(";")[0] in {"text/html", "application/xhtml+xml"}:
            from html import escape
            cleaned = "<article>" + "".join("<p>" + escape(line) + "</p>" for line in document.body.splitlines()) + "</article>"
            markdown = DefaultMarkdownGenerator().generate_markdown(cleaned_html=cleaned, base_url=observation.final_url)
            body = markdown.raw_markdown.strip()
        else:
            body = document.body
        source = FetchedSource(title=document.title, url=observation.requested_url, canonical_url=observation.final_url,
            content=body, content_hash=content_hash(body.encode()), fetched_at=observation.fetched_at,
            published_at=document.published_at)
        self.observations[(source.canonical_url, source.content_hash)] = observation
        while len(self.observations) > 64:
            self.observations.popitem(last=False)
        return source


class PublicWebTools:
    def __init__(self, *, discovery=None, fetcher=None, max_pages=5):
        if not 1 <= max_pages <= 10:
            raise ValueError("web page budget must be between one and ten")
        self.discovery, self.fetcher, self.max_pages = discovery, fetcher, max_pages
        self.calls = OrderedDict()

    def _budget(self, context):
        if datetime.now(timezone.utc) >= context.deadline_at:
            raise BudgetExceeded()
        key = (context.access.principal_id, context.run_id, context.request_id)
        count = self.calls.get(key, 0)
        if count >= context.max_tool_calls:
            raise BudgetExceeded()
        self.calls[key] = count + 1
        self.calls.move_to_end(key)
        while len(self.calls) > 1024:
            self.calls.popitem(last=False)

    async def discover(self, query, context):
        if context.mode == "offline" or self.discovery is None:
            raise ServiceUnavailable()
        if not query.strip() or len(query) > 500:
            raise ValueError("bounded minimal public discovery query required")
        self._budget(context)
        try:
            async with asyncio.timeout(max(0.001, (context.deadline_at - datetime.now(timezone.utc)).total_seconds())):
                urls = await self.discovery.discover(query, limit=self.max_pages)
            return list(dict.fromkeys(canonical_url(url) for url in urls))[:self.max_pages]
        except (TimeoutError, OSError) as error:
            raise ServiceUnavailable() from error

    async def fetch(self, urls, context):
        if context.mode == "offline" or self.fetcher is None:
            return WebResearchResult(status="unavailable", limitations=["web_fetch_unavailable"])
        if len(urls) > self.max_pages:
            raise BudgetExceeded()
        sources, limitations = [], []
        for url in dict.fromkeys(urls):
            self._budget(context)
            try:
                remaining = (context.deadline_at - datetime.now(timezone.utc)).total_seconds()
                async with asyncio.timeout(max(0.001, remaining)):
                    sources.append(await asyncio.to_thread(self.fetcher.fetch, canonical_url(url)))
            except ServiceUnavailable:
                limitations.append("crawl4ai_unavailable")
            except (ValueError, OSError, TimeoutError, UnicodeError):
                limitations.append("source_fetch_failed_or_policy_denied")
        return WebResearchResult(status="completed" if sources else "unavailable" if "crawl4ai_unavailable" in limitations else "failed",
            sources=sources, limitations=list(dict.fromkeys(limitations)))


def create_web_tools(*, discovery=None, user_agent=None, allowed_hosts=()):
    fetcher = Crawl4AIFetcher(SafeHTTP(user_agent=user_agent, allowed_hosts=allowed_hosts)) if user_agent else None
    return PublicWebTools(discovery=discovery, fetcher=fetcher)


class BraveDiscovery:
    def __init__(self, api_key, *, timeout=10):
        if not api_key or timeout <= 0:
            raise ValueError("explicit discovery key and timeout required")
        self.api_key, self.timeout = api_key, timeout

    def _discover(self, query, limit):
        connection = http.client.HTTPSConnection("api.search.brave.com", timeout=self.timeout)
        try:
            path = "/res/v1/web/search?" + urlencode({"q": query, "count": min(limit, 10)})
            connection.request("GET", path, headers={"Accept": "application/json", "X-Subscription-Token": self.api_key})
            response = connection.getresponse()
            raw = response.read(256001)
            if response.status != 200 or len(raw) > 256000:
                raise ServiceUnavailable()
            payload = json.loads(raw)
            return [canonical_url(item["url"]) for item in payload.get("web", {}).get("results", [])][:limit]
        except (ValueError, KeyError, OSError) as error:
            raise ServiceUnavailable() from error
        finally:
            connection.close()

    async def discover(self, query, *, limit):
        return await asyncio.to_thread(self._discover, query, limit)
