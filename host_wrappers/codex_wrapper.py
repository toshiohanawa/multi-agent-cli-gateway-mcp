"""
FastAPI wrapper for running the `codex` CLI via HTTP.
"""

import subprocess
from typing import List, Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

CLI_COMMAND = ["codex", "exec"]
TIMEOUT_SECONDS = 120


class HistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    history: List[HistoryItem] = Field(default_factory=list)


class ChatResponse(BaseModel):
    output: str


app = FastAPI(title="Codex CLI Wrapper", version="0.1.0")


@app.post("/codex", response_model=ChatResponse)
async def call_codex(body: ChatRequest) -> JSONResponse:
    """Execute the codex CLI and return its stdout."""
    try:
        result = subprocess.run(
            CLI_COMMAND,
            input=body.prompt,
            text=True,
            capture_output=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(status_code=504, detail=f"codex CLI timed out after {TIMEOUT_SECONDS}s") from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail="failed to execute codex CLI") from exc

    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise HTTPException(status_code=500, detail=f"codex CLI failed: {stderr or 'unknown error'}")

    return JSONResponse(status_code=200, content={"output": result.stdout})


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("codex_wrapper:app", host="0.0.0.0", port=9001, reload=False)
