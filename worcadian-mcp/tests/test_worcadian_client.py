import pytest
import respx
from httpx import Response

from app.worcadian_client import WORCADIAN_RPC_URL, WorcadianClient, WorcadianRPCError


@pytest.fixture
def client():
    return WorcadianClient()


@respx.mock
async def test_check_words_success(client):
    respx.post(WORCADIAN_RPC_URL).mock(
        return_value=Response(200, json={"jsonrpc": "2.0", "result": {"APPLE": True, "FIG": False}, "id": 1})
    )

    result = await client.check_words(["apple", "fig"])

    assert result == {"APPLE": True, "FIG": False}
    request = respx.calls.last.request
    assert request.url == WORCADIAN_RPC_URL
    import json

    body = json.loads(request.content)
    assert body["method"] == "check"
    assert body["params"] == {"words": ["apple", "fig"]}


@respx.mock
async def test_gameday_current_success(client):
    respx.post(WORCADIAN_RPC_URL).mock(
        return_value=Response(200, json={"jsonrpc": "2.0", "result": {"min_day": 84, "max_day": 85}, "id": 1})
    )

    result = await client.gameday_current()

    assert result == {"min_day": 84, "max_day": 85}


@respx.mock
async def test_board_results_success(client):
    expected = {
        "num_submissions": 5,
        "best_score": 18,
        "submissions": [{"player": "alice", "board": "x" * 121}],
    }
    respx.post(WORCADIAN_RPC_URL).mock(
        return_value=Response(200, json={"jsonrpc": "2.0", "result": expected, "id": 1})
    )

    result = await client.board_results(40)

    assert result == expected


@respx.mock
async def test_rpc_error_is_raised(client):
    respx.post(WORCADIAN_RPC_URL).mock(
        return_value=Response(
            200,
            json={"jsonrpc": "2.0", "error": {"code": -32602, "message": "Invalid params"}, "id": 1},
        )
    )

    with pytest.raises(WorcadianRPCError) as excinfo:
        await client.board_results(-1)

    assert excinfo.value.code == -32602
    assert excinfo.value.message == "Invalid params"
