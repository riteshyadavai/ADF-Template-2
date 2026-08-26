"""AWS Bedrock implementation of the shared LLM protocol."""

from __future__ import annotations

import asyncio
import importlib
from collections.abc import AsyncIterator
from typing import Any

from factories.llm.protocol import LLMClientProtocol


class BedrockLLMClient(LLMClientProtocol):
    def __init__(self, region: str, default_model: str) -> None:
        self._region = region
        self._default_model = default_model
        self._client: Any | None = None

    def _runtime_client(self) -> Any:
        if self._client is None:
            try:
                boto3 = importlib.import_module("boto3")
            except ModuleNotFoundError as exc:
                raise RuntimeError(
                    "The Bedrock backend requires the optional 'aws' dependencies. "
                    "Install them with: uv sync --extra aws"
                ) from exc
            self._client = boto3.client("bedrock-runtime", region_name=self._region)
        return self._client

    @staticmethod
    def _bedrock_messages(
        messages: list[dict[str, str]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
        system: list[dict[str, str]] = []
        converted: list[dict[str, Any]] = []
        for message in messages:
            if message["role"] == "system":
                system.append({"text": message["content"]})
                continue
            role = "assistant" if message["role"] == "assistant" else "user"
            converted.append({"role": role, "content": [{"text": message["content"]}]})
        return converted, system

    async def complete(self, messages: list[dict[str, str]], *, model: str = "") -> dict[str, Any]:
        selected_model = model or self._default_model
        converted, system = self._bedrock_messages(messages)

        def invoke() -> dict[str, Any]:
            kwargs: dict[str, Any] = {"modelId": selected_model, "messages": converted}
            if system:
                kwargs["system"] = system
            return self._runtime_client().converse(**kwargs)

        response = await asyncio.to_thread(invoke)
        content = "".join(
            block.get("text", "")
            for block in response.get("output", {}).get("message", {}).get("content", [])
        )
        usage = response.get("usage", {})
        return {
            "content": content,
            "model": selected_model,
            "usage": {
                "prompt_tokens": usage.get("inputTokens", 0),
                "completion_tokens": usage.get("outputTokens", 0),
            },
        }

    async def complete_stream(
        self, messages: list[dict[str, str]], *, model: str = ""
    ) -> AsyncIterator[str]:
        selected_model = model or self._default_model
        converted, system = self._bedrock_messages(messages)

        def collect() -> list[str]:
            kwargs: dict[str, Any] = {"modelId": selected_model, "messages": converted}
            if system:
                kwargs["system"] = system
            response = self._runtime_client().converse_stream(**kwargs)
            return [
                event["contentBlockDelta"]["delta"]["text"]
                for event in response.get("stream", [])
                if event.get("contentBlockDelta", {}).get("delta", {}).get("text")
            ]

        for token in await asyncio.to_thread(collect):
            yield token

    async def health_check(self) -> dict[str, Any]:
        def check() -> None:
            self._runtime_client().converse(
                modelId=self._default_model,
                messages=[{"role": "user", "content": [{"text": "ping"}]}],
                inferenceConfig={"maxTokens": 1},
            )

        await asyncio.to_thread(check)
        return {"status": "ok", "provider": "bedrock", "region": self._region}
