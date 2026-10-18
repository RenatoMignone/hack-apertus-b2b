"""Parse discovery links only; search snippets never become evidence."""
from html.parser import HTMLParser
import ipaddress
from urllib.parse import parse_qs, urljoin, urlsplit

from backend.contracts.pipeline import canonical_url
from backend.contracts.services import ServiceUnavailable


SEARCH_ORIGIN = "https://html.duckduckgo.com"


def result_url(value):
    try:
        value = urljoin(SEARCH_ORIGIN, value)
        parts = urlsplit(value)
    except ValueError:
        return None
    if parts.hostname in {"duckduckgo.com", "html.duckduckgo.com"}:
        if parts.path != "/l/":
            return None
        value = parse_qs(parts.query).get("uddg", [""])[0]
    try:
        value = canonical_url(value)
        parts = urlsplit(value)
        host = parts.hostname
        if parts.port not in {None, 80, 443} or not host or "." not in host:
            return None
        if host in {"duckduckgo.com", "html.duckduckgo.com"} or host.endswith((".localhost", ".local", ".internal")):
            return None
        try:
            if not ipaddress.ip_address(host).is_global:
                return None
        except ValueError:
            pass  # DNS/public-IP checks happen before any source fetch, not here.
        return value
    except ValueError:
        return None


class _Results(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.empty, self.blocked = [], False, False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get("class", "").split()
        if attrs.get("id") in {"challenge-form", "anomaly-form"}:
            self.blocked = True
        if "no-results" in classes:
            self.empty = True
        if tag == "a" and "result__a" in classes:
            url = result_url(attrs.get("href", ""))
            if url and url not in self.links:
                self.links.append(url)


def parse_results(html, limit):
    parser = _Results()
    parser.feed(html)
    if parser.blocked or (not parser.links and not parser.empty):
        # Changed markup, advertisements only and challenges are not zero matches.
        raise ServiceUnavailable()
    return parser.links[:limit]
