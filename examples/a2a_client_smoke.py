"""Call a peer A2A agent. Set A2A_ENABLED=true and A2A_PEER_URL."""

from __future__ import annotations

import asyncio
import os

from factories.a2a.client import send_text
from factories.a2a.factory import make_a2a_client


async def main() -> None:
    url = os.getenv("A2A_PEER_URL", "http://127.0.0.1:8000")
    client = await make_a2a_client(url)
    if client is None:
        raise SystemExit("A2A is disabled. Set A2A_ENABLED=true")
    try:
        print(await send_text(client, "Say hello in one sentence."))
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
