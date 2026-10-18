import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from backend.contracts.data import ModelConfiguration
from backend.contracts.services import BudgetExceeded, ServiceUnavailable
from backend.ingestion.evaluation import ReviewedQuery, recall_at_10
from backend.ingestion.classification import MeSHClassification, MeSHClassifier
from backend.ingestion.normalize import chunks, normalize, publication_date
from backend.ingestion.web import PublicWebTools, SafeHTTP
from backend.models.embeddings.local import LocalEmbedder
from backend.models.reranking.local import LocalReranker


class Tokenizer:
    def encode(self, text, paired=None, **kwargs):
        return list(range(len(text) + len(paired or "") + 2))


class Encoder:
    def encode(self, texts, **kwargs):
        assert kwargs["prompt"] == ""
        return [[3.0, 4.0] for text in texts]


def configuration():
    return ModelConfiguration(role="embedding", logical_name="fixture", artifact="fixture", revision="fixture-1",
        adapter_version="fixture-1", tokenizer="fixture", input_limit=100, dimension=2, normalization="l2",
        query_template="query: {text}", document_template="title: {title} | text: {text}", precision="float32",
        license="fixture", verified=True, test_only=True)


def test_faithful_html_unicode_dates_and_chunks():
    html = '<html lang="de"><title>Glukose</title><meta property="article:published_time" content="2026-04-10T09:00:00Z"><nav>hidden</nav><h1>Über uns</h1><p>Équipe 🧬 &amp; Forschung.</p></html>'
    document = normalize(html.encode(), "text/html")
    assert document.body == "Über uns\nÉquipe 🧬 & Forschung."
    assert document.language == "de"
    assert document.published_at == datetime(2026, 4, 10, 9, tzinfo=timezone.utc)
    assert publication_date("2026-04-10") is None
    assert publication_date("not-a-date") is None
    spans = chunks(document, lambda value, headings: len(value) < 10, max_characters=15)
    assert "".join(span.text for span in spans) == document.body
    for span in spans:
        span.validate_body(document.body)


def test_encoding_exact_templates_limits_and_normalization():
    embedder = LocalEmbedder(configuration(), Encoder(), Tokenizer())
    assert embedder.document_input("CGM", "Title") == "title: Title | text: CGM"
    assert embedder.embed_query("CGM") == [0.6, 0.8]
    assert embedder.embed_documents([embedder.document_input("CGM")]) == [[0.6, 0.8]]
    with pytest.raises(ValueError, match="truncation"):
        embedder.embed_query("x" * 100)
    assert embedder.benchmark(["one"])["count"] == 1


def test_reranker_budget_and_invalid_scores():
    model = SimpleNamespace(predict=lambda pairs, **kwargs: [float("nan") for pair in pairs])
    reranker = LocalReranker(model, Tokenizer(), input_limit=10, config_hash="fixture")
    with pytest.raises(ValueError, match="invalid"):
        reranker.score("a", ["b"])
    with pytest.raises(ValueError, match="truncation"):
        reranker.score("a", ["b" * 20])


@pytest.mark.parametrize("address", ["127.0.0.1", "10.1.0.1", "169.254.169.254", "::1", "192.168.10.230", "224.0.0.1"])
def test_private_network_rejected(address):
    transport = SafeHTTP(user_agent="NavigatorTest", resolver=lambda *args, **kwargs: [(None, None, None, None, (address, 443))])
    with pytest.raises(ValueError):
        transport.target("https://public.example/")


def test_offline_does_not_call_providers_and_deadlines_are_enforced():
    context = SimpleNamespace(mode="offline", deadline_at=datetime.now(timezone.utc) + timedelta(seconds=10),
        access=SimpleNamespace(principal_id=uuid4()), run_id=uuid4(), request_id="one", max_tool_calls=0)
    tools = PublicWebTools()
    assert asyncio.run(tools.fetch(["https://example.org"], context)).status == "unavailable"
    with pytest.raises(ServiceUnavailable):
        asyncio.run(tools.discover("glucose", context))
    context.mode = "connected"
    tools.fetcher = SimpleNamespace(fetch=lambda url: pytest.fail("budget must stop the provider"))
    with pytest.raises(BudgetExceeded):
        asyncio.run(tools.fetch(["https://example.org"], context))


def test_reviewed_recall_counts_unique_entities_not_passages():
    labels = [ReviewedQuery("one", frozenset({"expert", "unit"}), "reviewer", "monitoring")]
    assert recall_at_10(labels, [["expert"] * 20 + ["unit"]])["score"] == 1.0
    with pytest.raises(ValueError):
        recall_at_10([], [])


def test_meaning_classifier_validates_meSH_codes_and_exact_support():
    from backend.contracts.services import InvalidModelOutput
    document = normalize(b"<title>Study</title><p>Diabetes research</p>", "text/html")
    vocabulary = {"concepts": [{"code": "C", "facet": "category", "labels": {"en": ["Diseases"]}}]}
    output = {"tags": [{"code": "C", "quote": document.body, "char_start": 0, "char_end": len(document.body)}]}
    model = SimpleNamespace(with_structured_output=lambda schema: SimpleNamespace(invoke=lambda messages: output))
    classifier = MeSHClassifier(model)
    assert classifier.classify(document, vocabulary)[0]["code"] == "C"
    output["tags"][0]["code"] = "C19.246"
    with pytest.raises(InvalidModelOutput):
        classifier.classify(document, vocabulary)


def test_mixed_public_private_dns_and_redirect_targets_are_rejected():
    addresses = [(None, None, None, None, (address, 443)) for address in ("8.8.8.8", "127.0.0.1")]
    transport = SafeHTTP(user_agent="NavigatorTest", resolver=lambda *args, **kwargs: addresses)
    with pytest.raises(ValueError):
        transport.target("https://example.org/")
    with pytest.raises(ValueError):
        transport.target("https://name:password@example.org/")


def test_model_cannot_return_more_than_three_topic_labels():
    from pydantic import ValidationError
    labels = [{"code": code, "quote": "source", "char_start": 0, "char_end": 6} for code in ["C19", "C14", "E07", "C04"]]
    with pytest.raises(ValidationError):
        MeSHClassification(tags=labels)
