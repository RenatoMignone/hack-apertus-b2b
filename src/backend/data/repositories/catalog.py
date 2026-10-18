from sqlalchemy import select, text

from backend.data import schema as tables
from backend.data.database import require_scope, transaction


class CatalogRepository:
    def __init__(self, engine):
        self.engine = engine

    def resolve_concepts(self, access, text_value, language, taxonomy_version_id):
        with transaction(self.engine, access) as connection:
            rows = connection.execute(select(tables.concepts, tables.labels.c.label).join(tables.labels).where(
                tables.concepts.c.taxonomy_version_id == taxonomy_version_id, tables.labels.c.language == language,
                tables.labels.c.label.ilike("%" + text_value.replace("%", "\\%").replace("_", "\\_") + "%", escape="\\"))
                .limit(30)).mappings().all()
            return {"candidates": [dict(row) for row in rows], "mapping_kind": "label_candidate",
                    "limitations": ["broad-term expansion requires reviewed vocabulary and reasoning adapter"]}

    def get_entity(self, access, entity_id, snapshot_id):
        with transaction(self.engine, access) as connection:
            entity = connection.execute(select(tables.entities).join(tables.snapshot_entities).where(
                tables.entities.c.entity_id == entity_id, tables.snapshot_entities.c.snapshot_id == snapshot_id,
                text("ops.can_access(corpus.entities.scope_id)"))).mappings().one()
            require_scope(connection, entity["scope_id"])
            claims = connection.execute(select(tables.claims).join(tables.snapshot_claims).where(
                tables.claims.c.subject_id == entity_id, tables.snapshot_claims.c.snapshot_id == snapshot_id,
                tables.claims.c.status == "accepted", text("ops.can_access(corpus.claims.scope_id)"))).mappings().all()
            return {"entity_id": entity_id, "entity_type": entity["entity_type"], "claims": [dict(claim) for claim in claims],
                    "limitations": ["display facts must be rendered from pinned supported claims"]}

    def entities_for_hits(self, access, snapshot_id, hits):
        with transaction(self.engine, access) as connection:
            scored = {}
            for hit in hits:
                rows = connection.execute(select(tables.entities.c.entity_id, tables.entities.c.entity_type)
                    .select_from(tables.entities.join(tables.snapshot_entities).join(tables.claims,
                        tables.claims.c.subject_id == tables.entities.c.entity_id).join(tables.snapshot_claims,
                        tables.snapshot_claims.c.claim_id == tables.claims.c.claim_id).join(tables.claim_evidence))
                    .where(tables.snapshot_entities.c.snapshot_id == snapshot_id,
                        tables.snapshot_claims.c.snapshot_id == snapshot_id, tables.claims.c.status == "accepted",
                        tables.claim_evidence.c.evidence_id.in_(hit.evidence_ids), tables.claim_evidence.c.relation == "supports",
                        text("ops.can_access(corpus.entities.scope_id)"), text("ops.can_access(corpus.claims.scope_id)")))
                for row in rows.mappings():
                    score = hit.reranker_score if hit.reranker_score is not None else hit.fusion_score
                    if row["entity_id"] not in scored or score > scored[row["entity_id"]]["relevance_score"]:
                        scored[row["entity_id"]] = {**dict(row), "relevance_score": score, "evidence_ids": hit.evidence_ids,
                            "support_status": "requires_need_fit_validation"}
            return sorted(scored.values(), key=lambda item: (-item["relevance_score"], str(item["entity_id"])))[:10]

    def search_cases(self, access, **kwargs):
        return {"status": "unavailable", "hits": [], "reason": "no reviewed historical-case dataset is published"}
