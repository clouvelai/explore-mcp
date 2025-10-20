"""
Pytest configuration and shared fixtures for MCP client tests.

This conftest provides client-specific fixtures for testing MCP client functionality
using FastMCP's in-memory transport and mocked stdio connections.
"""

import pytest
import asyncio
import sys
from pathlib import Path
from typing import AsyncGenerator, Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastmcp import FastMCP, Client
from mcp_servers.calculator.tools import register_tools, register_prompts
from mcp import ClientSession, StdioServerParameters
from mcp.types import Tool, Prompt, TextContent


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mcp_test_server():
    """Create a fresh MCP server instance for client testing."""
    server = FastMCP("test-calculator-client")
    register_tools(server)
    register_prompts(server)
    return server


@pytest.fixture
async def mcp_client_session(mcp_test_server) -> AsyncGenerator[Client, None]:
    """Create an MCP client connected to the test server via in-memory transport."""
    async with Client(mcp_test_server) as client:
        yield client


@pytest.fixture
def mock_stdio_server_params():
    """Provide mock StdioServerParameters for testing."""
    return StdioServerParameters(
        command="python",
        args=["server.py"],
        env=None
    )


@pytest.fixture
def mock_client_session():
    """Create a mock ClientSession for testing client behavior without a real server."""
    session = AsyncMock(spec=ClientSession)
    
    # Mock initialize method
    async def mock_initialize():
        mock_result = MagicMock()
        mock_result.serverInfo.name = "test-calculator"
        mock_result.serverInfo.version = "1.0.0"
        return mock_result
    
    session.initialize = mock_initialize
    
    # Mock list_tools method
    async def mock_list_tools():
        mock_result = MagicMock()
        mock_result.tools = [
            Tool(
                name="sum",
                description="Add two numbers together",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "a": {"type": "number"},
                        "b": {"type": "number"}
                    },
                    "required": ["a", "b"]
                }
            ),
            Tool(
                name="multiply",
                description="Multiply two numbers together",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "a": {"type": "number"},
                        "b": {"type": "number"}
                    },
                    "required": ["a", "b"]
                }
            )
        ]
        return mock_result
    
    session.list_tools = mock_list_tools
    
    # Mock list_prompts method
    async def mock_list_prompts():
        mock_result = MagicMock()
        mock_result.prompts = [
            Prompt(
                name="explain_calculation",
                description="Explain a mathematical calculation step by step"
            )
        ]
        return mock_result
    
    session.list_prompts = mock_list_prompts
    
    # Mock call_tool method
    async def mock_call_tool(name: str, arguments: Dict[str, Any]):
        mock_result = MagicMock()
        if name == "sum":
            a, b = arguments["a"], arguments["b"]
            result = a + b
            mock_result.content = [TextContent(type="text", text=f"The sum of {a} and {b} is {result}")]
        elif name == "multiply":
            a, b = arguments["a"], arguments["b"]
            result = a * b
            mock_result.content = [TextContent(type="text", text=f"The product of {a} and {b} is {result}")]
        else:
            raise ValueError(f"Unknown tool: {name}")
        return mock_result
    
    session.call_tool = mock_call_tool
    
    # Mock get_prompt method
    async def mock_get_prompt(name: str, arguments: Dict[str, Any] = None):
        mock_result = MagicMock()
        if name == "explain_calculation":
            calculation = arguments.get("calculation", "1 + 1") if arguments else "1 + 1"
            mock_result.description = "Educational calculation explanation"
            mock_message = MagicMock()
            mock_message.content = MagicMock()
            mock_message.content.text = f"Let me explain {calculation} step by step..."
            mock_result.messages = [mock_message]
        else:
            raise ValueError(f"Unknown prompt: {name}")
        return mock_result
    
    session.get_prompt = mock_get_prompt
    
    return session


