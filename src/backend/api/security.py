"""Bearer tokens mapped to server-controlled DB principals; no ambient cookies."""
import asyncio
import hashlib
import secrets
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
