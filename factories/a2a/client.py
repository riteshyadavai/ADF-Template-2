"""A2A client wrapper."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import httpx
from a2a.client import Client, ClientConfig, create_client
from a2a.types import SendMessageRequest

from factories.a2a.protocol import A2AClientProtocol


class A2AClient(A2AClientProtocol):
    def __init__(
        self,
        client: Client,
        *,
        owns_http_client: bool = False,
        httpx_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._client = client
        self._owns_http_client = owns_http_client
        self._httpx_client = httpx_client

    @property
    def client(self) -> Client:
        return self._client

    def send_message(self, request: SendMessageRequest) -> AsyncIterator[Any]:
        return self._client.send_message(request)

    async def aclose(self) -> None:
        if self._owns_http_client and self._httpx_client is not None:
            await self._httpx_client.aclose()


async def connect_a2a_client(
    agent_url: str,
    *,
    client_config: ClientConfig | None = None,
    httpx_client: httpx.AsyncClient | None = None,
) -> A2AClient:
    """Resolve an agent card from ``agent_url`` and return a connected client."""
    owns_http = httpx_client is None
    http = httpx_client or httpx.AsyncClient()
    client = await create_client(agent_url, client_config=client_config)
    return A2AClient(client, owns_http_client=owns_http, httpx_client=http)
