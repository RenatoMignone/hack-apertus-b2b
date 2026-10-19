"""Rank query variants while evaluating authorized membership once per branch."""
from sqlalchemy import bindparam, text


def statement(sql):
    return text(sql).bindparams(bindparam("languages", expanding=True),
        bindparam("excluded", expanding=True), bindparam("families", expanding=True))


def lexical(connection, eligible, parameters, queries, configs):
    values = []
    params = dict(parameters)
    for index, query in enumerate(queries):
        params[f"query{index}"] = query
        for config in configs:
            # Configurations come from our fixed LANGUAGE_CONFIGS, not user data.
            values.append(f"({index},'{config}',websearch_to_tsquery('{config}',:query{index}))")
    sql = ("WITH eligible AS MATERIALIZED (SELECT c.chunk_id " + eligible + "), "
        "projections AS MATERIALIZED (SELECT p.chunk_id,p.terms,p.language_config "
        "FROM retrieval.search_documents p JOIN eligible e ON e.chunk_id=p.chunk_id "
        "WHERE p.search_config_hash=:search_hash), "
        "queries(idx,config,query) AS MATERIALIZED (VALUES " + ",".join(values) + "), "
        "scored AS (SELECT q.idx,p.chunk_id,max(ts_rank_cd(p.terms,q.query)) AS score "
        "FROM projections p JOIN queries q ON p.language_config=q.config "
        "WHERE p.terms @@ q.query GROUP BY q.idx,p.chunk_id), "
        "ranked AS (SELECT *,row_number() OVER (PARTITION BY idx ORDER BY score DESC,chunk_id) AS rank "
        "FROM scored) SELECT idx,chunk_id,score FROM ranked WHERE rank<=30 ORDER BY idx,rank")
    return connection.execute(statement(sql), params).mappings().all()


def dense(connection, eligible, parameters, vectors):
    params = dict(parameters)
    values = []
    for index, vector in enumerate(vectors):
        params[f"vector{index}"] = "[" + ",".join(str(value) for value in vector) + "]"
        values.append(f"({index},CAST(:vector{index} AS vector))")
    sql = ("WITH eligible AS MATERIALIZED (SELECT c.chunk_id,e.vector " + eligible + "), "
        "queries(idx,vector) AS (VALUES " + ",".join(values) + ") "
        "SELECT q.idx,ranked.chunk_id,ranked.score FROM queries q CROSS JOIN LATERAL "
        "(SELECT e.chunk_id,e.vector <=> q.vector AS score FROM eligible e "
        "ORDER BY score,e.chunk_id LIMIT 30) ranked ORDER BY q.idx,ranked.score,ranked.chunk_id")
    return connection.execute(statement(sql), params).mappings().all()
