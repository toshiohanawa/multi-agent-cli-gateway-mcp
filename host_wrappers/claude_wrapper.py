"""
FastAPI wrapper for running the `claudecode` CLI via HTTP.
"""

import subprocess
from typing import List, Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

CLI_COMMAND = ["claude", "-p"]
TIMEOUT_SECONDS = 120


class HistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    history: List[HistoryItem] = Field(default_factory=list)


class ChatResponse(BaseModel):
    output: str


app = FastAPI(title="ClaudeCode CLI Wrapper", version="0.1.0")


@app.post("/claude", response_model=ChatResponse)
async def call_claude(body: ChatRequest) -> JSONResponse:
    """Execute the claudecode CLI and return its stdout."""
    try:
        # 環境変数を継承して実行（認証情報を含む）
        import os
        env = os.environ.copy()
        result = subprocess.run(
            CLI_COMMAND,
            input=body.prompt,
            text=True,
            capture_output=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
            env=env,
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

    uvicorn.run("claude_wrapper:app", host="0.0.0.0", port=9002, reload=False)
