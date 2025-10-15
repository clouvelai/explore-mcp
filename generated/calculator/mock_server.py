#!/usr/bin/env python3
"""
Auto-generated Mock MCP Server
Generated from: server.py
Generated at: 2025-10-15T11:53:44.550573
"""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP

# Suppress all output to stdout/stderr to avoid MCP protocol issues
logging.basicConfig(level=logging.CRITICAL, stream=sys.stderr)
logging.getLogger().setLevel(logging.CRITICAL)

# Create mock server instance
mcp = FastMCP("mock-server")

# Request log for verification
request_log = []

def log_request(tool_name: str, params: Dict[str, Any]):
    """Log tool requests for verification."""
    request_log.append({
        "timestamp": datetime.now().isoformat(),
        "tool": tool_name,
        "params": params
    })
    # Don't print to stdout as it interferes with MCP stdio protocol


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

    # Return mock success response
    return "Mock: Successfully created item with ID: mock_12345"

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

    # Return mock success response
    return "Mock sum result: 42"

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

    # Return mock success response
    return "Mock sum result: 42"

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

    # Return mock success response
    return "Mock product result: 84"

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

    # Return mock success response
    return "Mock division result: 21"


@mcp.tool()
def get_request_log() -> str:
    """Get the log of all requests made to this mock server."""
    return json.dumps(request_log, indent=2)


if __name__ == "__main__":
    # Don't print to stdout as it interferes with MCP stdio protocol
    mcp.run(show_banner=False)
