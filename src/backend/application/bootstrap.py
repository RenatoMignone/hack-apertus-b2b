"""Composition root. Factories are trusted operator config, never browser values."""
import os
from threading import Lock

from backend.application.adapters import Services
from backend.application.persistence.store import RuntimeStore
from backend.application.service import RuntimeApplication
from backend.config.runtime import RuntimeSettings
from backend.config.settings import Settings
from backend.contracts.services import ServiceUnavailable
from backend.data.database import check_schema, engine_for


class Registry:
    def __init__(self, settings=None):
        self.settings = settings or RuntimeSettings.from_env()
        self.apps = {}
        self.lock = Lock()

    def application(self, binding):
        # Factories run once per authenticated DB binding, not on every request.
        key = (binding.principal_id, binding.namespace, binding.database_url_env)
        with self.lock:
            if key not in self.apps:
                url = os.getenv(binding.database_url_env)
                if not url:
                    raise ServiceUnavailable()
                engine = engine_for(url)
                check_schema(engine)  # never migrate at application startup
                artifacts = Settings.from_env(database_url=url).artifact_store()
                try:
                    services = Services.configured(self.settings, engine, artifacts)
                except Exception:
                    engine.dispose()
                    raise ServiceUnavailable() from None
                from backend.observability.tracing import SafeTracer, langfuse_tracer
                tracer = SafeTracer()
                if self.settings.langfuse_url and self.settings.langfuse_public_key and self.settings.langfuse_secret_key:
                    try:
                        tracer = langfuse_tracer(self.settings.langfuse_url, self.settings.langfuse_public_key, self.settings.langfuse_secret_key)
                    except Exception:
                        tracer.degraded = True  # a diagnostic outage never blocks business work
                self.apps[key] = RuntimeApplication(RuntimeStore(engine, self.settings, artifacts), services, tracer=tracer)
            return self.apps[key]

    def close(self):
        for app in self.apps.values():
            app.store.engine.dispose()
            if app.tracer:
                app.tracer.close()
