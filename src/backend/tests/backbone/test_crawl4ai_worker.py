import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from backend.contracts.services import ServiceUnavailable
from backend.ingestion.crawl4ai_markdown import convert


def test_worker_receives_bounded_content_without_secrets_or_shell(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "synthetic-secret")
    monkeypatch.setenv("DATABASE_URL", "synthetic-database")
    def run(command, **options):
        assert command[1] == "-I" and Path(command[2]).name == "crawl4ai_worker.py"
        assert "LLM_API_KEY" not in options["env"] and "DATABASE_URL" not in options["env"]
        assert "shell" not in options and options["timeout"] == 20
        assert json.loads(options["input"]) == {"html": "<p>Glucose</p>", "base_url": "https://example.org/"}
        return SimpleNamespace(returncode=0, stdout=b'{"markdown":"Glucose"}')
    monkeypatch.setattr(subprocess, "run", run)
    assert convert("<p>Glucose</p>", "https://example.org/", python_executable=sys.executable) == "Glucose"


@pytest.mark.parametrize("output,code", [(b'not json', 0), (b'{}', 0), (b'{"markdown":[]}', 0),
    (b'{"markdown":""}', 0), (b'{"markdown":"valid"}', 1)])
def test_failed_workers_never_silently_substitute_content(monkeypatch, output, code):
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=code, stdout=output))
    with pytest.raises(ServiceUnavailable):
        convert("<p>Text</p>", "https://example.org/", python_executable=sys.executable)


def test_missing_interpreter_and_timeout_are_explicit_unavailability(monkeypatch):
    with pytest.raises(ServiceUnavailable):
        convert("Text", "https://example.org/", python_executable="relative-python")
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("worker", 20)
    monkeypatch.setattr(subprocess, "run", timeout)
    with pytest.raises(ServiceUnavailable):
        convert("Text", "https://example.org/", python_executable=sys.executable)


def test_fetcher_passes_only_sanitized_acquired_text_and_retains_observation(monkeypatch):
    from datetime import datetime, timezone
    from backend.contracts.data import content_hash
    from backend.ingestion.web import Crawl4AIFetcher, FetchObservation
    observation = FetchObservation("https://example.org/", "https://example.org/",
        b'<title>Study</title><script>untrusted()</script><p>Glucose &amp; sensors</p>',
        "text/html", 200, datetime.now(timezone.utc))
    def conversion(html, url, **kwargs):
        assert "<script>" not in html and "untrusted()" not in html
        assert "Glucose &amp; sensors" in html and kwargs["python_executable"] == sys.executable
        return "Glucose & sensors"
    monkeypatch.setattr("backend.ingestion.crawl4ai_markdown.convert", conversion)
    fetcher = Crawl4AIFetcher(SimpleNamespace(fetch=lambda url: observation), python_executable=sys.executable)
    result = fetcher.fetch(observation.final_url)
    assert result.content == "Glucose & sensors" and result.content_hash == content_hash(result.content.encode())
    assert fetcher.observations[(result.canonical_url, result.content_hash)] == observation
