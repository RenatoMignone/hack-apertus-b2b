from uuid import uuid4

from sqlalchemy import insert, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from backend.contracts.data import AccessContext, ModelConfiguration, Span, configuration_hash
from backend.data import schema as tables
from backend.data.repositories.corpus import CorpusRepository
from backend.data.repositories.snapshots import SnapshotRepository


FIXTURE_MODEL = ModelConfiguration(role="embedding", logical_name="synthetic-fixture", artifact="builtin-fixture",
    revision="1", adapter_version="1", tokenizer="fixture-words-v1", input_limit=4096, dimension=3,
    normalization="none", query_template="{text}", document_template="{text}", precision="float32",
    license="repository-fixture", verified=True, test_only=True)


class FixtureEmbedder:
    config_hash = FIXTURE_MODEL.config_hash

    def embed_query(self, text):
        lowered = text.lower()
        glucose = any(word in lowered for word in ("glucose", "glukose", "glycémie", "glicemia"))
        return [1.0, 0.1, 0.1] if glucose else [0.1, 1.0, 0.1]


def load_fixture(engine, artifacts, *, namespace=None, named_sources=False):
    namespace = namespace or "fixture_" + uuid4().hex[:12]
    if not namespace.startswith(("test", "fixture")):
        raise ValueError("synthetic fixtures require a test/fixture namespace")
    principal_id, scope_id, profile_id, taxonomy_id = uuid4(), uuid4(), uuid4(), uuid4()
    with engine.begin() as connection:
        from sqlalchemy import text
        database_role = connection.execute(text("SELECT session_user")).scalar_one()
        connection.execute(insert(tables.principals).values(principal_id=principal_id, database_role=database_role, namespace=namespace))
        connection.execute(insert(tables.scopes).values(scope_id=scope_id, kind="public", access_policy_id="synthetic-fixture-only"))
        connection.execute(insert(tables.scope_grants).values(principal_id=principal_id, scope_id=scope_id, can_write=True))
        connection.execute(insert(tables.profiles).values(profile_id=profile_id, namespace=namespace, name="synthetic",
            version="1", schema_version="1.0", config_hash=configuration_hash({"fixture": 1}),
            configuration={"required_source_families": ["ARTORG"] if named_sources else ["UniBE", "ARTORG", "DCB"], "synthetic": True}))
        connection.execute(insert(tables.taxonomies).values(taxonomy_version_id=taxonomy_id, name=namespace,
            version="1", artifact_hash=configuration_hash({"taxonomy": "fixture"})))
    access = AccessContext(principal_id=principal_id, namespace=namespace)
    corpus = CorpusRepository(engine, artifacts)
    config_id = corpus.register_embedding(access, FIXTURE_MODEL)
    chunker_hash = configuration_hash({"chunker": "whole-fixture-v1"})
    chunks = []
    entries = [("UniBE", "en", "Synthetic example: glucose monitoring and biosensors."),
               ("ARTORG", "de", "Synthetisches Beispiel: Glukose Sensoren und digitale Medizin."),
               ("DCB", "fr", "Exemple synthétique : glycémie et technologies du diabète."),
               ("DCB", "it", "Esempio sintetico: glicemia e tecnologie del diabete.")]
    if named_sources:
        entries = [("ARTORG", "en", "In this fictional test corpus, B2B Sensor Laboratory develops glucose biosensors "
            "and evaluates prototype sensor signals. B2B Sensor Laboratory is a fictional research unit, "
            "not a real institution. Clinical approval, facility availability and willingness to collaborate "
            "are not established. This passage supplies no expertise in satellite propulsion.")]
    for family, language, body in entries:
        source_id = uuid4()
        with engine.begin() as connection:
            connection.execute(pg_insert(tables.families).values(family_id=uuid4(), name=family).on_conflict_do_nothing(index_elements=["name"]))
            family_id = connection.execute(select(tables.families.c.family_id).where(tables.families.c.name == family)).scalar_one()
            connection.execute(insert(tables.sources).values(source_id=source_id, scope_id=scope_id,
                canonical_origin="https://fixture.invalid", registry_ref="synthetic-not-source-evidence"))
            connection.execute(insert(tables.family_memberships).values(source_id=source_id, family_id=family_id))
        span = Span(char_start=0, char_end=len(body), text=body)
        version_id = corpus.stage_document(access, scope_id=scope_id, source_id=source_id,
            url=f"https://fixture.invalid/{namespace}/{language}", title=f"Synthetic {family} fixture", language=language,
            raw=f"<p>{body}</p>".encode(), body=body, spans=[span], parser_hash=configuration_hash({"parser": "fixture"}))
        chunks.append(corpus.stage_chunk(access, version_id=version_id, span=span, chunker_hash=chunker_hash,
            config_id=config_id, vector=FixtureEmbedder().embed_query(body)))
    snapshots = SnapshotRepository(engine)
    snapshot_id = snapshots.stage(access, profile_id=profile_id, taxonomy_version_id=taxonomy_id, config_id=config_id,
        chunk_ids=chunks, chunker_hash=chunker_hash)
    snapshots.publish(access, snapshot_id)
    return {"principal_id": str(principal_id), "namespace": namespace, "scope_id": str(scope_id),
            "profile_id": str(profile_id), "taxonomy_version_id": str(taxonomy_id), "snapshot_id": str(snapshot_id),
            "embedding_config_hash": FIXTURE_MODEL.config_hash, "chunk_ids": [str(value) for value in chunks]}
