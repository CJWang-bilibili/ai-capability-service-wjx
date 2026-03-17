from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field


class CapabilityRequest(BaseModel):
    capability: str
    input: dict[str, Any]
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    api_key: str = ""
    model: str = "claude-sonnet-4-6"
    system: str = "You are a helpful assistant."
    messages: list[ChatMessage]


class ChatResponse(BaseModel):
    ok: bool
    message: str = ""
    model: str = ""
    usage: dict[str, int] = Field(default_factory=dict)
    error: str = ""


class Meta(BaseModel):
    request_id: str
    capability: str
    elapsed_ms: int


class SuccessResponse(BaseModel):
    ok: bool = True
    data: dict[str, Any]
    meta: Meta


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    ok: bool = False
    error: ErrorDetail
    meta: Meta
