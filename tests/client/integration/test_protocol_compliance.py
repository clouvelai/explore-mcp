"""
Integration tests for MCP protocol compliance.

These tests verify that the client properly implements the MCP protocol
specifications and handles protocol-level interactions correctly.
"""

import pytest
import asyncio
from unittest.mock import MagicMock

from mcp.types import Tool, Prompt, TextContent


@pytest.mark.client_integration
class TestMCPProtocolInitialization:
    """Test MCP protocol initialization compliance."""
    
    @pytest.mark.asyncio
    async def test_initialization_handshake(self, mcp_client_session):
        """Test proper MCP initialization handshake."""
        client = mcp_client_session
        
        # The client should be already initialized through the fixture
        # Test that we can perform operations that require initialization
        tools = await client.list_tools()
        assert len(tools) > 0
        
        prompts = await client.list_prompts()
        assert len(prompts) > 0
    
    @pytest.mark.asyncio
    async def test_protocol_version_handling(self, mock_client_session):
        """Test protocol version negotiation."""
        session = mock_client_session
        
        # Test that initialization returns proper version info
        result = await session.initialize()
        assert hasattr(result, 'serverInfo')
        assert hasattr(result.serverInfo, 'name')
        assert hasattr(result.serverInfo, 'version')
        assert isinstance(result.serverInfo.name, str)
        assert isinstance(result.serverInfo.version, str)
    
    @pytest.mark.asyncio
    async def test_capabilities_negotiation(self, mcp_client_session):
        """Test that client and server capabilities are properly negotiated."""
        client = mcp_client_session
        
        # Test that both tools and prompts are available (indicating full capability support)
        tools = await client.list_tools()
        prompts = await client.list_prompts()
        
        assert len(tools) > 0, "Server should expose tools capability"
        assert len(prompts) > 0, "Server should expose prompts capability"


@pytest.mark.client_integration
class TestMCPMessageFormats:
    """Test MCP message format compliance."""
    
    @pytest.mark.asyncio
    async def test_tool_call_message_format(self, mcp_client_session):
        """Test that tool calls follow proper MCP message format."""
        client = mcp_client_session
        
        # Test tool call with proper parameters
        result = await client.call_tool("sum", {"a": 5, "b": 3})
        
        # Verify response structure
        assert hasattr(result, 'content')
        assert isinstance(result.content, list)
        assert len(result.content) > 0
        
        # Verify content structure
        content = result.content[0]
        assert hasattr(content, 'text')
        assert isinstance(content.text, str)
    
    @pytest.mark.asyncio
    async def test_prompt_request_message_format(self, mcp_client_session):
        """Test that prompt requests follow proper MCP message format."""
        client = mcp_client_session
        
        result = await client.get_prompt("explain_calculation", {"calculation": "5 + 3"})
        
        # Verify response structure
        assert hasattr(result, 'description')
        assert hasattr(result, 'messages')
        assert isinstance(result.description, str)
        assert isinstance(result.messages, list)
        assert len(result.messages) > 0
        
        # Verify message structure
        message = result.messages[0]
        assert hasattr(message, 'content')
    
    @pytest.mark.asyncio
    async def test_list_tools_response_format(self, mcp_client_session):
        """Test that list_tools response follows MCP format."""
        client = mcp_client_session
        tools = await client.list_tools()
        
        # Verify tools list structure
        assert isinstance(tools, list)
        assert len(tools) > 0
        
        # Verify each tool structure
        for tool in tools:
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description')
            assert hasattr(tool, 'inputSchema')
            
            assert isinstance(tool.name, str)
            assert isinstance(tool.description, str)
            assert isinstance(tool.inputSchema, dict)
            
            # Verify input schema follows JSON Schema format
            schema = tool.inputSchema
            assert 'type' in schema
            assert schema['type'] == 'object'
    
    @pytest.mark.asyncio
    async def test_list_prompts_response_format(self, mcp_client_session):
        """Test that list_prompts response follows MCP format."""
        client = mcp_client_session
        prompts = await client.list_prompts()
        
        # Verify prompts list structure
        assert isinstance(prompts, list)
        assert len(prompts) > 0
        
        # Verify each prompt structure
        for prompt in prompts:
            assert hasattr(prompt, 'name')
            assert hasattr(prompt, 'description')
            
            assert isinstance(prompt.name, str)
            assert isinstance(prompt.description, str)


