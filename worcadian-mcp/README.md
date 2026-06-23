# Worcadian MCP Service

An [MCP](https://modelcontextprotocol.io) server, built with FastAPI, that wraps the
Worcadian JSON-RPC game server API (`https://worcadian.vercel.app/rpc`,
[spec](https://github.com/whatgamestudios/gameserver/blob/main/API.md)) as a set of MCP
tools. Designed to be deployed as a Python serverless function on Vercel.

## What it exposes

The service speaks MCP over Streamable HTTP at `/mcp`, with three tools:

| MCP tool         | Upstream JSON-RPC method | Arguments               | Returns                                                      |
|-------------------|----------------------------|---------------------------|------------------------------------------------------------------|
| `check_wordlist`   | `check`                     | `words: list[str]`         | `{"WORD": true/false, ...}`                                       |
| `gameday`          | `gameday.current`          | none                        | `{"min_day": int, "max_day": int}`                                |
| `results`          | `board.results`            | `game_day: int`             | `{"num_submissions", "best_score", "submissions": [...]}`        |

A plain `GET /healthz` route is also available for uptime checks.

## How it works

- [`app/worcadian_client.py`](app/worcadian_client.py) — a minimal async JSON-RPC client
  (`httpx`) for `https://worcadian.vercel.app/rpc`. Upstream `error` responses are raised
  as `WorcadianRPCError`.
- [`app/mcp_server.py`](app/mcp_server.py) — a `FastMCP` instance with the three tools
  above, each a thin wrapper around the client. Runs in `stateless_http` mode, since
  Vercel functions don't persist MCP session state between invocations, and with DNS
  rebinding protection explicitly disabled (that protection defaults to allowing only
  `localhost`/`127.0.0.1` Host headers, which would reject every request once deployed
  on a real domain).
- [`app/server.py`](app/server.py) — the FastAPI app. It mounts the MCP app (which
  already serves `/mcp` by default) at the root, and wires its `lifespan` to start/stop
  the MCP session manager (required even in stateless mode, and not handled
  automatically by Starlette's `Mount`).
- [`api/index.py`](api/index.py) — the Vercel entrypoint; re-exports the FastAPI `app`.

## Running locally

```bash
cd worcadian-mcp
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.server:app --reload
```

The MCP endpoint is then available at `http://127.0.0.1:8000/mcp`. Point an MCP client
(Claude, Cursor, etc.) at that URL using its HTTP/Streamable-HTTP MCP server transport.

## Testing

```bash
pip install -r requirements-dev.txt
pytest
```

Unit tests in `tests/test_worcadian_client.py` and `tests/test_mcp_tools.py` mock the
upstream HTTP call (via `respx`), so they run offline.

`tests/manual_smoke_test.py` is not part of the automated suite — it makes real calls to
the live Worcadian API (and optionally a deployed instance of this service) for a quick
human sanity check:

```bash
python tests/manual_smoke_test.py
# or, against a deployed MCP server:
MCP_BASE_URL=https://your-deployment.vercel.app python tests/manual_smoke_test.py
```

## Deploying to Vercel

```bash
cd worcadian-mcp
vercel deploy
```

`vercel.json` routes all requests to `api/index.py` via the Python ASGI runtime. No
environment variables are required — the upstream API has no authentication.

After deploying, the MCP endpoint is `https://<your-project>.vercel.app/mcp`.

## Out of scope

Only the three methods above are wrapped. The upstream API documents several other
methods (`board.submit`, `analyse`, `seedwords.check`, `checkin.*`, the 14 Numbers game,
etc.) that are not exposed by this service.
