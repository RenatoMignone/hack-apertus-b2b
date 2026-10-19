"""Bound request buffering before validation, with safe request correlation."""
import json
import re
from time import perf_counter
from backend.observability.logging import event
from uuid import uuid4


class RequestBoundary:
    def __init__(self, app, limit):
        self.app, self.limit = app, limit

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope["headers"])
        supplied = headers.get(b"x-request-id", b"").decode("ascii", errors="ignore")
        request_id = supplied if re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", supplied) else str(uuid4())
        scope.setdefault("state", {})["request_id"] = request_id
        started = perf_counter()
        if scope["method"] != "GET":
            event("http.started", method=scope["method"], route=scope["path"], request_id=request_id)
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > self.limit:
                data = json.dumps({"schema_version": "1", "request_id": request_id,
                    "error": {"code": "request_too_large", "message": "Request body exceeds the configured limit", "retryable": False}}).encode()
                await send({"type": "http.response.start", "status": 413,
                    "headers": [(b"content-type", b"application/json"), (b"x-request-id", request_id.encode())]})
                return await send({"type": "http.response.body", "body": data})
            if not message.get("more_body", False):
                break
        delivered = False
        async def replay():
            nonlocal delivered
            if delivered:
                return await receive()
            delivered = True
            return {"type": "http.request", "body": bytes(body), "more_body": False}
        async def correlated(message):
            if message["type"] == "http.response.start":
                elapsed = round((perf_counter()-started)*1000)
                if scope["method"] != "GET" or message["status"] >= 400 or elapsed >= 1000:
                    event("http.completed", method=scope["method"], route=scope["path"], request_id=request_id,
                          status=message["status"], elapsed_ms=elapsed)
                message["headers"] = [*message.get("headers", []), (b"x-request-id", request_id.encode())]
            await send(message)
        await self.app(scope, replay, correlated)
