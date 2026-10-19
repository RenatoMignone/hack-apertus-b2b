"""Distribute bounded extraction across documents without changing source spans."""
from collections import deque


def select_batches(records, hits):
    ranked = {eid: rank for rank, hit in reversed(list(enumerate(hits))) for eid in hit.evidence_ids}
    groups = {}
    oversized = False
    for record in records:
        if len(record.literal_text) > 18000:
            oversized = True
            continue
        groups.setdefault(record.document_version_id, []).append(record)
    queues = []
    for group in groups.values():
        # Pair a retrieval-selected passage with literal document identity context.
        anchor = min(group, key=lambda e: e.char_start)
        ordered = sorted(group, key=lambda e: (ranked.get(e.evidence_id, len(hits)), e.char_start))
        first = ordered[0]
        queue = [first] + ([anchor] if anchor != first else [])
        queue += [e for e in ordered if e not in queue]
        queues.append(deque(queue))
    batches, current, size = [], [], 0
    # Two spans per document per pass prevent a long early page starving later units.
    while any(queues):
        for queue in queues:
            pair = [queue.popleft() for _ in range(min(2, len(queue)))]
            if not pair:
                continue
            if current and (len(current)+len(pair) > 12 or size+sum(len(e.literal_text) for e in pair) > 18000):
                batches.append(current)
                current, size = [], 0
            for record in pair:
                if current and size+len(record.literal_text) > 18000:
                    batches.append(current)
                    current, size = [], 0
                current.append(record)
                size += len(record.literal_text)
    if current:
        batches.append(current)
    return batches, oversized
