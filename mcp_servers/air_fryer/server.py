#!/usr/bin/env python3
"""
Air Fryer MCP Server using FastMCP with HTTP (SSE) transport.

This server provides air fryer tools via HTTP protocol.
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastmcp import FastMCP

from mcp_servers.air_fryer.tools import register_resources, register_tools

# Create MCP instance
mcp = FastMCP("Air Fryer")

# Register all air fryer tools and resources
register_tools(mcp)
register_resources(mcp)

if __name__ == "__main__":
    # Run with SSE transport on HTTP
    print("🍟 Starting Air Fryer MCP Server on HTTP (SSE transport)")
    print("🌐 Server will be available at: http://localhost:8080/sse")
    print("📋 Available tools: cook")
    print("📚 Available resources: airfryer://recipes")
    print()
    
    # FastMCP runs with SSE transport for HTTP access
    mcp.run(transport="sse", host="localhost", port=8080)