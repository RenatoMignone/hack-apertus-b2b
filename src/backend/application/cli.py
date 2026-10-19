"""Explicit API/worker/checkpoint commands, independent from the data maintainer CLI."""
import argparse
import asyncio
import sys

from backend.application.bootstrap import Registry
from backend.application.worker import Worker
from backend.config.runtime import RuntimeSettings


def run_async(coroutine):
    # Psycopg's asynchronous connections cannot use Windows' Proactor loop.
    return asyncio.run(coroutine, loop_factory=asyncio.SelectorEventLoop if sys.platform == "win32" else None)


async def work(registry, once):
    workers = [(binding.access, Worker(registry.application(binding))) for binding in registry.settings.bindings]
    if not workers:
        raise ValueError("RUNTIME_AUTH_BINDINGS is required for the worker")
    try:
        while True:
            progressed = False
            for access, worker in workers:
                progressed = await worker.run_once(access) or progressed
            if once:
                return
            if not progressed:
                await asyncio.sleep(.5)
    finally:
        registry.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", help="Load a private KEY=value environment file without overriding existing values")
    sub = parser.add_subparsers(dest="command", required=True)
    server = sub.add_parser("serve")
    server.add_argument("--host", default="127.0.0.1")
    server.add_argument("--port", type=int, default=8000)
    worker = sub.add_parser("worker")
    worker.add_argument("--once", action="store_true")
    sub.add_parser("checkpoints-setup")
    args = parser.parse_args()
    from backend.observability.logging import configure
    configure()
    if args.env_file:
        from backend.data.cli import load_environment
        load_environment(args.env_file)
    if args.command == "serve":
        if RuntimeSettings.from_env().local_access and args.host not in {"127.0.0.1", "::1", "localhost"}:
            parser.error("RUNTIME_LOCAL_ACCESS requires a loopback --host")
        import uvicorn
        uvicorn.run("backend.api.app:create_app", factory=True, host=args.host, port=args.port,
                    log_config=None, proxy_headers=False)
    elif args.command == "worker":
        run_async(work(Registry(), args.once))
    else:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        settings = RuntimeSettings.from_env()
        if not settings.langgraph_database_url:
            raise ValueError("LANGGRAPH_DATABASE_URL is required")
        async def setup():
            async with AsyncPostgresSaver.from_conn_string(settings.langgraph_database_url) as saver:
                await saver.setup()
        run_async(setup())


if __name__ == "__main__":
    main()
