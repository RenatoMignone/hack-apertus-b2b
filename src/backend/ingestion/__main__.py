import argparse
from datetime import datetime
import json
from pathlib import Path
from uuid import UUID

from backend.config.settings import Settings
from backend.contracts.data import AccessContext, ModelConfiguration, Span, content_hash
from backend.data.cli import load_environment
from backend.data.database import check_schema, engine_for
from backend.ingestion.mesh import mesh_vocabulary
from backend.ingestion.classification import SpecificSubject
from backend.ingestion.normalize import normalize
from backend.ingestion.pipeline import CorpusBuilder
from backend.ingestion.registry import RegistryImporter
from backend.ingestion.web import FetchObservation, SafeHTTP


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, value):
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8") as output:
        json.dump(value, output, ensure_ascii=False, indent=2, default=str)


def main():
    parser = argparse.ArgumentParser(prog="python -m backend.ingestion")
    parser.add_argument("--env-file")
    commands = parser.add_subparsers(dest="command", required=True)
    mesh = commands.add_parser("mesh-import")
    mesh.add_argument("--trees", required=True, type=Path)
    mesh.add_argument("--manifest", required=True, type=Path)
    mesh.add_argument("--access", required=True, type=Path)
    mesh.add_argument("--reviewer", required=True)
    mesh.add_argument("--output", required=True, type=Path)
    collect = commands.add_parser("collect")
    collect.add_argument("url")
    collect.add_argument("--user-agent", required=True)
    collect.add_argument("--output", required=True, type=Path)
    benchmark = commands.add_parser("benchmark")
    benchmark.add_argument("--configuration", required=True, type=Path)
    benchmark.add_argument("--model-path", required=True, type=Path)
    benchmark.add_argument("--inputs", required=True, type=Path)
    benchmark.add_argument("--output", required=True, type=Path)
    build = commands.add_parser("build")
    build.add_argument("--access", required=True, type=Path)
    build.add_argument("--scope", required=True, type=UUID)
    build.add_argument("--sources", required=True, type=Path)
    build.add_argument("--mesh-pins", required=True, type=Path)
    build.add_argument("--configuration", required=True, type=Path)
    build.add_argument("--model-path", required=True, type=Path)
    build.add_argument("--confirm-public-sources", action="store_true", required=True)
    build.add_argument("--publish", action="store_true")
    build.add_argument("--expected-active", type=UUID)
    build.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    if arguments.output.exists():
        raise ValueError("output already exists; choose a new immutable delivery path")
    if arguments.command == "collect":
        observation = SafeHTTP(user_agent=arguments.user_agent).fetch(arguments.url)
        document = normalize(observation.raw, observation.mime)
        raw_path = arguments.output.with_suffix(".raw")
        if raw_path.exists():
            raise ValueError("raw source artifact already exists")
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        with raw_path.open("xb") as output:
            output.write(observation.raw)
        write_json(arguments.output, {"url": observation.requested_url, "final_url": observation.final_url,
            "raw_path": raw_path.name, "raw_sha256": content_hash(observation.raw), "body_sha256": content_hash(document.body.encode()),
            "mime": observation.mime, "status": observation.status, "fetched_at": observation.fetched_at,
            "redirects": list(observation.redirects), "published_at": document.published_at})
        return
    load_environment(arguments.env_file)
    if arguments.command == "benchmark":
        from backend.models.embeddings.local import load_embeddinggemma
        configuration = ModelConfiguration.model_validate(read_json(arguments.configuration))
        embedder = load_embeddinggemma(configuration, arguments.model_path)
        inputs = read_json(arguments.inputs)
        embedder.encode_inputs(inputs[:1])
        write_json(arguments.output, embedder.benchmark(inputs))
        return
    settings = Settings.from_env()
    engine = engine_for(settings.database_url)
    check_schema(engine)
    identity = read_json(arguments.access)
    access = AccessContext(principal_id=identity["principal_id"], namespace=identity["namespace"])
    registry = RegistryImporter(engine)
    if arguments.command == "mesh-import":
        vocabulary = mesh_vocabulary(arguments.trees.read_bytes(), read_json(arguments.manifest))
        write_json(arguments.output, registry.profile(access, vocabulary, reviewer=arguments.reviewer))
        return
    from backend.models.embeddings.local import load_embeddinggemma
    configuration = ModelConfiguration.model_validate(read_json(arguments.configuration))
    embedder = load_embeddinggemma(configuration, arguments.model_path)
    builder = CorpusBuilder(engine, settings.artifact_store(), embedder, configuration)
    pins = read_json(arguments.mesh_pins)
    records = []
    for source in read_json(arguments.sources):
        observation_path = (arguments.sources.parent / source["observation"]).resolve()
        metadata = read_json(observation_path)
        raw = (observation_path.parent / metadata["raw_path"]).read_bytes()
        if content_hash(raw) != metadata["raw_sha256"]:
            raise ValueError("raw source hash differs from collected observation")
        observation = FetchObservation(metadata["url"], metadata["final_url"], raw, metadata["mime"], metadata["status"],
            datetime.fromisoformat(metadata["fetched_at"]), tuple(metadata.get("redirects", [])))
        source_id = registry.source(access, arguments.scope, source["origin"], source["families"], source["registry_ref"])
        claims = [{**claim, "span": Span.model_validate(claim["span"])} for claim in source.get("reviewed_claims", [])]
        tags = [{"code": tag["code"], "span": Span.model_validate(tag["span"])} for tag in source.get("mesh_tags", [])]
        records.append(builder.ingest(access, scope_id=arguments.scope, source_id=source_id, observation=observation,
            reviewed_claims=claims, taxonomy_version_id=UUID(pins["taxonomy_version_id"]), tag_proposals=tags,
            tag_reviewer=source.get("tag_reviewer"), specific_subjects=[SpecificSubject.model_validate(subject)
                for subject in source.get("specific_subjects", [])]))
    snapshot = builder.publish(access, records, profile_id=UUID(pins["profile_id"]), taxonomy_version_id=UUID(pins["taxonomy_version_id"]),
        expected_active=arguments.expected_active) if arguments.publish else None
    write_json(arguments.output, {"records": records, "snapshot": snapshot, "embedding_config_hash": configuration.config_hash})


if __name__ == "__main__":
    main()
