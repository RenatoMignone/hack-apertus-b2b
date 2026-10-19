"""Bounded, non-destructive one/six-input SQL benchmark on an existing owned run."""
import argparse
import json
import os
from pathlib import Path
from time import perf_counter
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import make_url

from backend.application.factories import ConfiguredEmbedding
from backend.application.persistence.store import RuntimeStore
from backend.config.runtime import RuntimeSettings
from backend.contracts.data import validate_vector
from backend.data.cli import load_environment
from backend.data.database import engine_for, transaction
from backend.data.repositories.corpus import LANGUAGE_CONFIGS
from backend.data.retrieval import batched
from backend.data.retrieval.hybrid import ELIGIBLE
from backend.data.retrieval.prepared import prepare


class RecordingConnection:
    def __init__(self, connection):
        self.connection = connection

    def execute(self, statement, parameters=None):
        self.statement, self.parameters = statement, parameters or {}
        return self.connection.execute(statement, self.parameters)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", required=True)
    parser.add_argument("--run-id", required=True, type=UUID)
    parser.add_argument("--queries-file", required=True, type=Path, help="JSON list of 1-6 queries, or object with queries")
    parser.add_argument("--vectors-file", type=Path, help="Explicit compatible cached queries/vectors/config_hash; no provider call")
    parser.add_argument("--db-host")
    parser.add_argument("--db-port", type=int)
    parser.add_argument("--repeats", type=int, choices=range(1, 4), default=2)
    parser.add_argument("--plans", action="store_true", help="Separate diagnostic EXPLAIN reruns; affects subsequent cache conditions")
    parser.add_argument("--output", type=Path, default=Path(".local/retrieval-benchmark.json"))
    args = parser.parse_args()
    load_environment(args.env_file)
    settings = RuntimeSettings.from_env()
    if len(settings.bindings) != 1:
        parser.error("Use one authorized operator binding")
    binding = settings.bindings[0]
    url = make_url(os.environ[binding.database_url_env])
    if args.db_host:
        url = url.set(host=args.db_host)
    if args.db_port:
        url = url.set(port=args.db_port)
    engine = engine_for(url.render_as_string(hide_password=False), runtime=True)
    try:
        context = RuntimeStore(engine, settings, None).context(binding.access, args.run_id)
        raw = json.loads(args.queries_file.read_text(encoding="utf-8"))
        queries = raw["queries"] if isinstance(raw, dict) else raw
        if not 1 <= len(queries) <= 6 or any(not isinstance(q, str) or not q.strip() or len(q) > 10000 for q in queries):
            parser.error("Supply 1-6 nonempty bounded query strings")
        encoder = ConfiguredEmbedding(settings)
        if encoder.config_hash != context.embedding_config_hash:
            raise ValueError("Encoder and capture configuration differ")
        started = perf_counter()
        if args.vectors_file:
            cached = json.loads(args.vectors_file.read_text(encoding="utf-8"))
            if cached["queries"] != queries or cached["config_hash"] != encoder.config_hash:
                raise ValueError("Cached vectors do not match the exact queries and capture encoder")
            vectors = cached["vectors"]
        else:
            vectors = encoder.embed_queries(queries)
        if len(vectors) != len(queries):
            raise ValueError("One vector per query is required")
        vectors = [validate_vector(v, encoder.configuration.dimension) for v in vectors]
        result = {"embedding_seconds": round(perf_counter()-started, 4),
                  "vectors_cached": bool(args.vectors_file), "measurements": [],
                  "snapshot_id": str(context.snapshot_id), "embedding_config_hash": encoder.config_hash,
                  "persistent_data_writes": False, "plans_are_separate_reruns": args.plans}
        parameters = {"snapshot": context.snapshot_id, "namespace": binding.namespace, "run": context.run_id,
            "case": context.case_id, "all_languages": True, "languages": ["und"],
            "all_documents": True, "excluded": [UUID(int=0)], "all_families": True, "families": [UUID(int=0)]}
        with transaction(engine, binding.access) as c:
            result["identity"] = dict(c.execute(text("SELECT current_user,session_user,rolsuper,rolbypassrls "
                "FROM pg_roles WHERE rolname=current_user")).mappings().one())
            parameters["search_hash"] = c.execute(text("SELECT search_config_hash FROM retrieval.index_builds "
                "WHERE build_id=:build"), {"build": context.build_id}).scalar_one()
        for repeat in range(args.repeats):
            for count in sorted({1, len(queries)}):
                row = {"repeat": repeat, "query_count": count}
                with transaction(engine, binding.access) as c:
                    c.execute(text("SELECT set_config('statement_timeout',least(coalesce(nullif(setting::int,0),"
                        "30000),30000)::text,true) FROM pg_settings WHERE name='statement_timeout'"))
                    started = perf_counter()
                    prepare(c, ELIGIBLE, parameters, vectors=True)
                    row["eligibility_seconds"] = round(perf_counter()-started, 4)
                    row["eligible_chunks"] = c.execute(text("SELECT count(*) FROM pg_temp.navigator_retrieval_eligible")).scalar_one()
                    for name in ("lexical", "dense"):
                        wrapped = RecordingConnection(c)
                        started = perf_counter()
                        rows = (batched.lexical(wrapped, ELIGIBLE, parameters, queries[:count],
                                sorted({"simple", *LANGUAGE_CONFIGS.values()})) if name == "lexical"
                                else batched.dense(wrapped, ELIGIBLE, parameters, vectors[:count]))
                        row[name+"_seconds"] = round(perf_counter()-started, 4)
                        row[name+"_rows"] = [dict(value) for value in rows]
                        if args.plans:
                            row[name+"_plan"] = c.execute(text("EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) " +
                                wrapped.statement.text), wrapped.parameters).scalar_one()
                    row["combined_seconds"] = round(sum(row[k] for k in
                        ("eligibility_seconds", "lexical_seconds", "dense_seconds")), 4)
                result["measurements"].append(row)
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(result, default=str, indent=2), encoding="utf-8")
                args.output.chmod(0o600)
                print(json.dumps({k: v for k, v in row.items() if not k.endswith(("_rows", "_plan"))}), flush=True)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
