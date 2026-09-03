"""BQML client factory."""

from __future__ import annotations

from config.settings import Settings, get_settings
from factories.bqml.bigquery.client import BigQueryMlClient
from factories.bqml.protocol import BqmlClient


def make_bqml_client(settings: Settings | None = None) -> BqmlClient:
    settings = settings or get_settings()
    bqml = settings.bqml
    if not bqml.enabled:
        return BigQueryMlClient(bqml, client=None)
    try:
        from google.cloud import bigquery
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "google-cloud-bigquery is required when BQML_ENABLED=true. "
            "Install with: uv sync --extra bqml"
        ) from exc
    kwargs: dict[str, str] = {}
    if bqml.project:
        kwargs["project"] = bqml.project
    if bqml.location:
        kwargs["location"] = bqml.location
    client = bigquery.Client(**kwargs)
    return BigQueryMlClient(bqml, client=client)
