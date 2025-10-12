"""
Unit tests for MCP client tool call functionality.

These tests verify tool calling, parameter validation, response parsing,
and error handling using both mocked and real FastMCP connections.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any

from mcp.types import TextContent, Tool


@pytest.mark.client_unit
class TestToolDiscovery:
    """Test tool discovery and metadata retrieval."""
    
    @pytest.mark.asyncio
    async def test_list_tools_basic(self, mock_client_session):
        """Test basic tool listing functionality."""
        session = mock_client_session
        result = await session.list_tools()
        
        assert result is not None
        assert hasattr(result, 'tools')
        assert len(result.tools) >= 2
        
        # Verify expected tools are present
        tool_names = [tool.name for tool in result.tools]
        assert "sum" in tool_names
        assert "multiply" in tool_names
    
    @pytest.mark.asyncio
    async def test_list_tools_with_real_server(self, mcp_client_session):
        """Test tool listing with real FastMCP server."""
        client = mcp_client_session
        tools = await client.list_tools()
        
        assert len(tools) == 5  # Expected number of tools
        tool_names = [tool.name for tool in tools]
        expected_tools = ["add", "sum", "sum_many", "multiply", "divide"]
        
        for expected in expected_tools:
            assert expected in tool_names
    
    @pytest.mark.asyncio
    async def test_tool_metadata_validation(self, mcp_client_session):
        """Test that tool metadata is properly structured."""
        client = mcp_client_session
        tools = await client.list_tools()
        
        for tool in tools:
            # Each tool should have required metadata
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description')
            assert hasattr(tool, 'inputSchema')
            
            # Name and description should be non-empty strings
            assert isinstance(tool.name, str) and len(tool.name) > 0
            assert isinstance(tool.description, str) and len(tool.description) > 0
            
            # Input schema should be a dictionary
            assert isinstance(tool.inputSchema, dict)
    
    @pytest.mark.asyncio
    async def test_specific_tool_schemas(self, mcp_client_session):
        """Test specific tool input schemas are correct."""
        client = mcp_client_session
        tools = await client.list_tools()
        
        # Find sum tool and validate its schema
        sum_tool = next((t for t in tools if t.name == "sum"), None)
        assert sum_tool is not None
        
        schema = sum_tool.inputSchema
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "a" in schema["properties"]
        assert "b" in schema["properties"]
        assert schema["properties"]["a"]["type"] == "number"
        assert schema["properties"]["b"]["type"] == "number"
        assert "required" in schema
        assert "a" in schema["required"]
        assert "b" in schema["required"]


@pytest.mark.client_unit
class TestBasicToolCalls:
    """Test basic tool calling functionality."""
    
    @pytest.mark.asyncio
    async def test_sum_tool_call(self, mock_client_session):
        """Test calling the sum tool with mocked session."""
        session = mock_client_session
        result = await session.call_tool("sum", {"a": 5, "b": 3})
        
        assert result is not None
        assert hasattr(result, 'content')
        assert len(result.content) > 0
        
        content_text = result.content[0].text
        assert "5" in content_text
        assert "3" in content_text
        assert "8" in content_text
    
    @pytest.mark.asyncio
    async def test_multiply_tool_call(self, mock_client_session):
        """Test calling the multiply tool with mocked session."""
        session = mock_client_session
        result = await session.call_tool("multiply", {"a": 4, "b": 7})
        
        assert result is not None
        content_text = result.content[0].text
        assert "4" in content_text
        assert "7" in content_text
        assert "28" in content_text
    
    @pytest.mark.asyncio
    async def test_real_server_tool_calls(self, mcp_client_session, sample_tool_calls):
        """Test tool calls with real FastMCP server."""
        client = mcp_client_session
        
        # Test sum calls
        for call_data in sample_tool_calls["sum_calls"]:
            result = await client.call_tool(call_data["name"], call_data["arguments"])
            content_text = result.content[0].text
            assert call_data["expected"] in content_text
        
        # Test multiply calls
        for call_data in sample_tool_calls["multiply_calls"]:
            result = await client.call_tool(call_data["name"], call_data["arguments"])
            content_text = result.content[0].text
            assert call_data["expected"] in content_text
    
    @pytest.mark.asyncio
    async def test_tool_call_response_structure(self, mcp_client_session):
        """Test that tool call responses have correct structure."""
        client = mcp_client_session
        result = await client.call_tool("sum", {"a": 10, "b": 20})
        
        # Response should have content
        assert hasattr(result, 'content')
        assert len(result.content) > 0
        
        # Content should be text type
        content = result.content[0]
        assert hasattr(content, 'text')
        assert isinstance(content.text, str)
        assert len(content.text) > 0


@pytest.mark.client_unit
class TestParameterValidation:
    """Test parameter validation and type handling."""
    
    @pytest.mark.asyncio
    async def test_integer_parameters(self, mcp_client_session):
        """Test tool calls with integer parameters."""
        client = mcp_client_session
        result = await client.call_tool("sum", {"a": 5, "b": 10})
        
        content_text = result.content[0].text
        assert "15" in content_text
    
    @pytest.mark.asyncio
    async def test_float_parameters(self, mcp_client_session):
        """Test tool calls with float parameters."""
        client = mcp_client_session
        result = await client.call_tool("sum", {"a": 5.5, "b": 4.3})
        
        content_text = result.content[0].text
        assert "9.8" in content_text
    
    @pytest.mark.asyncio
    async def test_negative_numbers(self, mcp_client_session):
        """Test tool calls with negative numbers."""
        client = mcp_client_session
        result = await client.call_tool("sum", {"a": -5, "b": 10})
        
        content_text = result.content[0].text
        assert "5" in content_text  # -5 + 10 = 5
    
    @pytest.mark.asyncio
    async def test_zero_values(self, mcp_client_session):
        """Test tool calls with zero values."""
        client = mcp_client_session
        
        # Test sum with zero
        result = await client.call_tool("sum", {"a": 0, "b": 5})
        content_text = result.content[0].text
        assert "5" in content_text
        
        # Test multiply with zero
        result = await client.call_tool("multiply", {"a": 0, "b": 100})
        content_text = result.content[0].text
        assert "0" in content_text
    
    @pytest.mark.asyncio
    async def test_large_numbers(self, mcp_client_session):
        """Test tool calls with large numbers."""
        client = mcp_client_session
        large_num = 1000000
        result = await client.call_tool("sum", {"a": large_num, "b": large_num})
        
        content_text = result.content[0].text
        assert "2000000" in content_text


@pytest.mark.client_unit
class TestToolCallErrors:
    """Test tool call error handling."""
    
    @pytest.mark.asyncio
    async def test_nonexistent_tool_error(self, mock_client_session):
        """Test calling a non-existent tool."""
        session = mock_client_session
        
        with pytest.raises(ValueError, match="Unknown tool"):
            await session.call_tool("nonexistent_tool", {})
    
    @pytest.mark.asyncio
    async def test_missing_required_parameters(self, mcp_client_session):
        """Test calling tool with missing required parameters."""
        client = mcp_client_session
        
        # sum tool requires both 'a' and 'b' parameters
        with pytest.raises(Exception):  # The exact exception type may vary
            await client.call_tool("sum", {"a": 5})  # Missing 'b'
    
    @pytest.mark.asyncio
    async def test_invalid_parameter_types_with_mock(self, mock_client_session):
        """Test calling tool with invalid parameter types using mock."""
        session = mock_client_session
        
        # Modify mock to raise error for invalid types
        async def mock_call_tool_with_validation(name: str, arguments: Dict[str, Any]):
            if name == "sum":
                a, b = arguments.get("a"), arguments.get("b")
                if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
                    raise ValueError("Invalid parameter type")
                result = a + b
                mock_result = MagicMock()
                mock_result.content = [TextContent(type="text", text=f"The sum of {a} and {b} is {result}")]
                return mock_result
            raise ValueError(f"Unknown tool: {name}")
        
        session.call_tool = mock_call_tool_with_validation
        
        with pytest.raises(ValueError, match="Invalid parameter type"):
            await session.call_tool("sum", {"a": "not_a_number", "b": 5})
    
    @pytest.mark.asyncio
    async def test_empty_parameters(self, mcp_client_session):
        """Test calling tool with empty parameters."""
        client = mcp_client_session
        
        with pytest.raises(Exception):
            await client.call_tool("sum", {})
    
    @pytest.mark.asyncio
    async def test_extra_parameters_validation(self, mcp_client_session):
        """Test that extra parameters are properly validated."""
        client = mcp_client_session
        
        # FastMCP strictly validates parameters - extra params should cause an error
        with pytest.raises(Exception):  # ToolError or ValidationError
            await client.call_tool("sum", {
                "a": 5, 
                "b": 3, 
                "extra_param": "not_allowed"
            })


@pytest.mark.client_unit
class TestSpecializedTools:
    """Test specialized tool functionality."""
    
    @pytest.mark.asyncio
    async def test_sum_many_tool(self, mcp_client_session):
        """Test the sum_many tool with multiple numbers."""
        client = mcp_client_session
        
        numbers = [1, 2, 3, 4, 5]
        result = await client.call_tool("sum_many", {"numbers": numbers})
        
        content_text = result.content[0].text
        assert "15" in content_text  # Sum of 1+2+3+4+5
    
    @pytest.mark.asyncio
    async def test_sum_many_empty_list(self, mcp_client_session):
        """Test sum_many with empty list."""
        client = mcp_client_session
        
        result = await client.call_tool("sum_many", {"numbers": []})
        content_text = result.content[0].text
        assert "Error: No numbers provided" in content_text
    
    @pytest.mark.asyncio
    async def test_sum_many_single_number(self, mcp_client_session):
        """Test sum_many with single number."""
        client = mcp_client_session
        
        result = await client.call_tool("sum_many", {"numbers": [42]})
        content_text = result.content[0].text
        assert "42" in content_text
    
    @pytest.mark.asyncio
    async def test_divide_tool(self, mcp_client_session):
        """Test the divide tool."""
        client = mcp_client_session
        
        result = await client.call_tool("divide", {"a": 10, "b": 2})
        content_text = result.content[0].text
        assert "5" in content_text
    
    @pytest.mark.asyncio
    async def test_divide_by_zero(self, mcp_client_session):
        """Test divide by zero error handling."""
        client = mcp_client_session
        
        result = await client.call_tool("divide", {"a": 10, "b": 0})
        content_text = result.content[0].text
        assert "Error: Cannot divide by zero" in content_text


@pytest.mark.client_unit
class TestConcurrentToolCalls:
    """Test concurrent tool call execution."""
    
    @pytest.mark.asyncio
    async def test_concurrent_same_tool(self, mcp_client_session):
        """Test multiple concurrent calls to the same tool."""
        client = mcp_client_session
        
        # Create multiple concurrent sum operations
        tasks = [
            client.call_tool("sum", {"a": i, "b": i + 1})
            for i in range(10)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Verify all results
        assert len(results) == 10
        for i, result in enumerate(results):
            expected_sum = i + (i + 1)
            content_text = result.content[0].text
            assert str(expected_sum) in content_text
    
    @pytest.mark.asyncio
    async def test_concurrent_different_tools(self, mcp_client_session):
        """Test concurrent calls to different tools."""
        client = mcp_client_session
        
        tasks = [
            client.call_tool("sum", {"a": 10, "b": 20}),
            client.call_tool("multiply", {"a": 5, "b": 6}),
            client.call_tool("divide", {"a": 100, "b": 4}),
            client.call_tool("sum_many", {"numbers": [1, 2, 3]})
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 4
        assert "30" in results[0].content[0].text  # sum
        assert "30" in results[1].content[0].text  # multiply
        assert "25" in results[2].content[0].text  # divide
        assert "6" in results[3].content[0].text   # sum_many
    
    @pytest.mark.asyncio
    async def test_concurrent_with_errors(self, mcp_client_session):
        """Test concurrent calls including some that should error."""
        client = mcp_client_session
        
        tasks = [
            client.call_tool("sum", {"a": 5, "b": 3}),           # Should succeed
            client.call_tool("divide", {"a": 10, "b": 0}),       # Should return error message
            client.call_tool("multiply", {"a": 4, "b": 5}),      # Should succeed
            client.call_tool("sum_many", {"numbers": []})        # Should return error message
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 4
        assert "8" in results[0].content[0].text                    # sum success
        assert "Cannot divide by zero" in results[1].content[0].text # divide error
        assert "20" in results[2].content[0].text                   # multiply success
        assert "No numbers provided" in results[3].content[0].text  # sum_many error


@pytest.mark.client_unit
class TestPerformanceAndLimits:
    """Test performance characteristics and limits."""
    
    @pytest.mark.asyncio
    async def test_rapid_sequential_calls(self, mcp_client_session):
        """Test rapid sequential tool calls."""
        client = mcp_client_session
        
        # Make 50 rapid sequential calls
        for i in range(50):
            result = await client.call_tool("sum", {"a": i, "b": 1})
            content_text = result.content[0].text
            assert str(i + 1) in content_text
    
    @pytest.mark.asyncio
    async def test_large_parameter_values(self, mcp_client_session):
        """Test tool calls with very large parameter values."""
        client = mcp_client_session
        
        large_num = 10**15
        result = await client.call_tool("sum", {"a": large_num, "b": large_num})
        
        content_text = result.content[0].text
        expected_result = str(2 * large_num)
        assert expected_result in content_text
    
    @pytest.mark.asyncio
    async def test_precision_with_decimals(self, mcp_client_session):
        """Test precision handling with decimal numbers."""
        client = mcp_client_session
        
        result = await client.call_tool("sum", {"a": 0.1, "b": 0.2})
        content_text = result.content[0].text
        
        # Note: Due to floating point precision, 0.1 + 0.2 = 0.30000000000000004
        # The test should account for this
        assert "0.3" in content_text
    
    @pytest.mark.asyncio
    async def test_sum_many_large_list(self, mcp_client_session):
        """Test sum_many with a large list of numbers."""
        client = mcp_client_session
        
        # Sum of numbers 1 to 100 is 5050
        numbers = list(range(1, 101))
        result = await client.call_tool("sum_many", {"numbers": numbers})
        
        content_text = result.content[0].text
        assert "5050" in content_text