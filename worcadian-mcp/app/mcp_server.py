"""MCP tool definitions wrapping the Worcadian JSON-RPC API."""

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from app.worcadian_client import WorcadianClient

# FastMCP auto-enables DNS-rebinding Host-header protection restricted to
# localhost when no transport_security is given. This server is reached over
# the public internet (Vercel's domain), not localhost, so that protection
# must be explicitly disabled or every request would be rejected with a 421.
mcp = FastMCP(
    "worcadian",
    stateless_http=True,
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)

_client = WorcadianClient()


@mcp.tool()
async def check_wordlist(words: list[str]) -> dict[str, bool]:
    """Check whether each given word exists in the Worcadian dictionary.

    Maps to the upstream `check` JSON-RPC method.
    """
    return await _client.check_words(words)


@mcp.tool()
async def gameday() -> dict:
    """Get the current acceptable Worcadian game-day range.

    Maps to the upstream `gameday.current` JSON-RPC method.
    """
    return await _client.gameday_current()


@mcp.tool()
async def results(game_day: int) -> dict:
    """Get submission stats and winning boards for a Worcadian game day.

    Maps to the upstream `board.results` JSON-RPC method.
    """
    return await _client.board_results(game_day)
