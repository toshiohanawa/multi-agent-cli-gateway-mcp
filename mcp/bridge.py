"""
Bridge MCP server exposing debate tools that call out to host CLI wrappers.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

CODEX_URL = "http://host.docker.internal:9001/codex"
CLAUDE_URL = "http://host.docker.internal:9002/claude"
HTTP_TIMEOUT = 120


Role = Literal["user", "assistant", "system"]


@dataclass
class Message:
    role: Role
    content: str


@dataclass
class ModelOutput:
    model: Literal["codex", "claude"]
    content: str


@dataclass
class Turn:
    user_instruction: str
    codex_output: str
    claude_output: str


@dataclass
class DebateSession:
    active: bool = False
    history: List[Turn] = field(default_factory=list)


session = DebateSession()


class StartDebateRequest(BaseModel):
    initial_prompt: str = Field(..., min_length=1)


class Decision(BaseModel):
    type: Literal["adopt_codex", "adopt_claude", "custom_instruction"]
    custom_text: Optional[str] = Field(None, description="Used when type is custom_instruction")

    def validated_text(self) -> str:
        if self.type == "custom_instruction":
            if not self.custom_text or not self.custom_text.strip():
                raise HTTPException(status_code=400, detail="custom_text is required for custom_instruction")
            return self.custom_text.strip()
        return ""


class StepRequest(BaseModel):
    decision: Decision


class TurnResponse(BaseModel):
    user_instruction: str
    codex_output: str
    claude_output: str


class StatusResponse(BaseModel):
    status: str
    turn: Optional[TurnResponse] = None
    message: Optional[str] = None


app = FastAPI(title="AI Debate MCP Bridge", version="1.0.0")


def call_model(url: str, prompt: str) -> str:
    payload = {"prompt": prompt, "history": []}
    try:
        resp = requests.post(url, json=payload, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"failed to reach model wrapper: {exc}") from exc

    data: Dict[str, str] = resp.json()
    output = data.get("output")
    if output is None:
        raise HTTPException(status_code=500, detail="wrapper response missing 'output'")
    return output


def build_next_prompt(decision: Decision, last_turn: Turn) -> str:
    context = (
        "Continue the debate with awareness of the previous turn.\n"
        "Previous Codex output:\n"
        f"{last_turn.codex_output}\n\n"
        "Previous Claude output:\n"
        f"{last_turn.claude_output}\n\n"
    )

    if decision.type == "adopt_codex":
        prefix = "Proceed using Codex's approach as the primary direction."
    elif decision.type == "adopt_claude":
        prefix = "Proceed using Claude's approach as the primary direction."
    else:
        prefix = f"Follow this new instruction from the user: {decision.validated_text()}"

    return f"{prefix}\n\n{context}Keep responses concise but actionable."


@app.post("/start_debate", response_model=StatusResponse)
async def start_debate(body: StartDebateRequest) -> JSONResponse:
    if session.active:
        raise HTTPException(status_code=400, detail="debate session already active")

    prompt = body.initial_prompt
    codex_output = call_model(CODEX_URL, prompt)
    claude_output = call_model(CLAUDE_URL, prompt)

    turn = Turn(user_instruction=prompt, codex_output=codex_output, claude_output=claude_output)
    session.history.append(turn)
    session.active = True

    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "turn": {
                "user_instruction": turn.user_instruction,
                "codex_output": turn.codex_output,
                "claude_output": turn.claude_output,
            },
        },
    )


@app.post("/step", response_model=StatusResponse)
async def step(body: StepRequest) -> JSONResponse:
    if not session.active or not session.history:
        raise HTTPException(status_code=400, detail="no active session")

    last_turn = session.history[-1]
    next_prompt = build_next_prompt(body.decision, last_turn)

    codex_output = call_model(CODEX_URL, next_prompt)
    claude_output = call_model(CLAUDE_URL, next_prompt)

    turn = Turn(user_instruction=next_prompt, codex_output=codex_output, claude_output=claude_output)
    session.history.append(turn)

    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "turn": {
                "user_instruction": turn.user_instruction,
                "codex_output": turn.codex_output,
                "claude_output": turn.claude_output,
            },
        },
    )


@app.post("/stop", response_model=StatusResponse)
async def stop() -> JSONResponse:
    if not session.active:
        raise HTTPException(status_code=400, detail="no active session")

    session.active = False
    session.history.clear()

    return JSONResponse(status_code=200, content={"status": "stopped"})


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "active": session.active, "turns": len(session.history)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("mcp.bridge:app", host="0.0.0.0", port=8080, reload=False)
