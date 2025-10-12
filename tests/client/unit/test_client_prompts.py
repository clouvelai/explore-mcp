"""
Unit tests for MCP client prompt functionality.

These tests verify prompt discovery, retrieval, argument handling,
and response parsing for MCP prompts.
"""

import pytest
import asyncio
from unittest.mock import MagicMock
from typing import Dict, Any


@pytest.mark.client_unit
class TestPromptDiscovery:
    """Test prompt discovery and metadata retrieval."""
    
    @pytest.mark.asyncio
    async def test_list_prompts_basic(self, mock_client_session):
        """Test basic prompt listing functionality."""
        session = mock_client_session
        result = await session.list_prompts()
        
        assert result is not None
        assert hasattr(result, 'prompts')
        assert len(result.prompts) >= 1
        
        # Verify expected prompt is present
        prompt_names = [prompt.name for prompt in result.prompts]
        assert "explain_calculation" in prompt_names
    
    @pytest.mark.asyncio
    async def test_list_prompts_with_real_server(self, mcp_client_session):
        """Test prompt listing with real FastMCP server."""
        client = mcp_client_session
        prompts = await client.list_prompts()
        
        assert len(prompts) >= 1
        prompt_names = [prompt.name for prompt in prompts]
        assert "explain_calculation" in prompt_names
    
    @pytest.mark.asyncio
    async def test_prompt_metadata_validation(self, mcp_client_session):
        """Test that prompt metadata is properly structured."""
        client = mcp_client_session
        prompts = await client.list_prompts()
        
        for prompt in prompts:
            # Each prompt should have required metadata
            assert hasattr(prompt, 'name')
            assert hasattr(prompt, 'description')
            
            # Name and description should be non-empty strings
            assert isinstance(prompt.name, str) and len(prompt.name) > 0
            assert isinstance(prompt.description, str) and len(prompt.description) > 0
    
    @pytest.mark.asyncio
    async def test_explain_calculation_prompt_metadata(self, mcp_client_session):
        """Test specific metadata for the explain_calculation prompt."""
        client = mcp_client_session
        prompts = await client.list_prompts()
        
        explain_prompt = next((p for p in prompts if p.name == "explain_calculation"), None)
        assert explain_prompt is not None
        assert "calculation" in explain_prompt.description.lower()
        assert "explain" in explain_prompt.description.lower()


@pytest.mark.client_unit
class TestPromptRetrieval:
    """Test prompt retrieval and processing."""
    
    @pytest.mark.asyncio
    async def test_get_prompt_basic(self, mock_client_session):
        """Test basic prompt retrieval."""
        session = mock_client_session
        result = await session.get_prompt("explain_calculation", {"calculation": "5 + 3"})
        
        assert result is not None
        assert hasattr(result, 'description')
        assert hasattr(result, 'messages')
        assert len(result.messages) > 0
        
        # Check that the calculation is included in the prompt
        message_text = str(result.messages[0].content.text)
        assert "5 + 3" in message_text
    
    @pytest.mark.asyncio
    async def test_get_prompt_with_real_server(self, mcp_client_session):
        """Test prompt retrieval with real FastMCP server."""
        client = mcp_client_session
        result = await client.get_prompt("explain_calculation", {"calculation": "25 + 17"})
        
        assert result is not None
        assert hasattr(result, 'description')
        assert hasattr(result, 'messages')
        assert len(result.messages) > 0
        
        # Check that the calculation is included
        message_text = str(result.messages[0].content)
        assert "25 + 17" in message_text
    
    @pytest.mark.asyncio
    async def test_prompt_response_structure(self, mcp_client_session):
        """Test that prompt responses have correct structure."""
        client = mcp_client_session
        result = await client.get_prompt("explain_calculation", {"calculation": "10 * 5"})
        
        # Response should have description and messages
        assert hasattr(result, 'description')
        assert hasattr(result, 'messages')
        
        # Description should be a string
        assert isinstance(result.description, str)
        assert len(result.description) > 0
        
        # Messages should be a list with at least one message
        assert isinstance(result.messages, list)
        assert len(result.messages) > 0
        
        # Each message should have content
        for message in result.messages:
            assert hasattr(message, 'content')
    
    @pytest.mark.asyncio
    async def test_prompt_without_arguments(self, mock_client_session):
        """Test retrieving prompt without arguments."""
        session = mock_client_session
        
        # Modify mock to handle no arguments
        async def mock_get_prompt_no_args(name: str, arguments: Dict[str, Any] = None):
            if name == "explain_calculation":
                calculation = "1 + 1"  # Default when no arguments
                mock_result = MagicMock()
                mock_result.description = "Educational calculation explanation"
                mock_message = MagicMock()
                mock_message.content = MagicMock()
                mock_message.content.text = f"Let me explain {calculation} step by step..."
                mock_result.messages = [mock_message]
                return mock_result
            raise ValueError(f"Unknown prompt: {name}")
        
        session.get_prompt = mock_get_prompt_no_args
        
        result = await session.get_prompt("explain_calculation")
        assert result is not None
        assert "1 + 1" in result.messages[0].content.text


