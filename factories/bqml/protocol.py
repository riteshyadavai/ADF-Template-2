"""BigQuery ML client protocol."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BqmlClient(ABC):
    enabled: bool

    @abstractmethod
    def list_models(self, dataset: str | None = None) -> list[dict[str, Any]]: ...

    @abstractmethod
    def get_model(self, model_id: str) -> dict[str, Any]: ...

    @abstractmethod
    def predict(self, model_id: str, source_sql: str) -> list[dict[str, Any]]: ...

    @abstractmethod
    def explain_predict(self, model_id: str, source_sql: str) -> list[dict[str, Any]]: ...

    @abstractmethod
    def run_sql(self, sql: str) -> list[dict[str, Any]]: ...
