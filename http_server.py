"""
HTTP version of the MCP server using Server-Sent Events transport.

Same calculator tools as the stdio server, but accessible via HTTP.
"""

from fastmcp import FastMCP
from mcp_tools import register_tools, register_prompts
from mcp.server.sse import sse_server
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse

# Create the FastMCP server instance
mcp = FastMCP("simple-calculator")

# Register all tools and prompts (shared with stdio server)
register_tools(mcp)
register_prompts(mcp)


# HTTP transport wrapper
async def handle_sse(request):
    """Handle Server-Sent Events connections for MCP."""
    async with sse_server() as (read, write):
        await mcp.run(read, write, mcp.create_initialization_options())


async def health_check(request):
    """Health check endpoint."""
    return JSONResponse({"status": "healthy", "server": "simple-calculator"})


# Create web application
routes = [
    Route("/sse", endpoint=handle_sse),  # MCP endpoint
    Route("/health", endpoint=health_check),  # Health check
]

app = Starlette(routes=routes)


if __name__ == "__main__":
    import uvicorn
    
    print("🌐 Starting HTTP MCP Server...")
    print("📡 Server available at: http://localhost:8000/sse")
    print("🔍 Health check at: http://localhost:8000/health")
    print("💡 Same server logic as server.py, just HTTP transport!")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)