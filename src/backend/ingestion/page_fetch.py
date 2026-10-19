"""Bounded concurrent page I/O; policy enforcement stays in SafeHTTP."""
import asyncio
from datetime import datetime, timezone

from backend.contracts.pipeline import canonical_url
from backend.contracts.services import ServiceUnavailable
from backend.observability.logging import activity


async def fetch_pages(fetcher, urls, context, charge):
    slots = asyncio.Semaphore(3)

    async def fetch(index, url):
        async with slots:
            charge(context)  # charge actual admitted attempts, including failures
            try:
                remaining = (context.deadline_at - datetime.now(timezone.utc)).total_seconds()
                async with activity("web.page", run_id=context.run_id, attempt=index+1,
                                    count=len(urls)), asyncio.timeout(max(0.001, remaining)):
                    return await asyncio.to_thread(fetcher.fetch, canonical_url(url)), None
            except ServiceUnavailable:
                return None, "crawl4ai_unavailable"
            except (ValueError, OSError, TimeoutError, UnicodeError):
                return None, "source_fetch_failed_or_policy_denied"

    tasks = [asyncio.create_task(fetch(index, url)) for index, url in enumerate(urls)]
    try:
        results = await asyncio.gather(*tasks)
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
    # Completion timing must not reorder discovery relevance or provenance.
    return ([source for source, _ in results if source is not None],
            list(dict.fromkeys(error for _, error in results if error)))
