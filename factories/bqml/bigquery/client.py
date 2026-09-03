"""BQML operations through the official BigQuery Python client."""

from __future__ import annotations

from typing import Any

from config.settings import BqmlSettings
from factories.bqml.protocol import BqmlClient


class BqmlDisabledError(RuntimeError):
    pass


class BigQueryMlClient(BqmlClient):
    def __init__(self, settings: BqmlSettings, client: Any | None = None) -> None:
        self._settings = settings
        self._client = client
        self.enabled = bool(settings.enabled and client is not None)

    def _require(self) -> Any:
        if not self.enabled or self._client is None:
            raise BqmlDisabledError(
                "BQML is disabled or not configured. Set BQML_ENABLED=true "
                "and BQML_PROJECT / BQML_DATASET (ADC or GOOGLE_APPLICATION_CREDENTIALS)."
            )
        return self._client

    def model_ref(self, model_id: str) -> str:
        cleaned = model_id.strip().strip("`")
        if cleaned.count(".") >= 2:
            return cleaned
        dataset = self._settings.dataset
        project = self._settings.project
        if cleaned.count(".") == 1:
            if project:
                return f"{project}.{cleaned}"
            return cleaned
        parts = [part for part in (project, dataset, cleaned) if part]
        return ".".join(parts)

    def predict_sql(self, model_id: str, source_sql: str) -> str:
        return (
            f"SELECT * FROM ML.PREDICT(MODEL `{self.model_ref(model_id)}`, "
            f"({_inner_sql(source_sql)}))"
        )

    def explain_predict_sql(self, model_id: str, source_sql: str) -> str:
        return (
            f"SELECT * FROM ML.EXPLAIN_PREDICT(MODEL `{self.model_ref(model_id)}`, "
            f"({_inner_sql(source_sql)}))"
        )

    def list_models(self, dataset: str | None = None) -> list[dict[str, Any]]:
        client = self._require()
        target = dataset or self._settings.dataset
        if not target:
            raise ValueError("BQML_DATASET is required to list models")
        rows: list[dict[str, Any]] = []
        for model in client.list_models(target):
            rows.append(
                {
                    "model_id": getattr(model, "model_id", None),
                    "model_type": getattr(model, "model_type", None),
                    "created": str(getattr(model, "created", "") or ""),
                }
            )
        return rows

    def get_model(self, model_id: str) -> dict[str, Any]:
        model = self._require().get_model(self.model_ref(model_id))
        return {
            "model_id": getattr(model, "model_id", None),
            "model_type": getattr(model, "model_type", None),
            "feature_columns": [
                getattr(col, "name", str(col)) for col in (getattr(model, "feature_columns", None) or [])
            ],
            "label_columns": [
                getattr(col, "name", str(col)) for col in (getattr(model, "label_columns", None) or [])
            ],
            "created": str(getattr(model, "created", "") or ""),
        }

    def predict(self, model_id: str, source_sql: str) -> list[dict[str, Any]]:
        return self.run_sql(self.predict_sql(model_id, source_sql))

    def explain_predict(self, model_id: str, source_sql: str) -> list[dict[str, Any]]:
        return self.run_sql(self.explain_predict_sql(model_id, source_sql))

    def run_sql(self, sql: str) -> list[dict[str, Any]]:
        job = self._require().query(sql)
        result = job.result()
        return [dict(row) for row in result]


def _inner_sql(source_sql: str) -> str:
    sql = source_sql.strip().rstrip(";")
    if not sql:
        raise ValueError("source_sql is required")
    return sql
