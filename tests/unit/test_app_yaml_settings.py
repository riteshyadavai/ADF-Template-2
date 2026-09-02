"""app.yaml is loaded by Settings (env still wins)."""

import os
from pathlib import Path

from config.settings import get_settings, load_app_yaml


def test_load_app_yaml_maps_vector_and_observability(tmp_path: Path, monkeypatch):
    config = tmp_path / "config"
    config.mkdir()
    (config / "app.yaml").write_text(
        "cache:\n  backend: redis\n"
        "vector:\n  backend: qdrant\n"
        "observability:\n  langfuse: false\n  logfire: true\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("config.settings.PROJECT_ROOT", tmp_path)
    data = load_app_yaml(tmp_path)
    assert data["cache"]["backend"] == "redis"
    assert data["vector_store"]["backend"] == "qdrant"
    assert data["langfuse"]["enabled"] is False
    assert data["logfire"]["enabled"] is True


def test_load_app_yaml_nested_langfuse(tmp_path: Path, monkeypatch):
    config = tmp_path / "config"
    config.mkdir()
    (config / "app.yaml").write_text(
        "observability:\n"
        "  langfuse:\n    enabled: false\n    host: https://example.com\n"
        "  logfire:\n    enabled: true\n    service_name: demo\n"
        "  otel_endpoint: http://localhost:4318\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("config.settings.PROJECT_ROOT", tmp_path)
    data = load_app_yaml(tmp_path)
    assert data["langfuse"]["enabled"] is False
    assert data["langfuse"]["host"] == "https://example.com"
    assert data["logfire"]["service_name"] == "demo"
    assert data["observability"]["otel_endpoint"] == "http://localhost:4318"


def test_get_settings_reads_app_yaml(tmp_path: Path, monkeypatch):
    config = tmp_path / "config"
    config.mkdir()
    (config / "app.yaml").write_text("cache:\n  backend: redis\n", encoding="utf-8")
    monkeypatch.setattr("config.settings.PROJECT_ROOT", tmp_path)
    monkeypatch.delenv("CACHE_BACKEND", raising=False)
    get_settings.cache_clear()
    try:
        assert get_settings().cache.backend == "redis"
    finally:
        get_settings.cache_clear()


def test_factory_registry_uses_app_yaml_cache(tmp_path: Path, monkeypatch):
    from factories.cache.redis.client import RedisCacheProvider
    from factories.registry import FactoryRegistry

    config = tmp_path / "config"
    config.mkdir()
    (config / "app.yaml").write_text("cache:\n  backend: redis\n", encoding="utf-8")
    monkeypatch.setattr("config.settings.PROJECT_ROOT", tmp_path)
    monkeypatch.delenv("CACHE_BACKEND", raising=False)
    get_settings.cache_clear()
    try:
        reg = FactoryRegistry(get_settings())
        assert isinstance(reg.cache(), RedisCacheProvider)
    finally:
        get_settings.cache_clear()


def test_env_overrides_app_yaml(tmp_path: Path, monkeypatch):
    config = tmp_path / "config"
    config.mkdir()
    (config / "app.yaml").write_text("cache:\n  backend: redis\n", encoding="utf-8")
    monkeypatch.setattr("config.settings.PROJECT_ROOT", tmp_path)
    monkeypatch.setenv("CACHE_BACKEND", "memory")
    get_settings.cache_clear()
    try:
        assert get_settings().cache.backend == "memory"
    finally:
        get_settings.cache_clear()
        os.environ.pop("CACHE_BACKEND", None)
