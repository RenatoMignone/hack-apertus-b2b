"""Exercise real PostgreSQL cancellation and savepoint recovery on disposable DBs."""
from uuid import UUID

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from backend.contracts.data import AccessContext, QueryPlan
from backend.contracts.services import ServiceUnavailable
from backend.data.fixtures import FixtureEmbedder
from backend.data.repositories.snapshots import SnapshotRepository
from backend.data.retrieval import batched
from backend.data.retrieval.hybrid import HybridSearch


def timeout(connection, *args):
    connection.execute(text("SET LOCAL statement_timeout='1ms'"))
    connection.execute(text("SELECT pg_sleep(0.05)"))


def setup_search(database, corpus, strategy=None):
    fixture, _ = corpus
    access = AccessContext(principal_id=fixture['principal_id'], namespace=fixture['namespace'])
    snapshot = SnapshotRepository(database).get(access,
        profile_id=UUID(fixture['profile_id']), snapshot_id=UUID(fixture['snapshot_id']))
    plan = QueryPlan(original_request='glucose', profile_id=fixture['profile_id'],
        snapshot_id=fixture['snapshot_id'], taxonomy_version_id=fixture['taxonomy_version_id'],
        build_id=snapshot['build_id'], embedding_config_hash=fixture['embedding_config_hash'])
    return HybridSearch(database, FixtureEmbedder(), strategy=strategy), access, plan


@pytest.mark.integration
@pytest.mark.parametrize('failed_branch,limitation,missing_rank', [
    ('lexical', 'lexical_search_timeout', 'lexical_rank'),
    ('dense', 'vector_search_timeout', 'vector_rank'),
])
def test_timeout_preserves_other_authorized_branch(database, corpus, monkeypatch,
                                                  failed_branch, limitation, missing_rank):
    search, access, plan = setup_search(database, corpus)
    monkeypatch.setattr(batched, failed_branch, timeout)
    result = search.search(access, plan)
    assert result.hits
    assert limitation in result.limitations
    assert all(getattr(hit, missing_rank) is None for hit in result.hits)
    assert all(hit.snapshot_id == plan.snapshot_id and hit.query_matches for hit in result.hits)


@pytest.mark.integration
def test_both_branches_timeout_is_service_failure(database, corpus, monkeypatch):
    search, access, plan = setup_search(database, corpus)
    monkeypatch.setattr(batched, 'lexical', timeout)
    monkeypatch.setattr(batched, 'dense', timeout)
    with pytest.raises(ServiceUnavailable):
        search.search(access, plan)


@pytest.mark.integration
@pytest.mark.parametrize('strategy', ['lexical', 'rrf', 'reranked'])
def test_explicit_evaluation_never_silently_degrades(database, corpus, monkeypatch, strategy):
    search, access, plan = setup_search(database, corpus, strategy)
    monkeypatch.setattr(batched, 'lexical', timeout)
    with pytest.raises(DBAPIError):
        search.search(access, plan)


@pytest.mark.integration
def test_non_timeout_sql_error_is_not_hidden(database, corpus, monkeypatch):
    search, access, plan = setup_search(database, corpus)
    def invalid(connection, *args):
        connection.execute(text('SELECT 1/0'))
    monkeypatch.setattr(batched, 'lexical', invalid)
    with pytest.raises(DBAPIError):
        search.search(access, plan)


@pytest.mark.integration
def test_surviving_empty_branch_still_reports_incomplete_search(database, corpus, monkeypatch):
    search, access, plan = setup_search(database, corpus)
    monkeypatch.setattr(batched, 'lexical', timeout)
    monkeypatch.setattr(batched, 'dense', lambda *args: [])
    result = search.search(access, plan)
    assert not result.hits
    assert 'lexical_search_timeout' in result.limitations
