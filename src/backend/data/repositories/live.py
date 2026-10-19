"""Resolve a case-owned live capture without publication or corpus write grants."""
from pathlib import Path
import logging
from time import monotonic
from sqlalchemy.exc import DBAPIError

from sqlalchemy import select, text

from backend.data.snapshot_projection import snapshot_metadata
from backend.contracts.data import ModelConfiguration
from backend.contracts.services import ServiceUnavailable
from backend.data import schema as t


def capture_live_corpus(connection, settings, case_id, profile_id):
    if not settings.embedding_configuration:
        raise ServiceUnavailable()
    model = ModelConfiguration.model_validate_json(
        Path(settings.embedding_configuration).read_text(encoding="utf-8-sig"))
    model.require_resolved()
    started = monotonic()
    timeout = connection.execute(text("SELECT current_setting('statement_timeout') AS previous, "
        "setting::int AS milliseconds FROM pg_settings WHERE name='statement_timeout'")).mappings().one()
    milliseconds = min(timeout['milliseconds'] or settings.capture_timeout_seconds * 1000,
                       settings.capture_timeout_seconds * 1000)
    connection.execute(text("SELECT set_config('statement_timeout',:value,true)"), {'value':str(milliseconds)})
    try:
        snapshot_id = connection.execute(text("""
            SELECT ops.capture_live_corpus(:case,:profile,:taxonomy,:embedding)
        """), {"case": case_id, "profile": profile_id, "taxonomy": settings.live_taxonomy_version_id,
                "embedding": model.config_hash}).scalar_one()
    except DBAPIError as error:
        if (getattr(error.orig, 'sqlstate', None) == '57014'
                and 'statement timeout' in getattr(getattr(error.orig, 'diag', None), 'message_primary', '')):
            logging.getLogger(__name__).warning('live_capture_timeout elapsed_seconds=%.3f', monotonic()-started)
            raise ServiceUnavailable() from None
        raise
    # On an error PostgreSQL aborts the transaction and rolls back SET LOCAL too.
    connection.execute(text("SELECT set_config('statement_timeout',:value,true)"), {'value':timeout['previous']})
    logging.getLogger(__name__).info('live_capture_completed elapsed_seconds=%.3f', monotonic()-started)
    return connection.execute(select(*snapshot_metadata()).where(t.snapshots.c.snapshot_id == snapshot_id)).mappings().one()
