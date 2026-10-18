"""Prove fresh physical schema and runtime metadata agree after finalization."""
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import inspect, insert, select, text
from sqlalchemy.exc import DBAPIError

from backend.data import schema as t
from backend.data.schema_docs import REFERENCE, render


def test_schema_reference_is_current():
    assert REFERENCE.read_text() == render()


@pytest.mark.integration
def test_final_schema_has_no_retired_tables_and_matches_metadata(database):
    inspector = inspect(database)
    actual = {f"{schema}.{name}" for schema in ("corpus", "taxonomy", "retrieval", "cases", "ops")
              for name in inspector.get_table_names(schema=schema)}
    assert actual == set(t.metadata.tables)
    assert "legacy" not in inspector.get_schema_names()  # fresh installs create no empty archive
    for table in t.metadata.tables.values():
        columns = {column["name"]: column for column in inspector.get_columns(table.name, schema=table.schema)}
        assert set(columns) == set(table.columns.keys()), table.fullname
        for column in table.columns:
            assert columns[column.name]["nullable"] == column.nullable, (table.fullname, column.name)
        foreign_keys = {(tuple(fk["constrained_columns"]), fk["referred_schema"], fk["referred_table"],
                         tuple(fk["referred_columns"]))
                        for fk in inspector.get_foreign_keys(table.name, schema=table.schema)}
        expected = {(tuple(c.name for c in fk.columns), fk.referred_table.schema, fk.referred_table.name,
                     tuple(element.column.name for element in fk.elements)) for fk in table.foreign_key_constraints}
        assert foreign_keys == expected, table.fullname
        assert set(inspector.get_pk_constraint(table.name, schema=table.schema)["constrained_columns"]) == {
            column.name for column in table.primary_key}, table.fullname
        assert {index["name"] for index in inspector.get_indexes(table.name, schema=table.schema)
                if not index.get("duplicates_constraint")} == {index.name for index in table.indexes}, table.fullname


@pytest.mark.integration
def test_entity_types_and_duplicate_aliases_are_rejected(database, corpus):
    fixture, _ = corpus
    with pytest.raises(DBAPIError, match="entity_type_allowed"):
        with database.begin() as c:
            c.execute(insert(t.entities).values(entity_id=uuid4(), scope_id=UUID(fixture["scope_id"]),
                entity_type="arbitrary_table_name", display_label="Bad input"))
    with pytest.raises(DBAPIError):
        with database.begin() as c:
            c.execute(insert(t.aliases).values(alias_id=uuid4(), document_id=c.execute(
                select(t.documents.c.document_id).limit(1)).scalar_one(), url="https://duplicate.example"))
            c.execute(text("INSERT INTO corpus.document_aliases SELECT :id,created_at,document_id,url FROM corpus.document_aliases WHERE url='https://duplicate.example'"),
                      {"id": uuid4()})


@pytest.mark.integration
def test_dated_sources_and_relationship_snapshot_require_complete_support(database, corpus):
    from backend.contracts.data import Span
    from backend.data.fixtures import FixtureEmbedder
    from backend.data.repositories.corpus import CorpusRepository
    from backend.data.repositories.snapshots import SnapshotRepository
    from backend.tests.test_database import context

    fixture, artifacts = corpus
    access = context(fixture)
    repository = CorpusRepository(database, artifacts)
    with database.connect() as c:
        source = c.execute(select(t.sources.c.source_id).where(t.sources.c.scope_id == UUID(fixture["scope_id"]))).scalars().first()
        build = c.execute(select(t.builds).join(t.snapshots).where(
            t.snapshots.c.snapshot_id == UUID(fixture["snapshot_id"]))).mappings().one()
    body = "Synthetic researcher belongs to synthetic institute."
    span = Span(char_start=0, char_end=len(body), text=body)
    args = dict(scope_id=UUID(fixture["scope_id"]), source_id=source, url="https://fixture.invalid/affiliation",
                title="Affiliation", language="en", raw=body.encode(), body=body, spans=[span], parser_hash="fixture")
    with pytest.raises(ValueError, match="timezone-aware"):
        repository.stage_document(access, **args, source_date=datetime(2026, 1, 1))
    published = datetime(2026, 1, 1, tzinfo=timezone.utc)
    version = repository.stage_document(access, **args, source_date=published)
    chunk = repository.stage_chunk(access, version_id=version, span=span, chunker_hash=build["chunker_hash"],
        config_id=build["config_id"], vector=FixtureEmbedder().embed_query(body))
    with database.connect() as c:
        assert c.execute(select(t.versions.c.source_date).where(t.versions.c.document_version_id == version)).scalar_one() == published
        evidence = c.execute(select(t.spans.c.evidence_id).where(t.spans.c.document_version_id == version)).scalar_one()
    person = repository.record_entity(access, scope_id=UUID(fixture["scope_id"]), entity_type="person", display_label="Synthetic researcher")
    unit = repository.record_entity(access, scope_id=UUID(fixture["scope_id"]), entity_type="unit", display_label="Synthetic institute")
    claim = repository.record_claim(access, scope_id=UUID(fixture["scope_id"]), subject_id=person,
        predicate="affiliated_with", object_entity_id=unit, evidence_ids=[evidence], accepted=True)
    args = dict(profile_id=UUID(fixture["profile_id"]), taxonomy_version_id=UUID(fixture["taxonomy_version_id"]),
                config_id=build["config_id"], chunker_hash=build["chunker_hash"], claim_ids=[claim])
    snapshots = SnapshotRepository(database)
    with pytest.raises(ValueError, match="pinned subject/object"):
        snapshots.stage(access, **args, chunk_ids=[chunk], entity_ids=[person])
    with pytest.raises(ValueError, match="complete accepted support"):
        snapshots.stage(access, **args, chunk_ids=[UUID(fixture["chunk_ids"][0])], entity_ids=[person, unit])
    assert snapshots.stage(access, **args, chunk_ids=[chunk], entity_ids=[person, unit])
