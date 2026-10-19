"""Bound inference context/output size without changing literal evidence."""
import asyncio

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
    from backend.evidence.extraction_selection import select_batches
    batches, oversized = select_batches(records, research.hits)
    gaps = (["A source passage exceeds the extraction context budget; it was not assessed."]
            if oversized else [])
    from backend.observability.logging import event
    event("extraction.available_batches", run_id=context.run_id, count=len(batches))
    event("extraction.selected_documents", run_id=context.run_id,
          count=len({e.document_version_id for batch in batches[:6] for e in batch}))
    if len(batches) > 6:
        gaps.append("Extraction batch budget reached; remaining passages were not assessed.")
    entities, claims, valid = [], [], 0
    last_error = None
    async def source_batches():
        # Fixed extraction tasks are independent. Two at a time bounds gateway
        # concurrency without serializing up to twelve generation/repair calls.
        # Consume in input order so entity keys and truncation stay deterministic.
        for start in range(0, min(6, len(batches)), 2):
            pair = batches[start:start+2]
            tasks = [asyncio.create_task(extract(interpretation, ResearchBundle(evidence=records,
                existing_entities=research.existing_entities, limitations=research.limitations), context))
                for records in pair]
            try:
                answers = await asyncio.gather(*tasks, return_exceptions=True)
            finally:
                for task in tasks:
                    if not task.done():
                        task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
            for offset, answer in enumerate(answers):
                yield start+offset, answer

    async for index, answer in source_batches():
        if len(entities) >= 30 or len(claims) >= 60:
            gaps.append("Extraction entity/claim budget reached; remaining passages were not assessed.")
            break
        if isinstance(answer, InvalidModelOutput):
            event("extraction.batch_excluded", run_id=context.run_id, attempt=index+1,
                  error_code="invalid_model_output")
            last_error = answer
            gaps.append("A source batch did not produce valid extraction after repair; its claims were excluded.")
            continue
        if isinstance(answer, BaseException):
            raise answer
        batch = answer
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
        # A batch cannot establish absence across the entire corpus. Keep its
        # observation explicitly scoped, even if the model words it globally.
        gaps.extend(f"Within extraction batch {index+1} only (not a corpus-wide finding): {gap}"
                    for gap in batch.gaps)
    if not valid and last_error:
        raise last_error
    return ExtractionBatch(entities=entities, claims=claims, gaps=list(dict.fromkeys(gaps)))
