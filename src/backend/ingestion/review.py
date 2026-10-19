"""Explicit corpus-owner curation. Dry-run and apply share source/hash checks."""
import json
from typing import Literal
from uuid import UUID, uuid5

from pydantic import Field, model_validator
from sqlalchemy import insert, select, update, exists
from sqlalchemy.dialects.postgresql import insert as pg_insert

from backend.contracts.data import Contract, configuration_hash, content_hash
from backend.data import schema as t
from backend.data.database import require_scope, transaction


def digest(value):
    return configuration_hash(json.loads(json.dumps(value, default=str)))


class RecordDecision(Contract):
    kind: Literal['entity', 'claim']
    record_id: UUID
    expected_hash: str = Field(pattern=r'^[a-f0-9]{64}$')
    decision: Literal['accepted', 'rejected']
    justification: str = Field(min_length=1)
    semantic_support_confirmed: bool = False


class TagDecision(Contract):
    concept_id: UUID
    evidence_id: UUID
    mapping_kind: Literal['direct', 'related'] = 'direct'
    justification: str = Field(min_length=1)
    semantic_support_confirmed: bool


class ReviewManifest(Contract):
    schema_version: Literal[1] = 1
    scope_id: UUID
    reviewer: str = Field(min_length=1)
    decisions: list[RecordDecision] = Field(default_factory=list, max_length=100)
    tags: list[TagDecision] = Field(default_factory=list, max_length=100)

    @model_validator(mode='after')
    def real_review(self):
        if not self.reviewer.strip() or any(not item.justification.strip() for item in [*self.decisions, *self.tags]):
            raise ValueError('reviewer and substantive justification required')
        return self


def source_record(c, evidence_id, scope_id):
    row = c.execute(select(t.spans, t.versions.c.body_hash, t.versions.c.body_text,
        t.versions.c.status.label('version_status'), t.documents.c.canonical_url).select_from(
        t.spans.join(t.versions).join(t.documents)).where(t.spans.c.evidence_id == evidence_id,
        t.spans.c.scope_id == scope_id, t.versions.c.scope_id == scope_id)).mappings().one()
    if (row['version_status'] != 'accepted' or content_hash(row['body_text'].encode()) != row['body_hash']
            or row['body_text'][row['char_start']:row['char_end']] != row['literal_text']):
        raise ValueError('source body/hash/literal support is invalid')
    return {key: row[key] for key in ('evidence_id', 'document_version_id', 'body_hash',
        'char_start', 'char_end', 'literal_text', 'canonical_url')}


def record(c, kind, record_id, scope_id, *, lock=False):
    table = t.entities if kind == 'entity' else t.claims
    key = table.c.entity_id if kind == 'entity' else table.c.claim_id
    query = select(table).where(key == record_id, table.c.scope_id == scope_id)
    row = dict(c.execute(query.with_for_update() if lock else query).mappings().one())
    if kind == 'claim':
        links = c.execute(select(t.claim_evidence).where(t.claim_evidence.c.claim_id == record_id).order_by(t.claim_evidence.c.evidence_id)).mappings().all()
    else:
        links = c.execute(select(t.claim_evidence).join(t.claims).where(
            t.claims.c.subject_id == record_id, t.claims.c.scope_id == scope_id).order_by(t.claim_evidence.c.evidence_id)).mappings().all()
    row['support'] = [{**source_record(c, link['evidence_id'], scope_id), 'relation': link['relation']} for link in links]
    return row


