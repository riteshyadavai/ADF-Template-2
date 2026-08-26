"""Document parsing interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ParsedDocument(BaseModel):
    text: str
    sections: list[dict[str, str]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    parser: str


class DocumentParser(ABC):
    @abstractmethod
    async def parse(self, path: Path) -> ParsedDocument: ...
