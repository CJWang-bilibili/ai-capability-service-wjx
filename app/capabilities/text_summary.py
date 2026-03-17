from __future__ import annotations

import logging
from typing import Any

from app.capabilities.base import BaseCapability, CapabilityError
from app.config import settings

logger = logging.getLogger(__name__)

_MOCK_SUMMARY = (
    "This is a mock summary generated in development mode. "
    "Set ANTHROPIC_API_KEY in your .env to get real summaries."
)


class TextSummaryCapability(BaseCapability):
    name = "text_summary"

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        text = input_data.get("text")
        if not text or not isinstance(text, str):
            raise CapabilityError(
                code="INVALID_INPUT",
                message="'text' field is required and must be a non-empty string",
            )

        max_length: int = int(input_data.get("max_length", 150))

        if settings.use_mock:
            logger.info("text_summary: using mock response (no API key configured)")
            return {"result": _MOCK_SUMMARY[:max_length]}

        return await self._call_claude(text, max_length)

    async def _call_claude(self, text: str, max_length: int) -> dict[str, Any]:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

        system_prompt = (
            "You are a precise text summarization assistant. "
            "Summarize the given text concisely. "
            f"The summary must be at most {max_length} characters. "
            "Return only the summary text, nothing else."
        )

        try:
            async with client.messages.stream(
                model="claude-opus-4-6",
                max_tokens=512,
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

        result = next(
            (block.text for block in message.content if block.type == "text"), ""
        )
        return {"result": result}
