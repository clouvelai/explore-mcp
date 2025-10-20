#!/usr/bin/env python3
"""
Google Drive MCP Server using FastMCP.

This server provides tools to interact with Google Drive using the Google Drive API.
It requires OAuth authentication via environment variables.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastmcp import FastMCP
from mcp_servers.google_drive.tools import register_tools

# Create MCP instance
mcp = FastMCP("Google Drive")

# Register all Google Drive tools
register_tools(mcp)

if __name__ == "__main__":
    # FastMCP handles all the stdio server setup automatically
    mcp.run()