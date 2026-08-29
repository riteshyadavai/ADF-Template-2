"""Default A2A executor that forwards user text to the platform orchestrator."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from uuid import uuid4

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue_v2 import EventQueue
from a2a.types import Message, Part

RunQuery = Callable[[str], Awaitable[str]]


class OrchestratorAgentExecutor(AgentExecutor):
    def __init__(self, run_query: RunQuery) -> None:
        self._run_query = run_query

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        query = context.get_user_input()
        result = await self._run_query(query)
        part = Part()
        part.text = result
        message = Message()
        message.message_id = str(uuid4())
        message.parts.append(part)
        await event_queue.enqueue_event(message)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        return None
