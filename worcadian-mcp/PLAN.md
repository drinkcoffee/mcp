# Plan: Worcadian MCP Service

## Goal

Build a Model Context Protocol (MCP) server, implemented with FastAPI, that wraps the
Worcadian JSON-RPC API (`https://worcadian.vercel.app/rpc`) and exposes three MCP tools.
The service deploys to Vercel as a Python ASGI serverless function.

## Upstream API (reference)

Spec: https://github.com/whatgamestudios/gameserver/blob/main/API.md

JSON-RPC 2.0 envelope over `POST https://worcadian.vercel.app/rpc`:

```json
{"jsonrpc": "2.0", "method": "<name>", "params": {}, "id": 1}
```

Methods used by this service:

| MCP tool         | JSON-RPC method   | Params                | Result                                                          |
|-------------------|-------------------|------------------------|------------------------------------------------------------------|
| `check_wordlist`   | `check`           | `{"words": [str, ...]}` | `{"WORD": true/false, ...}`                                     |
| `gameday`          | `gameday.current` | `{}`                    | `{"min_day": int, "max_day": int}`                              |
| `results`          | `board.results`   | `{"game_day": int}`     | `{"num_submissions", "best_score", "submissions": [...]}`       |

Verified live against the real endpoint during planning (`gameday.current` returned
`{"min_day": 84, "max_day": 85}` on 2026-06-23).

## Architecture decisions

- **Location**: new `worcadian-mcp/` subdirectory at the repo root, alongside any other
  example MCP servers (per user choice — repo stays a multi-example collection).
- **Framework**: FastAPI, per the request. The actual MCP protocol surface (tools,
  streamable HTTP transport) is provided by the official `mcp` Python SDK's `FastMCP`,
  and its ASGI app is mounted inside the FastAPI app — this satisfies "FastAPI service"
  while still being a spec-compliant MCP server reachable by MCP clients (Claude, Cursor,
  etc.) over HTTP.
- **Transport**: MCP Streamable HTTP, with `stateless_http=True`. Vercel functions are
  stateless/ephemeral between invocations and may run on different instances, so the
  session-persisting default mode is not viable; stateless mode is the documented option
  for serverless deployments.
- **Lifespan wiring**: Starlette does not automatically propagate a mounted sub-app's
  lifespan to the parent app. `FastMCP`'s streamable HTTP app requires its
  `session_manager.run()` context to be active (even in stateless mode) or it raises at
  request time. The FastAPI app's own `lifespan` is therefore wired to enter
  `mcp.session_manager.run()` directly. `mcp.streamable_http_app()` already serves its
  route at `/mcp` (FastMCP's default `streamable_http_path`), so it's mounted at the
  FastAPI app's root (`/`) rather than re-prefixed with `/mcp` again, avoiding a doubled
  `/mcp/mcp` path and the redirect that a mismatched trailing slash would otherwise cause.
- **DNS-rebinding protection must be disabled**: `FastMCP` auto-enables Host-header
  validation restricted to `localhost`/`127.0.0.1` whenever no `transport_security` is
  passed explicitly. That protection guards against browser-based DNS-rebinding attacks
  on a locally-running dev server — it doesn't apply to a server reached over the public
  internet via Vercel's domain, and left enabled it would reject every real request with
  a 421. `transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False)`
  is passed explicitly to `FastMCP` to avoid this. Verified by reproducing the 421 against
  a local `TestClient` before adding the fix.
- **Upstream client**: a small async `httpx`-based JSON-RPC client
  (`app/worcadian_client.py`) with one `call(method, params)` primitive and three typed
  wrapper methods, one per upstream method used. JSON-RPC `error` responses are raised as
  a `WorcadianRPCError(code, message)` exception, which MCP will surface as a tool error.
- **No authentication**: the upstream API is documented as having no auth requirements;
  none is added.

## File layout

```
worcadian-mcp/
  api/
    index.py            # Vercel entrypoint: imports and re-exports the FastAPI `app`
  app/
    __init__.py
    worcadian_client.py # JSON-RPC client + WorcadianRPCError
    mcp_server.py        # FastMCP instance + the 3 @mcp.tool() definitions
    server.py             # FastAPI app: lifespan wiring, mounts the MCP app, /healthz
  tests/
    __init__.py
    conftest.py
    test_worcadian_client.py   # unit tests, upstream HTTP mocked with respx
    test_mcp_tools.py           # tests calling the tool functions, upstream mocked
    manual_smoke_test.py        # optional script: hits the *real* upstream API directly
  requirements.txt       # fastapi, mcp, httpx
  requirements-dev.txt    # -r requirements.txt, pytest, pytest-asyncio, respx
  vercel.json
  README.md
  .gitignore
  PLAN.md (this file)
```

## Implementation steps

1. `app/worcadian_client.py` — `WorcadianClient` with `call()`, `check_words()`,
   `gameday_current()`, `board_results()`; `WorcadianRPCError` exception.
2. `app/mcp_server.py` — construct `FastMCP("worcadian", stateless_http=True,
   streamable_http_path="/")`, register the three tools, each a thin async wrapper
   around the client.
3. `app/server.py` — `FastAPI` app with a `lifespan` that runs
   `mcp.session_manager.run()`, a `GET /healthz` route, and
   `app.mount("/mcp", mcp.streamable_http_app())`.
4. `api/index.py` — `from app.server import app`.
5. `vercel.json` — route all requests to `api/index.py` via the Python ASGI runtime.
6. `requirements.txt` / `requirements-dev.txt`.
7. `tests/` — mocked unit tests for the client and tools, plus a manual smoke-test
   script that talks to the live upstream API (not run in CI by default).
8. `README.md` — what the service is, the tool table above, local dev instructions
   (`uvicorn app.server:app --reload`), how to point an MCP client at it, and how to
   deploy (`vercel deploy`).
9. `.gitignore` — Python + Vercel artifacts (`__pycache__/`, `.venv/`, `.vercel/`,
   `.env`, `.pytest_cache/`, etc.).

## Testing strategy

- Unit tests mock the upstream HTTP call (via `respx`) so they run offline and
  deterministically; they cover success and JSON-RPC error paths for all three tools.
- A separate manual/integration script is provided for hitting the real
  `https://worcadian.vercel.app/rpc` endpoint (and, once deployed, the live MCP
  endpoint) — useful for a human to sanity-check after deploying, not part of the
  automated suite.

## Deployment

- `vercel` CLI from `worcadian-mcp/` (Vercel project root = this subdirectory).
- No environment variables required (no auth on the upstream API).
- After deploy, the MCP endpoint is `https://<project>.vercel.app/mcp`, usable as an
  HTTP MCP server entry in Claude/Cursor MCP config.

## Out of scope

- The other upstream methods documented in `API.md` (`board.submit`, `analyse`,
  `checkin.*`, the 14 Numbers game, etc.) — only the three requested methods are
  wrapped.
- Caching, rate limiting, or auth in front of this service.
