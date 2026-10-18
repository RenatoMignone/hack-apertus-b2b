from dataclasses import dataclass
from statistics import mean


@dataclass(frozen=True)
class ReviewedQuery:
    query: str
    relevant_entity_ids: frozenset
    reviewer: str
    intent: str


def recall_at_10(labels, ranked_entities):
    if not labels or any(not item.reviewer.strip() or not item.relevant_entity_ids for item in labels):
        raise ValueError("nonempty independently reviewed expert/unit labels required")
    if len(labels) != len(ranked_entities):
        raise ValueError("one ranking per reviewed query required")
    scores = []
    for label, ranked in zip(labels, ranked_entities, strict=True):
        unique = list(dict.fromkeys(ranked))[:10]
        scores.append(len(set(unique) & label.relevant_entity_ids) / len(label.relevant_entity_ids))
    intents = {}
    for label, score in zip(labels, scores, strict=True):
        intents.setdefault(label.intent, []).append(score)
    return {"metric": "intent-balanced-entity-Recall@10", "score": mean(mean(values) for values in intents.values()),
        "per_query": scores, "queries": len(labels), "intents": len(intents), "unit": "unique_reviewed_expert_or_unit"}
