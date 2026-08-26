"""In-memory Google ADK runner."""

from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import uuid4

from google.adk.events.event import Event
from google.adk.runners import InMemoryRunner, Runner
from google.genai import types

from factories.adk.protocol import ADKRunner


class InMemoryADKRunner(ADKRunner):
    def __init__(self, runner: InMemoryRunner, *, app_name: str) -> None:
        self._runner = runner
        self._app_name = app_name

    @property
    def runner(self) -> Runner:
        return self._runner

    @property
    def app_name(self) -> str:
        return self._app_name

    async def ensure_session(self, user_id: str, session_id: str | None = None) -> str:
        resolved = session_id or str(uuid4())
        existing = await self._runner.session_service.get_session(
            app_name=self._app_name,
            user_id=user_id,
            session_id=resolved,
        )
        if existing is None:
            session = await self._runner.session_service.create_session(
                app_name=self._app_name,
                user_id=user_id,
                session_id=resolved,
            )
            return session.id
        return existing.id

    async def run_message(
        self,
        user_id: str,
        message: str,
        *,
        session_id: str | None = None,
    ) -> str:
        parts: list[str] = []
        async for event in self.run_message_stream(
            user_id=user_id,
            message=message,
            session_id=session_id,
        ):
            text = _event_text(event)
            if text:
                parts.append(text)
        return parts[-1] if parts else ""

    async def run_message_stream(
        self,
        user_id: str,
        message: str,
        *,
        session_id: str | None = None,
    ) -> AsyncIterator[Event]:
        resolved_session_id = await self.ensure_session(user_id, session_id)
        async for event in self._runner.run_async(
            user_id=user_id,
            session_id=resolved_session_id,
            new_message=types.Content(
                role="user",
                parts=[types.Part(text=message)],
            ),
        ):
            yield event


def _event_text(event: Event) -> str | None:
    content = getattr(event, "content", None)
    if content is None or not content.parts:
        return None
    texts = [part.text for part in content.parts if getattr(part, "text", None)]
    if not texts:
        return None
    return "".join(texts)
