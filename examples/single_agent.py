"""Run a single orchestrator turn (no HTTP)."""

from __future__ import annotations

import asyncio

from app.platform import Platform
from shared.schemas import AgentRequest


async def main() -> None:
    platform = Platform()
    response = await platform.orchestrator.run(
        AgentRequest(query="Say hello in one sentence.", tenant_id="demo")
    )
    print(response.output)


if __name__ == "__main__":
    asyncio.run(main())