class CorpusReview:
    def __init__(self, engine):
        self.engine = engine

    def candidates(self, access, scope_id, limit=50):
        if not 1 <= limit <= 100:
            raise ValueError('limit must be 1–100')
        with transaction(self.engine, access) as c:
            require_scope(c, scope_id)
            rows = []
            for kind, table, key in [('entity', t.entities, t.entities.c.entity_id), ('claim', t.claims, t.claims.c.claim_id)]:
                query = select(key).where(table.c.scope_id == scope_id, table.c.status.in_(['draft', 'needs_review']))
                if kind == 'claim':
                    newer = t.claims.alias('newer_claim')
                    query = query.where(~exists(select(newer.c.claim_id).where(newer.c.supersedes_id == key,
                        newer.c.scope_id == scope_id, newer.c.status.in_(['accepted', 'rejected']))))
                ids = c.execute(query.order_by(key).limit(limit)).scalars()
                for identity in ids:
                    value = record(c, kind, identity, scope_id)
                    rows.append({'kind': kind, 'record_id': str(identity), 'expected_hash': digest(value),
                        'record': json.loads(json.dumps(value, default=str))})
            return {'scope_id': str(scope_id), 'candidates': rows,
                'notice': 'Source integrity is checked; semantic support still requires explicit review.'}

    def review(self, access, manifest, *, apply=False):
        manifest = ReviewManifest.model_validate(manifest)
        if not manifest.decisions and not manifest.tags:
            raise ValueError('empty review')
        if len({(d.kind, d.record_id) for d in manifest.decisions}) != len(manifest.decisions):
            raise ValueError('duplicate review decision')
        with transaction(self.engine, access) as c:
            require_scope(c, manifest.scope_id, write=apply)
            if c.execute(select(t.scopes.c.kind).where(t.scopes.c.scope_id == manifest.scope_id)).scalar_one() != 'public':
                raise ValueError('shared curation is restricted to public corpus scopes')
            staged, already = [], []
            for decision in sorted(manifest.decisions, key=lambda item: (item.kind, str(item.record_id))):
                audit_id = uuid5(decision.record_id, digest({'reviewer': manifest.reviewer, **decision.model_dump(mode='json')}))
                if c.execute(select(t.derivations.c.derivation_id).where(t.derivations.c.derivation_id == audit_id,
                        t.derivations.c.scope_id == manifest.scope_id)).first():
                    already.append(str(decision.record_id)); continue
                value = record(c, decision.kind, decision.record_id, manifest.scope_id, lock=apply)
                if apply and c.execute(select(t.derivations.c.derivation_id).where(t.derivations.c.derivation_id == audit_id,
                        t.derivations.c.scope_id == manifest.scope_id)).first():
                    already.append(str(decision.record_id)); continue
                if decision.kind == 'claim' and c.execute(select(t.claims.c.claim_id).where(
                        t.claims.c.supersedes_id == decision.record_id, t.claims.c.scope_id == manifest.scope_id,
                        t.claims.c.status.in_(['accepted', 'rejected']))).first():
                    raise ValueError('stale claim: a reviewed successor already exists')
                if digest(value) != decision.expected_hash or value['status'] not in {'draft', 'needs_review'}:
                    raise ValueError('stale or already finalized record')
                if decision.decision == 'accepted':
                    if not decision.semantic_support_confirmed or not value['support']:
                        raise ValueError('acceptance requires explicit semantic review and literal sources')
                    if any(s['relation'] != 'supports' for s in value['support']):
                        raise ValueError('contradictory support needs separate resolution')
                    if decision.kind == 'entity' and not any(value['display_label'].casefold() in s['literal_text'].casefold() for s in value['support']):
                        raise ValueError('entity name is not literally supported')
                staged.append((decision, value, audit_id))
            accepted_entities = {d.record_id for d, _, _ in staged if d.kind == 'entity' and d.decision == 'accepted'}
            for decision, value, _ in staged:
                if decision.kind == 'claim' and decision.decision == 'accepted':
                    for identity in [value['subject_id'], *([value['object_entity_id']] if value['object_entity_id'] else [])]:
                        entity = c.execute(select(t.entities).where(t.entities.c.entity_id == identity,
                            t.entities.c.scope_id == manifest.scope_id)).mappings().one()
                        if entity['status'] != 'accepted' and identity not in accepted_entities:
                            raise ValueError('claim endpoints need accepted identities')
            tags = []
            counts = {}
            for tag in manifest.tags:
                if not tag.semantic_support_confirmed:
                    raise ValueError('tagging requires explicit semantic review')
                support = source_record(c, tag.evidence_id, manifest.scope_id)
                concept = c.execute(select(t.concepts).join(t.taxonomies).where(t.concepts.c.concept_id == tag.concept_id,
                    t.taxonomies.c.status == 'reviewed', t.concepts.c.facet != 'system')).mappings().one()
                pair = (support['document_version_id'], concept['taxonomy_version_id'])
                counts.setdefault(pair, set())
                if concept['facet'] != 'category':
                    counts[pair].add(tag.concept_id)
                counts[pair].update(c.execute(select(t.assignments.c.concept_id).join(t.concepts).where(
                    t.assignments.c.document_version_id == pair[0], t.concepts.c.taxonomy_version_id == pair[1],
                    t.concepts.c.facet != 'category',
                    t.assignments.c.status != 'rejected')).scalars())
                if len(counts[pair]) > 3:
                    raise ValueError('document topic budget exceeded')
                tags.append((tag, support))
            if apply:
                for decision, value, audit_id in staged:
                    c.execute(insert(t.derivations).values(derivation_id=audit_id, scope_id=manifest.scope_id,
                        inputs={'kind': 'corpus_review', 'reviewer': manifest.reviewer,
                            'decision': decision.model_dump(mode='json'), 'source_hashes': [s['body_hash'] for s in value['support']]},
                        configuration_hash=digest({'corpus_review': 1}), output_hash=decision.expected_hash, status=decision.decision))
                    if decision.kind == 'entity':
                        c.execute(update(t.entities).where(t.entities.c.entity_id == decision.record_id).values(status=decision.decision))
                    else:
                        # Claims and support links are immutable. Review creates
                        # an explicit successor; existing snapshots keep old IDs.
                        revision = uuid5(audit_id, 'reviewed-claim')
                        body = {key: value[key] for key in ('subject_id', 'predicate', 'object_entity_id', 'typed_literal')}
                        c.execute(insert(t.claims).values(claim_id=revision, scope_id=manifest.scope_id, **body,
                            derivation_id=audit_id, supersedes_id=decision.record_id, status=decision.decision))
                        for support in value['support']:
                            c.execute(insert(t.claim_evidence).values(claim_id=revision, evidence_id=support['evidence_id'],
                                relation=support['relation'], review_decision=decision.decision))
                for tag, support in tags:
                    identity = uuid5(support['document_version_id'], digest({'tag': tag.model_dump(mode='json'), 'reviewer': manifest.reviewer}))
                    c.execute(pg_insert(t.derivations).values(derivation_id=identity, scope_id=manifest.scope_id,
                        inputs={'kind': 'reviewed_tag', 'reviewer': manifest.reviewer, **tag.model_dump(mode='json'),
                            'body_hash': support['body_hash']}, configuration_hash=digest({'reviewed_tag': 1}),
                        output_hash=digest(tag.model_dump(mode='json')), status='accepted').on_conflict_do_nothing())
                    c.execute(pg_insert(t.assignments).values(assignment_id=identity, scope_id=manifest.scope_id,
                        concept_id=tag.concept_id, document_version_id=support['document_version_id'],
                        derivation_id=identity, mapping_kind=tag.mapping_kind, status='accepted').on_conflict_do_nothing())
                    c.execute(pg_insert(t.assignment_evidence).values(assignment_id=identity, evidence_id=tag.evidence_id).on_conflict_do_nothing())
            return {'applied': apply, 'records': len(staged), 'tags': len(tags), 'already_applied': already}
