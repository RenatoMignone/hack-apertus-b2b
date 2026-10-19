import asyncio
from datetime import datetime, timezone
from functools import partial
from uuid import uuid4

from sqlalchemy import insert, or_, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import DBAPIError, NoResultFound

from backend.contracts.data import Span, configuration_hash, content_hash
from backend.contracts.pipeline import SupportedClaim, canonical_url
from backend.contracts.services import (BudgetExceeded, EvidenceRecord, EvidenceRejected, PersistedClaims,
    RegisteredResearch, ResearchBundle, ServiceUnavailable, StaleRevision)
from backend.data import schema as tables
from backend.data.database import require_scope, transaction
from backend.data.repositories.cases import CaseRepository
from backend.data.repositories.corpus import CorpusRepository
from backend.data.repositories.research import ResearchRepository
from backend.data.retrieval.graph import RelationshipExpansion


class BackboneRepository:
    def __init__(self, engine, artifacts, *, observations=None):
        self.engine, self.artifacts = engine, artifacts
        self.cases = CaseRepository(engine)
        self.corpus = CorpusRepository(engine, artifacts)
        self.research = ResearchRepository(engine)
        self.observations = observations if observations is not None else {}

    def authorize(self, connection, context, *, historical=False):
        if datetime.now(timezone.utc) >= context.deadline_at:
            raise BudgetExceeded()
        try:
            if historical:
                self.cases._case(connection, context.access, context.case_id)
                run = connection.execute(select(tables.runs).where(tables.runs.c.run_id == context.run_id)).mappings().one()
            else:
                run = self.cases._run(connection, context.access, context.run_id)
        except ValueError as error:
            raise StaleRevision() from error
        if (run["case_id"], run["input_id"], run["snapshot_id"]) != (context.case_id, context.input_id, context.snapshot_id):
            raise EvidenceRejected()
        pin = connection.execute(select(tables.snapshots, tables.embedding_configs.c.config_hash).select_from(
            tables.snapshots.join(tables.builds).join(tables.embedding_configs)).where(
                tables.snapshots.c.snapshot_id == context.snapshot_id,
                tables.snapshots.c.status.in_(["published", "live"]))).mappings().one()
        if pin["status"] == "live" and pin["manifest"].get("runtime_case_id") != str(context.case_id):
            raise EvidenceRejected()
        if (pin["namespace"] != context.access.namespace or pin["profile_id"] != context.profile_id
                or pin["taxonomy_version_id"] != context.taxonomy_version_id or pin["build_id"] != context.build_id
                or pin["config_hash"] != context.embedding_config_hash):
            raise EvidenceRejected()
        return run

    def taxonomy(self, context):
        with transaction(self.engine, context.access) as connection:
            self.authorize(connection, context)
            version = connection.execute(select(tables.taxonomies).where(
                tables.taxonomies.c.taxonomy_version_id == context.taxonomy_version_id,
                tables.taxonomies.c.status == "reviewed")).mappings().one()
            profile = connection.execute(select(tables.profiles).where(tables.profiles.c.profile_id == context.profile_id)).mappings().one()
            concepts = connection.execute(select(tables.concepts).where(
                tables.concepts.c.taxonomy_version_id == context.taxonomy_version_id)).mappings().all()
            ids = [row["concept_id"] for row in concepts]
            labels = connection.execute(select(tables.labels).where(tables.labels.c.concept_id.in_(ids))).mappings().all()
            relations = connection.execute(select(tables.relations).where(tables.relations.c.subject_id.in_(ids),
                tables.relations.c.object_id.in_(ids))).mappings().all()
            return {"version": dict(version), "profile": dict(profile), "concepts": [dict(row) for row in concepts],
                "labels": [dict(row) for row in labels], "relations": [dict(row) for row in relations],
                "limitations": ["related_and_broader_terms_are_discovery_hints_not_equivalence"]}

    def _evidence(self, connection, context, evidence_ids):
        rows = connection.execute(select(tables.spans, tables.versions.c.title, tables.versions.c.language, tables.versions.c.body_hash,
            tables.versions.c.body_text, tables.versions.c.source_date, tables.versions.c.raw_artifact_id,
            tables.documents.c.canonical_url, tables.scopes.c.case_id).select_from(tables.spans.join(tables.versions).join(tables.documents).join(
                tables.scopes, tables.scopes.c.scope_id == tables.spans.c.scope_id)).where(tables.spans.c.evidence_id.in_(set(evidence_ids)),
                tables.versions.c.status == "accepted")).mappings().all()
        if len(rows) != len(set(evidence_ids)):
            raise EvidenceRejected()
        output = {}
        for row in rows:
            require_scope(connection, row["scope_id"])
            pinned = connection.execute(select(tables.snapshot_documents).where(
                tables.snapshot_documents.c.snapshot_id == context.snapshot_id,
                tables.snapshot_documents.c.document_version_id == row["document_version_id"])).first()
            if not pinned and row["case_id"] != context.case_id:
                raise EvidenceRejected()
            if (content_hash(row["body_text"].encode()) != row["body_hash"]
                    or row["body_text"][row["char_start"]:row["char_end"]] != row["literal_text"]):
                raise EvidenceRejected()
            output[row["evidence_id"]] = dict(row)
        return output

    def _project(self, connection, context, row):
        origin = "corpus" if row["case_id"] is None else "web"
        original_record = None
        if row["case_id"]:
            mirrors = connection.execute(select(tables.derivations.c.inputs).where(tables.derivations.c.scope_id == row["scope_id"],
                tables.derivations.c.inputs["kind"].astext == "case_mirror",
                tables.derivations.c.inputs["local_version_id"].astext == str(row["document_version_id"]))).scalars().all()
            for mirror in mirrors:
                if mirror["snapshot_id"] != str(context.snapshot_id) or mirror.get("local_evidence_id") != str(row["evidence_id"]):
                    continue
                from uuid import UUID
                original = self._evidence(connection, context, [UUID(mirror["original_evidence_id"])])
                source = next(iter(original.values()))
                if (mirror["snapshot_id"] == str(context.snapshot_id) and source["body_hash"] == row["body_hash"]
                        and source["literal_text"] == row["literal_text"]):
                    origin = "corpus"
                    original_record = self._project(connection, context, source)
                    break
        fetched_at = connection.execute(select(tables.fetches.c.created_at).where(
            tables.fetches.c.document_id == connection.execute(select(tables.versions.c.document_id).where(
                tables.versions.c.document_version_id == row["document_version_id"])).scalar_one(),
            tables.fetches.c.raw_artifact_id == row["raw_artifact_id"]).order_by(tables.fetches.c.created_at).limit(1)).scalar_one()
        discovery = connection.execute(select(tables.web_sources.c.payload).join(tables.web_research).where(
            tables.web_sources.c.document_version_id == row["document_version_id"], tables.web_research.c.run_id == context.run_id)).scalars().first()
        if discovery:
            fetched_at = datetime.fromisoformat(discovery["fetched_at"])
        if original_record:
            fetched_at = original_record.fetched_at
        return EvidenceRecord(**{name: row[name] for name in ("evidence_id", "document_version_id", "scope_id", "title",
            "language", "body_hash", "char_start", "char_end", "literal_text", "heading_path", "page")},
            url=row["canonical_url"], fetched_at=fetched_at, published_at=row["source_date"], origin=origin,
            review_status="curated" if origin == "corpus" else "unreviewed")

    def read_evidence(self, evidence_ids, context):
        if len(evidence_ids) > 100:
            raise BudgetExceeded()
        with transaction(self.engine, context.access) as connection:
            self.authorize(connection, context, historical=True)
            rows = self._evidence(connection, context, evidence_ids)
            return [self._project(connection, context, rows[key]) for key in dict.fromkeys(evidence_ids)]

    def heading_evidence(self, version_ids, context):
        """Bounded identity/neighbor expansion; metadata alone is never evidence."""
        import re
        from sqlalchemy import func
        with transaction(self.engine, context.access) as connection:
            self.authorize(connection, context)
            ranked = select(tables.spans.c.evidence_id, tables.spans.c.document_version_id,
                tables.spans.c.char_start, tables.spans.c.literal_text, tables.versions.c.title,
                func.row_number().over(partition_by=tables.spans.c.document_version_id,
                    order_by=(tables.spans.c.char_start, tables.spans.c.evidence_id)).label("ordinal")).select_from(
                tables.spans.join(tables.versions).join(tables.snapshot_documents,
                    tables.snapshot_documents.c.document_version_id == tables.spans.c.document_version_id)).where(
                tables.snapshot_documents.c.snapshot_id == context.snapshot_id,
                tables.spans.c.document_version_id.in_(list(dict.fromkeys(version_ids))[:30])).subquery()
            rows = connection.execute(select(ranked).where(ranked.c.ordinal <= 256).order_by(
                ranked.c.document_version_id, ranked.c.char_start, ranked.c.evidence_id)).mappings().all()
            groups = {}
            for row in rows:
                groups.setdefault(row["document_version_id"], []).append(row)
            ids = []
            for version_id in dict.fromkeys(version_ids):
                spans = groups.get(version_id, [])
                if not spans:
                    continue
                ids.append(spans[0]["evidence_id"])
                # Components only select existing literal spans. No new source
                # facts or title-only assertions are generated by this lookup.
                parts = [part.rsplit(":", 1)[-1].strip() for part in re.split(r"\s[-–|]\s", spans[0]["title"])]
                for part in [p for p in parts if len(p.split()) >= 2][-2:]:
                    index = next((i for i, row in enumerate(spans) if part.casefold() in row["literal_text"].casefold()), None)
                    if index is not None:
                        ids.extend(row["evidence_id"] for row in spans[index:index+3] if row["evidence_id"] not in ids)
            return ids

    def subject_mentions(self, version_ids, context):
        if len(version_ids) > 30:
            raise BudgetExceeded()
        with transaction(self.engine, context.access) as connection:
            self.authorize(connection, context)
            eligible = set(connection.execute(select(tables.snapshot_documents.c.document_version_id).where(
                tables.snapshot_documents.c.snapshot_id == context.snapshot_id,
                tables.snapshot_documents.c.document_version_id.in_(version_ids))).scalars())
            if not set(version_ids) <= eligible:
                raise EvidenceRejected()
            mentions = connection.execute(select(tables.derivations).where(tables.derivations.c.inputs["kind"].astext == "specific_subject",
                tables.derivations.c.inputs["version_id"].astext.in_(list(map(str, version_ids))),
                tables.derivations.c.inputs["taxonomy_version_id"].astext == str(context.taxonomy_version_id))).mappings().all()
            output = []
            for mention in mentions:
                require_scope(connection, mention["scope_id"])
                from uuid import UUID
                payload = mention["inputs"]
                support = [UUID(payload["evidence_id"]), *[UUID(item["evidence_id"]) for item in payload["attributes"]]]
                self._evidence(connection, context, support)
                output.append({"subject_id": mention["derivation_id"], **payload, "status": mention["status"]})
            return output

    def _case_scope(self, connection, context):
        rows = connection.execute(select(tables.scopes.c.scope_id).where(tables.scopes.c.case_id == context.case_id,
            tables.scopes.c.kind == "case", tables.scopes.c.revoked.is_(False))).scalars().all()
        if len(rows) != 1:
            raise EvidenceRejected()
        require_scope(connection, rows[0], write=True)
        return rows[0]

    def _source(self, connection, scope, url, registry_ref):
        from urllib.parse import urlsplit
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        existing = connection.execute(select(tables.sources.c.source_id).where(tables.sources.c.scope_id == scope,
            tables.sources.c.canonical_origin == origin, tables.sources.c.registry_ref == registry_ref)).scalar_one_or_none()
        if existing:
            return existing
        source_id = uuid4()
        connection.execute(insert(tables.sources).values(source_id=source_id, scope_id=scope,
            canonical_origin=origin, registry_ref=registry_ref))
        return source_id

    def register_research(self, result, context):
        with transaction(self.engine, context.access) as connection:
            self.authorize(connection, context)
        if context.mode == "offline" and result.sources:
            raise EvidenceRejected()
        if not result.sources:
            return RegisteredResearch(limitations=result.limitations)
        if len(result.sources) > 10:
            raise BudgetExceeded()
        evidence_ids, limitations = [], list(result.limitations)
        research_id = self.research.start(context.access, context.run_id, "bounded public-source registration")
        seen_urls = set()
        try:
            for source in result.sources:
                if source.canonical_url in seen_urls:
                    limitations.append("duplicate_research_source_deduplicated")
                    continue
                seen_urls.add(source.canonical_url)
                duplicate = (self.research.corpus_duplicate(context.access, context.run_id, source.canonical_url)
                    or self.research.corpus_duplicate(context.access, context.run_id, source.url))
                version_id = duplicate
                if duplicate:
                    limitations.append("pinned_corpus_version_preferred_over_live_duplicate")
                else:
                    with transaction(self.engine, context.access) as connection:
                        self.authorize(connection, context)
                        scope = self._case_scope(connection, context)
                        source_id = self._source(connection, scope, source.canonical_url, "case-web-v1")
                    observation = self.observations.get((source.canonical_url, source.content_hash))
                    version_id = self.corpus.stage_document(context.access, scope_id=scope, source_id=source_id,
                        url=source.canonical_url, title=source.title, language="und", body=source.content,
                        raw=observation.raw if observation else source.content.encode(),
                        raw_mime=observation.mime if observation else "text/plain; charset=utf-8",
                        spans=[Span(char_start=0, char_end=len(source.content), text=source.content)],
                        parser_hash=configuration_hash({"parser": "case-public-text-v1"}), source_date=source.published_at,
                        http_status=observation.status if observation else None)
                self.research.record_source(context.access, research_id, source, version_id=None if duplicate else version_id)
                with transaction(self.engine, context.access) as connection:
                    evidence_ids.extend(connection.execute(select(tables.spans.c.evidence_id).where(
                        tables.spans.c.document_version_id == version_id)).scalars())
            self.research.finish(context.access, research_id, status="completed", diagnostics={"count": len(result.sources)})
        except Exception:
            self.research.finish(context.access, research_id, status="failed", diagnostics={"reason": "registration_failed"})
            raise
        return RegisteredResearch(evidence=self.read_evidence(evidence_ids, context), limitations=list(dict.fromkeys(limitations)))

    def _mirror(self, connection, context, scope, row):
        if row["scope_id"] == scope:
            return row["evidence_id"]
        document_id = connection.execute(select(tables.documents.c.document_id).where(tables.documents.c.scope_id == scope,
            tables.documents.c.canonical_url == row["canonical_url"])).scalar_one_or_none()
        if not document_id:
            source_id = self._source(connection, scope, row["canonical_url"], "case-mirror-v1")
            document_id = uuid4()
            connection.execute(insert(tables.documents).values(document_id=document_id, source_id=source_id,
                scope_id=scope, canonical_url=row["canonical_url"]))
        original = connection.execute(select(tables.versions).where(
            tables.versions.c.document_version_id == row["document_version_id"])).mappings().one()
        parser_hash = configuration_hash({"mirror": str(original["document_version_id"]), "version": 1})
        version_id = connection.execute(select(tables.versions.c.document_version_id).where(tables.versions.c.document_id == document_id,
            tables.versions.c.parser_hash == parser_hash, tables.versions.c.body_hash == original["body_hash"])).scalar_one_or_none()
        if not version_id:
            version_id = uuid4()
            connection.execute(insert(tables.versions).values(document_version_id=version_id, document_id=document_id, scope_id=scope,
                **{name: original[name] for name in ("raw_artifact_id", "body_artifact_id", "body_hash", "body_text", "language", "title", "source_date")},
                parser_hash=parser_hash))
            connection.execute(insert(tables.fetches).values(fetch_id=uuid4(), document_id=document_id,
                requested_url=row["canonical_url"], final_url=row["canonical_url"], raw_artifact_id=original["raw_artifact_id"],
                headers={"kind": "authorized_artifact_mirror_not_network_fetch"}))
        evidence_id = connection.execute(select(tables.spans.c.evidence_id).where(tables.spans.c.document_version_id == version_id,
            tables.spans.c.char_start == row["char_start"], tables.spans.c.char_end == row["char_end"])).scalar_one_or_none()
        if not evidence_id:
            evidence_id = uuid4()
            connection.execute(insert(tables.spans).values(evidence_id=evidence_id, document_version_id=version_id, scope_id=scope,
                **{name: row[name] for name in ("char_start", "char_end", "literal_text", "heading_path", "page")}, extraction_method="authorized-mirror"))
            lineage = {"kind": "case_mirror", "snapshot_id": str(context.snapshot_id), "original_version_id": str(row["document_version_id"]),
                "original_evidence_id": str(row["evidence_id"]), "local_version_id": str(version_id), "local_evidence_id": str(evidence_id)}
            connection.execute(insert(tables.derivations).values(derivation_id=uuid4(), scope_id=scope, inputs=lineage,
                configuration_hash=configuration_hash({"mirror": 1}), output_hash=configuration_hash(lineage), status="accepted"))
        return evidence_id

    def persist_extraction(self, batch, context):
        if len(batch.entities) > 30 or len(batch.claims) > 60:
            raise BudgetExceeded()
        with transaction(self.engine, context.access) as connection:
            self.authorize(connection, context)
            if not batch.entities and not batch.claims:
                return PersistedClaims()
            scope = self._case_scope(connection, context)
            connection.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:case,0))"), {"case": str(context.case_id)})
            evidence_ids = {key for item in [*batch.entities, *batch.claims] for key in item.evidence_ids}
            rows = self._evidence(connection, context, evidence_ids)
            entities, original_entities = {}, {}
            for candidate in batch.entities:
                if not any(candidate.display_label.casefold() in rows[key]["literal_text"].casefold() for key in candidate.evidence_ids):
                    raise EvidenceRejected()
                existing = None
                if candidate.existing_entity_id:
                    existing = connection.execute(select(tables.entities).where(
                        tables.entities.c.entity_id == candidate.existing_entity_id)).mappings().one()
                    require_scope(connection, existing["scope_id"])
                    pinned = connection.execute(select(tables.snapshot_entities).where(tables.snapshot_entities.c.snapshot_id == context.snapshot_id,
                        tables.snapshot_entities.c.entity_id == candidate.existing_entity_id)).first()
                    if ((not pinned and existing["scope_id"] != scope) or existing["entity_type"] != candidate.entity_type
                            or existing["display_label"] != candidate.display_label):
                        raise EvidenceRejected()
                    original_entities[candidate.key] = existing["entity_id"]
                identity = {"kind": "case_entity", "label": candidate.display_label, "type": candidate.entity_type,
                    "original_entity_id": str(candidate.existing_entity_id) if existing else None,
                    "evidence_ids": sorted(map(str, candidate.evidence_ids))}
                digest = configuration_hash(identity)
                previous = connection.execute(select(tables.derivations.c.inputs).where(tables.derivations.c.scope_id == scope,
                    tables.derivations.c.output_hash == digest)).scalars().first()
                if previous:
                    from uuid import UUID
                    entities[candidate.key] = UUID(previous["entity_id"])
                elif existing and existing["scope_id"] == scope:
                    entities[candidate.key] = existing["entity_id"]
                else:
                    entity_id = uuid4()
                    connection.execute(insert(tables.entities).values(entity_id=entity_id, scope_id=scope,
                        entity_type=candidate.entity_type, display_label=candidate.display_label, status="needs_review"))
                    connection.execute(insert(tables.derivations).values(derivation_id=uuid4(), scope_id=scope,
                        inputs={**identity, "entity_id": str(entity_id)}, configuration_hash=configuration_hash({"case_entity": 1}),
                        output_hash=digest, status="needs_review"))
                    entities[candidate.key] = entity_id
            persisted = []
            for candidate in batch.claims:
                shared = connection.execute(select(tables.claims).join(tables.snapshot_claims).where(
                    tables.snapshot_claims.c.snapshot_id == context.snapshot_id, tables.claims.c.status == "accepted",
                    tables.claims.c.subject_id == original_entities.get(candidate.subject_key), tables.claims.c.predicate == candidate.predicate,
                    tables.claims.c.typed_literal == candidate.typed_literal if candidate.typed_literal is not None else
                    tables.claims.c.object_entity_id == original_entities.get(candidate.object_key))).mappings().all()
                reused = None
                for claim in shared:
                    support = set(connection.execute(select(tables.claim_evidence.c.evidence_id).where(tables.claim_evidence.c.claim_id == claim["claim_id"],
                        tables.claim_evidence.c.relation == "supports", tables.claim_evidence.c.review_decision == "accepted")).scalars())
                    if support == set(candidate.evidence_ids) and candidate.typed_literal and candidate.statement == candidate.typed_literal["value"]:
                        reused = claim["claim_id"]
                        break
                if reused:
                    persisted.append(SupportedClaim(claim_id=reused, text=candidate.statement, evidence_ids=candidate.evidence_ids, kind=candidate.kind))
                    continue
                mapped = [self._mirror(connection, context, scope, rows[key]) for key in dict.fromkeys(candidate.evidence_ids)]
                proposal = {"kind": "case_claim", "run_id": str(context.run_id), "statement": candidate.statement,
                    "subject": str(entities[candidate.subject_key]), "predicate": candidate.predicate,
                    "object": str(entities[candidate.object_key]) if candidate.object_key else None,
                    "literal": candidate.typed_literal, "evidence_ids": sorted(map(str, mapped)), "claim_kind": candidate.kind}
                digest = configuration_hash(proposal)
                previous = connection.execute(select(tables.claims.c.claim_id).join(tables.derivations).where(tables.claims.c.scope_id == scope,
                    tables.derivations.c.output_hash == digest)).scalar_one_or_none()
                claim_id, derivation_id = previous or uuid4(), uuid4()
                if not previous:
                    connection.execute(insert(tables.derivations).values(derivation_id=derivation_id, scope_id=scope, inputs=proposal,
                        configuration_hash=configuration_hash({"case_extraction": 1}), output_hash=digest, status="needs_review"))
                    connection.execute(insert(tables.claims).values(claim_id=claim_id, scope_id=scope, subject_id=entities[candidate.subject_key],
                        predicate=candidate.predicate, object_entity_id=entities[candidate.object_key] if candidate.object_key else None,
                        typed_literal=candidate.typed_literal, derivation_id=derivation_id, status="needs_review"))
                    for evidence_id in mapped:
                        connection.execute(insert(tables.claim_evidence).values(claim_id=claim_id, evidence_id=evidence_id,
                            relation="supports", review_decision="needs_review"))
                persisted.append(SupportedClaim(claim_id=claim_id, text=candidate.statement, evidence_ids=mapped, kind=candidate.kind))
            return PersistedClaims(claims=persisted, entity_ids=entities)


