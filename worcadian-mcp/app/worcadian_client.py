"""Async JSON-RPC client for the Worcadian game server API."""

import itertools

import httpx

WORCADIAN_RPC_URL = "https://worcadian.vercel.app/rpc"


class WorcadianRPCError(Exception):
    """Raised when the upstream JSON-RPC API returns an error response."""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"Worcadian RPC error {code}: {message}")


class WorcadianClient:
    def __init__(self, base_url: str = WORCADIAN_RPC_URL, timeout: float = 10.0):
        self._base_url = base_url
        self._timeout = timeout
        self._ids = itertools.count(1)

    async def call(self, method: str, params: dict | None = None) -> dict:
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": next(self._ids),
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(self._base_url, json=payload)
        response.raise_for_status()
        body = response.json()
        if "error" in body:
            error = body["error"]
            raise WorcadianRPCError(error.get("code", -32603), error.get("message", "Unknown error"))
        return body["result"]

    async def check_words(self, words: list[str]) -> dict[str, bool]:
        return await self.call("check", {"words": words})

    async def gameday_current(self) -> dict:
        return await self.call("gameday.current", {})

    async def board_results(self, game_day: int) -> dict:
        return await self.call("board.results", {"game_day": game_day})
