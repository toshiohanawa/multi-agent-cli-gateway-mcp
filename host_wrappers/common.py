"""
Shared utilities for Codex/Claude HTTP wrappers.
"""

import os
import time
from typing import Dict, List, Optional

from fastapi import Header, HTTPException, Request

ALLOWED_ENV_VARS = {"PATH", "HOME", "SHELL", "LANG", "LC_ALL", "TERM"}
AUTH_TOKEN = os.getenv("WRAPPER_AUTH_TOKEN")
MAX_BODY_BYTES = int(os.getenv("WRAPPER_MAX_BODY_BYTES", str(16 * 1024)))  # default 16KB
RATE_LIMIT_WINDOW = int(os.getenv("WRAPPER_RATE_WINDOW", "60"))
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("WRAPPER_RATE_MAX_REQUESTS", "30"))


def build_safe_env() -> dict:
    """Return a sanitized environment limited to whitelisted variables."""
    env = {k: v for k, v in os.environ.items() if k in ALLOWED_ENV_VARS}
    env.setdefault("PATH", os.environ.get("PATH", ""))
    return env


def verify_token(token: Optional[str] = Header(default=None, alias="X-Auth-Token")) -> None:
    """Verify authentication token if set."""
    if AUTH_TOKEN is None:
        return
    if token != AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="unauthorized")


def make_rate_and_size_guard(
    rate_log: Dict[str, List[float]],
    max_body_bytes: int = MAX_BODY_BYTES,
    window_seconds: int = RATE_LIMIT_WINDOW,
    max_requests: int = RATE_LIMIT_MAX_REQUESTS,
):
    """Build a middleware that enforces rate limiting and body size caps."""

    async def _guard(request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        entries = rate_log.setdefault(client_ip, [])
        entries[:] = [ts for ts in entries if now - ts < window_seconds]
        if len(entries) >= max_requests:
            raise HTTPException(status_code=429, detail="rate limit exceeded")
        entries.append(now)

        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > max_body_bytes:
                    raise HTTPException(status_code=413, detail="request body too large")
            except ValueError:
                raise HTTPException(status_code=400, detail="invalid content-length header")
        else:
            body = await request.body()
            if len(body) > max_body_bytes:
                raise HTTPException(status_code=413, detail="request body too large")
            request._body = body  # cache for downstream handlers

        return await call_next(request)

    return _guard