@pytest.mark.client_unit
class TestPromptArguments:
    """Test prompt argument handling."""
    
    @pytest.mark.asyncio
    async def test_prompt_with_simple_calculation(self, mcp_client_session, sample_prompts):
        """Test prompt with simple calculation argument."""
        client = mcp_client_session
        
        for prompt_data in sample_prompts["valid_prompts"]:
            result = await client.get_prompt(prompt_data["name"], prompt_data["arguments"])
            
            assert result is not None
            calculation = prompt_data["arguments"]["calculation"]
            message_text = str(result.messages[0].content)
            assert calculation in message_text
    
    @pytest.mark.asyncio
    async def test_prompt_with_complex_expression(self, mcp_client_session):
        """Test prompt with complex mathematical expression."""
        client = mcp_client_session
        complex_calc = "(5 + 3) * 2 - 1"
        
        result = await client.get_prompt("explain_calculation", {"calculation": complex_calc})
        
        assert result is not None
        message_text = str(result.messages[0].content)
        assert complex_calc in message_text
    
    @pytest.mark.asyncio
    async def test_prompt_with_special_characters(self, mcp_client_session):
        """Test prompt with special characters in calculation."""
        client = mcp_client_session
        special_calc = "√(16) + π"
        
        result = await client.get_prompt("explain_calculation", {"calculation": special_calc})
        
        assert result is not None
        message_text = str(result.messages[0].content)
        assert special_calc in message_text
    
    @pytest.mark.asyncio
    async def test_prompt_with_empty_calculation(self, mcp_client_session):
        """Test prompt with empty calculation string."""
        client = mcp_client_session
        
        result = await client.get_prompt("explain_calculation", {"calculation": ""})
        
        # Should handle empty string gracefully
        assert result is not None
        assert len(result.messages) > 0
    
    @pytest.mark.asyncio
    async def test_prompt_argument_types(self, mcp_client_session):
        """Test prompt with different argument types."""
        client = mcp_client_session
        
        # Test with string (normal case)
        result1 = await client.get_prompt("explain_calculation", {"calculation": "2 + 2"})
        assert result1 is not None
        
        # Test with number as string
        result2 = await client.get_prompt("explain_calculation", {"calculation": "42"})
        assert result2 is not None


@pytest.mark.client_unit
class TestPromptErrors:
    """Test prompt error handling."""
    
    @pytest.mark.asyncio
    async def test_nonexistent_prompt_error(self, mock_client_session):
        """Test requesting a non-existent prompt."""
        session = mock_client_session
        
        with pytest.raises(ValueError, match="Unknown prompt"):
            await session.get_prompt("nonexistent_prompt", {})
    
    @pytest.mark.asyncio
    async def test_invalid_prompt_arguments(self, mock_client_session):
        """Test prompt with invalid arguments."""
        session = mock_client_session
        
        # Modify mock to validate arguments
        async def mock_get_prompt_with_validation(name: str, arguments: Dict[str, Any] = None):
            if name == "explain_calculation":
                if not arguments or "calculation" not in arguments:
                    raise ValueError("Missing required argument: calculation")
                calculation = arguments["calculation"]
                mock_result = MagicMock()
                mock_result.description = "Educational calculation explanation"
                mock_message = MagicMock()
                mock_message.content = MagicMock()
                mock_message.content.text = f"Let me explain {calculation} step by step..."
                mock_result.messages = [mock_message]
                return mock_result
            raise ValueError(f"Unknown prompt: {name}")
        
        session.get_prompt = mock_get_prompt_with_validation
        
        # Test missing required argument
        with pytest.raises(ValueError, match="Missing required argument"):
            await session.get_prompt("explain_calculation", {})
        
        # Test with None arguments
        with pytest.raises(ValueError, match="Missing required argument"):
            await session.get_prompt("explain_calculation", None)


@pytest.mark.client_unit
class TestPromptContentValidation:
    """Test validation of prompt content and responses."""
    
    @pytest.mark.asyncio
    async def test_prompt_content_includes_step_by_step(self, mcp_client_session):
        """Test that explanation prompts include step-by-step content."""
        client = mcp_client_session
        result = await client.get_prompt("explain_calculation", {"calculation": "15 + 27"})
        
        message_text = str(result.messages[0].content).lower()
        assert "step" in message_text or "explain" in message_text
    
    @pytest.mark.asyncio
    async def test_prompt_content_educational_tone(self, mcp_client_session):
        """Test that prompt content has educational tone."""
        client = mcp_client_session
        result = await client.get_prompt("explain_calculation", {"calculation": "8 * 7"})
        
        # Should contain educational keywords
        message_text = str(result.messages[0].content).lower()
        educational_keywords = ["explain", "step", "calculation", "understand", "learn"]
        
        # At least one educational keyword should be present
        assert any(keyword in message_text for keyword in educational_keywords)
    
    @pytest.mark.asyncio
    async def test_prompt_preserves_calculation_format(self, mcp_client_session):
        """Test that prompts preserve the original calculation format."""
        client = mcp_client_session
        
        test_calculations = [
            "2 + 2",
            "10 - 5",
            "3 * 4",
            "20 / 4",
            "(5 + 3) * 2"
        ]
        
        for calc in test_calculations:
            result = await client.get_prompt("explain_calculation", {"calculation": calc})
            message_text = str(result.messages[0].content)
            assert calc in message_text
    
    @pytest.mark.asyncio
    async def test_prompt_response_completeness(self, mcp_client_session):
        """Test that prompt responses are complete and meaningful."""
        client = mcp_client_session
        result = await client.get_prompt("explain_calculation", {"calculation": "12 + 8"})
        
        # Response should be substantial (not just echoing the input)
        message_text = str(result.messages[0].content)
        assert len(message_text) > 20  # Should be more than just the calculation
        assert "12 + 8" in message_text  # Should include the calculation
        
        # Description should be meaningful
        assert len(result.description) > 10


