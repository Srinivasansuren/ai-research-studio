from __future__ import annotations

import os
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

APP_NAME = "orchestrator-api"
APP_VERSION = "0.1.0-phase1"

app = FastAPI(title=APP_NAME, version=APP_VERSION)


class ChatRequest(BaseModel):
    """
    Phase 1: Stub request model.
    Later phases will include attachments (PDFs/links), hypothesis objects, etc.
    """
    message: str = Field(..., min_length=1, max_length=20000)
    conversation_id: Optional[str] = Field(default=None, max_length=200)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    request_id: str
    conversation_id: str
    created_at_unix: int
    model: str
    output: str
    blocks: List[Dict[str, Any]]


@app.get("/healthz")
def healthz() -> Dict[str, Any]:
    # Simple health endpoint for Cloud Run readiness checks / monitoring.
    return {
        "ok": True,
        "service": APP_NAME,
        "version": APP_VERSION,
        "time_unix": int(time.time()),
    }


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    """
    Phase 1: Stubbed chat endpoint.
    - No LLM calls
    - No web
    - No storage
    Returns a structured response shape that later phases will extend.
    """
    request_id = f"REQ-{uuid.uuid4().hex[:12]}"
    conversation_id = req.conversation_id or f"CONV-{uuid.uuid4().hex[:12]}"
    now = int(time.time())

    output_text = (
        "Phase 1 stub response.\n\n"
        "Received your message and returned a structured placeholder output.\n"
        "No search, no evidence, no debate, no artifacts in this phase."
    )

    blocks = [
        {
            "type": "text",
            "format": "markdown",
            "content": output_text,
        },
        {
            "type": "debug",
            "content": {
                "echo": req.message[:5000],
                "metadata": req.metadata,
                "env": {
                    "port": os.getenv("PORT"),
                },
            },
        },
    ]

    return ChatResponse(
        request_id=request_id,
        conversation_id=conversation_id,
        created_at_unix=now,
        model="none-phase1",
        output=output_text,
        blocks=blocks,
    )
