"""Ollama implementation of the shared LLM protocol."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from factories.llm.protocol import LLMClientProtocol


class OllamaLLMClient(LLMClientProtocol):
    def __init__(self, base_url: str, default_model: str, timeout_seconds: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._default_model = default_model
        self._timeout = httpx.Timeout(timeout_seconds)

    async def complete(self, messages: list[dict[str, str]], *, model: str = "") -> dict[str, Any]:
        selected_model = model or self._default_model
        payload = {"model": selected_model, "messages": messages, "stream": False}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(f"{self._base_url}/api/chat", json=payload)
            response.raise_for_status()
        body = response.json()
        return {
            "content": body.get("message", {}).get("content", ""),
            "model": body.get("model", selected_model),
            "usage": {
                "prompt_tokens": body.get("prompt_eval_count", 0),
                "completion_tokens": body.get("eval_count", 0),
            },
        }

    async def complete_stream(
        self, messages: list[dict[str, str]], *, model: str = ""
    ) -> AsyncIterator[str]:
        payload = {
            "model": model or self._default_model,
            "messages": messages,
            "stream": True,
        }
        async with (
            httpx.AsyncClient(timeout=self._timeout) as client,
            client.stream("POST", f"{self._base_url}/api/chat", json=payload) as response,
        ):
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                chunk = json.loads(line)
                content = chunk.get("message", {}).get("content", "")
                if content:
                    yield content

    async def health_check(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(f"{self._base_url}/api/version")
            response.raise_for_status()
        return {
            "status": "ok",
            "provider": "ollama",
            "version": response.json().get("version", "unknown"),
        }
