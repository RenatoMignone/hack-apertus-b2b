"""Retrieval PoC with no persistent writes on an existing owned capture."""
import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from uuid import UUID

from sqlalchemy import event, func, select, text
from sqlalchemy.engine import make_url

from backend.application.factories import ConfiguredEmbedding
from backend.application.persistence.store import RuntimeStore
from backend.config.runtime import RuntimeSettings
from backend.contracts.data import QueryPlan
from backend.data import schema as t
from backend.data.database import engine_for, transaction
from backend.data.repositories.catalog import CatalogRepository
from backend.data.retrieval.hybrid import HybridSearch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", required=True, type=Path)
    parser.add_argument("--run-id", required=True, type=UUID)
    parser.add_argument("--db-host")
    parser.add_argument("--db-port", type=int)
    parser.add_argument("--output", type=Path, default=Path(".local/proof-concept/raw-results.json"))
    parser.add_argument("--demo-dir", type=Path, default=Path("demo"))
    args = parser.parse_args()
    # Private env is explicit and never printed; preserve the established loader convention.
    from backend.data.cli import load_environment
    load_environment(args.env_file)
    settings = RuntimeSettings.from_env()
    if len(settings.bindings) != 1:
        parser.error("Use a single-operator private environment")
    binding = settings.bindings[0]
    url = make_url(os.environ[binding.database_url_env])
    if args.db_host:
        url = url.set(host=args.db_host)
    if args.db_port:
        url = url.set(port=args.db_port)
    engine = engine_for(url.render_as_string(hide_password=False))

    @event.listens_for(engine, "connect")
    def readonly(connection, _record):
        previous = connection.autocommit
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute("SET statement_timeout='30s'")
            cursor.execute("SET lock_timeout='5s'")
        connection.autocommit = previous

    output = {"started_at": datetime.now(timezone.utc).isoformat(),
              "mode": "real_corpus_real_hosted_embeddings_no_frontend",
              "strategy": "rrf", "reranker_enabled": False,
              "reasoning_model_called": False, "database_read_only": False, "persistent_data_read_only": True,
              "temporary_retrieval_relations": True,
              "cases_created": 0, "queries": []}
    args.output.parent.mkdir(parents=True, exist_ok=True)

    @event.listens_for(engine, "before_cursor_execute")
    def prevent_persistent_writes(_connection, _cursor, statement, _parameters, _context, _many):
        normalized = " ".join(statement.upper().split())
        allowed = normalized.startswith(("SELECT ", "SET ", "SHOW ", "SAVEPOINT ", "RELEASE SAVEPOINT ",
            "ROLLBACK TO SAVEPOINT ", "CREATE TEMP TABLE NAVIGATOR_RETRIEVAL_"))
        allowed = allowed or (normalized.startswith(("CREATE INDEX ON PG_TEMP.NAVIGATOR_RETRIEVAL_",
            "CREATE UNIQUE INDEX ON PG_TEMP.NAVIGATOR_RETRIEVAL_", "ANALYZE PG_TEMP.NAVIGATOR_RETRIEVAL_")))
        if not allowed and not normalized.startswith("WITH "):
            raise RuntimeError("PoC harness refuses persistent write statements")

    def save():
        args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        context = RuntimeStore(engine, settings, None).context(binding.access, args.run_id)
        with transaction(engine, binding.access) as connection:
            output["schema_revision"] = connection.execute(text("select version_num from public.alembic_version")).scalar_one()
            output["capture"] = {
                "snapshot_id": str(context.snapshot_id),
                "build_id": str(context.build_id),
                "profile_id": str(context.profile_id),
                "taxonomy_version_id": str(context.taxonomy_version_id),
                "embedding_config_hash": context.embedding_config_hash,
                "chunks": connection.execute(select(func.count()).select_from(t.snapshot_chunks)
                    .where(t.snapshot_chunks.c.snapshot_id == context.snapshot_id)).scalar_one()}
        output["private_reproduction_run_id"] = str(args.run_id)
        output["source_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        variants = json.loads((args.demo_dir / "query-variants.json").read_text(encoding="utf-8"))
        output["demo_fixture"] = variants["fixture"]
        output["input_sha256"] = hashlib.sha256((args.demo_dir / "case-brief.md").read_bytes()).hexdigest()
        embedder = ConfiguredEmbedding(settings)
        output["encoder"] = embedder.configuration.model_dump()
        search = HybridSearch(engine, embedder, strategy="rrf")
        cases = [{"id": "full-demo-brief", "prompt": (args.demo_dir / "case-brief.md").read_text(encoding="utf-8")},
                 *variants["variants"]]
        for case in cases:
            started = perf_counter()
            row = {"id": case["id"], "query": case["prompt"], "status": "running"}
            output["queries"].append(row); save()
            print("START " + case["id"], flush=True)
            plan = QueryPlan(original_request=case["prompt"], variants=[], run_id=context.run_id,
                case_id=context.case_id, input_revision_id=context.input_id,
                snapshot_id=context.snapshot_id, profile_id=context.profile_id,
                taxonomy_version_id=context.taxonomy_version_id, build_id=context.build_id,
                embedding_config_hash=context.embedding_config_hash)
            try:
                result = search.search(binding.access, plan)
                row.update(status="succeeded", seconds=round(perf_counter()-started, 3),
                           limitations=result.limitations, hits=[])
                # Body reads only verify already-ranked hits; no ranking/name prefilter.
                with transaction(engine, binding.access) as connection:
                    versions = {r["document_version_id"]: r for r in connection.execute(
                        select(t.versions.c.document_version_id, t.versions.c.body_text,
                            t.versions.c.body_hash, t.versions.c.created_at)
                        .where(t.versions.c.document_version_id.in_(
                            {h.document_version_id for h in result.hits}))).mappings()}
                    for rank, hit in enumerate(result.hits, 1):
                        version = versions[hit.document_version_id]
                        body = version["body_text"]
                        item = hit.model_dump(mode="json")
                        item.update(rank=rank,
                            exact_body_slice=body[hit.char_start:hit.char_end] == hit.text,
                            body_sha256_valid=hashlib.sha256(body.encode("utf-8")).hexdigest() == version["body_hash"],
                            body_sha256=version["body_hash"],
                            version_created_at=version["created_at"].isoformat())
                        row["hits"].append(item)
                entities = CatalogRepository(engine).entities_for_hits(binding.access, context.snapshot_id, result.hits)
                row["accepted_entity_projection"] = [
                    {"entity_id": str(entity["entity_id"]), "label": entity.get("preferred_label", entity.get("label", "")),
                     "entity_type": entity.get("entity_type")} for entity in entities]
                print("DONE " + case["id"] + " hits=" + str(len(result.hits)) +
                      " seconds=" + str(row["seconds"]), flush=True)
            except Exception as error:
                # Never include provider/SQL bodies, DSNs or private prompts in error logs.
                row.update(status="failed", seconds=round(perf_counter()-started, 3), error_type=type(error).__name__)
                print("FAILED " + case["id"] + " " + type(error).__name__, flush=True)
            save()
        output["completed_at"] = datetime.now(timezone.utc).isoformat(); save()
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
