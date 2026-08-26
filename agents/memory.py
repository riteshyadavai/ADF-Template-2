"""Platform contracts for hot and cold workflow state."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class WorkflowStateRecord(BaseModel):
    run_id: str
    tenant_id: str
    state: dict[str, Any] = Field(default_factory=dict)
    status: str = "running"
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class HotStateStore(ABC):
    """Low-latency in-flight workflow/session state."""

    @abstractmethod
    async def get(self, run_id: str) -> WorkflowStateRecord | None: ...

    @abstractmethod
    async def save(self, record: WorkflowStateRecord) -> None: ...

    @abstractmethod
    async def delete(self, run_id: str) -> None: ...


class ColdStateStore(ABC):
    """Analytical execution history and eval results."""

    @abstractmethod
    async def append_history(self, run_id: str, event: dict[str, Any]) -> None: ...

    @abstractmethod
    async def get_history(self, run_id: str) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def save_eval_result(
        self,
        *,
        run_id: str,
        git_sha: str,
        prompt_version: str,
        model_version: str,
        score: float,
        metadata: dict[str, Any],
    ) -> None: ...
