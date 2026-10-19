"""Console diagnostics contain identifiers/counts/timings, never task payloads."""
import asyncio
from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar
import logging
from logging.config import dictConfig
import re
from time import perf_counter

_context = ContextVar('navigator_log_context', default={})
_KEYS = {'run_id', 'case_id', 'stage', 'task', 'model', 'attempt', 'status', 'elapsed_ms',
         'count', 'query_count', 'candidate_count', 'prompt_tokens', 'completion_tokens',
         'error_type', 'error_code', 'validation_field', 'validation_type', 'request_id', 'method', 'route', 'remaining_seconds'}


def event(name, **fields):
    safe = {}
    for key, value in {**_context.get(), **fields}.items():
        if key not in _KEYS or value is None:
            continue
        if isinstance(value, (int, float, bool)) or re.fullmatch(r'[a-zA-Z0-9_./:{}$-]{1,160}', str(value)):
            safe[key] = value
    logging.getLogger('backend.runtime').info('%s %s', name,
        ' '.join(f'{key}={value}' for key, value in safe.items()))


@contextmanager
def context(**values):
    token = _context.set({**_context.get(), **values})
    try:
        yield
    finally:
        _context.reset(token)


@contextmanager
def timed(name, **fields):
    started = perf_counter()
    with context(**fields):
        event(name + '.started')
        try:
            yield
        except BaseException as error:
            event(name + '.failed', elapsed_ms=round((perf_counter()-started)*1000), error_type=type(error).__name__)
            raise
        else:
            event(name + '.completed', elapsed_ms=round((perf_counter()-started)*1000))


@asynccontextmanager
async def activity(name, **fields):
    started = perf_counter()
    async def heartbeat():
        while True:
            await asyncio.sleep(10)
            event(name + '.waiting', elapsed_ms=round((perf_counter()-started)*1000))
    with timed(name, **fields):
        pulse = asyncio.create_task(heartbeat())
        try:
            yield
        finally:
            pulse.cancel()
            await asyncio.gather(pulse, return_exceptions=True)


class PollFilter(logging.Filter):
    def filter(self, record):
        # Uvicorn's structured args: client, method, path, protocol, status.
        args = record.args
        if isinstance(args, tuple) and len(args) == 5:
            _, method, path, _, status = args
            if method == 'GET' and status == 200 and re.fullmatch(
                    r'/api/v1/(cases/[^/?]+(?:/runs/[^/?]+)?|operations/[^/?]+)', path):
                return False
        return True


def configure():
    dictConfig({'version': 1, 'disable_existing_loggers': False,
        'formatters': {'console': {'format': '%(asctime)s %(levelname)-7s %(name)s | %(message)s',
                                   'datefmt': '%Y-%m-%d %H:%M:%S'}},
        'filters': {'poll': {'()': PollFilter}},
        'handlers': {'console': {'class': 'logging.StreamHandler', 'formatter': 'console', 'filters': ['poll']}},
        'root': {'handlers': ['console'], 'level': 'INFO'},
        'loggers': {name: {'handlers': [], 'propagate': True, 'level': level} for name, level in
                    [('uvicorn', 'INFO'), ('uvicorn.error', 'INFO'), ('uvicorn.access', 'INFO'),
                     ('httpx', 'WARNING'), ('httpcore', 'WARNING')]}})
