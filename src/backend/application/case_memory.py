"""Own-case semantic memory: opt-in, versioned, never generated-pitch learning."""
import asyncio
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import cast, func, insert, select, text, update

from backend.contracts.data import configuration_hash, validate_vector
from backend.contracts.pipeline import CaseInterpretation
from backend.contracts.services import ServiceUnavailable, StaleRevision
from backend.data import schema as t


def profile(interpretation):
    # Outcomes, company names and generated recommendations cannot inflate similarity.
    value = {key: interpretation.model_dump(mode='json')[key] for key in
        ('activity_label', 'primary_field', 'additional_fields', 'needs', 'bern_intents', 'constraints', 'concepts')}
    import json
    semantic = json.dumps(value, ensure_ascii=False, sort_keys=True)
    if len(semantic) > 8000:
        raise ValueError('case profile exceeds indexing budget')
    return value, semantic


class CaseMemory:
    def __init__(self, store, embedder, *, minimum_score=50):
        self.store, self.embedder, self.minimum_score = store, embedder, minimum_score

    def available(self):
        try:
            self.embedder.config_hash
        except ServiceUnavailable:
            return False
        with self.store.engine.connect() as c:
            return c.execute(text("SELECT to_regclass('cases.memory_profiles') IS NOT NULL")).scalar_one()

    def state(self, access, case_id):
        if not self.available():
            return {'available': False, 'eligible': False}
        with self.store.session(access) as c:
            case = self.store.case(c, access, case_id)
            eligible = c.execute(select(t.case_memory.c.memory_id).where(t.case_memory.c.case_id == case_id,
                t.case_memory.c.owner_id == access.principal_id, t.case_memory.c.namespace == access.namespace,
                t.case_memory.c.enabled, t.case_memory.c.input_id == case['current_input_id'])).first()
            return {'available': True, 'eligible': bool(eligible)}

    async def set(self, access, case_id, key, body):
        if not await asyncio.to_thread(self.available):
            raise ServiceUnavailable()
        prepared = None
        if body['eligible']:
            if body['synthetic'] or not body['permitted_context_confirmed']:
                raise ValueError('only explicitly permitted non-synthetic cases may be indexed')
            prepared = await asyncio.to_thread(self._prepare, access, case_id, body)
            vector = prepared.get('vector')
            if vector is None:
                vector = await asyncio.to_thread(self.embedder.embed_query, prepared['semantic'])
            prepared['vector'] = validate_vector(vector, len(vector))
        return await asyncio.to_thread(self._save, access, case_id, key, body, prepared)

    def _prepare(self, access, case_id, body):
        with self.store.session(access) as c:
            case = self.store.case(c, access, case_id)
            if case['revision'] != body['expected_revision'] or not case['current_result_id']:
                raise StaleRevision()
            result = c.execute(select(t.results).where(t.results.c.result_id == case['current_result_id'])).mappings().one()
            if result['result_hash'] != body['expected_result_hash']:
                raise StaleRevision()
            from backend.data.repositories.drafts import selection_hash as current_selection_hash
            self.store.repositories(c)[0]._validate_pack(c, result['pack_id'])
            selection_hash = current_selection_hash(c, result['result_id'], require_complete=True)
            review = c.execute(select(t.reviews.c.review_id).where(t.reviews.c.result_id == result['result_id'],
                t.reviews.c.result_hash == result['result_hash'], t.reviews.c.selection_hash == selection_hash,
                t.reviews.c.decision == 'accepted')).first()
            if not review:
                raise ValueError('case memory requires an exact reviewed result')
            pack = c.execute(select(t.packs.c.payload).where(t.packs.c.pack_id == result['pack_id'])).scalar_one()
            interpretation = CaseInterpretation.model_validate(pack['interpretation'])
            value, semantic = profile(interpretation)
            cached = c.execute(select(t.case_memory.c.embedding).where(t.case_memory.c.case_id == case_id,
                t.case_memory.c.input_id == case['current_input_id'], t.case_memory.c.projection_hash == configuration_hash(value),
                t.case_memory.c.embedding_config_hash == self.embedder.config_hash)).scalar_one_or_none()
            return {'input_id': case['current_input_id'], 'result_id': result['result_id'], 'features': value,
                'semantic': semantic, 'companyLabel': interpretation.company_name or 'Previous case',
                'outcome': case['outcome'], 'status': case['status'], 'selection_hash': selection_hash,
                'vector': [float(v) for v in cached] if cached is not None else None}

    def _save(self, access, case_id, key, body, prepared):
        def callback(c):
            case = self.store.case(c, access, case_id)
            if case['revision'] != body['expected_revision']:
                raise StaleRevision()
            c.execute(update(t.case_memory).where(t.case_memory.c.case_id == case_id,
                t.case_memory.c.owner_id == access.principal_id, t.case_memory.c.namespace == access.namespace).values(enabled=False))
            if prepared:
                if case['current_input_id'] != prepared['input_id'] or case['current_result_id'] != prepared['result_id']:
                    raise StaleRevision()
                from backend.data.repositories.drafts import selection_hash
                if selection_hash(c, prepared['result_id'], require_complete=True) != prepared['selection_hash']:
                    raise StaleRevision()
                digest = configuration_hash(prepared['features'])
                existing = c.execute(select(t.case_memory.c.memory_id).where(t.case_memory.c.case_id == case_id,
                    t.case_memory.c.input_id == prepared['input_id'], t.case_memory.c.projection_hash == digest,
                    t.case_memory.c.embedding_config_hash == self.embedder.config_hash)).scalar_one_or_none()
                if existing:
                    c.execute(update(t.case_memory).where(t.case_memory.c.memory_id == existing).values(enabled=True))
                else:
                    c.execute(insert(t.case_memory).values(memory_id=uuid4(), case_id=case_id,
                        input_id=prepared['input_id'], result_id=prepared['result_id'], owner_id=access.principal_id,
                        namespace=access.namespace, projection_hash=digest, embedding_config_hash=self.embedder.config_hash,
                        dimension=len(prepared['vector']), embedding=prepared['vector'], payload={
                            key: prepared[key] for key in ('features', 'companyLabel', 'outcome', 'status')}))
            return {'case_id': str(case_id), 'eligible': body['eligible']}
        return self.store.command(access, key, f'memory:{case_id}', body, callback)

    async def search(self, access, case_id, interpretation, limit=5):
        if not await asyncio.to_thread(self.available):
            raise ServiceUnavailable()
        features, semantic = profile(interpretation)
        vector = await asyncio.to_thread(self.embedder.embed_query, semantic)
        vector = validate_vector(vector, len(vector))
        return await asyncio.to_thread(self._search, access, case_id, features, vector, limit)

    def _search(self, access, case_id, features, vector, limit):
        if not 1 <= limit <= 10:
            raise ValueError('case match limit must be 1–10')
        with self.store.session(access) as c:
            self.store.case(c, access, case_id)
            c.execute(text("SET LOCAL hnsw.iterative_scan='strict_order'"))
            distance = cast(t.case_memory.c.embedding, Vector(len(vector))).cosine_distance(vector)
            rows = c.execute(select(t.case_memory, distance.label('distance')).join(t.cases,
                t.cases.c.case_id == t.case_memory.c.case_id).where(t.case_memory.c.owner_id == access.principal_id,
                t.case_memory.c.namespace == access.namespace, t.case_memory.c.enabled,
                t.case_memory.c.case_id != case_id, t.case_memory.c.input_id == t.cases.c.current_input_id,
                t.case_memory.c.embedding_config_hash == self.embedder.config_hash,
                t.case_memory.c.dimension == len(vector)).order_by(distance, t.case_memory.c.memory_id).limit(50)).mappings().all()
            result = []
            for row in rows:
                score = round(max(0, min(1, 1-float(row['distance'])))*100, 1)
                if score < self.minimum_score:
                    continue
                old = row['payload']['features']
                shared = [need for need in old['needs'] if need.casefold() in {n.casefold() for n in features['needs']}]
                differences = [need for need in features['needs'] if need.casefold() not in {n.casefold() for n in old['needs']}]
                status = {'ready_for_review': 'in_review', 'draft': 'researching'}.get(row['payload']['status'], row['payload']['status'])
                result.append({'memoryId': str(row['memory_id']), 'caseId': str(row['case_id']),
                    'companyLabel': row['payload']['companyLabel'], 'score': score,
                    'method': 'symmetric-needs-cosine-v1', 'shared': shared, 'differences': differences[:5],
                    'status': status if status in {'in_review', 'researching', 'pitch_sent', 'closed'} else 'researching',
                    **({'outcome': row['payload']['outcome']} if row['payload']['outcome'] else {}), 'inputId': str(row['input_id']),
                    'resultId': str(row['result_id']), 'indexedAt': row['created_at'].isoformat()})
                if len(result) == limit:
                    break
            return result

    def visible_ids(self, access, identities):
        if not identities or not self.available():
            return set()
        with self.store.session(access) as c:
            return set(map(str, c.execute(select(t.case_memory.c.memory_id).join(t.cases,
                t.cases.c.case_id == t.case_memory.c.case_id).where(t.case_memory.c.owner_id == access.principal_id,
                t.case_memory.c.memory_id.in_([UUID(value) for value in identities]),
                t.case_memory.c.namespace == access.namespace, t.case_memory.c.enabled,
                t.case_memory.c.input_id == t.cases.c.current_input_id)).scalars()))
