"""Factory selection tests for optional reusable services."""

import pytest

from config.settings import Settings
from factories.adk.factory import make_adk_runner, make_default_llm_agent
from factories.eval.factory import make_eval_client
from factories.eval.local.client import LocalEvalClient
from factories.eval.protocol import EvalCase
from factories.guardrails.factory import make_content_guardrail
from factories.guardrails.passthrough.client import PassthroughGuardrail
from factories.llm.bedrock.client import BedrockLLMClient
from factories.llm.factory import make_llm_client
from factories.llm.ollama.client import OllamaLLMClient
from factories.observability.factory import configure_logfire, make_langfuse
from factories.observability.langfuse.client import LangfuseTracer
from factories.vectorstore.factory import make_vector_store
from factories.vectorstore.opensearch.client import OpenSearchVectorStore


def test_passthrough_guardrail_is_default():
    assert isinstance(make_content_guardrail(Settings()), PassthroughGuardrail)


def test_llm_factory_selects_ollama():
    settings = Settings(
        gateway={"provider": "ollama"},
        ollama={"base_url": "http://ollama.test", "model": "test-model"},
    )
    assert isinstance(make_llm_client(settings), OllamaLLMClient)


def test_llm_factory_selects_bedrock():
    settings = Settings(
        gateway={"provider": "bedrock"},
        bedrock={"region": "eu-west-1", "model_id": "test-model"},
    )
    assert isinstance(make_llm_client(settings), BedrockLLMClient)


def test_llm_factory_rejects_unknown_provider():
    settings = Settings(gateway={"provider": "unknown"})
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        make_llm_client(settings)


def test_adk_runner_is_disabled_by_default():
    agent = make_default_llm_agent(Settings())
    assert make_adk_runner(agent, Settings()) is None


def test_vector_store_factory_selects_opensearch():
    settings = Settings(
        vector_store={
            "backend": "opensearch",
            "opensearch_url": "https://search.test:9443",
        }
    )
    assert isinstance(make_vector_store(settings), OpenSearchVectorStore)


def test_logfire_is_disabled_by_default():
    assert configure_logfire(Settings()) is False


def test_langfuse_tracer_is_disabled_without_credentials():
    tracer = make_langfuse(Settings())
    assert isinstance(tracer, LangfuseTracer)
    assert tracer.enabled is False


def test_eval_factory_defaults_to_local():
    client = make_eval_client(Settings())
    assert isinstance(client, LocalEvalClient)
    assert client.backend == "local"


async def test_local_eval_scores_expected_overlap():
    client = make_eval_client(Settings(eval={"threshold": 0.5}))
    scores = await client.evaluate_case(
        EvalCase(
            input="What is 2+2?",
            actual_output="The answer is 4",
            expected_output="4",
        )
    )
    assert scores[0].passed is True


def test_eval_factory_rejects_unknown_backend():
    with pytest.raises(ValueError, match="Unsupported eval backend"):
        make_eval_client(Settings(eval={"backend": "unknown"}))
