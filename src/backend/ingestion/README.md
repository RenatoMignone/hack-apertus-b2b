# Acquisition integration

Bulk ingestion remains separate from this case-data change. Future case-time
fetching uses self-hosted Crawl4AI through LangChain tools and LangGraph, with a
separate URL discovery provider. [Web research](../../../docs/data/WEB_RESEARCH.md)
owns tool limits, source flags and deduplication. `data/repositories/research.py`
implements persistence and corpus URL preference, not a scraper/search service.
Use faithful normalized text, raw artifacts and exact spans via existing corpus
ports. Confidential company documents remain outside allowed intake.

## Parallel feature routing

[Module handoffs](../../../docs/plans/MODULE_HANDOFFS.md) lists this module's
focused read path, outputs and acceptance checks. [Active questions](../../../docs/project/OPEN_QUESTIONS.md)
own unresolved inputs. Implement scoped behavior against agreed contracts and
fixtures; coordinate shared schema/config changes. Leave `src/frontend/` untouched.
