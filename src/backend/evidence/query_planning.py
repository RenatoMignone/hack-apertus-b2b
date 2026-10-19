"""Bounded gap-driven query proposals; no retrieval or authority changes."""
from backend.contracts.services import ResearchQueries


def query_key(value):
    return " ".join(value.casefold().split())


async def revise_queries(tasks, interpretation, gaps, previous_queries, context):
    previous = {query_key(q) for q in previous_queries}

    def check(value):
        if any(not query.strip() or len(query) > 400 for query in value.variants):
            raise ValueError("queries must contain 1 to 400 characters")

    response = await tasks.run("revise_queries", "Propose at most FIVE complementary capability "
        "queries to close the supplied evidence gaps for the original operator needs. Preserve "
        "exclusions, uncertainty and original scientific wording. Do not repeat a previous query. "
        "Do not turn excluded technologies into positive requirements. Do not invent names or "
        "facts. Opaque claim UUIDs, infrastructure errors, unavailable services and generic "
        "coverage warnings are not research topics. Return [] when further searching cannot "
        "resolve the gaps or would repeat existing work. These are retrieval hints, not facts.",
        {"interpretation": interpretation.model_dump(mode="json"), "gaps": gaps,
         "previous_queries": previous_queries}, ResearchQueries, context, check=check)
    variants = {}
    for query in response.variants:
        key = query_key(query)
        if key not in previous:
            variants.setdefault(key, query.strip())
    return ResearchQueries(variants=list(variants.values()))
