#!/usr/bin/env python3
"""
DEPRECATED: This is a backwards compatibility wrapper.
Use mcp_servers/google_drive/server.py instead.

Simple Google Drive MCP Server

This server provides tools to interact with Google Drive using the Google Drive API.
It requires OAuth authentication via environment variables.
"""

import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and run the new Google Drive server
from mcp_servers.google_drive.server import mcp

if __name__ == "__main__":
    # FastMCP handles all the stdio server setup automatically
    mcp.run()