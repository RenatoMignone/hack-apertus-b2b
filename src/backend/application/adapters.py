"""Trusted configuration-only factories; no hidden fixture or hosted fallback."""
from importlib import import_module

from backend.contracts.services import ServiceUnavailable


class Unavailable:
    async def _missing(self, *args, **kwargs):
        raise ServiceUnavailable()

    def __getattr__(self, name):
        return self._missing


def load_factory(spec, *, settings, engine, artifacts):
    if not spec:
        return Unavailable()
    module_name, name = spec.split(":", 1)
    if not module_name.startswith("backend.") or not name.isidentifier():
        raise ValueError("adapter factory must be a configured backend.module:function")
    return getattr(import_module(module_name), name)(settings=settings, engine=engine, artifacts=artifacts)


class Services:
    def __init__(self, *, reasoning, backbone, web=None, pdf=None, memory=None):
        self.reasoning, self.backbone, self.web, self.pdf = reasoning, backbone, web, pdf or Unavailable()
        self.memory = memory

    @classmethod
    def configured(cls, settings, engine, artifacts):
        def adapter(spec):
            return load_factory(spec, settings=settings, engine=engine, artifacts=artifacts)
        services = cls(reasoning=adapter(settings.reasoning_factory), backbone=adapter(settings.backbone_factory),
            web=adapter(settings.web_factory) if settings.mode == "connected" and settings.web_factory else None,
            pdf=adapter(settings.pdf_factory))
        from backend.application.factories import connect_observations
        connect_observations(services.backbone, services.web)
        if settings.case_memory_enabled:
            from backend.application.case_memory import CaseMemory
            from backend.application.factories import ConfiguredEmbedding
            from backend.application.persistence.store import RuntimeStore
            services.memory = CaseMemory(RuntimeStore(engine, settings, artifacts), ConfiguredEmbedding(settings),
                minimum_score=settings.case_memory_min_score)
        return services
