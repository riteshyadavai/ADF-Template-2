"""One-turn Google ADK smoke test (no HTTP). Set GOOGLE_API_KEY and ADK_ENABLED=true."""

from __future__ import annotations

import asyncio

from config.settings import Settings
from factories.adk.factory import make_adk_runner


async def main() -> None:
    settings = Settings(adk={"enabled": True})
    runner = make_adk_runner(settings=settings)
    if runner is None:
        raise SystemExit("ADK is disabled. Set ADK_ENABLED=true")
    text = await runner.run_turn("local-user", "Say hello in one sentence.")
    print(text)


if __name__ == "__main__":
    asyncio.run(main())
