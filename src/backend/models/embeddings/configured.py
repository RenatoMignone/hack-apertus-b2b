"""One encoder selection path for ingestion, benchmarks and runtime queries."""
def load_configured(configuration, settings, *, local_path=None):
    if settings.embedding_backend == "hf":
        from backend.models.embeddings.hosted import load_hf
        return load_hf(configuration, settings.embedding_endpoint_url, settings.hf_token,
                       settings.embedding_tokenizer_path, revision=settings.embedding_model_revision,
                       mode=settings.mode)
    from backend.models.embeddings.local import load_embeddinggemma
    path = local_path or settings.embedding_model_path
    if not path:
        from backend.contracts.services import ServiceUnavailable
        raise ServiceUnavailable()
    return load_embeddinggemma(configuration, path, device=settings.model_device)
