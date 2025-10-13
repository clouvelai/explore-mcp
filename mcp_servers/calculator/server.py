"""
Simple MCP Server with calculator tools using FastMCP.

This server demonstrates the basics of MCP by exposing tools
for basic arithmetic operations.
"""

from fastmcp import FastMCP
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from mcp_servers.calculator.tools import register_tools, register_prompts

# Create the FastMCP server instance
mcp = FastMCP("simple-calculator")

# Register all tools and prompts
register_tools(mcp)
register_prompts(mcp)

if __name__ == "__main__":
    # FastMCP handles all the stdio server setup automatically
    mcp.run()