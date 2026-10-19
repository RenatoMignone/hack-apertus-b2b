import math
from time import perf_counter
from uuid import UUID

from sqlalchemy import bindparam, select, text

from backend.data.snapshot_projection import snapshot_metadata
from backend.contracts.data import EvidenceHit, QueryPlan, SearchResult, validate_vector
from backend.contracts.services import ServiceUnavailable
from backend.data import schema as tables
from backend.data.database import transaction
from backend.observability.logging import timed, event


def fuse(lexical: dict, vector: dict, limit=30):
    candidates = []
    for chunk_id in set(lexical) | set(vector):
        lexical_rank = lexical.get(chunk_id, {}).get("rank")
        vector_rank = vector.get(chunk_id, {}).get("rank")
        score = (1 / (60 + lexical_rank) if lexical_rank else 0) + (1 / (60 + vector_rank) if vector_rank else 0)
        candidates.append((chunk_id, score))
    return sorted(candidates, key=lambda item: (-item[1], str(item[0])))[:limit]


ELIGIBLE = """
    FROM retrieval.snapshot_chunks sc
    JOIN corpus.snapshots s ON s.snapshot_id=sc.snapshot_id
    JOIN retrieval.index_builds b ON b.build_id=s.build_id
    JOIN retrieval.chunks c ON c.chunk_id=sc.chunk_id
    JOIN corpus.document_versions v ON v.document_version_id=c.document_version_id
    JOIN corpus.documents d ON d.document_id=v.document_id
    JOIN retrieval.embeddings e ON e.embedding_id=sc.embedding_id AND e.chunk_id=c.chunk_id AND e.config_id=b.config_id
    WHERE s.snapshot_id=:snapshot AND s.namespace=:namespace
      AND (s.status='published' OR (s.status='live' AND EXISTS (
        SELECT 1 FROM cases.runs r WHERE r.run_id=:run AND r.snapshot_id=s.snapshot_id
          AND r.case_id=:case)))
      AND ops.can_access(c.scope_id) AND v.status='accepted'
      AND (:all_languages OR c.language IN :languages)
      AND (:all_documents OR d.document_id NOT IN :excluded)
      AND (:all_families OR EXISTS (
        SELECT 1 FROM corpus.source_family_memberships f WHERE f.source_id=d.source_id AND f.family_id IN :families))
"""


def query_statement(statement):
    return text(statement).bindparams(bindparam("languages", expanding=True), bindparam("excluded", expanding=True),
                                     bindparam("families", expanding=True))


