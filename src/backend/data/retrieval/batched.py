"""Rank variants over one caller-authorized, transaction-local eligibility relation."""
from sqlalchemy import bindparam, text


def statement(sql):
    result = text(sql)
    for name in ("languages", "excluded", "families"):
        if ":" + name in sql:
            result = result.bindparams(bindparam(name, expanding=True))
    return result


def lexical(connection, eligible, parameters, queries, configs):
    # The permanent tsvector @@ operator is not leakproof, so PostgreSQL cannot
    # push it through source-table RLS. Index only already-authorized projections;
    # never weaken the global policy or mark a text operator leakproof.
    values, params = [], dict(parameters)
    for index, query in enumerate(queries):
        params[f"query{index}"] = query
        for config in configs:
            values.append(f"({index},'{config}',websearch_to_tsquery('{config}',:query{index}))")
    # Match before staging: do not copy/index every authorized tsvector merely
    # to retain a handful of matches. This is an OR union across queries and
    # affects only lexical work; dense eligibility remains independent.
    matches = []
    for config in configs:
        alternatives = " || ".join(
            f"websearch_to_tsquery('{config}',:query{index})" for index in range(len(queries)))
        matches.append(f"(p.language_config='{config}' AND p.terms @@ ({alternatives}))")
    connection.execute(text("""CREATE TEMP TABLE navigator_retrieval_projections ON COMMIT DROP AS
        SELECT p.chunk_id,p.terms,p.language_config FROM retrieval.search_documents p
        JOIN pg_temp.navigator_retrieval_eligible e USING(chunk_id)
        WHERE p.search_config_hash=:search_hash AND (""" + " OR ".join(matches) + ")"), params)
    connection.execute(text("CREATE INDEX ON pg_temp.navigator_retrieval_projections USING gin(terms)"))
    connection.execute(text("ANALYZE pg_temp.navigator_retrieval_projections"))
    sql = ("WITH queries(idx,config,query) AS MATERIALIZED (VALUES " + ",".join(values) + "), "
        "scores AS (SELECT q.idx,p.chunk_id,p.score FROM queries q CROSS JOIN LATERAL "
        "(SELECT p.chunk_id,max(ts_rank_cd(p.terms,q.query)) AS score "
        "FROM pg_temp.navigator_retrieval_projections p "
        "WHERE p.language_config=q.config AND p.terms @@ q.query GROUP BY p.chunk_id) p), "
        "scored AS (SELECT idx,chunk_id,max(score) AS score FROM scores GROUP BY idx,chunk_id), "
        "ranked AS (SELECT *,row_number() OVER (PARTITION BY idx ORDER BY score DESC,chunk_id) AS rank "
        "FROM scored) SELECT idx,chunk_id,score FROM ranked WHERE rank<=30 ORDER BY idx,rank")
    return connection.execute(text(sql), params).mappings().all()


def dense(connection, eligible, parameters, vectors):
    params, values = dict(parameters), []
    for index, vector in enumerate(vectors):
        params[f"vector{index}"] = "[" + ",".join(str(value) for value in vector) + "]"
        values.append(f"({index},CAST(:vector{index} AS vector))")
    sql = ("WITH eligible AS MATERIALIZED (SELECT m.chunk_id,e.vector "
        "FROM pg_temp.navigator_retrieval_eligible m JOIN retrieval.embeddings e "
        "ON e.embedding_id=m.embedding_id), queries(idx,vector) AS (VALUES " + ",".join(values) + ") "
        "SELECT q.idx,ranked.chunk_id,ranked.score FROM queries q CROSS JOIN LATERAL "
        "(SELECT e.chunk_id,e.vector <=> q.vector AS score FROM eligible e "
        "ORDER BY score,e.chunk_id LIMIT 30) ranked ORDER BY q.idx,ranked.score,ranked.chunk_id")
    return connection.execute(text(sql), params).mappings().all()
