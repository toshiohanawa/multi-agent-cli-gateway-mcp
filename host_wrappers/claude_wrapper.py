"""
FastAPI wrapper for running the `claudecode` CLI via HTTP.
"""

import os
import subprocess
import time
from typing import Dict, List, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

CLI_COMMAND = ["claude", "-p"]
TIMEOUT_SECONDS = int(os.getenv("CLI_TIMEOUT_SECONDS", "60"))  # デフォルト60秒（CLI処理に時間がかかる場合があるため）
AUTH_TOKEN = os.getenv("WRAPPER_AUTH_TOKEN")
MAX_BODY_BYTES = 16 * 1024  # 16KB
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX_REQUESTS = 30
ALLOWED_ENV_VARS = {"PATH", "HOME", "SHELL", "LANG", "LC_ALL", "TERM"}
_rate_log: Dict[str, List[float]] = {}


class HistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    history: List[HistoryItem] = Field(default_factory=list)


class ChatResponse(BaseModel):
    output: str


app = FastAPI(title="ClaudeCode CLI Wrapper", version="0.1.0")


def _build_safe_env() -> dict:
    """Build a safe environment variable dict with only whitelisted vars."""
    env = {k: v for k, v in os.environ.items() if k in ALLOWED_ENV_VARS}
    env.setdefault("PATH", os.environ.get("PATH", ""))
    return env


def _verify_token(token: str = Header(default=None, alias="X-Auth-Token")) -> None:
    """Verify authentication token if AUTH_TOKEN is set."""
    if AUTH_TOKEN is None:
        return
    if token != AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="unauthorized")


@app.middleware("http")
async def rate_and_size_guard(request: Request, call_next):
    """Rate limiting and request size checking middleware."""
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    entries = _rate_log.setdefault(client_ip, [])
    entries[:] = [ts for ts in entries if now - ts < RATE_LIMIT_WINDOW]
    if len(entries) >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(status_code=429, detail="rate limit exceeded")
    entries.append(now)

    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_BODY_BYTES:
                raise HTTPException(status_code=413, detail="request body too large")
        except ValueError:
            raise HTTPException(status_code=400, detail="invalid content-length header")
    else:
        body = await request.body()
        if len(body) > MAX_BODY_BYTES:
            raise HTTPException(status_code=413, detail="request body too large")
        request._body = body  # cache for downstream handlers

    return await call_next(request)


@app.post("/claude", response_model=ChatResponse)
async def call_claude(body: ChatRequest, _: None = Depends(_verify_token)) -> JSONResponse:
    """Execute the claudecode CLI and return its stdout."""
    try:
        result = subprocess.run(
            CLI_COMMAND,
            input=body.prompt,
            text=True,
            capture_output=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
            env=_build_safe_env(),
        )
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(status_code=504, detail=f"claudecode CLI timed out after {TIMEOUT_SECONDS}s") from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail="failed to execute claudecode CLI") from exc

    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise HTTPException(status_code=500, detail=f"claudecode CLI failed: {stderr or 'unknown error'}")

    return JSONResponse(status_code=200, content={"output": result.stdout})


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "claude_wrapper:app",
        host=os.getenv("WRAPPER_BIND_HOST", "127.0.0.1"),
        port=int(os.getenv("WRAPPER_BIND_PORT", "9002")),
        reload=False,
    )
