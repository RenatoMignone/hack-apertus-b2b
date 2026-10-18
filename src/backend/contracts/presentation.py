"""Deterministic wording for diagnostic codes at report/UI presentation boundaries."""
LIMITATIONS = {
    "scores_are_not_confidence": "Search relevance does not establish factual certainty.",
    "reranker_unavailable": "Results use the initial search ranking; additional relevance ranking was unavailable.",
    "graph_adjacency_is_not_expertise_or_availability": "An institutional connection does not establish expertise or willingness to collaborate.",
    "graph_expansion_budget_reached": "The search for related people and groups reached its limit.",
    "web_disabled_offline": "Offline mode: research used the pinned source collection only.",
    "web_unconfigured": "Public web research was not configured; coverage is limited to the source collection.",
    "web_unavailable": "Public web research was unavailable; coverage is limited to the source collection.",
    "web_fetch_unavailable": "Public pages could not be fetched.",
    "web_source_failure": "Some public sources could not be read.",
    "web_tool_budget_exhausted": "Public web research reached its configured limit.",
    "no_public_search_terms": "No suitable public search terms were available.",
    "crawl4ai_unavailable": "The public-page extraction service was unavailable.",
    "source_fetch_failed_or_policy_denied": "Some public pages were unavailable or excluded by the source policy.",
    "duplicate_research_source_deduplicated": "Duplicate public sources were consolidated.",
    "pinned_corpus_version_preferred_over_live_duplicate": "Existing source versions were retained for reproducible citations.",
}


def public_limitations(values):
    return list(dict.fromkeys(LIMITATIONS.get(value, value) for value in values))
