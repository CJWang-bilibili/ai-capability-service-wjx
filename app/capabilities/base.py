from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class CapabilityError(Exception):
    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


class BaseCapability(ABC):
    name: str

    @abstractmethod
    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        ...
