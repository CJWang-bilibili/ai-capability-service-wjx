from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field


class CapabilityRequest(BaseModel):
    capability: str
    input: dict[str, Any]
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


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
