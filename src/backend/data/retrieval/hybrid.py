import math
from time import perf_counter
from uuid import UUID

from sqlalchemy import bindparam, select, text

from backend.contracts.data import EvidenceHit, QueryPlan, SearchResult, validate_vector
from backend.data import schema as tables
from backend.data.database import transaction


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
    WHERE s.snapshot_id=:snapshot AND s.status='published' AND s.namespace=:namespace
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
    def __init__(self, engine, embedder, reranker=None, tracer=None):
        self.engine = engine
        self.embedder = embedder
        self.reranker = reranker
        self.tracer = tracer

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
        parameters = {"snapshot": plan.snapshot_id, "namespace": access.namespace,
                      "all_languages": not plan.languages, "languages": plan.languages or ["und"],
                      "all_documents": not plan.excluded_document_ids, "excluded": plan.excluded_document_ids or [UUID(int=0)],
                      "all_families": not plan.source_family_ids, "families": plan.source_family_ids or [UUID(int=0)]}
        with transaction(self.engine, access) as connection:
            pin = connection.execute(select(tables.snapshots, tables.embedding_configs.c.config_hash,
                tables.embedding_configs.c.dimension).select_from(tables.snapshots.join(tables.builds).join(
                    tables.embedding_configs)).where(tables.snapshots.c.snapshot_id == plan.snapshot_id,
                    tables.snapshots.c.namespace == access.namespace,
                    tables.snapshots.c.status == "published")).mappings().one()
            if (pin["profile_id"] != plan.profile_id or pin["taxonomy_version_id"] != plan.taxonomy_version_id
                    or pin["build_id"] != plan.build_id or pin["config_hash"] != plan.embedding_config_hash
                    or self.embedder.config_hash != pin["config_hash"]):
                raise ValueError("query profile, taxonomy, snapshot, build or embedding space is incompatible")
        queries = list(dict.fromkeys([plan.original_request, *plan.variants]))
        vectors = [validate_vector(self.embedder.embed_query(query), pin["dimension"]) for query in queries]
        lexical, vector, rows_by_id = {}, {}, {}
        with transaction(self.engine, access) as connection:
            for query, query_vector in zip(queries, vectors, strict=True):
                lexical_rows = connection.execute(query_statement("""
                    SELECT c.chunk_id, max(ts_rank_cd(p.terms, websearch_to_tsquery(CAST(p.language_config AS regconfig),:query))) AS score
                """ + ELIGIBLE.replace("WHERE s.snapshot_id", "JOIN retrieval.search_documents p ON p.chunk_id=c.chunk_id AND p.search_config_hash=b.search_config_hash WHERE s.snapshot_id") + """
                    AND p.terms @@ websearch_to_tsquery(CAST(p.language_config AS regconfig),:query)
                    GROUP BY c.chunk_id ORDER BY score DESC,c.chunk_id LIMIT 30
                """), {**parameters, "query": query}).mappings().all()
                vector_rows = connection.execute(query_statement("SELECT c.chunk_id, e.vector <=> CAST(:vector AS vector) AS score " +
                    ELIGIBLE + " ORDER BY score,c.chunk_id LIMIT 30"),
                    {**parameters, "vector": "[" + ",".join(str(value) for value in query_vector) + "]"}).mappings().all()
                for branch, rows in ((lexical, lexical_rows), (vector, vector_rows)):
                    for rank, row in enumerate(rows, start=1):
                        if row["chunk_id"] not in branch or rank < branch[row["chunk_id"]]["rank"]:
                            branch[row["chunk_id"]] = {"rank": rank, "score": row["score"]}
            lexical = dict(sorted(lexical.items(), key=lambda item: (item[1]["rank"], str(item[0])))[:30])
            vector = dict(sorted(vector.items(), key=lambda item: (item[1]["rank"], str(item[0])))[:30])
            fused = fuse(lexical, vector, limit=60)
            for chunk_id, score in fused:
                row = connection.execute(select(tables.chunks, tables.versions.c.document_id, tables.documents.c.canonical_url)
                    .select_from(tables.chunks.join(tables.versions).join(tables.documents)).where(tables.chunks.c.chunk_id == chunk_id,
                    text("ops.can_access(retrieval.chunks.scope_id)"))).mappings().one()
                if any(previous["document_version_id"] == row["document_version_id"] and
                       max(0, min(previous["char_end"], row["char_end"]) - max(previous["char_start"], row["char_start"])) /
                       min(previous["char_end"] - previous["char_start"], row["char_end"] - row["char_start"]) >= .8
                       for previous in rows_by_id.values()):
                    continue
                evidence_ids = list(connection.execute(select(tables.chunk_evidence.c.evidence_id).where(
                    tables.chunk_evidence.c.chunk_id == chunk_id)).scalars())
                rows_by_id[chunk_id] = {**dict(row), "evidence_ids": evidence_ids, "fusion_score": score}
                if len(rows_by_id) == 30:
                    break
        passages = [f"Title: {row['title']}\nHeadings: {' / '.join(row['heading_path'])}\nPassage: {row['literal_text']}"
                    for row in rows_by_id.values()]
        reranked = self.reranker.score(plan.original_request, passages) if self.reranker and passages else None
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
                reranker_score=reranked[index] if reranked is not None else None))
        if reranked is not None:
            hits.sort(key=lambda hit: (-hit.reranker_score, str(hit.chunk_id)))
        with transaction(self.engine, access) as connection:
            for row in rows_by_id.values():
                from backend.data.database import require_scope
                require_scope(connection, row["scope_id"])
        return SearchResult(hits=hits, limitations=[] if reranked is not None else ["reranker_unavailable", "scores_are_not_confidence"])
