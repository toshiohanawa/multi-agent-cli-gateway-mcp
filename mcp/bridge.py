"""
Bridge MCP server exposing debate tools that call out to host CLI wrappers.
"""

import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

import requests
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

CODEX_URL = "http://host.docker.internal:9001/codex"
CLAUDE_URL = "http://host.docker.internal:9002/claude"
HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT_SECONDS", "60"))  # デフォルト60秒（CLI処理に時間がかかる場合があるため）
AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN")
MAX_BODY_BYTES = 32 * 1024  # 32KB
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX_REQUESTS = 20
_rate_log: Dict[str, List[float]] = {}


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
    """A turn in the debate, containing alternating responses."""
    user_instruction: str
    codex_output: Optional[str] = None  # None if Codex didn't respond this turn
    claude_output: Optional[str] = None  # None if Claude didn't respond this turn
    responder: Literal["codex", "claude"] = "codex"  # Who responded in this turn


@dataclass
class DebateSession:
    active: bool = False
    history: List[Turn] = field(default_factory=list)
    user_id: Optional[str] = None
    next_responder: Literal["codex", "claude"] = "codex"  # Track who should respond next


# Session storage: user_id -> DebateSession
_sessions: Dict[str, DebateSession] = {}


class StartDebateRequest(BaseModel):
    initial_prompt: str = Field(..., min_length=1, max_length=8192)  # Limit prompt size


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
    codex_output: Optional[str] = None
    claude_output: Optional[str] = None
    responder: Literal["codex", "claude"]
    next_responder: Optional[Literal["codex", "claude"]] = None


class StatusResponse(BaseModel):
    status: str
    turn: Optional[TurnResponse] = None
    message: Optional[str] = None


app = FastAPI(title="AI Debate MCP Bridge", version="1.0.0")


def _verify_token(token: str = Header(default=None, alias="X-Auth-Token")) -> None:
    """Verify authentication token if AUTH_TOKEN is set."""
    if AUTH_TOKEN is None:
        return
    if token != AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="unauthorized")


def _get_user_id(request: Request) -> str:
    """Get or create user ID from request header or generate new one."""
    user_id_header = request.headers.get("X-User-ID")
    if user_id_header:
        return user_id_header
    # Generate a new user ID if not provided
    return str(uuid.uuid4())


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


def call_model(url: str, prompt: str, auth_token: Optional[str] = None) -> str:
    """Call model wrapper with optional authentication."""
    payload = {"prompt": prompt, "history": []}
    headers = {}
    if auth_token:
        headers["X-Auth-Token"] = auth_token
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"failed to reach model wrapper: {exc}") from exc

    data: Dict[str, str] = resp.json()
    output = data.get("output")
    if output is None:
        raise HTTPException(status_code=500, detail="wrapper response missing 'output'")
    return output


def build_next_prompt(
    decision: Decision,
    last_turn: Turn,
    next_responder: Literal["codex", "claude"],
    conversation_history: List[Turn],
) -> str:
    """Build prompt for the next responder, including conversation history."""
    # Build conversation context from history
    context_parts = []
    for turn in conversation_history[-3:]:  # Last 3 turns for context
        if turn.codex_output:
            context_parts.append(f"Codex: {turn.codex_output}")
        if turn.claude_output:
            context_parts.append(f"Claude: {turn.claude_output}")
    
    context = "\n\n".join(context_parts) if context_parts else ""
    
    # Get the last response from the other model
    last_response = None
    if next_responder == "codex" and last_turn.claude_output:
        last_response = f"Claude said: {last_turn.claude_output}"
    elif next_responder == "claude" and last_turn.codex_output:
        last_response = f"Codex said: {last_turn.codex_output}"
    
    # Build instruction prefix
    if decision.type == "adopt_codex":
        prefix = "Proceed using Codex's approach as the primary direction."
    elif decision.type == "adopt_claude":
        prefix = "Proceed using Claude's approach as the primary direction."
    else:
        prefix = f"Follow this new instruction from the user: {decision.validated_text()}"
    
    # Construct prompt
    prompt_parts = [prefix]
    if last_response:
        prompt_parts.append(f"\n{last_response}")
    if context:
        prompt_parts.append(f"\n\nPrevious conversation:\n{context}")
    prompt_parts.append("\n\nRespond concisely and continue the debate.")
    
    return "".join(prompt_parts)


