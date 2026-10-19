"""Authorization equivalence, exact ranking and cleanup on disposable PostgreSQL."""
from uuid import UUID

import pytest
from sqlalchemy import text, update, select
from sqlalchemy.exc import DBAPIError, NoResultFound

from backend.contracts.data import QueryPlan
from backend.data import schema as t
from backend.data.database import transaction
from backend.data.fixtures import FixtureEmbedder
from backend.data.retrieval.hybrid import HybridSearch, ELIGIBLE, query_statement
from backend.data.retrieval.prepared import prepare
from backend.data.retrieval import batched
from backend.tests.runtime.test_live_corpus import live_users, start
from backend.tests.runtime.conftest import harness

pytestmark = pytest.mark.integration


def test_scope_sets_equal_legacy_and_follow_revocation(harness, live_users):
    store, access = live_users[0]
    scope = UUID(harness.fixture["scope_id"])
    with transaction(store.engine, access) as c:
        visible = set(c.execute(text("SELECT ops.readable_scope_ids()")).scalars())
        assert scope in visible
        for target in c.execute(select(t.scopes.c.scope_id)).scalars():
            assert c.execute(text("SELECT ops.can_access(:scope)"), {"scope": target}).scalar_one() == (target in visible)
        c.execute(text("SELECT set_config('navigator.principal',:foreign,true)"),
                  {"foreign": str(live_users[1][1].principal_id)})
        assert list(c.execute(text("SELECT ops.readable_scope_ids()")).scalars()) == []
    with harness.store.engine.begin() as c:
        c.execute(update(t.scopes).where(t.scopes.c.scope_id == scope).values(revoked=True))
    try:
        with transaction(store.engine, access) as c:
            assert scope not in c.execute(text("SELECT ops.readable_scope_ids()")).scalars().all()
            assert not c.execute(text("SELECT ops.can_access(:scope)"), {"scope": scope}).scalar_one()
    finally:
        with harness.store.engine.begin() as c:
            c.execute(update(t.scopes).where(t.scopes.c.scope_id == scope).values(revoked=False))


def test_prepared_eligibility_exact_membership_and_cleanup(live_users):
    store, access = live_users[0]
    context, plan = start(store, access, "prepared-membership")
    params = {"snapshot": plan.snapshot_id, "namespace": access.namespace, "run": context.run_id,
              "case": context.case_id, "all_languages": True, "languages": ["und"],
              "all_documents": True, "excluded": [UUID(int=0)],
              "all_families": True, "families": [UUID(int=0)]}
    with transaction(store.engine, access) as c:
        expected = set(c.execute(query_statement("SELECT c.chunk_id " + ELIGIBLE), params).scalars())
        prepare(c, ELIGIBLE, params, vectors=True)
        actual = set(c.execute(text("SELECT chunk_id FROM pg_temp.navigator_retrieval_eligible")).scalars())
        assert actual == expected
        assert c.execute(text("SELECT reltuples FROM pg_class WHERE oid='pg_temp.navigator_retrieval_members'::regclass")).scalar_one() == len(expected)
    with transaction(store.engine, access) as c:
        assert c.execute(text("SELECT to_regclass('pg_temp.navigator_retrieval_members')")).scalar_one() is None


def test_foreign_owner_and_filtering_remain_enforced(live_users):
    store, access = live_users[0]
    foreign_store, foreign = live_users[1]
    context, plan = start(store, access, "prepared-private")
    result = HybridSearch(store.engine, FixtureEmbedder()).search(access, plan)
    assert result.hits
    excluded = plan.model_copy(update={"excluded_document_ids": list({h.document_id for h in result.hits})})
    assert not HybridSearch(store.engine, FixtureEmbedder()).search(access, excluded).hits
    with pytest.raises((PermissionError, NoResultFound)):
        HybridSearch(foreign_store.engine, FixtureEmbedder()).search(foreign, plan)
    with transaction(store.engine, access) as c:
        flags = c.execute(text("SELECT rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user")).one()
        assert not any(flags)


