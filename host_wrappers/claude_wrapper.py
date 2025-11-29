"""
FastAPI wrapper for running the `claudecode` CLI via HTTP.
"""

import os
import subprocess
from typing import Dict, List, Literal

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, conlist

from common import (
    AUTH_TOKEN,
    MAX_BODY_BYTES,
    RATE_LIMIT_MAX_REQUESTS,
    RATE_LIMIT_WINDOW,
    build_safe_env,
    make_rate_and_size_guard,
    verify_token,
)

CLI_COMMAND = ["claude", "-p"]
TIMEOUT_SECONDS = int(os.getenv("CLI_TIMEOUT_SECONDS", "60"))  # デフォルト60秒（CLI処理に時間がかかる場合があるため）
_rate_log: Dict[str, List[float]] = {}


class HistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=8192)
    history: conlist(HistoryItem, max_length=10) = Field(default_factory=list)


class ChatResponse(BaseModel):
    output: str


app = FastAPI(title="ClaudeCode CLI Wrapper", version="0.1.0")
app.middleware("http")(
    make_rate_and_size_guard(
        _rate_log,
        max_body_bytes=MAX_BODY_BYTES,
        window_seconds=RATE_LIMIT_WINDOW,
        max_requests=RATE_LIMIT_MAX_REQUESTS,
    )
)


@app.post("/claude", response_model=ChatResponse)
async def call_claude(body: ChatRequest, _: None = Depends(verify_token)) -> JSONResponse:
    """Execute the claudecode CLI and return its stdout."""
    try:
        result = subprocess.run(
            CLI_COMMAND,
            input=body.prompt,
            text=True,
            capture_output=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
            env=build_safe_env(),
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
