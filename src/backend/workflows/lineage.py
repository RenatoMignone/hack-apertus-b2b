"""Recorded retrieval paths only; never infer concept relevance from text overlap."""
from hashlib import sha256

from backend.contracts.pipeline import canonical_url


def source_identity(record):
    return (canonical_url(record.url), record.body_hash, record.char_start,
            record.char_end, record.literal_text)


def search_trace(input_id, observations, research_records, canonical_records):
    canonical = {}
    for record in canonical_records:
        canonical.setdefault(source_identity(record), set()).add(str(record.evidence_id))
    remap = {str(record.evidence_id): canonical.get(source_identity(record), set())
             for record in research_records}
    input_key = "input:"+str(input_id)
    terms, links = {}, set()
    for row in observations:
        evidence_ids = {key for original in row["evidence_ids"] for key in remap.get(original, set())}
        if not evidence_ids:
            continue
        query = row["query"]
        term_key = "query:"+sha256(query.encode()).hexdigest()[:20]
        terms[term_key] = {"id": term_key, "label": query}
        links.add((input_key, term_key))
        links.update((term_key, evidence_id) for evidence_id in evidence_ids)
    return {"inputs": [{"id": input_key, "label": "Original permitted request"}] if terms else [],
            "terms": list(terms.values()), "links": [
                {"source": source, "target": target, "value": 1} for source, target in sorted(links)]}