def test_six_variants_keep_exact_dense_scores_and_lineage(live_users):
    store, access = live_users[0]
    _, plan = start(store, access, "prepared-six")
    plan = plan.model_copy(update={"variants": ["monitoring", "glucose sensors", "CGM", "diabetes", "sensor"]})
    result = HybridSearch(store.engine, FixtureEmbedder(), strategy="rrf").search(access, plan)
    assert result.hits
    for hit in result.hits:
        assert hit.evidence_ids and hit.query_matches
        if hit.cosine_distance is not None:
            assert -1e-6 <= hit.cosine_distance <= 2
    again = HybridSearch(store.engine, FixtureEmbedder(), strategy="rrf").search(access, plan)
    assert [(h.chunk_id, h.fusion_score, h.cosine_distance, h.query_matches) for h in result.hits] == [
        (h.chunk_id, h.fusion_score, h.cosine_distance, h.query_matches) for h in again.hits]


def test_prepared_ranks_equal_direct_authorized_queries(live_users):
    store, access = live_users[0]
    context, plan = start(store, access, "exact-ranks")
    params = {"snapshot": plan.snapshot_id, "namespace": access.namespace, "run": context.run_id,
              "case": context.case_id, "all_languages": True, "languages": ["und"],
              "all_documents": True, "excluded": [UUID(int=0)],
              "all_families": True, "families": [UUID(int=0)]}
    queries = ["glucose", "monitoring"]
    vectors = [FixtureEmbedder().embed_query(q) for q in queries]
    from backend.data.repositories.corpus import LANGUAGE_CONFIGS
    with transaction(store.engine, access) as c:
        params["search_hash"] = c.execute(select(t.builds.c.search_config_hash).where(
            t.builds.c.build_id == plan.build_id)).scalar_one()
        expected_lexical, expected_dense = [], []
        for idx, query in enumerate(queries):
            qparams = {**params, "query": query, "vector": "[" + ",".join(map(str, vectors[idx])) + "]"}
            linked = ELIGIBLE.replace("WHERE s.snapshot_id", "JOIN retrieval.search_documents p ON p.chunk_id=c.chunk_id WHERE s.snapshot_id")
            expression = "websearch_to_tsquery(p.language_config::regconfig,:query)"
            lexical_sql = ("SELECT c.chunk_id,max(ts_rank_cd(p.terms," + expression + ")) AS score " +
                           linked + " AND p.search_config_hash=:search_hash AND p.terms @@ " + expression +
                           " GROUP BY c.chunk_id ORDER BY score DESC,c.chunk_id LIMIT 30")
            for row in c.execute(query_statement(lexical_sql), qparams).mappings():
                expected_lexical.append({"idx": idx, **dict(row)})
            for row in c.execute(query_statement("SELECT c.chunk_id,e.vector <=> CAST(:vector AS vector) AS score " +
                    ELIGIBLE + " ORDER BY score,c.chunk_id LIMIT 30"), qparams).mappings():
                expected_dense.append({"idx": idx, **dict(row)})
        prepare(c, ELIGIBLE, params, vectors=True)
        actual_l = [dict(r) for r in batched.lexical(c, ELIGIBLE, params, queries, sorted({"simple", *LANGUAGE_CONFIGS.values()}))]
        actual_d = [dict(r) for r in batched.dense(c, ELIGIBLE, params, vectors)]
        assert actual_l == expected_lexical
        assert actual_d == expected_dense


def test_reserved_relation_collision_is_not_reused(live_users):
    store, access = live_users[0]
    _, plan = start(store, access, "reserved-relation")
    # A caller-created reserved name fails instead of supplying foreign membership.
    from backend.application.persistence.session import BoundEngine
    with transaction(store.engine, access) as c:
        c.execute(text("CREATE TEMP TABLE navigator_retrieval_members(marker text) ON COMMIT DROP"))
        with pytest.raises(DBAPIError):
            with c.begin_nested():
                HybridSearch(BoundEngine(c), FixtureEmbedder()).search(access, plan)
        assert c.execute(text("SELECT count(*) FROM pg_temp.navigator_retrieval_members")).scalar_one() == 0


