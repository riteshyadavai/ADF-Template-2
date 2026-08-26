"""Observability bundle protocol."""

from __future__ import annotations

from dataclasses import dataclass

from factories.observability.langfuse.client import LangfuseTracer


@dataclass
class ObservabilityBundle:
    logger: object
    langfuse: LangfuseTracer

    @property
    def llm_tracer(self) -> LangfuseTracer:
        return self.langfuse
