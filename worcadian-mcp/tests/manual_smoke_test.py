"""Manual smoke test — makes real network calls. Not run by pytest/CI.

Exercises the live Worcadian upstream API directly via WorcadianClient. If
MCP_BASE_URL is set, also calls a deployed instance of this service's MCP
endpoint to confirm it's reachable end-to-end.

Usage:
    python tests/manual_smoke_test.py
    MCP_BASE_URL=https://your-deployment.vercel.app python tests/manual_smoke_test.py
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.worcadian_client import WorcadianClient  # noqa: E402


async def check_upstream():
    client = WorcadianClient()
    day_range = await client.gameday_current()
    print(f"gameday.current -> {day_range}")

    checked = await client.check_words(["apple", "zzzzzqx"])
    print(f"check -> {checked}")

    game_day = day_range["min_day"]
    board = await client.board_results(game_day)
    print(f"board.results({game_day}) -> {board}")


async def check_deployed_mcp_server(base_url: str):
    import httpx

    async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as http_client:
        response = await http_client.get("/healthz")
        response.raise_for_status()
        print(f"GET /healthz -> {response.json()}")


async def main():
    await check_upstream()

    base_url = os.environ.get("MCP_BASE_URL")
    if base_url:
        await check_deployed_mcp_server(base_url)


if __name__ == "__main__":
    asyncio.run(main())
