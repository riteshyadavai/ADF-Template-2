"""LLM client factory."""

from __future__ import annotations

from config.settings import Settings, get_settings
from factories.llm.bedrock.client import BedrockLLMClient
from factories.llm.ollama.client import OllamaLLMClient
from factories.llm.openai.client import OpenAILLMClient
from factories.llm.protocol import LLMClientProtocol


def make_llm_client(settings: Settings | None = None) -> LLMClientProtocol:
    settings = settings or get_settings()
    provider = settings.gateway.provider
    if provider in ("litellm", "openai"):
        return OpenAILLMClient()
    if provider == "bedrock":
        return BedrockLLMClient(
            region=settings.bedrock.region,
            default_model=settings.bedrock.model_id,
        )
    if provider == "ollama":
        return OllamaLLMClient(
            base_url=settings.ollama.base_url,
            default_model=settings.ollama.model,
            timeout_seconds=settings.ollama.timeout_seconds,
        )
    raise ValueError(f"Unsupported LLM provider: {provider}")
