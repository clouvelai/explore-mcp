#!/usr/bin/env python3
"""
Calculator MCP Server using FastMCP.

This server provides calculator tools for basic arithmetic operations.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastmcp import FastMCP
from mcp_servers.calculator.tools import register_tools, register_resources

# Create MCP instance
mcp = FastMCP("Calculator")

# Register all calculator tools and resources
register_tools(mcp)
register_resources(mcp)

# Add explanatory prompt
@mcp.prompt()
def explain_calculation(calculation: str) -> str:
    """Explain how to perform a calculation step by step.
    
    Args:
        calculation: The calculation to explain (e.g. "2 + 3 * 4")
    """
    return f"""Please explain how to calculate "{calculation}" step by step, showing:
1. Order of operations
2. Each step of the calculation
3. The final result

Make your explanation clear and educational."""

if __name__ == "__main__":
    # FastMCP handles all the stdio server setup automatically
    mcp.run()