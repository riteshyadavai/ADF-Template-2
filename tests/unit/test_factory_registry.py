"""Factory registry composition tests."""

from factories.registry import FactoryRegistry, get_factory_registry


def test_factory_registry_exposes_all_services():
    reg = FactoryRegistry()
    assert reg.ai_gateway() is not None
    assert reg.cache() is not None
    assert reg.vector_store() is not None
    assert reg.embeddings() is not None
    assert reg.llm() is not None
    assert reg.observability() is not None
    assert reg.langfuse() is not None
    assert reg.langfuse().enabled is False
    assert reg.content_guardrail() is not None
    assert reg.document_parser() is not None
    assert reg.eval().backend == "local"
    assert reg.mcp() is not None
    assert reg.secrets().get_secret("MISSING_FACTORY_SECRET") is None
    assert reg.looker().enabled is False
    assert reg.bqml().enabled is False
    assert reg.assets().enabled is False


def test_factory_registry_singleton():
    assert get_factory_registry() is get_factory_registry()
