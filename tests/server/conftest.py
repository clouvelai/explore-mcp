"""
Pytest configuration and shared fixtures for MCP server tests.

This conftest provides server-specific fixtures for testing the MCP calculator server
using FastMCP's in-memory transport for fast, reliable testing.
"""

import pytest
import asyncio
import sys
from pathlib import Path
from typing import AsyncGenerator

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastmcp import FastMCP, Client
from mcp_servers.calculator.tools import register_tools, register_prompts


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mcp_server():
    """Create a fresh MCP server instance for testing."""
    server = FastMCP("test-calculator")
    register_tools(server)
    register_prompts(server)
    return server


@pytest.fixture
async def mcp_client(mcp_server) -> AsyncGenerator[Client, None]:
    """Create an MCP client connected to the test server via in-memory transport."""
    async with Client(mcp_server) as client:
        yield client


@pytest.fixture
def sample_numbers():
    """Provide sample test data for calculator operations."""
    return {
        "positive": [1, 2, 3, 4, 5],
        "negative": [-1, -2, -3, -4, -5],
        "mixed": [-2, -1, 0, 1, 2],
        "decimals": [0.1, 0.2, 0.3, 0.4, 0.5],
        "large": [1000000, 2000000, 3000000],
        "edge_cases": {
            "zero": 0,
            "one": 1,
            "negative_one": -1,
            "small_decimal": 0.00001,
            "large_number": 999999999,
        }
    }


@pytest.fixture
def expected_responses():
    """Expected response patterns for validation."""
    return {
        "sum_pattern": "The sum of {a} and {b} is {result}",
        "product_pattern": "The product of {a} and {b} is {result}",
        "division_pattern": "{a} divided by {b} is {result}",
        "error_division_zero": "Error: Cannot divide by zero",
        "error_no_numbers": "Error: No numbers provided",
    }