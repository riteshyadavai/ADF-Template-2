"""Qdrant, sqlite state, ADK app, A2A executor tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI

from agents.memory import WorkflowStateRecord
from config.settings import Settings
from factories.a2a.executor import OrchestratorAgentExecutor
from factories.a2a.mount import mount_a2a
from factories.a2a.protocol import A2AServerBundle
from factories.adk.app import make_adk_app
from factories.database.factory import make_cold_state_store, make_hot_state_store
from factories.vectorstore.factory import make_vector_store


def test_make_adk_app_has_root_agent():
    settings = Settings(adk={"app_name": "test-app", "agent_name": "tester"})
    app = make_adk_app(settings)
    assert app.name == "test-app"
    assert app.root_agent.name == "tester"


@pytest.mark.asyncio
async def test_orchestrator_executor_uses_run_query():
    async def run_query(text: str) -> str:
        return f"echo:{text}"

    executor = OrchestratorAgentExecutor(run_query)
    context = MagicMock()
    context.get_user_input.return_value = "hi"
    queue = MagicMock()
    queue.enqueue_event = AsyncMock()
    await executor.execute(context, queue)
    queue.enqueue_event.assert_awaited()


def test_mount_a2a_appends_routes():
    app = FastAPI()
    bundle = A2AServerBundle(agent_card=MagicMock(), request_handler=MagicMock(), routes=[])
    mount_a2a(app, bundle)


@pytest.mark.asyncio
async def test_sqlite_hot_state(tmp_path: Path):
    url = f"sqlite+aiosqlite:///{tmp_path / 'hot.db'}"
    store = make_hot_state_store(Settings(database={"backend": "sqlite", "hot_url": url}))
    record = WorkflowStateRecord(run_id="r1", tenant_id="t", state={"x": 1})
    await store.save(record)
    loaded = await store.get("r1")
    assert loaded is not None
    assert loaded.state["x"] == 1
    cold = make_cold_state_store(Settings(database={"backend": "sqlite", "cold_url": url}))
    await cold.append_history("r1", {"ok": True})
    assert await cold.get_history("r1") == [{"ok": True}]


def test_qdrant_factory_constructs_with_mock():
    try:
        import qdrant_client  # noqa: F401
    except ModuleNotFoundError:
        with pytest.raises(RuntimeError, match="qdrant"):
            make_vector_store(
                Settings(vector_store={"backend": "qdrant", "qdrant_url": "http://qdrant.test"})
            )
        return
    fake_client = MagicMock()
    with patch("qdrant_client.AsyncQdrantClient", return_value=fake_client):
        store = make_vector_store(
            Settings(vector_store={"backend": "qdrant", "qdrant_url": "http://qdrant.test"})
        )
    assert store.url == "http://qdrant.test"


def test_pgvector_is_planned():
    with pytest.raises(NotImplementedError):
        make_vector_store(Settings(vector_store={"backend": "pgvector"}))