@pytest.mark.client_integration
class TestMCPResourceManagement:
    """Test MCP resource management compliance."""
    
    @pytest.mark.asyncio
    async def test_tool_resource_isolation(self, mcp_client_session):
        """Test that tool calls are properly isolated."""
        client = mcp_client_session
        
        # Multiple tool calls should not interfere with each other
        result1 = await client.call_tool("sum", {"a": 10, "b": 20})
        result2 = await client.call_tool("multiply", {"a": 5, "b": 6})
        result3 = await client.call_tool("sum", {"a": 1, "b": 1})
        
        # Each should return independent results
        assert "30" in result1.content[0].text
        assert "30" in result2.content[0].text
        assert "2" in result3.content[0].text
    
    @pytest.mark.asyncio
    async def test_session_state_management(self, mcp_client_session):
        """Test that session state is properly managed."""
        client = mcp_client_session
        
        # Operations should be stateless - order shouldn't matter
        operations = [
            ("sum", {"a": 5, "b": 5}),
            ("multiply", {"a": 3, "b": 4}),
            ("divide", {"a": 20, "b": 4}),
            ("sum", {"a": 1, "b": 9})
        ]
        
        for tool_name, params in operations:
            result = await client.call_tool(tool_name, params)
            assert result is not None
            assert len(result.content) > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_operations_isolation(self, mcp_client_session):
        """Test that concurrent operations are properly isolated."""
        client = mcp_client_session
        
        # Create concurrent operations
        tasks = [
            client.call_tool("sum", {"a": i, "b": i + 1})
            for i in range(10)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Verify each result is correct and independent
        for i, result in enumerate(results):
            expected_sum = i + (i + 1)
            assert str(expected_sum) in result.content[0].text


@pytest.mark.client_integration
class TestMCPErrorHandling:
    """Test MCP protocol error handling compliance."""
    
    @pytest.mark.asyncio
    async def test_tool_not_found_error_format(self, mock_client_session):
        """Test that tool not found errors follow MCP format."""
        session = mock_client_session
        
        # Ensure the mock raises proper errors
        with pytest.raises(ValueError) as exc_info:
            await session.call_tool("nonexistent_tool", {})
        
        # Error should be descriptive
        assert "nonexistent_tool" in str(exc_info.value).lower() or "unknown tool" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_invalid_parameters_error_format(self, mcp_client_session):
        """Test that invalid parameter errors follow MCP format."""
        client = mcp_client_session
        
        # Missing required parameter should raise an error
        with pytest.raises(Exception):
            await client.call_tool("sum", {"a": 5})  # Missing 'b'
    
    @pytest.mark.asyncio
    async def test_prompt_not_found_error_format(self, mock_client_session):
        """Test that prompt not found errors follow MCP format."""
        session = mock_client_session
        
        with pytest.raises(ValueError) as exc_info:
            await session.get_prompt("nonexistent_prompt", {})
        
        # Error should be descriptive
        assert "nonexistent_prompt" in str(exc_info.value).lower() or "unknown prompt" in str(exc_info.value).lower()


@pytest.mark.client_integration
class TestMCPDataTypes:
    """Test MCP data type handling compliance."""
    
    @pytest.mark.asyncio
    async def test_numeric_parameter_types(self, mcp_client_session):
        """Test handling of different numeric parameter types."""
        client = mcp_client_session
        
        # Test integers
        result1 = await client.call_tool("sum", {"a": 5, "b": 3})
        assert "8" in result1.content[0].text
        
        # Test floats
        result2 = await client.call_tool("sum", {"a": 5.5, "b": 2.3})
        assert "7.8" in result2.content[0].text
        
        # Test negative numbers
        result3 = await client.call_tool("sum", {"a": -5, "b": 10})
        assert "5" in result3.content[0].text
    
    @pytest.mark.asyncio
    async def test_array_parameter_types(self, mcp_client_session):
        """Test handling of array parameter types."""
        client = mcp_client_session
        
        # Test with array of numbers
        numbers = [1, 2, 3, 4, 5]
        result = await client.call_tool("sum_many", {"numbers": numbers})
        assert "15" in result.content[0].text
        
        # Test with empty array
        result_empty = await client.call_tool("sum_many", {"numbers": []})
        assert "Error" in result_empty.content[0].text
    
    @pytest.mark.asyncio
    async def test_string_parameter_types(self, mcp_client_session):
        """Test handling of string parameter types."""
        client = mcp_client_session
        
        # Test string parameters in prompts
        result = await client.get_prompt("explain_calculation", {"calculation": "10 + 5"})
        assert "10 + 5" in str(result.messages[0].content)
        
        # Test with complex string
        complex_calc = "(3 + 4) * 2 - 1"
        result2 = await client.get_prompt("explain_calculation", {"calculation": complex_calc})
        assert complex_calc in str(result2.messages[0].content)


@pytest.mark.client_integration
class TestMCPSchemaValidation:
    """Test MCP schema validation compliance."""
    
    @pytest.mark.asyncio
    async def test_tool_input_schema_validation(self, mcp_client_session):
        """Test that tool input schemas are valid JSON Schema."""
        client = mcp_client_session
        tools = await client.list_tools()
        
        for tool in tools:
            schema = tool.inputSchema
            
            # Basic JSON Schema validation
            assert isinstance(schema, dict)
            assert 'type' in schema
            assert schema['type'] == 'object'
            
            if 'properties' in schema:
                assert isinstance(schema['properties'], dict)
                for prop_name, prop_schema in schema['properties'].items():
                    assert isinstance(prop_name, str)
                    assert isinstance(prop_schema, dict)
                    assert 'type' in prop_schema
            
            if 'required' in schema:
                assert isinstance(schema['required'], list)
                for req_field in schema['required']:
                    assert isinstance(req_field, str)
                    assert req_field in schema.get('properties', {})
    
    @pytest.mark.asyncio
    async def test_response_content_validation(self, mcp_client_session):
        """Test that response content follows MCP specifications."""
        client = mcp_client_session
        
        result = await client.call_tool("sum", {"a": 10, "b": 20})
        
        # Content should be a list
        assert isinstance(result.content, list)
        assert len(result.content) > 0
        
        # Each content item should have proper structure
        for content_item in result.content:
            # Should have text attribute for TextContent
            assert hasattr(content_item, 'text')
            assert isinstance(content_item.text, str)
    
    @pytest.mark.asyncio
    async def test_prompt_response_validation(self, mcp_client_session):
        """Test that prompt responses follow MCP specifications."""
        client = mcp_client_session
        
        result = await client.get_prompt("explain_calculation", {"calculation": "5 * 4"})
        
        # Should have description
        assert hasattr(result, 'description')
        assert isinstance(result.description, str)
        
        # Should have messages
        assert hasattr(result, 'messages')
        assert isinstance(result.messages, list)
        assert len(result.messages) > 0
        
        # Each message should have content
        for message in result.messages:
            assert hasattr(message, 'content')


@pytest.mark.client_integration
class TestMCPProtocolFlow:
    """Test complete MCP protocol flows."""
    
    @pytest.mark.asyncio
    async def test_complete_tool_workflow(self, mcp_client_session):
        """Test complete tool discovery and execution workflow."""
        client = mcp_client_session
        
        # 1. Discover available tools
        tools = await client.list_tools()
        assert len(tools) > 0
        
        # 2. Find a specific tool
        sum_tool = next((t for t in tools if t.name == "sum"), None)
        assert sum_tool is not None
        
        # 3. Validate tool schema
        schema = sum_tool.inputSchema
        assert 'properties' in schema
        assert 'a' in schema['properties']
        assert 'b' in schema['properties']
        
        # 4. Call the tool with valid parameters
        result = await client.call_tool("sum", {"a": 15, "b": 25})
        assert "40" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_complete_prompt_workflow(self, mcp_client_session):
        """Test complete prompt discovery and execution workflow."""
        client = mcp_client_session
        
        # 1. Discover available prompts
        prompts = await client.list_prompts()
        assert len(prompts) > 0
        
        # 2. Find a specific prompt
        explain_prompt = next((p for p in prompts if p.name == "explain_calculation"), None)
        assert explain_prompt is not None
        
        # 3. Use the prompt with parameters
        result = await client.get_prompt("explain_calculation", {"calculation": "12 + 8"})
        
        # 4. Validate response
        assert hasattr(result, 'description')
        assert hasattr(result, 'messages')
        assert "12 + 8" in str(result.messages[0].content)
    
    @pytest.mark.asyncio
    async def test_mixed_operations_workflow(self, mcp_client_session):
        """Test workflow mixing tools and prompts."""
        client = mcp_client_session
        
        # 1. List both tools and prompts
        tools = await client.list_tools()
        prompts = await client.list_prompts()
        assert len(tools) > 0
        assert len(prompts) > 0
        
        # 2. Use a tool
        tool_result = await client.call_tool("multiply", {"a": 6, "b": 7})
        assert "42" in tool_result.content[0].text
        
        # 3. Use a prompt for the same calculation
        prompt_result = await client.get_prompt("explain_calculation", {"calculation": "6 * 7"})
        assert "6 * 7" in str(prompt_result.messages[0].content)
        
        # 4. Use another tool
        tool_result2 = await client.call_tool("sum", {"a": 42, "b": 8})
        assert "50" in tool_result2.content[0].text
        
        # All operations should be independent and successful
        assert tool_result is not None
        assert prompt_result is not None
        assert tool_result2 is not None


@pytest.mark.client_integration
class TestMCPExtensibility:
    """Test MCP protocol extensibility features."""
    
    @pytest.mark.asyncio
    async def test_additional_tool_metadata(self, mcp_client_session):
        """Test handling of additional tool metadata."""
        client = mcp_client_session
        tools = await client.list_tools()
        
        for tool in tools:
            # Basic required fields should always be present
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description')
            assert hasattr(tool, 'inputSchema')
            
            # Tool might have additional metadata - client should handle gracefully
            # (In real implementations, this could include tags, categories, etc.)
    
    @pytest.mark.asyncio
    async def test_forward_compatibility(self, mcp_client_session):
        """Test forward compatibility with protocol extensions."""
        client = mcp_client_session
        
        # Client should handle responses with additional fields gracefully
        # Test that basic operations still work
        tools = await client.list_tools()
        assert len(tools) > 0
        
        result = await client.call_tool("sum", {"a": 1, "b": 1})
        assert "2" in result.content[0].text
        
        # Additional fields in responses should not break functionality
    
    @pytest.mark.asyncio
    async def test_protocol_resilience(self, mcp_client_session):
        """Test protocol resilience to various conditions."""
        client = mcp_client_session
        
        # Test multiple rapid operations
        for i in range(10):
            result = await client.call_tool("sum", {"a": i, "b": 1})
            assert str(i + 1) in result.content[0].text
        
        # Test interleaved operations
        tool_result = await client.call_tool("multiply", {"a": 3, "b": 4})
        prompt_result = await client.get_prompt("explain_calculation", {"calculation": "3 * 4"})
        tool_result2 = await client.call_tool("sum", {"a": 12, "b": 5})
        
        assert "12" in tool_result.content[0].text
        assert "3 * 4" in str(prompt_result.messages[0].content)
        assert "17" in tool_result2.content[0].text