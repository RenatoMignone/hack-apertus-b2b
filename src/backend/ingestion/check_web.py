"""Opt-in public discovery/fetch probe; no DB, models or corpus writes."""
import argparse
import asyncio
from datetime import datetime, timedelta, timezone
import json
from types import SimpleNamespace
from uuid import uuid4

from backend.application.factories import web
from backend.config.runtime import RuntimeSettings
from backend.contracts.services import BudgetExceeded, ServiceUnavailable
from backend.data.cli import load_environment


async def probe(settings, query=None, url=None):
    if settings.mode != "connected":
        print(json.dumps({"status": "unavailable", "reason": "web_disabled_offline"}))
        return 1
    tools = web(settings=settings, engine=None, artifacts=None)
    context = SimpleNamespace(mode=settings.mode, access=SimpleNamespace(principal_id=uuid4()),
        run_id=uuid4(), request_id=str(uuid4()), max_tool_calls=6,
        deadline_at=datetime.now(timezone.utc) + timedelta(seconds=60))
    failed, urls = False, []
    if query:
        try:
            urls = await tools.discover(query, context)
            print(json.dumps({"stage": "discovery", "status": "completed", "urls": urls}))
        except (ServiceUnavailable, BudgetExceeded):
            failed = True
            print(json.dumps({"stage": "discovery", "status": "unavailable"}))
    if url or urls:
        result = await tools.fetch([url] if url else urls[:3], context)
        print(json.dumps({"stage": "fetch", "status": result.status, "limitations": result.limitations,
            "sources": [{"title": s.title, "url": s.canonical_url, "characters": len(s.content),
                         "content_hash": s.content_hash} for s in result.sources]}))
        failed |= result.status != "completed"
    return int(failed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", required=True)
    parser.add_argument("--query", help="Only public capability terms; never a confidential case prompt")
    parser.add_argument("--url", help="Optional explicit public page, also probes fetch when discovery fails")
    args = parser.parse_args()
    if not (args.query or args.url):
        parser.error("supply --query and/or --url")
    load_environment(args.env_file)
    return asyncio.run(probe(RuntimeSettings.from_env(), args.query, args.url))


if __name__ == "__main__":
    raise SystemExit(main())
