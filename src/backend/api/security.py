"""Bearer tokens mapped to server-controlled DB principals; no ambient cookies."""
import asyncio
import hashlib
import secrets
from ipaddress import ip_address
from urllib.parse import urlsplit
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.contracts.data import AccessContext

bearer = HTTPBearer(auto_error=False)


@dataclass
class Actor:
    access: AccessContext
    application: object


async def actor(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    registry = request.app.state.registry
    if credentials is None and registry.settings.local_access:
        local = {"127.0.0.1", "localhost", "::1"}
        try:
            allowed = (ip_address(request.client.host).is_loopback
                and urlsplit("http://" + request.headers.get("host", "")).hostname in local
                and not any(h in request.headers for h in ("forwarded", "x-forwarded-for", "x-forwarded-host"))
                and (not request.headers.get("origin") or urlsplit(request.headers["origin"]).hostname in local))
        except (ValueError, AttributeError):
            allowed = False
        if not allowed:
            raise HTTPException(status_code=403, detail="Local access requires a loopback connection")
        binding = registry.settings.bindings[0]
        app = await asyncio.to_thread(registry.application, binding)
        return Actor(access=binding.access, application=app)
    if credentials is None or len(request.headers.getlist("authorization")) != 1:
        raise HTTPException(status_code=401, detail="Authentication required", headers={"WWW-Authenticate": "Bearer"})
    digest = hashlib.sha256(credentials.credentials.encode()).hexdigest()
    binding = None
    for candidate in request.app.state.registry.settings.bindings:
        if secrets.compare_digest(digest, candidate.token_sha256):
            binding = candidate
    if binding is None:
        raise HTTPException(status_code=401, detail="Authentication required", headers={"WWW-Authenticate": "Bearer"})
    app = await asyncio.to_thread(request.app.state.registry.application, binding)
    return Actor(access=binding.access, application=app)


async def idempotency_key(request: Request):
    keys = request.headers.getlist("idempotency-key")
    if len(keys) != 1 or not 1 <= len(keys[0]) <= 128 or not all(32 < ord(c) < 127 for c in keys[0]):
        raise HTTPException(status_code=422, detail="One Idempotency-Key header of 1–128 visible ASCII characters is required")
    return keys[0]
