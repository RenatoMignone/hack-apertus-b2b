"""Regression: bounded extraction must reach later documents and retain literal IDs."""
import asyncio
from uuid import uuid4

from backend.contracts.services import ExtractionBatch, ResearchBundle
from backend.evidence.extraction_batches import extract_batches
from backend.evidence.extraction_selection import select_batches


def test_large_first_document_cannot_starve_later_sources(evidence):
    records = []
    for doc in range(31):
        version = uuid4()
        for span in range(20 if doc == 0 else 4):
            records.append(evidence.model_copy(update={'evidence_id': uuid4(),
                'document_version_id': version, 'char_start': span*100}))
    batches, _ = select_batches(records, [])
    selected = [e for batch in batches[:6] for e in batch]
    assert {e.document_version_id for e in selected} == {e.document_version_id for e in records}
    assert all(len(batch) <= 12 and sum(len(e.literal_text) for e in batch) <= 18000 for batch in batches)
    assert len([e for batch in batches for e in batch]) == len(records)


def test_batch_absence_is_scoped_to_assessed_subset(context, interpretation, evidence):
    async def extract(*args):
        return ExtractionBatch(gaps=['No named researcher is documented.'])
    result = asyncio.run(extract_batches(extract, interpretation,
        ResearchBundle(evidence=[evidence]), context))
    assert result.gaps == ['Within extraction batch 1 only (not a corpus-wide finding): No named researcher is documented.']
