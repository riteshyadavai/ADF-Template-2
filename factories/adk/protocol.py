"""Google ADK runner protocol."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from google.adk.runners import Runner


class ADKRunner(ABC):
    """Vendor-neutral wrapper around a Google ADK ``Runner``."""

    @property
    @abstractmethod
    def runner(self) -> Runner:
        """Underlying ADK runner instance."""

    @property
    @abstractmethod
    def app_name(self) -> str:
        """Application name used for session scoping."""

    @abstractmethod
    async def ensure_session(self, user_id: str, session_id: str | None = None) -> str:
        """Create a session when missing and return its id."""

    @abstractmethod
    async def run_message(
        self,
        user_id: str,
        message: str,
        *,
        session_id: str | None = None,
    ) -> str:
        """Run a single user turn and return the final text response."""

    @abstractmethod
    def run_message_stream(
        self,
        user_id: str,
        message: str,
        *,
        session_id: str | None = None,
    ) -> Any:
        """Yield ADK events for a single user turn."""
