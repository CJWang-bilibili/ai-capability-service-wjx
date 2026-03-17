from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Union

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.capabilities.base import CapabilityError
from app.capabilities.registry import get_capability, list_capabilities
from app.config import settings
from app.models import (
    CapabilityRequest,
    ChatRequest,
    ChatResponse,
    ErrorDetail,
    ErrorResponse,
    Meta,
    SuccessResponse,
)

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    mode = "MOCK (no real API calls)" if settings.use_mock else "LIVE (Claude API)"
    logger.info("Service starting — mode: %s", mode)
    logger.info("Available capabilities: %s", list_capabilities())
    yield
    logger.info("Service shutting down")


app = FastAPI(
    title="AI Capability Service",
    description="Unified model capability dispatch service",
    version="1.0.0",
    lifespan=lifespan,
)


def _make_meta(request_id: str, capability: str, elapsed_ms: int) -> Meta:
    return Meta(request_id=request_id, capability=capability, elapsed_ms=elapsed_ms)


def _error_response(
    request_id: str,
    capability: str,
    elapsed_ms: int,
    code: str,
    message: str,
    details: dict | None = None,
    status_code: int = 400,
) -> JSONResponse:
    body = ErrorResponse(
        error=ErrorDetail(code=code, message=message, details=details or {}),
        meta=_make_meta(request_id, capability, elapsed_ms),
    )
    return JSONResponse(status_code=status_code, content=body.model_dump())


@app.post(
    "/v1/capabilities/run",
    response_model=Union[SuccessResponse, ErrorResponse],
    responses={
        200: {"model": SuccessResponse},
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def run_capability(req: CapabilityRequest, http_request: Request):
    start = time.monotonic()
    request_id = req.request_id or str(uuid.uuid4())
    capability_name = req.capability

    logger.info(
        "request_id=%s capability=%s input_keys=%s",
        request_id,
        capability_name,
        list(req.input.keys()),
    )

    capability = get_capability(capability_name)
    if capability is None:
        elapsed = int((time.monotonic() - start) * 1000)
        logger.warning("request_id=%s unknown capability=%s", request_id, capability_name)
        return _error_response(
            request_id=request_id,
            capability=capability_name,
            elapsed_ms=elapsed,
            code="UNKNOWN_CAPABILITY",
            message=f"Unknown capability '{capability_name}'. Available: {list_capabilities()}",
            status_code=404,
        )

    try:
        result = await capability.run(req.input)
    except CapabilityError as exc:
        elapsed = int((time.monotonic() - start) * 1000)
        logger.warning(
            "request_id=%s capability=%s error_code=%s message=%s",
            request_id,
            capability_name,
            exc.code,
            exc.message,
        )
        return _error_response(
            request_id=request_id,
            capability=capability_name,
            elapsed_ms=elapsed,
            code=exc.code,
            message=exc.message,
            details=exc.details,
            status_code=400,
        )
    except Exception as exc:
        elapsed = int((time.monotonic() - start) * 1000)
        logger.exception("request_id=%s capability=%s unexpected error", request_id, capability_name)
        return _error_response(
            request_id=request_id,
            capability=capability_name,
            elapsed_ms=elapsed,
            code="INTERNAL_ERROR",
            message="An unexpected error occurred",
            status_code=500,
        )

    elapsed = int((time.monotonic() - start) * 1000)
    logger.info(
        "request_id=%s capability=%s elapsed_ms=%d status=ok",
        request_id,
        capability_name,
        elapsed,
    )

    return SuccessResponse(
        data=result,
        meta=_make_meta(request_id, capability_name, elapsed),
    )


@app.get("/healthz")
async def health():
    return {
        "status": "ok",
        "mode": "mock" if settings.use_mock else "live",
        "capabilities": list_capabilities(),
    }


@app.get("/", response_class=HTMLResponse)
async def frontend():
    import pathlib
    html_path = pathlib.Path(__file__).parent.parent / "frontend" / "index.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.post("/v1/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    import anthropic

    api_key = req.api_key.strip() if req.api_key else settings.anthropic_api_key
    if not api_key.startswith("sk-"):
        return JSONResponse(
            status_code=401,
            content={"ok": False, "error": "请先配置有效的 API Key（以 sk- 开头）", "message": "", "model": "", "usage": {}},
        )

    client = anthropic.AsyncAnthropic(api_key=api_key)
    msgs = [{"role": m.role, "content": m.content} for m in req.messages]

    try:
        message = await client.messages.create(
            model=req.model,
            max_tokens=2048,
            system=req.system or "You are a helpful assistant.",
            messages=msgs,
        )
    except anthropic.AuthenticationError:
        return JSONResponse(
            status_code=401,
            content={"ok": False, "error": "API Key 无效或已过期", "message": "", "model": "", "usage": {}},
        )
    except anthropic.RateLimitError:
        return JSONResponse(
            status_code=429,
            content={"ok": False, "error": "请求频率超限，请稍后重试", "message": "", "model": "", "usage": {}},
        )
    except anthropic.APIStatusError as exc:
        return JSONResponse(
            status_code=502,
            content={"ok": False, "error": f"上游 API 错误: {exc.message}", "message": "", "model": "", "usage": {}},
        )

    text = next((block.text for block in message.content if block.type == "text"), "")
    logger.info("chat model=%s input_tokens=%d output_tokens=%d", req.model, message.usage.input_tokens, message.usage.output_tokens)

    return ChatResponse(
        ok=True,
        message=text,
        model=req.model,
        usage={"input_tokens": message.usage.input_tokens, "output_tokens": message.usage.output_tokens},
    )
