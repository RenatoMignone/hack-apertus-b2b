from sqlalchemy import or_, select

from backend.data import schema as tables
from backend.data.database import require_scope, transaction


class RelationshipExpansion:
    def __init__(self, engine, *, max_hops=1, max_entities=10, max_claims=30, max_evidence=60):
        if not 0 <= max_hops <= 2 or not 1 <= max_entities <= 10 or not 1 <= max_claims <= 60 or not 1 <= max_evidence <= 90:
            raise ValueError("graph expansion budgets out of bounds")
        self.engine = engine
        self.max_hops, self.max_entities, self.max_claims, self.max_evidence = max_hops, max_entities, max_claims, max_evidence

    def expand(self, access, plan, hits):
        seed_evidence = {key for hit in hits for key in hit.evidence_ids}
        support_scores = {}
        for hit in hits:
            score = hit.reranker_score if hit.reranker_score is not None else hit.fusion_score
            for key in hit.evidence_ids:
                support_scores[key] = max(support_scores.get(key, float("-inf")), score)
        if not seed_evidence:
            return {"entities": [], "evidence_ids": [], "limitations": []}
        with transaction(self.engine, access) as connection:
            pinned = set(connection.execute(select(tables.snapshot_entities.c.entity_id).where(
                tables.snapshot_entities.c.snapshot_id == plan.snapshot_id)).scalars())
            base = select(tables.claims).join(tables.snapshot_claims).where(tables.snapshot_claims.c.snapshot_id == plan.snapshot_id,
                tables.claims.c.status == "accepted").order_by(tables.claims.c.claim_id)
            seeds = connection.execute(base.join(tables.claim_evidence).where(tables.claim_evidence.c.evidence_id.in_(seed_evidence),
                tables.claim_evidence.c.relation == "supports", tables.claim_evidence.c.review_decision == "accepted").distinct().limit(
                    self.max_claims * 4 + 1)).mappings().all()
            seed_scores = {}
            for row in connection.execute(select(tables.claim_evidence).where(tables.claim_evidence.c.claim_id.in_([item["claim_id"] for item in seeds]),
                    tables.claim_evidence.c.evidence_id.in_(seed_evidence))).mappings():
                seed_scores[row["claim_id"]] = max(seed_scores.get(row["claim_id"], float("-inf")), support_scores[row["evidence_id"]])
            seeds = sorted(seeds, key=lambda row: (-seed_scores.get(row["claim_id"], 0), str(row["claim_id"])))
            frontier, entities, evidence, claims_seen = set(), {}, set(), set()
            limited = len(seeds) > self.max_claims * 4
            candidates = seeds
            for hop in range(self.max_hops + 1):
                next_frontier = set()
                for claim in candidates:
                    if claim["claim_id"] in claims_seen:
                        continue
                    endpoints = {claim["subject_id"]} | ({claim["object_entity_id"]} if claim["object_entity_id"] else set())
                    if not endpoints <= pinned:
                        continue
                    support = connection.execute(select(tables.spans, tables.versions.c.document_id, tables.versions.c.language,
                        tables.documents.c.source_id).select_from(tables.claim_evidence.join(tables.spans).join(tables.versions).join(tables.documents).join(
                            tables.snapshot_documents, tables.snapshot_documents.c.document_version_id == tables.versions.c.document_version_id))
                        .where(tables.claim_evidence.c.claim_id == claim["claim_id"], tables.claim_evidence.c.relation == "supports",
                            tables.claim_evidence.c.review_decision == "accepted", tables.snapshot_documents.c.snapshot_id == plan.snapshot_id,
                            tables.versions.c.status == "accepted")).mappings().all()
                    complete = set(connection.execute(select(tables.claim_evidence.c.evidence_id).where(
                        tables.claim_evidence.c.claim_id == claim["claim_id"], tables.claim_evidence.c.relation == "supports",
                        tables.claim_evidence.c.review_decision == "accepted")).scalars())
                    if not support or {row["evidence_id"] for row in support} != complete:
                        continue
                    eligible = True
                    for row in support:
                        require_scope(connection, row["scope_id"])
                        if row["document_id"] in plan.excluded_document_ids or (plan.languages and row["language"] not in plan.languages):
                            eligible = False
                        if plan.source_family_ids and not connection.execute(select(tables.family_memberships).where(
                                tables.family_memberships.c.source_id == row["source_id"],
                                tables.family_memberships.c.family_id.in_(plan.source_family_ids))).first():
                            eligible = False
                    if not eligible:
                        continue
                    if (len(entities.keys() | endpoints) > self.max_entities or len(claims_seen) >= self.max_claims
                            or len(evidence | complete) > self.max_evidence):
                        limited = True
                        continue
                    require_scope(connection, claim["scope_id"])
                    claims_seen.add(claim["claim_id"])
                    evidence.update(complete)
                    projection = {name: claim[name] for name in ("claim_id", "subject_id", "predicate", "object_entity_id", "typed_literal")}
                    projection.update(evidence_ids=sorted(complete, key=str), graph_hop=hop)
                    for entity_id in sorted(endpoints, key=str):
                        if entity_id not in entities:
                            entity = connection.execute(select(tables.entities).where(tables.entities.c.entity_id == entity_id)).mappings().one()
                            require_scope(connection, entity["scope_id"])
                            entities[entity_id] = {"entity_id": entity_id, "entity_type": entity["entity_type"],
                                "display_label": entity["display_label"], "claims": [],
                                "relevance_score": seed_scores.get(claim["claim_id"]),
                                "support_status": "requires_need_fit_validation"}
                            next_frontier.add(entity_id)
                        entities[entity_id]["claims"].append(projection)
                frontier |= next_frontier
                if not frontier or hop == self.max_hops:
                    break
                candidates = connection.execute(base.where(or_(tables.claims.c.subject_id.in_(frontier),
                    tables.claims.c.object_entity_id.in_(frontier))).limit(self.max_claims * 4 + 1)).mappings().all()
                limited |= len(candidates) > self.max_claims * 4
            return {"entities": sorted(entities.values(), key=lambda item: (item["relevance_score"] is None,
                -(item["relevance_score"] or 0), str(item["entity_id"]))), "evidence_ids": sorted(evidence, key=str),
                "limitations": ["graph_adjacency_is_not_expertise_or_availability"] + (["graph_expansion_budget_reached"] if limited else [])}
