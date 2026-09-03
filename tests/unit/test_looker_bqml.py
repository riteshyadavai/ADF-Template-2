"""Looker and BQML factory tests (mocked SDKs)."""

from __future__ import annotations

import sys
import types

import pytest

from config.settings import BqmlSettings, LookerSettings, Settings
from factories.bqml.bigquery.client import BigQueryMlClient, BqmlDisabledError
from factories.bqml.factory import make_bqml_client
from factories.looker.factory import make_looker_client
from factories.looker.sdk.client import LookerDisabledError, LookerSdkClient
from factories.registry import FactoryRegistry


class _FakeLookerSdk:
    def me(self):
        return {"email": "analyst@example.com", "first_name": "Ada"}

    def run_look(self, look_id, result_format):
        assert look_id == "42"
        return '[{"site":"south-loop"}]'

    def run_inline_query(self, result_format, body):
        assert body["model"] == "sites"
        assert body["view"] == "scores"
        assert body["fields"] == ["scores.rank"]
        return [{"rank": 1}]


class _FakeRow(dict):
    pass


class _FakeQueryJob:
    def __init__(self, sql: str) -> None:
        self.sql = sql

    def result(self):
        return [_FakeRow(predicted_label=0.81)]


class _FakeBqClient:
    def __init__(self) -> None:
        self.last_sql = ""

    def query(self, sql: str):
        self.last_sql = sql
        return _FakeQueryJob(sql)

    def list_models(self, dataset: str):
        assert dataset == "sites"
        return [types.SimpleNamespace(model_id="site_score", model_type="BOOSTED_TREE_REGRESSOR", created="now")]

    def get_model(self, model_id: str):
        return types.SimpleNamespace(
            model_id=model_id.split(".")[-1],
            model_type="BOOSTED_TREE_REGRESSOR",
            feature_columns=[types.SimpleNamespace(name="foot_traffic")],
            label_columns=[types.SimpleNamespace(name="score")],
            created="now",
        )


def test_looker_disabled_raises():
    client = make_looker_client(Settings(looker=LookerSettings(enabled=False)))
    assert client.enabled is False
    with pytest.raises(LookerDisabledError):
        client.me()


def test_looker_sdk_methods():
    client = LookerSdkClient(LookerSettings(enabled=True), sdk=_FakeLookerSdk())
    assert client.me()["email"] == "analyst@example.com"
    rows = client.run_look("42")
    assert rows[0]["site"] == "south-loop"
    inline = client.run_inline_query(
        model="sites",
        view="scores",
        fields=["scores.rank"],
        filters={"scores.area": "South Loop"},
    )
    assert inline[0]["rank"] == 1


def test_looker_factory_init40(monkeypatch):
    fake = _FakeLookerSdk()
    monkeypatch.setitem(sys.modules, "looker_sdk", types.SimpleNamespace(init40=lambda: fake))
    client = make_looker_client(
        Settings(looker=LookerSettings(enabled=True, base_url="https://example.cloud.looker.com"))
    )
    assert client.enabled is True
    assert client.me()["first_name"] == "Ada"


def test_bqml_disabled_raises():
    client = make_bqml_client(Settings(bqml=BqmlSettings(enabled=False)))
    assert client.enabled is False
    with pytest.raises(BqmlDisabledError):
        client.list_models()


def test_bqml_sql_and_methods():
    bq = _FakeBqClient()
    client = BigQueryMlClient(
        BqmlSettings(enabled=True, project="proj", dataset="sites", model="site_score"),
        client=bq,
    )
    predict_sql = client.predict_sql("site_score", "SELECT 1 AS foot_traffic;")
    assert "ML.PREDICT" in predict_sql
    assert "`proj.sites.site_score`" in predict_sql
    explain_sql = client.explain_predict_sql("site_score", "SELECT 1 AS foot_traffic")
    assert "ML.EXPLAIN_PREDICT" in explain_sql
    rows = client.predict("site_score", "SELECT 1 AS foot_traffic")
    assert rows[0]["predicted_label"] == 0.81
    assert "ML.PREDICT" in bq.last_sql
    models = client.list_models()
    assert models[0]["model_id"] == "site_score"
    detail = client.get_model("site_score")
    assert detail["feature_columns"] == ["foot_traffic"]


def test_bqml_factory_constructs_client(monkeypatch):
    created: dict[str, str] = {}

    class Client:
        def __init__(self, **kwargs):
            created.update(kwargs)

    cloud_bq = types.SimpleNamespace(Client=Client)
    cloud = types.SimpleNamespace(bigquery=cloud_bq)
    google = types.SimpleNamespace(cloud=cloud)
    monkeypatch.setitem(sys.modules, "google", google)
    monkeypatch.setitem(sys.modules, "google.cloud", cloud)
    monkeypatch.setitem(sys.modules, "google.cloud.bigquery", cloud_bq)

    client = make_bqml_client(
        Settings(bqml=BqmlSettings(enabled=True, project="proj", location="US", dataset="sites"))
    )
    assert client.enabled is True
    assert created["project"] == "proj"
    assert created["location"] == "US"


def test_registry_exposes_looker_and_bqml():
    reg = FactoryRegistry(Settings())
    assert reg.looker().enabled is False
    assert reg.bqml().enabled is False
