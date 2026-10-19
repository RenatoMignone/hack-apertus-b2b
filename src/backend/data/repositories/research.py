"""Case-local discovery records and source preference; fetching is an adapter boundary."""
from uuid import uuid4

from sqlalchemy import insert, select, update

from backend.contracts.pipeline import FetchedSource, canonical_url
from backend.data import schema as t
from backend.data.database import require_scope, transaction
from backend.data.repositories.cases import CaseRepository


class ResearchRepository:
    def __init__(self, engine):
        self.engine = engine
        self.cases = CaseRepository(engine)

    def start(self, access, run_id, query, *, mode="connected"):
        if mode not in {"connected", "offline"} or not query.strip():
            raise ValueError("research requires mode and public query")
        with transaction(self.engine, access) as connection:
            self.cases._run(connection, access, run_id)
            key = uuid4()
            connection.execute(insert(t.web_research).values(research_id=key, run_id=run_id, query=query, mode=mode,
                status="unavailable" if mode == "offline" else "pending",
                diagnostics={"reason": "offline"} if mode == "offline" else {}))
            return key

    def finish(self, access, research_id, *, status, diagnostics=None):
        if status not in {"completed", "unavailable", "failed"}:
            raise ValueError("invalid research outcome")
        with transaction(self.engine, access) as connection:
            research = connection.execute(select(t.web_research).where(
                t.web_research.c.research_id == research_id).with_for_update()).mappings().one()
            self.cases._run(connection, access, research["run_id"])
            if research["status"] != "pending":
                raise ValueError("research already finalized")
            connection.execute(update(t.web_research).where(t.web_research.c.research_id == research_id)
                .values(status=status, diagnostics=diagnostics or {}))

    def corpus_duplicate(self, access, run_id, url):
        """Check every visible document/alias in the pinned snapshot, not retrieval hits."""
        target = canonical_url(url)
        with transaction(self.engine, access) as connection:
            run = self.cases._run(connection, access, run_id, lock=False)
            return self._corpus_duplicate(connection, run, target)

    def _corpus_duplicate(self, connection, run, target):
        rows = connection.execute(select(t.documents.c.document_id, t.documents.c.canonical_url,
            t.versions.c.document_version_id, t.versions.c.scope_id,
            t.aliases.c.url.label('alias_url')).select_from(t.documents.join(t.versions).join(t.snapshot_documents)
            .outerjoin(t.aliases, t.aliases.c.document_id == t.documents.c.document_id)).where(
            t.snapshot_documents.c.snapshot_id == run["snapshot_id"])
            .order_by(t.documents.c.document_id, t.versions.c.document_version_id, t.aliases.c.url)).mappings().all()
        for row in rows:
            if any(canonical_url(value) == target for value in [row["canonical_url"], row['alias_url']] if value):
                require_scope(connection, row["scope_id"])
                return row["document_version_id"]
        return None

    def record_source(self, access, research_id, source: FetchedSource, *, version_id=None):
        with transaction(self.engine, access) as connection:
            research = connection.execute(select(t.web_research).where(
                t.web_research.c.research_id == research_id).with_for_update()).mappings().one()
            run = self.cases._run(connection, access, research["run_id"])
            if research["mode"] != "connected" or research["status"] != "pending":
                raise ValueError("web tools unavailable or research closed")
            duplicate = (self._corpus_duplicate(connection, run, source.canonical_url)
                         or self._corpus_duplicate(connection, run, canonical_url(source.url)))
            if duplicate is None:
                version = connection.execute(select(t.versions, t.scopes.c.case_id).join(t.scopes).where(
                    t.versions.c.document_version_id == version_id)).mappings().one()
                require_scope(connection, version["scope_id"], write=True)
                document_url = connection.execute(select(t.documents.c.canonical_url).where(
                    t.documents.c.document_id == version["document_id"])).scalar_one()
                if (version["case_id"] != run["case_id"] or version["body_hash"] != source.content_hash
                        or canonical_url(document_url) != source.canonical_url or version["status"] != "accepted"):
                    raise PermissionError("new web source must resolve to matching own case content")
            key = uuid4()
            connection.execute(insert(t.web_sources).values(discovery_id=key, research_id=research_id,
                canonical_url=source.canonical_url, document_version_id=None if duplicate else version_id,
                duplicate_version_id=duplicate, payload=source.model_dump(mode="json", exclude={"content"})))
            return {"discovery_id": key, "origin": "corpus" if duplicate else "web",
                    "version_id": duplicate or version_id, "review_status": "curated" if duplicate else "unreviewed"}
