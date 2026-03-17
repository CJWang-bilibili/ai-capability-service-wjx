from __future__ import annotations

from app.capabilities.base import BaseCapability
from app.capabilities.sentiment_analysis import SentimentAnalysisCapability
from app.capabilities.text_summary import TextSummaryCapability

_CAPABILITIES: dict[str, BaseCapability] = {}


def _register(*caps: BaseCapability) -> None:
    for cap in caps:
        _CAPABILITIES[cap.name] = cap


_register(
    TextSummaryCapability(),
    SentimentAnalysisCapability(),
)


def get_capability(name: str) -> BaseCapability | None:
    return _CAPABILITIES.get(name)


def list_capabilities() -> list[str]:
    return sorted(_CAPABILITIES.keys())