@app.post("/start_debate", response_model=StatusResponse)
async def start_debate(
    body: StartDebateRequest,
    request: Request,
    _: None = Depends(_verify_token),
) -> JSONResponse:
    """Start a new debate session for the user. Codex responds first, then Claude."""
    user_id = _get_user_id(request)
    session = _sessions.get(user_id)

    if session and session.active:
        raise HTTPException(status_code=400, detail="debate session already active")

    if session is None:
        session = DebateSession(user_id=user_id, next_responder="codex")
        _sessions[user_id] = session

    prompt = body.initial_prompt
    wrapper_auth = os.getenv("WRAPPER_AUTH_TOKEN")
    
    # Step 1: Codex responds first
    codex_output = call_model(CODEX_URL, prompt, auth_token=wrapper_auth)
    turn1 = Turn(
        user_instruction=prompt,
        codex_output=codex_output,
        claude_output=None,
        responder="codex",
    )
    session.history.append(turn1)
    
    # Step 2: Claude responds to Codex's output
    claude_prompt = f"Codex said: {codex_output}\n\nRespond to Codex's point and continue the discussion."
    claude_output = call_model(CLAUDE_URL, claude_prompt, auth_token=wrapper_auth)
    turn2 = Turn(
        user_instruction=claude_prompt,
        codex_output=None,
        claude_output=claude_output,
        responder="claude",
    )
    session.history.append(turn2)
    session.active = True
    session.next_responder = "codex"  # Next turn, Codex responds

    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "turn": {
                "user_instruction": prompt,
                "codex_output": codex_output,
                "claude_output": claude_output,
                "responder": "claude",  # Last responder
                "next_responder": "codex",
            },
        },
        headers={"X-User-ID": user_id},
    )


@app.post("/step", response_model=StatusResponse)
async def step(
    body: StepRequest,
    request: Request,
    _: None = Depends(_verify_token),
) -> JSONResponse:
    """Advance the debate session for the user. Only one model responds per turn."""
    user_id = _get_user_id(request)
    session = _sessions.get(user_id)

    if not session or not session.active or not session.history:
        raise HTTPException(status_code=400, detail="no active session")

    last_turn = session.history[-1]
    next_responder = session.next_responder
    
    # Build prompt for the next responder
    next_prompt = build_next_prompt(body.decision, last_turn, next_responder, session.history)

    wrapper_auth = os.getenv("WRAPPER_AUTH_TOKEN")
    
    # Only call the next responder (alternating)
    if next_responder == "codex":
        codex_output = call_model(CODEX_URL, next_prompt, auth_token=wrapper_auth)
        turn = Turn(
            user_instruction=next_prompt,
            codex_output=codex_output,
            claude_output=None,
            responder="codex",
        )
        session.next_responder = "claude"  # Next turn, Claude responds
    else:  # claude
        claude_output = call_model(CLAUDE_URL, next_prompt, auth_token=wrapper_auth)
        turn = Turn(
            user_instruction=next_prompt,
            codex_output=None,
            claude_output=claude_output,
            responder="claude",
        )
        session.next_responder = "codex"  # Next turn, Codex responds
    
    session.history.append(turn)

    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "turn": {
                "user_instruction": turn.user_instruction,
                "codex_output": turn.codex_output,
                "claude_output": turn.claude_output,
                "responder": turn.responder,
                "next_responder": session.next_responder,
            },
        },
        headers={"X-User-ID": user_id},
    )


@app.post("/stop", response_model=StatusResponse)
async def stop(
    request: Request,
    _: None = Depends(_verify_token),
) -> JSONResponse:
    """Stop the debate session for the user."""
    user_id = _get_user_id(request)
    session = _sessions.get(user_id)

    if not session or not session.active:
        raise HTTPException(status_code=400, detail="no active session")

    session.active = False
    session.history.clear()

    return JSONResponse(
        status_code=200,
        content={"status": "stopped"},
        headers={"X-User-ID": user_id},
    )


@app.get("/health")
async def health(request: Request) -> dict:
    """Health check endpoint (no auth required)."""
    user_id = _get_user_id(request)
    session = _sessions.get(user_id)
    if session:
        return {
            "status": "ok",
            "active": session.active,
            "turns": len(session.history),
            "user_id": user_id,
        }
    return {"status": "ok", "active": False, "turns": 0}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "mcp.bridge:app",
        host=os.getenv("MCP_BIND_HOST", "127.0.0.1"),
        port=int(os.getenv("MCP_BIND_PORT", "8080")),
        reload=False,
    )
