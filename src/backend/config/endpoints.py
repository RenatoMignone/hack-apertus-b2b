"""One explicit local inference policy, shared by bootstrap and model transport."""
from urllib.parse import urlsplit

LOCAL_INFERENCE_HOSTS = frozenset({"localhost", "127.0.0.1", "::1", "apertus", "llm"})


def local_inference_url(value: str) -> bool:
    endpoint = urlsplit(value)
    return (endpoint.scheme in {"http", "https"} and endpoint.hostname in LOCAL_INFERENCE_HOSTS
            and not any((endpoint.username, endpoint.password, endpoint.query, endpoint.fragment)))