class PostgresBackbone:
    def __init__(self, repository, search, *, graph=None):
        self.repository, self.search = repository, search
        self.graph = graph or RelationshipExpansion(repository.engine)

    async def _call(self, function, *args):
        try:
            context = next((value for value in args if hasattr(value, "deadline_at")), None)
            if context:
                remaining = (context.deadline_at - datetime.now(timezone.utc)).total_seconds()
                if remaining <= 0:
                    raise BudgetExceeded()
                async with asyncio.timeout(remaining):
                    return await asyncio.to_thread(partial(function, *args))
            return await asyncio.to_thread(partial(function, *args))
        except TimeoutError as error:
            raise BudgetExceeded() from error
        except (PermissionError, NoResultFound) as error:
            raise EvidenceRejected() from error
        except ValueError as error:
            raise EvidenceRejected() from error
        except DBAPIError as error:
            raise ServiceUnavailable() from error

    async def taxonomy(self, context):
        return await self._call(self.repository.taxonomy, context)

    async def retrieve(self, plan, context):
        if self.search.embedder is None:
            raise ServiceUnavailable()
        pins = ("snapshot_id", "profile_id", "taxonomy_version_id", "build_id", "embedding_config_hash")
        if any(getattr(plan, name) != getattr(context, name) for name in pins) or plan.round_number > context.max_research_rounds:
            raise EvidenceRejected()
        if any(value is not None and value != expected for value, expected in
               ((plan.run_id, context.run_id), (plan.case_id, context.case_id), (plan.input_revision_id, context.input_id))):
            raise EvidenceRejected()
        await self._call(self.repository.read_evidence, [], context)
        result = await self._call(self.search.search, context.access, plan)
        expansion = await self._call(self.graph.expand, context.access, plan, result.hits)
        evidence_ids = list(dict.fromkeys([key for hit in result.hits for key in hit.evidence_ids] + expansion["evidence_ids"]))
        headers = await self._call(self.repository.heading_evidence,
            [hit.document_version_id for hit in result.hits], context)
        all_evidence_ids = list(dict.fromkeys([*evidence_ids, *headers]))
        if len(all_evidence_ids) > 100:
            result = result.model_copy(update={"limitations": [*result.limitations, "source_context_expansion_budget_reached"]})
        evidence_ids = all_evidence_ids[:100]
        return ResearchBundle(hits=result.hits, evidence=await self.read_evidence(evidence_ids, context),
            existing_entities=expansion["entities"], limitations=list(dict.fromkeys(result.limitations + expansion["limitations"])))

    async def register_research(self, result, context):
        return await self._call(self.repository.register_research, result, context)

    async def persist_extraction(self, batch, context):
        return await self._call(self.repository.persist_extraction, batch, context)

    async def read_evidence(self, evidence_ids, context):
        return await self._call(self.repository.read_evidence, evidence_ids, context)


def create_backbone(engine, artifacts, embedder, *, reranker=None, observations=None):
    from backend.data.retrieval.hybrid import HybridSearch
    return PostgresBackbone(BackboneRepository(engine, artifacts, observations=observations),
        HybridSearch(engine, embedder, reranker))
