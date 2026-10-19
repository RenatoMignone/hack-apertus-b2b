"""Controlled LangChain tools and deterministic research merge, no SQL."""
from langchain_core.tools import StructuredTool

from backend.contracts.services import ResearchBundle, canonical_url


def research_tools(adapter, context):
    async def discover(query: str) -> list[str]:
        """Discover public source URLs for a capability-only research query."""
        return await adapter.discover(query, context)

    async def fetch(urls: list[str]) -> dict:
        """Fetch bounded public URLs as actual source text and provenance."""
        result = await adapter.fetch(urls, context)
        return result.model_dump(mode="json")

    return (StructuredTool.from_function(coroutine=discover), StructuredTool.from_function(coroutine=fetch))


def public_query(interpretation, variants=None):
    # Never send the whole case prompt/company summary to a discovery provider.
    terms = variants[:2] if variants is not None else [interpretation.activity_label, *interpretation.search_terms[:4]]
    company = (interpretation.company_name or "").casefold()
    return " ".join(term[:80] for term in terms if "@" not in term and "://" not in term
                    and (not company or company not in term.casefold()))[:400]


def merged(db, registered):
    curated = {canonical_url(e.url) for e in db.evidence if e.origin == "corpus"}
    evidence = {e.evidence_id: e for e in db.evidence}
    for record in registered.evidence:
        if record.origin == "web" and canonical_url(record.url) in curated:
            continue
        evidence[record.evidence_id] = record
    return ResearchBundle(hits=db.hits, evidence=list(evidence.values()), existing_entities=db.existing_entities,
                          limitations=list(dict.fromkeys([*db.limitations, *registered.limitations])))
