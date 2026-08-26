"""Agent2Agent (A2A) protocol abstractions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from a2a.client.client import Client
    from a2a.server.request_handlers import DefaultRequestHandler
    from a2a.types import AgentCard, SendMessageRequest
    from starlette.routing import BaseRoute


@dataclass(frozen=True)
class A2AServerBundle:
    """Routes and handler wiring for exposing an A2A agent over HTTP."""

    agent_card: AgentCard
    request_handler: DefaultRequestHandler
    routes: Sequence[BaseRoute]


class A2AClientProtocol(ABC):
    """Client for calling remote A2A agents."""

    @property
    @abstractmethod
    def client(self) -> Client:
        """Underlying A2A SDK client."""

    @abstractmethod
    def send_message(self, request: SendMessageRequest) -> AsyncIterator[Any]:
        """Stream A2A events for a send-message request."""

    @abstractmethod
    async def aclose(self) -> None:
        """Release transport resources."""
