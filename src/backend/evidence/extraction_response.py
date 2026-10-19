"""Short model-only support references; canonical evidence IDs stay code-owned."""
from backend.contracts.services import EntityCandidate, ClaimCandidate, ExtractionBatch


class EntityResponse(EntityCandidate):
    evidence_ids: list[str]


class ClaimResponse(ClaimCandidate):
    evidence_ids: list[str]


class ExtractionResponse(ExtractionBatch):
    entities: list[EntityResponse]
    claims: list[ClaimResponse]


def canonical_batch(response, references):
    value = response.model_dump(mode='json')
    for item in [*value['entities'], *value['claims']]:
        if any(key not in references for key in item['evidence_ids']):
            raise ValueError('evidence_ids must use the supplied S1, S2 support references; remove unknown references')
        item['evidence_ids'] = [references[key] for key in item['evidence_ids']]
    return ExtractionBatch.model_validate(value)
