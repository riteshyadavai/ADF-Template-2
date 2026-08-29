"""SQLAlchemy async hot/cold state stores."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import Column, Float, String, Text, select
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from agents.memory import ColdStateStore, HotStateStore, WorkflowStateRecord


class Base(DeclarativeBase):
    pass


class HotRow(Base):
    __tablename__ = "hot_state"
    run_id = Column(String, primary_key=True)
    payload = Column(Text, nullable=False)


class HistoryRow(Base):
    __tablename__ = "cold_history"
    id = Column(String, primary_key=True)
    run_id = Column(String, index=True, nullable=False)
    event = Column(Text, nullable=False)


class EvalRow(Base):
    __tablename__ = "cold_evals"
    id = Column(String, primary_key=True)
    run_id = Column(String, index=True, nullable=False)
    git_sha = Column(String, nullable=False)
    prompt_version = Column(String, nullable=False)
    model_version = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    metadata_json = Column(Text, nullable=False)


def _engine(url: str) -> AsyncEngine:
    return create_async_engine(url)


class SqliteHotStateStore(HotStateStore):
    def __init__(self, url: str) -> None:
        self._engine = _engine(url)
        self._sessions = async_sessionmaker(self._engine, expire_on_commit=False)
        self._ready = False

    async def _ensure(self) -> None:
        if self._ready:
            return
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self._ready = True

    async def get(self, run_id: str) -> WorkflowStateRecord | None:
        await self._ensure()
        async with self._sessions() as session:
            row = await session.get(HotRow, run_id)
            if row is None:
                return None
            return WorkflowStateRecord.model_validate(json.loads(row.payload))

    async def save(self, record: WorkflowStateRecord) -> None:
        await self._ensure()
        async with self._sessions() as session:
            await session.merge(HotRow(run_id=record.run_id, payload=record.model_dump_json()))
            await session.commit()

    async def delete(self, run_id: str) -> None:
        await self._ensure()
        async with self._sessions() as session:
            row = await session.get(HotRow, run_id)
            if row is not None:
                await session.delete(row)
                await session.commit()


class SqliteColdStateStore(ColdStateStore):
    def __init__(self, url: str) -> None:
        self._engine = _engine(url)
        self._sessions = async_sessionmaker(self._engine, expire_on_commit=False)
        self._ready = False

    async def _ensure(self) -> None:
        if self._ready:
            return
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self._ready = True

    async def append_history(self, run_id: str, event: dict[str, Any]) -> None:
        from uuid import uuid4

        await self._ensure()
        async with self._sessions() as session:
            session.add(HistoryRow(id=str(uuid4()), run_id=run_id, event=json.dumps(event)))
            await session.commit()

    async def get_history(self, run_id: str) -> list[dict[str, Any]]:
        await self._ensure()
        async with self._sessions() as session:
            result = await session.execute(select(HistoryRow).where(HistoryRow.run_id == run_id))
            return [json.loads(row.event) for row in result.scalars()]

    async def save_eval_result(
        self,
        *,
        run_id: str,
        git_sha: str,
        prompt_version: str,
        model_version: str,
        score: float,
        metadata: dict[str, Any],
    ) -> None:
        from uuid import uuid4

        await self._ensure()
        async with self._sessions() as session:
            session.add(
                EvalRow(
                    id=str(uuid4()),
                    run_id=run_id,
                    git_sha=git_sha,
                    prompt_version=prompt_version,
                    model_version=model_version,
                    score=score,
                    metadata_json=json.dumps(metadata),
                )
            )
            await session.commit()
