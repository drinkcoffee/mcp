import pytest
import respx
from httpx import Response

from app.worcadian_client import WORCADIAN_RPC_URL
from app.mcp_server import check_wordlist, gameday, results


@respx.mock
async def test_check_wordlist_tool():
    respx.post(WORCADIAN_RPC_URL).mock(
        return_value=Response(200, json={"jsonrpc": "2.0", "result": {"APPLE": True}, "id": 1})
    )

    result = await check_wordlist(words=["apple"])

    assert result == {"APPLE": True}


@respx.mock
async def test_gameday_tool():
    respx.post(WORCADIAN_RPC_URL).mock(
        return_value=Response(200, json={"jsonrpc": "2.0", "result": {"min_day": 1, "max_day": 3}, "id": 1})
    )

    result = await gameday()

    assert result == {"min_day": 1, "max_day": 3}


@respx.mock
async def test_results_tool():
    expected = {"num_submissions": 0, "best_score": None, "submissions": []}
    respx.post(WORCADIAN_RPC_URL).mock(
        return_value=Response(200, json={"jsonrpc": "2.0", "result": expected, "id": 1})
    )

    result = await results(game_day=40)

    assert result == expected
