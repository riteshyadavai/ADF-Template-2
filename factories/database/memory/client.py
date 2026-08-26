"""In-memory hot/cold state backends."""

from __future__ import annotations

from typing import Any

from agents.memory import ColdStateStore, HotStateStore, WorkflowStateRecord


class InMemoryHotStateStore(HotStateStore):
    def __init__(self) -> None:
        self._store: dict[str, WorkflowStateRecord] = {}

    async def get(self, run_id: str) -> WorkflowStateRecord | None:
        return self._store.get(run_id)

    async def save(self, record: WorkflowStateRecord) -> None:
        self._store[record.run_id] = record

    async def delete(self, run_id: str) -> None:
        self._store.pop(run_id, None)


class InMemoryColdStateStore(ColdStateStore):
    def __init__(self) -> None:
        self._history: dict[str, list[dict[str, Any]]] = {}
        self._evals: list[dict[str, Any]] = []

    async def append_history(self, run_id: str, event: dict[str, Any]) -> None:
        self._history.setdefault(run_id, []).append(event)

    async def get_history(self, run_id: str) -> list[dict[str, Any]]:
        return self._history.get(run_id, [])

    async def save_eval_result(
        self,
        *,
        run_id: str,
        git_sha: str,
        prompt_version: str,
        model_version: str,
        score: float,
        metadata: dict[str, Any],
    ) -> None:
        self._evals.append(
            {
                "run_id": run_id,
                "git_sha": git_sha,
                "prompt_version": prompt_version,
                "model_version": model_version,
                "score": score,
                "metadata": metadata,
            }
        )
