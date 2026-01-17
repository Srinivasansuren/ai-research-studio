from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.routes.chat import router as chat_router

APP_NAME = "orchestrator-api"
APP_VERSION = "0.1.0-phase3"

app = FastAPI(title=APP_NAME, version=APP_VERSION)

# ----------------------------
# Models (unchanged)
# ----------------------------

class ChatRequest(BaseModel):
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


# ----------------------------
# Health check (unchanged)
# ----------------------------

@app.get("/healthz")
def healthz() -> Dict[str, Any]:
    return {
        "ok": True,
        "service": APP_NAME,
        "version": APP_VERSION,
        "time_unix": int(time.time()),
    }


# ----------------------------
# Routes
# ----------------------------

app.include_router(chat_router)
