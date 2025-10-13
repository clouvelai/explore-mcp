#!/usr/bin/env python3
"""
Gmail MCP Server

This server provides tools to interact with Gmail using the Gmail API.
It requires OAuth authentication via environment variables.
"""

from fastmcp import FastMCP
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from mcp_servers.gmail.tools import register_tools

# Create the FastMCP server instance
mcp = FastMCP("gmail")

# Register all tools
register_tools(mcp)

if __name__ == "__main__":
    # FastMCP handles all the stdio server setup automatically
    mcp.run()