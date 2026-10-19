"""Bound inference context/output size without changing literal evidence."""
from backend.contracts.services import EvidenceRejected, ExtractionBatch, InvalidModelOutput, ResearchBundle


async def extract_batches(extract, interpretation, research, context):
    unique = {}
    for record in research.evidence:
        if record.evidence_id in unique and record != unique[record.evidence_id]:
            raise EvidenceRejected()
        unique[record.evidence_id] = record
    records = list(unique.values())
    if not records or interpretation.blocking_questions:
        return await extract(interpretation, research, context)
    # Keep each source's identity/header support beside its retrieved passage.
    groups = {}
    for record in records:
        groups.setdefault(record.document_version_id, []).append(record)
    records = [record for group in groups.values() for record in sorted(group, key=lambda e: e.char_start)]
    batches, current, size, gaps = [], [], 0, []
    for record in records:
        if len(record.literal_text) > 18000:
            gaps.append("A source passage exceeds the extraction context budget; it was not assessed.")
            continue
        if current and (len(current) == 12 or size + len(record.literal_text) > 18000):
            batches.append(current)
            current, size = [], 0
        current.append(record)
        size += len(record.literal_text)
    if current:
        batches.append(current)
    if len(batches) > 6:
        gaps.append("Extraction batch budget reached; remaining passages were not assessed.")
    entities, claims, valid = [], [], 0
    last_error = None
    for index, records in enumerate(batches[:6]):
        if len(entities) >= 30 or len(claims) >= 60:
            gaps.append("Extraction entity/claim budget reached; remaining passages were not assessed.")
            break
        try:
            batch = await extract(interpretation, ResearchBundle(evidence=records,
                existing_entities=research.existing_entities, limitations=research.limitations), context)
        except InvalidModelOutput as error:
            last_error = error
            gaps.append("A source batch did not produce valid extraction after repair; its claims were excluded.")
            continue
        valid += 1
        prefix = f"b{index}:" if len(batches) > 1 else ""
        selected = batch.entities[:30-len(entities)]
        keys = {e.key for e in selected}
        candidates = [c for c in batch.claims if c.subject_key in keys and (c.object_key is None or c.object_key in keys)]
        kept = candidates[:60-len(claims)]
        if len(selected) != len(batch.entities) or len(kept) != len(batch.claims):
            gaps.append("Extraction entity/claim budget reached; additional proposals were excluded.")
        entities.extend(e.model_copy(update={"key": prefix+e.key}) for e in selected)
        claims.extend(c.model_copy(update={"key": prefix+c.key, "subject_key": prefix+c.subject_key,
            "object_key": prefix+c.object_key if c.object_key is not None else None}) for c in kept)
        gaps.extend(batch.gaps)
    if not valid and last_error:
        raise last_error
    return ExtractionBatch(entities=entities, claims=claims, gaps=list(dict.fromkeys(gaps)))