@pytest.mark.client_unit
class TestPromptPerformance:
    """Test prompt performance and concurrent access."""
    
    @pytest.mark.asyncio
    async def test_multiple_prompt_requests(self, mcp_client_session):
        """Test multiple sequential prompt requests."""
        client = mcp_client_session
        
        calculations = ["1 + 1", "2 * 3", "10 - 5", "8 / 2", "5 + 7"]
        
        for calc in calculations:
            result = await client.get_prompt("explain_calculation", {"calculation": calc})
            assert result is not None
            assert calc in str(result.messages[0].content)
    
    @pytest.mark.asyncio
    async def test_concurrent_prompt_requests(self, mcp_client_session):
        """Test concurrent prompt requests."""
        client = mcp_client_session
        
        calculations = [f"{i} + {i+1}" for i in range(5)]
        
        # Create concurrent prompt requests
        tasks = [
            client.get_prompt("explain_calculation", {"calculation": calc})
            for calc in calculations
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Verify all results
        assert len(results) == 5
        for i, result in enumerate(results):
            assert result is not None
            expected_calc = calculations[i]
            message_text = str(result.messages[0].content)
            assert expected_calc in message_text
    
    @pytest.mark.asyncio
    async def test_prompt_with_very_long_calculation(self, mcp_client_session):
        """Test prompt with very long calculation string."""
        client = mcp_client_session
        
        # Create a long calculation string
        long_calc = " + ".join([str(i) for i in range(1, 21)])  # "1 + 2 + 3 + ... + 20"
        
        result = await client.get_prompt("explain_calculation", {"calculation": long_calc})
        
        assert result is not None
        message_text = str(result.messages[0].content)
        assert long_calc in message_text
        
        # Response should handle long input gracefully
        assert len(message_text) > len(long_calc)


@pytest.mark.client_unit
class TestPromptIntegration:
    """Test integration between prompts and other client functionality."""
    
    @pytest.mark.asyncio
    async def test_prompt_after_tool_calls(self, mcp_client_session):
        """Test using prompts after making tool calls."""
        client = mcp_client_session
        
        # First, make a tool call
        tool_result = await client.call_tool("sum", {"a": 15, "b": 27})
        assert "42" in tool_result.content[0].text
        
        # Then, use a prompt to explain the same calculation
        prompt_result = await client.get_prompt("explain_calculation", {"calculation": "15 + 27"})
        assert "15 + 27" in str(prompt_result.messages[0].content)
        
        # Both should work independently
        assert tool_result is not None
        assert prompt_result is not None
    
    @pytest.mark.asyncio
    async def test_alternating_tools_and_prompts(self, mcp_client_session):
        """Test alternating between tool calls and prompt requests."""
        client = mcp_client_session
        
        # Alternate between tools and prompts
        tool_result1 = await client.call_tool("sum", {"a": 5, "b": 3})
        prompt_result1 = await client.get_prompt("explain_calculation", {"calculation": "5 + 3"})
        
        tool_result2 = await client.call_tool("multiply", {"a": 4, "b": 6})
        prompt_result2 = await client.get_prompt("explain_calculation", {"calculation": "4 * 6"})
        
        # All should succeed
        assert "8" in tool_result1.content[0].text
        assert "5 + 3" in str(prompt_result1.messages[0].content)
        assert "24" in tool_result2.content[0].text
        assert "4 * 6" in str(prompt_result2.messages[0].content)
    
    @pytest.mark.asyncio
    async def test_session_state_independence(self, mcp_client_session):
        """Test that prompt calls don't affect session state."""
        client = mcp_client_session
        
        # Make a prompt request
        await client.get_prompt("explain_calculation", {"calculation": "10 + 5"})
        
        # Tool calls should still work normally
        tool_result = await client.call_tool("sum", {"a": 10, "b": 5})
        assert "15" in tool_result.content[0].text
        
        # Another prompt should work
        prompt_result = await client.get_prompt("explain_calculation", {"calculation": "20 - 5"})
        assert "20 - 5" in str(prompt_result.messages[0].content)