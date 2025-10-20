#!/usr/bin/env python3
"""
Auto-generated Mock MCP Server
"""

import logging
import sys

# Suppress output to avoid MCP protocol issues
logging.basicConfig(level=logging.CRITICAL, stream=sys.stderr)
logging.getLogger().setLevel(logging.CRITICAL)

from fastmcp import FastMCP
from tools import register_tools

# Create mock server instance
mcp = FastMCP("mock-server")

# Register all tools
register_tools(mcp)

if __name__ == "__main__":
    # Run the server
    mcp.run(show_banner=False)
