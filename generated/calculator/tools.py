"""
Auto-generated MCP Tools
Generated from: mcp_servers/calculator/server.py
Generated at: 2025-10-20T09:36:36.694105
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP

# Request log for verification
request_log = []


def log_request(tool_name: str, params: Dict[str, Any]):
    """Log tool requests for verification."""
    request_log.append({
        "timestamp": datetime.now().isoformat(),
        "tool": tool_name,
        "params": params
    })


def register_tools(mcp: FastMCP):
    """Register all tools with the MCP server."""
    
    @mcp.tool()
    def add(a: float, b: float) -> str:
        """
        Add two numbers together.

Args:
    a: The first number
    b: The second number
    
Returns:
    A message with the sum of the two numbers
        """
        # Log the request
        log_request("add", locals())
        
        # Validate required parameters
        if a is None:
            return "Error: Missing required parameter: a"
        if b is None:
            return "Error: Missing required parameter: b"

        # Return mock response
        return "The sum of 15 and 27 is 42"

    @mcp.tool()
    def sum(a: float, b: float) -> str:
        """
        Add two numbers together.

Args:
    a: The first number
    b: The second number
    
Returns:
    A message with the sum of the two numbers
        """
        # Log the request
        log_request("sum", locals())
        
        # Validate required parameters
        if a is None:
            return "Error: Missing required parameter: a"
        if b is None:
            return "Error: Missing required parameter: b"

        # Return mock response
        return "The sum of 8 and 13 is 21"

    @mcp.tool()
    def sum_many(numbers: List[float]) -> str:
        """
        Add multiple numbers together.

Args:
    numbers: A list of numbers to add together
    
Returns:
    A message with the sum of all numbers
        """
        # Log the request
        log_request("sum_many", locals())
        
        # Validate required parameters
        if numbers is None:
            return "Error: Missing required parameter: numbers"

        # Return mock response
        return "The sum of [3, 7, 11, 2, 5] is 28"

    @mcp.tool()
    def multiply(a: float, b: float) -> str:
        """
        Multiply two numbers together.

Args:
    a: The first number
    b: The second number
    
Returns:
    A message with the product of the two numbers
        """
        # Log the request
        log_request("multiply", locals())
        
        # Validate required parameters
        if a is None:
            return "Error: Missing required parameter: a"
        if b is None:
            return "Error: Missing required parameter: b"

        # Return mock response
        return "The product of 6 and 9 is 54"

    @mcp.tool()
    def divide(a: float, b: float) -> str:
        """
        Divide one number by another.

Args:
    a: The dividend (number to be divided)
    b: The divisor (number to divide by)
    
Returns:
    A message with the quotient, or an error if dividing by zero
        """
        # Log the request
        log_request("divide", locals())
        
        # Validate required parameters
        if a is None:
            return "Error: Missing required parameter: a"
        if b is None:
            return "Error: Missing required parameter: b"

        # Return mock response
        return "The quotient of 36 divided by 4 is 9"

    @mcp.tool()
    def get_request_log() -> str:
        """Get the log of all requests made to this mock server."""
        return json.dumps(request_log, indent=2)
