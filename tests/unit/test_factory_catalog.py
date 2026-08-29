"""Factory catalog tests."""

from cli.factory_catalog import get_backend, load_factory_catalog


def test_factory_catalog_has_core_capabilities():
    catalog = load_factory_catalog()
    ids = {c.id for c in catalog.capabilities}
    assert {"gateway", "cache", "vector", "adk", "a2a", "mcp", "secrets"} <= ids
    for cap in catalog.capabilities:
        assert cap.backends
        for backend in cap.backends:
            assert backend.status in {"implemented", "stub", "planned"}


def test_qdrant_is_implemented():
    assert get_backend("vector", "qdrant").status == "implemented"
    assert get_backend("vector", "qdrant").extra == "qdrant"