class HybridSearch:
    def __init__(self, engine, embedder, reranker=None, tracer=None, *, strategy=None):
        self.engine = engine
        self.embedder = embedder
        self.reranker = reranker
        self.tracer = tracer
        self.default_strategy = strategy is None
        self.strategy = strategy or ('reranked' if reranker else 'rrf')
        if self.strategy not in {'lexical', 'dense', 'rrf', 'reranked'}:
            raise ValueError('unknown retrieval strategy')

    def search(self, access, plan: QueryPlan) -> SearchResult:
        started = perf_counter()
        try:
            result = self._search(access, plan)
        except Exception:
            if self.tracer:
                self.tracer.emit({"stage": "retrieval", "error_code": "invalid", "snapshot_id": str(plan.snapshot_id),
                                  "duration_ms": (perf_counter() - started) * 1000})
            raise
        if self.tracer:
            self.tracer.emit({"stage": "retrieval", "snapshot_id": str(plan.snapshot_id), "build_id": str(plan.build_id),
                "run_id": str(plan.run_id) if plan.run_id else None, "config_hash": plan.embedding_config_hash,
                "candidate_count": len(result.hits), "duration_ms": (perf_counter() - started) * 1000})
        return result

    def _search(self, access, plan: QueryPlan) -> SearchResult:
        parameters = {"snapshot": plan.snapshot_id, "namespace": access.namespace, "run": plan.run_id,
                      "all_languages": not plan.languages, "languages": plan.languages or ["und"],
                      "all_documents": not plan.excluded_document_ids, "excluded": plan.excluded_document_ids or [UUID(int=0)],
                      "all_families": not plan.source_family_ids, "families": plan.source_family_ids or [UUID(int=0)]}
        with transaction(self.engine, access) as connection:
            connection.execute(text("SELECT set_config('statement_timeout', "
                "least(coalesce(nullif(setting::int,0),30000),30000)::text,true) "
                "FROM pg_settings WHERE name='statement_timeout'"))
            pin = connection.execute(select(*snapshot_metadata(), tables.embedding_configs.c.config_hash,
                tables.embedding_configs.c.dimension).select_from(tables.snapshots.join(tables.builds).join(
                    tables.embedding_configs)).where(tables.snapshots.c.snapshot_id == plan.snapshot_id,
                    tables.snapshots.c.namespace == access.namespace,
                    tables.snapshots.c.status.in_(["published", "live"]))).mappings().one()
            parameters["case"] = plan.case_id or UUID(int=0)
            if pin["status"] == "live":
                run = connection.execute(select(tables.runs.c.case_id).where(
                    tables.runs.c.run_id == plan.run_id, tables.runs.c.snapshot_id == plan.snapshot_id)).scalar_one_or_none()
                parameters["case"] = run
                if run is None or str(run) != pin["runtime_case_id"]:
                    raise PermissionError("live retrieval requires its owning case run")
            if (pin["profile_id"] != plan.profile_id or pin["taxonomy_version_id"] != plan.taxonomy_version_id
                    or pin["build_id"] != plan.build_id or pin["config_hash"] != plan.embedding_config_hash
                    or self.embedder.config_hash != pin["config_hash"]):
                raise ValueError("query profile, taxonomy, snapshot, build or embedding space is incompatible")
        queries = list(dict.fromkeys([plan.original_request, *plan.variants]))
        if self.strategy == 'lexical':
            vectors = [None] * len(queries)
        else:
            batch = getattr(self.embedder, 'embed_queries', None)
            with timed("embedding", run_id=plan.run_id, query_count=len(queries)):
                encoded = batch(queries) if callable(batch) else [self.embedder.embed_query(query) for query in queries]
            if len(encoded) != len(queries):
                raise ValueError('embedding batch must cover every query exactly')
            vectors = [validate_vector(value, pin['dimension']) for value in encoded]
        lexical, vector, rows_by_id, query_matches = {}, {}, {}, {}
        with transaction(self.engine, access) as connection:
            connection.execute(text("SELECT set_config('statement_timeout', "
                "least(coalesce(nullif(setting::int,0),30000),30000)::text,true) "
                "FROM pg_settings WHERE name='statement_timeout'"))
            # Constant regconfig avoids per-row query parsing and provides a fixed
            # GIN scan key where caller RLS and the planner permit it. Do not
            # assume a production index scan without checking EXPLAIN.
            from backend.data.repositories.corpus import LANGUAGE_CONFIGS
            configs = sorted({'simple', *LANGUAGE_CONFIGS.values()})
            from backend.data.retrieval import batched
            parameters['search_hash'] = connection.execute(select(tables.builds.c.search_config_hash).where(
                tables.builds.c.build_id == plan.build_id)).scalar_one()
            with timed('retrieval.lexical', run_id=plan.run_id, query_count=len(queries)):
                lexical_rows = [] if self.strategy == 'dense' else batched.lexical(
                    connection, ELIGIBLE, parameters, queries, configs)
            with timed('retrieval.vector', run_id=plan.run_id, query_count=len(queries)):
                vector_rows = [] if self.strategy == 'lexical' else batched.dense(
                    connection, ELIGIBLE, parameters, vectors)
            for index, query in enumerate(queries):
                for branch, all_rows in ((lexical, lexical_rows), (vector, vector_rows)):
                    rows = [row for row in all_rows if row['idx'] == index]
                    for rank, row in enumerate(rows, start=1):
                        query_matches.setdefault(row["chunk_id"], set()).add(query)
                        if row["chunk_id"] not in branch or rank < branch[row["chunk_id"]]["rank"]:
                            branch[row["chunk_id"]] = {"rank": rank, "score": row["score"]}
            event('retrieval.candidates', run_id=plan.run_id, query_count=len(queries),
                  candidate_count=len(set(lexical) | set(vector)))
            lexical = dict(sorted(lexical.items(), key=lambda item: (item[1]["rank"], str(item[0])))[:30])
            vector = dict(sorted(vector.items(), key=lambda item: (item[1]["rank"], str(item[0])))[:30])
            fused = fuse(lexical, vector, limit=60)
            candidate_ids = [chunk_id for chunk_id, _ in fused]
            candidate_rows = {row['chunk_id']: row for row in connection.execute(
                select(tables.chunks, tables.versions.c.document_id, tables.documents.c.canonical_url)
                .select_from(tables.chunks.join(tables.versions).join(tables.documents))
                .where(tables.chunks.c.chunk_id.in_(candidate_ids),
                    text("ops.can_access(retrieval.chunks.scope_id)"))).mappings()}
            evidence_by_chunk = {}
            for row in connection.execute(select(tables.chunk_evidence)
                    .where(tables.chunk_evidence.c.chunk_id.in_(candidate_ids))
                    .order_by(tables.chunk_evidence.c.chunk_id, tables.chunk_evidence.c.evidence_id)).mappings():
                evidence_by_chunk.setdefault(row['chunk_id'], []).append(row['evidence_id'])
            for chunk_id, score in fused:
                if chunk_id not in candidate_rows:
                    from sqlalchemy.exc import NoResultFound
                    raise NoResultFound('ranked passage is no longer accessible')
                row = candidate_rows[chunk_id]
                if any(previous["document_version_id"] == row["document_version_id"] and
                       max(0, min(previous["char_end"], row["char_end"]) - max(previous["char_start"], row["char_start"])) /
                       min(previous["char_end"] - previous["char_start"], row["char_end"] - row["char_start"]) >= .8
                       for previous in rows_by_id.values()):
                    continue
                evidence_ids = evidence_by_chunk.get(chunk_id, [])
                rows_by_id[chunk_id] = {**dict(row), "evidence_ids": evidence_ids, "fusion_score": score}
                if len(rows_by_id) == 30:
                    break
        passages = [f"Title: {row['title']}\nHeadings: {' / '.join(row['heading_path'])}\nPassage: {row['literal_text']}"
                    for row in rows_by_id.values()]
        details = None
        reranker = self.reranker if self.strategy == 'reranked' else None
        try:
            if reranker and passages and hasattr(reranker, "score_with_details"):
                with timed("reranking", run_id=plan.run_id, candidate_count=len(passages)):
                    details = reranker.score_with_details(plan.original_request, passages)
                reranked = [row["score"] for row in details]
            else:
                reranked = reranker.score(plan.original_request, passages) if reranker and passages else None
        except ServiceUnavailable:
            reranked = None
        if reranked is not None and (len(reranked) != len(passages) or not all(math.isfinite(score) for score in reranked)):
            raise ValueError("reranker returned invalid scores")
        hits = []
        for index, (chunk_id, row) in enumerate(rows_by_id.items()):
            hits.append(EvidenceHit(chunk_id=chunk_id, document_id=row["document_id"], document_version_id=row["document_version_id"],
                text=row["literal_text"], title=row["title"], heading_path=row["heading_path"], char_start=row["char_start"],
                char_end=row["char_end"], language=row["language"], source_url=row["canonical_url"], evidence_ids=row["evidence_ids"],
                snapshot_id=plan.snapshot_id, build_id=plan.build_id, lexical_rank=lexical.get(chunk_id, {}).get("rank"),
                vector_rank=vector.get(chunk_id, {}).get("rank"), lexical_score=lexical.get(chunk_id, {}).get("score"),
                cosine_distance=vector.get(chunk_id, {}).get("score"), fusion_score=row["fusion_score"],
                reranker_score=reranked[index] if reranked is not None else None,
                reranker_windows=details[index]["windows"] if details is not None else [],
                query_matches=[q for q in queries if q in query_matches[chunk_id]],
                ranking_version="rrf60-rerank-max-window-v1" if details is not None else "rrf60-v1"))
        if reranked is not None:
            hits.sort(key=lambda hit: (-hit.reranker_score, str(hit.chunk_id)))
        with transaction(self.engine, access) as connection:
            from backend.data.database import require_scope
            for scope_id in {row["scope_id"] for row in rows_by_id.values()}:
                require_scope(connection, scope_id)
        return SearchResult(hits=hits, limitations=["scores_are_not_confidence"]
            + (["live_corpus_incomplete_coverage"] if pin["status"] == "live" else [])
            + (["reranker_unavailable"] if (self.default_strategy or self.strategy == 'reranked') and reranked is None else []))