@pytest.fixture
def sample_tool_calls():
    """Provide sample tool call data for testing."""
    return {
        "sum_calls": [
            {"name": "sum", "arguments": {"a": 5, "b": 3}, "expected": "8"},
            {"name": "sum", "arguments": {"a": -5, "b": 10}, "expected": "5"},
            {"name": "sum", "arguments": {"a": 0, "b": 0}, "expected": "0"},
        ],
        "multiply_calls": [
            {"name": "multiply", "arguments": {"a": 4, "b": 7}, "expected": "28"},
            {"name": "multiply", "arguments": {"a": -3, "b": 5}, "expected": "-15"},
            {"name": "multiply", "arguments": {"a": 0, "b": 100}, "expected": "0"},
        ],
        "invalid_calls": [
            {"name": "nonexistent", "arguments": {}, "expected_error": "Unknown tool"},
            {"name": "sum", "arguments": {"a": 5}, "expected_error": "Missing parameter"},
            {"name": "sum", "arguments": {"a": "not_a_number", "b": 5}, "expected_error": "Invalid parameter type"},
        ]
    }


@pytest.fixture
def sample_prompts():
    """Provide sample prompt data for testing."""
    return {
        "valid_prompts": [
            {"name": "explain_calculation", "arguments": {"calculation": "5 + 3"}},
            {"name": "explain_calculation", "arguments": {"calculation": "10 * 7"}},
        ],
        "invalid_prompts": [
            {"name": "nonexistent_prompt", "arguments": {}, "expected_error": "Unknown prompt"},
        ]
    }


@pytest.fixture
def mock_stdio_transport():
    """Mock stdio transport for testing connection scenarios."""
    with patch('mcp.client.stdio.stdio_client') as mock_stdio:
        # Create mock read/write streams
        mock_read = AsyncMock()
        mock_write = AsyncMock()
        
        async def mock_stdio_context(*args, **kwargs):
            return mock_read, mock_write
        
        mock_stdio.return_value.__aenter__ = mock_stdio_context
        mock_stdio.return_value.__aexit__ = AsyncMock(return_value=None)
        
        yield mock_stdio, mock_read, mock_write


@pytest.fixture
def connection_test_scenarios():
    """Provide test scenarios for connection testing."""
    return {
        "successful_connection": {
            "server_params": StdioServerParameters(command="python", args=["server.py"]),
            "expected_tools": ["sum", "multiply", "divide", "sum_many", "add"],
            "expected_prompts": ["explain_calculation"]
        },
        "connection_failures": [
            {
                "scenario": "invalid_command",
                "server_params": StdioServerParameters(command="nonexistent_command", args=[]),
                "expected_error": "FileNotFoundError"
            },
            {
                "scenario": "invalid_args",
                "server_params": StdioServerParameters(command="python", args=["nonexistent_file.py"]),
                "expected_error": "FileNotFoundError"
            }
        ]
    }


@pytest.fixture
def error_response_scenarios():
    """Provide error response scenarios for testing error handling."""
    return {
        "tool_errors": [
            {"error_type": "tool_not_found", "tool_name": "nonexistent", "message": "Tool not found"},
            {"error_type": "invalid_parameters", "tool_name": "sum", "params": {"a": "invalid"}, "message": "Invalid parameter type"},
            {"error_type": "missing_parameters", "tool_name": "sum", "params": {"a": 5}, "message": "Missing required parameter: b"},
        ],
        "connection_errors": [
            {"error_type": "connection_timeout", "message": "Connection timed out"},
            {"error_type": "server_disconnect", "message": "Server disconnected unexpectedly"},
            {"error_type": "protocol_error", "message": "Invalid MCP protocol message"},
        ]
    }


@pytest.fixture
def performance_test_data():
    """Provide data for performance and stress testing."""
    return {
        "rapid_calls": [
            {"name": "sum", "arguments": {"a": i, "b": i + 1}} 
            for i in range(100)
        ],
        "large_numbers": {
            "very_large": [10**10, 10**15],
            "very_small": [1e-10, 1e-15],
            "precision_test": [0.1, 0.2, 0.3]
        }
    }