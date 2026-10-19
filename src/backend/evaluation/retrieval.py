"""Comparable retrieval observations and honest human-label gates."""
from collections import defaultdict
from statistics import median
from time import perf_counter

from pydantic import Field, model_validator

from backend.contracts.data import Contract, QueryPlan
from backend.ingestion.evaluation import ReviewedQuery, recall_at_10
from backend.contracts.services import ServiceError


class QueryCase(Contract):
    id: str
    intent: str
    query: str = Field(min_length=1, max_length=10000)
    kind: str = 'positive'
    expected_entity_ids: list[str] = Field(default_factory=list)
    reviewed: bool = False
    reviewer: str = ''

    @model_validator(mode='after')
    def reviewed_labels(self):
        if self.kind not in {'positive', 'negative', 'ambiguity'}:
            raise ValueError('unknown query kind')
        if self.reviewed and (not self.reviewer.strip() or (self.kind == 'positive' and not self.expected_entity_ids)):
            raise ValueError('reviewed positive queries require independent reviewer and expected entities')
        if self.expected_entity_ids and not self.reviewed:
            raise ValueError('unreviewed expectations cannot be used as gold')
        return self


class QuerySuite(Contract):
    version: str
    cases: list[QueryCase] = Field(min_length=1, max_length=100)

    @model_validator(mode='after')
    def unique_ids(self):
        if len({case.id for case in self.cases}) != len(self.cases):
            raise ValueError('duplicate query IDs')
        return self


def summarize(suite, observations):
    groups = defaultdict(list)
    by_id = {case.id: case for case in suite.cases}
    for row in observations:
        if row['query_id'] not in by_id:
            raise ValueError('unknown measured query')
        groups[row['strategy']].append(row)
    result = {}
    for strategy, rows in groups.items():
        # Repetitions measure latency; they must not overweight a wording variant.
        per_query = {}
        for row in rows:
            if row.get('status', 'succeeded') == 'succeeded':
                per_query.setdefault(row['query_id'], row)
        positives = [(by_id[key], row) for key, row in per_query.items()
                     if by_id[key].reviewed and by_id[key].kind == 'positive']
        labels = [ReviewedQuery(q.query, frozenset(q.expected_entity_ids), q.reviewer, q.intent) for q, _ in positives]
        metric = recall_at_10(labels, [r['entity_ids'] for _, r in positives]) if labels else None
        result[strategy] = {'measurements': len(rows), 'failures': sum(r.get('status') == 'failed' for r in rows),
            'latency_median_seconds': median(r['seconds'] for r in rows),
            'latency_max_seconds': max(r['seconds'] for r in rows),
            'reviewed_quality': metric, 'quality_status': 'reviewed_subset_only' if labels else 'pending_independent_labels',
            'unreviewed_queries': sum(not by_id[key].reviewed for key in per_query),
            'negative_cases': [{'query_id': q.id, 'returned_entities': len(r['entity_ids']),
                'expected_abstention': q.reviewed} for key, r in per_query.items() if (q := by_id[key]).kind == 'negative']}
    return result


def measure(searches, catalog, access, context, suite, repeats=1):
    if not 1 <= repeats <= 5:
        raise ValueError('repeats must be 1–5')
    observations = []
    for case in suite.cases:
        plan = QueryPlan(original_request=case.query, variants=[], run_id=context.run_id,
            case_id=context.case_id, input_revision_id=context.input_id, snapshot_id=context.snapshot_id,
            profile_id=context.profile_id, taxonomy_version_id=context.taxonomy_version_id,
            build_id=context.build_id, embedding_config_hash=context.embedding_config_hash)
        for strategy, search in searches.items():
            for repeat in range(repeats):
                started = perf_counter()
                try:
                    result = search.search(access, plan)
                except ServiceError as error:
                    observations.append({'query_id': case.id, 'strategy': strategy, 'repeat': repeat,
                        'seconds': round(perf_counter()-started, 6), 'status': 'failed', 'error_code': error.code})
                    continue
                entities = catalog.entities_for_hits(access, context.snapshot_id, result.hits)
                observations.append({'query_id': case.id, 'strategy': strategy, 'repeat': repeat, 'status': 'succeeded',
                    'seconds': round(perf_counter()-started, 6), 'entity_ids': [str(e['entity_id']) for e in entities][:10],
                    'hits': [{'chunk_id': str(h.chunk_id), 'document_id': str(h.document_id),
                        'url': h.source_url, 'evidence_ids': list(map(str, h.evidence_ids))} for h in result.hits],
                    'limitations': result.limitations})
    return {'suite_version': suite.version, 'pins': {key: str(getattr(context, key)) for key in
        ('snapshot_id', 'profile_id', 'taxonomy_version_id', 'build_id', 'embedding_config_hash')},
        'summary': summarize(suite, observations), 'observations': observations}
