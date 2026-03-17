from __future__ import annotations

import json
import logging
from typing import Any

from app.capabilities.base import BaseCapability, CapabilityError
from app.config import settings

logger = logging.getLogger(__name__)

_MOCK_RESULT = {
    "sentiment": "positive",
    "score": 0.85,
    "explanation": "Mock sentiment analysis (no API key configured).",
}


class SentimentAnalysisCapability(BaseCapability):
    name = "sentiment_analysis"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        text = input_data.get("text")
        if not text or not isinstance(text, str):
            raise CapabilityError(
                code="INVALID_INPUT",
                message="'text' field is required and must be a non-empty string",
            )

        if settings.use_mock:
            logger.info("sentiment_analysis: using mock response (no API key configured)")
            return {"result": _MOCK_RESULT}

        return await self._call_claude(text)

    async def _call_claude(self, text: str) -> dict[str, Any]:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

        system_prompt = (
            "You are a sentiment analysis assistant. "
            "Analyze the sentiment of the given text and respond ONLY with valid JSON "
            "in this exact format (no markdown, no extra text):\n"
            '{"sentiment": "positive|negative|neutral", "score": 0.0-1.0, "explanation": "..."}'
        )

        try:
            async with client.messages.stream(
                model="claude-opus-4-6",
                max_tokens=256,
                system=system_prompt,
                messages=[{"role": "user", "content": text}],
            ) as stream:
                message = await stream.get_final_message()
        except anthropic.AuthenticationError:
            raise CapabilityError(
                code="AUTH_ERROR",
                message="Invalid or missing Anthropic API key",
            )
        except anthropic.RateLimitError:
            raise CapabilityError(
                code="RATE_LIMIT",
                message="Rate limit reached. Please retry later.",
            )
        except anthropic.APIStatusError as exc:
            raise CapabilityError(
                code="UPSTREAM_ERROR",
                message=f"Upstream API error: {exc.message}",
                details={"status_code": exc.status_code},
            )

        raw = next(
            (block.text for block in message.content if block.type == "text"), ""
        ).strip()

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            raise CapabilityError(
                code="PARSE_ERROR",
                message="Failed to parse model response as JSON",
                details={"raw": raw},
            )

        return {"result": parsed}
