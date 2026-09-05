"""Asset Factory bundle tests (mocked enterprise_agent_sdk)."""

from __future__ import annotations

import importlib.util
import os
import sqlite3
import sys
import tempfile
import types

import pytest

from config.settings import AssetsSettings, Settings
from factories.assets.factory import make_asset_bundle
from factories.assets.protocol import AssetsConfigError, AssetsDisabledError
from factories.registry import FactoryRegistry


class _FakeAsset:
    def __init__(self) -> None:
        self.hydrated: dict | None = None

    def hydrate(self, config: dict) -> _FakeAsset:
        self.hydrated = config
        return self

    def safe_run(self, **kwargs):
        return types.SimpleNamespace(status="success", data=kwargs, to_dict=lambda: kwargs)


def _install_fake_sdk(monkeypatch: pytest.MonkeyPatch) -> dict[str, _FakeAsset]:
    tools = {
        "AnySQLSafeExecutor": _FakeAsset(),
        "DynamicOpenAPIClient": _FakeAsset(),
        "HITLApprovalGateway": _FakeAsset(),
        "OmniChannelDocumentCrawler": _FakeAsset(),
        "PIIToxicContentShield": _FakeAsset(),
        "ZeroCodeVectorSyncNode": _FakeAsset(),
    }

    def ctor(name: str):
        def _make() -> _FakeAsset:
            return tools[name]

        return _make

    assets_mod = types.SimpleNamespace(
        AnySQLSafeExecutor=ctor("AnySQLSafeExecutor"),
        DynamicOpenAPIClient=ctor("DynamicOpenAPIClient"),
        HITLApprovalGateway=ctor("HITLApprovalGateway"),
        OmniChannelDocumentCrawler=ctor("OmniChannelDocumentCrawler"),
        PIIToxicContentShield=ctor("PIIToxicContentShield"),
        ZeroCodeVectorSyncNode=ctor("ZeroCodeVectorSyncNode"),
    )
    pkg = types.SimpleNamespace(assets=assets_mod)
    monkeypatch.setitem(sys.modules, "enterprise_agent_sdk", pkg)
    monkeypatch.setitem(sys.modules, "enterprise_agent_sdk.assets", assets_mod)
    return tools


def test_assets_disabled_raises():
    bundle = make_asset_bundle(Settings(assets=AssetsSettings(enabled=False)))
    assert bundle.enabled is False
    with pytest.raises(AssetsDisabledError):
        bundle.sql()


def test_assets_sql_missing_url(monkeypatch):
    _install_fake_sdk(monkeypatch)
    bundle = make_asset_bundle(Settings(assets=AssetsSettings(enabled=True)))
    with pytest.raises(AssetsConfigError):
        bundle.sql()


def test_assets_hydrate_sql_and_pii(monkeypatch):
    tools = _install_fake_sdk(monkeypatch)
    bundle = make_asset_bundle(
        Settings(
            assets=AssetsSettings(
                enabled=True,
                sql_db_url="sqlite:///./app.db",
                sql_read_only=True,
                sql_max_rows=10,
                sql_allowed_tables=["orders"],
            )
        )
    )
    assert bundle.enabled is True
    sql = bundle.sql()
    assert tools["AnySQLSafeExecutor"].hydrated == {
        "db_url": "sqlite:///./app.db",
        "read_only": True,
        "max_rows": 10,
        "allowed_tables": ["orders"],
    }
    assert sql.safe_run(query="SELECT 1").status == "success"
    assert bundle.pii() is tools["PIIToxicContentShield"]


def test_assets_rejects_stub_vector_provider(monkeypatch):
    _install_fake_sdk(monkeypatch)
    with pytest.raises(AssetsConfigError, match="memory"):
        make_asset_bundle(Settings(assets=AssetsSettings(enabled=True, vector_provider="qdrant")))


def test_registry_exposes_assets():
    assert FactoryRegistry(Settings()).assets().enabled is False


@pytest.mark.skipif(
    importlib.util.find_spec("enterprise_agent_sdk") is None,
    reason="enterprise-agent-sdk not installed",
)
def test_sqlite_sql_asset_when_sdk_present():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE t (id INTEGER)")
    conn.execute("INSERT INTO t VALUES (1)")
    conn.commit()
    conn.close()
    bundle = make_asset_bundle(
        Settings(
            assets=AssetsSettings(
                enabled=True,
                sql_db_url=f"sqlite:///{path}",
                sql_read_only=True,
            )
        )
    )
    result = bundle.sql().safe_run(query="SELECT * FROM t")
    status = result.status.value if hasattr(result.status, "value") else result.status
    assert status == "success"
    os.remove(path)
