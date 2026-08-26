"""Langfuse tracing client — LLM and agent observability."""

from __future__ import annotations

import importlib
from contextlib import contextmanager
from typing import Any

from config.settings import LangfuseSettings
from shared.logger import get_logger

log = get_logger(__name__)


class LangfuseTracer:
    """Wrapper for Langfuse tracing with LangChain/LangGraph callback support."""

    def __init__(self, settings: LangfuseSettings) -> None:
        self._settings = settings
        self.client: Any | None = None

        if not settings.enabled:
            log.info("langfuse_disabled")
            return
        if not settings.public_key or not settings.secret_key:
            log.info("langfuse_missing_credentials")
            return

        try:
            langfuse_module = importlib.import_module("langfuse")
            self.client = langfuse_module.Langfuse(
                public_key=settings.public_key.get_secret_value(),
                secret_key=settings.secret_key.get_secret_value(),
                host=settings.host,
                flush_at=settings.flush_at,
                flush_interval=settings.flush_interval,
                debug=settings.debug,
            )
            log.info("langfuse_initialized", host=settings.host)
        except ModuleNotFoundError:
            log.warning("langfuse_not_installed")
        except Exception as exc:
            log.error("langfuse_init_failed", error=str(exc))
            self.client = None

    @property
    def enabled(self) -> bool:
        return self.client is not None

    def get_callback_handler(
        self,
        *,
        trace_name: str | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        tags: list[str] | None = None,
    ) -> Any | None:
        if not self.client:
            return None
        try:
            callback_module = importlib.import_module("langfuse.langchain")
            return callback_module.CallbackHandler(
                trace_name=trace_name,
                user_id=user_id,
                session_id=session_id,
                metadata=metadata,
                tags=tags,
            )
        except Exception as exc:
            log.error("langfuse_callback_handler_failed", error=str(exc))
            return None

    @contextmanager
    def trace_langgraph_agent(
        self,
        name: str,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        tags: list[str] | None = None,
    ):
        handler = self.get_callback_handler(
            trace_name=name,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata,
            tags=tags,
        )
        yield None, handler

    @contextmanager
    def start_span(
        self,
        name: str,
        *,
        input_data: Any | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        if not self.client:
            yield None
            return
        try:
            with self.client.start_as_current_observation(
                name=name,
                as_type="span",
                input=input_data,
                metadata=metadata or {},
            ) as span:
                yield span
            self.client.flush()
        except Exception as exc:
            log.warning("langfuse_span_failed", error=str(exc))
            yield None

    def update_span(
        self,
        span: Any,
        *,
        output: Any | None = None,
        metadata: dict[str, Any] | None = None,
        level: str | None = None,
        status_message: str | None = None,
    ) -> None:
        if not span:
            return
        update: dict[str, Any] = {}
        if output is not None:
            update["output"] = output
        if metadata:
            update["metadata"] = metadata
        if level:
            update["level"] = level
        if status_message:
            update["status_message"] = status_message
        if update:
            span.update(**update)

    def trace_generation(
        self,
        *,
        run_id: str,
        model: str,
        prompt: str,
        completion: str,
        token_usage: dict[str, int],
        cost_usd: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        log.info(
            "llm_generation",
            run_id=run_id,
            model=model,
            token_usage=token_usage,
            cost_usd=cost_usd,
            metadata=metadata or {},
        )
        if not self.client:
            return
        try:
            with self.client.start_as_current_observation(
                name="llm_call",
                as_type="generation",
                model=model,
                input=prompt,
                metadata={"run_id": run_id, **(metadata or {})},
            ) as generation:
                generation.update(
                    output=completion,
                    usage_details={
                        "input": token_usage.get("prompt_tokens", 0),
                        "output": token_usage.get("completion_tokens", 0),
                        "total": token_usage.get("total_tokens", 0),
                    },
                )
            self.client.flush()
        except Exception as exc:
            log.warning("langfuse_generation_trace_failed", error=str(exc))

    def get_trace_id(self) -> str | None:
        if not self.client:
            return None
        try:
            return self.client.get_current_trace_id()
        except Exception as exc:
            log.warning("langfuse_trace_id_failed", error=str(exc))
            return None

    def submit_feedback(
        self,
        trace_id: str,
        score: float,
        *,
        name: str = "user-feedback",
        comment: str | None = None,
    ) -> bool:
        if not self.client:
            return False
        try:
            self.client.create_score(
                trace_id=trace_id,
                name=name,
                value=score,
                comment=comment,
            )
            return True
        except Exception as exc:
            log.warning("langfuse_feedback_failed", error=str(exc))
            return False

    def set_trace_user_session(self, user_id: str, session_id: str) -> None:
        if not self.client:
            return
        try:
            otel_trace = importlib.import_module("opentelemetry.trace")
            span = otel_trace.get_current_span()
            if span and span.is_recording():
                span.set_attribute("langfuse.user.id", user_id)
                span.set_attribute("langfuse.session.id", session_id)
        except Exception as exc:
            log.warning("langfuse_user_session_failed", error=str(exc))

    def flush(self) -> None:
        if self.client:
            try:
                self.client.flush()
            except Exception as exc:
                log.warning("langfuse_flush_failed", error=str(exc))

    def shutdown(self) -> None:
        if self.client:
            try:
                self.client.flush()
                self.client.shutdown()
            except Exception as exc:
                log.warning("langfuse_shutdown_failed", error=str(exc))
