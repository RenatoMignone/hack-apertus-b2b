import pytest
from backend.evaluation.retrieval import QueryCase, QuerySuite, summarize


def test_reviewed_intent_metric_and_repeats_do_not_weight_variants():
    suite=QuerySuite(version='fixture',cases=[
        QueryCase(id='a',intent='one',query='A',reviewed=True,reviewer='fixture-reviewer',expected_entity_ids=['x']),
        QueryCase(id='b',intent='two',query='B',reviewed=True,reviewer='fixture-reviewer',expected_entity_ids=['y'])])
    rows=[{'query_id':key,'strategy':'rrf','seconds':1,'entity_ids':ids} for key,ids in [('a',['x','x']),('a',['x']),('b',[])]]
    assert summarize(suite,rows)['rrf']['reviewed_quality']['score']==.5


def test_unreviewed_queries_never_claim_quality_or_negative_abstention():
    suite=QuerySuite(version='candidate',cases=[QueryCase(id='x',intent='x',query='Unknown',kind='negative')])
    value=summarize(suite,[{'query_id':'x','strategy':'dense','seconds':2,'entity_ids':[]}])['dense']
    assert value['reviewed_quality'] is None and not value['negative_cases'][0]['expected_abstention']
    with pytest.raises(ValueError): QueryCase(id='x',intent='x',query='x',expected_entity_ids=['fabricated'])
    with pytest.raises(ValueError): QuerySuite(version='x',cases=[suite.cases[0],suite.cases[0]])


@pytest.mark.integration
def test_lexical_baseline_does_not_call_embedding_or_reranker(database,corpus):
    from uuid import UUID
    from backend.contracts.data import AccessContext,QueryPlan
    from backend.data.fixtures import FixtureEmbedder
    from backend.data.repositories.snapshots import SnapshotRepository
    from backend.data.retrieval.hybrid import HybridSearch
    fixture,_=corpus
    access=AccessContext(principal_id=fixture['principal_id'],namespace=fixture['namespace'])
    snapshot=SnapshotRepository(database).get(access,profile_id=UUID(fixture['profile_id']),snapshot_id=UUID(fixture['snapshot_id']))
    plan=QueryPlan(original_request='glucose',profile_id=fixture['profile_id'],snapshot_id=fixture['snapshot_id'],
        taxonomy_version_id=fixture['taxonomy_version_id'],build_id=snapshot['build_id'],embedding_config_hash=fixture['embedding_config_hash'])
    class NoCall(FixtureEmbedder):
        def embed_query(self,text): raise AssertionError('lexical called encoder')
    class NoRerank:
        def score(self,*args): raise AssertionError('baseline called reranker')
    result=HybridSearch(database,NoCall(),reranker=NoRerank(),strategy='lexical').search(access,plan)
    assert result.hits and all(hit.vector_rank is None and hit.reranker_score is None for hit in result.hits)
