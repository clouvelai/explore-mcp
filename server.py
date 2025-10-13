#!/usr/bin/env python3
"""
DEPRECATED: This is a backwards compatibility wrapper.
Use mcp_servers/calculator/server.py instead.

Simple MCP Server with calculator tools using FastMCP.

This server demonstrates the basics of MCP by exposing tools
for basic arithmetic operations.
"""

import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and run the new calculator server
from mcp_servers.calculator.server import mcp

if __name__ == "__main__":
    # FastMCP handles all the stdio server setup automatically
    mcp.run()