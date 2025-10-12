"""
Integration tests for MCP protocol functionality.

These tests verify that tools are properly registered with the MCP server
and can be called through the MCP protocol using the in-memory client.
"""

import pytest
import json
from typing import Any, Dict


@pytest.mark.integration
class TestMCPToolRegistration:
    """Test tool registration and discovery through MCP protocol."""
    
    @pytest.mark.asyncio
    async def test_list_tools(self, mcp_client):
        """Test that all tools are properly registered and discoverable."""
        tools = await mcp_client.list_tools()
        
        # Verify we have the expected number of tools (add + sum + sum_many + multiply + divide = 5)
        assert len(tools) == 5
        
        # Extract tool names
        tool_names = [tool.name for tool in tools]
        
        # Verify all expected tools are present
        expected_tools = ['add', 'sum', 'sum_many', 'multiply', 'divide']
        for expected in expected_tools:
            assert expected in tool_names, f"Tool '{expected}' not found in registered tools"
    
    @pytest.mark.asyncio
    async def test_tool_metadata(self, mcp_client):
        """Test that tool metadata is correctly exposed."""
        tools = await mcp_client.list_tools()
        
        # Find the sum tool
        sum_tool = next((t for t in tools if t.name == 'sum'), None)
        assert sum_tool is not None, "Sum tool not found"
        
        # Verify tool has description
        assert sum_tool.description is not None
        assert "Add two numbers" in sum_tool.description
        
        # Verify input schema
        assert sum_tool.inputSchema is not None
        properties = sum_tool.inputSchema.get('properties', {})
        assert 'a' in properties
        assert 'b' in properties


@pytest.mark.integration
class TestMCPToolExecution:
    """Test tool execution through MCP protocol."""
    
    @pytest.mark.asyncio
    async def test_call_sum_tool(self, mcp_client):
        """Test calling the sum tool through MCP."""
        result = await mcp_client.call_tool('sum', {'a': 5, 'b': 3})
        
        assert result is not None
        assert hasattr(result, 'content')
        # Access the text content directly
        content_text = result.content[0].text if result.content else ""
        assert "The sum of" in content_text and "5" in content_text and "3" in content_text and "8" in content_text
    
    @pytest.mark.asyncio
    async def test_call_multiply_tool(self, mcp_client):
        """Test calling the multiply tool through MCP."""
        result = await mcp_client.call_tool('multiply', {'a': 4, 'b': 7})
        
        assert result is not None
        content_text = result.content[0].text if result.content else ""
        assert "The product of" in content_text and "4" in content_text and "7" in content_text and "28" in content_text
    
    @pytest.mark.asyncio
    async def test_call_divide_tool(self, mcp_client):
        """Test calling the divide tool through MCP."""
        result = await mcp_client.call_tool('divide', {'a': 15, 'b': 3})
        
        assert result is not None
        content_text = result.content[0].text if result.content else ""
        assert "15" in content_text and "divided by" in content_text and "3" in content_text and "5" in content_text
    
    @pytest.mark.asyncio
    async def test_call_sum_many_tool(self, mcp_client):
        """Test calling the sum_many tool through MCP."""
        numbers = [1, 2, 3, 4, 5]
        result = await mcp_client.call_tool('sum_many', {'numbers': numbers})
        
        assert result is not None
        content_text = result.content[0].text if result.content else ""
        assert "The sum of" in content_text and "15" in content_text
    
    @pytest.mark.asyncio
    async def test_error_handling_divide_by_zero(self, mcp_client):
        """Test error handling for division by zero through MCP."""
        result = await mcp_client.call_tool('divide', {'a': 10, 'b': 0})
        
        assert result is not None
        content_text = result.content[0].text if result.content else ""
        assert "Error: Cannot divide by zero" in content_text
    
    @pytest.mark.asyncio
    async def test_error_handling_empty_sum_many(self, mcp_client):
        """Test error handling for empty list in sum_many."""
        result = await mcp_client.call_tool('sum_many', {'numbers': []})
        
        assert result is not None
        content_text = result.content[0].text if result.content else ""
        assert "Error: No numbers provided" in content_text
    
    @pytest.mark.asyncio
    async def test_missing_parameters(self, mcp_client):
        """Test handling of missing required parameters."""
        with pytest.raises(Exception) as exc_info:
            await mcp_client.call_tool('sum', {'a': 5})  # Missing 'b' parameter
        
        # The exact error message may vary, but it should indicate missing parameter
        assert exc_info.value is not None
    
    @pytest.mark.asyncio
    async def test_invalid_tool_name(self, mcp_client):
        """Test calling a non-existent tool."""
        with pytest.raises(Exception) as exc_info:
            await mcp_client.call_tool('non_existent_tool', {'param': 'value'})
        
        assert exc_info.value is not None


@pytest.mark.integration
class TestMCPPrompts:
    """Test prompt functionality through MCP protocol."""
    
    @pytest.mark.asyncio
    async def test_list_prompts(self, mcp_client):
        """Test that prompts are properly registered and discoverable."""
        prompts = await mcp_client.list_prompts()
        
        # Verify we have at least one prompt
        assert len(prompts) >= 1
        
        # Extract prompt names
        prompt_names = [prompt.name for prompt in prompts]
        
        # Verify the expected prompt is present
        assert 'explain_calculation' in prompt_names
    
    @pytest.mark.asyncio
    async def test_get_prompt(self, mcp_client):
        """Test retrieving a specific prompt."""
        result = await mcp_client.get_prompt(
            'explain_calculation',
            {'calculation': '15 + 27'}
        )
        
        assert result is not None
        assert hasattr(result, 'messages')
        assert len(result.messages) > 0
        
        # Check that the prompt includes the calculation
        prompt_text = str(result.messages[0].content)
        assert '15 + 27' in prompt_text
        assert 'step by step' in prompt_text.lower()


@pytest.mark.integration
class TestConcurrentOperations:
    """Test concurrent operations through MCP protocol."""
    
    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self, mcp_client):
        """Test multiple concurrent tool calls."""
        import asyncio
        
        # Create multiple concurrent tasks
        tasks = [
            mcp_client.call_tool('sum', {'a': i, 'b': i + 1})
            for i in range(10)
        ]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks)
        
        # Verify all results
        assert len(results) == 10
        for i, result in enumerate(results):
            expected_sum = i + (i + 1)
            content_text = result.content[0].text if result.content else ""
            assert f"is {expected_sum}" in content_text
    
    @pytest.mark.asyncio
    async def test_mixed_concurrent_operations(self, mcp_client):
        """Test different tools being called concurrently."""
        import asyncio
        
        tasks = [
            mcp_client.call_tool('sum', {'a': 10, 'b': 20}),
            mcp_client.call_tool('multiply', {'a': 5, 'b': 6}),
            mcp_client.call_tool('divide', {'a': 100, 'b': 4}),
            mcp_client.call_tool('sum_many', {'numbers': [1, 2, 3]}),
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 4
        assert "is 30" in results[0].content[0].text  # sum
        assert "is 30" in results[1].content[0].text  # multiply
        assert "is 25" in results[2].content[0].text  # divide
        assert "is 6" in results[3].content[0].text   # sum_many