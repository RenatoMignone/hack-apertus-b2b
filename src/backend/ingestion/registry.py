from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import insert, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from backend.contracts.data import configuration_hash
from backend.contracts.pipeline import canonical_url
from backend.data import schema as tables
from backend.data.database import require_scope, transaction


class RegistryImporter:
    def __init__(self, engine):
        self.engine = engine

    def source(self, access, scope_id, origin, families, registry_ref):
        origin = canonical_url(origin).rstrip("/")
        source_id = uuid5(scope_id, origin + "|" + registry_ref)
        with transaction(self.engine, access) as connection:
            require_scope(connection, scope_id, write=True)
            connection.execute(pg_insert(tables.sources).values(source_id=source_id, scope_id=scope_id,
                canonical_origin=origin, registry_ref=registry_ref).on_conflict_do_nothing())
            for name in sorted(set(families)):
                family_id = uuid5(NAMESPACE_URL, "navigator-family:" + name)
                connection.execute(pg_insert(tables.families).values(family_id=family_id, name=name).on_conflict_do_nothing())
                family_id = connection.execute(select(tables.families.c.family_id).where(tables.families.c.name == name)).scalar_one()
                connection.execute(pg_insert(tables.family_memberships).values(source_id=source_id, family_id=family_id).on_conflict_do_nothing())
        return source_id

    def profile(self, access, vocabulary, *, reviewer):
        if not reviewer.strip() or vocabulary.get("status") != "reviewed":
            raise ValueError("explicitly reviewed vocabulary and reviewer required")
        digest = configuration_hash(vocabulary)
        taxonomy_id = uuid5(NAMESPACE_URL, vocabulary["name"] + ":" + vocabulary["version"])
        profile_id = uuid5(taxonomy_id, access.namespace)
        concepts = {item["code"]: item for item in vocabulary["concepts"]}
        if len(concepts) != len(vocabulary["concepts"]) or "unknown" not in concepts:
            raise ValueError("unique concept codes and explicit unknown required")
        for item in concepts.values():
            if not item["definition"].strip() or not item["labels"].get("en"):
                raise ValueError("concept definition and English label required")
        for relation in vocabulary["relations"]:
            if (relation["subject"] not in concepts or relation["object"] not in concepts
                    or relation["kind"] not in {"broader", "narrower", "related"} or relation["subject"] == relation["object"]):
                raise ValueError("invalid taxonomy relation")
        with transaction(self.engine, access) as connection:
            connection.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:key,0))"), {"key": str(taxonomy_id)})
            existing = connection.execute(select(tables.taxonomies).where(tables.taxonomies.c.name == vocabulary["name"],
                tables.taxonomies.c.version == vocabulary["version"])).mappings().one_or_none()
            if existing and existing["artifact_hash"] != digest:
                raise ValueError("immutable taxonomy version already has different content")
            if existing:
                taxonomy_id = existing["taxonomy_version_id"]
            else:
                connection.execute(insert(tables.taxonomies).values(taxonomy_version_id=taxonomy_id, name=vocabulary["name"],
                    version=vocabulary["version"], artifact_hash=digest, status="reviewed"))
                for code, item in concepts.items():
                    concept_id = uuid5(taxonomy_id, code)
                    connection.execute(insert(tables.concepts).values(concept_id=concept_id, taxonomy_version_id=taxonomy_id,
                        code=code, definition=item["definition"], facet=item.get("facet", "topic"), notes={"reviewer": reviewer}))
                    for language, aliases in item["labels"].items():
                        for index, label in enumerate(aliases):
                            connection.execute(insert(tables.labels).values(label_id=uuid5(concept_id, language + ":" + label),
                                concept_id=concept_id, language=language, label=label, preferred=index == 0))
                for relation in vocabulary["relations"]:
                    connection.execute(insert(tables.relations).values(subject_id=uuid5(taxonomy_id, relation["subject"]),
                        object_id=uuid5(taxonomy_id, relation["object"]), kind=relation["kind"]))
            configuration = {"required_source_families": ["UniBE", "ARTORG", "DCB"], "taxonomy_hash": digest,
                "taxonomy_version_id": str(taxonomy_id), "reviewer": reviewer, "output_language": "en"}
            existing_profile = connection.execute(select(tables.profiles).where(tables.profiles.c.profile_id == profile_id)).mappings().one_or_none()
            if existing_profile and existing_profile["config_hash"] != configuration_hash(configuration):
                raise ValueError("immutable profile version already has different configuration")
            connection.execute(pg_insert(tables.profiles).values(profile_id=profile_id, name=vocabulary["name"], namespace=access.namespace,
                version=vocabulary["version"], schema_version="1.0", config_hash=configuration_hash(configuration),
                configuration=configuration).on_conflict_do_nothing())
        return {"profile_id": profile_id, "taxonomy_version_id": taxonomy_id, "taxonomy_hash": digest}
