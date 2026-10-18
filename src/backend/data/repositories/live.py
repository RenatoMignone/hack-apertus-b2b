"""Resolve a case-owned live capture without publication or corpus write grants."""
from pathlib import Path

from sqlalchemy import select, text

from backend.contracts.data import ModelConfiguration
from backend.contracts.services import ServiceUnavailable
from backend.data import schema as t


def capture_live_corpus(connection, settings, case_id, profile_id):
    if not settings.embedding_configuration:
        raise ServiceUnavailable()
    model = ModelConfiguration.model_validate_json(
        Path(settings.embedding_configuration).read_text(encoding="utf-8-sig"))
    model.require_resolved()
    snapshot_id = connection.execute(text("""
        SELECT ops.capture_live_corpus(:case,:profile,:taxonomy,:embedding)
    """), {"case": case_id, "profile": profile_id, "taxonomy": settings.live_taxonomy_version_id,
            "embedding": model.config_hash}).scalar_one()
    return connection.execute(select(t.snapshots).where(t.snapshots.c.snapshot_id == snapshot_id)).mappings().one()
