"""FastAPI application exposing the Worcadian MCP server over Streamable HTTP."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.mcp_server import mcp

mcp_asgi_app = mcp.streamable_http_app()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp.session_manager.run():
        yield


app = FastAPI(title="Worcadian MCP Service", lifespan=lifespan)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


# mcp_asgi_app already serves its route at /mcp (FastMCP's default
# streamable_http_path), so it's mounted at the root to avoid a doubled
# /mcp/mcp path. The /healthz route above takes precedence since it's
# registered first.
app.mount("/", mcp_asgi_app)
