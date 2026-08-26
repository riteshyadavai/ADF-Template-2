"""Tests for Langfuse tracer behavior."""

from config.settings import Settings
from factories.observability.langfuse.client import LangfuseTracer
from factories.observability.langfuse.factory import make_langfuse_tracer_for


def test_trace_generation_noops_when_disabled():
    tracer = LangfuseTracer(Settings().langfuse)
    tracer.trace_generation(
        run_id="run-1",
        model="test-model",
        prompt="hello",
        completion="world",
        token_usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    )


def test_callback_handler_returns_none_when_disabled():
    tracer = make_langfuse_tracer_for(Settings())
    assert tracer.get_callback_handler(trace_name="test") is None
